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
    os.sched_setaffinity(0, {52})
    reg = json.loads((root/'REGISTRATION.json').read_text())
    assert reg['cycle'] == 16 and reg['action_seed'] == 2026102626
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
    deadline = time.monotonic()+7200
    rows, seen, states = [], set(), []
    for job in launch['jobs']:
        folder = Path(job['output'])
        while not (folder/'POLICY_UNCHANGED.json').exists():
            assert time.monotonic() < deadline, 'Finite evaluation deadline exceeded'
            assert not (folder/'FAILURE.json').exists(), 'Original evaluator failed; do not repeat'
            if not Path(f"/proc/{job['pid']}").exists():
                raise RuntimeError('Original evaluator exited without invariant receipt')
            time.sleep(5)
        result = json.loads((folder/'RESULTS.json').read_text())
        state = json.loads((folder/'POLICY_UNCHANGED.json').read_text())
        gate = json.loads((folder/'EXTERNAL_ACTION_RNG_GATE.json').read_text())
        assert result['finished'] and state['full_learner_state_unchanged']
        assert state['new_optimizer_updates'] == 0 and gate['passed'] and gate['full_state_unchanged']
        states.append(state['initial_state_digest'])
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
            physical = summarize(path, 'direct_formal16_frozen_stochastic', case)
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
        limitation='Frozen complete16 on all30 registered training conditions with one external stochastic action seed. This evaluates the unchanged learned stochastic policy; it is not an independent training seed, held-out test, deterministic-mode evaluation, or final ESN comparison. Physical/filter/torque replay checks saved telemetry; full dynamics are not independently rerun. No final SPT reference is selected here.')
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
