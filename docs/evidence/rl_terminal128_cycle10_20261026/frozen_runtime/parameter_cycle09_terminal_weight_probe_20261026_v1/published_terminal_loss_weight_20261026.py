"""Explicit terminal weighting in CHEQ critic regression, with unchanged actor loss.

This changes the fitting objective; it is not an equivalent optimization. All
critic rows retain positive weights and each critic's masked loss is normalized
by its actual total weight. No reward, bootstrap, sampling or state reset.
"""
import ast
import hashlib
from pathlib import Path
import textwrap
import types


def install(wrapper, weight):
    if weight not in (1, 128) or wrapper.bellman_target_count != 2:
        raise ValueError('Registered weight1/128 and original pair target required')
    source = (Path(wrapper.runtime)/'published_cheq/agents/rl/sac_ensemble.py').read_text()
    cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == 'SACEnsemble')
    node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'train')
    base = textwrap.dedent(''.join(source.splitlines(keepends=True)[node.lineno-1:node.end_lineno]))
    if not wrapper.numerical_amendments:
        raise ValueError('Expected already registered numerical amendments')
    before = 'min_q_pi = torch.min(q1_pi, q2_pi).view(-1)'
    assert base.count(before) == 1
    base = base.replace(before, 'min_q_pi = torch.min(q1_pi, q2_pi).view(-1, 1)')
    digest = hashlib.sha256(base.encode()).hexdigest()
    if digest != wrapper.numerical_patch_receipt['ensemble_sac']['replacement_sha256']:
        raise ValueError('Reconstructed current training implementation differs')
    old = '((q_a_values[q_net] - next_q_value)**2 * data.masks[:, q_net].view(-1)).sum() / torch.sum(data.masks[:, q_net])'
    new = '((q_a_values[q_net] - next_q_value)**2 * data.masks[:, q_net].view(-1) * (1 + _terminal_extra_weight * data.dones.flatten())).sum() / (data.masks[:, q_net].view(-1) * (1 + _terminal_extra_weight * data.dones.flatten())).sum()'
    if base.count(old) != 1:
        raise ValueError('Critic regression seam changed')
    candidate = base.replace(old, new)
    namespace = dict(wrapper._original_train.__func__.__globals__, _terminal_extra_weight=weight-1)
    exec(compile(candidate, '<registered_terminal_weighted_critic>', 'exec'), namespace)
    wrapper.learner.train = types.MethodType(namespace['train'], wrapper.learner)
    return dict(weight=weight, base_sha256=digest,
                candidate_sha256=hashlib.sha256(candidate.encode()).hexdigest(),
                actor_objective_unchanged=True, reward_unchanged=True)
