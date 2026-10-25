"""Candidate performance amendment for resumed noncapturable, nonfused Adam.

Only scalar step counters move to CPU. Parameters, moments and update equations
stay unchanged. Not installed in any formal learner by this module.
"""
import torch


def move_adam_steps_to_cpu(optimizer):
    if type(optimizer) is not torch.optim.Adam:
        raise ValueError('Only registered torch.optim.Adam is supported')
    states = []
    for group in optimizer.param_groups:
        if group.get('capturable') or group.get('fused') or group.get('differentiable'):
            raise ValueError('Capturable, fused or differentiable Adam is unsupported')
        for parameter in group['params']:
            state = optimizer.state.get(parameter, {})
            if not state:
                continue
            step = state.get('step')
            if (not torch.is_tensor(step) or step.numel() != 1 or step.ndim != 0
                    or not step.is_floating_point() or step.requires_grad
                    or not torch.isfinite(step).item() or step.item() < 0):
                raise ValueError('Expected finite nonnegative scalar Adam step')
            states.append(state)
    # Validate every group first, so unsupported configurations remain untouched.
    moved = sum(state['step'].device.type != 'cpu' for state in states)
    for state in states:
        state['step'] = state['step'].cpu()
    return dict(step_tensors=len(states), moved_to_cpu=moved)
