"""Fixed-checkpoint causal action interventions; no privileged input or gating.

Use with run_with_substep_metrics_20260923.py --policy-transform MODULE:FUNCTION.
Always call the original policy once per observation, preserving ESN memory.
These are diagnostic variants, not new checkpoint selections or proposed fixes.
"""
import numpy as np


class ComponentAblation:
    def __init__(self, policy, label, zero_indices):
        self.policy = policy
        self.kind = getattr(policy, 'kind', 'policy') + '_' + label
        self.zero_indices = tuple(zero_indices)

    def reset(self):
        if hasattr(self.policy, 'reset'):
            self.policy.reset()

    def act(self, *args, **kwargs):
        action = np.asarray(self.policy.act(*args, **kwargs), dtype=float).copy()
        if action.shape != (7,) or not np.isfinite(action).all():
            raise ValueError('Expected finite action7')
        action[list(self.zero_indices)] = 0.
        return action


def slowdown_only(policy):
    return ComponentAblation(policy, 'slowdown_only', range(1, 7))


def yield_only(policy):
    return ComponentAblation(policy, 'yield_only', (0,))


def no_angular_yield(policy):
    return ComponentAblation(policy, 'no_angular_yield', (4, 5, 6))


def no_x_yield(policy):
    return ComponentAblation(policy, 'no_x_yield', (1,))


class CausalLowPass:
    """Fixed alpha=.25, all 7 raw action channels, before unchanged safety slew."""
    def __init__(self, policy):
        self.policy = policy
        self.kind = getattr(policy, 'kind', 'vmc') + '_lowpass_025'
        self.previous = np.zeros(7)

    def __getattr__(self, name):
        # Teacher diagnostics such as .slide remain available to the runner.
        return getattr(self.policy, name)

    def reset(self):
        if hasattr(self.policy, 'reset'):
            self.policy.reset()
        self.previous.fill(0.)

    def act(self, *args, **kwargs):
        action = np.asarray(self.policy.act(*args, **kwargs), dtype=float)
        if action.shape != (7,) or not np.isfinite(action).all():
            raise ValueError('Expected finite action7')
        self.previous += .25 * (action - self.previous)
        return self.previous.copy()


def lowpass_025(policy):
    return CausalLowPass(policy)


def neutral_action(policy):
    return ComponentAblation(policy, 'neutral_action', range(7))
