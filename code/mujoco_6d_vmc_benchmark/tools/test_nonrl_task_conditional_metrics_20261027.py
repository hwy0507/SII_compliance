import unittest
from nonrl_task_conditional_metrics_20261027 import aggregate


def row(method, condition, task, strict, time):
    return dict(method=method, condition=condition, task_success=task,
        strict_success=strict, completion_time_s=time, peak_torque_nm=20., spt=.123,
        comfort=dict(human_contact_duration_s=0., human_comfort_torque_compliance=None,
                     machine_safety_violation=not strict))


class MetricsTest(unittest.TestCase):
    def test_task_only_denominator_and_common_reference(self):
        rows = [row('esn_s1','a',True,False,10.), row('esn_s1','b',True,True,20.),
                row('esn_s1','c',False,False,None), row('mlp_s1','a',False,False,None)]
        r = aggregate(rows)
        self.assertEqual(r['t_ref_s'],10.)
        self.assertEqual(r['methods'][0]['spt_task_conditional_mean'],.75)
        self.assertEqual(r['methods'][0]['spt_task_conditional_n'],2)
        self.assertIsNone(r['methods'][1]['spt_task_conditional_mean'])
        self.assertIsNone(r['rows'][2]['spt_task_conditional'])
        self.assertEqual(rows[0]['spt'],.123)  # caller/historical rows unchanged
        self.assertEqual(r['rows'][0]['legacy_spt'],.123)

    def test_no_success_is_na(self):
        r = aggregate([row('mlp_s1','a',False,False,None)])
        self.assertIsNone(r['t_ref_s'])
        self.assertIsNone(r['methods'][0]['spt_task_conditional_mean'])

    def test_missing_invalid_time_rejected(self):
        for t in (None,0.,float('nan'),-1.):
            with self.assertRaises(ValueError): aggregate([row('esn_s1','a',True,True,t)])

    def test_duplicate_rejected(self):
        r = row('esn_s1','a',True,True,10.)
        with self.assertRaises(ValueError): aggregate([r,r])


if __name__ == '__main__': unittest.main()
