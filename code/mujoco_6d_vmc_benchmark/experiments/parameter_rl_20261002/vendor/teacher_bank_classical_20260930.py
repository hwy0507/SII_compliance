"""Classical controllers for the paired source-domain teacher-bank campaign.

Admittance shifts a WBC pose reference using M-D-K dynamics. Impedance applies
J.T times a Cartesian spring/damper wrench through the existing motor limiter.
Neither controller is a renamed VMC, nor an ESN distillation action label.
This process-local adapter must run in an isolated rollout subprocess.
"""
from __future__ import annotations

from dataclasses import asdict
from types import SimpleNamespace

import numpy as np

METHODS = ('admittance', 'impedance')
SEARCH_DIMENSIONS = {'admittance': 7, 'impedance': 5}
DIMENSIONS = ('stiffness', 'rot_stiffness', 'mass', 'inertia',
              'zeta', 'rot_zeta', 'vertical_stiffness_ratio')


def decode(x, method):
    """Unit-cube search with fixed safety, without redundant impedance axes.

    Positive M/K/D alone do not guarantee the robot's closed-loop stability.
    Both controllers get the same evaluation count, not the same numerical K.
    """
    if method not in METHODS:
        raise ValueError(f'Unknown classical method: {method}')
    x = np.asarray(x, dtype=float)
    dimensions = SEARCH_DIMENSIONS[method]
    if x.shape != (dimensions,) or not np.isfinite(x).all() or np.any((x < 0) | (x > 1)):
        raise ValueError(f'{dimensions} finite unit-cube coordinates required for {method}')
    if method == 'impedance':
        # This is a spring/damper torque controller, not virtual inertial
        # dynamics. M/I only parameterize damping, so freeze them and search
        # stiffness, damping ratios and vertical anisotropy independently.
        keys = ('stiffness', 'rot_stiffness', 'zeta', 'rot_zeta', 'vertical_stiffness_ratio')
        bounds = ((150., 1800.), (7.5, 90.), (.5, 2.), (.5, 2.), (.5, 2.))
        return dict(mass=.5, inertia=.06, **{key: float(lo * (hi / lo) ** v)
            for key, v, (lo, hi) in zip(keys, x, bounds)})
    bounds = [(60., 900.), (3., 45.)]
    bounds += [(.3, 2.), (.03, .16), (.5, 2.), (.5, 2.), (.5, 2.)]
    return {key: float(lo * (hi / lo) ** v)
            for key, v, (lo, hi) in zip(DIMENSIONS, x, bounds)}


def validate_config(config):
    if set(config) != set(DIMENSIONS):
        raise ValueError('Classical config must have exactly the seven declared dimensions')
    if any(not np.isfinite(v) or v <= 0 for v in config.values()):
        raise ValueError('Classical parameters must be finite and positive')
    return SimpleNamespace(**config)


def physical_vectors(config):
    cfg = validate_config(config)
    k = np.r_[cfg.stiffness, cfg.stiffness,
              cfg.stiffness * cfg.vertical_stiffness_ratio,
              np.repeat(cfg.rot_stiffness, 3)]
    mass = np.r_[np.repeat(cfg.mass, 3), np.repeat(cfg.inertia, 3)]
    zeta = np.r_[np.repeat(cfg.zeta, 3), np.repeat(cfg.rot_zeta, 3)]
    return mass, k, 2 * zeta * np.sqrt(mass * k)


def _observation(observation):
    observation = np.asarray(observation, dtype=float)
    if observation.shape != (48,) or not np.isfinite(observation).all():
        raise ValueError('Finite canonical48 observation required (not wrench6)')
    return observation


def _finite_row(row, shapes):
    """Reject incomplete/nonfinite traces before reductions can mask NaN."""
    for key, shape in shapes.items():
        value = np.asarray(row[key], dtype=float)
        if value.shape != shape or not np.isfinite(value).all():
            raise ValueError(f'Invalid classical trace field {key}: expected finite shape {shape}')


def _maximum_difference(maximum, left, right):
    left, right = np.asarray(left), np.asarray(right)
    if left.shape != right.shape or not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError('Nonfinite or mismatched classical replay comparison')
    return max(maximum, float(np.max(np.abs(left - right))))


