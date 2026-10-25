from pathlib import Path
from types import SimpleNamespace
import copy
import sys
import unittest
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from probe_published_actor_lr_20261025 import set_actor_learning_rate


class ActorRateTests(unittest.TestCase):
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
