"""Explicit numerical amendments to the pinned authors' SAC implementation.

No observation/action/physics changes. Stable tanh log-Jacobians retain entropy
gradients near saturation. Column-shaped actor Q avoids an unnecessary BxB
broadcast whose mean is mathematically the same scalar policy objective.
"""
import hashlib
import inspect
import textwrap

import torch


def tanh_log_jacobian(pre_tanh, scale):
    return torch.log(scale)+2*(0.6931471805599453-pre_tanh-torch.nn.functional.softplus(-2*pre_tanh))


def stable_action_and_log_prob(self, observation):
    mean, log_std = self(observation)
    distribution = torch.distributions.Normal(mean, log_std.exp())
    pre_tanh = distribution.rsample().to(self.device).to(torch.float)
    action = pre_tanh.tanh()*self.action_scale+self.action_bias
    log_prob = (distribution.log_prob(pre_tanh).to(self.device).to(torch.float)
        -tanh_log_jacobian(pre_tanh, self.action_scale)).sum(1, keepdim=True)
    return action, log_prob


def install():
    from agents.rl.policies import SACActor
    from agents.rl.sac import SAC
    from agents.rl.sac_ensemble import SACEnsemble
    if getattr(SACActor, '_sii_numerics_receipt', None) is not None:
        return SACActor._sii_numerics_receipt
    receipt = {'actor': dict(original_sha256=hashlib.sha256(
        inspect.getsource(SACActor.get_action_and_log_prob).encode()).hexdigest(),
        replacement_sha256=hashlib.sha256(inspect.getsource(stable_action_and_log_prob).encode()).hexdigest())}
    for name, cls, old, new in [
        ('sac', SAC, 'min_qf_pi = torch.min(qf1_pi, qf2_pi).view(-1)',
         'min_qf_pi = torch.min(qf1_pi, qf2_pi).view(-1, 1)'),
        ('ensemble_sac', SACEnsemble, 'min_q_pi = torch.min(q1_pi, q2_pi).view(-1)',
         'min_q_pi = torch.min(q1_pi, q2_pi).view(-1, 1)')]:
        original = textwrap.dedent(inspect.getsource(cls.train))
        if original.count(old) != 1:
            raise ValueError('Published actor-loss shape seam changed: '+name)
        replacement = original.replace(old, new)
        namespace = dict(cls.train.__globals__)
        exec(compile(replacement, '<registered_sii_'+name+'_column_actor_loss>', 'exec'), namespace)
        cls.train = namespace['train']
        receipt[name] = dict(original_sha256=hashlib.sha256(original.encode()).hexdigest(),
            replacement_sha256=hashlib.sha256(replacement.encode()).hexdigest(), old=old, new=new)
    SACActor.get_action_and_log_prob = stable_action_and_log_prob
    SACActor._sii_numerics_receipt = receipt
    return receipt
