from dataclasses import dataclass, asdict
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from probe_goal_actor_regularization_20261016 import set_probe_regularization


@dataclass(frozen=True)
class Config:
    actor_bc_alpha: float = 0.
    gamma: float = .9995
    n_step: int = 25
    target_tau: float = .005


class ProbeRegularizationTests(unittest.TestCase):
    def agent(self):
        return SimpleNamespace(config=asdict(Config()),raw_agent=SimpleNamespace(
            _cfg=Config(),_actor=object(),_critic=object(),_temperature=object(),_rng=object()))

    def test_only_loss_coefficient_changes_without_model_or_rng_reset(self):
        for alpha in (0.,1.):
            agent=self.agent();before=dict(vars(agent.raw_agent))
            set_probe_regularization(agent,alpha)
            self.assertEqual(agent.config,dict(asdict(Config()),actor_bc_alpha=alpha))
            self.assertEqual(asdict(agent.raw_agent._cfg),agent.config)
            for key,value in before.items():
                if key!='_cfg':self.assertIs(getattr(agent.raw_agent,key),value)

    def test_invalid_or_previously_treated_state_rejected(self):
        for alpha in (True,-1.,.5,2.,float('nan')):
            with self.assertRaises(ValueError):set_probe_regularization(self.agent(),alpha)
        agent=self.agent();set_probe_regularization(agent,1.)
        with self.assertRaises(ValueError):set_probe_regularization(agent,0.)


if __name__=='__main__':unittest.main()
