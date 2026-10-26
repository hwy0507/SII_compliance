"""Experimental separation of temperature states from n-step critic endpoints.

No official source is modified. The candidate delegates the temperature loss
to the pinned official implementation with a separately supplied successor.
Critic/actor losses, optimizers, update ratios and RNG handling stay inherited.
This helper alone is not a formal checkpoint migration or deployment driver.
"""
from functools import lru_cache
import numpy as np


@lru_cache(maxsize=1)
def candidate_agent_class():
    import flax.struct
    from serl_launcher.agents.continuous.sac import SACAgent

    @flax.struct.dataclass
    class TemperatureStateAgent(SACAgent):
        def temperature_loss_fn(self, batch, params, rng):
            if 'temperature_next_observations' not in batch:
                raise ValueError('Explicit temperature successor states required')
            temperature_batch = dict(batch)
            temperature_batch['next_observations'] = batch['temperature_next_observations']
            return super().temperature_loss_fn(temperature_batch, params, rng)

    return TemperatureStateAgent


def convert_agent(agent):
    from serl_launcher.agents.continuous.sac import SACAgent
    if type(agent) is not SACAgent:
        raise ValueError('Convert an original pinned SACAgent exactly once')
    return candidate_agent_class()(state=agent.state, config=agent.config)


def augment_batch(learner, batch, temperature_observations):
    """Validate normalized49 successors and add only the temperature leaf."""
    value = np.asarray(temperature_observations, np.float32)
    count = batch['rewards'].shape[0]
    if value.shape != (count, 49) or not np.isfinite(value).all():
        raise ValueError('Finite temperature successor matrix (batch,49) required')
    if np.any((value[:, 48] < 0) | (value[:, 48] > 1)):
        raise ValueError('Temperature successor clock outside [0,1]')
    successor = dict(state=np.ascontiguousarray(value[:, :48]),
        clock=np.ascontiguousarray(value[:, 48:49]))
    return dict(batch, temperature_next_observations=learner.jax.device_put(successor))


def candidate_learner_class(base):
    class TemperatureStateLearner(base):
        def batch(self, arrays):
            if '_temperature_observations' not in arrays:
                raise ValueError('Explicit temperature observations required')
            return augment_batch(self, super().batch(arrays), arrays['_temperature_observations'])

    return TemperatureStateLearner
