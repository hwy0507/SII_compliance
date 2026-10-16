import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from goal_tracking_reward_20261016 import (CONFIG, validate_guidance, check_reward_resume,
                                          tracking_terms, discounted_cost_tail)


class TrackingRewardTests(unittest.TestCase):
    def test_dense_cost_prefers_lower_tracking_error(self):
        kw = dict(interval_s=.04, elapsed_s=.04, terminated=False, success=False, config=CONFIG)
        perfect = sum(tracking_terms(0., **kw).values())
        poor = sum(tracking_terms(.04/55, **kw).values())
        self.assertEqual(perfect, 0.)
        self.assertAlmostEqual(poor, -4*.04/55)
        self.assertGreater(perfect, poor)

    def test_tail_matches_explicit_discounted_full_and_partial_steps(self):
        for gamma in (1., .9995, .9):
            for remaining in (0., .02, .04, .1, 54.96):
                n = int(math.floor(remaining/.04+1e-9))
                partial = max(0., remaining-n*.04)
                expected = 4/55*(sum(gamma**k*.04 for k in range(1, n+1))+gamma**(n+1)*partial)
                actual = discounted_cost_tail(remaining, weight=4, horizon_s=55, control_dt_s=.04, gamma=gamma)
                self.assertAlmostEqual(actual, expected, places=11)

    def test_failure_cannot_avoid_remaining_worst_case_cost(self):
        gamma = CONFIG['gamma']; cost = .04/55
        early = tracking_terms(cost, .04, .04, terminated=True, success=False, config=CONFIG)
        full = -4*cost*sum(gamma**i for i in range(1375))
        self.assertAlmostEqual(sum(early.values()), full, places=10)
        final = tracking_terms(cost, .04, 55., terminated=True, success=False, config=CONFIG)
        self.assertEqual(final['tracking_failure_continuation'], 0.)
        successful = tracking_terms(cost, .04, .04, terminated=True, success=True, config=CONFIG)
        self.assertEqual(successful['tracking_failure_continuation'], 0.)

    def test_registration_and_resume_reject_objective_mixing(self):
        args = dict(controller=None, reward='office_task', reward_variant='task_safety')
        self.assertIsNone(validate_guidance({}, **args))
        self.assertEqual(validate_guidance({'tracking_guidance': CONFIG}, **args), CONFIG)
        for mutation in (dict(args, controller='vmc'), dict(args, reward='metric')):
            with self.assertRaises(ValueError): validate_guidance({'tracking_guidance': CONFIG}, **mutation)
        with self.assertRaises(ValueError): validate_guidance({'tracking_guidance': dict(CONFIG, weight=8)}, **args)
        check_reward_resume({}, {})
        check_reward_resume({'tracking_guidance': CONFIG}, {'tracking_guidance': CONFIG})
        with self.assertRaises(ValueError): check_reward_resume({}, {'tracking_guidance': CONFIG})
        with self.assertRaises(ValueError): check_reward_resume({'tracking_guidance': CONFIG}, {})

    def test_invalid_physics_telemetry_fails_closed(self):
        for cost, interval, elapsed in ((float('nan'),.04,.04),(-.01,.04,.04),(.1,.04,.04),(0,.05,.05),(0,.04,56)):
            with self.assertRaises(ValueError):
                tracking_terms(cost, interval, elapsed, terminated=False, success=False, config=CONFIG)


if __name__ == '__main__': unittest.main()
