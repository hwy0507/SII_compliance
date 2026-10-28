"""Arithmetic regression: conditional SPT, independent success denominators."""
import unittest
from run_nonrl_spt_matrix_20261025 import aggregate, render


def row(method, task, strict, time):
    return dict(method=method, task_success=task, strict_success=strict,
                completion_time_s=time, peak_torque_nm=10., comfort=dict(
                    human_contact_duration_s=0., human_comfort_torque_compliance=None,
                    machine_safety_violation=not strict, machine_safety_violation_reasons=[]))


class MetricTests(unittest.TestCase):
    def test_failure_is_excluded_from_spt_not_success_rate(self):
        report=aggregate([row('A',True,True,10),row('A',False,False,None),
                          row('B',True,True,20),row('B',True,False,5)])
        a,b=report['methods']
        self.assertEqual(report['t_ref_s'],10)
        self.assertEqual((a['spt_mean'],b['spt_mean']),(1,.5))
        self.assertEqual((a['task_success_rate'],b['task_success_rate']),(.5,1))
        self.assertEqual(b['strict_success_rate'],.5)
        self.assertIsNone(b['human_comfort_torque_compliance_contact_time_weighted'])

    def test_empty_success_is_na_and_renders(self):
        report=aggregate([row('A',True,False,10),row('A',False,True,None)])
        self.assertIsNone(report['t_ref_s'])
        self.assertIsNone(report['methods'][0]['spt_mean'])
        self.assertIn('NA',render(report))

    def test_missing_completion_is_disclosed(self):
        report=aggregate([row('A',True,True,None)])
        self.assertEqual(report['methods'][0]['spt_missing_time_episodes'],1)
        self.assertIsNone(report['methods'][0]['spt_mean'])


if __name__=='__main__': unittest.main()
