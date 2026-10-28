"""Optional finite-horizon critic input; the published actor still sees 49 inputs.

This is an explicitly registered algorithm adaptation, not a performance patch.
The time-conditioned ensemble also changes CHEQ's uncertainty and hence mixing.
Only fresh construction is supported; old checkpoints cannot be converted here.
"""
import torch
from torch import nn


def actor_without_clock(module, args):
    (observation,) = args
    if observation.shape[-1] != 50:
        raise ValueError('Clock learner expects 50 replay features before actor isolation')
    return (observation[..., :49],)


def install(learner):
    if learner.num_gradient_steps != 0 or learner.q_optimizer.state:
        raise ValueError('Clock architecture requires fresh critics and optimizer')
    agent = learner.agent
    if agent.actor.latent_pi[0].in_features != 49:
        raise ValueError('Expected original 49-dimensional CHEQ actor')
    # Preserve RNG: expanding the critics must not consume policy randomness.
    devices = [agent.actor.mu.weight.device.index] if agent.actor.mu.weight.is_cuda else []
    with torch.random.fork_rng(devices=devices):
        for ensemble in (agent.ensemble, agent.ensemble_targets):
            for q in ensemble:
                old = q.q_net[0]
                if not isinstance(old, nn.Linear):
                    raise ValueError('Expected upstream first Linear')
                new = nn.Linear(old.in_features+1, old.out_features,
                                bias=old.bias is not None, device=old.weight.device,
                                dtype=old.weight.dtype)
                with torch.no_grad():
                    new.weight[:, :49].copy_(old.weight[:, :49])
                    new.weight[:, 49].zero_()
                    new.weight[:, 50:].copy_(old.weight[:, 49:])
                    if old.bias is not None:
                        new.bias.copy_(old.bias)
                q.q_net[0] = new
    learner.q_optimizer = torch.optim.Adam(agent.ensemble.parameters(), **learner.q_optimizer.defaults)
    agent.ensemble_targets.requires_grad_(False)
    agent.actor.register_forward_pre_hook(actor_without_clock)
