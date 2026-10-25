import math
from pathlib import Path
import sys
import unittest

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from published_compliance_numerics_20261025 import tanh_log_jacobian


class NumericsTests(unittest.TestCase):
    def test_unsaturated_log_jacobian_matches_exact_density(self):
        x = torch.linspace(-2, 2, 25, dtype=torch.float64)
        scale = torch.tensor(.5, dtype=torch.float64)
        torch.testing.assert_close(tanh_log_jacobian(x, scale),
            torch.log(scale*(1-x.tanh().square())), rtol=1e-12, atol=1e-12)

    def test_saturated_tanh_keeps_finite_restoring_entropy_gradient(self):
        x = torch.tensor([-20., 20.], requires_grad=True)
        self.assertTrue(bool((x.tanh().abs() == 1).all()))
        value = tanh_log_jacobian(x, torch.ones(2)).sum()
        value.backward()
        self.assertTrue(bool(torch.isfinite(value)))
        torch.testing.assert_close(x.grad, torch.tensor([2., -2.]))

    def test_actor_column_loss_preserves_scalar_and_gradients(self):
        logp = torch.arange(8, dtype=torch.float64).reshape(-1, 1).requires_grad_()
        q = torch.linspace(-2, 3, 8, dtype=torch.float64).reshape(-1, 1).requires_grad_()
        original = (.2*logp-q.reshape(-1)).mean()
        original_grad = torch.autograd.grad(original, (logp, q), retain_graph=True)
        corrected = (.2*logp-q).mean()
        corrected_grad = torch.autograd.grad(corrected, (logp, q))
        torch.testing.assert_close(original, corrected, rtol=1e-12, atol=1e-12)
        for left, right in zip(original_grad, corrected_grad):
            torch.testing.assert_close(left, right, rtol=1e-12, atol=1e-12)


if __name__ == '__main__':
    unittest.main()
