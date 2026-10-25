from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from analyze_published_contact_tradeoff_20261025 import contact_summary


class ContactAttributionTests(unittest.TestCase):
    def test_weighted_contact_overlap_and_dominant_partition(self):
        torque = np.zeros((4, 7))
        torque[0, 0] = 100.  # No contact: excluded despite large torque.
        torque[1, 0] = -1.  # Equal threshold: compliant.
        torque[2, :2] = [2., -3.]
        torque[3, 0] = 2.
        result = contact_summary(np.array([9., 1., 2., 3.]), torque,
                                 np.array([.05, 1., 1., 1.]), np.ones(7))
        self.assertEqual(result['contact_s'], 6.)
        self.assertEqual(result['compliance_ratio'], 1/6)
        self.assertEqual(result['per_joint_exceed_s'][:2], [5., 2.])
        self.assertEqual(result['dominant_joint_violating_s'][:2], [3., 2.])
        self.assertAlmostEqual(result['bounded_torque_cost_integral_s'], 2*2/3+3/2)

    def test_no_contact_is_na(self):
        result = contact_summary(np.ones(2), np.ones((2, 7))*99, np.zeros(2), np.ones(7))
        self.assertIsNone(result['compliance_ratio'])
        self.assertIsNone(result['contact_peak_abs_torque_nm'])
        self.assertEqual(result['per_joint_exceed_fraction'], [None]*7)
        self.assertEqual(result['bounded_torque_cost_integral_s'], 0.)

    def test_invalid_measurements_rejected(self):
        for dt, force in [(np.array([0.]), np.ones(1)), (np.ones(1), np.array([np.nan])),
                          (np.ones(1), np.array([-1.]))]:
            with self.assertRaises(ValueError):
                contact_summary(dt, np.zeros((1, 7)), force, np.ones(7))


if __name__ == '__main__':
    unittest.main()
