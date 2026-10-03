"""Synthetic checks only; no final condition or policy reads."""
import unittest
import numpy as np
from research72_paired_statistics_20261003 import (
    crossed_difference, success_summary, contact_pair_arrays, recovery_summary)


class StatisticsTests(unittest.TestCase):
    def test_constant_paired_effect_has_exact_interval(self):
        x = np.arange(72).reshape(3,24)
        r = crossed_difference(x+2,x)
        self.assertEqual(r['difference'],2)
        self.assertEqual(r['ci95'],[2,2])
        self.assertEqual(r['paired_conditions'],24)

    def test_deterministic_reference_keeps_single_seed(self):
        r = crossed_difference(np.ones((3,4)),np.zeros((1,4)))
        self.assertEqual(r['right_seed_count'],1)
        self.assertEqual(r['ci95'],[1,1])
        self.assertEqual(r['paired_conditions'],4)

    def test_missing_not_counted_as_completed_failure(self):
        r = success_summary([[1,0,np.nan]])
        self.assertIsNone(r['rate'])
        self.assertEqual(r['planned_rate_bounds'],[1/3,2/3])
        self.assertEqual(r['missing'],1)

    def test_seed_correlation_is_not_flattened(self):
        # All conditions have the same seed effect. Crossed resampling retains
        # the full seed uncertainty rather than shrinking it with 24 repeats.
        x = np.repeat([[-1.],[0.],[1.]],24,axis=1)
        r = crossed_difference(x,np.zeros((1,24)))
        self.assertEqual(r['ci95'],[-1,1])
        self.assertEqual(r,crossed_difference(x,np.zeros((1,24))))

    def test_no_pairs_remain_na(self):
        r = crossed_difference([[np.nan]],[[1.]])
        self.assertIsNone(r['difference']);self.assertIsNone(r['ci95'])
        self.assertEqual(r['valid_bootstrap_replicates'],0)

    def test_no_contact_short_failure_excluded_from_contact_pair(self):
        def row(exposed=True,full=True,success=True,force=8):
            return dict(full_horizon=full,strict_success=success,
                        contact={'rod':dict(exposure=exposed,peak_force_n=force)})
        a = [[row(),row(False,force=0),row(full=False),row(success=False)]]
        b = [[row(force=10)]*4]
        x,y,mask = contact_pair_arrays(a,b,'rod','peak_force_n')
        r = crossed_difference(x,y,eligible=mask)
        self.assertEqual(r['paired_cells'],1);self.assertEqual(r['difference'],-2)
        self.assertTrue(r['outcome_conditioned'])

    def test_recovery_censoring_not_zero(self):
        rows = [dict(recovery={'rod':dict(exposed=True,settled_rejoin_time_s=None,
                 right_censored=True,observation_window_s=.15)})]
        r = recovery_summary(rows,'rod')
        self.assertEqual(r['right_censored'],1)
        self.assertIsNone(r['unconditional_mean_recovery_s'])
        self.assertEqual(r['observed_recovery_times_s'],[])

    def test_failed_first_seed_does_not_erase_deterministic_control(self):
        def row(success,force):
            return dict(full_horizon=True,strict_success=success,
                        contact={'rod':dict(exposure=True,peak_force_n=force)})
        a = [[row(False,5)],[row(True,7)],[row(True,9)]]
        b = [[row(True,10)]]
        x,y,mask = contact_pair_arrays(a,b,'rod','peak_force_n')
        r = crossed_difference(x,y,eligible=mask)
        self.assertEqual(r['paired_cells'],2)
        self.assertEqual(r['difference'],-2)
        self.assertEqual(r['right_seed_count'],1)


if __name__ == '__main__':
    unittest.main()
