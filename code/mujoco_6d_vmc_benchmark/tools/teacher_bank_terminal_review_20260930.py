"""Metadata-only campaign closeout audit. Never dispatches or changes a run.

Creates a new directory containing immutable JSON metadata snapshots plus a
report. No NPZ/MJB is decoded; raw hashes and remote receipts are declarations,
not fresh raw/server verification. Safe to run before deadline as a live review.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import time

import teacher_bank_status_20260930 as status

SKIP = {'source', 'source_inputs', 'assets', 'metadata', 'final_reports'}
FINAL_REPORT_NAMES = {'teacher_bank.json', 'dataset_index.json', 'status.json',
                      'validation_results.json', 'complete.json'}


def dumps(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def metadata_paths(root):
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not (Path(directory)/d).is_symlink())
        for name in sorted(files):
            path = Path(directory)/name
            if name.endswith('.json') and not path.is_symlink():
                yield path


def copy_snapshot(root, output):
    snapshot = output/'metadata_snapshot'
    snapshot.mkdir()
    hashes = {}
    paths = list(metadata_paths(root))
    for path in paths:
        data = path.read_bytes()
        relative = str(path.relative_to(root))
        hashes[relative] = hashlib.sha256(data).hexdigest()
        destination = snapshot/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    # Detect concurrent progress, do not pause or lock the running campaign.
    changed = [name for name, value in hashes.items()
               if not (root/name).exists() or status.sha(root/name) != value]
    new = sorted(str(p.relative_to(root)) for p in metadata_paths(root)
                 if str(p.relative_to(root)) not in hashes)
    return snapshot, hashes, changed, new


def independent_candidate(rows, x, index):
    """Aggregate per-anchor audit labels; never union across parameter vectors."""
    errors = []
    scores, labels, eligible = [], [], []
    for row in rows:
        success = row.get('eligible')
        reasons = row.get('failure_reasons')
        if not isinstance(success, bool) or not isinstance(reasons, list):
            return None, ['invalid_success_or_failure_labels']
        label_count = len(reasons)
        if success != (label_count == 0):
            errors.append('success_failure_labels_disagree')
        constraint = -1. if success else float(label_count)
        if row.get('constraint') != constraint:
            errors.append('anchor_constraint_not_failure_label_count')
        try:
            score = row['rmse_m']/.05+.3*row['torque_ratio']+.1*row['completion_proxy_retreat_s']/55.
            if not math.isfinite(score) or abs(score-row['score']) > 1e-12:
                errors.append('anchor_score_mismatch')
        except (TypeError, KeyError):
            return None, ['missing_score_evidence']
        scores.append(score); labels.append(label_count); eligible.append(success)
    failed = len(rows)-sum(eligible)
    worst = max(labels, default=0)
    return dict(x=x, index=index, eligible_count=sum(eligible), total=len(rows),
        failed_anchor_count=failed, violation_proxy=float(worst),
        constraint=-1. if not failed else failed+.25*worst/(1.+worst),
        score=sum(scores)/len(scores)), errors


def rank(value):
    return value['failed_anchor_count'], value['violation_proxy'], value['score']


def same_fields(expected, actual):
    if not isinstance(actual, dict):
        return False
    for key, value in expected.items():
        other = actual.get(key)
        if isinstance(value, float):
            if not isinstance(other, (float, int)) or not math.isfinite(other) or abs(value-other) > 1e-12:
                return False
        elif value != other:
            return False
    return True


def closeout(snapshot, report, stable=True):
    """Build stricter lock/parameter certification atop reusable status data."""
    def read(name, default=None):
        path = snapshot/name
        if not path.exists():
            return default
        try:
            return status.read_json(path)
        except (ValueError, OSError):
            return default

    plan = read('plan.json')
    progress = report['search_progress']
    bank, marker = read('teacher_bank.json', {}), read('anchor_feasibility.json')
    reconstructed = {}
    globally_complete = progress.get('available', False)
    for group in progress.get('method_category', []):
        key = group['category']+'/'+group['method']
        history = read('search/'+key+'/history.json', [])
        history_index = defaultdict(list)
        for entry in history if isinstance(history, list) else []:
            if isinstance(entry, dict):
                history_index[entry.get('index')].append(entry)
        candidates = []
        selected_request = {}
        for candidate in group['candidates']:
            index = candidate['index']
            item = dict(index=index, complete=candidate['complete'],
                        errors=[], anchors=candidate['anchors'], independently_reconstructed=None)
            if candidate['complete']:
                decision = read(f'search/{key}/c{index:02d}/decision.json', {})
                audits = [read(a['folder']+'/audit.json', {}) for a in candidate['anchors']]
                requests = [read(a['folder']+'/request.json', {}) for a in candidate['anchors']]
                rebuilt, errors = independent_candidate(audits, decision.get('x'), index)
                item['errors'].extend(errors)
                item['independently_reconstructed'] = rebuilt
                if len(history_index[index]) != 1 or not same_fields(rebuilt or {}, history_index[index][0]):
                    item['errors'].append('history_summary_mismatch_or_duplicate')
                if len({dumps(r.get('teacher')) for r in requests}) != 1:
                    item['errors'].append('candidate_controller_config_differs_by_anchor')
                if requests:
                    selected_request[index] = requests[0]
            item['verified'] = bool(item['complete'] and not item['errors'])
            candidates.append(item)
        valid = [v['independently_reconstructed'] for v in candidates if v['verified']]
        best = min(valid, key=rank) if valid else None
        selection = bank.get(key) if isinstance(bank, dict) else None
        selection = selection[0] if isinstance(selection, list) and len(selection) == 1 else None
        matches = bool(best and same_fields(best, selection)
                       and selection.get('anchor_feasible') == (best['constraint'] <= 0))
        complete = bool(candidates) and all(v['verified'] for v in candidates)
        globally_complete = globally_complete and complete and matches
        reconstructed[key] = dict(all_budget_candidates_verified=complete,
            recorded_selection_matches_independent_rank=matches,
            best_complete_candidate=best, recorded_selection=selection,
            selected_controller_config=(selected_request[best['index']].get('teacher') if best else None),
            candidates=candidates)
    expected_infeasible = sorted(k for k, value in reconstructed.items()
        if value['best_complete_candidate'] and value['best_complete_candidate']['constraint'] > 0)
    marker_ok = isinstance(marker, dict) and sorted(marker.get('infeasible_method_categories', [])) == expected_infeasible
    model_sets = defaultdict(set)
    for group in progress.get('method_category', []):
        for candidate in group['candidates']:
            for anchor in candidate['anchors']:
                if anchor['complete']:
                    model_sets[(group['category'], anchor['anchor_index'])].add(anchor.get('model_sha256'))
    models_consistent = bool(model_sets) and all(len(values) == 1 and None not in values for values in model_sets.values())
    paired = all(block['model_pairing_verified'] for category in progress.get('category', [])
                 for block in category['blocks'])
    lock = bool(globally_complete and marker_ok and stable and models_consistent and paired)
    search_finished = [anchor.get('finished_epoch') for group in reconstructed.values()
        for candidate in group['candidates'] if candidate['verified'] for anchor in candidate['anchors']]
    lock_not_before = max((v for v in search_finished if isinstance(v, (float, int))), default=None)
    post_selection = []
    unique = defaultdict(set)
    fixed_parameter_successes = defaultdict(set)
    for row in report['attempts']:
        request = read(row['folder']+'/request.json', {})
        if row['status'] == 'eligible':
            parameter_id = hashlib.sha256(dumps(dict(x=row['controller_coordinates'],
                                                     teacher=request.get('teacher'))).encode()).hexdigest()
            fixed_parameter_successes[(row['category'], row['method'], row['split'], parameter_id)].add(row['fixture_id'])
        if row['phase'] not in ('validation', 'collection'):
            continue
        key = row['category']+'/'+row['method']
        chosen = reconstructed.get(key, {})
        best = chosen.get('best_complete_candidate')
        errors = []
        if not lock:
            errors.append('bank_not_certified_locked')
        if not best or request.get('x') != best['x'] or request.get('teacher') != chosen.get('selected_controller_config'):
            errors.append('executed_parameters_differ_from_selected_search_candidate')
        expected_split = 'validation' if row['phase'] == 'validation' else 'train'
        if row['split'] != expected_split:
            errors.append('phase_split_mismatch')
        if row['status'] not in ('eligible', 'physical_failure'):
            errors.append('not_valid_completed_execution')
        if (lock_not_before is None or not isinstance(row.get('started_epoch'), (float, int))
                or row['started_epoch'] < lock_not_before):
            errors.append('post_selection_dispatch_precedes_complete_search_or_time_missing')
        verified = not errors
        if verified and row['status'] == 'eligible':
            unique[(key, row['phase'])].add(row['fixture_id'])
        post_selection.append(dict(folder=row['folder'], phase=row['phase'], key=key,
            fixture_id=row['fixture_id'], status=row['status'], verified_locked_parameters=verified, errors=errors))
    return dict(bank_certified_locked=lock, all_candidate_summaries_and_rank_verified=bool(globally_complete),
        compiled_model_metadata_consistent_across_methods_and_candidates=models_consistent and paired,
        anchor_feasibility_marker_matches=marker_ok, expected_infeasible_groups=expected_infeasible,
        reconstructed_groups=reconstructed, post_selection_attempts=post_selection,
        lock_cannot_precede_search_finish_epoch=lock_not_before,
        unique_eligible_with_verified_locked_parameters=[dict(group=key, phase=phase,
            count=len(ids), fixture_ids=sorted(ids)) for (key, phase), ids in sorted(unique.items())],
        eligible_counts_per_fixed_parameter=[dict(category=category, method=method, split=split,
            coordinates_and_controller_config_sha256=parameter, unique_fixture_count=len(ids), fixture_ids=sorted(ids))
            for (category, method, split, parameter), ids in sorted(fixed_parameter_successes.items())],
        warning='Any-phase unique training data in reusable status is a mixed-parameter data inventory, never a single-policy success rate.')


def run(root, output, now=None):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() or output == root or root in output.parents:
        raise ValueError('Output must be new and outside the immutable run')
    output.mkdir(parents=True)
    snapshot, hashes, changed, new = copy_snapshot(root, output)
    report = status.summarize(snapshot, now=now)
    stable = not changed and not new
    plan = status.read_json(snapshot/'plan.json')
    sources = {}
    for relative, expected in plan.get('sources', {}).items():
        path = root/'source'/relative
        actual = status.sha(path) if path.is_file() and not path.is_symlink() else None
        sources[relative] = dict(expected=expected, actual=actual, matches=actual == expected)
    sources_ok = bool(sources) and all(value['matches'] for value in sources.values())
    selection = closeout(snapshot, report, stable=stable and sources_ok)
    selection['source_manifest_verified'] = sources_ok
    # A live process may finish after the JSON snapshot. Never turn a captured
    # running record into terminal certification solely because its PID vanished.
    active = any(r['execution_status'] == 'running' for r in report['attempts'])
    explicit_terminal = 'deadline_reached.json' in hashes or 'complete.json' in hashes
    terminal = bool(stable and explicit_terminal and not active)
    # campaign only copies five root reports at full normal completion. Per-run
    # receipts archive trajectories; they do not imply root metadata archival.
    metadata_gaps = []
    for name, value in hashes.items():
        if name.startswith(('source', 'archive_receipts/', 'metadata/')):
            continue
        if '/' not in name or name.startswith(('paired_model_checks/', 'recovery_records/', 'reuse_records/')) or name.endswith(('/history.json', '/decision.json')):
            final = root/'final_reports'/name
            mirrored = name in FINAL_REPORT_NAMES and final.is_file() and status.sha(final) == value
            metadata_gaps.append(dict(path=name, sha256=value, exact_final_reports_copy_present=mirrored,
                automatic_final_reports_scope=name in FINAL_REPORT_NAMES,
                archive_state='local_copy_only_remote_unverified' if mirrored else 'not_in_matching_final_reports_copy'))
    result = dict(schema=1, original_run=str(root), metadata_snapshot=str(snapshot),
        generated_epoch=time.time() if now is None else now, script_sha256=status.sha(Path(__file__)),
        status_helper_sha256=status.sha(Path(status.__file__)),
        snapshot_consistency=dict(stable=stable, files_changed_during_copy=changed, files_added_during_copy=new),
        snapshot_kind='terminal_evidence' if terminal else 'live_or_unverified_snapshot',
        process_status_caveat='Reusable status probes live /proc after metadata capture; a captured running record may appear stale if it finished meanwhile. This is not evidence the original campaign is currently stalled; check a fresh live execution.json. Captured running records always prevent terminal certification.',
        terminal_basis=dict(explicit_marker=explicit_terminal, active_attempts_present=active),
        metadata_sha256=hashes, source_verification=sources, closeout=selection, status=report,
        archive_metadata_inventory=metadata_gaps,
        deadline_archive_behavior='attempt() writes deadline_reached then raises SystemExit; no finally archives summary metadata. final_reports archive executes only after complete collection, with five selected root files; history/decisions/anchor_feasibility/deadline/recovery/reuse/paired checks need explicit closeout archive.',
        scope='Metadata/source hashes only; no NPZ/MJB decode, raw hashes not revalidated, remote receipts not revalidated. Defined fixtures are not executed trajectories.')
    destination = output/'review.json'
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = run(args.run, args.output)
    print(dumps(dict(output=str(args.output/'review.json'), snapshot_kind=value['snapshot_kind'],
        locked=value['closeout']['bank_certified_locked'], definitions=value['status']['total_definitions'],
        executed_attempts=value['status']['attempts_total'])))


if __name__ == '__main__':
    main()
