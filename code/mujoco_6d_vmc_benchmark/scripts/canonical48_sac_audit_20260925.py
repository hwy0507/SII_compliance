"""Observe standard SB3 SAC boundaries without changing its sampling or losses."""
from __future__ import annotations

import json
from pathlib import Path
import time

import gymnasium as gym
import numpy as np
from stable_baselines3.common.buffers import ReplayBuffer
from stable_baselines3.common.callbacks import BaseCallback


def require(condition, message):
    if not condition:
        raise ValueError(message)


def owned(value):
    return json.loads(json.dumps(value, allow_nan=False, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x.item()))


def equal(actual, expected, name):
    actual, expected = np.asarray(actual), np.asarray(expected)
    require(actual.shape == expected.shape and np.isfinite(actual).all() and np.isfinite(expected).all()
            and np.array_equal(actual, expected), 'SAC audit mismatch: ' + name)


def write(stream, row):
    stream.write(json.dumps(owned(row), allow_nan=False, separators=(',', ':')) + '\n')


def stats(normalizer):
    if normalizer is None:
        return None
    return owned(dict(mean=normalizer.obs_rms.mean, var=normalizer.obs_rms.var,
                      count=normalizer.obs_rms.count, clip_obs=normalizer.clip_obs,
                      epsilon=normalizer.epsilon, norm_obs=normalizer.norm_obs,
                      norm_reward=normalizer.norm_reward))


class OnlineEvidenceEnv(gym.Wrapper):
    """Copy the just-completed journal row before DummyVecEnv auto-reset."""
    def step(self, action):
        observation, reward, terminated, truncated, info = self.env.step(action)
        row = owned(self.env.journal.rows[-1])
        info = dict(info, sac_transition=row,
                    sac_episode_directory=str(self.env.journal.directory))
        return observation, reward, terminated, truncated, info


