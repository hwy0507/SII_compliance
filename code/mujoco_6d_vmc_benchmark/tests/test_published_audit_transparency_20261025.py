"""Do not let the task's NA sentinel hide nonfinite physical telemetry."""
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from compare_published_audit_trajectories_20261025 import compare


class TransparencyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.left, self.right = root/'original/case', root/'audited/case'
        for folder in (self.left, self.right):
            (folder/'rollout_metrics').mkdir(parents=True)
            (folder.parent/'checkpoint_frozen.pt').write_bytes(b'same snapshot')
            for name in ('rollout.mjb', 'actor_intervals.jsonl', 'TERMINAL.json'):
                (folder/name).write_bytes(b'same evidence')
            np.savez(folder/'rollout.npz', qpos=np.zeros((2, 7)), task_carry_load=[np.nan, 1.])
            np.savez(folder/'rollout_metrics/substep_metrics.npz', qfrc_actuator=np.ones((2, 7)))
            np.savez(folder/'rollout_ball_detail.npz', time=np.array([.04, .08]))

    def test_identical_unavailable_carry_load_is_allowed(self):
        self.assertTrue(compare(self.left, self.right)['passed'])

    def test_identical_nan_in_physical_state_is_rejected(self):
        for folder in (self.left, self.right):
            q = np.zeros((2, 7)); q[0, 0] = np.nan
            np.savez(folder/'rollout.npz', qpos=q, task_carry_load=[np.nan, 1.])
        self.assertFalse(compare(self.left, self.right)['passed'])

    def test_small_physical_change_is_not_rounded_away(self):
        torque = np.ones((2, 7)); torque[0, 0] += 1e-10
        np.savez(self.right/'rollout_metrics/substep_metrics.npz', qfrc_actuator=torque)
        self.assertFalse(compare(self.left, self.right)['passed'])


if __name__ == '__main__':
    unittest.main()
