"""Finite diagnostic of random-pair target averaging; actor minimum unchanged.

This changes the Bellman estimator. It retains terminal weight128, the proved
upper projection, every sampled pair and RNG call. No unproved lower bound.
"""
import hashlib
import inspect

import torch


def reduce_pair(first, second, mean_pair):
    if first.shape != second.shape:
        raise ValueError('Target pair shape mismatch')
    return (first + second) * .5 if mean_pair else torch.minimum(first, second)


def install(wrapper, mean_pair=False):
    from published_finite_target_projection_20261026 import install as projection
    source = inspect.getsource(projection)
    old = "new='min_q_next_target = _project_q(torch.min(q1_next_target, q2_next_target),"
    new = "new='min_q_next_target = _project_q(_reduce_pair(q1_next_target, q2_next_target, _mean_pair),"
    seam = 'namespace=dict(wrapper._original_train.__func__.__globals__,_terminal_extra_weight=127,'
    replacement = seam + '\n                   _reduce_pair=_reduce_pair,_mean_pair=_mean_pair,'
    if source.count(old) != 1 or source.count(seam) != 1:
        raise ValueError('Projected target implementation drift')
    candidate = source.replace(old, new).replace(seam, replacement)
    namespace = dict(projection.__globals__, _reduce_pair=reduce_pair, _mean_pair=mean_pair)
    exec(compile(candidate, '<registered_target_pair_reducer>', 'exec'), namespace)
    receipt = namespace['install'](wrapper, True)
    receipt.update(target_pair_reduction='mean' if mean_pair else 'minimum',
                   actor_pair_reduction='minimum', random_pair_selection_unchanged=True,
                   source_transform_sha256=hashlib.sha256(candidate.encode()).hexdigest())
    return receipt
