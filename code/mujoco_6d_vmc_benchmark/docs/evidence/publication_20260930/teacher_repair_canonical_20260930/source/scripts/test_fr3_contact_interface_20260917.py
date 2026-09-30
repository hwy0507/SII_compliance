"""Portable numerical checks; these do not certify robot safety."""
import unittest
import numpy as np
from fr3_contact_interface_20260917 import SampledMomentumObserver,SensorConfig,ActionBoundary
from contact_transfer_student_20260916 import TransferStudent


class InterfaceTests(unittest.TestCase):
    def test_known_external_load_and_sample_count(self):
        observer=SampledMomentumObserver(np.zeros(7),np.zeros(7),SensorConfig(
            velocity_noise_std=0,torque_noise_std=0,torque_bias_std=0))
        m=np.eye(7)*2;ext=np.arange(1,8)*.2
        for step in range(10000):
            t=(step+1)*.0001
            result=observer.update(ext*t/2,m,np.zeros(7),np.zeros(7),np.zeros(7),.0001)
        self.assertEqual(observer.samples,1000)
        np.testing.assert_allclose(result,ext,atol=1e-10)

    def test_motor_generated_motion_is_not_external_force(self):
        observer=SampledMomentumObserver(np.zeros(7),np.zeros(7),SensorConfig(
            velocity_noise_std=0,torque_noise_std=0,torque_bias_std=0))
        motor=np.arange(1,8)*.2
        for step in range(1000):
            result=observer.update(motor*(step+1)*.001,np.eye(7),np.zeros(7),np.zeros(7),motor,.001)
        np.testing.assert_allclose(result,0,atol=1e-10)

    def test_boundary_stop_latches_and_limits(self):
        boundary=ActionBoundary();previous=np.zeros(3)
        for _ in range(1000):
            result=boundary.step(np.ones(3),np.ones(7),0,.001)
            self.assertLessEqual(np.linalg.norm(result),.120000001)
            self.assertLessEqual(np.linalg.norm(result-previous),.000800001)
            previous=result
        np.testing.assert_array_equal(boundary.step(np.zeros(3),np.zeros(7),.1,.001),0)
        self.assertTrue(boundary.stop_requested)
        np.testing.assert_array_equal(boundary.step(np.ones(3),np.ones(7),0,.001),0)

    def test_reservoir_contraction_for_same_input(self):
        model=TransferStudent('esn',np.zeros(45),np.ones(45),reservoir=32,dt=.01,spectral_bound=.8)
        self.assertLessEqual(np.linalg.norm(model.w,2),.80000001)
        x=np.zeros(45);a=np.zeros(32);b=np.ones(32)
        initial=np.linalg.norm(a-b,ord=np.inf)
        for _ in range(2000):
            a+=model.leak*(np.tanh(model.win@np.r_[1,x]+model.w@a)-a)
            b+=model.leak*(np.tanh(model.win@np.r_[1,x]+model.w@b)-b)
        self.assertLess(np.linalg.norm(a-b),initial*1e-2)
        # Reservoir forgetting is not a proof of closed-loop robot stability.


if __name__=='__main__':unittest.main()
