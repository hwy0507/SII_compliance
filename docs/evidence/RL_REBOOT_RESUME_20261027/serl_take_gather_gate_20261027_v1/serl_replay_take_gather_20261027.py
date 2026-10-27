"""Candidate byte-equivalent gather for valid mature SERL replay rows.

No live patching, extra draws, reordering, dropped fields or serialized changes.
Requires an independently registered restore/update gate before deployment.
"""
import hashlib
import inspect
import numpy as np


def take_class(base, expected_sample_source_sha256):
    source = inspect.getsourcefile(base.sample)
    with open(source, 'rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != expected_sample_source_sha256:
            raise ValueError('Unexpected parent replay sampler')

    class TakeReplay(base):
        def sample(self, batch_size):
            if not self.ready:
                raise ValueError('No mature replay')
            draws = self.rng.integers(len(self.ready), size=batch_size)
            ids = self.ready_array[draws]
            end = self.target_endpoints[ids]
            # Clipping is used only after rejecting an invalid internal index.
            # Persisted loader independently validates the full ready partition.
            if ids.size and (ids.min() < 0 or ids.max() >= self.size
                             or end.min() < 0 or end.max() >= self.size):
                raise ValueError('Mature replay gather index outside retained data')
            values = {k: np.take(v, ids, axis=0, mode='clip')
                      for k, v in self.arrays.items()
                      if k not in ('rewards', 'next_observations')}
            values['rewards'] = np.take(self.target_rewards, ids, mode='clip')[:, None]
            values['next_observations'] = np.take(self.arrays['next_observations'], end,
                                                 axis=0, mode='clip')
            values['_bootstrap'] = np.take(self.target_bootstrap, ids, mode='clip')
            return values
    return TakeReplay
