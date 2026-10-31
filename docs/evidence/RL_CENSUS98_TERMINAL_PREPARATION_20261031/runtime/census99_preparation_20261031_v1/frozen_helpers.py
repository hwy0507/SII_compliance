"""Violation52 gate and native replay; preserves original physical/filter/torque review."""
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
        native = []
        for row in observations:
            learner.consume_interval(row['interval'])
            native.append(learner.act(row['observation'], step=checkpoint['steps'], deterministic=False))
    finally:
        restore_rng(learner, original)
    assert digest(learner.state_dict()) == initial
    external = ExternalActions(learner, seed, case)
    external.call(learner.reset_episode)
    for observation, expected in zip(observations, native):
        learner.consume_interval(observation['interval'])
        actual = external.call(learner.act, observation['observation'], step=checkpoint['steps'], deterministic=False)
        for left, right in zip(actual, expected):
            np.testing.assert_array_equal(left, right)
    assert digest(learner.state_dict()) == initial
    other = ExternalActions(learner, seed+1, case)
    other.call(learner.reset_episode)
    learner.consume_interval(observations[0]['interval'])
    different = other.call(learner.act, observations[0]['observation'], step=checkpoint['steps'], deterministic=False)
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
            learner.consume_interval(row['interval'])
            obs, raw, action, context = learner.act(row['observation'], step=ck['steps'], deterministic=False)
            assert obs.shape == (52,) and obs[49] == np.float32((1375-index)/1375)
            from persisted_history_critic import feature
            peak = 0. if row['interval'] is None else row['interval']['external_penetration_peak_m']
            assert obs[50] == feature(peak) and obs[51] == float(peak > .0002)
            np.testing.assert_allclose(action, row['action'], rtol=0, atol=1e-7)
            max_error = max(max_error, float(np.max(abs(action-np.asarray(row['action'])))))
        learner.consume_interval(terminal['interval'])
        terminal_obs = learner.terminal_observation(obs)
        peak = terminal['interval']['external_penetration_peak_m']
        assert terminal_obs[49] == np.float32((1375-len(rows))/1375)
        assert terminal_obs[50] == feature(peak) and terminal_obs[51] == float(peak > .0002)
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
