"""Finite frozen29 short0600 action-seed diagnostic, including saved-physics review.

One pinned learner per method, four registered action seeds, original physics and
CHEQ mixing. External RNG streams leave all checkpoint learning/RNG state intact.
This selected-condition diagnostic is not the full-matrix convergence validation.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import os
import random
import selectors
import shutil
import subprocess
import sys
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def capture_rng(learner):
    import numpy as np
    import torch
    return dict(python=random.getstate(), numpy=np.random.get_state(),
                local=copy.deepcopy(learner.rng.bit_generator.state),
                torch=torch.get_rng_state(), cuda=torch.cuda.get_rng_state_all())


def restore_rng(learner, state):
    import numpy as np
    import torch
    random.setstate(state['python'])
    np.random.set_state(state['numpy'])
    learner.rng.bit_generator.state = copy.deepcopy(state['local'])
    torch.set_rng_state(state['torch'])
    torch.cuda.set_rng_state_all(state['cuda'])


def seed_native(learner, action_seed, case):
    import numpy as np
    import torch
    if type(action_seed) is not int or action_seed < 0:
        raise ValueError('Nonnegative integer action seed required')
    effective = int.from_bytes(hashlib.sha256(f'{action_seed}:{case}'.encode()).digest()[:4], 'little')
    random.seed(effective)
    np.random.seed(effective)
    torch.manual_seed(effective)
    torch.cuda.manual_seed_all(effective)
    learner.rng = np.random.default_rng(effective)
    return effective


class ExternalActions:
    def __init__(self, learner, seed, case):
        self.learner = learner
        original = capture_rng(learner)
        try:
            self.effective_seed = seed_native(learner, seed, case)
            self.state = capture_rng(learner)
        finally:
            restore_rng(learner, original)

    def call(self, function, *args, **kwargs):
        original = capture_rng(self.learner)
        try:
            restore_rng(self.learner, self.state)
            result = function(*args, **kwargs)
            self.state = capture_rng(self.learner)
            return result
        finally:
            restore_rng(self.learner, original)


def gate(learner, checkpoint, observations, seed, case, digest):
    import numpy as np
    initial = digest(learner.state_dict())
    original = capture_rng(learner)
    try:
        seed_native(learner, seed, case)
        learner.reset_episode()
        native = [learner.act(obs, step=checkpoint['steps'], deterministic=False)
                  for obs in observations]
    finally:
        restore_rng(learner, original)
    assert digest(learner.state_dict()) == initial
    external = ExternalActions(learner, seed, case)
    external.call(learner.reset_episode)
    for observation, expected in zip(observations, native):
        actual = external.call(learner.act, observation, step=checkpoint['steps'], deterministic=False)
        for left, right in zip(actual, expected):
            np.testing.assert_array_equal(left, right)
    assert digest(learner.state_dict()) == initial
    other = ExternalActions(learner, seed+1, case)
    other.call(learner.reset_episode)
    different = other.call(learner.act, observations[0], step=checkpoint['steps'], deterministic=False)
    assert not np.array_equal(native[0][1], different[1])
    assert digest(learner.state_dict()) == initial
    rejected = 0
    for bad in [-1, 1.5]:
        try:
            ExternalActions(learner, bad, case)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError('Invalid external seed accepted')
    assert rejected == 2 and digest(learner.state_dict()) == initial
    return dict(passed=True, native_vs_external_three_actions_exact=True,
                same_seed_exact=True, different_seed_changes_raw_action=True,
                negative_seed_guards=2, full_learner_state_unchanged=True,
                new_optimizer_updates=0, new_physics=0)


def review_episode(learner, ck, seed, case, folder, digest):
    import numpy as np
    from summarize_published_episode_audit_20261025 import summarize
    from replay_published_filter_audit_20261025 import audit as filter_audit
    from replay_published_torque_audit_20261025 import audit as torque_audit
    from spt_rl_reward_20261025 import SPTReward
    from training_comparison_metrics_20261025 import completion_bonus
    initial = digest(learner.state_dict())
    physical = summarize(folder, ck['controller'], case)
    filtered, torque = filter_audit(folder), torque_audit(folder)
    assert filtered['passed'] and torque['passed']
    rows = [json.loads(line) for line in (folder/'actor_intervals.jsonl').read_text().splitlines()]
    terminal = json.loads((folder/'TERMINAL.json').read_text())
    assert 0 < len(rows) <= 1375
    if terminal['result']['full_task_horizon_completed']:
        assert len(rows) == 1375 and physical['samples'] == 1100000
    else:
        assert terminal['result']['abort_reason'] and physical['samples'] < 1100000
    # Replay native sampling in one uninterrupted stream; do not reuse the
    # evaluator's per-action RNG-switching implementation for this comparison.
    original = capture_rng(learner)
    max_error = 0.
    try:
        seed_native(learner, seed, case)
        learner.reset_episode()
        for index, row in enumerate(rows):
            obs, raw, action, context = learner.act(row['observation'], step=ck['steps'], deterministic=False)
            assert obs.shape == (50,) and obs[-1] == np.float32((1375-index)/1375)
            np.testing.assert_allclose(action, row['action'], rtol=0, atol=1e-7)
            max_error = max(max_error, float(np.max(abs(action-np.asarray(row['action'])))))
    finally:
        restore_rng(learner, original)
    assert digest(learner.state_dict()) == initial
    reward_function = SPTReward()
    reward = 0.
    for index, row in enumerate(rows):
        done = index == len(rows)-1
        nxt = terminal if done else rows[index+1]
        value, _ = reward_function(current_potential=row['payload_potential'],
            next_potential=nxt['payload_potential'], interval=nxt['interval'], terminated=done,
            task_success=terminal['result']['task_success'] if done else False,
            strict_success=terminal['result']['strict_success'] if done else False)
        if done and terminal['result']['strict_success']:
            value += completion_bonus(task_success=True, strict_success=True,
                                      completion_time_s=terminal['completion_time_s'])
        reward += value
    rollout = json.loads((folder/'rollout.json').read_text())
    return dict(passed=True, action_seed=seed, condition=case, actions=len(rows),
                physical=physical, filter=filtered, torque=torque, reward=reward,
                external_penetration_mm=rollout['stats']['max_external_penetration_m']*1000,
                native_stochastic_parameter_action_max_error=max_error,
                full_learner_state_unchanged=True, new_optimizer_updates=0, new_physics=0)


def main(registration, check_only):
    reg = json.loads(registration.read_text())
    os.sched_setaffinity(0, {reg['cpu']})
    os.nice(10)
    import numpy as np
    import torch
    torch.set_num_threads(1)
    root, output = Path(reg['runtime']), registration.parent
    runtime = Path(reg['audit_runtime'])
    for name, expected in reg['source_hashes'].items():
        assert sha(runtime/name) == expected, name
    assert reg['case_id'] == 'active_short_train_0600'
    assert reg['action_seeds'] == [2026102633, 2026102634, 2026102635, 2026102636]
    assert sha(reg['checkpoint']) == reg['checkpoint_sha256']
    assert sha(reg['training_registration']) == reg['training_registration_sha256']
    protocol = json.loads(Path(reg['training_registration']).read_text())
    assert protocol['runtime'] == str(root) and sha(root/'RUNTIME.json') == protocol['runtime_sha256']
    for name, expected in json.loads((root/'SOURCE_HASHES.json').read_text()).items():
        assert sha(root/'source'/name) == expected, name
    assert sha(protocol['reference_plan']) == protocol['reference_plan_sha256']
    condition = next(c for c in protocol['conditions'] if c['id'] == reg['case_id'])
    assert sha(condition['path']) == condition['sha256']
    review = json.loads(Path(reg['required_review']).read_text())
    assert sha(reg['required_review']) == reg['required_review_sha256'] and review['passed']
    assert review['methods'][reg['controller']]['checkpoint_sha256'] == reg['checkpoint_sha256']
    sys.path[:0] = [str(runtime), str(root/'source/tools')]
    from published_compliance_learner_20261025 import PublishedLearner
    from published_pair_reduction_learner_20261026 import pair_class, marker
    from parameter_replay_capacity_20261026 import replay_class, MARKER
    from train_published_compliance_20261025 import Replay
    from validate_published_finite_check_20261025 import digest
    ck = torch.load(reg['checkpoint'], map_location='cpu', weights_only=False)
    assert ck['cycle'] == 29 and ck['boundary'] == 'complete_condition_cycle'
    assert ck['controller'] == reg['controller'] and ck['protocol_sha256'] == sha(reg['training_registration'])
    assert ck['replay']['replay_capacity_extension'] == MARKER
    assert protocol['replay_capacity_stage']['parent_cycle'] == 23
    replay = replay_class(Replay)(ck['replay']['arrays']['actions'].shape[1], 50, 2026102633)
    replay.load_state_dict(ck['replay'])
    replay_digest = digest(replay.state_dict())
    assert replay_digest == digest(ck['replay'])
    reduction = {'impedance': 'minimum', 'admittance': 'mean', 'vmc': 'mean'}[reg['controller']]
    assert ck['learner']['target_pair_reduction'] == marker(reduction)
    dimension = json.loads((root/'parameter/PRIORS.json').read_text())['methods'][reg['controller']]['action_dimension']
    learner = pair_class(PublishedLearner, reduction)(root, dimension=dimension, direct=False,
        seed=ck['seed'], device=reg['device'], algorithm='cheq', critic_layer_norm=True,
        numerical_amendments=True, critic_clock=True)
    learner.load_state_dict(ck['learner'])
    initial = digest(learner.state_dict())
    assert initial == digest(ck['learner'])
    journal = Path(reg['gate_observations'])
    assert sha(journal) == reg['gate_observations_sha256']
    with journal.open() as stream:
        observations = [json.loads(next(stream))['observation'] for _ in range(3)]
    result = gate(learner, ck, observations, reg['action_seeds'][0], reg['case_id'], digest)
    result.update(full_replay_restored_exact=True, replay_digest=replay_digest,
                  full_learner_digest=initial, checkpoint_sha256=sha(reg['checkpoint']))
    write(output/('CHECK_ONLY_REVIEW.json' if check_only else 'STARTUP_REVIEW.json'), result)
    if check_only:
        assert digest(replay.state_dict()) == replay_digest
        return
    assert json.loads((output/'CHECK_ONLY_REVIEW.json').read_text())['passed']
    assert not (output/'EVALUATION.json').exists()
    write(output/'EVALUATION.json', dict(registration_sha256=sha(registration),
        checkpoint_sha256=sha(reg['checkpoint']), action_seeds=reg['action_seeds'], case_id=reg['case_id'],
        full_learner_digest=initial, full_replay_digest=replay_digest, expected_episodes=4,
        maximum_actions=5500, maximum_substeps=4400000, optimizer_updates=0,
        scope='Selected short0600 action-seed sensitivity at fixed29; not full30, independent training seeds, or final convergence validation'))
    results = []
    for seed in reg['action_seeds']:
        assert digest(learner.state_dict()) == initial
        external = ExternalActions(learner, seed, reg['case_id'])
        external.call(learner.reset_episode)
        folder = output/f'seed_{seed}'
        command = ['taskset', '-c', str(reg['cpu']), sys.executable,
            str(runtime/'audit_published_episode_20261025.py'), '--runtime', str(root),
            '--output', str(folder), '--fixture', condition['path'], '--reference-plan',
            protocol['reference_plan'], '--controller', reg['controller'], '--ipc']
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1',
                   OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', MUJOCO_GL='disable')
        with (output/f'seed_{seed}.stderr.log').open('x') as log:
            child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=log, text=True, bufsize=1, env=env)
            write(output/'CURRENT_PHYSICS.json', dict(pid=child.pid, seed=seed, time=time.time(), command=command))
            selector = selectors.DefaultSelector()
            selector.register(child.stdout, selectors.EVENT_READ)
            actions = 0
            try:
                while True:
                    if not selector.select(timeout=600):
                        raise TimeoutError('No physics event for600seconds')
                    line = child.stdout.readline()
                    if not line:
                        raise RuntimeError('Physics exited before terminal')
                    event = json.loads(line)
                    if event['kind'] == 'error':
                        raise RuntimeError(event['error'])
                    if event['kind'] == 'terminal':
                        assert event['model_sha256'] == condition['model_sha256']
                        assert child.wait(timeout=60) == 0
                        break
                    assert event['kind'] == 'observation' and actions < 1375
                    if actions == 0:
                        assert sha(folder/'rollout.mjb') == condition['model_sha256']
                    _, _, action, _ = external.call(learner.act, event['observation'],
                                                   step=ck['steps'], deterministic=False)
                    child.stdin.write(json.dumps(dict(action=action.tolist()))+'\n')
                    child.stdin.flush()
                    actions += 1
                    if actions % 100 == 0:
                        write(output/'PROGRESS.json', dict(seed=seed, actions=actions,
                            completed_seeds=len(results), physics_pid=child.pid, time=time.time()))
            finally:
                child.stdin.close()
                selector.close()
                try:
                    child.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    child.terminate()
                    child.wait(timeout=30)
        assert digest(learner.state_dict()) == initial
        reviewed = review_episode(learner, ck, seed, reg['case_id'], folder, digest)
        assert reviewed['actions'] == actions
        write(output/f'seed_{seed}_REVIEW.json', reviewed)
        results.append(reviewed)
        write(output/'RESULTS.json', dict(episodes=results, completed=len(results), expected=4))
    assert digest(learner.state_dict()) == initial
    assert digest(replay.state_dict()) == replay_digest
    assert sha(reg['checkpoint']) == reg['checkpoint_sha256']
    for name, expected in reg['source_hashes'].items():
        assert sha(runtime/name) == expected
    write(output/'FINISHED.json', dict(passed=True, time=time.time(), episodes=4,
        actions=sum(r['actions'] for r in results), substeps=sum(r['physical']['samples'] for r in results),
        task=sum(r['physical']['row']['task_success'] for r in results),
        strict=sum(r['physical']['row']['strict_success'] for r in results),
        full_learner_state_unchanged=True, full_replay_state_unchanged=True,
        initial_learner_digest=initial, final_learner_digest=digest(learner.state_dict()),
        new_optimizer_updates=0, convergence_claim=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    try:
        main(args.registration, args.check_only)
    except BaseException as error:
        write(args.registration.parent/('CHECK_ONLY_FAILURE.json' if args.check_only else 'FAILURE.json'),
              dict(time=time.time(), error=repr(error)))
        raise
