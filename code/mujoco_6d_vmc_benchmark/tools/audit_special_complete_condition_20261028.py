"""Audit one complete nine-model condition without claiming the matrix is complete."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

from audit_special_frozen108_20261028 import verify_episode
from prepare_special_frozen_test_20261028 import manifest, read, require, sha


def audit_condition(preparation, condition_id):
    plan = read(preparation / 'REGISTRATION.json')
    root = Path(plan['evaluation'])
    state_bytes = (root / 'execution.json').read_bytes()
    state = json.loads(state_bytes)
    lock = read(root / 'INPUT_MODEL_LOCK.json')
    models = {m['name']: m for m in lock['models']}
    require(len(models) == len(lock['models']) == 9, 'Expected nine selected models')
    require(sha(root / 'INPUT_MODEL_LOCK.json') == sha(Path(plan['training']) / 'MODEL_LOCK.json'),
            'Model lock drift')
    require(manifest(root / 'source') == plan['physics_source_sha256'], 'Physics source drift')
    parent_root = Path(plan['source_run'])
    conditions = {c['id']: c for c in read(parent_root / 'CONDITIONS.json')['conditions']}
    require(condition_id in conditions, 'Unknown condition')
    require(sha(root / 'CONDITIONS.json') == sha(parent_root / 'CONDITIONS.json'), 'Condition drift')
    parent = read(parent_root / 'REGISTRATION.json')
    parent['formal_model_sha256'] = read(parent_root / 'PROTOCOL.json')['formal_model_sha256']
    rows = [r for r in state['results'] if r['condition'] == condition_id]
    require(Counter(r['method'] for r in rows) == Counter({m: 1 for m in models}),
            'Condition incomplete or duplicate models')
    verified_sources = set()
    checks = []
    for row in rows:
        model = models[row['method']]
        require(sha(Path(model['checkpoint'])) == model['checkpoint_sha256'], 'Selected model drift')
        check = verify_episode(row, model, conditions[condition_id], root,
                               root / 'source', parent, verified_sources)
        summary = read(Path(row['run']) / 'rollout.json')
        check.update(family=model['family'], seed=model['seed'],
                     task_success=row['task_success'], strict_success=row['strict_success'],
                     duration_s=row['duration_s'], completion_time_s=row['completion_time_s'],
                     comfort=row['comfort'], terminal_stage=summary.get('stage'))
        checks.append(check)
        print(json.dumps({'audited': row['method'], 'substeps': check['substeps']}), flush=True)
    # Check the same completed rows still exist after the live coordinator advances.
    current = read(root / 'execution.json')
    require([r for r in current['results'] if r['condition'] == condition_id] == rows,
            'Completed rows changed during audit')
    return dict(status='complete_condition_saved_evidence_passed',
                created_utc=datetime.now(timezone.utc).isoformat(), condition=condition_id,
                matrix_completed_at_snapshot=state['completed'], expected_matrix_episodes=108,
                verified_episodes=len(checks), verified_substeps=sum(c['substeps'] for c in checks),
                preparation=str(preparation), auditor_sha256=sha(Path(__file__)),
                episode_auditor_sha256=sha(Path(__file__).with_name('audit_special_frozen108_20261028.py')),
                model_lock_sha256=sha(root / 'INPUT_MODEL_LOCK.json'), rows=rows, checks=checks,
                t_ref_s=None, spt_status='deferred_until_complete_108',
                limitation='One condition only; no overall ranking or global SPT. Saved-substep arithmetic, hashes and original actor/filter receipts checked, not independent dynamics reintegration. Comfort is a contact-conditioned engineering proxy, not validated human safety.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--condition', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Preserve prior audit')
    result = audit_condition(args.preparation.resolve(), args.condition)
    with args.output.open('x') as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'verified_episodes', 'verified_substeps')}))
