"""Counterfactual actor diagnosis on saved histories; no integration or fitting.

First replay an actual teacher history exactly. Teacher predictions on student
states are then explicitly counterfactual, never labels or physical outcomes.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from run_video_reference_coverage_20261029 import make_actor


def predict(actor, obs):
    result = []
    for o in obs:
        actor.observe(o)
        result.append(actor.act(o[39:45], .04))
    return np.asarray(result)


def summary(actual, counterfactual):
    error = actual-counterfactual
    return dict(mse=float(np.mean(error**2)), max_abs=float(np.abs(error).max()),
                channel_rmse=np.sqrt(np.mean(error**2, axis=0)).tolist(),
                requested_residual_saturation_fraction=float(np.mean(np.any(np.abs(actual[:, 1:]) >= .999, axis=1))),
                teacher_counterfactual_residual_saturation_fraction=float(np.mean(np.any(np.abs(counterfactual[:, 1:]) >= .999, axis=1))))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--support-diagnosis', type=Path, required=True)
    p.add_argument('--regression', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    support = read(a.support_diagnosis)
    assert support['dataset_sha256'] == '120173888964ee0545393cd0d2685c794f7aa261626463fa7c10fc981b9c6407'
    baseline = ROOT/'outputs/special_scene_direction_collection_20261029_v9/rod_00/rod'
    baseline_hashes = read(baseline/'SOURCE_HASHES.json')
    for name in ('tools/optimize_tool_contact_20261002.py', 'tools/intent_recovery_teacher_20261029.py',
                 'tools/intent_equilibrium_teacher_20261029.py', 'scripts/vmc_teacher_stable_readout_20260930.py',
                 'scripts/run_vmc_6d_constrained_push_20260918.py'):
        assert sha(ROOT/name) == baseline_hashes[name], name
    config = read(baseline/'teacher.json')
    execution = read(baseline/'execution.json')
    assert execution['teacher_config_sha256'] == sha(baseline/'teacher.json')
    with np.load(baseline/'trajectory.npz', allow_pickle=False) as z:
        teacher_obs, teacher_actions = z['observation'], z['action']
    replay = predict(make_actor(config), teacher_obs)
    np.testing.assert_array_equal(replay, teacher_actions)
    rows = []
    for original in support['rows']:
        folder = a.regression/'evaluation'/(original['method']+'__'+original['condition'])
        assert sha(folder/'rollout.npz') == original['trace_sha256']
        with np.load(folder/'rollout.npz', allow_pickle=False) as z:
            obs, requested, time = (z[k].copy() for k in ('observation', 'esn_action', 'time'))
        expected = predict(make_actor(config), obs)
        assert expected.shape == requested.shape == (len(time), 7)
        point_time = original['first_applied_saturation_s']
        point = None
        if point_time is not None:
            k = int(np.argmin(np.abs(time-point_time)))
            point = dict(time_s=float(time[k]), student_requested=requested[k].tolist(),
                teacher_counterfactual_requested=expected[k].tolist(),
                estimated_wrench=obs[k, 39:45].tolist(),
                max_abs_difference=float(np.abs(requested[k]-expected[k]).max()))
        windows = []
        for start, end in ((0., 1.5), (1.5, 2.12), (2.12, 6.), (6., float(time[-1])+.001)):
            selected = (time >= start-1e-8) & (time < end-1e-8)
            if selected.any():
                windows.append(dict(start_s=start, end_s=end, frames=int(selected.sum()),
                                    **summary(requested[selected], expected[selected])))
        rows.append(dict(method=original['method'], condition=original['condition'],
            trajectory_sha256=original['trace_sha256'], frames=len(time),
            comparison=summary(requested, expected), windows=windows, first_saturation_comparison=point))
    result = dict(schema='sii-v9-teacher-on-saved-student-histories-v1',
        status='counterfactual_actor_diagnosis_no_physics_no_fit', created_utc=datetime.now(timezone.utc).isoformat(),
        support_diagnosis_sha256=sha(a.support_diagnosis), source_sha256=sha(Path(__file__)),
        teacher_config_sha256=sha(baseline/'teacher.json'),
        teacher_replay=dict(trajectory_sha256=sha(baseline/'trajectory.npz'), frames=len(teacher_actions),
                            max_abs_error=float(np.max(np.abs(replay-teacher_actions)))),
        rows=rows, limitations=['Teacher never physically executed on these student states.',
            'Counterfactual predictions are not training labels, a teacher success certificate or a causal intervention.',
            'Only already-inspected condition000 is analyzed; no held-out model selection.',
            'Different task tracking references and state histories remain relevant.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    write(a.output, result)
    print([dict(method=r['method'], mse=r['comparison']['mse'], first_saturation=r['first_saturation_comparison']) for r in rows])


if __name__ == '__main__':
    main()