class AuditedReplayBuffer(ReplayBuffer):
    def __init__(self, *args, audit_directory, expected_demo=0, **kwargs):
        super().__init__(*args, **kwargs)
        require(self.n_envs == 1 and not self.optimize_memory_usage and self.handle_timeout_termination,
                'Only standard single-env separate-next replay is covered')
        require(expected_demo in (0, 600), 'Only pinned 600-transition demo is allowed')
        self.expected_demo = expected_demo
        self.audit_directory = Path(audit_directory)
        # SAC.load constructs a replay buffer even for inference. Loading a
        # checkpoint must not reopen or mutate that training run's audit files.
        self.insert_log = self.sample_log = None
        self.pending = None
        self.sources = []
        self.next_valid = []
        self.online_steps = 0
        self.sample_calls = 0
        self.sampled_demo = 0
        self.sampled_online = 0
        self.last_sample_indices = None

    def start_audit(self):
        require(self.insert_log is None and self.sample_log is None, 'Audit already started')
        self.audit_directory.mkdir(parents=True, exist_ok=True)
        self.insert_log = (self.audit_directory / 'replay_insertions.jsonl').open('x', buffering=1)
        try:
            self.sample_log = (self.audit_directory / 'replay_samples.jsonl').open('x', buffering=1)
        except BaseException:
            self.insert_log.close()
            raise

    def expect(self, row):
        require(self.insert_log is not None and not self.insert_log.closed, 'Explicit fresh training audit required')
        require(self.pending is None, 'Previous transition was not stored')
        self.pending = owned(row)

    def add(self, obs, next_obs, action, reward, done, infos):
        require(self.pending is not None, 'Unbound replay insertion')
        require(not self.full and len(self.sources) < self.buffer_size, 'Replay overwrite is outside protocol')
        pending = self.pending
        index = self.pos
        is_demo = pending['source'] == 'demo'
        require(pending['source'] in ('demo', 'online'), 'Unknown replay source')
        require(is_demo == (index < self.expected_demo), 'Demo must be exactly the initial pinned prefix')
        require(not infos[0].get('TimeLimit.truncated', False), 'Task termination cannot be timeout')
        inputs = dict(observations=np.asarray(obs, np.float32), next_observations=np.asarray(next_obs, np.float32),
                      actions=np.asarray(action, np.float32), rewards=np.asarray(reward, np.float32).reshape(1),
                      dones=np.asarray(done, np.float32).reshape(1), timeouts=np.zeros(1, np.float32))
        super().add(obs, next_obs, action, reward, done, infos)
        # Read actual allocated slots after SB3 has performed its own assignments.
        actual = {key: getattr(self, key)[index].copy() for key in inputs}
        for key, expected in inputs.items():
            equal(actual[key], expected, 'post-add ' + key)
        equal(actual['observations'], np.asarray(pending['observation'], np.float32).reshape(1, 48), 'Gym/demo raw observation')
        equal(actual['actions'], np.asarray(pending['buffer_action'], np.float32).reshape(1, 7), 'actual buffer_actions')
        equal(actual['rewards'], np.asarray([pending['reward']], np.float32), 'Gym/demo reward')
        equal(actual['dones'], np.asarray([pending['done']], np.float32), 'Gym/demo terminal')
        require(bool(actual['dones'][0]) == (not pending['next_observation_valid']), 'Placeholder would bootstrap')
        if pending['next_observation_valid'] or is_demo:
            equal(actual['next_observations'], np.asarray(pending['next_observation'], np.float32).reshape(1, 48), 'valid raw next or pinned demo placeholder')
        if not is_demo:
            require(pending['online_step'] == self.online_steps + 1, 'Online step gap/duplicate')
            self.online_steps += 1
        self.sources.append(pending['source'])
        self.next_valid.append(pending['next_observation_valid'])
        write(self.insert_log, dict(index=index, stored=actual, evidence=pending,
                                   terminal_next_semantics='Invalid masked placeholder; VecNormalize terminal roundtrip may change its values'))
        self.pending = None

    def _get_samples(self, batch_inds, env=None):
        require(self.sample_log is not None and not self.sample_log.closed, 'Sampling requires active audit')
        before = stats(env)
        if env is not None:
            require(not env.norm_reward, 'Reward normalization is forbidden')
        # Exactly one original sampler call; the logger never calls an RNG.
        sampled = super()._get_samples(batch_inds, env=env)
        require(stats(env) == before, 'Replay sampling changed observation statistics')
        idx = np.asarray(batch_inds)
        require(len(self.sources) == self.size(), 'Replay source ledger is incomplete')
        raw_obs = self.observations[idx, 0]
        raw_next = self.next_observations[idx, 0]
        expected = dict(observations=env.normalize_obs(raw_obs) if env is not None else raw_obs,
                        next_observations=env.normalize_obs(raw_next) if env is not None else raw_next,
                        actions=self.actions[idx, 0], rewards=self.rewards[idx].reshape(-1, 1),
                        dones=self.dones[idx].reshape(-1, 1))
        require(not self.timeouts[idx].any(), 'Sampled task terminal has timeout')
        for key, value in expected.items():
            equal(getattr(sampled, key).detach().cpu().numpy(), value, 'actual sample ' + key)
        valid = np.asarray(self.next_valid, bool)[idx].reshape(-1, 1)
        equal(1. - expected['dones'], valid.astype(np.float32), 'sample bootstrap mask')
        demo_count = int(np.count_nonzero(idx < self.expected_demo))
        self.sample_calls += 1
        self.sampled_demo += demo_count
        self.sampled_online += len(idx) - demo_count
        self.last_sample_indices = idx.copy()
        write(self.sample_log, dict(call=self.sample_calls, online_steps=self.online_steps,
                                   indices=idx, demo_count=demo_count, online_count=len(idx)-demo_count,
                                   normalization=before, actual_sample_arrays_verified=True))
        return sampled

    def export_valid(self, path):
        require(self.pending is None and not self.full, 'Cannot export pending or overwritten replay')
        count = self.size()
        require(count == self.expected_demo + self.online_steps == len(self.sources), 'Replay budget mismatch')
        payload = {key: getattr(self, key)[:count].copy() for key in
                   ('observations', 'next_observations', 'actions', 'rewards', 'dones', 'timeouts')}
        payload.update(is_demo=np.asarray([source == 'demo' for source in self.sources]),
                       next_observation_valid=np.asarray(self.next_valid, bool))
        require(not Path(path).exists(), 'Fresh replay export required')
        np.savez_compressed(path, **payload)
        return dict(size=count, pos=self.pos, full=self.full, online_steps=self.online_steps,
                    demo_transitions=self.expected_demo, sample_calls=self.sample_calls,
                    sampled_demo=self.sampled_demo, sampled_online=self.sampled_online)

    def close_logs(self):
        for stream in (self.insert_log, self.sample_log):
            if stream is not None:
                stream.close()


def prefill(buffer, data):
    require(buffer.expected_demo == 600 and buffer.size() == 0, 'Prefill must precede all online data')
    for index in range(600):
        buffer.expect(dict(source='demo', demo_index=index, observation=data['observations'][index],
                           next_observation=data['next_observations'][index],
                           next_observation_valid=bool(data['next_observation_valid'][index, 0]),
                           buffer_action=data['actions_sac'][index], reward=float(data['rewards'][index, 0]),
                           done=bool(data['dones'][index, 0])))
        buffer.add(data['observations'][index:index+1], data['next_observations'][index:index+1],
                   data['actions_sac'][index:index+1], data['rewards'][index], data['dones'][index],
                   [{'TimeLimit.truncated': False}])


