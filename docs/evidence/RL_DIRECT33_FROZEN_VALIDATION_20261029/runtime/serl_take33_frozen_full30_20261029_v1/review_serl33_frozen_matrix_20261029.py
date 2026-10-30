"""Review a registered full training-cohort frozen policy, with no optimization."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def main(root):
    os.sched_setaffinity(0, {3})
    reg = json.loads((root/'REGISTRATION.json').read_text())
    assert reg['cycle'] == 33 and reg['action_seed'] == 2026102626
    assert reg['maximum_episodes'] == 30 and reg['maximum_physical_substeps'] == 33000000
    assert reg['noise_schedule'] == 'independent'
    for ref in reg['inputs'].values():
        assert sha(ref['path']) == ref['sha256']
    for ref in reg['sources'].values():
        assert sha(ref['path']) == ref['sha256']
    protocol = json.loads(Path(reg['inputs']['training_registration']['path']).read_text())
    conditions = {c['id']: c for c in protocol['conditions']}
    assert len(conditions) == 30
    sys.path[:0] = [reg['evaluation_runtime'], str(Path(protocol['runtime'])/'source/tools')]
    from summarize_published_episode_audit_20261025 import summarize
    from replay_published_filter_audit_20261025 import audit as filter_audit
    from replay_published_torque_audit_20261025 import audit as torque_audit
    launch = json.loads((root/'LAUNCH.json').read_text())
    deadline = time.monotonic()+21600
    rows, seen, states = [], set(), []
    for job in launch['jobs']:
        folder = Path(job['output'])
        while not (folder/'POLICY_UNCHANGED.json').exists():
            assert time.monotonic() < deadline, 'Finite evaluation deadline exceeded'
            assert not (folder/'FAILURE.json').exists(), 'Original evaluator failed; do not repeat'
            process = Path(f"/proc/{job['pid']}")
            if process.exists():
                assert process.joinpath('stat').read_text().rsplit(')',1)[1].split()[19] == job['start'], 'PID identity changed'
            if not process.exists():
                raise RuntimeError('Original evaluator exited without invariant receipt')
            time.sleep(5)
        result = json.loads((folder/'RESULTS.json').read_text())
        state = json.loads((folder/'POLICY_UNCHANGED.json').read_text())
        gate = json.loads((folder/'EXTERNAL_ACTION_RNG_GATE.json').read_text())
        assert result['finished'] and state['full_learner_state_unchanged']
        assert state['new_optimizer_updates'] == 0 and gate['passed'] and gate['full_state_unchanged']
        restore = json.loads((folder/'FULL_STATE_RESTORE.json').read_text())
        assert restore['passed'] and restore['cycle'] == 33
        assert restore['full_replay_state_exact'] and restore['full_learner_state_exact']
        assert restore['replay_capacity'] == 2000000 and restore['historical_capacity_entry'] == 23
        assert restore['checkpoint_sha256'] == reg['inputs']['checkpoint']['sha256']
        recovery=restore['recovery_state'];assert recovery['quarantined_pending']==930 and recovery['original_pending_exact'] and recovery['original_pending_raw_derived_exact'] and recovery['pending_not_mature_or_sampleable']
        assert not recovery['complete25_invented'] and recovery['complete_cycles_after_recovery']==list(range(26,34))
        assert state['recovery_state']==recovery
        assert state['full_replay_state_unchanged'] and state['replay_writes'] == 0
        assert state['replay_digest'] == restore['replay_digest']
        assert state['history_digest'] == restore['history_digest']
        states.append((state['initial_state_digest'], state['replay_digest'], state['history_digest']))
        evaluation = result['evaluation']
        assert evaluation['checkpoint_sha256'] == reg['inputs']['checkpoint']['sha256']
        assert sha(folder/'checkpoint_frozen.pt') == evaluation['checkpoint_sha256']
        assert evaluation['registration_sha256'] == reg['inputs']['training_registration']['sha256']
        assert evaluation['action_seed'] == reg['action_seed'] and not evaluation['deterministic']
        assert evaluation['noise_schedule'] == 'independent' and evaluation['audit_substeps']
        assert evaluation['case_ids'] == job['case_ids']
        assert {e['condition'] for e in result['episodes']} == set(job['case_ids'])
        for episode in result['episodes']:
            case = episode['condition']
            assert case in conditions and case not in seen
            seen.add(case)
            path = folder/case
            assert sha(path/'rollout.mjb') == conditions[case]['model_sha256']
            physical = summarize(path, 'direct_recovery33_frozen_stochastic', case)
            filtered, torque = filter_audit(path), torque_audit(path)
            assert filtered['passed'] and torque['passed']
            assert 0 < physical['samples'] <= 1100000
            assert physical['row']['elapsed_s'] <= 55.000001
            audit = dict(physical=physical, filter=filtered, torque=torque)
            write(path/'FROZEN_PHYSICAL_REVIEW.json', audit)
            rows.append(dict(case=case, category=conditions[case]['category'],
                actions=episode['actions'], samples=physical['samples'], row=physical['row'],
                audit=dict(path=str(path/'FROZEN_PHYSICAL_REVIEW.json'),
                           sha256=sha(path/'FROZEN_PHYSICAL_REVIEW.json'))))
            write(root/'REVIEW_PROGRESS.json', dict(reviewed=len(rows), maximum=30))
    assert seen == conditions.keys() and len(rows) == 30
    assert len(set(states)) == 1
    assert sum(r['actions'] for r in rows) <= 41250
    samples = sum(r['samples'] for r in rows)
    assert samples <= reg['maximum_physical_substeps']
    for ref in reg['inputs'].values():
        assert sha(ref['path']) == ref['sha256']
    report = dict(passed=True, time=time.time(), episodes=rows, physical_samples=samples,
        task=sum(r['row']['task_success'] for r in rows),
        strict=sum(r['row']['strict_success'] for r in rows),
        full_horizon=sum(r['row']['full_horizon'] for r in rows),
        machine_violations=sum(r['row']['machine_safety_violation'] for r in rows),
        full_training_cohort=True, independent_training_seeds=1, external_action_seeds=1,
        optimizer_updates=0, replay_writes=0, formal_state_unchanged=True,
        checkpoint_sha256=reg['inputs']['checkpoint']['sha256'], convergence_claim=False,
        limitation='Frozen recovered complete33 on all30 registered training conditions with one external stochastic action seed. This evaluates the unchanged learned stochastic policy; it is not an independent training seed, held-out test, deterministic-mode evaluation, or final ESN comparison. Physical/filter/torque replay checks saved telemetry; full dynamics are not independently rerun. No final SPT reference is selected here.')
    write(root/'REVIEW.json', report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.root)
    except BaseException as error:
        write(args.root/'REVIEW_FAILURE.json', dict(error=repr(error), time=time.time()))
        raise
