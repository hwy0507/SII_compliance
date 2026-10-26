"""Experimental actor entropy coefficient floor with original dual optimizer.

Only for pinned SERL without entropy backup. Official policy loss calls the
floored forward value, while the inherited temperature Lagrange loss continues
using the original learned multiplier. This is an actor-objective intervention,
not a claim to reproduce a constrained dual algorithm or a deployment loader.
"""
from functools import lru_cache
import math


@lru_cache(maxsize=1)
def candidate_agent_class():
    import flax.struct
    import jax.numpy as jnp
    from serl_launcher.agents.continuous.sac import SACAgent

    @flax.struct.dataclass
    class ActorEntropyFloorAgent(SACAgent):
        actor_entropy_floor: float = flax.struct.field(pytree_node=False, default=0.0)

        def raw_temperature(self, *, grad_params=None):
            return super().forward_temperature(grad_params=grad_params)

        def forward_temperature(self, *, grad_params=None):
            value = self.raw_temperature(grad_params=grad_params)
            if self.actor_entropy_floor == 0.0:
                return value
            return jnp.maximum(value, self.actor_entropy_floor)

    return ActorEntropyFloorAgent


def convert_agent(agent, floor):
    from serl_launcher.agents.continuous.sac import SACAgent
    if type(agent) is not SACAgent:
        raise ValueError('Convert original pinned SACAgent exactly once')
    if not math.isfinite(floor) or floor not in (0.0, 0.1):
        raise ValueError('Only registered control0 and candidate0.1 supported')
    if agent.config['backup_entropy']:
        raise ValueError('Actor-only intervention requires no entropy backup')
    return candidate_agent_class()(state=agent.state, config=agent.config, actor_entropy_floor=float(floor))
