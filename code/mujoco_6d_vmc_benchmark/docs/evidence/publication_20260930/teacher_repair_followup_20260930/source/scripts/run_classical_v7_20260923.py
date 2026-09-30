"""Classical controllers on the unchanged v7 primitive task/physics protocol.

Impedance uses bias + J.T @ (K e + D e_dot), with the existing torque box
projection and slew limiter. Admittance integrates M xdd + D xd + K x = w_hat
and uses the existing bounded Cartesian-velocity action adapter. No contact
oracle, fixture clock, or obstacle geometry is provided to either controller.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

import audited_velocity_env as velocity_env
import current_student_policy_20260921 as loader
import run_primitive_teacher_v7_20260917 as primitive
from haptic_vmc_teacher_20260916 import equivalent_tool_wrench
from run_benchmark import body_jacobian, body_twist, so3_log


def primitive_args(argv):
    """Reuse the frozen runner's parser declarations without copying defaults."""
    source = Path(primitive.__file__)
    main_guard = ast.parse(source.read_text()).body[-1]
    # Parser declarations and parse_args precede validation and run(args).
    declarations = []
    for statement in main_guard.body:
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            if isinstance(statement.value.func, ast.Name) and statement.value.func.id == 'run':
                break
        declarations.append(statement)
    tree = ast.Module(body=declarations, type_ignores=[])
    namespace = dict(vars(primitive))
    previous = sys.argv
    try:
        sys.argv = [str(source), *argv]
        exec(compile(tree, str(source), 'exec'), namespace)
    finally:
        sys.argv = previous
    return namespace['args']


class Admittance:
    kind = 'cartesian_admittance'

    def __init__(self, cfg, environment):
        self.env = environment
        self.mass = np.r_[np.full(3, cfg.mass), np.full(3, cfg.inertia)]
        self.k = np.r_[np.full(3, cfg.stiffness), np.full(3, cfg.rot_stiffness)]
        self.d = 2 * cfg.zeta * np.sqrt(self.mass * self.k)
        self.offset = np.zeros(6)
        self.velocity = np.zeros(6)
        self.speed_limit = np.r_[np.full(3, .16), np.full(3, .6)]
        self.offset_limit = np.r_[np.full(3, .08), np.full(3, .25)]

    def act(self, observation):
        # contact45_v2 joint-load slots are 32:39. The Jacobian depends only
        # on the robot joint configuration, not contact or obstacle state.
        jacobian = body_jacobian(self.env.model, self.env.data, self.env._hand_id)
        wrench = equivalent_tool_wrench(jacobian, observation[32:39])
        bounds = np.array([30., 30., 30., 3., 3., 3.])
        wrench = bounds * np.tanh(wrench / bounds)
        dt = primitive.RL_DT / 20
        for _ in range(20):
            acceleration = (wrench - self.d * self.velocity - self.k * self.offset) / self.mass
            self.velocity = np.clip(self.velocity + acceleration * dt, -self.speed_limit, self.speed_limit)
            self.offset = np.clip(self.offset + self.velocity * dt, -self.offset_limit, self.offset_limit)
        action = np.zeros(7)
        action[1:4] = self.velocity[:3] / self.env.safety_config.maximum_linear_yield_mps
        action[4:] = self.velocity[3:] / self.env.safety_config.maximum_angular_yield_radps
        return np.clip(action, -1., 1.)


class ZeroAction:
    kind = 'cartesian_impedance'

    def act(self, observation):
        return np.zeros(7)


