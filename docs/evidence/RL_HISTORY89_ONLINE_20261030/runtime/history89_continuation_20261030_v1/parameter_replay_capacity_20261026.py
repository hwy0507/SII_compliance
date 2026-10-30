"""Explicit append-only capacity migration; preserve all existing replay and RNG.

Capacity expansion changes future sampling relative to overwriting the old ring
once its old capacity is crossed. It is not an algorithmically equivalent change
past that boundary. Refuse overwrite at the expanded capacity as well.
"""
import copy
import numpy as np

MARKER = dict(version=1, original_capacity=1_000_000, capacity=2_000_000,
              retention='append_without_overwrite', sampling='uniform_all_retained_rows',
              full_behavior='raise_before_overwrite')


def replay_class(base, legacy_digest=None):
    class CapacityReplay(base):
        def __init__(self, dimension, observation_dim, seed, capacity=2_000_000):
            if capacity != MARKER['capacity']:
                raise ValueError('Registered expanded capacity required')
            super().__init__(dimension, observation_dim, seed, capacity=capacity)

        def add(self, **row):
            if self.size >= self.capacity or self.cursor != self.size:
                raise ValueError('Expanded replay must never overwrite retained rows')
            super().add(**row)
            self.cursor = self.size

        def state_dict(self):
            return dict(super().state_dict(), replay_capacity_extension=copy.deepcopy(MARKER))

        def load_state_dict(self, state):
            from validate_published_finite_check_20261025 import digest
            required = {'capacity', 'size', 'cursor', 'arrays', 'rng'}
            if 'replay_capacity_extension' in state:
                if set(state) != required | {'replay_capacity_extension'}:
                    raise ValueError('Unexpected expanded replay state fields')
                if state['replay_capacity_extension'] != MARKER or state['capacity'] != self.capacity:
                    raise ValueError('Missing or altered capacity marker')
            else:
                if (set(state) != required or legacy_digest is None or digest(state) != legacy_digest
                        or state['capacity'] != MARKER['original_capacity']
                        or state['size'] >= state['capacity']):
                    raise ValueError('Only exact registered unwrapped legacy parent may migrate')
            size = state['size']
            if (type(size) is not int or not 0 <= size <= self.capacity
                    or state['cursor'] != size or set(state['arrays']) != set(self.arrays)):
                raise ValueError('Replay is wrapped, malformed, or exceeds capacity')
            for key, value in state['arrays'].items():
                if (value.dtype != np.float32 or value.shape != (size, self.arrays[key].shape[1])
                        or not np.isfinite(value).all()):
                    raise ValueError('Invalid replay field: '+key)
            masks = state['arrays']['masks']
            if not np.all((masks == 0) | (masks == 1)):
                raise ValueError('Binary CHEQ bootstrap masks required')
            rng = np.random.default_rng()
            rng.bit_generator.state = copy.deepcopy(state['rng'])
            migrated = dict(state, capacity=self.capacity)
            migrated.pop('replay_capacity_extension', None)
            super().load_state_dict(migrated)
    return CapacityReplay
