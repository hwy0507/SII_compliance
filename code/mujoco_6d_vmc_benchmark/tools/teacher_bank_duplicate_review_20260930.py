"""Supplement locked closeout with duplicate execution and optional NPZ replay.

No polling or simulation. Reads a frozen terminal metadata snapshot; optional raw
comparison is restricted to completed selected-search/collection identity pairs.
ZIP byte equality and array equality are reported separately.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''): value.update(block)
    return value.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def identity(request, audit):
    fixture = request['fixture']
    physical = fixture.get('active_physical_parameters')
    if not physical or digest(physical) != fixture.get('physical_config_sha256'):
        raise ValueError('Physical parameter hash missing or inconsistent')
    return dict(category=fixture['category'], physical_config_sha256=fixture['physical_config_sha256'],
        model_sha256=audit['model_sha256'], seed=fixture['seed'], method=request['method'],
        x=request['x'], teacher=request['teacher'])


def compare_npz(left, right):
    """At most one member pair in memory; no pickle and no simulator imports."""
    containers_equal = sha(left) == sha(right)
    members = []
    with np.load(left, allow_pickle=False) as a, np.load(right, allow_pickle=False) as b:
        keys_equal = sorted(a.files) == sorted(b.files)
        for key in sorted(set(a.files) & set(b.files)):
            av, bv = a[key], b[key]
            dtype_equal, shape_equal = av.dtype == bv.dtype, av.shape == bv.shape
            equal = dtype_equal and shape_equal and np.array_equal(av, bv,
                equal_nan=av.dtype.kind in 'fc' and bv.dtype.kind in 'fc')
            members.append(dict(name=key, dtype_left=str(av.dtype), dtype_right=str(bv.dtype),
                shape_left=list(av.shape), shape_right=list(bv.shape), values_equal=bool(equal)))
            del av, bv
    return dict(zip_file_bytes_equal=containers_equal, member_keys_equal=keys_equal,
        left_only_members=sorted(set(a.files)-set(b.files)), right_only_members=sorted(set(b.files)-set(a.files)),
        arrays_equal=keys_equal and all(v['values_equal'] for v in members), members=members,
        nan_semantics='Matching NaNs count equal; dtype, shape and all remaining values must match exactly')


def review_duplicates(review_dir, raw_root, output, expected_review_sha256, compare_arrays=False):
    review_dir, raw_root, output = map(lambda p: Path(p).resolve(), (review_dir, raw_root, output))
    if output.exists() or any(output == parent or parent in output.parents for parent in (review_dir, raw_root)):
        raise ValueError('Use new output outside original run and frozen review')
    review_path = review_dir/'review.json'
    if sha(review_path) != expected_review_sha256: raise ValueError('Review hash mismatch')
    report = json.loads(review_path.read_text())
    if Path(report['original_run']).resolve() != raw_root: raise ValueError('Raw root differs from reviewed run')
    if report['closeout'].get('bank_certified_locked') is not True: raise ValueError('Locked bank required')
    hashes = report['metadata_sha256']; snapshot = review_dir/'metadata_snapshot'; loaded = {}
    def read(relative):
        relative_path = Path(relative)
        if relative_path.is_absolute() or '..' in relative_path.parts: raise ValueError('Unsafe metadata path')
        path = snapshot/relative
        if relative not in hashes or path.is_symlink() or sha(path) != hashes[relative]:
            raise ValueError('Snapshot hash mismatch: '+relative)
        loaded[relative] = hashes[relative]
        return json.loads(path.read_text())
    selected = set()
    configs = {}
    for key, group in report['closeout']['reconstructed_groups'].items():
        best = group['best_complete_candidate']
        candidate = next(c for c in group['candidates'] if c['index'] == best['index'])
        selected.update(a['folder'] for a in candidate['anchors'])
        configs[key] = dict(x=best['x'], teacher=group['selected_controller_config'])
    groups = defaultdict(list); rows = []; skipped = []; audits = {}
    for row in report['status']['attempts']:
        if row.get('split') != 'train': continue
        folder = row['folder']
        if row['status'] not in ('eligible', 'physical_failure'):
            skipped.append(dict(folder=folder, reason='not_completed_valid_execution', status=row['status'])); continue
        request, audit, execution = (read(folder+'/'+name+'.json') for name in ('request','audit','execution'))
        if execution.get('status') != 'completed' or execution.get('returncode') != 0:
            skipped.append(dict(folder=folder, reason='execution_not_completed')); continue
        if hashes[folder+'/request.json'] != audit.get('files_sha256', {}).get('request.json'):
            skipped.append(dict(folder=folder, reason='request_hash_not_bound_by_audit')); continue
        binding = identity(request, audit)
        fixture = request['fixture']; key = fixture['category']+'/'+request['method']
        if audit.get('fixture_id') != fixture['id'] or audit.get('method') != request['method'] or audit.get('split') != 'train':
            skipped.append(dict(folder=folder, reason='request_audit_identity_mismatch')); continue
        locked = configs[key]
        matches = request['x'] == locked['x'] and request['teacher'] == locked['teacher']
        value = dict(folder=folder, fixture_id=fixture['id'], category=fixture['category'], method=request['method'],
            phase=request['phase'], selected_search_anchor=folder in selected,
            matches_locked_parameters=matches, eligible=audit.get('eligible') is True,
            esn_label_eligible=audit.get('esn_label_eligible') is True,
            identity_sha256=digest(binding), identity=binding)
        rows.append(value); groups[value['identity_sha256']].append(value); audits[folder]=audit
    duplicate_groups = [dict(identity_sha256=key, identity=values[0]['identity'], executions=len(values),
        repeat_executions=len(values)-1, fixture_ids=sorted({v['fixture_id'] for v in values}),
        folders=[v['folder'] for v in values], phases=[v['phase'] for v in values])
        for key,values in groups.items() if len(values)>1]
    comparisons = []
    for values in groups.values():
        source = [v for v in values if v['selected_search_anchor']]
        copies = [v for v in values if v['phase'] == 'collection' and v['matches_locked_parameters']]
        for left in source:
            for right in copies:
                if left['folder'] == right['folder']: continue
                evidence = dict(search=left['folder'], collection=right['folder'], identity_sha256=left['identity_sha256'],
                    arrays_checked=False, files=[])
                if compare_arrays:
                    for value in (left, right):
                        folder = value['folder']
                        for name in ('request.json','audit.json','execution.json'):
                            if sha(raw_root/folder/name) != hashes[folder+'/'+name]:
                                raise ValueError('Raw metadata changed since frozen review: '+folder+'/'+name)
                    left_files = {name for name in audits[left['folder']]['files_sha256'] if name.endswith('.npz')}
                    right_files = {name for name in audits[right['folder']]['files_sha256'] if name.endswith('.npz')}
                    evidence['npz_file_sets_equal'] = left_files == right_files
                    evidence['npz_evidence_present'] = bool(left_files and right_files)
                    evidence['left_only_npz'] = sorted(left_files-right_files)
                    evidence['right_only_npz'] = sorted(right_files-left_files)
                    for name in sorted(left_files & right_files):
                        if Path(name).is_absolute() or '..' in Path(name).parts: raise ValueError('Unsafe NPZ path')
                        paths = [raw_root/v['folder']/name for v in (left,right)]
                        actual = [sha(p) for p in paths]
                        expected = [audits[v['folder']]['files_sha256'][name] for v in (left,right)]
                        if actual != expected: raise ValueError('Raw NPZ hash differs from saved audit: '+name)
                        evidence['files'].append(dict(file=name, left_sha256=actual[0], right_sha256=actual[1],
                                                       **compare_npz(*paths)))
                    evidence['arrays_checked'] = bool(evidence['files'])
                    evidence['all_npz_arrays_equal'] = (evidence['npz_file_sets_equal'] and all(
                        v['arrays_equal'] for v in evidence['files'])) if evidence['files'] else None
                comparisons.append(evidence)
    inventories = []
    for category in sorted({r['category'] for r in rows}):
        for method in sorted({r['method'] for r in rows if r['category'] == category}):
            subset = [r for r in rows if r['category'] == category and r['method'] == method]
            locked_subset = [r for r in subset if r['matches_locked_parameters']]
            inventories.append(dict(category=category, method=method, completed_executions=len(subset),
                unique_training_fixture_ids=len({r['fixture_id'] for r in subset}),
                unique_execution_identities=len({r['identity_sha256'] for r in subset}),
                duplicate_executions=len(subset)-len({r['identity_sha256'] for r in subset}),
                unique_eligible_training_fixture_ids_any_parameters=len({r['fixture_id'] for r in subset if r['eligible']}),
                locked_parameter_executions=len(locked_subset),
                unique_eligible_training_fixture_ids_locked_parameters=len({r['fixture_id'] for r in locked_subset if r['eligible']}),
                unique_eligible_vmc_labels_any_phase=len({r['fixture_id'] for r in subset if method=='vmc' and r['eligible'] and r['esn_label_eligible']}),
                unique_eligible_vmc_labels_collection=len({r['fixture_id'] for r in subset if method=='vmc' and r['phase']=='collection' and r['eligible'] and r['esn_label_eligible']})))
    result = dict(script_sha256=sha(Path(__file__)), review_sha256=expected_review_sha256,
        original_run=str(raw_root), snapshot_hashes_verified=loaded, compare_arrays_requested=compare_arrays,
        accounting=inventories, duplicate_identity_groups=duplicate_groups, selected_search_collection_pairs=comparisons,
        completed_training_rows=rows, skipped_incomplete_or_invalid=skipped,
        semantics='Execution identity includes registered physical config, recorded compiled model hash, seed, method, x and teacher config. MJB model hashes are verified frozen metadata, not rehashed model files by this supplement. Repeated collection does not create another unique fixture/label. Any-parameter eligible counts are data inventory, not one fixed policy success rate. ZIP hash inequality alone does not imply array differences. No not-completed NPZ is opened; absent NPZ evidence is unknown, never vacuous equality.')
    output.mkdir(parents=True)
    (output/'review.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', required=True, type=Path)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--review-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--compare-arrays', action='store_true')
    args=parser.parse_args()
    result=review_duplicates(args.review,args.run,args.output,args.review_sha256,args.compare_arrays)
    print(json.dumps(dict(output=str(args.output), duplicate_groups=len(result['duplicate_identity_groups']),
        search_collection_pairs=len(result['selected_search_collection_pairs']))))


if __name__=='__main__': main()
