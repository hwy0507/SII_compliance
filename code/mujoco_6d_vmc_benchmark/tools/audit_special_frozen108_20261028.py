"""Independent saved-evidence and six-metric audit of the new frozen108.

Does not integrate dynamics again or certify human comfort. All failures remain
in success/safety/torque denominators. SPT uses only BOTH-success episodes.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path

import numpy as np

from prepare_special_frozen_test_20261028 import read, sha, require, manifest


def equal(actual, expected, label):
    if actual is None or expected is None:
        require(actual is expected, label)
    else:
        require(math.isfinite(actual) and math.isfinite(expected)
                and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10), label)


def verify_episode(row, model, condition, root, source, parent, verified_sources):
    run = Path(row['run'])
    require(run == root / 'evaluation' / (row['method'] + '__' + row['condition']), 'Wrong episode path')
    for key, filename in (
        ('audit_sha256', 'AUDIT.json'), ('trace_sha256', 'rollout.npz'),
        ('model_sha256', 'rollout.mjb'), ('execution_sha256', 'execution.json'),
        ('chain_sha256', 'execution_chain.npz'),
        ('substep_metrics_sha256', 'rollout_metrics/substep_metrics.npz'),
        ('research_substeps_sha256', 'research_substeps.npz')):
        require(sha(run / filename) == row[key], 'Changed physical evidence: ' + filename)
    metric_file = root / 'metrics' / (row['method'] + '__' + row['condition'] + '.json')
    require(sha(metric_file) == row['metric_sha256'], 'Changed metric receipt')
    metric, execution, audit, summary = [read(p) for p in (
        metric_file, run / 'execution.json', run / 'AUDIT.json', run / 'rollout.json')]
    require(execution['status'] == 'complete', 'Incomplete physical execution')
    require(sha(run / 'checkpoint.npz') == execution['checkpoint_sha256'] == model['checkpoint_sha256'], 'Wrong model checkpoint')
    require(sha(root / 'configs' / (row['method'] + '__' + row['condition'] + '.json')) == execution['config_sha256'], 'Config changed')
    provenance = execution['runtime_provenance']
    require(provenance['research_condition'] == condition and provenance['physics_dt_s'] == .00005, 'Condition/clock changed')
    require(provenance['research_protocol_sha256'] == parent['protocol_sha256'], 'Protocol changed')
    require(provenance['condition_file_sha256'] == parent['condition_sha256'], 'Condition population changed')
    require(execution['python'] == parent['simulation_python'] and execution['mujoco'] == '3.11.0', 'Runtime changed')
    require(row['model_sha256'] == parent['formal_model_sha256'], 'Wrong formal MJB')
    require(audit['actor_replay_performed'] and audit['action_replay_max_abs'] == 0
            and audit['common_filter_replay_max_abs'] == 0, 'Actor/filter replay did not pass')
    for field in ('task_success', 'strict_success'):
        require(row[field] == audit[field] == metric[field] == summary[field], 'Success flag mismatch')
    for name, digest in execution['source_sha256'].items():
        if (name, digest) not in verified_sources:
            require(sha(source / name) == digest, 'Physical source changed: ' + name)
            verified_sources.add((name, digest))
    require(metric['metric_source_sha256'] == sha(source / 'tools/paper_metrics_20261002.py'), 'Metric source changed')
    channels = read(run / 'research_channels.json')
    require(channels['telemetry_sha256'] == row['research_substeps_sha256']
            and channels['force_columns'][2] == 'human_robot_sum', 'Wrong contact channel')
    with np.load(run / 'rollout.npz', allow_pickle=False) as z:
        time = z['time'].copy()
    require(np.isfinite(time).all() and np.allclose(np.diff(time), .04, rtol=0, atol=1e-8), 'Invalid actor clock')
    completion = None
    if row['task_success']:
        hold = int(round(summary['placement_hold_s'] / .04))
        require(13 <= hold <= len(time), 'Task success missing terminal hold evidence')
        completion = float(time[len(time) - hold + 12])
    equal(row['completion_time_s'], completion, 'Completion time mismatch')
    with np.load(run / 'rollout_metrics/substep_metrics.npz', allow_pickle=False) as z:
        dt, torque, error, twist = [z[k].astype(float) for k in ('dt', 'qfrc_actuator', 'error', 'twist')]
    with np.load(run / 'research_substeps.npz', allow_pickle=False) as z:
        force = z['contact_force_sum'][:, 2].astype(float)
        penetration = 1000 * np.maximum(z['external_penetration_m'], z['edge_penetration_m'])
    require(len(dt) > 0 and all(len(v) == len(dt) for v in (torque, error, twist, force, penetration)), 'Substeps not aligned')
    require(all(np.isfinite(v).all() for v in (dt, torque, error, twist, force, penetration)), 'Nonfinite telemetry needs explicit failure review')
    require(np.allclose(dt, .00005, rtol=0, atol=1e-12), 'Physical dt mismatch')
    torque = np.abs(torque[:, :7])
    threshold = np.array([43.5] * 4 + [6.] * 3)
    contact = force > .05
    within = np.all(torque <= threshold * (1 + 1e-6), axis=1)
    duration = float(dt[contact].sum())
    comfort = float(dt[contact & within].sum() / duration) if duration else None
    c = row['comfort']
    np.testing.assert_array_equal(c['comfort_threshold_nm'], threshold)
    equal(c['comfort_threshold_ratio_of_actuator_limit'], .5, 'Comfort ratio changed')
    equal(c['human_force_threshold_n'], .05, 'Contact threshold changed')
    equal(c['human_contact_duration_s'], duration, 'Contact duration mismatch')
    equal(c['human_comfort_torque_compliance'], comfort, 'Comfort ratio mismatch')
    peak = float(torque.max())
    equal(row['peak_torque_nm'], peak, 'Raw peak torque mismatch')
    equal(c['max_penetration_mm'], float(penetration.max()), 'Penetration mismatch')
    rmse = float(1000 * np.sqrt(np.sum(np.sum(error**2, axis=1) * dt) / dt.sum()))
    speed = float(np.linalg.norm(twist[:, :3], axis=1).max())
    equal(metric['rmse_mm'], rmse, 'RMSE mismatch')
    equal(metric['peak_speed_mps'], speed, 'Peak speed mismatch')
    equal(row['duration_s'], float(dt.sum()), 'Episode duration mismatch')
    reasons = []
    if penetration.max() > .2 + 1e-12:
        reasons.append('penetration_gt_0.2mm')
    if np.max(torque / (2 * threshold)) > 1 + 1e-6:
        reasons.append('actuator_torque_gt_limit')
    if summary.get('abort_reason'):
        reasons.append('episode_abort:' + summary['abort_reason'])
    require(reasons == c['machine_safety_violation_reasons'] and bool(reasons) == c['machine_safety_violation'], 'Machine compliance mismatch')
    return dict(method=row['method'], condition=row['condition'], substeps=len(dt),
                rmse_mm=rmse, peak_speed_mps=speed, peak_torque_nm=peak,
                human_force_peak_n=float(force.max()), human_contact_impulse_ns=float(np.sum(force[contact] * dt[contact])),
                comfort_exceed_duration_s=float(dt[contact & ~within].sum()),
                failure_stage=audit.get('stage') if not row['task_success'] else None,
                abort_reason=summary.get('abort_reason'))


def summaries(rows, models):
    successes = [r for r in rows if r['task_success'] and r['strict_success']]
    require(all(r['completion_time_s'] is not None and math.isfinite(r['completion_time_s'])
                and r['completion_time_s'] > 0 for r in successes), 'Missing/invalid BOTH completion time')
    ref = min((r['completion_time_s'] for r in successes), default=None)
    methods = {}
    for name in models:
        group = [r for r in rows if r['method'] == name]
        both = [r for r in group if r['task_success'] and r['strict_success']]
        contact = sum(r['comfort']['human_contact_duration_s'] for r in group)
        mass = sum((r['comfort']['human_comfort_torque_compliance'] or 0)
                   * r['comfort']['human_contact_duration_s'] for r in group)
        methods[name] = dict(episodes=len(group), task_success=sum(r['task_success'] for r in group),
            strict_success=sum(r['strict_success'] for r in group), both_success=len(both),
            task_success_rate=sum(r['task_success'] for r in group)/len(group),
            strict_success_rate=sum(r['strict_success'] for r in group)/len(group),
            spt_mean=float(np.mean([ref / max(ref, r['completion_time_s']) for r in both])) if both else None,
            spt_valid_episodes=len(both), spt_missing_time_episodes=0,
            peak_torque_mean_nm=float(np.mean([r['peak_torque_nm'] for r in group])),
            human_comfort_torque_compliance_contact_time_weighted=mass/contact if contact else None,
            human_contact_duration_s_total=contact,
            machine_compliance_rate=sum(not r['comfort']['machine_safety_violation'] for r in group)/len(group))
    fields = ('task_success_rate', 'strict_success_rate', 'spt_mean', 'peak_torque_mean_nm',
              'human_comfort_torque_compliance_contact_time_weighted', 'machine_compliance_rate')
    families = {}
    for family in sorted({m['family'] for m in models.values()}):
        members = sorted((m for m in models.values() if m['family'] == family), key=lambda m: m['seed'])
        families[family] = {}
        for field in fields:
            values = [methods[m['name']][field] for m in members]
            valid = all(v is not None for v in values)
            families[family][field] = dict(seeds=[m['seed'] for m in members], per_seed=values,
                mean=float(np.mean(values)) if valid else None,
                sample_sd=float(np.std(values, ddof=1)) if valid and len(values)>1 else None)
    return ref, methods, families


def audit(preparation):
    plan = read(preparation / 'REGISTRATION.json')
    done = read(preparation / 'execution.json')
    require(done['status'] == 'evaluation_complete_pending_independent_audit', 'Dispatch incomplete')
    require(done['registration_sha256'] == sha(preparation / 'REGISTRATION.json'), 'Preparation changed')
    require(manifest(preparation / 'tools') == plan['tools_sha256'], 'Prepared source changed')
    root, training, parent_root = [Path(plan[k]) for k in ('evaluation', 'training', 'source_run')]
    for path, digest in plan['input_hashes'].items():
        require(sha(Path(path)) == digest, 'Changed pinned input')
    require(manifest(root / 'source') == plan['physics_source_sha256'], 'Evaluation physics source drift')
    require(sha(root / 'coordinator.py') == plan['tools_sha256']['run_nonrl_spt_matrix_20261025.py'], 'Wrong coordinator')
    fit_audit = read(preparation / 'FIT_AUDIT.json')
    require(sha(preparation / 'FIT_AUDIT.json') == done['fit_audit_sha256'] and fit_audit['status'] == 'passed', 'Missing fit audit')
    lock_sha = sha(training / 'MODEL_LOCK.json')
    require(lock_sha == fit_audit['model_lock_sha256'] == sha(root / 'INPUT_MODEL_LOCK.json'), 'Model lock mismatch')
    lock = read(root / 'INPUT_MODEL_LOCK.json')
    require(sha(training / 'data/training_data.npz') == fit_audit['dataset_sha256']
            == lock['training_data_sha256'], 'Training data changed after fitting audit')
    models = {m['name']: m for m in lock['models']}
    require(len(lock['models']) == len(models) == 9, 'Nine distinct selected models required')
    for model in models.values():
        require(sha(Path(model['checkpoint'])) == model['checkpoint_sha256']
                and sha(Path(model['metadata'])) == model['metadata_sha256'], 'Selected fitting evidence changed')
    require(Counter((m['family'], m['seed']) for m in models.values()) == Counter({(f,s):1 for f in
        ('esn_ridge','mlp_scratch','rnn_scratch') for s in (2026102801,2026102802,2026102803)}), 'Model family/seed coverage')
    state, report, registration = [read(root / n) for n in ('execution.json', 'REPORT.json', 'REGISTRATION.json')]
    require(state['status'] == report['status'] == 'complete' and state['completed'] == state['expected'] == 108, 'Matrix incomplete')
    require(state['report_sha256'] == done['report_sha256'] == sha(root / 'REPORT.json'), 'Report changed')
    require(report['registration_sha256'] == sha(root / 'REGISTRATION.json'), 'Test registration changed')
    require(registration['model_lock_sha256'] == lock_sha, 'Test used another model lock')
    conditions = {c['id']: c for c in read(parent_root / 'CONDITIONS.json')['conditions']}
    require(set(conditions) == set(plan['conditions']) and len(conditions) == 12, 'Changed12 conditions')
    require(sha(root / 'CONDITIONS.json') == sha(parent_root / 'CONDITIONS.json'), 'Condition snapshot changed')
    rows = report['rows']
    require(len(rows) == 108 and Counter((r['method'],r['condition']) for r in rows) ==
            Counter({(m,c):1 for m in models for c in conditions}), 'Missing/duplicate matrix cells')
    parent = read(parent_root / 'REGISTRATION.json')
    parent['formal_model_sha256'] = read(parent_root / 'PROTOCOL.json')['formal_model_sha256']
    verified = set()
    checks = [verify_episode(r, models[r['method']], conditions[r['condition']], root,
                            root / 'source', parent, verified) for r in rows]
    ref, methods, families = summaries(rows, models)
    equal(report['t_ref_s'], ref, 'Global T_ref mismatch')
    for r in rows:
        expected = ref/max(ref,r['completion_time_s']) if r['task_success'] and r['strict_success'] else None
        equal(r['spt'], expected, 'Row SPT mismatch')
    require(len(report['methods']) == 9 and {m['method'] for m in report['methods']} == set(models), 'Aggregate coverage')
    for method in report['methods']:
        for field, expected in methods[method['method']].items():
            equal(method[field], expected, 'Aggregate mismatch: ' + field)
    return dict(status='frozen108_saved_evidence_audit_passed', created_utc=datetime.now(timezone.utc).isoformat(),
        preparation=str(preparation), report_sha256=sha(root / 'REPORT.json'), model_lock_sha256=lock_sha,
        auditor_sha256=sha(Path(__file__)), verified_episodes=108, t_ref_s=ref,
        methods=methods, family_summary=families, episode_checks=checks,
        limitation='Saved-substep arithmetic, evidence hashes, original actor/filter audit receipts and six-metric denominators verified; no independent dynamics reintegration. Current12 previously inspected. Comfort is an engineering proxy. Family means/SD use three seed-level values; any NA remains NA.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Preserve previous audit')
    result = audit(args.preparation.resolve())
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(status=result['status'], episodes=result['verified_episodes'])))
