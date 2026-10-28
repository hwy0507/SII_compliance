"""Explicit candidate: all-five target minimum, preserving actor's sampled pair.

This changes the Bellman operator and is NOT an equivalent performance patch or
an exact reproduction of the authors' implementation. Use only in registered
independent diagnostics until a separate online stage is reviewed.
"""
import ast
import hashlib
import inspect
from pathlib import Path
import textwrap
from types import MethodType

import torch


def all_critic_minimum(learner, state, action):
    if torch.is_grad_enabled():
        raise RuntimeError('Bellman minimum must be evaluated without gradients')
    values = [learner.agent.get_q_value(state=state, action=action, q_net=i, target=True)
              for i in range(learner.ensemble_size)]
    if not values or any(v.ndim != 2 or v.shape != (len(state), 1) for v in values):
        raise ValueError('Expected column-shaped target Q values')
    return torch.stack(values).amin(dim=0)


def transform_train_source(source):
    tree = ast.parse(source)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'SACEnsemble']
    if len(classes) != 1:
        raise ValueError('Expected one published SACEnsemble class')
    methods = [n for n in classes[0].body if isinstance(n, ast.FunctionDef) and n.name == 'train']
    if len(methods) != 1:
        raise ValueError('Expected one published train method')
    original = textwrap.dedent(ast.get_source_segment(source, methods[0]))
    first = 'q1_next_target = self.agent.get_q_value(state=data.next_observations, action=next_state_actions, q_net=indices[0], target=True)'
    second = 'q2_next_target = self.agent.get_q_value(state=data.next_observations, action=next_state_actions, q_net=indices[1], target=True)'
    target = 'min_q_next_target = torch.min(q1_next_target, q2_next_target) - self.alpha * next_state_log_pi'
    actor = 'min_q_pi = torch.min(q1_pi, q2_pi).view(-1)'
    if any(original.count(seam) != 1 for seam in (first, second, target, actor)):
        raise ValueError('Published target or registered numerical seam changed')
    candidate = original.replace(first, '# Registered all-five Bellman target below.')
    candidate = candidate.replace(second, '# Actor still uses the original sampled critic pair.')
    candidate = candidate.replace(target, 'min_q_next_target = _sii_all_critic_minimum(self, data.next_observations, next_state_actions) - self.alpha * next_state_log_pi')
    # Retain the already registered numerical amendment; do not reintroduce BxB broadcasting.
    candidate = candidate.replace(actor, 'min_q_pi = torch.min(q1_pi, q2_pi).view(-1, 1)')
    return original, candidate


def install_bellman_minimum(learner, count):
    if count not in (2, 5) or learner.ensemble_size != 5:
        raise ValueError('This candidate compares original pair with all five critics')
    original = learner.train
    if original.__func__.__code__.co_filename != '<registered_sii_ensemble_sac_column_actor_loss>':
        raise ValueError('Expected original learner with registered column-loss amendment only')
    if count == 2:
        return dict(target_count=2, original_bound_method_preserved=True)
    source = Path(inspect.getfile(type(learner))).read_text()
    raw, candidate = transform_train_source(source)
    namespace = dict(original.__func__.__globals__, _sii_all_critic_minimum=all_critic_minimum)
    exec(compile(candidate, '<registered_sii_all5_bellman_minimum>', 'exec'), namespace)
    learner.train = MethodType(namespace['train'], learner)
    return dict(target_count=5, original_sha256=hashlib.sha256(raw.encode()).hexdigest(),
        candidate_sha256=hashlib.sha256(candidate.encode()).hexdigest(),
        actor_pair_selection_preserved=True, target_only=True)
