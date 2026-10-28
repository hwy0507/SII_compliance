"""Protect budgets and completed failures during a resource-only handoff."""
import unittest
from parallel_classical_search_20261010 import may_dispatch,pending_jobs,GIB


class DispatchTest(unittest.TestCase):
    def test_memory_and_concurrency_admission(self):
        self.assertFalse(may_dispatch(6*GIB,0))
        self.assertTrue(may_dispatch(7*GIB,0))
        self.assertFalse(may_dispatch(3*GIB,1))
        self.assertTrue(may_dispatch(4*GIB,1))
        self.assertFalse(may_dispatch(100*GIB,2))

    def test_failed_task_and_inflight_are_never_repeated(self):
        jobs=[dict(name=n) for n in ('a','b','c')]
        done=[dict(job=jobs[0],status='complete',audit=dict(task_success=False))]
        self.assertEqual(pending_jobs(jobs,done,['b']),[jobs[2]])
        self.assertEqual(pending_jobs(jobs,done,[]),jobs[1:])

    def test_duplicate_completion_cannot_consume_budget(self):
        row=dict(job=dict(name='a'))
        with self.assertRaises(ValueError):pending_jobs([row['job']],[row,row],[])


if __name__=='__main__':unittest.main()
