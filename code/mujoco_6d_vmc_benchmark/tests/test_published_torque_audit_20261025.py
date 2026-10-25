from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'scripts')]
from audit_published_episode_20261025 import Recorder
from replay_published_torque_audit_20261025 import replay_arrays
from wbc_velocity_residual_core import VelocityResidualSafetyConfig, safe_velocity_tracking_torque


class TorqueAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.recorder = Recorder(Path(self.tmp.name))
        self.config = VelocityResidualSafetyConfig()
        limits = np.array([87.]*4+[12.]*3)
        env = SimpleNamespace(execution_mode='twist', safety_config=self.config,
            previous_torque=np.zeros(7), torque_limits=limits, data=SimpleNamespace(time=0.))
        backend = SimpleNamespace(safe_velocity_tracking_torque=safe_velocity_tracking_torque)
        self.recorder.bind_torque(env, backend)
        # Native impedance captures this function after instrumentation.
        captured_projection = backend.safe_velocity_tracking_torque
        for i, command in enumerate([np.ones(7)*10, -np.ones(7)*10, np.zeros(7)]):
            env.data.time = i*.004
            inputs = (np.ones(7), np.zeros(7), command, env.previous_torque, .004, self.config)
            plain = safe_velocity_tracking_torque(*inputs, torque_limits=limits)
            observed = captured_projection(*inputs, torque_limits=limits)
            np.testing.assert_array_equal(observed[0], plain[0])
            self.assertEqual(observed[1], plain[1])
            env.previous_torque = observed[0].copy()
        self.arrays = {key: np.asarray([row[key] for row in self.recorder.torque_rows])
                       for key in self.recorder.torque_rows[0]}
        self.physical = np.zeros((240, 11))
        self.physical[:, 0] = .00005
        self.physical[:, 1:8] = np.repeat(self.arrays['applied'], 80, axis=0)
        self.physical[:, 10] = (self.arrays['time'][:, None]+np.arange(1, 81)*.00005).ravel()

    def replay(self):
        return replay_arrays(self.recorder.torque_metadata, self.arrays, self.physical,
            safe_velocity_tracking_torque, VelocityResidualSafetyConfig)

    def test_transparent_projection_recurrence_and_physical_linkage(self):
        result = self.replay()
        self.assertTrue(result['actuator_torque_linkage_exact'])
        self.assertGreater(result['scaled_projection_calls'], 0)

    def test_small_command_output_change_rejected(self):
        self.arrays['applied'][1, 0] += 1e-12
        with self.assertRaisesRegex(ValueError, 'Torque replay mismatch'):
            self.replay()

    def test_previous_output_recurrence_change_rejected(self):
        self.arrays['previous'][1, 0] += 1e-12
        with self.assertRaisesRegex(ValueError, 'Torque recurrence mismatch'):
            self.replay()

    def test_physical_actuator_change_rejected(self):
        self.physical[80, 1] += 1e-12
        with self.assertRaisesRegex(ValueError, 'Actual actuator torques differ'):
            self.replay()

    def test_physical_clock_change_rejected(self):
        self.physical[80, 10] += 1e-7
        with self.assertRaisesRegex(ValueError, 'clock alignment failed'):
            self.replay()

    def test_changed_actuator_limit_rejected(self):
        self.arrays['limits'][0, 0] += 1.
        with self.assertRaisesRegex(ValueError, 'Torque limits differ'):
            self.replay()


if __name__ == '__main__':
    unittest.main()
