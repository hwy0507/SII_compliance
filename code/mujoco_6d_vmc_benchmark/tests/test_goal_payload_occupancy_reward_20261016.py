from pathlib import Path
import math
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from goal_payload_occupancy_reward_20261016 import CONFIG,occupancy_terms,validate_guidance,check_reward_resume


class OccupancyRewardTests(unittest.TestCase):
    def test_stationary_progress_cost_is_dense_bounded_and_monotone(self):
        def total(phi):
            return sum(sum(occupancy_terms(phi,.04,(i+1)*.04,terminated=i==1374,
                success=False,config=CONFIG).values()) for i in range(1375))
        self.assertAlmostEqual(total(0.),-4.)
        self.assertAlmostEqual(total(.5),-2.)
        self.assertAlmostEqual(total(1.),0.)
        self.assertGreater(total(.6),total(.5))
        # Same physical progress has the same cost, independent of which local
        # route target the planner has just selected; no waypoint input exists.
        expected=-4.*(1-.53)*.04/55.
        self.assertAlmostEqual(occupancy_terms(.53,.04,10.,terminated=False,success=False,
            config=CONFIG)['payload_occupancy'],expected)

    def test_failure_tail_matches_explicit_future_worst_case_discount(self):
        for completed in (1,25,1000,1374,1375):
            terms=occupancy_terms(.53,.04,completed*.04,terminated=True,success=False,config=CONFIG)
            expected=sum(CONFIG['gamma']**k*4.*.04/55. for k in range(1,1375-completed+1))
            self.assertAlmostEqual(-terms['payload_occupancy_failure_continuation'],expected,places=11)
        success=occupancy_terms(.8,.04,10.,terminated=True,success=True,config=CONFIG)
        self.assertEqual(success['payload_occupancy_failure_continuation'],0.)

    def test_config_scope_and_reward_history_cannot_change_silently(self):
        job=dict(payload_occupancy_guidance=CONFIG)
        self.assertEqual(validate_guidance(job,controller='impedance',reward='metric',reward_variant='payload_shaping'),CONFIG)
        with self.assertRaises(ValueError):validate_guidance(job,controller=None,reward='office_task',reward_variant='task_safety')
        with self.assertRaises(ValueError):check_reward_resume({},job)
        check_reward_resume(job,dict(job))
        for phi,dt,elapsed in ((math.nan,.04,1.),(-.1,.04,1.),(1.1,.04,1.),(.5,0.,1.),(.5,.05,1.),(.5,.04,56.)):
            with self.assertRaises(ValueError):occupancy_terms(phi,dt,elapsed,terminated=False,success=False,config=CONFIG)
        with self.assertRaises(ValueError):occupancy_terms(.5,.04,1.,terminated=False,success=True,config=CONFIG)


if __name__=='__main__':unittest.main()
