"""Suppress unused CHEQ target-parameter gradients, retaining action gradients.

Target weights are updated by Polyak averaging, never by an optimizer. Actor
gradients must still flow through target critics to their action inputs. This
does not use no_grad around actor loss or change any Bellman/actor objective.
"""


def freeze_target_parameters(learner):
    targets = getattr(learner.agent, 'ensemble_targets', None)
    if targets is None:
        raise ValueError('This helper is specifically for the published CHEQ ensemble')
    count = 0
    for parameter in targets.parameters():
        parameter.requires_grad_(False)
        parameter.grad = None
        count += parameter.numel()
    if not count:
        raise ValueError('No target critic parameters found')
    return count
