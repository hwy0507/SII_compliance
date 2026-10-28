"""Offline, bounded-memory diagnostics for existing 48D development traces.

Loads one <=600-row rollout at a time; does not create any MuJoCo environment.
Contact and stage are used for audit grouping only, never fed to the policy.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from current_student_policy_20260921 import load_current
from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics
from wbc_velocity_residual_core import VelocityResidualActionFilter, VelocityResidualSafetyConfig

BLOCKS = {'q': (0, 7), 'qdot': (7, 14), 'wbc_twist': (14, 20),
          'pose_error': (20, 26), 'twist_error': (26, 32),
          'joint_load': (32, 39), 'estimated_wrench': (39, 45), 'path_direction': (45, 48)}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def summarize(mask, arrays, normalized, physical_action, shadow_teacher):
    if not np.any(mask):
        return {'n': 0}
    obs, action = arrays['observation'][mask], arrays['action'][mask]
    positions, target = arrays['position'][mask], arrays['target'][mask]
    twist, t = arrays['twist'][mask], arrays['time'][mask]
    desired = physical_action[mask]
    nominal_linear = obs[:, 14:17]
    yield_linear = desired[:, 1:4]
    path = obs[:, 45:48]
    path = path / np.maximum(np.linalg.norm(path, axis=1, keepdims=True), 1.e-12)
    z = normalized[mask]
    return dict(n=int(mask.sum()), first_time_s=float(t[0]), last_time_s=float(t[-1]),
                action_mean=action.mean(0).tolist(), action_abs_p95=np.percentile(abs(action), 95, axis=0).tolist(),
                filtered_feedback_scale_next_action_mean=float(desired[:, 0].mean()),
                filtered_yield_twist_mean=desired[:, 1:].mean(0).tolist(),
                raw_scaled_yield_mean=(action[:, 1:]*np.array([.32,.32,.32,.6,.6,.6])).mean(0).tolist(),
                slew_minus_raw_yield_mean=(desired[:, 1:]-action[:, 1:]*np.array([.32,.32,.32,.6,.6,.6])).mean(0).tolist(),
                x_action_std=float(action[:, 1].std()),
                x_action_sign_flip_fraction=float(np.mean(action[1:, 1]*action[:-1, 1]<0)) if len(action)>1 else None,
                x_action_lag1_correlation=float(np.corrcoef(action[1:,1],action[:-1,1])[0,1]) if len(action)>2 and action[1:,1].std()>1.e-10 and action[:-1,1].std()>1.e-10 else None,
                nominal_twist_mean=obs[:, 14:20].mean(0).tolist(),
                observed_twist_mean=twist.mean(0).tolist(),
                yield_opposes_nominal_fraction=float(np.mean(np.sum(nominal_linear * yield_linear, axis=1) < -1.e-7)),
                yield_along_path_mean_mps=float(np.mean(np.sum(yield_linear * path, axis=1))),
                endpoint_error_m=float(np.linalg.norm(positions[-1] - target[-1])),
                speed_p95_25hz_mps=float(np.percentile(np.linalg.norm(twist[:, :3], axis=1), 95)),
                estimated_wrench_mean=obs[:, 39:45].mean(0).tolist(),
                estimated_wrench_abs_p95=np.percentile(abs(obs[:, 39:45]), 95, axis=0).tolist(),
                normalized_max_abs=float(abs(z).max()),
                normalized_any_gt3_fraction=float(np.mean(np.max(abs(z), axis=1) > 3)),
                normalized_any_gt12_fraction=float(np.mean(np.max(abs(z), axis=1) > 12)),
                normalized_block_max_abs={k: float(abs(z[:, lo:hi]).max()) for k, (lo, hi) in BLOCKS.items()},
                same_state_reference_vmc_action_mae=np.mean(abs(action-shadow_teacher[mask]), axis=0).tolist(),
                same_state_reference_vmc_action_mean=shadow_teacher[mask].mean(0).tolist())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--esn', type=Path, required=True)
    parser.add_argument('--mlp', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    protocol = json.loads((args.evidence / 'panel48_protocol.json').read_text())
    final = json.loads((args.evidence / 'panel48_final.json').read_text())
    checkpoints = {'esn': args.esn, 'mlp': args.mlp}
    for family, checkpoint in checkpoints.items():
        if digest(checkpoint) != protocol['models'][family]['sha256']:
            raise ValueError(f'Frozen checkpoint hash mismatch: {family}')
    with np.load(args.esn, allow_pickle=False) as checkpoint:
        mean, std = checkpoint['mean'].copy(), checkpoint['std'].copy()
    with np.load(args.mlp, allow_pickle=False) as checkpoint:
        if not np.allclose(mean, checkpoint['mean']) or not np.allclose(std, checkpoint['std']):
            raise ValueError('MLP/ESN normalization mismatch')
    rows = []
    for method in ('vmc', 'mlp', 'esn'):
        for path in sorted((args.evidence / 'panel48_traces' / method).glob('*/rollout.npz')):
            with np.load(path, allow_pickle=False) as trace:
                data = {k: trace[k].copy() for k in trace.files}
            obs, action = data['observation'], data['action']
            if obs.shape != (len(action), 48) or action.shape[1] != 7:
                raise ValueError(f'Invalid contract: {path}')
            normalized = (obs-mean) / std
            result = next(r for r in final['rows'] if r['method'] == method and str(r['fixture']['seed']) == path.parent.name)
            actor = load_current(checkpoints[method]) if method in checkpoints else None
            replay_error = None
            if actor is not None:
                pred = np.stack([actor.act(o) for o in obs])
                replay_error = float(np.max(abs(pred-action)))
            teacher = SixDVirtualDynamics(protocol['vmc'])
            shadow_teacher = np.stack([teacher.act(o[39:45], .04) for o in obs])
            filt = VelocityResidualActionFilter(VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32))
            physical_action = []
            slew_limited = []
            amplitude_saturated = []
            for a in action:
                applied = filt.filter(a, .04)
                physical_action.append(np.r_[applied.wbc_scale, applied.cartesian_yield_twist])
                slew_limited.append(applied.slew_limited)
                amplitude_saturated.append(applied.amplitude_saturated)
            physical_action = np.asarray(physical_action)
            contact = np.linalg.norm(data['force'], axis=1) > .05
            indices = np.flatnonzero(contact)
            n = len(action)
            pre = np.arange(n) < indices[0] if len(indices) else np.ones(n, bool)
            post = np.arange(n) > indices[-1] if len(indices) else np.zeros(n, bool)
            masks = {'all': np.ones(n, bool), 'pre_contact_sample': pre,
                     'contact_samples': contact, 'between_first_last_contact_samples': ~(pre | post) if len(indices) else np.zeros(n, bool),
                     'post_last_contact_sample': post, 'last_1s': np.arange(n) >= n-25}
            masks.update({f'stage_{stage}': data['stage'] == stage for stage in np.unique(data['stage'])})
            transitions = np.flatnonzero(np.r_[True, np.diff(data['stage']) != 0])
            rows.append(dict(method=method, fixture=result['fixture'], task_success=result['task_success'],
                             trace=str(path), trace_sha256=digest(path), checkpoint_action_replay_max_abs_error=replay_error,
                             reference_vmc_replay_max_abs_error=float(abs(shadow_teacher-action).max()) if method == 'vmc' else None,
                             recorded_teacher_action_all_zero=bool(np.all(data['teacher_action'] == 0)),
                             transitions=[dict(stage=int(data['stage'][i]), recorded_poststep_time_s=float(data['time'][i])) for i in transitions],
                             first_contact_sample_s=float(data['time'][indices[0]]) if len(indices) else None,
                             last_contact_sample_s=float(data['time'][indices[-1]]) if len(indices) else None,
                             largest_normalized_dimensions=np.argsort(np.max(abs(normalized), axis=0))[-8:].tolist(),
                             amplitude_saturated_steps=int(sum(amplitude_saturated)),
                             slew_limited_steps=int(sum(slew_limited)),
                             last_1s_action_execution_replay=[dict(poststep_time_s=float(data['time'][i]),
                                 pre_step_time_s=float(data['time'][i]-.04), raw_action=action[i].tolist(),
                                 filtered_feedback_scale_for_next_action=float(physical_action[i,0]),
                                 feedback_scale_input_to_current_action=float(physical_action[i-1,0]) if i else 1.,
                                 raw_yield_twist=(action[i,1:]*np.array([.32,.32,.32,.6,.6,.6])).tolist(),
                                 slew_filtered_yield_twist=physical_action[i,1:].tolist(),
                                 observed_nominal_twist_pre_step=obs[i,14:20].tolist(),
                                 observed_twist_post_step=data['twist'][i].tolist()) for i in range(max(0,n-25),n)],
                             groups={name: summarize(mask, data, normalized, physical_action, shadow_teacher) for name, mask in masks.items()}))
    report = dict(scope='offline diagnostics of fixed-checkpoint development traces; no new rollout or selection',
                  source_sha256=digest(__file__), checkpoint_sha256={k: digest(p) for k, p in checkpoints.items()},
                  observation_blocks=BLOCKS,
                  limitations=['force contact masks are 25Hz audit samples, not substep contact segmentation',
                               'observation/action are pre-step; recorded time/position/twist are post-step (40ms offset)',
                               'reconstructed filtered actions precede joint-velocity/acceleration/torque projections',
                               'direct_esn mode uses filtered scale as feedback scheduling next action, then sets composed wbc_scale=1; never multiply nominal twist again',
                               'same-state reference VMC replay is a diagnostic counterfactual, not a rollout or the unique training teacher',
                               'normalization z scores are distribution proxies, not proof of membership in training support',
                               'student teacher_action arrays are zeros when mixture=0; they must not be treated as teacher labels'],
                  rows=rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'output': str(args.output), 'rollouts': len(rows),
                      'largest_action_replay_error': max(r['checkpoint_action_replay_max_abs_error'] or 0 for r in rows)}))


if __name__ == '__main__':
    main()
