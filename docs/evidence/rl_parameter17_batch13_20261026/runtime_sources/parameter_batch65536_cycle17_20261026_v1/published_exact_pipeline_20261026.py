"""Candidate exact replay acceptance and batched Polyak operations.

No batch, RNG, target formula or update cadence changes. Binary masks permit
an acceptance proof from a prefix; an inconclusive prefix uses the old full
reduction. The foreach implementation must pass full-state equivalence gates.
"""
import hashlib
import inspect
import types

import numpy as np
import torch


def accepted(binary_masks, indices):
    prefix = binary_masks[indices[:32]]
    if np.all(prefix.sum(axis=0) > 0):
        return True
    return not np.any(binary_masks[indices].sum(axis=0) == 0)


def cache_class(base):
    class ExactCache(base):
        def refresh(self):
            mask = self.replay.arrays['masks'][:self.replay.size]
            if not np.all((mask == 0) | (mask == 1)):
                raise ValueError('Prefix acceptance requires binary bootstrap masks')
            super().refresh()

        def sample(self, count=256):
            while True:
                index = self.replay.rng.integers(self.replay.size, size=count)
                if not accepted(self.replay.arrays['masks'], index):
                    continue
                device_index = torch.as_tensor(index, device=self.device)
                return {key: torch.index_select(value, 0, device_index)
                        for key, value in self.arrays.items()}
    return ExactCache


def install_foreach(wrapper):
    learner = wrapper.learner
    # A matched probe restores the same learner repeatedly. Validate the frozen
    # original method again, then bind fresh parameter references after restore.
    original = getattr(learner, '_sii_foreach_original_target_update',
                       learner.update_target_networks)
    source = inspect.getsource(original)
    if ('target_param.data.mul_(1 - self.polyak_factor)' not in source or
            'torch.add(target_param.data, param.data, alpha=self.polyak_factor, out=target_param.data)' not in source):
        raise ValueError('Unexpected target averaging implementation')
    learner._sii_foreach_original_target_update = original
    online, target = [], []
    for current, delayed in zip(learner.agent.ensemble, learner.agent.ensemble_targets, strict=True):
        pairs = list(zip(current.parameters(), delayed.parameters(), strict=True))
        for p, t in pairs:
            if p.shape != t.shape or p.dtype != t.dtype or p.device != t.device:
                raise ValueError('Target parameter contract mismatch')
            online.append(p)
            target.append(t)

    def update_target_networks(self):
        with torch.no_grad():
            torch._foreach_mul_(target, 1-self.polyak_factor)
            torch._foreach_add_(target, online, alpha=self.polyak_factor)

    learner.update_target_networks = types.MethodType(update_target_networks, learner)
    return dict(base_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                parameter_tensors=len(online), formula='target*(1-tau) + tau*online',
                batch_size_changed=False, update_frequency_changed=False)
