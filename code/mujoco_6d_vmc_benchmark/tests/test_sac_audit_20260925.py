"""Real SB3 integration against synthetic observations; never a MuJoCo rollout."""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import gymnasium as gym
import numpy as np
import pytest
import torch
from stable_baselines3 import SAC
from stable_baselines3.common.buffers import ReplayBuffer
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from canonical48_sac_audit_20260925 import (AuditedReplayBuffer, OnlineEvidenceEnv,
                                          SACProgress, prefill, stats)

OBS = gym.spaces.Box(-np.inf, np.inf, (48,), np.float32)
ACT = gym.spaces.Box(np.array([0., -1., -1., -1., -1., -1., -1.], np.float32), np.ones(7, np.float32))


class SyntheticJournalEnv(gym.Env):
    observation_space = OBS
    action_space = ACT

    def __init__(self):
        self.episode = -1
        self.calls = 0

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.episode += 1
        self.step_number = 0
        self.obs = np.linspace(.1, .9, 48) + self.episode * .2
        self.journal = SimpleNamespace(rows=[], directory=Path('/synthetic') / str(self.episode))
        return self.obs.astype(np.float32), {}

    def step(self, action):
        self.calls += 1
        previous = self.obs.copy()
        self.step_number += 1
        terminal = self.step_number == 2
        if not terminal:
            self.obs += .031
        reward = .123456789 + float(action[0]) * .01
        row = dict(observation=previous, next_observation=self.obs.copy(), next_observation_valid=not terminal,
                   requested_action=np.asarray(action, np.float64), execution_action=np.asarray(action, np.float64),
                   reward=reward, terminated=terminal, truncated=False, step_index=self.step_number-1)
        self.journal.rows.append(row)
        return self.obs.astype(np.float32), reward, terminal, False, dict(reward_terms={'synthetic': reward})


def audited(tmp_path, expected_demo=0, size=1024):
    buffer = AuditedReplayBuffer(size, OBS, ACT, device='cpu', n_envs=1,
                                audit_directory=tmp_path, expected_demo=expected_demo)
    buffer.start_audit()
    return buffer


def add_online(buffer, index, terminal=False):
    obs = np.full((1, 48), index + .123, np.float32)
    nxt = obs + .05
    action = np.full((1, 7), .234567, np.float32)
    reward = np.asarray([.321 + index], np.float32)
    done = np.asarray([terminal])
    buffer.expect(dict(source='online', online_step=index+1, observation=obs[0], next_observation=nxt[0],
                       next_observation_valid=not terminal, buffer_action=action[0], reward=reward[0], done=terminal))
    buffer.add(obs, nxt, action, reward, done, [{'TimeLimit.truncated': False}])


class TrackedPlainReplay(ReplayBuffer):
    def _get_samples(self, batch_inds, env=None):
        self.last_indices = batch_inds.copy()
        return super()._get_samples(batch_inds, env)


def rng_equal(a, b):
    return a[0] == b[0] and np.array_equal(a[1], b[1]) and a[2:] == b[2:]


def test_post_add_and_sample_match_stock_indices_arrays_and_rng(tmp_path):
    logged = audited(tmp_path)
    plain = TrackedPlainReplay(1024, OBS, ACT, device='cpu')
    norm = VecNormalize(DummyVecEnv([SyntheticJournalEnv]), norm_reward=False, clip_obs=12.)
    norm.obs_rms.mean = np.linspace(-.2, .5, 48)
    norm.obs_rms.var = np.linspace(.4, 1.8, 48)
    norm.obs_rms.count = 31.
    norm.training = False
    before = stats(norm)
    try:
        for index in range(11):
            add_online(logged, index, terminal=index == 9)
            plain.add(logged.observations[index], logged.next_observations[index], logged.actions[index],
                      logged.rewards[index], logged.dones[index], [{'TimeLimit.truncated': False}])
        for seed in range(12):
            np.random.seed(seed)
            expected = plain.sample(17, env=norm)
            stock_rng = np.random.get_state()
            np.random.seed(seed)
            actual = logged.sample(17, env=norm)
            assert np.array_equal(logged.last_sample_indices, plain.last_indices)
            assert rng_equal(stock_rng, np.random.get_state())
            for key in ('observations', 'next_observations', 'actions', 'rewards', 'dones'):
                assert torch.equal(getattr(actual, key), getattr(expected, key))
        assert stats(norm) == before
        report = logged.export_valid(tmp_path / 'valid.npz')
        assert report['size'] == report['online_steps'] == 11 and report['sampled_online'] == 12*17
        with np.load(tmp_path / 'valid.npz') as data:
            assert data['observations'].shape == (11, 1, 48)
            assert data['next_observation_valid'][-1] and data['dones'][-1] == 0
    finally:
        logged.close_logs()
        norm.close()


