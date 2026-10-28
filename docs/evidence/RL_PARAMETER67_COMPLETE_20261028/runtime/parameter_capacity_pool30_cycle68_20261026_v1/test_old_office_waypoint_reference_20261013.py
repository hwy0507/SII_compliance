"""Check common-reference progression and preserve the old release gate."""
from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from old_office_waypoint_reference_20261013 import LocalCarryReference
from office_task_v4_20260917 import PickPlaceTask


class ReferenceTest(unittest.TestCase):
    def test_original_lateral_rejoin_rule(self):
        ref=LocalCarryReference(np.array([.54,-.19,.6]),[7,8],[7,8])
        ref.index=4;ref.carry_cursor=1;ref.goals[4]=ref.carry_route[1].copy()
        direction=ref.carry_route[1]-ref.carry_route[0];direction/=np.linalg.norm(direction)
        lateral=np.cross(direction,np.array([1.,0.,0.]));lateral/=np.linalg.norm(lateral)
        q=np.zeros(9);zero=np.zeros(6)
        ref.update(q,q,ref.goals[4]+direction*.002+lateral*.081,ref.rotation,zero,zero)
        self.assertEqual(ref.carry_cursor,1)
        ref.update(q,q,ref.goals[4]+direction*.002+lateral*.04,ref.rotation,zero,zero)
        self.assertEqual(ref.carry_cursor,2)

    def test_route_and_stage_gates(self):
        args=(np.array([.54,-.19,.6]),[7,8],[7,8])
        ref=LocalCarryReference(*args);base=PickPlaceTask(*args)
        self.assertLessEqual(np.max(np.linalg.norm(np.diff(ref.carry_route,axis=0),axis=1)),.010000001)
        np.testing.assert_array_equal(ref.carry_route[-1],base.goals[4])
        for stage in (0,1,2,3,5,6,7):np.testing.assert_array_equal(ref.goals[stage],base.goals[stage])
        q=np.zeros(9);q[7:]=.02;zero=np.zeros(6);rot=ref.rotation.copy();ref.index=4
        # A displaced robot cannot advance the reference merely because time passes.
        for _ in range(20):
            self.assertFalse(ref.update(q,q*0,ref.goals[4]+[.1,0,0],rot,zero,zero))
        self.assertEqual(ref.carry_cursor,0)
        for index in range(len(ref.carry_route)-1):
            self.assertEqual(ref.carry_cursor,index)
            self.assertFalse(ref.update(q,q*0,ref.goals[4].copy(),rot,zero,zero))
            self.assertEqual(ref.index,4)
        for _ in range(4):
            self.assertFalse(ref.update(q,q*0,ref.goals[4].copy(),rot,zero,zero))
        self.assertTrue(ref.update(q,q*0,ref.goals[4].copy(),rot,zero,zero))
        self.assertEqual(ref.index,5)
        # Pose alone must not bypass legacy load-transfer readiness.
        for _ in range(10):ref.update(q,q*0,ref.goals[5].copy(),rot,zero,zero)
        self.assertEqual(ref.index,5)
        wrench=np.array([0.,0.,1.,0.,0.,0.])
        for _ in range(5):ref.update(q,q*0,ref.goals[5].copy(),rot,zero,wrench)
        self.assertEqual(ref.index,6)


if __name__=='__main__':unittest.main()
