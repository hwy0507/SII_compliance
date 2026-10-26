"""Scientific guards for the isolated critic-clock intervention."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

import numpy as np
import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from probe_published_critic_clock_20261026 import known_clock, extend_critic, bellman


class ClockProbeTests(unittest.TestCase):
    def test_clock_never_uses_future_abort_length(self):
        current, nxt = known_clock(np.arange(859))
        self.assertAlmostEqual(float(nxt[-1]), 516/1375, places=7)
        self.assertEqual(float(current[0]), 1.)
        self.assertEqual(float(known_clock(np.array([1374]))[1][0]), 0.)
        for bad in (np.array([-1]), np.array([1375]), np.array([1.5])):
            with self.assertRaises(ValueError):
                known_clock(bad)

    def test_extra_column_preserves_function_and_can_learn(self):
        torch.manual_seed(7)
        original = nn.Sequential(nn.Linear(5, 16), nn.LayerNorm(16), nn.ReLU(), nn.Linear(16, 1))
        before = {k: v.clone() for k, v in original.state_dict().items()}
        net = extend_critic(SimpleNamespace(q_net=original))
        x = torch.randn(32, 5)
        clock = torch.rand(32, 1)
        torch.testing.assert_close(net(torch.cat((x, clock), 1)), original(x))
        net(torch.cat((x, clock), 1)).sum().backward()
        self.assertGreater(float(net[0].weight.grad[:, -1].abs().sum()), 0.)
        for key, value in original.state_dict().items():
            self.assertTrue(torch.equal(value, before[key]))

    def test_terminal_has_no_bootstrap_or_entropy(self):
        reward = torch.tensor([-25., 25., -1.])
        done = torch.tensor([1., 1., 0.])
        q = torch.tensor([999., -999., 2.])
        log_pi = torch.tensor([-5., -5., -5.])
        result = bellman(reward, done, q, log_pi, .1, .9995)
        torch.testing.assert_close(result[:2], reward[:2])
        self.assertAlmostEqual(float(result[2]), -1+.9995*2.5, places=6)


if __name__ == '__main__':
    unittest.main()
