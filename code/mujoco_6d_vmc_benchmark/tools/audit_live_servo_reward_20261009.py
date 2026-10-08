"""Independently audit completed corrected training episodes without stopping jobs.

Check first and latest completed episode per corrected metric job. No simulator,
policy update, final condition access, or use of the training cost helper.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from office_v7_uniform24_20261008 import read, write, sha, now


def audit_episode(row, terms):
    run = Path(row['run'])
    assert sha(run/'rollout.npz') == row['trace_sha256']
    assert sha(run/'AUDIT.json') == row['audit_sha256']
    metadata = read(run/'RL_REWARD_METADATA.json')
    assert metadata['torque_slew_time_base'] == 'executed_motor_torque_changes_at_250Hz_not_physics_dt'
    execution = read(run/'execution.json')
    rates = np.asarray(execution['action_filter_config']['maximum_torque_rate_nmps'])
    with np.load(run/'rollout_metrics/substep_metrics.npz') as data:
        torque = data['qfrc_actuator'].astype(float)
        dt = data['dt'].astype(float)
    # Independent discrete command-increment energy, not the helper used online.
    delta = torque[1:] - torque[:-1]
    ratios = delta / rates / .004
    assert np.max(np.abs(ratios)) <= 1.00001
    costs = np.r_[0., np.einsum('ij,ij->i', delta/rates, delta/rates)/(.004*55.)]
    intervals = read(run/'RL_INTERVALS.json')
    assert intervals[0] is None and len(intervals) == row['steps']+1
    offset = 0
    maximum_error = 0.
    for j, interval in enumerate(intervals[1:]):
        end = offset+interval['substeps']
        value = float(np.sum(costs[offset:end]))
        logged = terms[row['step_before']+j+1]
        np.testing.assert_allclose(value, interval['torque_slew_cost'], rtol=1e-10, atol=1e-10)
        np.testing.assert_allclose(-value, logged['physical_slew'], rtol=1e-10, atol=1e-10)
        maximum_error = max(maximum_error, abs(value-interval['torque_slew_cost']))
        offset = end
    assert offset == len(dt)
    last = terms[row['step_after']]
    remaining_updates = int(np.ceil(max(0., 55.-float(np.sum(dt)))/.004-1e-8))
    failed = not (row['result']['task_success'] and row['result']['strict_success'])
    expected_remaining = -7*remaining_updates*.004/55. if failed else 0.
    np.testing.assert_allclose(expected_remaining, last['physical_slew_failure_continuation'], atol=1e-10)
    native_cost = None
    if (run/'impedance_servo.npz').exists():
        with np.load(run/'impedance_servo.npz') as data:
            servo = data['values']
        durations = np.diff(servo[:, 0])
        np.testing.assert_allclose(durations, .004, atol=1e-9)
        changes = np.diff(servo[:, 20:27], axis=0)/rates
        native_cost = float(np.sum(np.sum(changes**2, axis=1)/durations)/55.)
        np.testing.assert_allclose(costs.sum(), native_cost, rtol=1e-6, atol=1e-10)
    return dict(run=str(run), steps=row['steps'], task=row['result']['task_success'],
        strict=row['result']['strict_success'], substeps=len(dt), duration_s=float(dt.sum()),
        independently_computed_cost=float(costs.sum()), native_servo_cost=native_cost,
        max_servo_slew_ratio=float(np.max(np.abs(ratios))), interval_max_abs_error=maximum_error,
        failure_remaining_cost=-expected_remaining,
        hashes={str(p):sha(p) for p in (run/'RL_INTERVALS.json', run/'rollout_metrics/substep_metrics.npz',
            run/'RL_REWARD_METADATA.json', run/'AUDIT.json')})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    plan = read(a.root/'SERVO_CLOCK_REPAIR_PLAN.json')
    evidence = []
    for item in plan['plans']:
        path = Path(item['continued'])
        if not (path/'execution.json').exists():
            evidence.append(dict(path=str(path), status='not_resumed_yet'))
            continue
        state = read(path/'execution.json')
        rows = [r for r in state['rows'] if 'result' in r]
        if not rows:
            evidence.append(dict(path=str(path), status='no_complete_episode_yet'))
            continue
        selected = [rows[0]] if len(rows) == 1 else [rows[0], rows[-1]]
        terms = {}
        with (path/'training.jsonl').open() as stream:
            for line in stream:
                if not line.endswith('\n'): break
                value = json.loads(line)
                terms[value['step']] = value['terms']
        episodes = [audit_episode(row, terms) for row in selected]
        evidence.append(dict(path=str(path), status='passed', selection='first_and_latest_complete',
            state_steps=state['steps'], state_updates=state['updates'], episodes=episodes))
        print(path.name, path.parent.name, 'passed', len(episodes), flush=True)
    write(a.output, dict(created_utc=now(), source_sha256=sha(__file__), jobs=evidence,
        scope='Sampled completed corrected metric episodes only. Independent servo-clock cost and training-term audit; not a convergence or task-success claim. No new physics or heldout access.'))


if __name__ == '__main__': main()
