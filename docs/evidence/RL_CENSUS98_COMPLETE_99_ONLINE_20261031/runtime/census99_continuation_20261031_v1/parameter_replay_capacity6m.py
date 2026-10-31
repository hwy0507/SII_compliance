"""Preparation-only 4m -> 6m append-only replay; no training dispatch.

Wrap the original Replay, then the original 52-column architecture wrapper.
Migration binds the complete stripped parent replay digest. Existing capacity
markers stay unchanged. Retaining rows past 4m differs from ring overwrite.
"""
import copy
import numpy as np
from parameter_replay_capacity_20261026 import MARKER as CAP2
from parameter_replay_capacity4m_20261027 import MARKER as CAP4

KEY = 'replay_capacity_third'
MARKER = dict(version=1, previous_capacity=4_000_000, capacity=6_000_000,
              retention='append_without_overwrite', sampling='uniform_all_retained_rows',
              full_behavior='raise_before_overwrite', historical_markers_preserved=True)


def replay_class(base, parent_digest=None):
    class CapacityReplay(base):
        def __init__(self, dimension, observation_dim, seed, capacity=6_000_000):
            if capacity != MARKER['capacity']:
                raise ValueError('Registered third expanded capacity required')
            super().__init__(dimension, observation_dim, seed, capacity=capacity)

        def add(self, **row):
            if self.size >= self.capacity or self.cursor != self.size:
                raise ValueError('Expanded replay must never overwrite retained rows')
            super().add(**row)
            self.cursor = self.size

        def state_dict(self):
            return dict(super().state_dict(), replay_capacity_extension=copy.deepcopy(CAP2),
                        replay_capacity_followup=copy.deepcopy(CAP4),
                        **{KEY: copy.deepcopy(MARKER)})

        def load_state_dict(self, state):
            from validate_published_finite_check_20261025 import digest
            required = {'capacity', 'size', 'cursor', 'arrays', 'rng',
                        'replay_capacity_extension', 'replay_capacity_followup'}
            if state.get('replay_capacity_extension') != CAP2 or state.get('replay_capacity_followup') != CAP4:
                raise ValueError('Historical capacity markers changed')
            if KEY in state:
                if set(state) != required | {KEY} or state[KEY] != MARKER or state['capacity'] != self.capacity:
                    raise ValueError('Unexpected third capacity state')
            elif (set(state) != required or parent_digest is None
                  or state['capacity'] != MARKER['previous_capacity']
                  or type(state['size']) is not int or not 0 <= state['size'] <= state['capacity']
                  or digest(state) != parent_digest):
                raise ValueError('Only exact registered unwrapped 4m parent may migrate')
            size = state['size']
            if (type(size) is not int or not 0 <= size <= self.capacity
                    or state['cursor'] != size or set(state['arrays']) != set(self.arrays)):
                raise ValueError('Replay is wrapped, malformed, or exceeds capacity')
            for key, value in state['arrays'].items():
                if (value.dtype != np.float32 or value.shape != (size, self.arrays[key].shape[1])
                        or not np.isfinite(value).all()):
                    raise ValueError('Invalid replay field: '+key)
            for key in ('masks', 'dones'):
                if not np.all((state['arrays'][key] == 0) | (state['arrays'][key] == 1)):
                    raise ValueError('Binary '+key+' required')
            rng = np.random.default_rng()
            rng.bit_generator.state = copy.deepcopy(state['rng'])
            plain = {k: v for k, v in state.items() if k not in
                     ('replay_capacity_extension', 'replay_capacity_followup', KEY)}
            super().load_state_dict(dict(plain, capacity=self.capacity))
    return CapacityReplay
