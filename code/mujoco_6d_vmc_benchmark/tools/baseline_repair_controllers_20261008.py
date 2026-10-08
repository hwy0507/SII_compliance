"""Versioned repairs to the frozen classical/parameter-RL adapters.

Install in an independent parameter-source directory alongside controllers_legacy.
No shared environment, historical teacher, gate or actuator configuration changes.
The impedance backend remains native Cartesian torque, with explicit command
and torque limiting; it is not an action7 policy or a global passivity proof.
"""
from pathlib import Path
import json
import tempfile

import numpy as np
from scipy.spatial.transform import Rotation

import controllers_legacy as legacy
from run_panel_impedance_reference_20260923 import MovingEquilibrium, clip_norm
from wbc_velocity_residual_core import (
    FilteredVelocityResidualAction, damped_pseudoinverse, safe_joint_velocity_command,
)

REPAIR_VERSION = 'physical-units-projected-impedance-v1'
ParameterShield = legacy.ParameterShield
vectors = legacy.vectors


class DiskArrayLog:
    """Append exact float64 rows without a per-substep Python-object history.

    Temporary disk storage is only an implementation detail of telemetry;
    controller state and final NPZ schema remain identical. The memory map
    lets NumPy's compressed save stream rows under the worker's memory cap.
    """
    def __init__(self, width):
        self.width=int(width);self.count=0
        self.file=tempfile.TemporaryFile(prefix='sii-impedance-telemetry-',buffering=1024*1024)

    def append(self,row):
        row=np.ascontiguousarray(row,dtype=np.float64)
        if row.shape!=(self.width,):raise ValueError('Telemetry row width changed')
        self.file.write(row.tobytes());self.count+=1

    def __bool__(self):return self.count>0

    def __len__(self):return self.count

    def __array__(self,dtype=None,copy=None):
        self.file.flush()
        if not self.count:return np.empty((0,self.width),dtype=dtype or np.float64)
        values=np.memmap(self.file,dtype=np.float64,mode='r',shape=(self.count,self.width))
        if dtype is not None and np.dtype(dtype)!=values.dtype:return values.astype(dtype)
        return values.copy() if copy else values

    def close(self):self.file.close()


class ProjectedEquilibrium(MovingEquilibrium):
    """Project the proposed reference onto the bounded spring-error ball.

    Unlike scalar conditional integration, tangential motion at the boundary
    remains possible. A disturbed robot can rebase a reference to the 4 cm
    ball; this bounded controller change is explicit, not an environment reset.
    """
    def update(self, position, rotation, nominal_twist, dt):
        p = np.asarray(position, float)
        r = np.asarray(rotation, float)
        v = np.asarray(nominal_twist, float)
        if p.shape != (3,) or r.shape != (3, 3) or v.shape != (6,):
            raise ValueError('Expected pose3/rotation3x3/twist6')
        if not all(np.isfinite(x).all() for x in (p, r, v)) or not np.isfinite(dt) or dt <= 0:
            raise ValueError('Nonfinite pose/twist or invalid dt')
        if not np.allclose(r.T @ r, np.eye(3), atol=1e-6) or np.linalg.det(r) <= 0:
            raise ValueError('Proper measured rotation required')
        cfg = self.cfg
        bounded = np.r_[clip_norm(v[:3], cfg.max_linear_speed),
                        clip_norm(v[3:], cfg.max_angular_speed)]
        if np.linalg.norm(bounded[3:] * dt) >= np.pi / 2:
            raise ValueError('Rotation increment too large')
        if self.position is None:
            self.position, self.rotation = p.copy(), r.copy()
        else:
            proposed_error = self.position + bounded[:3] * dt - p
            self.position_limited_steps += int(np.linalg.norm(proposed_error) > cfg.max_position_error)
            self.position = p + clip_norm(proposed_error, cfg.max_position_error)
            proposed_rotation = Rotation.from_rotvec(bounded[3:] * dt).as_matrix() @ self.rotation
            rotation_error = Rotation.from_matrix(proposed_rotation @ r.T).as_rotvec()
            self.rotation_limited_steps += int(np.linalg.norm(rotation_error) > cfg.max_rotation_error)
            self.rotation = Rotation.from_rotvec(clip_norm(rotation_error, cfg.max_rotation_error)).as_matrix() @ r
        self.updates += 1
        error = np.r_[self.position - p, Rotation.from_matrix(self.rotation @ r.T).as_rotvec()]
        return error, bounded


