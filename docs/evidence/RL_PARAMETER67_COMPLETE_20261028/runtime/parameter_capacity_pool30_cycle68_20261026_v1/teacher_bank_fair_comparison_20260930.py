"""Export frozen closeout evidence, keeping task and exposure outcomes separate.

Only JSON snapshots are read. No live run, simulator, or NPZ access. Locked
scores require a certified bank; paired summaries retain physical/task failures.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def boolean(value):
    return value if isinstance(value, bool) else 'unknown'


def numeric(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def measured_duration(rollout):
    metrics = rollout.get('metrics', {})
    counts = metrics.get('timestep_sample_counts')
    if isinstance(counts, dict) and counts:
        try:
            values = [(float(dt), count) for dt, count in counts.items()]
            if all(math.isfinite(dt) and dt > 0 and isinstance(count, int)
                   and not isinstance(count, bool) and count > 0 for dt, count in values):
                return sum(dt*count for dt, count in values)
        except (TypeError, ValueError):
            pass
    return None


def outcome(audit, rollout, audit_key, rollout_key):
    a, b = boolean(audit.get(audit_key)), boolean(rollout.get(rollout_key))
    if a == 'unknown' or b == 'unknown':
        return 'unknown', 'missing_explicit_'+audit_key
    if a != b:
        return 'unknown', 'audit_rollout_'+audit_key+'_disagree'
    return a, None


def export(review_dir, output, expected_review_sha256):
    review_dir, output = Path(review_dir).resolve(), Path(output).resolve()
    if output.exists() or output == review_dir or review_dir in output.parents:
        raise ValueError('Output must be new and outside frozen review')
    path = review_dir/'review.json'
    if sha(path) != expected_review_sha256:
        raise ValueError('Review SHA256 mismatch')
    review = json.loads(path.read_text())
    snapshot = review_dir/'metadata_snapshot'
    hashes = review['metadata_sha256']
    read_hashes = {}

    def read(name, default=None):
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe metadata path')
        target = snapshot/relative
        if name not in hashes:
            return default
        if not target.is_file() or target.is_symlink() or sha(target) != hashes[name]:
            raise ValueError('Snapshot SHA mismatch: '+name)
        read_hashes[name] = hashes[name]
        return json.loads(target.read_text())

    plan, fixtures = read('plan.json'), read('fixtures.json')
    methods = plan['methods']
    expected_duration = numeric(plan.get('duration_s'))
    locked = review['closeout'].get('bank_certified_locked') is True
    scopes, selected_configs = {}, {}
    if locked:
        for key, group in review['closeout']['reconstructed_groups'].items():
            best = group['best_complete_candidate']
            selected_configs[key] = dict(x=best['x'], teacher=group['selected_controller_config'])
            candidate = next(c for c in group['candidates'] if c['index'] == best['index'])
            for anchor in candidate['anchors']:
                scopes[anchor['folder']] = 'train_search_anchors'
    preregistered_validation = set()
    for category in plan['categories']:
        subset = [f for f in fixtures if f['category'] == category and f['split'] == 'validation']
        for index in plan.get('validation_indices', []):
            if 0 <= index < len(subset):
                preregistered_validation.add(subset[index]['id'])
    rows = []
    for attempt in review['status']['attempts']:
        folder = attempt['folder']
        request = read(folder+'/request.json', {})
        execution = read(folder+'/execution.json', {})
        audit = read(folder+'/audit.json', {})
        rollout = read(folder+'/rollout.json', {})
        fixture = request.get('fixture', {})
        key = fixture.get('category', 'unknown')+'/'+request.get('method', 'unknown')
        task, task_error = outcome(audit, rollout, 'task', 'task_success')
        strict, strict_error = outcome(audit, rollout, 'strict', 'strict_success')
        scope = scopes.get(folder, 'excluded')
        if locked and request.get('phase') == 'validation' and fixture.get('id') in preregistered_validation:
            scope = 'preregistered_validation'
        if locked and request.get('phase') == 'collection':
            scope = 'collection'
        config = selected_configs.get(key)
        params_match = bool(config and request.get('x') == config['x'] and request.get('teacher') == config['teacher'])
        errors = [e for e in (task_error, strict_error) if e]
        if not locked:
            errors.append('bank_not_certified_locked')
        if scope != 'excluded' and not params_match:
            errors.append('parameters_differ_from_locked_bank'); scope = 'excluded'
        if request.get('phase') in ('validation', 'collection'):
            post = next((r for r in review['closeout']['post_selection_attempts'] if r['folder'] == folder), None)
            if not post or not post['verified_locked_parameters']:
                errors.append('post_selection_execution_not_verified'); scope = 'excluded'
        duration = measured_duration(rollout)
        full = boolean(rollout.get('full_task_horizon_completed'))
        execution_complete = boolean(rollout.get('execution_complete'))
        abort = rollout.get('abort_reason', 'unknown')
        completed = (execution.get('status') == 'completed' and execution.get('returncode') == 0
                     and attempt['status'] in ('eligible', 'physical_failure'))
        duration_ok = bool(completed and full is True and execution_complete is True and abort is None
            and duration is not None and expected_duration is not None and abs(duration-expected_duration) <= 1e-6)
        row = dict(folder=folder, fixture_id=fixture.get('id', 'unknown'), category=fixture.get('category', 'unknown'),
            method=request.get('method', 'unknown'), phase=request.get('phase', 'unknown'), split=fixture.get('split', 'unknown'),
            scope=scope, matches_locked_parameters=params_match, execution_status=execution.get('status', 'unknown'),
            completed_execution=completed, task=task, strict=strict,
            exposure=boolean(audit.get('exposure', {}).get('passed')), eligible=boolean(audit.get('eligible')),
            physical_valid=boolean(rollout.get('physical_valid')), full_duration=full,
            execution_complete=execution_complete, abort=abort if abort is not None else 'none',
            measured_duration_s=duration, same_full_duration=duration_ok,
            model_sha256=audit.get('model_sha256', 'unknown'), pair_state='excluded',
            paired_metric_episode=False, metric_exclusion_reason='not_in_locked_paired_fixture',
            rmse_m=numeric(audit.get('rmse_m')), peak_torque_nm=numeric(audit.get('peak_torque_nm')),
            peak_speed_mps=numeric(audit.get('peak_speed_mps')),
            failure_reasons=json.dumps(audit.get('failure_reasons', [])), evidence_errors=';'.join(errors))
        # Metrics are explicit saved audit values; corroborate saved evaluator
        # metrics without decoding trajectories. Missing/mismatch stays unknown.
        metric_keys = {'rmse_m':'position_rmse_3d_m', 'peak_torque_nm':'generalized_actuator_torque_peak_nm',
                       'peak_speed_mps':'linear_speed_peak_mps'}
        for name, raw_name in metric_keys.items():
            corroborating = numeric(rollout.get('metrics', {}).get(raw_name))
            value = row[name]
            if value is None or corroborating is None or not math.isclose(value, corroborating, rel_tol=2e-7, abs_tol=1e-8):
                row[name] = None
                row['evidence_errors'] += ';missing_or_mismatched_'+name
        rows.append(row)
    pairing = defaultdict(list)
    for row in rows:
        if row['scope'] != 'excluded':
            pairing[(row['scope'], row['category'], row['fixture_id'])].append(row)
    pairs = []
    for (scope, category, fixture), members in sorted(pairing.items()):
        present = [r['method'] for r in members]
        reasons = []
        if sorted(present) != sorted(methods): reasons.append('missing_or_duplicate_method')
        if not all(r['completed_execution'] for r in members): reasons.append('incomplete_execution')
        models = {r['model_sha256'] for r in members}
        if len(models) != 1 or 'unknown' in models: reasons.append('compiled_model_metadata_mismatch_or_missing')
        paired = not reasons
        metric_errors = []
        if not paired:
            metric_errors.append('not_complete_matched_method_model_pair')
        if not all(r['same_full_duration'] for r in members):
            metric_errors.append('not_same_full_duration_all_methods')
        missing_metrics = [r['method']+':'+metric for r in members
            for metric in ('rmse_m', 'peak_torque_nm', 'peak_speed_mps') if r[metric] is None]
        if missing_metrics:
            metric_errors.append('missing_or_unverified_metric_in_pair:'+','.join(missing_metrics))
        metric_pair = not metric_errors
        for row in members:
            row['pair_state'] = 'paired' if paired else ';'.join(reasons)
            row['paired_metric_episode'] = metric_pair
            row['metric_exclusion_reason'] = ';'.join(metric_errors)
        pairs.append(dict(scope=scope, category=category, fixture_id=fixture, paired=paired,
            same_full_duration_all_methods=all(r['same_full_duration'] for r in members),
            all_three_metrics_verified_for_all_methods=not missing_metrics,
            paired_metric_episode=metric_pair, metric_exclusion_reasons=metric_errors,
            errors=reasons, folders=[r['folder'] for r in members]))
    summaries = []
    if locked:
        for scope in ('train_search_anchors', 'preregistered_validation', 'collection'):
            for category in plan['categories']:
                for method in methods:
                    selected = [r for r in rows if r['scope'] == scope and r['category'] == category and r['method'] == method]
                    paired = [r for r in selected if r['pair_state'] == 'paired']
                    summary = dict(scope=scope, category=category, method=method,
                        selected_attempts=len(selected), paired_episodes=len(paired),
                        unpaired_attempts=len(selected)-len(paired),
                        same_full_duration_metric_episodes=sum(r['paired_metric_episode'] for r in paired))
                    for flag in ('task', 'strict', 'exposure', 'eligible', 'physical_valid', 'full_duration'):
                        for value in (True, False, 'unknown'):
                            summary[flag+'_'+str(value).lower()] = sum(r[flag] == value for r in paired)
                    summary['abort_none'] = sum(r['abort'] == 'none' for r in paired)
                    summary['abort_unknown'] = sum(r['abort'] == 'unknown' for r in paired)
                    summary['abort_present'] = sum(r['abort'] not in ('none', 'unknown') for r in paired)
                    for metric in ('rmse_m', 'peak_torque_nm', 'peak_speed_mps'):
                        values = [r[metric] for r in paired if r['paired_metric_episode'] and r[metric] is not None]
                        summary[metric+'_n'] = len(values)
                        summary[metric+'_mean'] = sum(values)/len(values) if values else None
                        summary[metric+'_max'] = max(values) if values else None
                    summaries.append(summary)
    result = dict(scope='Frozen metadata comparison; no trajectories or live run read',
        input_review_sha256=expected_review_sha256, snapshot_files_verified=read_hashes,
        script_sha256=sha(Path(__file__)), bank_certified_locked=locked,
        locked_results_refused_reason=None if locked else 'bank_not_certified_locked',
        definitions=len(fixtures), defined_train=sum(f['split'] == 'train' for f in fixtures),
        defined_validation=sum(f['split'] == 'validation' for f in fixtures),
        recorded_attempts=len(rows), completed_executions=sum(r['completed_execution'] for r in rows),
        unique_executed_fixture_ids=len({r['fixture_id'] for r in rows if r['completed_execution']}),
        expected_duration_s=expected_duration, rows=rows, pairing=pairs, method_summary=summaries,
        summary_semantics='Task/contact counts use matched method/model fixture sets. All three metric aggregates use one common fixture set: all paired methods must have the same full horizon and all three metrics explicitly verified. One missing or mismatched metric excludes the whole fixture from every method\'s metric aggregates, while retaining task/contact counts and raw unknowns; metric_exclusion_reason explains the exclusion. Successful and failed full episodes remain included when evidence is complete. Fixed locked parameters only; training anchors are training performance, not held-out validation.')
    output.mkdir(parents=True)
    (output/'comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    def write_csv(name, values, fallback):
        with (output/name).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(values[0]) if values else fallback)
            writer.writeheader(); writer.writerows(values)
    write_csv('all_attempts.csv', rows, ['folder', 'scope', 'task', 'strict', 'exposure', 'eligible'])
    write_csv('method_summary.csv', summaries, ['scope', 'category', 'method', 'paired_episodes'])
    write_csv('partial_or_excluded.csv', [r for r in rows if r['pair_state'] != 'paired'], ['folder', 'pair_state'])
    write_csv('retained_failures.csv', [r for r in rows if any(r[k] is False for k in ('task', 'strict', 'exposure', 'eligible'))
                                     or not r['completed_execution']], ['folder', 'task', 'eligible'])
    lines = ['# Frozen fair comparison', '',
        f'Defined fixtures: {len(fixtures)}. Recorded attempts: {len(rows)}. Completed executions: {result["completed_executions"]}.', '',
        'Locked bank verified: '+str(locked)+'.', '']
    if not locked:
        lines.append('Locked-policy results refused: bank_not_certified_locked. CSV retains audit details, not fixed-policy performance.')
    else:
        lines += ['| Scope / category / method | Paired n | Task T/F/? | Strict T/F/? | Exposure T/F/? | Eligible T/F/? | Physical valid T/F/? | Full duration T/F/? | Abort none/present/? | Full-horizon metric n | RMSE mean/max (m) | Torque mean/max (Nm) | Speed mean/max (m/s) |',
                  '|---|---:|---|---|---|---|---|---|---|---:|---|---|---|']
        for row in summaries:
            fields = [f'{row["scope"]}/{row["category"]}/{row["method"]}', str(row['paired_episodes'])]
            fields += ['/'.join(str(row[flag+'_'+v]) for v in ('true','false','unknown')) for flag in ('task','strict','exposure','eligible','physical_valid','full_duration')]
            fields += ['/'.join(str(row['abort_'+v]) for v in ('none','present','unknown'))]
            fields += [str(row['same_full_duration_metric_episodes'])]
            fields += ['/'.join('unknown' if row[metric+'_'+stat] is None else f'{row[metric+"_"+stat]:.6g}' for stat in ('mean','max'))
                       for metric in ('rmse_m','peak_torque_nm','peak_speed_mps')]
            lines.append('| '+' | '.join(fields)+' |')
    lines += ['', result['summary_semantics'], '', 'Physical validity, full duration, execution completion, abort reason, measured duration and all failures are explicit in all_attempts.csv. Missing outcome metadata is unknown, never inferred from failure labels.']
    (output/'comparison.md').write_text('\n'.join(lines)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--review-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = export(args.review, args.output, args.review_sha256)
    print(json.dumps(dict(output=str(args.output), locked=result['bank_certified_locked'],
        locked_summary_rows=len(result['method_summary']), attempts=result['recorded_attempts'])))


if __name__ == '__main__':
    main()