def main():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--classical-controller', choices=('impedance', 'admittance'), required=True)
    p.add_argument('--classical-stiffness', dest='stiffness', type=float, default=900.)
    p.add_argument('--classical-rot-stiffness', dest='rot_stiffness', type=float, default=45.)
    p.add_argument('--classical-mass', dest='mass', type=float, default=1.)
    p.add_argument('--classical-inertia', dest='inertia', type=float, default=.08)
    p.add_argument('--classical-zeta', dest='zeta', type=float, default=1.)
    cfg, remaining = p.parse_known_args()
    if min(cfg.stiffness, cfg.rot_stiffness, cfg.mass, cfg.inertia, cfg.zeta) <= 0:
        raise ValueError('All classical controller parameters must be positive')
    args = primitive_args(remaining)
    args.model = Path('classical_controller_in_memory')
    args.teacher_profile = 'none'
    args.teacher_force_source = 'estimated'
    args.mixture = 0.
    original_create = primitive.create_environment
    original_torque = velocity_env.safe_velocity_tracking_torque
    original_load = loader.load_current
    state = {}

    def create(a):
        env, task, spec = original_create(a)
        state['env'] = env
        return env, task, spec

    def impedance_torque(bias_torque, measured_joint_velocity, joint_velocity_command,
                         previous_torque, dt, config, torque_limits=None):
        env = state['env']; model, data = env.model, env.data
        command = env._wbc_command(float(data.time))
        error = np.r_[command.target_position_m - data.xpos[env._hand_id],
                      so3_log(command.target_rotation @ data.xmat[env._hand_id].reshape(3, 3).T)]
        twist_error = command.task_twist_world - body_twist(model, data, env._hand_id)
        k = np.r_[np.full(3, cfg.stiffness), np.full(3, cfg.rot_stiffness)]
        inertia = np.r_[np.full(3, cfg.mass), np.full(3, cfg.inertia)]
        damping = 2 * cfg.zeta * np.sqrt(inertia * k)
        wrench = k * error + damping * twist_error
        jacobian = body_jacobian(model, data, env._hand_id)
        # Dampen redundant self-motion without adding a Cartesian task force.
        nullspace = np.eye(7) - jacobian.T @ np.linalg.pinv(jacobian.T)
        residual = jacobian.T @ wrench - nullspace @ (2. * measured_joint_velocity)
        # Reuse exactly the existing torque feasibility and slew projection:
        # encode our torque as an equivalent servo error before projection.
        equivalent_command = measured_joint_velocity + residual / np.asarray(config.velocity_gain_nm_per_radps)
        return original_torque(bias_torque, measured_joint_velocity, equivalent_command,
                               previous_torque, dt, config, torque_limits=torque_limits)

    primitive.create_environment = create
    loader.load_current = lambda _: Admittance(cfg, state['env']) if cfg.classical_controller == 'admittance' else ZeroAction()
    if cfg.classical_controller == 'impedance':
        velocity_env.safe_velocity_tracking_torque = impedance_torque
    try:
        primitive.run(args)
    finally:
        primitive.create_environment = original_create
        velocity_env.safe_velocity_tracking_torque = original_torque
        loader.load_current = original_load
    path = args.output.with_suffix('.json')
    result = json.loads(path.read_text())
    result['classical_parameters'] = vars(cfg)
    result['baseline_scope'] = 'v7 source primitive diagnostic; office blind test not used'
    result['impedance_backend'] = 'bias+J.T@(K*pose_error+D*twist_error); shared torque limits and slew'
    result['admittance_backend'] = 'causal proprioceptive wrench -> M-D-K -> bounded velocity residual'
    result['source_sha256'][Path(__file__).name] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    failures = []
    if not result['success']: failures.append('task_incomplete')
    if not result['real_contact'] and args.scene != 'empty': failures.append('no_valid_contact')
    if result['invalid_physics']: failures.append('penetration_over_2mm')
    if result['upstream_contact']: failures.append('upstream_contact')
    result['accepted'] = not failures
    result['failure_reasons'] = failures
    # Retain the legacy 2-mm stopping rule for comparability, but never label
    # its acceptance as the strict project gate.
    penetration = max(result['contact']['max_penetration_m'],
                      result['contact']['all_external_max_penetration_m'])
    result['penetration_mm'] = 1000. * penetration
    result['strict_gate_threshold_mm'] = .2
    result['strict_accepted'] = not failures and penetration <= .0002
    result['strict_failure_reasons'] = failures + (
        ['penetration_over_0.2mm'] if penetration > .0002 else [])
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'result': str(path), 'accepted': result['accepted'], 'failure_reasons': failures}), flush=True)


if __name__ == '__main__':
    main()
