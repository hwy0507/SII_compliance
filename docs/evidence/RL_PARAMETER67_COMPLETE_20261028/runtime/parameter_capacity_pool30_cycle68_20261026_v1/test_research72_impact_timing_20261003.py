import unittest
import numpy as np
from research72_impact_timing_20261003 import timing


class ImpactTimingTests(unittest.TestCase):
    def test_short_contact_finishes_before_actor_clock(self):
        time = np.arange(1, 1001)*.00005
        force = np.zeros(len(time)); force[100:104] = [1, 10, 5, 1]
        row = timing(time, np.full(len(time), .00005), force, [0, .04], 0, .05)
        self.assertTrue(row['window_peak_before_next_actor_update'])
        self.assertTrue(row['first_bout_ended_before_next_actor_update'])
        self.assertAlmostEqual(row['first_bout_duration_ms'], .2)
        self.assertAlmostEqual(row['next_actor_update_s'], .04)

    def test_later_larger_reimpact_is_separate_from_first_bout(self):
        time = np.arange(1, 1001)*.00005
        force = np.zeros(len(time)); force[100:104] = 10; force[900:904] = 100
        row = timing(time, np.full(len(time), .00005), force, [0, .04], 0, .05)
        self.assertTrue(row['first_bout_peak_before_next_actor_update'])
        self.assertFalse(row['window_peak_before_next_actor_update'])
        self.assertEqual(row['window_peak_force_n'], 100)

    def test_coincident_and_unobserved_update_are_not_preupdate_claims(self):
        row = timing([.01, .02, .03], [.01]*3, [0, 5, 0], [0, .02, .04], 0, .04)
        self.assertFalse(row['window_peak_before_next_actor_update'])
        row = timing([.01, .02, .03], [.01]*3, [0, 5, 0], [0, .01], 0, .04)
        self.assertIsNone(row['window_peak_before_next_actor_update'])

    def test_absent_contact_is_na(self):
        row = timing([.01, .02], [.01]*2, [0, 0], [0, .04], 0, .04)
        self.assertFalse(row['exposed'])
        self.assertIsNone(row['window_peak_before_next_actor_update'])


if __name__ == '__main__':
    unittest.main()