def test_real_pinned_demo_all_600_entries_and_terminal_are_sampled(tmp_path):
    dataset = ROOT / 'outputs/train_only_action7_demo_20260924_r2'
    assert hashlib.sha256((dataset / 'manifest.json').read_bytes()).hexdigest() == '9f9092c03abcbf80cbf3e036552fbd9d6a214cdd21af8dded5eed1c402eb0a56'
    with np.load(dataset / 'demonstration.npz') as archive:
        data = {key: archive[key] for key in archive.files}
    buffer = audited(tmp_path, expected_demo=600)
    try:
        prefill(buffer, data)
        sample = buffer._get_samples(np.arange(600))
        assert buffer.size() == 600 and buffer.online_steps == 0
        assert torch.equal(sample.actions, torch.from_numpy(data['actions_sac']))
        assert np.array_equal(sample.dones.numpy(), ~data['next_observation_valid'])
        assert sample.dones[-1].item() == 1 and buffer.timeouts[599] == 0
        assert buffer.sampled_demo == 600 and buffer.sampled_online == 0
        add_online(buffer, 0)
        mixed = buffer._get_samples(np.asarray([0, 599, 600]))
        assert buffer.size() == 601 and buffer.online_steps == 1
        assert mixed.dones[:, 0].tolist() == [0., 1., 0.]
        assert buffer.sampled_demo == 602 and buffer.sampled_online == 1
    finally:
        buffer.close_logs()


@pytest.mark.parametrize('error', ['none', 'failed', 'changed_original_source', 'wrong_base_protocol'])
def test_proof_accepts_only_original_source_subset_and_clean_bound_artifacts(tmp_path, error):
    sys.path.insert(0, str(ROOT / 'tools'))
    from run_canonical48_sac_20260925 import verify_proofs
    common = dict(fixture_specs={}, asset_hashes={}, runtime={}, device='cuda', nominal_options={})
    old_sources = {'scripts/original.py': 'a'*64}
    manifest = dict(**common, source_hashes={**old_sources, 'scripts/new_sac.py': 'b'*64},
                    reward={'gamma': .995}, base_protocol_sha256='c'*64)
    for mode in ('parameter6', 'direct7'):
        directory = tmp_path / mode
        directory.mkdir()
        proof = dict(**common, mode=mode, protocol_sha256='c'*64, source_hashes=old_sources, reward={'gamma': .995})
        parity = dict(mode=mode, passed=True, source_hashes=old_sources, nominal_options={})
        (directory / 'manifest.json').write_text(json.dumps(proof))
        (directory / 'PARITY.json').write_text(json.dumps(parity))
        complete = dict(mode=mode, status='proof_passed',
                        parity_sha256=hashlib.sha256((directory / 'PARITY.json').read_bytes()).hexdigest())
        (directory / 'COMPLETE.json').write_text(json.dumps(complete))
    if error == 'none':
        assert set(verify_proofs(tmp_path, manifest)) == {'parameter6', 'direct7'}
    else:
        if error == 'failed':
            (tmp_path / 'parameter6/FAILED.json').write_text('{}')
        elif error == 'changed_original_source':
            manifest['source_hashes']['scripts/original.py'] = 'd'*64
        else:
            manifest['base_protocol_sha256'] = 'd'*64
        with pytest.raises(ValueError):
            verify_proofs(tmp_path, manifest)


def train_synthetic(tmp_path, use_audit):
    tmp_path.mkdir()
    environment = SyntheticJournalEnv()
    norm = VecNormalize(DummyVecEnv([lambda: OnlineEvidenceEnv(environment)]), norm_reward=False, clip_obs=.05)
    kwargs = dict(learning_rate=3e-4, buffer_size=64, learning_starts=2, batch_size=3,
                  gamma=.995, train_freq=1, gradient_steps=1, seed=811, device='cpu',
                  policy_kwargs=dict(net_arch=[8, 8]))
    if use_audit:
        kwargs.update(replay_buffer_class=AuditedReplayBuffer,
                      replay_buffer_kwargs=dict(audit_directory=tmp_path / 'audit'))
    model = SAC('MlpPolicy', norm, **kwargs)
    callback = None
    if use_audit:
        model.replay_buffer.start_audit()
        callback = SACProgress(tmp_path, checkpoint_every=2)
    model.learn(7, callback=callback)
    return model, norm, environment, callback


