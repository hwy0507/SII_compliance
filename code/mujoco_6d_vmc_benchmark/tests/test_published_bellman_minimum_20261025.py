from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from published_bellman_minimum_20261025 import all_critic_minimum, transform_train_source


class BellmanMinimumTests(unittest.TestCase):
    def test_all_targets_minimum_and_column_shape(self):
        values = torch.tensor([[4., -2.], [3., 9.], [-1., 4.], [7., -8.], [0., 1.]])
        calls = []
        def query(state, action, q_net, target):
            self.assertTrue(target)
            calls.append(q_net)
            return values[q_net, :, None]
        learner = SimpleNamespace(ensemble_size=5, agent=SimpleNamespace(get_q_value=query))
        with torch.no_grad():
            got = all_critic_minimum(learner, torch.zeros(2, 49), torch.zeros(2, 7))
        torch.testing.assert_close(got, torch.tensor([[-1.], [-8.]]), rtol=0, atol=0)
        self.assertEqual(calls, list(range(5)))
        with self.assertRaises(RuntimeError):
            all_critic_minimum(learner, torch.zeros(2, 49), torch.zeros(2, 7))

    def test_flat_q_rejected(self):
        learner = SimpleNamespace(ensemble_size=5,
            agent=SimpleNamespace(get_q_value=lambda **kw: torch.zeros(2)))
        with torch.no_grad(), self.assertRaises(ValueError):
            all_critic_minimum(learner, torch.zeros(2, 49), torch.zeros(2, 7))

    def test_missing_upstream_seams_rejected(self):
        for source in ['', 'class SACEnsemble:\n    def train(self, batch):\n        return batch\n']:
            with self.assertRaises(ValueError):
                transform_train_source(source)


if __name__ == '__main__':
    unittest.main()
