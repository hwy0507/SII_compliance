"""Bounded velocity-reference-to-impedance adapter for panel development runs.

The existing task, WBC command, metric targets and panel audits are unchanged.
This separate variant integrates WBC twist instead of following raw waypoints.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.spatial.transform import Rotation


def clip_norm(value: np.ndarray, limit: float) -> np.ndarray:
    value = np.asarray(value, dtype=float)
    return value * min(1., limit / max(float(np.linalg.norm(value)), 1.e-15))


@dataclass(frozen=True)
class ReferenceImpedanceConfig:
    stiffness: float = 300.
    rot_stiffness: float = 15.
    mass: float = 1.
    inertia: float = .08
    zeta: float = 1.
    max_linear_speed: float = .35
    max_angular_speed: float = 1.2
    max_position_error: float = .04
    max_rotation_error: float = .20
    nullspace_damping: float = 0.

    def __post_init__(self):
        values = asdict(self)
        null_damping = values.pop('nullspace_damping')
        if any(not np.isfinite(v) or v <= 0 for v in values.values()):
            raise ValueError('Reference impedance parameters must be finite and positive')
        if not np.isfinite(null_damping) or null_damping < 0:
            raise ValueError('Nullspace damping must be finite and nonnegative')
        if self.max_rotation_error >= np.pi:
            raise ValueError('Rotation error limit must be below pi')


class MovingEquilibrium:
    """Causal integrator with conditional integration and bounded spring error.

    No target pose, contact state, obstacle or event timing enters this helper.
    dt is the low-level control period. First update initializes without motion.
    """
    def __init__(self, cfg: ReferenceImpedanceConfig):
        self.cfg = cfg
        self.position = None
        self.rotation = None
        self.k = np.r_[np.full(3, cfg.stiffness), np.full(3, cfg.rot_stiffness)]
        masses = np.r_[np.full(3, cfg.mass), np.full(3, cfg.inertia)]
        self.damping = 2 * cfg.zeta * np.sqrt(masses * self.k)
        self.updates = 0
        self.position_limited_steps = 0
        self.rotation_limited_steps = 0
        self.max_integrated_linear_speed = 0.
        self.max_integrated_angular_speed = 0.

    @staticmethod
    def _admissible_fraction(error_norm, limit):
        # Bound growing error when initially within the ball. If an external
        # displacement has moved the robot outside, allow only non-growth;
        # never instantaneously rebase the reference onto the measured pose.
        bound = max(limit, error_norm(0.))
        if error_norm(1.) <= bound + 1.e-12:
            return 1.
        lo, hi = 0., 1.
        for _ in range(28):
            mid = (lo + hi) / 2
            if error_norm(mid) <= bound:
                lo = mid
            else:
                hi = mid
        return lo

    def update(self, position, rotation, nominal_twist, dt):
        position = np.asarray(position, dtype=float)
        rotation = np.asarray(rotation, dtype=float)
        nominal_twist = np.asarray(nominal_twist, dtype=float)
        if position.shape != (3,) or rotation.shape != (3, 3) or nominal_twist.shape != (6,):
            raise ValueError('Expected position(3), rotation(3,3), nominal twist(6)')
        if not all(np.isfinite(v).all() for v in (position, rotation, nominal_twist)):
            raise ValueError('Reference inputs must be finite')
        if not np.isfinite(dt) or dt <= 0:
            raise ValueError('Control period must be finite and positive')
        if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1.e-6) or np.linalg.det(rotation) <= 0:
            raise ValueError('Measured orientation must be a proper rotation')
        cfg = self.cfg
        bounded_twist = np.r_[clip_norm(nominal_twist[:3], cfg.max_linear_speed),
                              clip_norm(nominal_twist[3:], cfg.max_angular_speed)]
        if self.position is None:
            self.position = position.copy()
            self.rotation = rotation.copy()
        else:
            dp, dr = bounded_twist[:3] * dt, bounded_twist[3:] * dt
            # A tiny low-level period keeps angular increments inside one
            # principal-log branch; reject caller mistakes rather than wrap.
            if np.linalg.norm(dr) >= np.pi / 2:
                raise ValueError('Angular integration increment must be below pi/2')
            ap = self._admissible_fraction(
                lambda a: np.linalg.norm(self.position + a * dp - position),
                cfg.max_position_error)
            def next_rotation(a):
                return Rotation.from_rotvec(a * dr).as_matrix() @ self.rotation
            ar = self._admissible_fraction(
                lambda a: np.linalg.norm(Rotation.from_matrix(next_rotation(a) @ rotation.T).as_rotvec()),
                cfg.max_rotation_error)
            self.position += ap * dp
            self.rotation = next_rotation(ar)
            self.position_limited_steps += int(ap < 1. - 1.e-8)
            self.rotation_limited_steps += int(ar < 1. - 1.e-8)
            self.max_integrated_linear_speed = max(self.max_integrated_linear_speed, float(ap * np.linalg.norm(dp) / dt))
            self.max_integrated_angular_speed = max(self.max_integrated_angular_speed, float(ar * np.linalg.norm(dr) / dt))
        self.updates += 1
        raw_error = np.r_[self.position - position,
                          Rotation.from_matrix(self.rotation @ rotation.T).as_rotvec()]
        spring_error = np.r_[clip_norm(raw_error[:3], cfg.max_position_error),
                             clip_norm(raw_error[3:], cfg.max_rotation_error)]
        return spring_error, bounded_twist

    def wrench(self, spring_error, nominal_twist, measured_twist):
        return self.k * spring_error + self.damping * (nominal_twist - measured_twist)

    def diagnostics(self):
        return {key: getattr(self, key) for key in (
            'updates', 'position_limited_steps', 'rotation_limited_steps',
            'max_integrated_linear_speed', 'max_integrated_angular_speed')}


def install(module, cfg, audit):
    import audited_velocity_env as velocity_env
    import current_student_policy_20260921 as loader
    from run_benchmark import body_jacobian, body_twist

    original_create = module.create_environment
    original_torque = velocity_env.safe_velocity_tracking_torque
    state = {}

    def create(args):
        args.model = Path('reference_impedance_in_memory')
        args.mixture = 0.
        env, task, scene = original_create(args)
        if env.execution_mode != 'twist':
            raise ValueError('Reference impedance requires the standard twist execution mode')
        integrator = MovingEquilibrium(cfg)
        state.update(env=env, integrator=integrator, last_time=None)
        audit['integrator'] = integrator
        original_wbc = env._wbc_command
        def capture_command(*args, **kwargs):
            command = original_wbc(*args, **kwargs)
            state['command'] = command
            return command
        env._wbc_command = capture_command
        return env, task, scene

    def impedance_torque(bias_torque, measured_joint_velocity, joint_velocity_command,
                         previous_torque, dt, config, torque_limits=None):
        env, integrator = state['env'], state['integrator']
        model, data = env.model, env.data
        if 'command' not in state:
            raise RuntimeError('No nominal WBC command was captured before torque evaluation')
        now = float(data.time)
        if state['last_time'] != now:
            if state['last_time'] is not None and now < state['last_time']:
                raise RuntimeError('Unexpected time reset: create a fresh integrator per episode')
            state['reference'] = integrator.update(
                data.xpos[env._hand_id], data.xmat[env._hand_id].reshape(3, 3),
                state['command'].task_twist_world, dt)
            state['last_time'] = now
        error, nominal_twist = state['reference']
        jacobian = body_jacobian(model, data, env._hand_id)
        wrench = integrator.wrench(error, nominal_twist, body_twist(model, data, env._hand_id))
        residual = jacobian.T @ wrench
        if cfg.nullspace_damping:
            nullspace = np.eye(7) - jacobian.T @ np.linalg.pinv(jacobian.T)
            residual -= cfg.nullspace_damping * nullspace @ measured_joint_velocity
        equivalent = measured_joint_velocity + residual / np.asarray(config.velocity_gain_nm_per_radps)
        return original_torque(bias_torque, measured_joint_velocity, equivalent,
                               previous_torque, dt, config, torque_limits=torque_limits)

    class ReferencePolicy:
        kind = 'cartesian_impedance_moving_reference'
        def act(self, observation):
            return np.zeros(7)

    module.create_environment = create
    loader.load_current = lambda _: ReferencePolicy()
    velocity_env.safe_velocity_tracking_torque = impedance_torque


def main():
    import audited_velocity_env as velocity_env
    import current_student_policy_20260921 as loader

    parser = argparse.ArgumentParser(add_help=False)
    for key, value in asdict(ReferenceImpedanceConfig()).items():
        parser.add_argument('--reference-' + key.replace('_', '-'), dest=key, type=float, default=value)
    parsed, remaining = parser.parse_known_args()
    cfg = ReferenceImpedanceConfig(**vars(parsed))
    if '--output' not in remaining:
        raise ValueError('--output is required')
    output = Path(remaining[remaining.index('--output') + 1]).with_suffix('.json')
    if output.exists():
        raise FileExistsError(f'Refusing to overwrite existing result: {output}')
    source = Path(__file__).with_name('run_panel_push_20260920.py')
    text = source.read_text()
    marker = '    run=module.run\n'
    if text.count(marker) != 1:
        raise RuntimeError('Panel runner contract changed: missing unique hook')
    text = text.replace(marker, '    _install_reference(module, _reference_cfg, _reference_audit)\n' + marker)
    audit = {}
    namespace = dict(__name__='panel_reference_impedance_runtime', __file__=str(source),
                     _install_reference=install, _reference_cfg=cfg, _reference_audit=audit)
    previous = sys.argv
    original_torque, original_load = velocity_env.safe_velocity_tracking_torque, loader.load_current
    try:
        sys.argv = [str(source), *remaining, '--teacher-profile', 'memory',
                    '--teacher-force-source', 'estimated', '--mixture', '0']
        exec(compile(text, str(source), 'exec'), namespace)
        namespace['main']()
    finally:
        sys.argv = previous
        velocity_env.safe_velocity_tracking_torque = original_torque
        loader.load_current = original_load
    result = json.loads(output.read_text())
    if result['teacher_called']:
        raise RuntimeError('Reference impedance unexpectedly called VMC teacher')
    result['reference_impedance_parameters'] = asdict(cfg)
    result['reference_impedance_diagnostics'] = audit['integrator'].diagnostics()
    result['baseline_scope'] = 'development only; velocity-reference-to-impedance adapter; unchanged task and metric targets'
    result['impedance_backend'] = 'bias+J.T@(K*bounded_integrated_pose_error+D*(bounded_nominal_twist-measured_twist)); shared torque box/slew'
    result['source_sha256'][Path(__file__).name] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(result=str(output), controller=result['controller'],
                         teacher_called=False, reference=audit['integrator'].diagnostics())))


if __name__ == '__main__':
    main()