def test_actual_online_store_terminal_autoreset_partial_updates_and_load(tmp_path):
    torch.set_num_threads(1)
    plain, plain_norm, plain_env, _ = train_synthetic(tmp_path / 'plain', False)
    model, norm, env, callback = train_synthetic(tmp_path / 'logged', True)
    try:
        assert model.num_timesteps == 7 and model._n_updates == 5
        assert callback.optimizer_steps == dict(actor=5, critic=5, entropy=5)
        assert model.replay_buffer.sample_calls == 5
        assert env.calls == plain_env.calls == 7  # synthetic steps, zero physical simulation
        for key, tensor in model.policy.state_dict().items():
            assert torch.equal(tensor, plain.policy.state_dict()[key]), key
        assert torch.equal(model.log_ent_coef, plain.log_ent_coef)
        assert stats(norm) == stats(plain_norm)
        rows = [json.loads(line) for line in (tmp_path / 'logged/audit/replay_insertions.jsonl').read_text().splitlines()]
        assert len(rows) == 7
        for index in (1, 3, 5):
            row = rows[index]
            assert row['evidence']['done'] and not row['evidence']['next_observation_valid']
            assert row['stored']['dones'] == [1.] and row['stored']['timeouts'] == [0.]
            assert row['evidence']['episode_step'] == 1
            assert row['evidence']['episode_directory'] == '/synthetic/' + str(index//2)
        # Very small clip deliberately exercises terminal normalize/unnormalize
        # distortion; it is valid only under a zero bootstrap mask.
        assert not np.array_equal(rows[1]['stored']['next_observations'][0], rows[1]['evidence']['next_observation'])
        assert rows[-1]['evidence']['next_observation_valid'] and rows[-1]['stored']['dones'] == [0.]
        assert np.array_equal(np.asarray(rows[-1]['stored']['next_observations'], np.float32)[0],
                              np.asarray(rows[-1]['evidence']['next_observation'], np.float32))
        for optimizer in (model.actor.optimizer, model.critic.optimizer, model.ent_coef_optimizer):
            assert {int(state['step']) for state in optimizer.state.values()} == {5}
        checkpoint = json.loads((tmp_path / 'logged/checkpoints/step_00000006.json').read_text())
        assert checkpoint['updates'] == 4 and checkpoint['optimizer_steps'] == dict(actor=4, critic=4, entropy=4)
        model.save(tmp_path / 'final.zip')
        audit_file = tmp_path / 'logged/audit/replay_insertions.jsonl'
        before = audit_file.read_bytes()
        loaded = SAC.load(tmp_path / 'final.zip', device='cpu')
        assert loaded.num_timesteps == 7 and loaded._n_updates == 5 and loaded.seed == 811
        assert loaded.replay_buffer.insert_log is None and audit_file.read_bytes() == before
        obs = np.zeros((1, 48), np.float32)
        assert np.array_equal(loaded.predict(obs, deterministic=True)[0], model.predict(obs, deterministic=True)[0])
    finally:
        callback.close_logs()
        model.replay_buffer.close_logs()
        norm.close()
        plain_norm.close()


@pytest.mark.parametrize('error', ['timeout', 'wrong_action', 'invalid_next_mask', 'unbound', 'io_failure'])
def test_invalid_replay_evidence_fails_closed(tmp_path, error):
    buffer = audited(tmp_path)
    obs = np.zeros((1, 48), np.float32)
    action = np.zeros((1, 7), np.float32)
    pending = dict(source='online', online_step=1, observation=obs[0], next_observation=obs[0],
                   next_observation_valid=True, buffer_action=action[0], reward=0., done=False)
    if error == 'wrong_action':
        pending['buffer_action'] = np.ones(7)
    if error == 'invalid_next_mask':
        pending['next_observation_valid'] = False
    try:
        if error != 'unbound':
            buffer.expect(pending)
        if error == 'io_failure':
            buffer.insert_log.close()
        with pytest.raises((ValueError, OSError)):
            buffer.add(obs, obs, action, np.zeros(1), np.zeros(1), [{'TimeLimit.truncated': error == 'timeout'}])
    finally:
        buffer.close_logs()
