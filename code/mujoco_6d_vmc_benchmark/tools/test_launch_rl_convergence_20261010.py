"""Continuation stopping criteria must not certify unusable or unsafe policies."""
import unittest
from launch_rl_convergence_20261010 import decision


def row(limit, task=0, strict=0):
    return dict(steps=limit-1000,scheduled_limit=limit,completed=8,task=task,strict=strict)


class ConvergenceDecisions(unittest.TestCase):
    def test_three_failed_nodes_request_revision_not_convergence(self):
        r=decision([row(s) for s in (110000,165000,220000)])
        self.assertTrue(r['stop_failed_plateau'])
        self.assertFalse(r['converged'])
        self.assertFalse(r['candidate_usable_and_stable'])

    def test_one_failed_node_still_allows_training(self):
        self.assertFalse(decision([row(110000)])['stop_failed_plateau'])

    def test_partial_matrix_is_rejected(self):
        r=row(110000);r['completed']=7
        with self.assertRaises(AssertionError):decision([r])

    def test_unsafe_success_does_not_qualify(self):
        r=decision([row(s,8,0) for s in (110000,165000,220000)])
        self.assertFalse(r['candidate_usable_and_stable'])
        self.assertFalse(r['converged'])

    def test_stable_success_needs_independent_seeds(self):
        r=decision([row(s,8,7) for s in (110000,165000,220000)])
        self.assertTrue(r['candidate_usable_and_stable'])
        self.assertFalse(r['converged'])
        self.assertFalse(r['final_comparison_authorized'])


if __name__=='__main__':unittest.main()
