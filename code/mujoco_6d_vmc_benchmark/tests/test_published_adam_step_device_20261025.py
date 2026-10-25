from pathlib import Path
import sys
import unittest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from published_adam_step_device_20261025 import move_adam_steps_to_cpu


class AdamStepTests(unittest.TestCase):
    def optimizer(self):
        p = torch.nn.Parameter(torch.tensor([1., -2.]))
        opt = torch.optim.Adam([p])
        p.square().sum().backward()
        opt.step()
        return p, opt

    def test_cpu_steps_and_moments_unchanged(self):
        p, opt = self.optimizer()
        state = opt.state[p]
        old = {key: value for key, value in state.items()}
        self.assertEqual(move_adam_steps_to_cpu(opt), dict(step_tensors=1, moved_to_cpu=0))
        self.assertTrue(all(state[key] is value for key, value in old.items()))

    def test_unsupported_adam_modes_rejected(self):
        for option in ('capturable', 'fused', 'differentiable'):
            p, opt = self.optimizer()
            opt.param_groups[0][option] = True
            with self.assertRaises(ValueError):
                move_adam_steps_to_cpu(opt)
        with self.assertRaises(ValueError):
            move_adam_steps_to_cpu(torch.optim.SGD([torch.nn.Parameter(torch.ones(1))], lr=.1))

    def test_invalid_counter_rejected(self):
        for step in (torch.tensor(float('nan')), torch.tensor(-1.), torch.ones(2), torch.tensor(1)):
            p, opt = self.optimizer()
            opt.state[p]['step'] = step
            with self.assertRaises(ValueError):
                move_adam_steps_to_cpu(opt)

    def test_fresh_optimizer_is_noop(self):
        opt = torch.optim.Adam([torch.nn.Parameter(torch.ones(2))])
        self.assertEqual(move_adam_steps_to_cpu(opt), dict(step_tensors=0, moved_to_cpu=0))


if __name__ == '__main__':
    unittest.main()
