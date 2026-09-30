"""Classical controllers through the existing panel scene/task/audit wrapper.

Installs controller hooks in memory. Use the same PANEL_CONFIG and primitive
CLI flags as the comparison teacher; historical source files are untouched.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import audited_velocity_env as velocity_env
import current_student_policy_20260921 as loader
from run_classical_v7_20260923 import Admittance, ZeroAction
from run_benchmark import body_jacobian, body_twist, so3_log


def install(module, cfg):
    original_create = module.create_environment
    original_torque = velocity_env.safe_velocity_tracking_torque
    state = {}

    def create(args):
        args.model = Path('classical_controller_in_memory')
        args.mixture = 0.
        env, task, scene = original_create(args)
        state['env'] = env
        return env, task, scene

    def impedance_torque(bias_torque, measured_joint_velocity, joint_velocity_command,
                         previous_torque, dt, config, torque_limits=None):
        env = state['env']; model, data = env.model, env.data
        command = env._wbc_command(float(data.time))
        error = np.r_[command.target_position_m - data.xpos[env._hand_id],
                      so3_log(command.target_rotation @ data.xmat[env._hand_id].reshape(3, 3).T)]
        twist_error = command.task_twist_world - body_twist(model, data, env._hand_id)
        k = np.r_[np.full(3, cfg.stiffness), np.full(3, cfg.rot_stiffness)]
        mass = np.r_[np.full(3, cfg.mass), np.full(3, cfg.inertia)]
        jacobian = body_jacobian(model, data, env._hand_id)
        nullspace = np.eye(7) - jacobian.T @ np.linalg.pinv(jacobian.T)
        residual = jacobian.T @ (k * error + 2 * cfg.zeta * np.sqrt(mass*k) * twist_error)
        residual -= nullspace @ (2. * measured_joint_velocity)
        equivalent = measured_joint_velocity + residual / np.asarray(config.velocity_gain_nm_per_radps)
        return original_torque(bias_torque, measured_joint_velocity, equivalent,
                               previous_torque, dt, config, torque_limits=torque_limits)

    module.create_environment = create
    loader.load_current = lambda _: (Admittance(cfg, state['env'])
        if cfg.classical_controller == 'admittance' else ZeroAction())
    if cfg.classical_controller == 'impedance':
        velocity_env.safe_velocity_tracking_torque = impedance_torque


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--classical-controller', choices=('impedance', 'admittance'), required=True)
    parser.add_argument('--classical-stiffness', dest='stiffness', type=float, default=900.)
    parser.add_argument('--classical-rot-stiffness', dest='rot_stiffness', type=float, default=45.)
    parser.add_argument('--classical-mass', dest='mass', type=float, default=1.)
    parser.add_argument('--classical-inertia', dest='inertia', type=float, default=.08)
    parser.add_argument('--classical-zeta', dest='zeta', type=float, default=1.)
    cfg, remaining = parser.parse_known_args()
    if min(cfg.stiffness, cfg.rot_stiffness, cfg.mass, cfg.inertia, cfg.zeta) <= 0:
        raise ValueError('Classical parameters must be positive')
    if '--output' not in remaining:
        raise ValueError('--output is required')
    output = Path(remaining[remaining.index('--output') + 1]).with_suffix('.json')
    if output.exists():
        raise FileExistsError(f'Refusing to overwrite existing result: {output}')
    source = Path(__file__).with_name('run_panel_push_20260920.py')
    text = source.read_text()
    marker = '    run=module.run\n'
    if text.count(marker) != 1:
        raise RuntimeError('Panel runner contract changed: missing unique controller hook')
    text = text.replace(marker, '    _install_classical(module, _classical_cfg)\n' + marker)
    namespace = dict(__name__='panel_classical_runtime', __file__=str(source),
                     _install_classical=install, _classical_cfg=cfg)
    previous = sys.argv
    original_torque, original_load = velocity_env.safe_velocity_tracking_torque, loader.load_current
    try:
        # Panel requires memory-profile metadata; model+mixture=0 means its
        # VMC teacher is never called. Result.teacher_called verifies this.
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
        raise RuntimeError('Classical rollout unexpectedly called VMC teacher')
    result['classical_parameters'] = vars(cfg)
    result['baseline_scope'] = 'panel push controller integration; fixed parameters'
    result['source_sha256'][Path(__file__).name] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(result=str(output), controller=result['controller'],
                         accepted_panel_demo=result.get('accepted_panel_demo'), teacher_called=False)))


if __name__ == '__main__':
    main()
