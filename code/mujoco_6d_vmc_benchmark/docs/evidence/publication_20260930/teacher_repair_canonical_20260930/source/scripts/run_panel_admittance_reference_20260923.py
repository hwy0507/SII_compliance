"""Independent panel admittance variant; common nominal task, WBC and safety.

    python scripts/run_panel_admittance_reference_20260923.py \
      --scene push --output outputs/new_variant/seed0 --duration 18 [panel args]

Never changes the historical velocity-only admittance runner or its results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import mujoco
import numpy as np

from admittance_reference_core_20260923 import (
    AdmittanceState, ShiftedWBCResidual, rotation_offset_and_jacobian,
)
from haptic_vmc_teacher_20260916 import equivalent_tool_wrench
from run_benchmark import body_jacobian
import current_student_policy_20260921 as loader


class ReferenceAdmittance:
    kind = 'cartesian_admittance_reference_v2'

    def __init__(self, cfg, env, control_dt):
        # Keep the SAME robot kinematic snapshot used by the nominal WBC.
        # mj_step advances qpos after computing xpos/J: rebuilding FK from
        # post-step q mixes timestamps with the runner's observed nominal.
        # Access below is restricted to arm q/J/hand pose; no contact queries,
        # object pose, task object, or scene clock enters the policy.
        self.model = env.model
        self.data = env.data
        self.hand_id = env._hand_id
        self.wbc = env.fixed_wbc
        self.dt = control_dt
        self.action_units = np.r_[np.full(3, env.safety_config.maximum_linear_yield_mps),
                                 np.full(3, env.safety_config.maximum_angular_yield_radps)]
        self.state = AdmittanceState(np.r_[np.full(3, cfg.mass), np.full(3, cfg.inertia)],
                                    np.r_[np.full(3, cfg.stiffness), np.full(3, cfg.rot_stiffness)], cfg.zeta)
        self.mapper = ShiftedWBCResidual()
        self.trace = []
        self.last_observation = None

    def act(self, observation):
        observation = np.asarray(observation, dtype=float)
        if observation.shape not in ((45,), (48,)) or not np.all(np.isfinite(observation)):
            raise ValueError('Requires finite contact45_v2 or proprio48_action7_6d_v1 observation')
        self.last_observation = observation.copy()
        if not np.array_equal(self.data.qpos[:7], observation[:7]):
            raise ValueError('Encoder observation is not from the current nominal-WBC snapshot')
        jacobian = body_jacobian(self.model, self.data, self.hand_id)
        wrench = equivalent_tool_wrench(jacobian, observation[32:39])
        effective = self.state.advance(wrench, self.dt)
        current_rotation = self.data.xmat[self.hand_id].reshape(3, 3)
        nominal_position = self.data.xpos[self.hand_id] + observation[20:23]
        nominal_rotation = rotation_offset_and_jacobian(observation[23:26])[0]@current_rotation

        def evaluate(offset, feedforward):
            rotation = rotation_offset_and_jacobian(offset[3:])[0]@nominal_rotation
            return self.wbc.command(self.data, nominal_position+offset[:3], rotation,
                                    feedforward, feedback_scale=1.).task_twist_world

        residual = self.mapper.compute(observation[14:20], self.state, evaluate)
        action = np.r_[0., np.clip(residual/self.action_units, -1., 1.)]
        self.trace.append(np.r_[self.state.offset, self.state.velocity, effective, residual,
                                self.mapper.scale, float(np.any(np.abs(residual/self.action_units)>1.))])
        return action


def install(module, cfg, state):
    original_create = module.create_environment

    def create(args):
        args.model = Path('admittance_reference_in_memory')
        args.mixture = 0.
        env, task, scene = original_create(args)
        # The panel BlindTask uses piecewise fixed targets with zero nominal
        # feedforward. Reject unsupported reference types instead of assuming.
        if type(task) not in (module.BlindTask, module.TableCornerTask):
            raise ValueError('Reference admittance only supports the frozen BlindTask reference')
        _, _, linear, angular = task.sample()
        if np.any(linear) or np.any(angular):
            raise ValueError('Nonzero nominal feedforward requires an explicit observation contract')
        state['policy'] = ReferenceAdmittance(cfg, env, module.RL_DT)
        return env, task, scene

    module.create_environment = create
    loader.load_current = lambda _: state['policy']


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--classical-controller', choices=('admittance',), default='admittance')
    parser.add_argument('--classical-stiffness', dest='stiffness', type=float, default=900.)
    parser.add_argument('--classical-rot-stiffness', dest='rot_stiffness', type=float, default=45.)
    parser.add_argument('--classical-mass', dest='mass', type=float, default=1.)
    parser.add_argument('--classical-inertia', dest='inertia', type=float, default=.08)
    parser.add_argument('--classical-zeta', dest='zeta', type=float, default=1.)
    cfg, remaining = parser.parse_known_args()
    values = np.asarray([cfg.stiffness, cfg.rot_stiffness, cfg.mass, cfg.inertia, cfg.zeta])
    if not np.all(np.isfinite(values)) or np.any(values <= 0):
        raise ValueError('Admittance parameters must be finite and positive')
    if '--output' not in remaining:
        raise ValueError('--output is required')
    output = Path(remaining[remaining.index('--output')+1]).with_suffix('.json')
    # Panel runner writes fixed sibling trace names; require a fresh rollout
    # directory so no historical or concurrently running artifacts are changed.
    if output.parent.exists() and any(output.parent.iterdir()):
        raise FileExistsError(f'Requires a new, empty output directory: {output.parent}')
    source = Path(__file__).with_name('run_panel_push_20260920.py')
    source_text = source.read_text()
    marker = '    run=module.run\n'
    if source_text.count(marker) != 1:
        raise RuntimeError('Panel hook contract changed')
    source_text = source_text.replace(marker, '    _install_reference(module, _cfg, _state)\n'+marker)
    state = {}
    namespace = dict(__name__='panel_admittance_reference_runtime', __file__=str(source),
                     _install_reference=install, _cfg=cfg, _state=state)
    previous, original_load = sys.argv, loader.load_current
    try:
        sys.argv = [str(source), *remaining, '--teacher-profile', 'memory',
                    '--teacher-force-source', 'estimated', '--mixture', '0']
        exec(compile(source_text, str(source), 'exec'), namespace)
        namespace['main']()
    except Exception as error:
        policy = state.get('policy')
        if policy is not None:
            diagnostic = dict(error=repr(error),
                observation=None if policy.last_observation is None else policy.last_observation.tolist(),
                completed_actions=len(policy.trace),
                nominal_wbc=policy.mapper.last_diagnostic,
                offset=policy.state.offset.tolist(), velocity=policy.state.velocity.tolist(),
                kinematics_source='same read-only robot snapshot as observed nominal WBC')
            output.with_name('admittance_reference_failure.json').write_text(
                json.dumps(diagnostic, indent=2, allow_nan=False)+'\n')
        raise
    finally:
        sys.argv = previous
        loader.load_current = original_load
    result = json.loads(output.read_text())
    if result['teacher_called']:
        raise RuntimeError('Unexpected VMC teacher call')
    policy = state['policy']
    np.savez_compressed(output.with_name('admittance_reference_state.npz'),
                       trace=np.asarray(policy.trace),
                       columns=np.asarray(['offset6', 'velocity6', 'effective_wrench6',
                                           'requested_residual6', 'nominal_scale1', 'action_clipped1']))
    result['admittance_reference'] = dict(
        version='shifted_wbc_reference_r2_snapshot_aligned', parameters=vars(cfg),
        equations='M*zdd+D*zd+K*z=w_hat; residual=s*(WBC(target+z,zd/s)-WBC(target,0))',
        control_period_s=policy.dt, nominal_reference_modified=False,
        controller_contact_truth=False, rotational_model='bounded local world rotation-vector M-D-K',
        kinematics_source='read-only arm q/J/hand pose from the same nominal-WBC control snapshot',
        safety='unchanged 7D action filter, IK, joint velocity/torque and slew limits',
        nominal_scale_unobservable_steps=policy.mapper.scale_unobservable_steps,
        trace='admittance_reference_state.npz',
        limitation='sample-held Cartesian difference with repeated damped-IK projection; not exact joint-space reference replacement')
    for name in (Path(__file__).name, 'admittance_reference_core_20260923.py',
                 'fixed_panda_wbc.py', 'audited_velocity_env.py', 'wbc_velocity_residual_core.py',
                 'haptic_vmc_teacher_20260916.py'):
        path = Path(__file__).with_name(name)
        result['source_sha256'][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'result': str(output), 'controller': policy.kind,
                      'accepted_panel_demo': result.get('accepted_panel_demo')}))


if __name__ == '__main__':
    main()
