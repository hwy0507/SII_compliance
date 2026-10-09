"""Read-only development census and independent physical metric reconstruction.

Count only completed managed receipts. Retain infrastructure failures separately
from physical task failures, and leave missing evaluations explicitly pending.
Never run a policy, train, select a model, or read final conditions.
"""
import argparse
from pathlib import Path

import numpy as np

from office_v7_uniform24_20261008 import read, write, sha, now
from research72_checkpoint_20261003 import checkpoint_hashes


def audit_run(run, receipt, protocol):
    for path, digest in receipt.get('artifacts', {}).items():
        assert sha(path) == digest
    audit = read(run/'AUDIT.json')
    result = read(run/'rollout.json')
    assert sha(run/'rollout.mjb') == audit['model_sha256'] == protocol['formal_model_sha256']
    assert sha(run/'rollout.npz') == audit['trace_sha256']
    assert sha(run/'execution_chain.npz') == audit['chain_sha256']
    assert audit['raw_actor_replay_max_abs'] == 0 and audit['normalization_unchanged']
    assert audit['common_filter_replay_max_abs'] == 0
    assert audit['task_success'] == result['task_success']
    assert audit['strict_success'] == result['strict_success']
    raw_metrics = run/'rollout_metrics/substep_metrics.npz'
    with np.load(raw_metrics, allow_pickle=False) as archive:
        dt = archive['dt'].astype(float)
        assert len(dt) and np.isfinite(dt).all()
        np.testing.assert_allclose(dt, protocol['physics_dt_s'], rtol=0, atol=1e-12)
        error = archive['error'].astype(float)
        rmse = 1000*float(np.sqrt(np.sum(dt[:, None]*error**2)/dt.sum()))
        speed = float(np.linalg.norm(archive['twist'][:, :3].astype(float), axis=1).max())
        torque = float(np.abs(archive['qfrc_actuator'].astype(float)).max())
    np.testing.assert_allclose([rmse, torque, speed],
        [audit['rmse_mm'], audit['peak_torque_nm'], audit['peak_speed_mps']], rtol=1e-6, atol=1e-6)
    np.testing.assert_allclose(dt.sum(), audit['physical_seconds'], rtol=0, atol=1e-7)
    if audit['full_horizon']:
        assert len(dt) == round(protocol['duration_s']/protocol['physics_dt_s'])
    with np.load(run/'baseline_policy.npz', allow_pickle=False) as policy, \
            np.load(run/'rollout.npz', allow_pickle=False) as trace, \
            np.load(run/'execution_chain.npz', allow_pickle=False) as chain:
        assert policy['observation'].shape[1] == 48
        np.testing.assert_array_equal(policy['observation'], trace['observation'])
        np.testing.assert_array_equal(policy['action'], trace['applied_action'])
        np.testing.assert_array_equal(policy['action'], chain['requested_action'])
        assert np.isfinite(policy['raw_action']).all()
    return dict(run=str(run), task=audit['task_success'], strict=audit['strict_success'],
        full_horizon=audit['full_horizon'], stage=audit['stage'], abort_reason=audit['abort_reason'],
        physical_steps=len(dt), rmse_mm=rmse, peak_torque_nm=torque, peak_speed_mps=speed,
        penetration_mm=audit['penetration_mm'], placement_error_xy_m=audit['placement_error_xy_m'],
        raw_metrics_sha256=sha(raw_metrics), audit_sha256=sha(run/'AUDIT.json'),
        checkpoint_manifest_sha256=sha(run/'ADAPTED_RL_CHECKPOINT.json'),
        model_sha256=audit['model_sha256'], trace_sha256=audit['trace_sha256'],
        worker_actor_replay_max_abs=0., independent_physical_metrics_passed=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    root = args.root.resolve()
    protocol = read(root/'PROTOCOL.json')
    conditions = read(root/'CONDITIONS.json')
    assert sha(root/'CONDITIONS.json') == protocol['condition_file_sha256']
    identities = [c['id'] for c in conditions['conditions'] if c['role'] == 'development']
    assert len(identities) == 8 and len(set(identities)) == 8
    report = dict(created_utc=now(), source_sha256=sha(__file__),
        protocol_sha256=sha(root/'PROTOCOL.json'), scope='development only; no final conditions',
        methods=[], preserved_infrastructure_failures=[], new_physics_steps=0, gradient_updates=0,
        limitation='A partial census is not a paired ranking; 11k interactions do not establish convergence.')
    for job in protocol['jobs']:
        rows, pending = [], []
        checkpoint = None
        for identity in identities:
            label = job['name']+'_segment011k__'+identity
            path = root/(label+'.execution.json')
            if not path.exists():
                pending.append(dict(condition=identity, status='not_started')); continue
            receipt = read(path)
            if receipt['status'] == 'failed_preserved':
                original = root/label
                message = (root/(label+'.log')).read_text()
                prephysics = not (original/'rollout.npz').exists()
                report['preserved_infrastructure_failures'].append(dict(
                    receipt=str(path), receipt_sha256=sha(path), no_raw_physics=prephysics))
                retry = root/(label+'_assets_retry_v2.execution.json')
                if not retry.exists():
                    pending.append(dict(condition=identity, status='failed_preserved')); continue
                assert prephysics and 'FileNotFoundError: MuJoCo Menagerie not found:' in message
                receipt = read(retry)
                assert receipt['preserved_failed_attempt']['receipt_sha256'] == sha(path)
                label += '_assets_retry_v2'
            if receipt['status'] != 'complete':
                pending.append(dict(condition=identity, status=receipt['status'])); continue
            run = root/label
            if checkpoint is None:
                checkpoint = read(root/(job['name']+'_segment011k.checkpoint.json'))
                assert checkpoint['controller'] == job['controller']
                assert checkpoint_hashes(Path(checkpoint['checkpoint'])) == checkpoint['hashes']
                assert sha(checkpoint['training_protocol']) == checkpoint['training_protocol_sha256']
            assert read(run/'ADAPTED_RL_CHECKPOINT.json') == checkpoint
            role = read(run/'REPAIR_ROLE.json')
            assert role['condition'] == next(c for c in conditions['conditions'] if c['id'] == identity)
            assert role['protocol_sha256'] == sha(root/'PROTOCOL.json')
            assert role['worker_kind'] == 'adapted_rl'
            row = audit_run(run, receipt, protocol)
            row['condition'] = identity
            row['parameter_audit_present'] = (run/'INDEPENDENT_PARAMETER_AUDIT.json').exists() if job['controller'] else None
            rows.append(row)
        method = dict(method=job['name'], completed=len(rows), planned=len(identities),
            task=sum(r['task'] for r in rows), strict=sum(r['strict'] for r in rows),
            all_development_complete=len(rows) == len(identities), episodes=rows, pending=pending)
        report['methods'].append(method)
        print(job['name'], 'complete', len(rows), '/8', 'task', method['task'], 'strict', method['strict'])
    write(args.output, report)


if __name__ == '__main__':
    main()
