"""Persist explicit 32-step off-policy targets while retaining raw replay.

The learner consumes derived reward/discount/endpoints. Its actor still uses
only the original state48. Historical behavior returns are not unbiased
current-policy targets. Pending online rows are sampled only when mature.
"""
import copy
from collections import deque
import numpy as np

from serl_clock_state_adapter_20261026 import SerlClockLearner

MARKER = dict(version=1, horizon=32, gamma=.9995, rewards='discounted_behavior_rewards',
              bootstrap='gamma_power_k_times_terminal_mask', sampling='uniform_mature_rows',
              original_replay_retained=True, importance_correction=False)


class SerlMultistepLearner(SerlClockLearner):
    def load_state_dict(self, state):
        if state.get('multistep_target_extension') != MARKER:
            raise ValueError('Explicit multistep learner marker required')
        clean = {k: v for k, v in state.items() if k != 'multistep_target_extension'}
        super().load_state_dict(clean)

    def import_one_step_state(self, state):
        if 'multistep_target_extension' in state:
            raise ValueError('Use strict loader for an extended state')
        super().load_state_dict(state)

    def state_dict(self):
        state = super().state_dict()
        state['multistep_target_extension'] = copy.deepcopy(MARKER)
        return state

    def batch(self, arrays):
        batch = super().batch(arrays)
        if '_bootstrap' not in arrays:
            raise ValueError('Derived multistep batch required')
        mask = np.asarray(arrays['_bootstrap'], np.float32)
        if mask.shape != batch['rewards'].shape or not np.isfinite(mask).all():
            raise ValueError('Invalid derived bootstrap shape/values')
        if np.any((mask < 0) | (mask > 1)):
            raise ValueError('Derived bootstrap outside unit interval')
        batch['masks'] = self.jax.device_put(mask)
        return batch


def replay_class(base):
    class MultistepReplay(base):
        def _allocate(self):
            self.target_rewards = np.zeros(self.capacity, np.float32)
            self.target_bootstrap = np.zeros(self.capacity, np.float32)
            self.target_endpoints = np.full(self.capacity, -1, np.int64)
            self.target_lengths = np.zeros(self.capacity, np.int32)
            self.ready = []
            self.ready_array = np.empty(self.capacity, np.int64)
            self.pending = {}

        def import_one_step_state(self, state, derived):
            if 'multistep_target_extension' in state:
                raise ValueError('Already extended replay')
            super().load_state_dict(state)
            self._allocate()
            for attr, key in [('target_rewards','rewards'), ('target_bootstrap','bootstrap'),
                              ('target_endpoints','endpoints'), ('target_lengths','lengths')]:
                value = np.asarray(derived[key])
                if value.shape != (self.size,):
                    raise ValueError('Derived history shape mismatch')
                getattr(self, attr)[:self.size] = value
            self.ready = list(range(self.size))
            self.ready_array[:self.size] = np.arange(self.size)

        def load_state_dict(self, state):
            extra = state.get('multistep_target_extension')
            if not extra or extra['marker'] != MARKER:
                raise ValueError('Explicit multistep replay required')
            super().load_state_dict({k:v for k,v in state.items() if k != 'multistep_target_extension'})
            self._allocate()
            for attr in ['target_rewards','target_bootstrap','target_endpoints','target_lengths']:
                value = np.asarray(extra[attr])
                if value.shape != (self.size,):
                    raise ValueError('Invalid persisted derived array')
                getattr(self, attr)[:self.size] = value
            self.ready = list(extra['ready'])
            self.ready_array[:len(self.ready)] = self.ready
            self.pending = {k:deque(v) for k,v in extra['pending'].items()}
            ready = np.asarray(self.ready, np.int64)
            pending = [i for v in self.pending.values() for i in v]
            if sorted(self.ready+pending) != list(range(self.size)):
                raise ValueError('Mature/pending replay partition invalid')
            if np.any(self.target_endpoints[ready] < ready) or np.any(self.target_endpoints[ready] >= self.size):
                raise ValueError('Invalid persisted endpoints')
            if np.any(self.target_lengths[ready] < 1) or np.any(self.target_lengths[ready] > 32):
                raise ValueError('Invalid persisted target horizon')
            if not np.isfinite(self.target_rewards[:self.size]).all() or not np.isfinite(self.target_bootstrap[:self.size]).all():
                raise ValueError('Nonfinite persisted targets')

        def state_dict(self):
            state = super().state_dict()
            state['multistep_target_extension'] = dict(marker=copy.deepcopy(MARKER),
                **{k:getattr(self,k)[:self.size].copy() for k in
                   ['target_rewards','target_bootstrap','target_endpoints','target_lengths']},
                ready=list(self.ready), pending={k:list(v) for k,v in self.pending.items()})
            return state

        def add(self, *, stream, **transition):
            if self.size >= self.capacity or self.cursor != self.size:
                raise ValueError('Registered stage cannot wrap replay capacity')
            i = self.size
            super().add(**transition)
            queue = self.pending.setdefault(stream, deque())
            queue.append(i)
            done = bool(np.asarray(transition['dones']).reshape(-1)[0])
            if len(queue) > 32:
                raise ValueError('Unflushed mature row')
            if len(queue) == 32 or done:
                while queue:
                    ids = list(queue)
                    start = ids[0]
                    value = sum(.9995**j * float(self.arrays['rewards'][idx,0]) for j,idx in enumerate(ids))
                    self.target_rewards[start] = np.float32(value)
                    self.target_bootstrap[start] = np.float32(0. if done else .9995**(len(ids)-1))
                    self.target_endpoints[start] = i
                    self.target_lengths[start] = len(ids)
                    self.ready_array[len(self.ready)] = start
                    self.ready.append(start)
                    queue.popleft()
                    if not done:
                        break
            if done:
                del self.pending[stream]

        def sample(self, batch_size):
            if not self.ready:
                raise ValueError('No mature replay')
            # Persistent index array avoids Python loops or rebuilding the mature set.
            draws = self.rng.integers(len(self.ready), size=batch_size)
            ids = self.ready_array[draws]
            end = self.target_endpoints[ids]
            values = {k:v[ids] for k,v in self.arrays.items()}
            values['rewards'] = self.target_rewards[ids,None]
            values['next_observations'] = self.arrays['next_observations'][end]
            values['_bootstrap'] = self.target_bootstrap[ids]
            return values
    return MultistepReplay