def configure_environment(env, config, method, records):
    """Return actor.act(obs48, dt=.04), installing impedance torque if needed.

    Must be called after env creation and before the first controlled step.
    Actors accept the same 48D record but access only the original baseline's
    proprioceptive/reference fields; FK/J come from the same robot snapshot.
    Call actor.close() in finally to restore the process-local backend.
    Save actor.servo_records separately for impedance algebra replay.
    """
    if method not in METHODS:
        raise ValueError(method)
    cfg = validate_config(config)
    mass, stiffness, damping = physical_vectors(config)
    if env.execution_mode != 'twist':
        raise ValueError('Classical comparison requires shared twist-mode environment')
    if method == 'admittance':
        from run_panel_admittance_reference_20260923 import ReferenceAdmittance
        base = ReferenceAdmittance(cfg, env, .04)
        base.state.mass = mass
        base.state.k = stiffness
        base.state.d = damping
        original_advance = base.state.advance
        raw_wrench = {}

        def capture_advance(wrench, dt):
            raw_wrench['value'] = np.array(wrench)
            return original_advance(wrench, dt)

        base.state.advance = capture_advance

        class AdmittanceActor:
            kind = 'cartesian_admittance_shifted_reference'
            servo_records = None
            metadata = dict(method=method, parameters=dict(config), actor_input='canonical48',
                reads='q[0:7], nominal_twist[14:20], pose_error[20:26], estimated_joint_load[32:39]; robot FK/J',
                equations='M*zdd+D*zd+K*z=w_hat; shifted-reference WBC residual',
                action_semantics='action7 Cartesian residual; baseline only, not current VMC distillation labels',
                limitation='sample-held reference difference through repeated WBC/IK; not exact reference replacement')

            def act(self, observation, dt=.04):
                obs = _observation(observation)
                if abs(dt - .04) > 1e-12:
                    raise ValueError('Frozen actor period is 0.04 s')
                action = base.act(obs)
                trace = base.trace[-1]
                records.append(dict(request=action.copy(), observation=obs.copy(),
                    offset=base.state.offset.copy(), velocity=base.state.velocity.copy(),
                    wrench=raw_wrench['value'].copy(),
                    effective_wrench=trace[12:18].copy(), requested_residual=trace[18:24].copy(),
                    nominal_scale=float(base.mapper.scale), action_units=base.action_units.copy()))
                return action

            def close(self):
                pass

        return AdmittanceActor()

    import audited_velocity_env as velocity_env
    from run_benchmark import body_jacobian, body_twist
    from run_panel_impedance_reference_20260923 import MovingEquilibrium, ReferenceImpedanceConfig
    reference_cfg = ReferenceImpedanceConfig(stiffness=cfg.stiffness,
        rot_stiffness=cfg.rot_stiffness, mass=cfg.mass, inertia=cfg.inertia, zeta=cfg.zeta)
    integrator = MovingEquilibrium(reference_cfg)
    integrator.k = stiffness
    integrator.damping = damping
    original_torque = velocity_env.safe_velocity_tracking_torque
    original_command = env._wbc_command
    state = dict(last_time=None)
    servo_records = []

    def capture_command(*args, **kwargs):
        command = original_command(*args, **kwargs)
        state['command'] = command
        return command

    def impedance_torque(bias_torque, measured_joint_velocity, joint_velocity_command,
                         previous_torque, dt, safety, torque_limits=None):
        if 'command' not in state:
            raise RuntimeError('Nominal command must precede impedance execution')
        data = env.data
        now = float(data.time)
        position = data.xpos[env._hand_id].copy()
        rotation = data.xmat[env._hand_id].reshape(3, 3).copy()
        nominal = state['command'].task_twist_world.copy()
        advanced = state['last_time'] != now
        if advanced:
            if state['last_time'] is not None and now < state['last_time']:
                raise RuntimeError('Fresh classical actor required on episode reset')
            state['reference'] = integrator.update(position, rotation, nominal, dt)
            state['last_time'] = now
        spring_error, bounded_nominal = state['reference']
        measured_twist = body_twist(env.model, data, env._hand_id)
        jacobian = body_jacobian(env.model, data, env._hand_id)
        wrench = integrator.wrench(spring_error, bounded_nominal, measured_twist)
        residual = jacobian.T @ wrench
        equivalent = measured_joint_velocity + residual / np.asarray(safety.velocity_gain_nm_per_radps)
        applied, scale = original_torque(bias_torque, measured_joint_velocity, equivalent,
                                        previous_torque, dt, safety, torque_limits=torque_limits)
        servo_records.append(dict(time=now, dt=float(dt), advanced=advanced, position=position,
            rotation=rotation, nominal_twist=nominal, measured_twist=measured_twist.copy(),
            jacobian=jacobian.copy(), spring_error=spring_error.copy(), wrench=wrench.copy(),
            residual_torque=residual.copy(), bias_torque=np.array(bias_torque),
            measured_joint_velocity=np.array(measured_joint_velocity), previous_torque=np.array(previous_torque),
            applied_torque=applied.copy(), feasible_scale=float(scale),
            torque_limits=np.array(torque_limits if torque_limits is not None else env.torque_limits)))
        return applied, scale

    env._wbc_command = capture_command
    velocity_env.safe_velocity_tracking_torque = impedance_torque

    class ImpedanceActor:
        kind = 'cartesian_impedance_moving_reference'
        metadata = dict(method=method, parameters=dict(config), actor_input='canonical48',
            reads='robot pose/twist/J and shared nominal WBC twist; no contact or scene input',
            equations='bias+J.T@(K*bounded_integrated_pose_error+D*(bounded_nominal_twist-measured_twist))',
            action_semantics='zero action7; real baseline control is the Cartesian impedance torque backend',
            safety='unchanged shared torque amplitude/slew limiter; fixed equilibrium bounds',
            reference_config=asdict(reference_cfg), limitation='not an action7 policy and not an ESN label source')
        metadata['mass_inertia_semantics'] = ('effective damping parameters only: D=2*zeta*sqrt(M*K); '
            'MovingEquilibrium integrates nominal velocity, not a virtual inertia ODE. '
            'Search fixes mass=.5 and inertia=.06 and uses five independent axes.')

        def act(self, observation, dt=.04):
            obs = _observation(observation)
            if abs(dt - .04) > 1e-12:
                raise ValueError('Frozen actor period is 0.04 s')
            action = np.zeros(7)
            records.append(dict(request=action.copy(), observation=obs.copy()))
            return action

        def close(self):
            if velocity_env.safe_velocity_tracking_torque is not impedance_torque:
                raise RuntimeError('Impedance backend changed concurrently; refusing to overwrite')
            velocity_env.safe_velocity_tracking_torque = original_torque
            env._wbc_command = original_command

    actor = ImpedanceActor()
    actor.servo_records = servo_records
    return actor


