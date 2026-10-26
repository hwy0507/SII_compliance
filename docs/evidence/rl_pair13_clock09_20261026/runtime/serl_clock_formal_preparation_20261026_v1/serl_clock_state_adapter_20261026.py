"""Persistent critic-only remaining-time adapter over pinned official SERL.

Canonical48 actor inputs and action mapping are unchanged. Critic time is a
separate leaf and enters the tested zero branch; full old optimizer state is
retained. Old replay must be explicitly migrated before this adapter is used.
"""
import copy

import numpy as np

from serl_state_adapter_20261026 import SerlStateLearner, execution_action
from serl_critic_clock_extension_20261026 import extend

MARKER = dict(version=1, maximum_actions=1375, actor_features=48,
              critic_observation_features=49, encoding='separate_state_and_clock_leaves',
              branch='zero_initialized_addition_to_first_critic_hidden',
              original_gemm_inputs=55)


class SerlClockLearner(SerlStateLearner):
    critic_clock = True
    replay_observation_dimension = 49

    def __init__(self, *args, critic_clock=True, **kwargs):
        if not critic_clock:
            raise ValueError('Clock adapter requires explicit critic_clock=True')
        super().__init__(*args, critic_clock=False, **kwargs)
        self._base_agent_template = self.agent
        self.agent, self.clock_extension_receipt = extend(self)
        self._episode_actions = {}

    def reset_episode(self, stream=0):
        self._episode_actions[stream] = 0

    def _clock(self, stream):
        count = self._episode_actions.get(stream, 0)
        if not 0 <= count <= 1375:
            raise ValueError('Episode action count outside frozen horizon')
        return np.float32((1375-count)/1375.)

    def observation(self, raw, stream=0):
        state = super().observation(raw, stream=stream)
        return np.r_[state, self._clock(stream)].astype(np.float32)

    def terminal_observation(self, previous, stream=0):
        previous = np.asarray(previous, np.float32)
        if previous.shape != (49,):
            raise ValueError('Expected clock-aware previous replay observation')
        result = previous.copy()
        result[48] = self._clock(stream)
        return result

    @staticmethod
    def actor_input(observation):
        return dict(state=np.ascontiguousarray(observation[..., :48]),
                    clock=np.ascontiguousarray(observation[..., 48:49]))

    def act(self, raw, *, step, deterministic=False, warmup=5000, stream=0):
        observation = self.observation(raw, stream=stream)
        if self._episode_actions.get(stream, 0) >= 1375:
            raise ValueError('Action requested beyond horizon')
        if step < warmup and not deterministic:
            action = self.rng.uniform(-1, 1, 7).astype(np.float32)
        elif deterministic:
            action = np.asarray(self.agent.sample_actions(self.actor_input(observation), argmax=True))
        else:
            self.action_rng, key = self.jax.random.split(self.action_rng)
            action = np.asarray(self.agent.sample_actions(self.actor_input(observation), seed=key))
        self._episode_actions[stream] = self._episode_actions.get(stream, 0) + 1
        return observation, action, execution_action(action), None

    def batch(self, arrays):
        plain = dict(arrays)
        for key in ('observations', 'next_observations'):
            value = np.asarray(arrays[key], np.float32)
            if value.ndim != 2 or value.shape[-1] != 49 or not np.isfinite(value).all():
                raise ValueError('Finite migrated replay49 required')
            if np.any(value[:, 48] < 0) or np.any(value[:, 48] > 1):
                raise ValueError('Clock outside unit interval')
            plain[key] = np.ascontiguousarray(value[:, :48])
        batch = super().batch(plain)
        for key in ('observations', 'next_observations'):
            batch[key] = dict(state=batch[key], clock=self.jax.device_put(
                np.ascontiguousarray(arrays[key][:, 48:49])))
        return batch

    def state_dict(self):
        state = super().state_dict()
        state['critic_clock_extension'] = copy.deepcopy(MARKER)
        return state

    def load_state_dict(self, state):
        if state.get('critic_clock_extension') != MARKER:
            raise ValueError('Explicit migrated critic clock checkpoint required')
        super().load_state_dict(state)
        self._episode_actions.clear()

    def import_original_state(self, state):
        """One explicit migration, never an implicit fallback during resume."""
        if 'critic_clock_extension' in state:
            raise ValueError('Already migrated checkpoint must use strict loader')
        self.agent = self._base_agent_template
        super().load_state_dict(state)
        self.agent, self.clock_extension_receipt = extend(self)
        self._episode_actions.clear()
