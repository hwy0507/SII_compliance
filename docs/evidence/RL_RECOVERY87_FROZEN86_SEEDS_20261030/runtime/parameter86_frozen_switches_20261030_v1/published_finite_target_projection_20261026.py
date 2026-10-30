"""Project target-critic estimates onto a proved finite-horizon upper bound.

The bound is 30 + alpha*log(action volume)*sum(gamma**k,k=1..n-1).
Potential shaping telescopes to a nonpositive contribution; running costs are
nonpositive and terminal plus completion reward is at most30. Project Q before
subtracting the sampled entropy term, not the stochastic Bellman target itself.
This is an explicit learning-objective adaptation, not equivalent optimization.
"""
import ast
import hashlib
import math
from pathlib import Path
import textwrap
import types
import numpy as np
import torch


def bound(alpha, gamma, remaining, log_volume):
    if not math.isfinite(alpha) or alpha < 0 or gamma != .9995 or not math.isfinite(log_volume) or log_volume <= 0:
        raise ValueError('Expected frozen reward discount and finite nonnegative entropy coefficient')
    # Compute in float64, then round upward by one output ULP so float32
    # rounding does not turn a valid upper bound into a lower threshold.
    n=remaining.to(torch.float64)
    exact=30. + alpha*log_volume*gamma*(1.-torch.pow(gamma,n-1.))/(1.-gamma)
    rounded=exact.to(remaining.dtype)
    return torch.nextafter(rounded,torch.full_like(rounded,float('inf')))


def project(q, observation, alpha, gamma, log_volume, enabled=True):
    if not enabled:
        return q
    if observation.shape[-1] != 50 or q.shape != (observation.shape[0], 1):
        raise ValueError('Expected clock critic with column target values')
    n=torch.round(observation[:,49:50]*1375.).clamp(1.,1375.)
    return torch.minimum(q, bound(alpha,gamma,n,log_volume))


def install(wrapper, enabled=True):
    if not wrapper.critic_clock or wrapper.learner.gamma != .9995:
        raise ValueError('Projection requires the registered finite-horizon clock and discount')
    from published_terminal_loss_weight_20261026 import install as install_terminal
    receipt=install_terminal(wrapper,128)
    source=(Path(wrapper.runtime)/'published_cheq/agents/rl/sac_ensemble.py').read_text()
    cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='SACEnsemble')
    node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='train')
    base=textwrap.dedent(''.join(source.splitlines(keepends=True)[node.lineno-1:node.end_lineno]))
    base=base.replace('min_q_pi = torch.min(q1_pi, q2_pi).view(-1)', 'min_q_pi = torch.min(q1_pi, q2_pi).view(-1, 1)')
    if hashlib.sha256(base.encode()).hexdigest()!=receipt['base_sha256']:raise ValueError('Numerical source drift')
    import inspect
    tree=ast.parse(textwrap.dedent(inspect.getsource(install_terminal)))
    strings={n.targets[0].id:n.value.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str)}
    if base.count(strings['old'])!=1:raise ValueError('Terminal-weight seam drift')
    weighted=base.replace(strings['old'],strings['new'])
    if hashlib.sha256(weighted.encode()).hexdigest()!=receipt['candidate_sha256']:raise ValueError('Weighted source reconstruction differs')
    old='min_q_next_target = torch.min(q1_next_target, q2_next_target) - self.alpha * next_state_log_pi'
    new='min_q_next_target = _project_q(torch.min(q1_next_target, q2_next_target), data.next_observations, self.alpha, self.gamma, _log_volume, _projection_enabled) - self.alpha * next_state_log_pi'
    if weighted.count(old)!=1:raise ValueError('Target projection seam drift')
    candidate=weighted.replace(old,new)
    log_volume=float(np.log(np.asarray(wrapper.spaces.action_space.high,dtype=np.float64)-np.asarray(wrapper.spaces.action_space.low,dtype=np.float64)).sum())
    namespace=dict(wrapper._original_train.__func__.__globals__,_terminal_extra_weight=127,
                   _project_q=project,_log_volume=log_volume,_projection_enabled=enabled)
    exec(compile(candidate,'<registered_finite_target_projection>','exec'),namespace)
    wrapper.learner.train=types.MethodType(namespace['train'],wrapper.learner)
    return dict(enabled=enabled,terminal_weight=128,log_action_volume=log_volume,
                weighted_base_sha256=receipt['candidate_sha256'],candidate_sha256=hashlib.sha256(candidate.encode()).hexdigest(),
                projection_position='target critic Q before stochastic entropy term',terminal_cap=30.,gamma=.9995)
