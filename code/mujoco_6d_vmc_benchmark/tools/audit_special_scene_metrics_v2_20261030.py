"""Supplement frozen v1 metrics with independently registered horizon checks.

Does not change a running worker or the frozen task/safety/comfort thresholds.
The expected horizon must come from the dispatch registration, never inferred
from the observed trajectory. Short, otherwise readable episodes remain rows.
"""
import argparse
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import read, sha, write


def check_horizon(execution, trajectory_time, substep_time, dt, legacy, expected_s):
    assert np.isfinite(expected_s) and expected_s > 0
    steps = round(expected_s/.04)
    assert abs(steps*.04-expected_s) < 1e-9, 'Horizon must be registered on the 25-Hz grid'
    assert execution['physics_dt_s'] == .00005
    t = np.asarray(trajectory_time)
    st = np.asarray(substep_time)
    dt = np.asarray(dt)
    assert t.ndim == st.ndim == dt.ndim == 1
    assert len(t) == execution['steps'] > 0
    assert len(st) == len(dt) == execution['substeps'] == len(t)*800
    assert np.isfinite(t).all() and np.isfinite(st).all() and np.isfinite(dt).all()
    # This wrapper records post-step states from t=0. Accumulated floating
    # point clock drift is below 1e-8 s for all registered 13/20/30-s scenes.
    np.testing.assert_allclose(t, np.arange(1,len(t)+1)*.04, atol=1e-8, rtol=0)
    np.testing.assert_allclose(st, np.arange(1,len(st)+1)*.00005, atol=1e-8, rtol=0)
    np.testing.assert_array_equal(dt, np.full(len(st),.00005))
    assert abs(execution['physical_seconds']-t[-1]) < 1e-8
    assert len(t) <= steps, 'Over-budget episode is an execution/registration defect'
    reasons = []
    if execution['status'] != 'complete':
        reasons.append('execution_not_complete')
    if len(t) != steps:
        reasons.append('registered_horizon_not_completed')
    if legacy.get('invalid_physics',False):
        reasons.append('legacy_invalid_physics')
    return dict(full_episode_completed=not reasons, failure_reasons=reasons,
                expected_duration_s=float(expected_s), expected_steps=steps,
                expected_substeps=steps*800, actual_steps=len(t),
                actual_substeps=len(st), actual_duration_s=float(t[-1]))


def horizon(folder, expected_s):
    execution = read(folder/'execution.json')
    assert sha(folder/'trajectory.npz') == execution['trajectory_sha256']
    assert sha(folder/'substeps.npz') == execution['substeps_sha256']
    with np.load(folder/'trajectory.npz',allow_pickle=False) as z:
        t = z['time']
    with np.load(folder/'substeps.npz',allow_pickle=False) as z:
        result = check_horizon(execution,t,z['time'],z['dt'],read(folder/'legacy.json'),expected_s)
    result['hashes'] = {n:sha(folder/n) for n in ('execution.json','trajectory.npz','substeps.npz','legacy.json')}
    return result


def episode(folder, method, condition, expected_s):
    from audit_special_scene_metrics_20261030 import episode as original_episode
    before = {n:sha(folder/n) for n in ('execution.json','trajectory.npz','substeps.npz','legacy.json')}
    duration = horizon(folder,expected_s)
    row = original_episode(folder,method,condition)
    row['horizon_audit'] = duration
    row['machine_compliant'] = bool(row['machine_compliant'] and duration['full_episode_completed'])
    row['strict_success'] = bool(row['strict_success'] and row['machine_compliant'])
    assert before == {n:sha(folder/n) for n in before}, 'Episode changed during audit'
    return row


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder',type=Path,required=True)
    p.add_argument('--expected-duration-s',type=float,required=True)
    p.add_argument('--method',required=True)
    p.add_argument('--condition',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--horizon-only',action='store_true')
    a = p.parse_args()
    assert not a.output.exists(), 'Preserve previous receipts'
    result = horizon(a.folder,a.expected_duration_s) if a.horizon_only else episode(
        a.folder,a.method,a.condition,a.expected_duration_s)
    write(a.output,dict(status='development_preview_not_final_test',
        auditor_sha256=sha(Path(__file__)),result=result,final_test_performed=False))
