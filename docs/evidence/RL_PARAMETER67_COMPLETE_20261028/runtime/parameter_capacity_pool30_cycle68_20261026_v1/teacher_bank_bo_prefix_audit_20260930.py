"""Replay recorded BO decisions using frozen training-history prefixes only.

This checks record consistency and provenance under the SAME optimizer implementation;
it is not an independent validation of GP, acquisition mathematics, or BO quality.
Never reads validation or runs dynamics. Missing decisions remain explicitly pending.
"""
import argparse
import hashlib
import importlib.util
import json
import platform
import resource
import sys
from pathlib import Path

import numpy as np
import scipy


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Independent report already exists; use a new output')
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    sys.dont_write_bytecode = True
    snapshots = {}
    def read(relative):
        path = args.run / relative
        raw = path.read_bytes()
        digest = sha_bytes(raw)
        if relative in snapshots and snapshots[relative] != digest:
            raise RuntimeError(f'Input changed during read: {relative}')
        snapshots[relative] = digest
        return json.loads(raw)
    manifest = read('source/archive_manifest.json')
    mismatches = [name for name, expected in manifest.items()
                  if sha_bytes((args.run / 'source' / name).read_bytes()) != expected]
    if mismatches:
        raise RuntimeError(f'Frozen source mismatch: {mismatches}')
    plan = read('plan.json')
    source = args.run / 'source/tools/teacher_bank_design_20260930.py'
    spec = importlib.util.spec_from_file_location('frozen_prefix_design', source)
    design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(design)
    results, pending, groups = [], [], []
    for ci, category in enumerate(plan['categories']):
        for method in plan['methods']:
            group = f'search/{category}/{method}'
            history = read(f'{group}/history.json')
            # Check each available prefix observation against original train audits.
            provenance = []
            for index, item in enumerate(history):
                if index >= plan['search_candidates_per_category']:
                    raise ValueError('Unexpected history beyond frozen budget')
                decision = read(f'{group}/c{index:02d}/decision.json')
                rows, requests = [], []
                for anchor in plan['anchor_indices']:
                    base = f'{group}/c{index:02d}/{anchor}'
                    audit = read(f'{base}/audit.json')
                    request = read(f'{base}/request.json')
                    if (request['phase'] != 'search' or request['method'] != method
                            or request['fixture']['split'] != 'train' or audit['split'] != 'train'
                            or request['fixture']['category'] != category
                            or request['fixture']['id'] != f'{category}_train_{anchor:04d}'
                            or audit['fixture_id'] != request['fixture']['id']
                            or request['x'] != item['x'] or request['x'] != decision['x']):
                        raise ValueError(f'Invalid training-prefix provenance: {base}')
                    if audit['eligible'] != (audit['constraint'] <= 0):
                        raise ValueError('Inconsistent per-anchor eligibility')
                    rows.append(audit)
                    requests.append(request)
                eligible = sum(row['eligible'] for row in rows)
                failed = len(rows) - eligible
                severity = max(max(row['constraint'], 0) for row in rows)
                expected = dict(index=index, x=decision['x'], total=len(rows), eligible_count=eligible,
                    failed_anchor_count=failed, violation_proxy=float(severity),
                    constraint=-1. if failed == 0 else failed + .25 * severity / (1 + severity),
                    score=float(np.mean([row['score'] for row in rows])))
                mismatched = [key for key, value in expected.items() if item[key] != value]
                if mismatched:
                    raise ValueError(f'Training summary mismatch {group}/{index}: {mismatched}')
                provenance.append(dict(index=index, anchor_count=len(rows),
                    source='original search/train audit.json and request.json', exact_summary_match=True))
            groups.append(dict(group=f'{category}/{method}', available_history=len(history), provenance=provenance))
            for index in range(plan['warm_candidates'], plan['search_candidates_per_category']):
                relative = f'{group}/c{index:02d}/decision.json'
                if not (args.run / relative).exists():
                    pending.append(relative)
                    continue
                decision = read(relative)
                prefix = history[:index]
                if len(prefix) != index or decision['history_count'] != index:
                    raise ValueError(f'Missing or inconsistent original prefix: {relative}')
                if decision['algorithm'] != 'constrained_gp_bo':
                    raise ValueError(f'Unexpected decision algorithm: {relative}')
                seed = design.SEED + ci * 100 + index
                reproduced = np.asarray(design.propose(prefix, seed))
                original = np.asarray(decision['x'])
                if reproduced.shape != original.shape:
                    raise ValueError('Candidate dimension mismatch')
                error = float(np.max(np.abs(reproduced - original)))
                results.append(dict(category=category, method=method, index=index, seed=seed,
                    history_count=index, only_prefix_used=True, prefix_indices=[r['index'] for r in prefix],
                    prefix_feasible_count=sum(r['constraint'] <= 0 for r in prefix),
                    dimensions=len(original), original_x=original.tolist(), reproduced_x=reproduced.tolist(),
                    max_abs_error=error, exact_match=bool(np.array_equal(reproduced, original)),
                    prefix_summary_provenance_verified=all(p['exact_summary_match'] for p in provenance[:index]),
                    decision_relative_path=relative))
    changed = [name for name, digest in snapshots.items()
               if sha_bytes((args.run / name).read_bytes()) != digest]
    report = dict(scope=__doc__, run=str(args.run.resolve()), host=platform.node(),
        runtime=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__),
        script_sha256=sha_bytes(Path(__file__).read_bytes()), source_manifest_sha256=snapshots['source/archive_manifest.json'],
        design_source_sha256=sha_bytes(source.read_bytes()), source_manifest_verified=True,
        source_manifest_count=len(manifest), source_files_sha256=manifest, inputs_sha256=snapshots,
        expected_decisions=27, replayed_count=len(results), exact_match_count=sum(r['exact_match'] for r in results),
        failed_decisions=[r['decision_relative_path'] for r in results if not r['exact_match']],
        pending_decisions=pending, decisions=results, groups=groups,
        stable_snapshot=not changed, changed_inputs=changed,
        complete=not pending and not changed and len(results) == 27 and all(r['exact_match'] for r in results),
        dynamics_run=False, validation_read=False, peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        limitation='Replaying the same implementation proves recorded-prefix consistency only. It does not independently validate optimization quality, physical metrics, or historical process memory provenance. Training source rows are checked against saved requests/audits, not independently re-evaluated.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({key: report[key] for key in ('replayed_count', 'exact_match_count', 'failed_decisions', 'pending_decisions', 'stable_snapshot', 'complete', 'peak_rss_kib')}))
    print(json.dumps(dict(output=str(args.output), sha256=sha_bytes(args.output.read_bytes()))))


if __name__ == '__main__':
    main()
