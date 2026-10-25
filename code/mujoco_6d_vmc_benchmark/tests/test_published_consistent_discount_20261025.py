from pathlib import Path
import copy
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from probe_published_consistent_discount_20261025 import discount_rewards


def episode():
    phi=[.2,.5,.8,1.]
    result=[]
    for i in range(3):
        done=i==2
        terms=dict(occupancy=-.1,time=-.02,comfort_torque=0.,contact_force=0.,torque_slew=0.,
            penetration=0.,peak_torque=0.,failure_tail=0.,terminal=25. if done else 0.,
            completion_efficiency=3. if done else 0.,current_potential=phi[i],next_potential=phi[i+1],
            progress=5*(.9995*(0 if done else phi[i+1])-phi[i]))
        reward=sum(terms[k] for k in ('occupancy','time','comfort_torque','contact_force','torque_slew',
            'penetration','peak_torque','failure_tail','terminal','completion_efficiency','progress'))
        terms['final_reward']=reward
        result.append(dict(done=done,reward=reward,reward_terms=terms))
    return result


class DiscountTests(unittest.TestCase):
    def test_consistent_pbrs_telescopes_and_preserves_terminal_reward(self):
        rows=episode();original=copy.deepcopy(rows)
        actual=discount_rewards(rows,.99,horizon=3)
        expected=np.array([r['reward']+5*(.99-.9995)*(0 if r['done'] else r['reward_terms']['next_potential']) for r in rows],dtype=np.float32)
        np.testing.assert_array_equal(actual,expected)
        self.assertEqual(rows,original)
        self.assertEqual(actual[-1],np.float32(rows[-1]['reward']))
        base=np.array([-.12,-.12,27.88])
        self.assertAlmostEqual(float(np.array([1,.99,.99**2])@(actual-base)),-1.,places=5)
        np.testing.assert_array_equal(discount_rewards(rows,.9995,horizon=3),np.array([r['reward'] for r in rows],dtype=np.float32))

    def test_reject_incomplete_and_early_abort_and_invalid_gamma(self):
        rows=episode()
        with self.assertRaises(ValueError):discount_rewards(rows,.99)
        rows[-1]['reward_terms']['failure_tail']=-1.
        with self.assertRaises(ValueError):discount_rewards(rows,.99,horizon=3)
        for gamma in [0.,1.,float('nan')]:
            with self.assertRaises(ValueError):discount_rewards(episode(),gamma,horizon=3)


if __name__=='__main__':unittest.main()
