import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from servo_action_bridge_20261013 import ServoActionBridge
from wbc_velocity_residual_core import FilteredVelocityResidualAction
from payload_clearance_reference_20261013 import PayloadClearanceReference
from old_office_waypoint_reference_20261013 import LocalCarryReference


class BridgeTest(unittest.TestCase):
    def test_direct_esn_feedback_scale_is_not_neutral_composition_scale(self):
        action=FilteredVelocityResidualAction(1.,np.zeros(6),np.zeros(7),False,False)
        env=SimpleNamespace(applied_action=action,_physics_step=lambda t:None,
            observation_mode='direct_esn',execution_mode='twist',_last_policy_wbc_scale=.84)
        bridge=ServoActionBridge(env)
        for k in range(10):
            bridge(k*.004)
            self.assertEqual(env.applied_action.wbc_scale,1.)
            self.assertAlmostEqual(env.current_predictive_wbc_feedback_scale,1.-.16*(k+1)/10)
        self.assertEqual(bridge.rows[-1]['wbc_scale'],.84)
        env._last_policy_wbc_scale=1.
        for k in range(10):bridge(.04+k*.004)
        self.assertEqual(env.current_predictive_wbc_feedback_scale,1.)

    def test_polyline_progress_and_original_release_gate(self):
        ref=PayloadClearanceReference.__new__(PayloadClearanceReference)
        LocalCarryReference.__init__(ref,np.array([.54,-.19,.6]),[7,8],[7,8],source=[.54,-.19,.425])
        ref.carry_route=np.array([ref.original_goals[3],[.54,.1,.66],ref.original_goals[4]])
        ref.cumulative=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(ref.carry_route,axis=0),axis=1))]
        ref.length=float(ref.cumulative[-1]);ref.arc=0.;ref.reference_velocity=np.zeros(3);ref.progress_records=[]
        ref.index=4;q=np.zeros(9);q[7:]=.02;zero=np.zeros(6)
        for _ in range(30):ref.update(q,q*0,ref.carry_route[0],ref.rotation,zero,zero)
        self.assertAlmostEqual(ref.arc,.012)
        np.testing.assert_allclose(ref.sample()[2],0,atol=1e-12)
        for _ in range(1000):
            if ref.arc==ref.length:break
            previous=ref.goals[4].copy()
            ref.update(q,q*0,previous,ref.rotation,zero,zero)
            np.testing.assert_allclose(ref.sample()[2],(ref.goals[4]-previous)/.04,atol=1e-12)
            self.assertLessEqual(np.linalg.norm(ref.sample()[2]),.06+1e-12)
        self.assertEqual(ref.arc,ref.length)
        for _ in range(4):self.assertFalse(ref.update(q,q*0,ref.goals[4],ref.rotation,zero,zero))
        self.assertTrue(ref.update(q,q*0,ref.goals[4],ref.rotation,zero,zero))
        for _ in range(20):ref.update(q,q*0,ref.goals[5],ref.rotation,zero,zero)
        self.assertEqual(ref.index,5)

    def test_convex_transition_and_boundary_continuity(self):
        def action(scale,v):return FilteredVelocityResidualAction(scale,np.array(v),np.zeros(7),False,False)
        env=SimpleNamespace(applied_action=action(1.,[0.]*6),_physics_step=lambda t:None)
        bridge=ServoActionBridge(env)
        targets=[action(.96,[.048,0,0,0,0,0]),action(1.,[0.]*6)]
        samples=[]
        for a in targets:
            env.applied_action=a
            for k in range(10):
                bridge(k*.004);samples.append(env.applied_action.cartesian_yield_twist.copy())
            np.testing.assert_array_equal(env.applied_action.cartesian_yield_twist,a.cartesian_yield_twist)
        changes=np.diff(np.vstack([np.zeros(6),samples]),axis=0)
        self.assertLessEqual(float(abs(changes).max()),.0048+1e-12)
        self.assertEqual(len(bridge.rows),20)


if __name__=='__main__':unittest.main()
