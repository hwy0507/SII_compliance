from pathlib import Path
from types import SimpleNamespace
import copy
import sys
import unittest
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from probe_published_actor_lr_20261025 import set_actor_learning_rate, set_learning_rate
from validate_published_finite_check_20261025 import digest


class ActorRateTests(unittest.TestCase):
    def test_critic_lr_preserves_actor_alpha_weights_and_all_adam_moments(self):
        parameters = [torch.nn.Parameter(torch.tensor([float(i+1)])) for i in range(3)]
        optimizers = [torch.optim.Adam([p], lr=lr)
                      for p, lr in zip(parameters, [3e-5, 3e-4, 3e-4])]
        for p, opt in zip(parameters, optimizers):
            p.square().sum().backward(); opt.step()
        learner = SimpleNamespace(actor_optimizer=optimizers[0], q_optimizer=optimizers[1],
                                  a_optimizer=optimizers[2])
        before = [copy.deepcopy(opt.state_dict()) for opt in optimizers]
        weights = [p.detach().clone() for p in parameters]
        rates = set_learning_rate(learner, .1, 'critic')
        self.assertAlmostEqual(rates[0]['after'], 3e-5)
        for i, opt in enumerate(optimizers):
            after = copy.deepcopy(opt.state_dict())
            if i == 1:
                after['param_groups'][0]['lr'] = before[i]['param_groups'][0]['lr']
            self.assertEqual(digest(after), digest(before[i]))
            torch.testing.assert_close(parameters[i], weights[i], rtol=0, atol=0)
        for optimizer, factor in [('temperature', .1), ('critic', 0), ('critic', float('nan'))]:
            unchanged = digest([opt.state_dict() for opt in optimizers])
            with self.assertRaises(ValueError):
                set_learning_rate(learner, factor, optimizer)
            self.assertEqual(digest([opt.state_dict() for opt in optimizers]), unchanged)

    def test_only_actor_lr_changes_and_moments_survive(self):
        param=torch.nn.Parameter(torch.tensor([2.]))
        actor=torch.optim.Adam([param],lr=3e-4)
        param.square().sum().backward();actor.step()
        before=copy.deepcopy(actor.state_dict());weight=param.detach().clone()
        other=torch.optim.Adam([torch.nn.Parameter(torch.tensor([3.]))],lr=3e-4)
        other_before=copy.deepcopy(other.state_dict())
        result=set_actor_learning_rate(SimpleNamespace(actor_optimizer=actor,q_optimizer=other),.1)
        self.assertAlmostEqual(result[0]['after'],3e-5)
        after=actor.state_dict();after['param_groups'][0]['lr']=before['param_groups'][0]['lr']
        self.assertEqual(after['param_groups'],before['param_groups'])
        for key,value in before['state'][0].items():torch.testing.assert_close(after['state'][0][key],value,rtol=0,atol=0)
        torch.testing.assert_close(param,weight,rtol=0,atol=0)
        self.assertEqual(other.state_dict(),other_before)

    def test_invalid_factor_rejected_without_mutation(self):
        param=torch.nn.Parameter(torch.tensor([2.]));actor=torch.optim.Adam([param],lr=3e-4)
        for factor in [0.,-1.,float('inf'),float('nan')]:
            with self.assertRaises(ValueError):set_actor_learning_rate(SimpleNamespace(actor_optimizer=actor),factor)
            self.assertEqual(actor.param_groups[0]['lr'],3e-4)


if __name__=='__main__':unittest.main()
