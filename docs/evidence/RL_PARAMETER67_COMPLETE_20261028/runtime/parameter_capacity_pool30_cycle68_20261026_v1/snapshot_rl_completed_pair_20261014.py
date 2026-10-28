"""Snapshot completed paired jobs while unrelated campaign lanes continue.

Hardlinks are limited to closed jobs and frozen sources. Live campaign receipts
are copied under captured names; no historical execution paths are rewritten.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
from snapshot_rl_diagnosis_checkpoint_20261014 import link_tree
from rl_reward_diagnosis_audit_20261014 import read, write, sha
from research72_checkpoint_20261003 import checkpoint_hashes
from archive_tool_campaign_20261002 import make


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--pair', required=True)
    parser.add_argument('--audit', type=Path, required=True)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.output.resolve()
    protocol = read(root/'PROTOCOL.json')
    pair = next(p for p in protocol['pairs'] if p['id'] == args.pair)
    audit = read(args.audit)
    assert audit['status'] == 'passed_for_captured_complete_episodes'
    audited = {e['trace_sha256'] for e in audit['episodes']}
    names = [args.pair+'_'+arm for arm in pair['arms']]
    records = []
    for name in names:
        assert read(root/(name+'.lane.json'))['status'] == 'complete'
        training = read(root/(name+'_train/execution.json'))
        assert training['status'] == 'complete'
        for cp in training['checkpoint_rows']:
            assert checkpoint_hashes(Path(cp['path'])) == cp['hashes']
        for row in training['rows']:
            assert 'result' in row and row['trace_sha256'] in audited
            assert sha(Path(row['run'])/'rollout.npz') == row['trace_sha256']
        evaluation = read(root/(name+'.results.json'))
        assert evaluation['status'] == 'complete' and len(evaluation['evaluations']) == 4
        for row in evaluation['evaluations']:
            assert row['independent_physical_metrics_passed']
            assert sha(Path(row['run'])/'rollout.npz') == row['trace_sha256']
            assert sha(Path(row['run'])/'AUDIT.json') == row['audit_sha256']
        records.append(dict(job=name, training_steps=training['steps'],
            training_episodes=len(training['rows']), evaluations=evaluation['evaluations']))
    assert not out.exists()
    out.mkdir()
    for folder in ('source', 'parameter_fullrange'):
        link_tree(root/folder, out/folder)
    for file in ('PROTOCOL.json', 'SOURCE_HASHES.json', 'PARAMETER_HASHES.json',
                 'CONDITIONS.json', 'teacher.json', 'RUNTIME_VERSIONS.json'):
        shutil.copy2(root/file, out/file)
    for path in sorted(root.iterdir()):
        if any(path.name.startswith(name+'.') or path.name.startswith(name+'_') for name in names):
            if path.is_dir():
                link_tree(path, out/path.name)
            else:
                shutil.copy2(path, out/path.name)
    shutil.copy2(root/'execution.json', out/'CAPTURED_CAMPAIGN_EXECUTION.json')
    shutil.copy2(args.audit, out/args.audit.name)
    for name in ('snapshot_rl_completed_pair_20261014.py', 'archive_tool_campaign_20261002.py',
                 'audit_rl_reward_live_20261014.py', 'snapshot_rl_diagnosis_checkpoint_20261014.py'):
        shutil.copy2(Path(__file__).with_name(name), out/name)
    write(out/'SNAPSHOT.json', dict(status='completed_pair_snapshot',
        captured_utc=datetime.now(timezone.utc).isoformat(), original_root=str(root),
        pair=args.pair, jobs=records, source_sha256=sha(__file__),
        audit_sha256=sha(args.audit), other_campaign_jobs_not_included=True,
        new_physics_steps=0, historical_execution_paths_preserved=True))
    make(out)


if __name__ == '__main__':
    main()
