"""Shared read-only consumer entrypoints for the versioned history architecture.

No autonomous evaluation dispatch or training authorization. Callers must bind
this module and the architecture adapter in their own finite registration.
"""
import numpy as np
import torch
from persisted_history_critic import KEY, marker, history_class
from published_compliance_learner_20261025 import PublishedLearner
from published_pair_reduction_learner_20261026 import pair_class
from published_finite_target_projection_20261026 import project
from persisted_history_critic import project_with_history


def restore_learner(state, binding, runtime, device, seed=20261025):
    if state.get(KEY) != marker(binding):
        raise ValueError('Consumer requires exact history architecture registration')
    base = pair_class(PublishedLearner, 'minimum' if binding['method']=='impedance' else 'mean')
    learner = history_class(base, binding)(runtime, dimension=binding['action_dimension'],
        direct=False, seed=seed, device=device, algorithm='cheq', critic_layer_norm=True,
        numerical_amendments=True, critic_clock=True)
    learner.load_state_dict(state)
    return learner


def frozen_event(learner, external, event, step, stream=0):
    if event.get('kind') not in ('observation', 'terminal'):
        raise ValueError('Frozen history consumer expects an observation or terminal')
    learner.consume_interval(event['interval'], stream=stream)
    if event['kind'] == 'terminal':
        return None
    return external.call(learner.act, event['observation'], step=step,
                         deterministic=False, stream=stream)


def terminal_health(learner, arrays):
    """Descriptive terminal residuals only; no new health/convergence gate."""
    idx = np.flatnonzero(arrays['dones'][:,0] == 1)
    obs = torch.as_tensor(arrays['observations'][idx], device=learner.device)
    actions = torch.as_tensor(arrays['actions'][idx], device=learner.device)
    if obs.shape[1] != 51:
        raise ValueError('Health consumer requires migrated replay')
    with torch.no_grad():
        pred = torch.stack([q(obs,actions).reshape(-1) for q in learner.learner.agent.ensemble],1)
        target = torch.stack([q(obs,actions).reshape(-1) for q in learner.learner.agent.ensemble_targets],1)
        q = target[:,0:1]
        volume = float(np.log(learner.spaces.action_space.high.astype(np.float64)-learner.spaces.action_space.low.astype(np.float64)).sum())
        p = project_with_history(q, obs, float(learner.learner.alpha), .9995, volume)
        if not torch.equal(p, project(q,obs[:,:50],float(learner.learner.alpha),.9995,volume)):
            raise ValueError('History changed the original clock projection')
    if not torch.isfinite(pred).all() or not torch.isfinite(target).all():
        raise ValueError('Nonfinite terminal critic values')
    return dict(indices=idx, prediction=pred.cpu().numpy(), target_prediction=target.cpu().numpy())
