"""Prevent blocked-reference feedforward and sign errors in motor compensation."""
import unittest
import numpy as np
from measured_friction_servo_20261013 import measured_friction


class FrictionTest(unittest.TestCase):
    def test_stationary_motor_has_no_feedforward(self):
        np.testing.assert_array_equal(measured_friction(np.zeros(7), np.ones(7), np.ones(7)), np.zeros(7))

    def test_opposes_internal_drag_without_exceeding_model(self):
        v = np.array([-.4, -.02, -.005, 0, .005, .02, .4])
        f = np.array([1.137]*4+[.763,.44,.248]); b = np.full(7, .21)
        value = measured_friction(v, f, b)
        np.testing.assert_array_equal(measured_friction(-v, f, b), -value)
        self.assertTrue(np.all(value*v >= 0))
        self.assertTrue(np.all(abs(value-b*v) <= f))


if __name__ == '__main__':
    unittest.main()
