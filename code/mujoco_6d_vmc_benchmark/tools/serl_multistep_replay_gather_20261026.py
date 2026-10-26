"""Candidate equivalent gather optimization; never patches a live run.

The original replay samples raw reward and next observation, then replaces
both with derived multistep fields. Skip only those overwritten gathers.
"""
import hashlib
import inspect

EXPECTED_BASE = '395eb3c618d37d6e3dad338478a7017d3fc273d7368bb2a8a8c488cfcdd840de'


def optimized_class(base):
    path = inspect.getsourcefile(base.sample)
    with open(path, 'rb') as f:
        if hashlib.file_digest(f, 'sha256').hexdigest() != EXPECTED_BASE:
            raise ValueError('Candidate gather requires the reviewed frozen multistep source')

    class OptimizedReplay(base):
        def sample(self, batch_size):
            if not self.ready:
                raise ValueError('No mature replay')
            draws = self.rng.integers(len(self.ready), size=batch_size)
            ids = self.ready_array[draws]
            end = self.target_endpoints[ids]
            values = {k:v[ids] for k,v in self.arrays.items()
                      if k not in ('rewards', 'next_observations')}
            values['rewards'] = self.target_rewards[ids,None]
            values['next_observations'] = self.arrays['next_observations'][end]
            values['_bootstrap'] = self.target_bootstrap[ids]
            return values
    return OptimizedReplay
