"""Safety and no-contact-input checks for the optional common servo probe."""
import unittest
import numpy as np
from run_payload_friction_probe_20261013 import friction_feedforward
from wbc_velocity_residual_core import safe_velocity_tracking_torque,VelocityResidualSafetyConfig


class FrictionProbeTest(unittest.TestCase):
    def test_zero_and_odd_bounded_model_correction(self):
        friction=np.array([1.137]*4+[.763,.44,.248]);damping=np.full(7,.21)
        zero=np.zeros(7)
        np.testing.assert_array_equal(friction_feedforward(zero,zero,friction,damping),zero)
        velocity=np.linspace(-.04,.04,7)
        a=friction_feedforward(velocity,velocity,friction,damping)
        np.testing.assert_array_equal(friction_feedforward(-velocity,-velocity,friction,damping),-a)
        self.assertTrue(np.all(abs(a-damping*velocity)<=friction))

    def test_correction_enters_existing_torque_and_slew_limits(self):
        cfg=VelocityResidualSafetyConfig();limits=np.array([87.]*4+[12.]*3)
        bias=limits-.1;command=np.full(7,1.25);measured=np.zeros(7);previous=np.zeros(7)
        correction=friction_feedforward(command,measured,np.ones(7),np.full(7,.21))
        torque,_=safe_velocity_tracking_torque(bias+correction,measured,command,previous,.004,cfg,limits)
        self.assertTrue(np.all(abs(torque)<=limits))
        self.assertTrue(np.all(abs(torque-previous)<=np.array(cfg.maximum_torque_rate_nmps)*.004))


if __name__=='__main__':unittest.main()
