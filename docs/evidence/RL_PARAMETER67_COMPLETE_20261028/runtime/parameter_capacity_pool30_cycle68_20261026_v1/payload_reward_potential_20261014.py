"""Privileged TRAINING REWARD only; never concatenate these fields into actor48.

Replace arm-reference progress with measured approach/lift/payload-goal progress.
Scales .04m and .10m are inherited from existing reference potential/lift gate.
Potential-based gamma shaping with terminal cancellation preserves base return
ordering for fixed initial state; test concerns TD guidance, not success relabeling.
"""
import numpy as np


def payload_potential(hand, payload, destination):
    hand,payload,destination=(np.asarray(v,float) for v in (hand,payload,destination))
    if any(v.shape!=(3,) or not np.isfinite(v).all() for v in (hand,payload,destination)):
        raise ValueError('Finite physical positions required for reward-only potential')
    approach=1./(1.+np.linalg.norm(hand-payload)/.04)
    lift=float(np.clip((payload[2]-.425)/.10,0.,1.))
    goal=1./(1.+np.linalg.norm(payload-destination)/.04)
    return float((approach+lift+goal)/3.)
