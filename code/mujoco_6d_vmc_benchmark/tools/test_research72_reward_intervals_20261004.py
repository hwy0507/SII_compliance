import copy
import unittest
import numpy as np
from research72_reward_intervals_20261004 import check_intervals


class IntervalTests(unittest.TestCase):
    def setUp(self):
        # Two intervals, with a shortened final interval. Expectations are
        # closed-form values rather than calls to the implementation reducer.
        self.raw=dict(time=np.array([.01,.02,.03]),dt=np.full(3,.01),
            error=np.array([[.12,0,0],[.12,0,0],[0,0,0]],dtype=np.float32),
            qfrc_actuator=np.tile([4.,0,0,0,0,0,0],(3,1)).astype(np.float32))
        self.raw['error']=self.raw['error'].astype(float)
        e=float(np.float32(.12));e2=e*e
        first=dict(elapsed_s=.02,error_integral=.02*e2,
            bounded_error_integral=.02*e2/(.12**2+e2),peak_torque_ratio=.5,
            peak_torque_nm_per_joint=[4.,0,0,0,0,0,0],max_position_error_m=e,
            substeps=2,executed_action=[.2,0,0,0,0,0,0])
        last=dict(first,elapsed_s=.01,error_integral=0.,bounded_error_integral=0.,
                  max_position_error_m=0.,substeps=1,executed_action=[.3,0,0,0,0,0,0])
        self.intervals=[None,first,last]
        self.start=np.array([0.,.02]);self.end=np.array([.02,.03])
        self.filtered=np.array([first['executed_action'],last['executed_action']])

    def call(self):
        return check_intervals(self.raw,self.start,self.end,self.filtered,self.intervals,np.full(7,8.))

    def test_reduces_first_and_short_terminal_without_potential(self):
        result=self.call()
        self.assertEqual(result['substeps_checked'],3)
        self.assertEqual(result['intervals_checked'],2)
        self.assertFalse(result['potential_checked'])

    def test_metadata_cannot_repartition_physics(self):
        self.intervals[1]['substeps']=1;self.intervals[2]['substeps']=2
        with self.assertRaises(AssertionError):self.call()

    def test_modified_physical_metric_rejected(self):
        for key in ('error_integral','bounded_error_integral','peak_torque_ratio','elapsed_s'):
            with self.subTest(key=key):
                before=copy.deepcopy(self.intervals)
                self.intervals[1][key]+=.001
                with self.assertRaises(AssertionError):self.call()
                self.intervals=before

    def test_wrong_action_rejected(self):
        self.intervals[-1]['executed_action'][0]=.4
        with self.assertRaises(AssertionError):self.call()

    def test_missing_terminal_samples_rejected(self):
        self.end[-1]=.025
        with self.assertRaises(AssertionError):self.call()

    def test_gapped_action_clock_rejected(self):
        self.start[-1]=.01
        with self.assertRaises(AssertionError):self.call()


if __name__=='__main__':unittest.main()
