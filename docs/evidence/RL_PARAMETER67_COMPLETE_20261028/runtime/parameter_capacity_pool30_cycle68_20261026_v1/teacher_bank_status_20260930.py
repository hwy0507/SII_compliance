"""Read-only campaign accounting. No simulation, network, or validation dispatch.

Only metadata of already executed attempts is examined. Report destinations
must be outside the campaign tree, and existing reports are never overwritten.
Large trajectory hashes are reported from audits, not silently revalidated.
Completed rollout.json metadata is hashed against its audit before extraction.
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
import re
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


def contact_metadata(folder, fixture, audit):
    """Extract existing evaluator metadata, never recompute contacts or gates."""
    exposure = audit.get('exposure')
    hashes = audit.get('files_sha256')
    result = dict(available=False, source='rollout.json',
        scope='Existing evaluator metadata extraction, not independent physical-substep recomputation',
        audit_failure_reasons=audit.get('failure_reasons', []),
        audit_exposure_reasons=exposure.get('reasons', []) if isinstance(exposure, dict) else [])
    expected = hashes.get('rollout.json') if isinstance(hashes, dict) else None
    result['expected_sha256'] = expected
    if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
        return dict(result, reason='missing_or_invalid_rollout_audit_hash')
    path = folder/'rollout.json'
    if path.is_symlink():
        return dict(result, reason='symlink_rollout_rejected')
    try:
        # Hash exactly the bytes parsed, rather than a separate earlier file read.
        raw = path.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        result['actual_sha256'] = actual
        if actual != expected:
            return dict(result, reason='rollout_audit_hash_mismatch')
        rollout = json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        events = rollout['stats']['events']
        if not isinstance(events, dict) or any(not isinstance(e, dict) for e in events.values()):
            raise ValueError('Events must map event names to metadata objects')
        # Includes 1e999, which Python's JSON decoder otherwise accepts as infinity.
        json.dumps(rollout, allow_nan=False)
    except (OSError, ValueError, TypeError, KeyError):
        return dict(result, reason='missing_or_invalid_rollout_metadata')
    category = fixture.get('category')
    relevant_names = (['office_v5_corner_face', 'office_v5_corner_training_bridge',
                       'office_v5_corner_training_bridge_connector'] if category == 'passive_corner'
                      else ['ball'] if category == 'active_short'
                      else ['person_hand'] if category == 'active_long' and fixture.get('apparatus') == 'person'
                      else ['rod'] if category == 'active_long' and fixture.get('apparatus') == 'rod' else [])
    booleans = {k:v for k,v in rollout.items() if isinstance(v, bool)}
    return dict(result, available=True, events=events,
        relevant_event_names=relevant_names,
        relevant_events={k:events[k] for k in relevant_names if k in events},
        evaluator_booleans=booleans,
        evaluator_false_fields=[k for k,v in booleans.items() if not v],
        evaluator_context={k:rollout[k] for k in ('abort_reason', 'contact_required', 'final_task_stage') if k in rollout},
        note='False fields are reported verbatim, not all are applicable failures. Support top is not passive edge exposure. Contact force N is distinct from actuator torque Nm.')


def search_accounting(root, plan, fixtures, attempts, now):
    """Evidence-bound candidate budgets; partially executed blocks stay visible."""
    categories, methods = plan.get('categories', []), plan.get('methods', ['vmc'])
    count, anchors = plan.get('search_candidates_per_category'), plan.get('anchor_indices')
    if (isinstance(count, bool) or not isinstance(count, int) or count <= 0
            or not isinstance(anchors, list) or not anchors
            or any(isinstance(i, bool) or not isinstance(i, int) or i < 0 for i in anchors)
            or len(set(anchors)) != len(anchors)):
        return dict(available=False, reason='Missing_or_invalid_search_budget_or_anchor_manifest',
                    bank_state='unverified_not_locked', category=[], partial_blocks=[])
    by_folder = {row['folder']: row for row in attempts}
    warnings, files = [], {}
    def metadata(relative):
        path = root/relative
        if not path.exists(): return None
        if path.is_symlink():
            warnings.append('symlink_metadata_rejected:'+relative);return None
        try:
            result = read_json(path);files[relative] = sha(path)
            return result
        except (OSError, ValueError, TypeError):
            warnings.append('invalid_search_metadata:'+relative);return None
    def safe_relative(value):
        return (isinstance(value, str) and not Path(value).is_absolute()
                and '..' not in Path(value).parts and root in (root/value).resolve().parents)
    def resolve(origin):
        relative, errors = origin, []
        reuse = metadata('reuse_records/'+origin+'.json')
        if reuse is None and (root/'reuse_records'/(origin+'.json')).exists():
            errors.append('unreadable_reuse_record')
        if reuse is not None:
            if not isinstance(reuse, dict) or not safe_relative(reuse.get('reused_relative')):
                return None, ['invalid_reuse_record']
            relative = reuse['reused_relative']
            reused_row = by_folder.get(relative)
            if not reused_row or reuse.get('request_sha256') != reused_row['metadata_sha256'].get('request.json'):
                errors.append('reused_request_hash_mismatch')
        recovery = metadata('recovery_records/'+relative+'.json')
        if recovery is None and (root/'recovery_records'/(relative+'.json')).exists():
            errors.append('unreadable_recovery_record')
        if recovery is not None:
            if (not isinstance(recovery, dict) or recovery.get('origin_relative') != relative
                    or not safe_relative(recovery.get('active_relative'))):
                return None, errors+['invalid_recovery_record']
            relative = recovery['active_relative']
        return by_folder.get(relative), errors
    groups, categories_out, partial, cutoff_partial = {}, [], [], []
    deadline = plan.get('deadline_epoch')
    deadline_valid = (not isinstance(deadline, bool) and isinstance(deadline, (float, int))
                      and math.isfinite(deadline))
    for category in categories:
        train = [f for f in fixtures if f.get('category') == category and f.get('split') == 'train']
        for method in methods:
            key = category+'/'+method
            history = metadata('search/'+key+'/history.json')
            hentries = {}
            if history is not None:
                if not isinstance(history, list): warnings.append('invalid_history:'+key)
                else:
                    for entry in history:
                        if (not isinstance(entry, dict) or isinstance(entry.get('index'), bool)
                                or not isinstance(entry.get('index'), int)):
                            warnings.append('invalid_history_entry:'+key);continue
                        index = entry['index']
                        if index in hentries:
                            hentries[index] = None;warnings.append('duplicate_history_index:'+key+':'+str(index))
                        else: hentries[index] = entry
            candidates = []
            for index in range(count):
                base = f'search/{key}/c{index:02d}'
                decision = metadata(base+'/decision.json')
                x = decision.get('x') if isinstance(decision, dict) else None
                valid_x = (isinstance(x, list) and len(x) > 0 and all(
                    not isinstance(v, bool) and isinstance(v, (float, int)) and math.isfinite(v) for v in x))
                anchor_rows = []
                for anchor in anchors:
                    row, errors = resolve(base+'/'+str(anchor))
                    if anchor >= len(train): errors.append('anchor_outside_training_manifest')
                    if row is not None:
                        if (row.get('category') != category or row.get('method') != method
                                or row.get('split') != 'train'
                                or (anchor < len(train) and row.get('fixture_id') != train[anchor]['id'])):
                            errors.append('anchor_identity_mismatch')
                        if not valid_x or row.get('controller_coordinates') != x:
                            errors.append('candidate_coordinates_mismatch')
                        if row['status'] not in ('eligible', 'physical_failure'):
                            errors.append('anchor_not_valid_completed_execution')
                    else: errors.append('anchor_not_executed')
                    anchor_rows.append(dict(anchor_index=anchor, folder=row['folder'] if row else None,
                        complete=not errors, status=row['status'] if row else 'not_executed', errors=errors,
                        started_epoch=row.get('started_epoch') if row else None,
                        finished_epoch=row.get('finished_epoch') if row else None,
                        model_sha256=row.get('model_sha256') if row else None))
                complete = bool(valid_x and all(row['complete'] for row in anchor_rows))
                entry = hentries.get(index)
                history_matches = bool(complete and isinstance(entry, dict) and entry.get('x') == x
                    and entry.get('total', len(anchors)) == len(anchors))
                candidates.append(dict(index=index, complete=complete, history_recorded=history_matches,
                    decision_present=decision is not None, anchors=anchor_rows,
                    evidence_present=decision is not None or index in hentries or any(r['folder'] for r in anchor_rows)))
            prefix = 0
            while prefix < count and candidates[prefix]['complete']: prefix += 1
            completed_indices = [r['index'] for r in candidates if r['complete']]
            groups[key] = dict(category=category, method=method, planned_candidates=count,
                complete_candidate_count=len(completed_indices), complete_candidate_indices=completed_indices,
                contiguous_complete_prefix_count=prefix,
                history_entry_count=len(hentries), verified_history_candidate_count=sum(r['history_recorded'] for r in candidates),
                history_without_complete_evidence=[i for i in hentries if i not in completed_indices],
                complete_without_history=[r['index'] for r in candidates if r['complete'] and not r['history_recorded']],
                candidates=candidates)
        common_prefix = 0
        blocks = []
        for index in range(count):
            matched = [groups[category+'/'+m]['candidates'][index] for m in methods]
            all_complete = all(r['complete'] for r in matched)
            model_equal = all_complete and all(
                len({r['anchors'][j]['model_sha256'] for r in matched}) == 1
                and isinstance(matched[0]['anchors'][j]['model_sha256'], str)
                and bool(re.fullmatch('[0-9a-f]{64}', matched[0]['anchors'][j]['model_sha256']))
                for j in range(len(anchors)))
            if index == common_prefix and model_equal: common_prefix += 1
            block = dict(category=category, candidate_index=index, all_methods_complete=all_complete,
                model_pairing_verified=bool(model_equal),
                methods={m:dict(complete=groups[category+'/'+m]['candidates'][index]['complete'],
                    completed_anchors=sum(a['complete'] for a in groups[category+'/'+m]['candidates'][index]['anchors']),
                    expected_anchors=len(anchors)) for m in methods})
            if any(r['evidence_present'] for r in matched) and not model_equal:
                partial.append(block)
            if deadline_valid and now >= deadline:
                cutoff_methods = {}
                any_dispatched = False
                for method, candidate in zip(methods, matched):
                    completed = 0
                    for anchor_row in candidate['anchors']:
                        start, finish = anchor_row['started_epoch'], anchor_row['finished_epoch']
                        any_dispatched = any_dispatched or (isinstance(start, (float, int)) and start <= deadline)
                        completed += bool(anchor_row['complete'] and isinstance(finish, (float, int)) and finish <= deadline)
                    cutoff_methods[method] = dict(complete=completed == len(anchors),
                        completed_anchors=completed, expected_anchors=len(anchors))
                if any_dispatched and not (all(r['complete'] for r in cutoff_methods.values()) and model_equal):
                    cutoff_partial.append(dict(category=category, candidate_index=index, methods=cutoff_methods,
                        as_of_epoch=deadline, note='Reconstructed from recorded execution start/finish timestamps; metadata written later may have been unavailable at cutoff.'))
            blocks.append(block)
        categories_out.append(dict(category=category,
            common_complete_prefix_count=common_prefix, common_complete_prefix_indices=list(range(common_prefix)),
            comparable_anchor_evaluations_per_method=common_prefix*len(anchors),
            complete_candidates_outside_comparison={m:[i for i in groups[category+'/'+m]['complete_candidate_indices']
                if i >= common_prefix] for m in methods}, blocks=blocks))
    search_complete = all(g['complete_candidate_count'] == count and
                          g['verified_history_candidate_count'] == count for g in groups.values()) and bool(groups)
    bank = metadata('teacher_bank.json')
    marker = metadata('anchor_feasibility.json')
    bank_rows, bank_consistent = {}, True
    for key, group in groups.items():
        selected = bank.get(key) if isinstance(bank, dict) else None
        selection = selected[0] if isinstance(selected, list) and len(selected) == 1 and isinstance(selected[0], dict) else None
        index = selection.get('index') if selection else None
        verified = (isinstance(index, int) and not isinstance(index, bool) and 0 <= index < count
            and group['candidates'][index]['complete'] and group['candidates'][index]['history_recorded'])
        if verified:
            decision = metadata(f'search/{key}/c{index:02d}/decision.json')
            verified = selection.get('x') == decision.get('x')
        bank_consistent = bank_consistent and bool(verified)
        bank_rows[key] = dict(present=selection is not None, selected_index=index,
            selection_has_complete_search_evidence=bool(verified), anchor_feasible=selection.get('anchor_feasible') if selection else None)
    locked = bool(search_complete and isinstance(marker, dict) and bank_consistent)
    if marker is not None and not locked:
        warnings.append('search_completion_marker_not_supported_by_complete_history_and_bank')
    deadline_record = metadata('deadline_reached.json')
    return dict(available=True, planned_candidates_per_method_category=count, anchors_per_candidate=len(anchors),
        method_category=list(groups.values()), category=categories_out,
        common_prefix_across_all_categories=min((v['common_complete_prefix_count'] for v in categories_out), default=0),
        partial_blocks=partial, partial_blocks_at_deadline=cutoff_partial,
        deadline_record=deadline_record, full_search_evidence_complete=search_complete,
        bank_state='locked_after_complete_search' if locked else 'provisional_not_locked' if bank is not None else 'absent',
        bank=bank_rows, metadata_sha256=files, warnings=warnings,
        comparison_scope='Only each category common contiguous completed candidate prefix with matching compiled model hashes; retained physical failures included. Extra and partial candidates are excluded from equal-budget comparison. Equal candidate/anchor counts are not equal wall or CPU time.',
        snapshot_note='Read-only live snapshot; an in-flight candidate may become complete after this report.')


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
        row['controller_coordinates'] = (request or {}).get('x')
        row['model_sha256'] = (audit or {}).get('model_sha256')
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
        row['started_epoch'] = (execution or {}).get('started')
        row['finished_epoch'] = (execution or {}).get('finished')
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
            row['contact_metadata'] = contact_metadata(folder, fixture, audit)
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
    search_progress = search_accounting(root, plan, fixtures, rows, now)
    if search_progress.get('available') and search_progress['bank_state'] != 'locked_after_complete_search':
        incomplete.append('Teacher bank is not verified locked; partial search selections are provisional')
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
        search_progress=search_progress,
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
              '## Search budget and provisional selection', '']
    search = report.get('search_progress', {})
    if search.get('available'):
        lines += [f'Teacher bank: **{search["bank_state"]}**. Full search evidence complete: {search["full_search_evidence_complete"]}.', '',
            '| Category / method | Complete candidates | Contiguous prefix | History verified |', '|---|---:|---:|---:|']
        lines += [f'| {r["category"]} / {r["method"]} | {r["complete_candidate_count"]}/{r["planned_candidates"]} | '
                  f'{r["contiguous_complete_prefix_count"]} | {r["verified_history_candidate_count"]} |'
                  for r in search['method_category']]
        lines += ['', '| Category | Common comparable prefix | Anchor evaluations per method |', '|---|---|---:|']
        lines += [f'| {r["category"]} | {r["common_complete_prefix_indices"]} | {r["comparable_anchor_evaluations_per_method"]} |'
                  for r in search['category']]
        lines += ['', search['comparison_scope'], '',
            f'Partial blocks: {len(search["partial_blocks"])}; partial blocks at deadline: {len(search["partial_blocks_at_deadline"])}.']
        for block in search['partial_blocks']:
            detail=', '.join(f'{m}={r["completed_anchors"]}/{r["expected_anchors"]} anchors'
                             for m,r in block['methods'].items())
            lines.append(f'- {block["category"]} / c{block["candidate_index"]:02d}: {detail}; model pairing={block["model_pairing_verified"]}.')
        lines += ['', 'The earlier aggregate metrics table is descriptive across all completed attempts; it is not an equal-budget controller comparison.']
    else:
        lines += ['Search budget unavailable; do not infer a locked bank or an equal-budget comparison.']
    lines += ['', '## Auxiliary contact-load metadata', '',
        'Only completed cases are read; rollout.json bytes must match the audit SHA256. These are existing evaluator event summaries, not independent physical-substep recomputation. Contact force (N) is distinct from actuator torque (Nm). No score, gate or primary metric changes.', '',
        '| Case | Category / method | Event | Peak (N) | Impulse (Ns) | Robot parts |',
        '|---|---|---|---:|---:|---|']
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')
    for row in report['attempts']:
        contact = row.get('contact_metadata')
        if not contact:
            continue
        if not contact['available']:
            lines.append(f'| {cell(row["folder"])} | {row["category"]} / {row["method"]} | Unavailable: {contact["reason"]} | — | — | — |')
            continue
        events = contact['relevant_events']
        for name, event in events.items():
            lines.append(f'| {cell(row["folder"])} | {row["category"]} / {row["method"]} | {cell(name)} | '
                         f'{cell(event.get("peak_n", "—"))} | {cell(event.get("impulse_ns", "—"))} | {cell(event.get("robot_parts", []))} |')
        if not events:
            lines.append(f'| {cell(row["folder"])} | {row["category"]} / {row["method"]} | No category-relevant event recorded | — | — | — |')
    lines += ['', 'Full event dictionaries and evaluator booleans are retained in JSON. Placement support top is excluded from passive edge rows. False flags below are verbatim metadata, not automatically applicable failure reasons.', '']
    for row in report['attempts']:
        contact = row.get('contact_metadata', {})
        if contact.get('available'):
            flags = ', '.join(k+'=false' for k in contact['evaluator_false_fields']) or 'none'
            lines.append(f'- {cell(row["folder"])}: {flags}; audit failure reasons={cell(contact["audit_failure_reasons"])}; exposure reasons={cell(contact["audit_exposure_reasons"])}.')
    lines += ['', '## Unfinished / limitations', '']
    lines += ['- '+v for v in report['unfinished'] + report['warnings'] + search.get('warnings', [])]
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
