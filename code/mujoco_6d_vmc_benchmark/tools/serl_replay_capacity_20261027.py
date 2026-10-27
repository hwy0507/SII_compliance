"""Explicit SERL replay expansion preserving raw rows and multistep state.

The old multistep replay raises at its capacity instead of overwriting. This
candidate permits additional retained rows; it does not claim equivalence to
a hypothetical ring buffer after one million rows. Deployment requires an
exact registered parent digest and a separate reviewed training entry.
"""
import copy
import numpy as np


MARKER = dict(version=1, original_capacity=1_000_000, capacity=2_000_000,
              retention='append_without_overwrite', sampling='uniform_mature_rows',
              derived_targets='unchanged_32_step_behavior_returns',
              full_behavior='raise_before_overwrite')


def replay_class(base, legacy_digest=None):
    class CapacityReplay(base):
        def __init__(self, dimension, observation_dim, seed, capacity=2_000_000):
            if capacity != MARKER['capacity'] or dimension != 7 or observation_dim != 49:
                raise ValueError('Registered SERL dimensions and expanded capacity required')
            super().__init__(dimension, observation_dim, seed, capacity=capacity)

        def add(self, **row):
            if self.size >= self.capacity or self.cursor != self.size:
                raise ValueError('Expanded SERL replay must never wrap or overwrite')
            super().add(**row)
            # The frozen raw replay wraps its cursor on the final free slot.
            self.cursor = self.size

        def state_dict(self):
            state = super().state_dict()
            state['replay_capacity_extension'] = copy.deepcopy(MARKER)
            return state

        def load_state_dict(self, state):
            from validate_serl_state_20261026 import digest
            from serl_multistep_state_adapter_20261026 import MARKER as MULTISTEP_MARKER
            required = {'capacity', 'size', 'cursor', 'arrays', 'rng', 'multistep_target_extension'}
            expanded = 'replay_capacity_extension' in state
            if expanded:
                if (set(state) != required | {'replay_capacity_extension'}
                        or state['replay_capacity_extension'] != MARKER
                        or state['capacity'] != self.capacity):
                    raise ValueError('Altered expanded SERL replay marker or fields')
            elif (set(state) != required or legacy_digest is None
                  or state['capacity'] != MARKER['original_capacity']
                  or state['size'] >= state['capacity'] or digest(state) != legacy_digest):
                raise ValueError('Only exact registered unwrapped legacy SERL replay may migrate')
            size = state['size']
            if (type(size) is not int or not 0 <= size <= self.capacity
                    or state['cursor'] != size or set(state['arrays']) != set(self.arrays)):
                raise ValueError('Invalid SERL replay size, cursor or raw fields')
            for key, value in state['arrays'].items():
                if (not isinstance(value, np.ndarray) or value.dtype != np.float32
                        or value.shape != (size, self.arrays[key].shape[1])
                        or not np.isfinite(value).all()):
                    raise ValueError('Invalid raw SERL replay field: '+key)
            if not np.isin(state['arrays']['dones'], [0, 1]).all():
                raise ValueError('Binary terminal flags required')
            extra = state['multistep_target_extension']
            fields = {'marker', 'target_rewards', 'target_bootstrap', 'target_endpoints',
                      'target_lengths', 'ready', 'pending'}
            if set(extra) != fields or extra['marker'] != MULTISTEP_MARKER:
                raise ValueError('Unchanged multistep marker and fields required')
            dtypes = dict(target_rewards=np.float32, target_bootstrap=np.float32,
                          target_endpoints=np.int64, target_lengths=np.int32)
            for key, dtype in dtypes.items():
                value = extra[key]
                if (not isinstance(value, np.ndarray) or value.dtype != dtype
                        or value.shape != (size,) or not np.isfinite(value).all()):
                    raise ValueError('Invalid derived SERL replay field: '+key)
            if np.any((extra['target_bootstrap'] < 0) | (extra['target_bootstrap'] > 1)):
                raise ValueError('Invalid multistep bootstrap range')
            # Check RNG validity without drawing or changing caller state.
            rng = np.random.default_rng()
            rng.bit_generator.state = copy.deepcopy(state['rng'])
            migrated = dict(state, capacity=self.capacity)
            migrated.pop('replay_capacity_extension', None)
            # Frozen multistep loader additionally validates ready/pending
            # partition, order-preserving restoration and mature endpoints.
            super().load_state_dict(migrated)
    return CapacityReplay
