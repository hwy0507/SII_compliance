from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'scripts')]
from audit_published_episode_20261025 import Recorder
from replay_published_filter_audit_20261025 import replay_arrays
from wbc_velocity_residual_core import VelocityResidualActionFilter, VelocityResidualSafetyConfig


class FilterAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.recorder = Recorder(Path(self.temporary.name))
        env = SimpleNamespace(action_filter=VelocityResidualActionFilter(),
            observation_mode='direct_esn', execution_mode='twist')
        self.recorder.bind_filter(env)
        self.actions = np.array([[1., 1., -1., 0., 1., -1., 0.],
            [0., -1., 1., 0., -1., 1., 0.], [0., 0., 0., 0., 0., 0., 0.]])
        control = VelocityResidualActionFilter()
        for action in self.actions:
            recorded, plain = env.action_filter.filter(action, .04), control.filter(action, .04)
            np.testing.assert_array_equal(recorded.cartesian_yield_twist, plain.cartesian_yield_twist)
            self.assertEqual(recorded.wbc_scale, plain.wbc_scale)
        self.arrays = {key: np.asarray([row[key] for row in self.recorder.filter_rows])
            for key in self.recorder.filter_rows[0]}

    def replay(self):
        return replay_arrays(self.recorder.filter_metadata, self.arrays, self.actions,
            VelocityResidualActionFilter, VelocityResidualSafetyConfig)

    def test_observer_is_transparent_and_stateful_replay_is_exact(self):
        self.assertEqual(self.replay()['common_filter_replay_max_abs'], 0.)
        self.assertTrue(self.arrays['slew_limited'].any())

    def test_small_filtered_command_change_is_rejected(self):
        self.arrays['yield_twist'][1, 0] += 1e-12
        with self.assertRaisesRegex(ValueError, 'Filter replay differs'):
            self.replay()

    def test_actor_journal_input_mismatch_is_rejected(self):
        self.actions[0, 1] -= 1e-12
        with self.assertRaisesRegex(ValueError, 'Actor journal'):
            self.replay()


if __name__ == '__main__':
    unittest.main()
