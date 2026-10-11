"""Continuation stopping criteria must not certify unusable or unsafe policies."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from launch_rl_convergence_20261010 import decision, reuse_development


def row(limit, task=0, strict=0):
    return dict(steps=limit-1000,scheduled_limit=limit,completed=8,task=task,strict=strict)


class ConvergenceDecisions(unittest.TestCase):
    def test_reuse_cannot_substitute_another_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            reg={'parents':{'job':{'segment':str(root/'expected')}},
                 'reuse_development':{'job':{'segment':str(root/'other')}}}
            with patch('launch_rl_convergence_20261010.audit_segment') as audit:
                with self.assertRaises(AssertionError):reuse_development(root,root,reg,'job')
                audit.assert_not_called()

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
