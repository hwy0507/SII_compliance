"""Check progress/feedforward consistency and preserve terminal task gates."""
import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from continuous_old_office_reference_20261013 import ContinuousCarryReference


class ContinuousTest(unittest.TestCase):
    def test_blocked_pose_bounds_reference_and_stops_feedforward(self):
        ref = ContinuousCarryReference(np.array([.54,-.2,.6]), [7,8], [7,8])
        ref.index=4; q=np.zeros(9); zero=np.zeros(6)
        pos=ref.original_goals[3].copy()
        for _ in range(200):
            previous=ref.goals[4].copy()
            ref.update(q,q,pos,ref.rotation,zero,zero)
            np.testing.assert_allclose(ref.sample()[2],(ref.goals[4]-previous)/.04,atol=1e-12)
        self.assertAlmostEqual(ref.arc,.012)
        np.testing.assert_allclose(ref.sample()[2],0,atol=1e-12)
        self.assertEqual(ref.index,4)

    def test_terminal_dwell_and_release_gate(self):
        ref = ContinuousCarryReference(np.array([.54,-.2,.6]), [7,8], [7,8])
        ref.index=4; q=np.zeros(9); q[7:]=.02; zero=np.zeros(6)
        for _ in range(1000):
            if ref.arc==ref.length:break
            ref.update(q,q*0,ref.goals[4].copy(),ref.rotation,zero,zero)
        self.assertEqual(ref.arc,ref.length)
        np.testing.assert_array_equal(ref.goals[4],ref.original_goals[4])
        for _ in range(4):self.assertFalse(ref.update(q,q*0,ref.goals[4],ref.rotation,zero,zero))
        self.assertTrue(ref.update(q,q*0,ref.goals[4],ref.rotation,zero,zero))
        for _ in range(20):ref.update(q,q*0,ref.goals[5],ref.rotation,zero,zero)
        self.assertEqual(ref.index,5)
        np.testing.assert_array_equal(ref.sample()[2],np.zeros(3))


if __name__=='__main__':unittest.main()
