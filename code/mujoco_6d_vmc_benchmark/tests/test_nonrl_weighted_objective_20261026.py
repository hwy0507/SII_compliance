"""Regression: unequal chunk weights must retain their global importance."""
import sys
import unittest
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from train_fair_students_20261013 import loss_mass, scheduled_rate


class ObjectiveTest(unittest.TestCase):
    def test_global_gradient_matches_weighted_dataset_with_short_tail(self):
        # Last chunk is shorter, and contact importance differs by two orders.
        weights = [torch.ones(512, dtype=torch.float64), torch.full((31,), 100., dtype=torch.float64)]
        targets = [torch.ones(512, dtype=torch.float64), torch.full((31,), 3., dtype=torch.float64)]
        mass = sum(w.sum() for w in weights)
        mean = mass / sum(w.numel() for w in weights)
        x = torch.tensor(.2, dtype=torch.float64, requires_grad=True)
        global_loss = (sum(((x-y)**2*w).sum() for w,y in zip(weights, targets)) + .1*x.square()) / mass
        expected = torch.autograd.grad(global_loss, x)[0]
        chunk_loss = sum(((x-y)**2*w).sum()/loss_mass(w, 'global', mean) +
                         (w > 0).sum()/512*.1/mass*x.square() for w,y in zip(weights, targets))
        got = torch.autograd.grad(chunk_loss, x)[0] * (512*mean/mass)
        torch.testing.assert_close(got, expected)
        legacy = sum(((x-y)**2*w).sum()/loss_mass(w, 'legacy_batch', mean) for w,y in zip(weights, targets))/2
        old = torch.autograd.grad(legacy, x)[0]
        self.assertGreater(abs(float(old-expected)), 1.)

    def test_legacy_denominator_unchanged(self):
        w = torch.tensor([1., 2., 9.])
        self.assertEqual(float(loss_mass(w, 'legacy_batch', 123.)), 12.)

    def test_cosine_rate_endpoints_and_monotonicity(self):
        rates = [scheduled_rate(1e-5, i, 32, 'cosine') for i in range(32)]
        self.assertAlmostEqual(rates[0], 1e-5)
        self.assertAlmostEqual(rates[-1], 1e-7)
        self.assertTrue(all(a >= b for a,b in zip(rates, rates[1:])))
        self.assertEqual(scheduled_rate(1e-5, 31, 32, 'constant'), 1e-5)


if __name__ == '__main__':
    unittest.main()
