"""Audit the actual v9 direct-scope 108 run, without a fictitious v8 handoff.

Reuses independent per-episode arithmetic and conditional-SPT checks. This is
the previously inspected office transfer test, not the new scene main matrix.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import os
from pathlib import Path

from audit_special_frozen108_20261028 import equal, summaries, verify_episode
from prepare_special_frozen_test_20261028 import ROOT, read, require, sha, write


def complete(state, report):
    require(state['status'] == report['status'] == 'complete', 'Original108 not complete; do not audit live run')
    require(state['completed'] == state['expected'] == len(state['results']) == len(report['rows']) == 108,
            'Require all108 completed results')


def verify_v9_episode(row, model, condition, root, source, parent, verified):
    execution = read(Path(row['run'])/'execution.json')
    # sys.executable retained an absolute "repo/../venv" spelling. Normalize
    # only lexical dot segments: resolving the Python symlink would wrongly
    # equate different virtual environments using the same base binary.
    recorded, expected = execution['python'], parent['simulation_python']
    require(Path(recorded).is_absolute() and Path(expected).is_absolute()
            and os.path.normpath(recorded) == os.path.normpath(expected), 'Virtual environment path changed')
    matched_parent = dict(parent, simulation_python=recorded)
    return verify_episode(row, model, condition, root, source, matched_parent, verified)


def audit(root):
    state, report, reg = [read(root/n) for n in ('execution.json', 'REPORT.json', 'REGISTRATION.json')]
    complete(state, report)
    require(sha(root/'REPORT.json') == state['report_sha256'], 'Completed report hash mismatch')
    require(report['registration_sha256'] == sha(root/'REGISTRATION.json'), 'Registration changed')
    require(sha(root/'coordinator.py') == reg['coordinator_sha256'], 'Coordinator changed')
    require(root.name == 'special_scene_frozen108_20261029_v9', 'Only original v9 transfer run is supported')
    require(reg['physics_dt'] == .00005 and reg['horizon_s'] == 55. and not reg['server_compute'], 'Protocol changed')
    training = ROOT/'outputs/special_scene_direction_retrain_20261029_v9'
    lock = read(root/'INPUT_MODEL_LOCK.json')
    require(sha(training/'MODEL_LOCK.json') == sha(root/'INPUT_MODEL_LOCK.json') == reg['model_lock_sha256'], 'Model lock changed')
    fit = read(training/'FIT_AUDIT.json')
    require(fit['status'] == 'passed' and fit['model_lock_sha256'] == reg['model_lock_sha256'], 'Fit audit mismatch')
    require(sha(training/'data/training_data.npz') == lock['training_data_sha256'] == fit['dataset_sha256']
            == '120173888964ee0545393cd0d2685c794f7aa261626463fa7c10fc981b9c6407', 'Wrong v9 data')
    models = {m['name']: m for m in lock['models']}
    require(len(models) == len(lock['models']) == 9 and set(models) == set(reg['methods']), 'Wrong nine models')
    expected_models = Counter({(f, s): 1 for f in ('esn_ridge', 'rnn_scratch', 'mlp_scratch')
                               for s in (2026102801, 2026102802, 2026102803)})
    require(Counter((m['family'], m['seed']) for m in models.values()) == expected_models, 'Family/seed mismatch')
    for model in models.values():
        require(sha(Path(model['checkpoint'])) == sha(root/'checkpoints'/(model['name']+'.npz'))
                == model['checkpoint_sha256'], 'Checkpoint changed')
        require(sha(Path(model['metadata'])) == model['metadata_sha256'], 'Fit metadata changed')
    parent_root = Path(reg['source_run'])
    parent, protocol = read(parent_root/'REGISTRATION.json'), read(parent_root/'PROTOCOL.json')
    require(sha(parent_root/'PROTOCOL.json') == parent['protocol_sha256'] == sha(root/'PARENT_PROTOCOL.json'), 'Parent protocol changed')
    require(sha(parent_root/'CONDITIONS.json') == parent['condition_sha256'] == sha(root/'CONDITIONS.json'), 'Conditions changed')
    conditions = {c['id']: c for c in read(root/'CONDITIONS.json')['conditions']}
    require(len(conditions) == 12 and set(conditions) == set(reg['conditions']), 'Wrong12 conditions')
    parent['formal_model_sha256'] = protocol['formal_model_sha256']
    snapshot = read(root/'PARENT_SOURCE_HASHES.json')['manifest']
    for name, digest in snapshot.items():
        require(sha(root/name) == digest, 'Frozen source snapshot changed: '+name)
    rows = report['rows']
    expected = Counter({(m, c): 1 for m in models for c in conditions})
    require(Counter((r['method'], r['condition']) for r in rows) == expected, 'Missing/duplicate matrix cells')
    require(state['results'] == rows, 'Coordinator results differ from final report')
    verified = set()
    checks = [verify_v9_episode(r, models[r['method']], conditions[r['condition']], root,
                            root/'source', parent, verified) for r in rows]
    ref, methods, families = summaries(rows, models)
    equal(report['t_ref_s'], ref, 'T_ref mismatch')
    for row in rows:
        expected_spt = ref/max(ref, row['completion_time_s']) if row['task_success'] and row['strict_success'] else None
        equal(row['spt'], expected_spt, 'Conditional SPT mismatch')
    require(len(report['methods']) == 9 and {m['method'] for m in report['methods']} == set(models), 'Summary coverage')
    for method in report['methods']:
        for key, value in methods[method['method']].items():
            equal(method[key], value, 'Summary mismatch: '+key)
    require(sha(root/'REPORT.json') == state['report_sha256'], 'Report changed during audit')
    return dict(status='v9_office_transfer108_saved_evidence_audit_passed',
        created_utc=datetime.now(timezone.utc).isoformat(), verified_episodes=108,
        root=str(root), report_sha256=state['report_sha256'],
        registration_sha256=sha(root/'REGISTRATION.json'), model_lock_sha256=reg['model_lock_sha256'],
        auditor_sha256=sha(Path(__file__)), episode_auditor_sha256=sha(ROOT/'tools/audit_special_frozen108_20261028.py'),
        t_ref_s=ref, methods=methods, family_summary=families, episode_checks=checks,
        limitation='Complete previously inspected office combination-transfer matrix only; not isolated-scene main matrix or unseen test. Saved-substep arithmetic and replay receipts, not dynamics reintegration; actual-human-contact comfort is an engineering proxy.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    require(not a.output.exists(), 'Preserve previous audits')
    result = audit(a.root.resolve())
    write(a.output, result)
    print(result['status'])
