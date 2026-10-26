"""Exercise actual pinned CHEQ: actor isolation, critic gradients and restart."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import torch

from published_compliance_learner_20261025 import PublishedLearner
from validate_published_finite_check_20261025 import digest


def validate(root):
    torch.set_num_threads(1)
    spec = importlib.util.spec_from_file_location('original_learner', root/'source/tools/published_compliance_learner_20261025.py')
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    rows = []
    for name, dim in [('direct', 7), ('impedance', 5), ('admittance', 7), ('vmc', 7)]:
        kw = dict(dimension=dim, direct=name=='direct', seed=20261026, device='cpu',
                  algorithm='cheq', critic_layer_norm=True, numerical_amendments=True)
        old = original.PublishedLearner(root, **kw)
        old_state = old.state_dict()
        default = PublishedLearner(root, **kw)
        assert digest(default.state_dict()) == digest(old_state), 'Default constructor drift'
        clock = PublishedLearner(root, **kw, critic_clock=True)
        agent = clock.learner.agent
        assert digest(agent.actor.state_dict()) == digest(old.learner.agent.actor.state_dict())
        obs = torch.randn(256, 49)
        a = torch.zeros(256, dim)
        x = torch.cat([obs, torch.rand(256, 1)], dim=1).requires_grad_()
        z = x.detach().clone(); z[:, -1] = 0
        outputs = agent.actor(x)
        for left, right in zip(outputs, agent.actor(z)):
            torch.testing.assert_close(left, right, rtol=0, atol=0)
        sum(t.sum() for t in outputs).backward()
        assert x.grad[:, -1].count_nonzero() == 0
        torch.manual_seed(117); action, lp = agent.get_action_and_log_prob(x)
        torch.manual_seed(117); action0, lp0 = agent.get_action_and_log_prob(z)
        torch.testing.assert_close(action, action0, rtol=0, atol=0)
        torch.testing.assert_close(lp, lp0, rtol=0, atol=0)
        for q, oldq in zip(agent.ensemble, old.learner.agent.ensemble):
            torch.testing.assert_close(q(x, a), oldq(obs, a), rtol=2e-5, atol=2e-5)
        assert {id(p) for g in clock.learner.q_optimizer.param_groups for p in g['params']} == {
            id(p) for p in agent.ensemble.parameters()}
        assert not any(p.requires_grad for p in agent.ensemble_targets.parameters())
        aa = a.clone().requires_grad_()
        agent.ensemble_targets[0](x.detach(), aa).sum().backward()
        assert aa.grad.abs().sum() > 0
        for p in agent.parameters():
            p.grad = None
        agent.ensemble[0](x, a).sum().backward()
        assert agent.ensemble[0].q_net[0].weight.grad[:, 49].abs().sum() > 0
        raw = np.zeros(48, np.float32)
        clock.reset_episode(stream=4)
        assert clock.observation(raw, 4)[-1] == 1
        clock.act(raw, step=0, stream=4)
        np.testing.assert_allclose(clock.observation(raw, 4)[-1], 1374/1375)
        assert clock.observation(raw)[-1] == 1
        clock.episode_actions[4] = 859
        np.testing.assert_allclose(clock.terminal_observation(np.zeros(50), 4)[-1], 516/1375)
        clock.episode_actions[4] = 1374
        previous, _, _, _ = clock.act(raw, step=0, stream=4)
        assert clock.terminal_observation(previous, 4)[-1] == 0
        try:
            clock.act(raw, step=0, stream=4)
        except ValueError:
            pass
        else:
            raise AssertionError('Accepted action beyond horizon')
        clock.reset_episode(4)
        assert clock.observation(raw, 4)[-1] == 1
        rng = np.random.default_rng(11)
        batch = dict(observations=x.detach().numpy(), next_observations=z.numpy(),
            actions=np.zeros((256, dim), np.float32), rewards=rng.normal(size=(256,1)).astype(np.float32),
            dones=np.r_[np.ones(32),np.zeros(224)].astype(np.float32)[:,None],
            masks=np.ones((256,5), np.float32))
        clock.update(batch)
        state = clock.state_dict()
        clock.update(batch)
        expected = clock.state_dict()
        restored = PublishedLearner(root, **kw, critic_clock=True)
        restored.load_state_dict(copy.deepcopy(state))
        restored.update(batch)
        assert digest(restored.state_dict()) == digest(expected), 'Next update after restart differs'
        try:
            default.load_state_dict(state)
        except ValueError:
            pass
        else:
            raise AssertionError('Silent clock architecture conversion')
        # Validate the untouched default update against the frozen adapter.
        old.load_state_dict(copy.deepcopy(old_state))
        default_batch = {k:(v[:,:49] if k in ('observations','next_observations') else v) for k,v in batch.items()}
        old.update(default_batch); expected_default=old.state_dict()
        default.load_state_dict(copy.deepcopy(old_state)); default.update(default_batch)
        assert digest(default.state_dict()) == digest(expected_default), 'Default update drift'
        rows.append(dict(method=name, actor_dimension=49, critic_dimension=50, action_dimension=dim,
                         actor_isolated=True, critic_clock_gradient=True, default_exact=True,
                         next_update_restore_exact=True, stream_and_terminal_clock=True))
    return dict(passed=True, interfaces=rows, physics_steps=0, weights_promoted=False)


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); args=p.parse_args()
    result=validate(args.runtime)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