class SACProgress(BaseCallback):
    def __init__(self, output, start=None, resource_check=None, checkpoint_every=2048):
        super().__init__()
        self.output = Path(output)
        self.start = time.time() if start is None else start
        self.resource_check = resource_check
        self.checkpoint_every = checkpoint_every
        self.last_checkpoint = 0
        self.optimizer_steps = dict(actor=0, critic=0, entropy=0)
        self.hooks = []
        self.reward_log = (self.output / 'sb3_received_rewards.jsonl').open('x', buffering=1)
        try:
            self.optimizer_log = (self.output / 'optimizer_steps.jsonl').open('x', buffering=1)
        except BaseException:
            self.reward_log.close()
            raise

    def _on_training_start(self):
        require(self.model.num_timesteps == 0 and self.model._n_updates == 0, 'Fresh SAC required')
        for name, optimizer in [('actor', self.model.actor.optimizer), ('critic', self.model.critic.optimizer),
                                ('entropy', self.model.ent_coef_optimizer)]:
            require(optimizer is not None, 'Auto entropy optimizer missing')
            def completed_step(optimizer, args, kwargs, name=name):
                self.optimizer_steps[name] += 1
                write(self.optimizer_log, dict(optimizer=name, completed_steps=self.optimizer_steps[name],
                                               online_step=self.model.num_timesteps))
            self.hooks.append(optimizer.register_step_post_hook(completed_step))

    def _on_step(self):
        info = self.locals['infos'][0]
        row = info['sac_transition']
        actions = self.locals['actions']
        buffer_actions = self.locals['buffer_actions']
        equal(self.model.policy.unscale_action(buffer_actions), actions, 'unscaled buffer action vs env request')
        equal(np.asarray(row['requested_action']), actions[0].astype(np.float64), 'journal environment request')
        equal(np.asarray(row['execution_action']), actions[0].astype(np.float64), 'journal direct7 execution')
        require(not row['truncated'] and not info.get('TimeLimit.truncated', False), 'Unexpected timeout')
        require(bool(self.locals['dones'][0]) == bool(row['terminated']), 'VecEnv terminal differs from Gym')
        actual = float(self.locals['rewards'][0])
        require(actual == float(np.float32(row['reward'])), 'SB3 received reward differs from Gym')
        buffer = self.model.replay_buffer
        buffer.expect(dict(source='online', online_step=int(self.num_timesteps),
                           observation=row['observation'], next_observation=row['next_observation'],
                           next_observation_valid=row['next_observation_valid'],
                           buffer_action=buffer_actions[0], environment_action=actions[0],
                           reward=row['reward'], done=row['terminated'],
                           episode_directory=info['sac_episode_directory'], episode_step=row['step_index']))
        write(self.reward_log, dict(step=int(self.num_timesteps), gym_float64=row['reward'], sb3_float32=actual,
                                   done=bool(row['terminated']), reward_terms=info['reward_terms']))
        if self.num_timesteps % 32 == 0:
            state = dict(status='training', timesteps=self.num_timesteps, updates=self.model._n_updates,
                         optimizer_steps=self.optimizer_steps, elapsed_s=time.time()-self.start)
            if self.resource_check is not None:
                state['resources'] = self.resource_check()
            (self.output / 'progress.json').write_text(json.dumps(owned(state), indent=2) + '\n')
        return True

    def _checkpoint(self):
        step = self.model.num_timesteps
        if not self.checkpoint_every or not step or step % self.checkpoint_every or step == self.last_checkpoint:
            return
        require(self.model.replay_buffer.pending is None, 'Checkpoint before replay insertion')
        directory = self.output / 'checkpoints'
        directory.mkdir(exist_ok=True)
        stem = f'step_{step:08d}'
        self.model.save(directory / (stem + '.zip'))
        self.model.get_vec_normalize_env().save(directory / (stem + '_vecnormalize.pkl'))
        (directory / (stem + '.json')).write_text(json.dumps(dict(timesteps=step, updates=self.model._n_updates,
            optimizer_steps=self.optimizer_steps, timing='After previous step update, before next rollout; final after learn update',
            selection='Fixed interval diagnostics only; no exact simulator/RNG resumability promised'), indent=2) + '\n')
        self.last_checkpoint = step

    def _on_rollout_start(self):
        self._checkpoint()

    def _on_training_end(self):
        self._checkpoint()

    def close_logs(self):
        for handle in self.hooks:
            handle.remove()
        self.hooks.clear()
        self.reward_log.close()
        self.optimizer_log.close()
