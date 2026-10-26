"""Candidate equivalent one-transfer batch construction for multistep SERL.

Keeps original shape/finite/clock/bootstrap validation and contiguous actor48
leaves. Avoids transferring a one-step mask that is immediately overwritten.
No optimizer formula, sampling distribution, or checkpoint field changes.
"""
import hashlib
import inspect
import numpy as np


def transfer_class(base):
    with open(inspect.getsourcefile(base.batch), 'rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != '395eb3c618d37d6e3dad338478a7017d3fc273d7368bb2a8a8c488cfcdd840de':
            raise ValueError('Expected reviewed frozen multistep adapter')

    class TransferLearner(base):
        def batch(self, arrays):
            observations = {}
            for key in ('observations', 'next_observations'):
                value = np.asarray(arrays[key], np.float32)
                if value.ndim != 2 or value.shape[-1] != 49 or not np.isfinite(value).all():
                    raise ValueError('Finite migrated replay49 required')
                if np.any(value[:,48] < 0) or np.any(value[:,48] > 1):
                    raise ValueError('Clock outside unit interval')
                observations[key] = dict(state=np.ascontiguousarray(value[:,:48]),
                                         clock=np.ascontiguousarray(arrays[key][:,48:49]))
            rewards = np.asarray(arrays['rewards'], np.float32).reshape(-1)
            actions = np.asarray(arrays['actions'], np.float32)
            # Retain the original requirement that dones can be converted, even
            # though its one-step mask is replaced by the registered bootstrap.
            np.asarray(arrays['dones'], np.float32).reshape(-1)
            if '_bootstrap' not in arrays:
                raise ValueError('Derived multistep batch required')
            mask = np.asarray(arrays['_bootstrap'], np.float32)
            if mask.shape != rewards.shape or not np.isfinite(mask).all():
                raise ValueError('Invalid derived bootstrap shape/values')
            if np.any((mask < 0) | (mask > 1)):
                raise ValueError('Derived bootstrap outside unit interval')
            return self.jax.device_put(dict(**observations, rewards=rewards,
                                           actions=actions, masks=mask))
    return TransferLearner
