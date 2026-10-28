"""Review completed collection/probe receipts without launching physics.

Preserve all failures, verify input hashes, and report a bounded teacher probe
against its exact registered conditions. This is not a test-set evaluation.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def evidence(folder):
    qualification = read(folder / 'DEMONSTRATION_QUALIFICATION.json')
    execution = read(folder / 'execution.json')
    assert execution['status'] == 'complete'
    for name, digest in qualification['input_hashes'].items():
        if sha(folder / name) != digest:
            raise ValueError(f'Stale evidence: {folder / name}')
    row = dict(folder=str(folder), status=qualification['status'],
               task=qualification['task_success'], safety=qualification['safety_valid'],
               contact=qualification['scene_contact_valid'],
               failed_checks=[k for k, v in qualification['checks'].items() if not v],
               teacher_sha256=execution['teacher_config_sha256'],
               model_sha256=execution['model_sha256'],
               max_penetration_mm=qualification['metrics']['max_external_penetration_m'] * 1000,
               peak_torque_nm=max(qualification['metrics']['peak_torque_nm']),
               qualification_sha256=sha(folder / 'DEMONSTRATION_QUALIFICATION.json'),
               execution_sha256=sha(folder / 'execution.json'))
    if execution['scene'] == 'rod':
        behavior = read(folder / 'ROD_YIELD_REJOIN_AUDIT_V3.json')
        row['rod'] = {k: behavior[k] for k in (
            'hand_contact_first_s', 'pass_s', 'rejoin_confirmed_s', 'retract_start_s')}
        row['rod']['failed_checks'] = [k for k, v in behavior['checks'].items() if not v]
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection', type=Path, required=True)
    parser.add_argument('--probe', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    collection = args.collection.resolve()
    plan = read(collection / 'COLLECTION_PLAN.json')
    state = read(collection / 'COLLECTION_PROGRESS.json')
    assert state['status'] in ('qualified_complete', 'finished_with_nonqualified_demonstrations')
    assert len(state['episodes']) == len(plan['episodes']) == 30
    assert state['plan_sha256'] == sha(collection / 'COLLECTION_PLAN.json')
    rows = []
    for entry, receipt in zip(plan['episodes'], state['episodes']):
        assert entry['id'] == receipt['id']
        folder = Path(entry['folder'])
        execution = read(folder / 'execution.json')
        assert execution['collection_plan_sha256'] == state['plan_sha256']
        assert execution['collection_identity'] == entry['id']
        assert execution['teacher_config_sha256'] == plan['teacher_config_sha256']
        row = evidence(folder)
        assert row['status'] == receipt['status']
        rows.append(dict(id=entry['id'], scene=entry['scene'], split=entry['split'], **row))
    result = dict(schema='sii-special-collection-review-v1',
                  reviewed_utc=datetime.now(timezone.utc).isoformat(),
                  collection=str(collection), plan_sha256=state['plan_sha256'], rows=rows,
                  per_scene={s: dict(Counter(r['status'] for r in rows if r['scene'] == s))
                             for s in ('rod', 'ball', 'corner')},
                  all30_qualified=all(r['status'] == 'qualified' for r in rows),
                  limitations='Development/collection gates and saved evidence hashes; not frozen test Task/Strict certification or independent physical re-integration.')
    if args.probe:
        probe = args.probe.resolve()
        registration = read(probe / 'REGISTRATION.json')
        progress = read(probe / 'execution.json')
        assert progress['status'] == 'complete' and len(progress['episodes']) == 4
        assert progress['registration_sha256'] == sha(probe / 'REGISTRATION.json')
        paired = []
        for entry, receipt in zip(registration['cases'], progress['episodes']):
            assert entry['id'] == receipt['id']
            candidate = evidence(probe / entry['id'] / entry['scene'])
            baseline = evidence(Path(entry['baseline']))
            assert candidate['status'] == receipt['status']
            assert candidate['model_sha256'] == baseline['model_sha256'] == entry['expected_model_sha256']
            assert baseline['execution_sha256'] == entry['baseline_execution_sha256']
            assert candidate['teacher_sha256'] == registration['candidate_config_sha256']
            paired.append(dict(id=entry['id'], scene=entry['scene'], baseline=baseline, candidate=candidate))
        result['probe'] = dict(root=str(probe), registration_sha256=sha(probe / 'REGISTRATION.json'),
                               pairs=paired,
                               all4_qualified=all(p['candidate']['status'] == 'qualified' for p in paired),
                               scope='Two failed training rod conditions, first ball training condition, original corner development. No validation/test selection.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(output=str(args.output), per_scene=result['per_scene'],
                          all30_qualified=result['all30_qualified'],
                          probe_all4_qualified=result.get('probe', {}).get('all4_qualified'))))


if __name__ == '__main__':
    main()
