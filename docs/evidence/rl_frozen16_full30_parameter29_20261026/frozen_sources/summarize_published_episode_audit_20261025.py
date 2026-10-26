"""Recompute physical metrics from observational evaluation audit substeps.

Creates one comparison row, including failures and no-contact NA semantics.
This verifies telemetry alignment and metrics, not independent filter replay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(folder, method, case_id):
    terminal = json.loads((folder/'TERMINAL.json').read_text())
    result = json.loads((folder/'rollout.json').read_text())
    extension = json.loads((folder/'AUDIT_EXTENSION.json').read_text())
    adapter = json.loads((folder/'ADAPTER.json').read_text())
    if not extension['completed'] or extension['base_adapter_sha256'] != adapter['adapter_file_sha256']:
        raise ValueError('Incomplete or mismatched observational audit')
    if terminal['model_sha256'] != sha(folder/'rollout.mjb'):
        raise ValueError('Physical model hash mismatch')
    if extension['substeps_sha256'] != sha(folder/'audit_substeps.npy'):
        raise ValueError('Audit trace hash mismatch')
    data = np.load(folder/'audit_substeps.npy', mmap_mode='r', allow_pickle=False)
    count = extension['samples']
    if not 0 < count <= len(data):
        raise ValueError('Invalid physical sample count')
    data = data[:count]
    if data.shape != (count, 11) or not np.isfinite(data).all():
        raise ValueError('Nonfinite or malformed physical telemetry')
    dt, torque, force, penetration, time = data[:, 0], data[:, 1:8], data[:, 8], data[:, 9], data[:, 10]
    if not np.all(dt == .00005) or np.any(force < 0) or np.any(penetration < 0):
        raise ValueError('Physical timestep or nonnegative telemetry violated')
    with np.load(folder/'rollout_metrics/substep_metrics.npz', allow_pickle=False) as archived:
        if not np.array_equal(dt, archived['dt']) or not np.array_equal(time, archived['time']):
            raise ValueError('Audit and original physical sample clocks differ')
        if not np.array_equal(torque.astype(np.float32), archived['qfrc_actuator']):
            raise ValueError('Coincident torque differs from original substep metrics')
    limits = np.asarray(extension['actuator_limits_nm'])
    if limits.shape != (7,) or np.any(limits <= 0):
        raise ValueError('Invalid frozen actuator limits')
    thresholds = .5*limits
    active = force > .05
    compliant = np.all(abs(torque) <= thresholds, axis=1)
    contact_s = float(dt[active].sum())
    below_s = float(dt[active & compliant].sum())
    peaks = abs(torque).max(axis=0)
    elapsed = float(dt.sum())
    journal = [json.loads(line) for line in (folder/'actor_intervals.jsonl').read_text().splitlines()]
    intervals = [row['interval'] for row in journal if row['interval'] is not None]+[terminal['interval']]
    errors = dict(
        elapsed_abs_s=abs(sum(row['elapsed_s'] for row in intervals)-elapsed),
        contact_abs_s=abs(sum(row['spt_contact']['human_contact_s'] for row in intervals)-contact_s),
        compliant_abs_s=abs(sum(row['spt_contact']['human_compliant_s'] for row in intervals)-below_s),
        peak_torque_abs_nm=float(np.max(abs(peaks-np.asarray(result['metrics']['generalized_actuator_torque_peak_by_joint_nm'])))),
        penetration_abs_m=abs(float(penetration.max())-result['stats']['max_external_penetration_m']))
    if max(errors.values()) > 1e-8 or abs(terminal['terminal_time_s']-elapsed) > 2e-6:
        raise ValueError('Original aggregates disagree with independent physical audit: '+str(errors))
    with np.load(folder/'rollout.npz', allow_pickle=False) as trace:
        if not np.array_equal(np.asarray([row['observation'] for row in journal]), trace['observation']):
            raise ValueError('Actor observations differ from the canonical trace')
        if not np.array_equal(np.asarray([row['executed_action'] for row in journal]), trace['applied_action']):
            raise ValueError('Controller actions differ from recorded execution')
    safety = bool(not result['physical_valid'] or result['abort_reason'] is not None
        or np.any(peaks > limits+1e-8) or not result.get('unexpected_edge_safe', True))
    row = dict(method=method, case_id=case_id, task_success=result['task_success'],
        strict_success=result['strict_success'], full_horizon=result['full_task_horizon_completed'],
        machine_safety_violation=safety, elapsed_s=elapsed,
        completion_time_s=terminal['completion_time_s'],
        completion_time_definition=terminal['completion_definition'], torque_thresholds_nm=thresholds.tolist(),
        peak_torque_nm_per_joint=peaks.tolist(), human_contact_s=contact_s, human_below_threshold_s=below_s,
        human_compliance_ratio=below_s/contact_s if contact_s else None,
        final_task_stage=result['final_task_stage'], abort_reason=result['abort_reason'])
    return dict(row=row, scope='physical_telemetry_and_metric_alignment',
        filter_replay_verified=False, actor_input_and_executed_action_trace_equal=True,
        samples=count, engineering_contact_force_onset_n=.05,
        threshold_status='engineering_reference_not_validated_human_comfort',
        aggregate_errors=errors,
        source_sha256=sha(Path(__file__)),
        evidence_sha256={name: sha(folder/name) for name in ['TERMINAL.json', 'rollout.json',
            'rollout.mjb', 'rollout.npz', 'audit_substeps.npy', 'AUDIT_EXTENSION.json', 'actor_intervals.jsonl',
            'rollout_metrics/substep_metrics.npz']})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--episode', type=Path, required=True)
    parser.add_argument('--method', required=True)
    parser.add_argument('--case-id', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = summarize(args.episode, args.method, args.case_id)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(report['row'], indent=2))
