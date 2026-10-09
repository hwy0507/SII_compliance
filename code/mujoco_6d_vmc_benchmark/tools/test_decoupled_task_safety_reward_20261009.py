import unittest
from audit_decoupled_task_safety_reward_20261009 import safety_potential,terminal_task_adjustment


class RewardTests(unittest.TestCase):
    def test_unchanged_safety_boundary_and_monotonic_cost(self):
        self.assertEqual(safety_potential(.0002),0.)
        values=[safety_potential(v) for v in [0.,.0001,.0002,.00021,.0004,.002,1.]]
        self.assertEqual(values,sorted(values))
        self.assertLess(values[-1],1.)

    def test_only_task_pass_strict_fail_changes_terminal(self):
        self.assertEqual(terminal_task_adjustment(False,False),0.)
        self.assertEqual(terminal_task_adjustment(True,True),0.)
        self.assertEqual(terminal_task_adjustment(True,False),40.)
        with self.assertRaises(AssertionError):terminal_task_adjustment(False,True)

    def test_repeated_contact_cannot_repeat_peak_penalty(self):
        peak=0.;total=0.
        for p in [.0001,.0003,.00015,.0003,.0004,.00035]:
            new=max(peak,p);total+=safety_potential(new)-safety_potential(peak);peak=new
        self.assertAlmostEqual(total,safety_potential(.0004))


if __name__=='__main__':unittest.main()
