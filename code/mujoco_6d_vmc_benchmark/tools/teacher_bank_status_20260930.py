"""Read-only campaign accounting. No simulation, network, or validation dispatch.

Only metadata of already executed attempts is examined. Report destinations
must be outside the campaign tree, and existing reports are never overwritten.
Large trajectory hashes are reported from audits, not silently revalidated.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import statistics
import sys
import time


METRICS = ('rmse_m', 'peak_torque_nm', 'peak_speed_mps', 'penetration_mm',
           'completion_proxy_retreat_s', 'action_delta_rms')
PRUNE = {'source', 'metadata', 'final_reports', 'archive_receipts', 'recovery_records'}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    with Path(path).open() as stream:
        return json.load(stream, parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError('Nonfinite JSON number: ' + value)))


def process_status(execution):
    """Read-only live evidence; remote-host records are never called confirmed."""
    if execution.get('host') != socket.gethostname():
        return 'running_unverified_host'
    pid = execution.get('pid')
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return 'running_unverified_identity'
    path = Path('/proc') / str(pid)
    try:
        fields = (path/'stat').read_text().rsplit(')', 1)[1].split()
        argv = [v.decode(errors='surrogateescape') for v in (path/'cmdline').read_bytes().split(b'\0') if v]
        boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        if fields[0] in ('Z', 'X'):
            return 'stale_running'
        saved = execution.get('process_identity')
        if saved and (saved.get('start_ticks') != int(fields[19]) or saved.get('boot_id') != boot):
            return 'stale_running_pid_reused'
        if argv != execution.get('command'):
            return 'running_unverified_identity' if saved else 'stale_running_pid_reused'
        return 'running_confirmed'
    except FileNotFoundError:
        return 'stale_running' if not path.exists() else 'running_unverified_identity'
    except (OSError, ValueError, IndexError):
        return 'running_unverified_identity'


def attempt_directories(root):
    for directory, subdirs, files in os.walk(root, followlinks=False):
        subdirs[:] = sorted(n for n in subdirs if n not in PRUNE and not (Path(directory)/n).is_symlink())
        if 'execution.json' in files or 'audit.json' in files:
            yield Path(directory)


def distribution(values):
    return None if not values else dict(count=len(values), minimum=min(values),
        median=statistics.median(values), mean=statistics.fmean(values), maximum=max(values))


def summarize(root, now=None):
    root = Path(root).resolve()
    now = time.time() if now is None else float(now)
    plan = read_json(root/'plan.json')
    fixtures = read_json(root/'fixtures.json')
    plan_hash, fixtures_hash = sha(root/'plan.json'), sha(root/'fixtures.json')
    definitions = Counter((f['category'], f['split']) for f in fixtures)
    fixture_ids = Counter(f['id'] for f in fixtures)
    expected = {f['id']: f for f in fixtures}
    warnings = []
    if any(n != 1 for n in fixture_ids.values()):
        warnings.append('duplicate_fixture_ids')
    fixture_hash_ok = plan.get('fixtures_sha256') == fixtures_hash
    if not fixture_hash_ok:
        warnings.append('fixture_manifest_hash_missing_or_mismatch')
    statuses, reasons = Counter(), Counter()
    groups = defaultdict(lambda: dict(attempts=0, statuses=Counter(), reasons=Counter(),
        metrics_all=defaultdict(list), metrics_eligible=defaultdict(list),
        metrics_by_split=defaultdict(lambda: defaultdict(list))))
    unique_train, unique_collection, seen_train = defaultdict(set), defaultdict(set), defaultdict(set)
    eligible_validation, executed_validation = defaultdict(set), defaultdict(set)
    durations, rows = [], []
    phases = Counter()
    for folder in sorted(attempt_directories(root)):
        relative = str(folder.relative_to(root))
        row = dict(folder=relative, metadata_sha256={}, archive='no_receipt', errors=[])
        metadata = {}
        for name in ('request', 'execution', 'audit'):
            path = folder/(name+'.json')
            if not path.exists():
                metadata[name] = None
                row['errors'].append('missing_'+name)
                continue
            row['metadata_sha256'][name+'.json'] = sha(path)
            try:
                value = read_json(path)
                if not isinstance(value, dict):
                    raise ValueError('Expected JSON object')
                metadata[name] = value
            except (OSError, ValueError, TypeError) as error:
                metadata[name] = None
                row['errors'].append('invalid_'+name+':'+type(error).__name__)
        request, execution, audit = (metadata[k] for k in ('request', 'execution', 'audit'))
        fixture = (request or {}).get('fixture', {})
        method = (request or {}).get('method', (audit or {}).get('method', 'unknown'))
        category, split, fixture_id = (fixture.get(k, 'unknown') for k in ('category', 'split', 'id'))
        phase = (request or {}).get('phase', 'unknown')
        row.update(method=method, category=category, split=split, fixture_id=fixture_id, phase=phase)
        phases[phase] += 1
        if expected.get(fixture_id) != fixture:
            row['errors'].append('fixture_configuration_not_in_plan')
        if not fixture_hash_ok:
            row['errors'].append('fixture_manifest_hash_missing_or_mismatch')
        if request and request.get('plan_sha256') != plan_hash:
            row['errors'].append('request_plan_hash_mismatch')
        if execution and execution.get('plan_sha256') != plan_hash:
            row['errors'].append('execution_plan_hash_mismatch')
        if audit:
            for key, value in (('fixture_id', fixture_id), ('split', split), ('method', method)):
                if audit.get(key) != value:
                    row['errors'].append('audit_'+key+'_mismatch')
            if not isinstance(audit.get('eligible'), bool):
                row['errors'].append('invalid_eligibility_flag')
            for name in METRICS:
                value = audit.get(name)
                if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
                    row['errors'].append('invalid_metric_'+name)
        if execution and execution.get('status') == 'running':
            status = process_status(execution)
        elif execution and execution.get('status') in ('failed', 'interrupted'):
            status = 'infrastructure_'+execution['status']
        elif row['errors']:
            status = 'incomplete_or_invalid_evidence'
        elif execution.get('status') == 'completed' and execution.get('returncode') == 0:
            status = 'eligible' if audit['eligible'] else 'physical_failure'
        else:
            status = 'infrastructure_unrecognized_exit'
        row['status'] = status
        row['execution_status'] = (execution or {}).get('status')
        row['execution_returncode'] = (execution or {}).get('returncode')
        statuses[status] += 1
        group = groups[(category, method)]
        group['attempts'] += 1
        group['statuses'][status] += 1
        if execution:
            start, finish = execution.get('started'), execution.get('finished')
            if isinstance(start, (int, float)) and isinstance(finish, (int, float)) and finish >= start:
                durations.append(finish-start)
                row['wall_seconds'] = finish-start
        if status in ('eligible', 'physical_failure'):
            if split == 'train':
                seen_train[(category, method)].add(fixture_id)
            elif split == 'validation':
                executed_validation[(category, method)].add(fixture_id)
                if status == 'eligible':
                    eligible_validation[(category, method)].add(fixture_id)
            for name in METRICS:
                value = audit.get(name)
                if value is not None:
                    group['metrics_all'][name].append(value)
                    group['metrics_by_split'][split][name].append(value)
                    if status == 'eligible':
                        group['metrics_eligible'][name].append(value)
            row['failure_reasons'] = audit.get('failure_reasons', [])
            for reason in row['failure_reasons']:
                reasons[reason] += 1
                group['reasons'][reason] += 1
            if status == 'eligible' and method == 'vmc' and split == 'train' and audit.get('esn_label_eligible') is True:
                unique_train[category].add(fixture_id)
                if phase == 'collection':
                    unique_collection[category].add(fixture_id)
        receipt = root/'archive_receipts'/relative/'receipt.json'
        if receipt.exists():
            row['metadata_sha256']['archive_receipt.json'] = sha(receipt)
            try:
                value = read_json(receipt)
                if not value.get('verified_path'):
                    raise ValueError('Receipt lacks verified_path')
                row.update(archive='recorded_verified_receipt', archive_path=value['verified_path'],
                           archive_verified_at=value.get('verified_at'))
            except (OSError, ValueError, TypeError, AttributeError):
                row['archive'] = 'invalid_receipt'
        rows.append(row)
    categories = plan.get('categories', sorted({c for c, _ in definitions}))
    methods = plan.get('methods', ['vmc'])
    target = int(plan.get('train_per_category', 1000))
    summaries = []
    for category in categories:
        for method in methods:
            group = groups[(category, method)]
            summaries.append(dict(category=category, method=method, attempts=group['attempts'],
                statuses=dict(group['statuses']), failure_reasons=dict(group['reasons']),
                unique_train_evaluated=len(seen_train[(category, method)]),
                unique_validation_evaluated=len(executed_validation[(category, method)]),
                unique_validation_eligible=len(eligible_validation[(category, method)]),
                metrics_all_completed={k: distribution(v) for k, v in group['metrics_all'].items()},
                metrics_by_split={s: {k: distribution(v) for k, v in vals.items()}
                                  for s, vals in group['metrics_by_split'].items()},
                metrics_eligible={k: distribution(v) for k, v in group['metrics_eligible'].items()}))
    vmc = {c: dict(target=target, unique_eligible_train_any_phase=len(unique_train[c]),
                   unique_eligible_train_collection=len(unique_collection[c]),
                   collection_shortfall=max(0, target-len(unique_collection[c]))) for c in categories}
    deadline = plan.get('deadline_epoch')
    incomplete = [f'{c}: VMC collection shortfall {r["collection_shortfall"]}/{target}'
                  for c, r in vmc.items() if r['collection_shortfall']]
    if statuses['physical_failure']:
        incomplete.append('Physical failures retained; these are not accepted teacher labels')
    if any(k.startswith('infrastructure_') or k.startswith('stale_') or k == 'incomplete_or_invalid_evidence'
           for k, n in statuses.items() if n):
        incomplete.append('Infrastructure/stale/incomplete evidence requires inspection; excluded from optimizer-quality counts')
    if not (root/'complete.json').exists():
        incomplete.append('Campaign completion marker absent; no completion inferred from scenario definitions')
    return dict(schema=1, generated_at_utc=datetime.fromtimestamp(now, timezone.utc).isoformat(),
        campaign_root=str(root), compute_host=socket.gethostname(),
        provenance=dict(script_sha256=sha(__file__), plan_sha256=plan_hash, fixtures_sha256=fixtures_hash,
            fixtures_match_plan=fixture_hash_ok, base_git_commit=plan.get('base_git_commit'),
            sources_declared_in_plan=plan.get('sources', {}),
            raw_trajectory_hashes_revalidated=False, remote_receipts_revalidated=False),
        definition_counts=[dict(category=c, split=s, count=n) for (c, s), n in sorted(definitions.items())],
        total_definitions=len(fixtures), unique_definition_ids=len(fixture_ids),
        attempt_counts=dict(statuses), attempts_total=len(rows), attempts_by_phase=dict(phases),
        vmc_training_data=vmc, method_category=summaries, failure_reasons=dict(reasons),
        archive_counts=dict(Counter(r['archive'] for r in rows)),
        budget=dict(deadline_epoch=deadline, deadline_reached=now >= deadline if isinstance(deadline, (int, float)) else None,
            remaining_wall_seconds=max(0, deadline-now) if isinstance(deadline, (int, float)) else None,
            limits={k:v for k,v in plan.items() if k.startswith('max_') or k.endswith('_candidates_per_category')},
            completed_attempt_wall_seconds=sum(durations),
            completed_attempt_wall_distribution=distribution(durations),
            note='Wall sum is metadata accounting, not CPU time; definitions are not executed rollouts'),
        warnings=warnings, unfinished=incomplete, attempts=rows,
        scope='Read-only metadata summary; no unexecuted validation results opened and no simulator/network invoked')


def markdown(report):
    lines = ['# Teacher-bank campaign status', '', report['generated_at_utc'], '',
        f"Campaign: `{report['campaign_root']}`", '',
        f"Defined fixtures: {report['total_definitions']}; recorded attempts: {report['attempts_total']}.", '',
        '| Attempt status | Count |', '|---|---:|']
    lines += [f'| {key} | {value} |' for key, value in sorted(report['attempt_counts'].items()) if value]
    lines += ['', '| Category | Eligible unique VMC train (all phases) | Collection | Target |', '|---|---:|---:|---:|']
    lines += [f'| {c} | {v["unique_eligible_train_any_phase"]} | {v["unique_eligible_train_collection"]} | {v["target"]} |'
              for c, v in report['vmc_training_data'].items()]
    lines += ['', '| Category / method | Completed | Eligible | RMSE median (m) | Peak torque max (Nm) | Peak speed max (m/s) |',
              '|---|---:|---:|---:|---:|---:|']
    for row in report['method_category']:
        metrics = row['metrics_all_completed']
        def value(key, statistic):
            item = metrics.get(key)
            return f'{item[statistic]:.6g}' if item else '—'
        statuses = row['statuses']
        lines.append(f'| {row["category"]} / {row["method"]} | {statuses.get("eligible",0)+statuses.get("physical_failure",0)} | '
                     f'{statuses.get("eligible",0)} | {value("rmse_m","median")} | '
                     f'{value("peak_torque_nm","maximum")} | {value("peak_speed_mps","maximum")} |')
    lines += ['', 'Table metrics include retained physical failures and already executed validation. JSON separately reports train/validation and eligible-only distributions.', '',
              f"Budget: deadline reached={report['budget']['deadline_reached']}; remaining wall seconds={report['budget']['remaining_wall_seconds']}; recorded completed attempt wall seconds={report['budget']['completed_attempt_wall_seconds']:.1f}.",
              '', 'Physical failure reasons: '+(', '.join(f'{k}={v}' for k,v in sorted(report['failure_reasons'].items())) or 'none recorded'),
              'Archive accounting: '+', '.join(f'{k}={v}' for k,v in sorted(report['archive_counts'].items())), '',
              '## Unfinished / limitations', '']
    lines += ['- '+v for v in report['unfinished'] + report['warnings']]
    lines += ['', 'Archive receipts are past verification records; this summary does not contact the server or rehash raw trajectories.',
              f"Plan SHA256: `{report['provenance']['plan_sha256']}`", '']
    return '\n'.join(lines)


def write_reports(report, output):
    output = Path(output).resolve()
    root = Path(report['campaign_root']).resolve()
    paths = [output.with_suffix('.json'), output.with_suffix('.md')]
    if any(p == root or root in p.parents for p in paths):
        raise ValueError('Output must be outside the original campaign directory')
    if any(p.exists() for p in paths):
        raise FileExistsError('Refusing to overwrite an existing report')
    output.parent.mkdir(parents=True, exist_ok=True)
    report['report_command'] = sys.argv
    contents = [json.dumps(report, indent=2, allow_nan=False)+'\n', markdown(report)]
    for path, content in zip(paths, contents):
        with path.open('x') as stream:
            stream.write(content)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New report prefix outside campaign root')
    args = parser.parse_args()
    paths = write_reports(summarize(args.root), args.output)
    print(json.dumps(dict(json=str(paths[0]), markdown=str(paths[1]))))


if __name__ == '__main__':
    main()
