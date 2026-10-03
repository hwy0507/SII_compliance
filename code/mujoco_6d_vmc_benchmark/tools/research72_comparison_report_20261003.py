"""Assemble audited final evidence without reopening the sealed manifest.

The planned queue ledger supplies condition identities, not environmental values.
Missing and unaudited runs stay missing; this tool never selects or fits models.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import numpy as np
from research72_final_lock_20261003 import read, sha, verify_lock
from research72_paired_statistics_20261003 import (
    success_summary, crossed_difference, contact_pair_arrays, recovery_summary)

EVENTS = ('ball', 'human', 'rod', 'unknown_edge', 'pillar')
SCALARS = ('rmse_mm', 'position_error_integral_m_s', 'time_above_25mm_s',
           'peak_torque_nm', 'peak_speed_mps', 'absolute_joint_mechanical_work_j')
CONTACT = ('contact_p95_force_n', 'peak_force_n', 'impulse_ns', 'contact_duration_s')


def distribution(values):
    values = [float(x) for x in values if x is not None]
    if not np.isfinite(values).all():
        raise ValueError('Nonfinite observed metric')
    return dict(n=len(values), mean=float(np.mean(values)) if values else None,
                median=float(np.median(values)) if values else None,
                minimum=min(values) if values else None, maximum=max(values) if values else None)


def matrix(records, field, *, full_only=False):
    values = np.full(records.shape, np.nan)
    for index in np.ndindex(records.shape):
        record = records[index]
        if record is not None and (not full_only or record['full_horizon']):
            values[index] = record[field]
    return values


def assemble(candidates, conditions, rows):
    """Pure aggregation. Each row carries one verified physical metric record."""
    if len(set(conditions)) != len(conditions) or not conditions:
        raise ValueError('Duplicate or empty condition axis')
    models = {c['name']: c for c in candidates}
    if len(models) != len(candidates):
        raise ValueError('Duplicate model')
    grouped = defaultdict(list)
    for c in candidates:
        grouped[c['category']].append(c)
    grids = {}; result = {}
    for family, members in sorted(grouped.items()):
        seeds = [c.get('seed') for c in members]
        if len(set(seeds)) != len(seeds) or (None in seeds and len(seeds) != 1):
            raise ValueError('Each selected family requires one model per seed')
        members = sorted(members, key=lambda c: c.get('seed') or -1)
        array = np.empty((len(members), len(conditions)), dtype=object); array.fill(None)
        grids[family] = (members, array)
    seen = set()
    for row in rows:
        key = row['candidate'], row['condition_id']
        if key in seen or key[0] not in models or key[1] not in conditions:
            raise ValueError('Duplicate or unplanned observation')
        seen.add(key)
        c = models[key[0]]; members, array = grids[c['category']]
        if row['category'] != c['category']:
            raise ValueError('Row category differs from locked candidate')
        array[[m['name'] for m in members].index(c['name']), conditions.index(key[1])] = row['metrics']
    for family, (members, array) in grids.items():
        records = [r for r in array.flat if r is not None]
        full = [r for r in records if r['full_horizon']]
        short = [r for r in records if not r['full_horizon']]
        item = dict(models=[m['name'] for m in members], seeds=[m.get('seed') for m in members],
                    task=success_summary(matrix(array, 'task_success')),
                    strict=success_summary(matrix(array, 'strict_success')),
                    full_horizon=len(full), short_horizon=len(short),
                    failed_task_stages=dict(Counter(r['final_stage'] for r in records if not r['task_success'])),
                    aborted=dict(Counter(r['abort_reason'] for r in records if r['abort_reason'])),
                    task_succeeded_but_strict_failed=sum(r['task_success'] and not r['strict_success'] for r in records),
                    full_horizon_metrics={k: distribution(r[k] for r in full) for k in SCALARS},
                    short_horizon_metrics={k: distribution(r[k] for r in short) for k in SCALARS},
                    contacts={}, recovery={})
        for event in EVENTS:
            exposed = [r for r in full if r['contact'][event]['exposure']]
            item['contacts'][event] = dict(observed_full_horizons=len(full), full_horizon_exposed=len(exposed),
                short_horizon_exposed=sum(r['contact'][event]['exposure'] for r in short),
                metrics={k: distribution(r['contact'][event].get(k) for r in exposed) for k in CONTACT})
            if event == 'rod':
                item['contacts'][event]['extended_no_contact_longest_s'] = distribution(
                    r['contact'][event].get('extended_no_contact_longest_s') for r in exposed)
        for event in ('ball', 'human', 'rod'):
            item['recovery'][event] = dict(full_horizon=recovery_summary(full, event),
                                          short_horizon=recovery_summary(short, event))
        result[family] = item
    comparisons = {}
    if 'esn' in grids:
        left_members, left = grids['esn']
        for family, (members, right) in grids.items():
            if family == 'esn':
                continue
            if len(members) > 1 and [c.get('seed') for c in members] != [c.get('seed') for c in left_members]:
                raise ValueError('Learned comparison seed identities differ')
            comparison = {k: crossed_difference(matrix(left, k), matrix(right, k))
                          for k in ('task_success', 'strict_success')}
            comparison['full_horizon_metrics'] = {k: crossed_difference(
                matrix(left, k, full_only=True), matrix(right, k, full_only=True)) for k in SCALARS}
            for statistic in comparison['full_horizon_metrics'].values():
                statistic.update(outcome_conditioned=True, subset='Both trajectories completed the full horizon; success not required')
            comparison['jointly_strict_full_exposed_contacts'] = {}
            for event in EVENTS:
                metrics = CONTACT + (('extended_no_contact_longest_s',) if event == 'rod' else ())
                comparison['jointly_strict_full_exposed_contacts'][event] = {}
                for metric in metrics:
                    a, b, eligible = contact_pair_arrays(left, right, event, metric)
                    comparison['jointly_strict_full_exposed_contacts'][event][metric] = crossed_difference(a, b, eligible=eligible)
            comparisons[family] = comparison
    return dict(families=result, esn_minus_baseline=comparisons, conditions=conditions,
                planned=len(candidates)*len(conditions), audited=len(rows),
                missing_pairs=[dict(candidate=c['name'], condition_id=d) for c in candidates for d in conditions
                               if (c['name'], d) not in seen],
                caveats=['Strict success is primary; task and all failures remain visible.',
                         'Contact differences condition on jointly strict, full, exposed pairs and are not causal claims.',
                         'Force integral is the integral of force magnitude, not signed net impulse.',
                         'Short trajectories are separate; unexposed contact metrics are NA.',
                         'Intervals are exploratory, crossed condition/seed bootstrap, not multiplicity-adjusted.',
                         'No scalar winner score, hardware validation, passivity or human-safety claim.'])


def load_evidence(root, phase, lock_path, lock_digest):
    lock, protocol = verify_lock(root, lock_path, lock_digest)
    receipt = read(root/'FINAL_UNSEAL_RECEIPT.json')
    assert receipt['model_lock_sha256'] == lock_digest
    assert receipt['protocol_sha256'] == sha(root/'PROTOCOL.json')
    assert receipt['sealed_condition_sha256'] == protocol['sealed_condition_sha256']
    assert Path(receipt['output']).resolve() == phase.resolve()
    state = read(phase/'execution.json')
    assert state['model_lock_sha256'] == lock_digest
    assert state['status'] in ('complete', 'deadline_no_new_dispatch', 'failed_preserved')
    candidates = {c['name']: c for c in lock['candidates']}
    plan_path = phase/'PLANNED.json'
    assert sha(plan_path) == state['planned_sha256']
    plan = read(plan_path); assert plan['model_lock_sha256'] == lock_digest
    planned = {(p['candidate'], p['condition_id']) for p in plan['rows']}
    assert len(planned) == len(plan['rows'])
    assert all(p['candidate'] in candidates and p['queue'] in range(4) for p in plan['rows'])
    attempted = set(); collected = []; evidence = [dict(path=str(plan_path), sha256=sha(plan_path))]; engineering = []
    for index in range(4):
        queue = phase/f'queue_{index}'; execution_path = queue/'execution.json'
        expected = {(p['candidate'], p['condition_id']) for p in plan['rows'] if p['queue'] == index}
        if not execution_path.exists():
            engineering.append(dict(queue=index, reason='Queue execution metadata never created', planned_missing=len(expected)))
            continue
        q = read(execution_path)
        assert q['model_lock_sha256'] == lock_digest
        assert q['status'] in ('complete', 'deadline_no_new_dispatch', 'failed_preserved')
        actual = {(p['candidate'], p['condition']) for p in q['planned']}
        assert actual == expected and len(actual) == len(q['planned'])
        analysis = phase/f'queue_{index}_analysis'; audited = {}; metrics_receipt = None
        if (analysis/'execution.json').exists():
            metrics_receipt = read(analysis/'execution.json')
            if metrics_receipt['status'] == 'complete':
                assert metrics_receipt['phase_execution_sha256'] == sha(execution_path)
                independent_path = analysis/'INDEPENDENT_AUDIT.json'
                assert sha(independent_path) == metrics_receipt['outputs']['INDEPENDENT_AUDIT.json']
                independent = read(independent_path)
                assert not independent['pending'] or metrics_receipt.get('allow_partial')
                audited = {str(Path(r['run']).resolve()): r for r in independent['rows']}
                assert len(audited) == len(independent['rows'])
                evidence.append(dict(path=str(independent_path), sha256=sha(independent_path)))
        for row in q['rows']:
            key = row['candidate'], row['condition_id']; assert key in expected
            assert key not in attempted
            attempted.add(key)
            run = queue/row['name']; independent = audited.get(str(run.resolve()))
            if independent is None or 'audit_sha256' not in row or 'trace_sha256' not in row:
                engineering.append(dict(candidate=key[0], condition_id=key[1],
                    reason='Missing completed independent phase audit', returncode=row.get('returncode')))
                continue
            assert independent['frozen_source_hashes_verified'] and independent['actuator_amplitude_and_command_slew_valid']
            assert independent['independent_contact_sidecar_verified']
            assert independent['model_sha256'] == protocol['formal_model_sha256']
            assert independent['audit_sha256'] == row['audit_sha256'] == sha(run/'AUDIT.json')
            candidate = candidates[key[0]]
            if candidate.get('checkpoint'):
                assert independent['checkpoint_sha256'] == candidate['checkpoint_sha256']
                assert independent['actor_replay_performed']
            role = read(run/'FINAL_ROLE.json')
            assert role['test_only'] and role['candidate'] == key[0] and role['condition']['id'] == key[1]
            assert role['model_lock_sha256'] == lock_digest
            assert role['protocol_sha256'] == sha(root/'PROTOCOL.json')
            metric_path = analysis/(row['name']+'.metrics.json')
            assert sha(metric_path) == metrics_receipt['outputs'][metric_path.name]
            metrics = read(metric_path)
            assert metrics['trace_sha256'] == independent['trace_sha256'] == row['trace_sha256']
            assert metrics['model_sha256'] == protocol['formal_model_sha256']
            for field in ('task_success', 'strict_success', 'full_horizon'):
                assert metrics[field] == independent[field]
            for field in ('rmse_mm', 'peak_torque_nm', 'peak_speed_mps'):
                assert abs(metrics[field]-independent[field]) <= 1e-8
            collected.append(dict(candidate=key[0], condition_id=key[1], category=candidate['category'],
                metrics=metrics, run=str(run), metric_sha256=sha(metric_path)))
        evidence.append(dict(path=str(execution_path), sha256=sha(execution_path)))
    conditions = sorted({d for _, d in planned})
    assert len(conditions) == 24
    assert planned == {(c, d) for c in candidates for d in conditions}
    return lock['candidates'], conditions, collected, evidence, engineering


def markdown(report):
    lines = ['# Frozen-model comparison', '',
        f"Audited {report['audited']}/{report['planned']} planned episodes. Missing records remain missing.", '',
        '| Family | Task | Strict | Missing | Full / short | RMSE mm (full mean) | Peak torque Nm (full mean) | Peak speed m/s (full mean) |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    def value(x):
        return 'NA' if x is None else f'{x:.3f}'
    for family, r in report['families'].items():
        n = r['strict']['planned']; s = r['full_horizon_metrics']
        lines.append(f"| {family} | {r['task']['successes']}/{n} | {r['strict']['successes']}/{n} | {r['strict']['missing']} | "
            f"{r['full_horizon']} / {r['short_horizon']} | {value(s['rmse_mm']['mean'])} | "
            f"{value(s['peak_torque_nm']['mean'])} | {value(s['peak_speed_mps']['mean'])} |")
    lines += ['', 'Counts use planned denominators; where missing > 0, these are observed successes, not complete success rates.',
              'JSON includes success-rate bounds, per-seed counts, failure stages, contact exposure, censored recovery and paired intervals.']
    lines += ['', '## ESN minus each baseline: strict success', '',
        'Paired observed cells only. Intervals are exploratory; incomplete pairs do not establish a full planned comparison.', '',
        '| Baseline | Rate difference | 95% crossed interval | Paired cells / planned |',
        '|---|---:|---|---:|']
    for family, comparison in report['esn_minus_baseline'].items():
        statistic = comparison['strict_success']; interval = statistic['ci95']
        interval_text = 'NA' if interval is None else f'[{value(interval[0])}, {value(interval[1])}]'
        lines.append(f"| {family} | {value(statistic['difference'])} | {interval_text} | "
            f"{statistic['paired_cells']}/{statistic['planned_paired_cells']} |")
    for event in EVENTS:
        lines += ['', f'## {event}: exposed full episodes only', '',
            '| Family | Exposed / full | P95 force N (mean) | Force-magnitude integral Ns (mean) | Contact duration s (mean) |',
            '|---|---:|---:|---:|---:|']
        for family, r in report['families'].items():
            c = r['contacts'][event]; m = c['metrics']
            lines.append(f"| {family} | {c['full_horizon_exposed']}/{c['observed_full_horizons']} | "
                f"{value(m['contact_p95_force_n']['mean'])} | {value(m['impulse_ns']['mean'])} | {value(m['contact_duration_s']['mean'])} |")
        lines += ['', 'The descriptive table above includes exposed failures. The following outcome-conditioned pairs require both methods to be strictly successful, full-length and exposed.', '',
            '| Baseline | Paired cells | ESN − baseline P95 N [95% CI] | ESN − baseline force integral Ns [95% CI] |',
            '|---|---:|---|---|']
        def paired_text(statistic):
            interval = statistic['ci95']
            if interval is None:
                return 'NA'
            return f"{value(statistic['difference'])} [{value(interval[0])}, {value(interval[1])}]"
        for family, comparison in report['esn_minus_baseline'].items():
            paired = comparison['jointly_strict_full_exposed_contacts'][event]
            lines.append(f"| {family} | {paired['contact_p95_force_n']['paired_cells']} | "
                f"{paired_text(paired['contact_p95_force_n'])} | {paired_text(paired['impulse_ns'])} |")
    lines += ['', '## Limits', ''] + ['- '+text for text in report['caveats']]
    return '\n'.join(lines)+'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'phase', 'model-lock', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--lock-sha256', required=True)
    args = parser.parse_args()
    candidates, conditions, rows, evidence, engineering = load_evidence(
        args.root.resolve(), args.phase.resolve(), args.model_lock.resolve(), args.lock_sha256)
    report = assemble(candidates, conditions, rows)
    report.update(created_utc=datetime.now(timezone.utc).isoformat(), source_sha256=sha(Path(__file__)),
        model_lock_sha256=args.lock_sha256, evidence=evidence, engineering=engineering,
        raw_rows=rows, metric_versions=sorted({r['metrics']['metric_version'] for r in rows}),
        sealed_manifest_read_by_report=False)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'REPORT.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    (args.output/'MATRIX.md').write_text(markdown(report))
    print(json.dumps(dict(audited=report['audited'], planned=report['planned'], output=str(args.output))))


if __name__ == '__main__':
    main()
