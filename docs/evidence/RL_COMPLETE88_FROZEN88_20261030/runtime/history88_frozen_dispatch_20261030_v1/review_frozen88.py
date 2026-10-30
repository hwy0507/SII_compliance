"""Collect the registered ninety frozen88 episodes without extending their budget."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def identity(pid):
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return dict(start=fields[19], state=fields[0])
    except FileNotFoundError:
        return None


def main(root):
    os.sched_setaffinity(0, {3})
    plan = json.loads((root/'PLAN.json').read_text())
    waiting = json.loads((root/'REVIEW_REGISTRATION.json').read_text())
    assert sha(__file__) == waiting['source_sha256']
    assert sha(root/'PLAN.json') == waiting['plan_sha256']
    assert plan['episodes'] == 90 and plan['maximum_substeps'] == 99000000
    assert plan['action_seed'] == 2026102638 and plan['parent_cycle'] == 88
    assert len(plan['case_ids']) == len(set(plan['case_ids'])) == 30
    deadline = time.monotonic()+21600
    while True:
        complete = True
        for job in waiting['evaluators']:
            directory = root/job['controller']
            assert not (directory/'FAILURE.json').exists(), str(directory/'FAILURE.json')
            if not (directory/'FINISHED.json').exists():
                complete = False
                state = identity(job['pid'])
                assert state is not None and state['state'] != 'Z' and state['start'] == job['start'], 'Original evaluator disappeared before FINISHED'
            else:
                assert json.loads((directory/'FINISHED.json').read_text())['passed']
        if complete:
            break
        assert time.monotonic() < deadline, '21600second wait ended; do not automatically repeat or extend'
        time.sleep(5)
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(3, 2, figsize=(11, 9), constrained_layout=True)
    results, inputs = {}, {}
    for index, method in enumerate(plan['controllers']):
        directory = root/method
        reg = json.loads((directory/'REGISTRATION.json').read_text())
        finished = json.loads((directory/'FINISHED.json').read_text())
        assert finished['full_learner_state_unchanged'] and finished['full_replay_state_unchanged']
        assert finished['initial_learner_digest'] == finished['final_learner_digest']
        assert finished['new_optimizer_updates'] == 0
        assert sha(reg['checkpoint']) == reg['checkpoint_sha256']
        for name, expected in reg['source_hashes'].items():
            assert sha(Path(reg['audit_runtime'])/name) == expected
        rows = []
        stored = json.loads((directory/'RESULTS.json').read_text())
        assert stored['completed'] == stored['expected'] == len(stored['episodes']) == 30
        assert reg['case_ids'] == plan['case_ids'] and reg['action_seed'] == plan['action_seed']
        assert len(set(r['condition'] for r in stored['episodes'])) == 30
        for case, original in zip(plan['case_ids'], stored['episodes']):
            seed = plan['action_seed']
            path = directory/f'{case}_REVIEW.json'
            reviewed = json.loads(path.read_text())
            assert reviewed == original and reviewed['passed']
            assert reviewed['action_seed'] == seed and reviewed['condition'] == case
            assert reviewed['full_learner_state_unchanged'] and reviewed['new_optimizer_updates'] == 0
            assert reviewed['native_stochastic_parameter_action_max_error'] <= 1e-7
            for kind in ['physical', 'filter', 'torque']:
                evidence = reviewed[kind]
                if kind != 'physical':
                    assert evidence['passed']
                for name, expected in evidence['evidence_sha256'].items():
                    assert sha(directory/case/name) == expected, (method, case, name)
            row = reviewed['physical']['row']
            rows.append(dict(condition=case, seed=seed, reward=reviewed['reward'],
                penetration_mm=reviewed['external_penetration_mm'], actions=reviewed['actions'],
                substeps=reviewed['physical']['samples'], task=row['task_success'], strict=row['strict_success'],
                full_horizon=row['full_horizon'], abort_reason=row['abort_reason'],
                machine_safety_violation=row['machine_safety_violation'],
                human_contact_s=row['human_contact_s'], human_compliance_ratio=row['human_compliance_ratio'],
                peak_torque_nm_per_joint=row['peak_torque_nm_per_joint'],
                completion_time_s=row['completion_time_s']))
            inputs[str(path)] = sha(path)
        assert sum(r['actions'] for r in rows) == finished['actions'] <= 41250
        assert sum(r['substeps'] for r in rows) == finished['substeps'] <= 33000000
        assert sum(r['task'] for r in rows) == finished['task']
        assert sum(r['strict'] for r in rows) == finished['strict']
        rewards = np.array([r['reward'] for r in rows])
        peaks = np.array([r['penetration_mm'] for r in rows])
        results[method] = dict(episodes=rows, task=sum(r['task'] for r in rows), strict=sum(r['strict'] for r in rows),
            mean_reward=float(rewards.mean()), reward_range=[float(rewards.min()), float(rewards.max())],
            penetration_range_mm=[float(peaks.min()), float(peaks.max())],
            machine_safety_violation_count=sum(r['machine_safety_violation'] for r in rows),
            full_horizon_count=sum(r['full_horizon'] for r in rows),
            initial_and_final_learner_digest=finished['initial_learner_digest'],
            checkpoint_sha256=reg['checkpoint_sha256'])
        xs = np.arange(30)
        axes[index, 0].scatter(xs, rewards)
        axes[index, 0].set(title=method+' frozen88 reward', ylabel='Episode return')
        axes[index, 1].scatter(xs, peaks)
        axes[index, 1].axhline(.2, color='red', linestyle='--', label='Original0.2mm limit')
        axes[index, 1].set(title=method+' external penetration', ylabel='mm')
        axes[index, 1].legend()
        for axis in axes[index]:
            axis.set_xticks(xs[::5])
            axis.set_xlabel('Registered condition index')
            axis.grid(alpha=.2)
        for name in ['REGISTRATION.json', 'CHECK_ONLY_REVIEW.json', 'STARTUP_REVIEW.json', 'EVALUATION.json', 'RESULTS.json', 'FINISHED.json']:
            path = directory/name
            inputs[str(path)] = sha(path)
    fig.suptitle('Frozen88: all30 training conditions, one action seed per method')
    plot = root/'frozen_full30_results.png'
    fig.savefig(plot, dpi=140)
    plt.close(fig)
    report = dict(passed=True, time=time.time(), methods=results, inputs=inputs, plot_sha256=sha(plot),
        total_episodes=90, total_actions=sum(r['actions'] for m in results.values() for r in m['episodes']),
        total_substeps=sum(r['substeps'] for m in results.values() for r in m['episodes']),
        new_physics=0, new_optimizer_updates=0, neural_forward_passes=0, convergence_claim=False,
        limitation='Complete88 was prospectively chosen while its training was incomplete, before its complete checkpoint and full reviews; all30 original training conditions and one external action seed per method were fixed in advance. Frozen full30 coverage does not by itself establish training convergence, generalization, independent training-seed robustness, or final SPT/ESN comparison. No condition exclusion, weight promotion, seed addition, or automatic extension.')
    (root/'REVIEW.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.root)
    except BaseException as error:
        (args.root/'REVIEW_FAILURE.json').write_text(json.dumps(dict(error=repr(error), time=time.time()))+'\n')
        raise