def replay_admittance(config, records):
    """Replay M-D-K and action normalization; WBC FK reconstruction is separate.

    Does not pretend recorded residuals independently prove correct FK/WBC.
    """
    from admittance_reference_core_20260923 import AdmittanceState
    mass, stiffness, damping = physical_vectors(config)
    state = AdmittanceState(mass, stiffness)
    state.d = damping
    maximum = 0.
    for row in records:
        _finite_row(row, dict(wrench=(6,), effective_wrench=(6,), offset=(6,), velocity=(6,),
            requested_residual=(6,), action_units=(6,), request=(7,)))
        if np.any(np.asarray(row['action_units']) <= 0):
            raise ValueError('Action units must be positive')
        effective = state.advance(row['wrench'], .04)
        action = np.r_[0., np.clip(np.asarray(row['requested_residual']) / row['action_units'], -1., 1.)]
        for a, b in ((effective, row['effective_wrench']), (state.offset, row['offset']),
                     (state.velocity, row['velocity']), (action, row['request'])):
            maximum = _maximum_difference(maximum, a, b)
    return dict(max_abs=maximum, scope='virtual M-D-K and action normalization only; FK/WBC not independently replayed')


def replay_impedance(config, rows, safety):
    """Independent reference, wrench, projection and shared limiter replay."""
    from run_panel_impedance_reference_20260923 import MovingEquilibrium, ReferenceImpedanceConfig
    from wbc_velocity_residual_core import safe_velocity_tracking_torque
    cfg = validate_config(config)
    state = MovingEquilibrium(ReferenceImpedanceConfig(stiffness=cfg.stiffness,
        rot_stiffness=cfg.rot_stiffness, mass=cfg.mass, inertia=cfg.inertia, zeta=cfg.zeta))
    _, state.k, state.damping = physical_vectors(config)
    maximum = 0.
    reference_initialized = False
    for row in rows:
        _finite_row(row, dict(dt=(), position=(3,), rotation=(3, 3), nominal_twist=(6,),
            measured_twist=(6,), jacobian=(6, 7), spring_error=(6,), wrench=(6,),
            residual_torque=(7,), bias_torque=(7,), measured_joint_velocity=(7,),
            previous_torque=(7,), applied_torque=(7,), feasible_scale=(), torque_limits=(7,)))
        if row['dt'] <= 0 or np.any(np.asarray(row['torque_limits']) <= 0):
            raise ValueError('Positive servo period and torque limits required')
        if not isinstance(row['advanced'], (bool, np.bool_)):
            raise ValueError('Reference update marker must be boolean')
        if row['advanced']:
            error, nominal = state.update(row['position'], row['rotation'], row['nominal_twist'], row['dt'])
            reference_initialized = True
        elif not reference_initialized:
            raise ValueError('Impedance trace must begin with a reference update')
        wrench = state.wrench(error, nominal, row['measured_twist'])
        residual = row['jacobian'].T @ wrench
        velocity = row['measured_joint_velocity']
        equivalent = velocity + residual / np.asarray(safety.velocity_gain_nm_per_radps)
        torque, scale = safe_velocity_tracking_torque(row['bias_torque'], velocity, equivalent,
            row['previous_torque'], row['dt'], safety, torque_limits=row['torque_limits'])
        for a, b in ((error, row['spring_error']), (wrench, row['wrench']),
                     (residual, row['residual_torque']), (torque, row['applied_torque']), (scale, row['feasible_scale'])):
            maximum = _maximum_difference(maximum, a, b)
    return dict(max_abs=maximum, scope='reference dynamics, Cartesian wrench, recorded-J projection, motor limiter; not simulator dynamics')
