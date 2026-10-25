import math
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from diagnose_published_value_bound_20261025 import soft_upper_bound,audit_episode


class SoftBoundTests(unittest.TestCase):
    def test_single_step_and_zero_entropy_weight(self):
        self.assertEqual(soft_upper_bound(10.,.9995,1,[-1],[1],.4),28.)
        self.assertEqual(soft_upper_bound(0.,.9995,1375,[-1],[1]),30.)

    def test_uniform_policy_finite_horizon_return_is_bounded(self):
        for gamma in [0.,.9,.9995,1.]:
            for n in [1,3,1375]:
                entropy=sum(gamma**i for i in range(1,n))*.7*math.log(2)
                exact=30*gamma**(n-1)-2.+entropy
                bound=soft_upper_bound(.7,gamma,n,[-1],[1],.4)
                self.assertLessEqual(exact,bound+1e-9)

    def test_direct_action_volume_and_invalid_inputs(self):
        low=[0]+[-1]*6;high=[1]*7
        self.assertAlmostEqual(soft_upper_bound(1.,1.,2,low,high),30+6*math.log(2))
        for n in [0,1.5,float('nan')]:
            with self.assertRaises(ValueError):soft_upper_bound(1.,.99,n,low,high)

    def test_reward_telescoping_and_positive_cost_rejection(self):
        rows=[];phi=[.2,.8,.4,0.];gamma=.9995
        names=('occupancy','time','comfort_torque','contact_force','torque_slew','penetration','peak_torque','failure_tail')
        for i in range(3):
            terms={k:0. for k in names};terms.update(time=-.1,current_potential=phi[i],next_potential=phi[i+1],
                progress=5*(gamma*phi[i+1]-phi[i]),terminal=25. if i==2 else 0.,completion_efficiency=2. if i==2 else 0.)
            reward=sum(terms[k] for k in names)+terms['progress']+terms['terminal']+terms['completion_efficiency']
            rows.append(dict(done=i==2,reward_terms=terms,reward=reward))
        result=audit_episode(rows,gamma,5.)
        self.assertAlmostEqual(result['discounted_shaping'],-1.)
        self.assertLess(result['discounted_return'],result['discounted_reward_upper_bound'])
        rows[0]['reward_terms']['time']=.1
        with self.assertRaisesRegex(AssertionError,'Positive running cost'):audit_episode(rows,gamma,5.)


if __name__=='__main__':unittest.main()