class ParameterController(legacy.ParameterController):
    def __init__(self, env, method, prior):
        super().__init__(env, method, prior)
        self.repair_servo = []
        self.repair_options = dict(prior.get('repair_options', {}))
        if method == 'vmc':
            self.actor.action_limits = np.r_[
                np.full(3, env.safety_config.maximum_linear_yield_mps),
                np.full(3, env.safety_config.maximum_angular_yield_radps)]
        elif method == 'impedance':
            import audited_velocity_env as backend
            from run_benchmark import body_jacobian, body_twist
            self.servo = DiskArrayLog(28)
            self.repair_servo = DiskArrayLog(36)
            self.actor = ProjectedEquilibrium(self.actor.cfg)
            self.apply(self.shield.theta)
            self.previous_equivalent_command = np.zeros(7)
            self.initial_joint_position = env.data.qpos[:7].copy()
            options = {'friction_compensation': 1., 'nullspace_stiffness': 5.,
                       'nullspace_damping': 1.}
            if set(self.repair_options) - set(options):
                raise ValueError('Unknown impedance repair options')
            options.update(self.repair_options)
            if not all(np.isfinite(v) and v >= 0 for v in options.values()):
                raise ValueError('Finite nonnegative controller gains required')
            if options['friction_compensation'] > 1:
                raise ValueError('Friction feedforward cannot exceed model friction loss')
            self.repair_options = options

            def torque(bias_torque, measured_joint_velocity, joint_velocity_command,
                       previous_torque, dt, config, torque_limits=None):
                e = self.env
                J = body_jacobian(e.model, e.data, e._hand_id)
                # Consume the actual nominal command after the common joint
                # speed/acceleration limiter, never re-query task/scene state.
                nominal = J @ np.asarray(joint_velocity_command)
                now = float(e.data.time)
                if self.last_servo_time != now:
                    self.last_error, self.last_nominal = self.actor.update(
                        e.data.xpos[e._hand_id].copy(), e.data.xmat[e._hand_id].reshape(3, 3).copy(), nominal, dt)
                    self.last_servo_time = now
                measured = body_twist(e.model, e.data, e._hand_id)
                self.last_relative_velocity = measured - self.last_nominal
                wrench = self.actor.wrench(self.last_error, self.last_nominal, measured)
                projector = np.eye(7) - damped_pseudoinverse(J, config.pseudoinverse_damping) @ J
                posture = projector.T @ (
                    options['nullspace_stiffness'] * (self.initial_joint_position - e.data.qpos[:7])
                    - options['nullspace_damping'] * np.asarray(measured_joint_velocity))
                # Known robot friction parameters and commanded encoder velocity
                # only. No contact force, payload pose or obstacle information.
                friction = options['friction_compensation'] * e.model.dof_frictionloss[:7] * np.tanh(
                    np.asarray(joint_velocity_command) / .03)
                residual = J.T @ wrench + posture + friction
                requested = np.asarray(measured_joint_velocity) + residual / np.asarray(config.velocity_gain_nm_per_radps)
                neutral = FilteredVelocityResidualAction(1., np.zeros(6), np.zeros(7), False, False)
                limited, _ = safe_joint_velocity_command(requested, J, neutral,
                    self.previous_equivalent_command, dt, config)
                applied, scale = self.original_torque(bias_torque, measured_joint_velocity,
                    limited, previous_torque, dt, config, torque_limits=torque_limits)
                self.previous_equivalent_command = limited.copy()
                self.servo.append(np.r_[now, self.last_error, wrench, residual, applied, float(scale)])
                self.repair_servo.append(np.r_[now, joint_velocity_command, requested, limited, posture, friction])
                return applied, scale

            backend.safe_velocity_tracking_torque = torque

    def save(self, out):
        report = super().save(out)
        report.update(repair_version=REPAIR_VERSION, repair_options=self.repair_options,
                      historical_controller_unmodified=True)
        if self.method == 'vmc':
            report['physical_action_units'] = self.actor.action_limits.tolist()
        if self.method == 'impedance':
            np.savez_compressed(out/'impedance_repair_servo.npz', values=np.asarray(self.repair_servo),
                columns=np.asarray(['time'] + [f'{name}_{i}' for name in (
                    'nominal_limited_qdot', 'requested_equivalent_qdot', 'limited_equivalent_qdot',
                    'nullspace_torque', 'friction_feedforward') for i in range(7)]))
            report['execution_semantics'] = 'Native torque: projected Cartesian spring/damper, model friction feedforward and nullspace posture; bounded equivalent joint command then unchanged torque amplitude/slew. Physical velocity still audited separately.'
            report['telemetry_storage'] = 'Disk-backed exact float64 rows, same complete servo NPZ schemas; no control-law change'
            self.servo.close();self.repair_servo.close()
        (Path(out)/'CONTROLLER_REPAIR.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
        return report
