"""Small fake reward state machine checks the audit's boundaries, not physics."""
from types import SimpleNamespace
import unittest
import numpy as np
from research72_reward_replay_audit_20261004 import replay_episode


class ToyReward:
    def __init__(self, config): self.previous=0.; self.elapsed=0.
    def __call__(self, interval, action, **kw):
        self.elapsed += interval.elapsed_s
        terms = dict(task=20. if kw['success'] else -20. if kw['failure'] else 0.,
            progress=(0. if kw['terminated'] else kw['next_potential'])-kw['current_potential'],
            error=-interval.error_cost, peak_torque=0., time=-interval.elapsed_s,
            smooth=-(action[0]-self.previous)**2, failure_continuation=0.)
        self.previous=action[0]; reward=sum(terms.values())
        terms.update(terminated=kw['terminated'],success=kw['success'],failure=kw['failure'],
            effective_next_potential=0. if kw['terminated'] else kw['next_potential'])
        return reward,terms


class RewardReplayTests(unittest.TestCase):
    def fixture(self, success=False):
        module=SimpleNamespace(OfficeReward=ToyReward,RewardConfig=lambda **kw:kw,IntervalMetrics=lambda **kw:SimpleNamespace(**kw))
        intervals=[None]+[dict(elapsed_s=.04,error_integral=0.,bounded_error_integral=0.,
            peak_torque_ratio=.1,peak_torque_nm_per_joint=[1.]*7,max_position_error_m=0.,
            substeps=800,executed_action=[x]*7,potential=phi) for x,phi in ((.2,.3),(.4,.6),(.1,.7))]
        # Deliberately inconsistent first reward: missing initial potential is
        # excluded, but the first action MUST initialize later smoothing state.
        expected=np.array([999., .6-.3-.04-.2**2,
            (20. if success else -20.)-.6-.04-.3**2],np.float32)
        return module,dict(horizon_s=55.,error_scale_m=.12),intervals,expected,success

    def test_first_unknown_excluded_but_state_and_failure_checked(self):
        result=replay_episode(*self.fixture())
        self.assertEqual(result['checked_rewards'],2)
        self.assertEqual(result['excluded_first_rewards'],1)
        self.assertTrue(result['terminal']['failure'])

    def test_terminal_success_checked(self):
        result=replay_episode(*self.fixture(True))
        self.assertEqual(result['terminal']['task'],20.)
        self.assertTrue(result['terminal']['success'])

    def test_changed_later_reward_rejected(self):
        args=list(self.fixture());args[3][1]+=.01
        with self.assertRaises(AssertionError): replay_episode(*args)

    def test_missing_interval_rejected(self):
        args=list(self.fixture());args[2].pop()
        with self.assertRaises(AssertionError): replay_episode(*args)


if __name__=='__main__': unittest.main()
