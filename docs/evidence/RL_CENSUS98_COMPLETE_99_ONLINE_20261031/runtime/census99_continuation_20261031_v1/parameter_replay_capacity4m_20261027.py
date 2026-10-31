"""Explicit second append-only capacity expansion, preserving the first marker.

Only a digest-bound unwrapped 2m parent can enter. Subsequent 4m restores carry
both historical and followup markers. Beyond 2m, retaining rows differs from
overwriting a ring; this does not claim algorithmic equivalence to a ring.
"""
import copy
import numpy as np

from parameter_replay_capacity_20261026 import MARKER as ORIGINAL_MARKER

MARKER = dict(version=1, previous_capacity=2_000_000, capacity=4_000_000,
              retention='append_without_overwrite', sampling='uniform_all_retained_rows',
              full_behavior='raise_before_overwrite', historical_marker_preserved=True)


def replay_class(base, parent_digest=None):
    class CapacityReplay(base):
        def __init__(self, dimension, observation_dim, seed, capacity=4_000_000):
            if capacity != MARKER['capacity']:
                raise ValueError('Registered second expanded capacity required')
            super().__init__(dimension, observation_dim, seed, capacity=capacity)

        def add(self, **row):
            if self.size >= self.capacity or self.cursor != self.size:
                raise ValueError('Expanded replay must never overwrite retained rows')
            super().add(**row)
            self.cursor = self.size

        def state_dict(self):
            return dict(super().state_dict(),
                        replay_capacity_extension=copy.deepcopy(ORIGINAL_MARKER),
                        replay_capacity_followup=copy.deepcopy(MARKER))

        def load_state_dict(self, state):
            from validate_published_finite_check_20261025 import digest
            required = {'capacity', 'size', 'cursor', 'arrays', 'rng', 'replay_capacity_extension'}
            if state.get('replay_capacity_extension') != ORIGINAL_MARKER:
                raise ValueError('Original historical capacity marker changed')
            if 'replay_capacity_followup' in state:
                if (set(state) != required | {'replay_capacity_followup'}
                        or state['replay_capacity_followup'] != MARKER
                        or state['capacity'] != self.capacity):
                    raise ValueError('Unexpected second capacity state')
            elif (set(state) != required or parent_digest is None
                    or state['capacity'] != MARKER['previous_capacity']
                    or digest(state) != parent_digest
                    or not 0 <= state['size'] <= state['capacity']):
                raise ValueError('Only exact registered unwrapped 2m parent may migrate')
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
            # Reject invalid RNG before the base loader writes any arrays.
            rng = np.random.default_rng()
            rng.bit_generator.state = copy.deepcopy(state['rng'])
            migrated = dict(state, capacity=self.capacity)
            migrated.pop('replay_capacity_extension')
            migrated.pop('replay_capacity_followup', None)
            super().load_state_dict(migrated)
    return CapacityReplay
