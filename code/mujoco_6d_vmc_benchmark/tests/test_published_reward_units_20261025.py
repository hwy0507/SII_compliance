from pathlib import Path
import sys
import unittest

import numpy as np
import torch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from probe_published_reward_units_20261025 import scaled_batch
from diagnose_published_value_bound_20261025 import soft_upper_bound


class RewardUnitTests(unittest.TestCase):
    def test_scaled_reward_preserves_terminal_masks_and_original_storage(self):
        rewards=torch.tensor([[-25.],[-.4],[25.]])
        masks=torch.tensor([[1.],[0.],[1.]])
        batch={'rewards':rewards,'dones':masks,'observations':torch.ones(3,48)}
        out=scaled_batch(batch,.04)
        torch.testing.assert_close(out['rewards'],torch.tensor([[-1.],[-.016],[1.]]))
        torch.testing.assert_close(rewards,torch.tensor([[-25.],[-.4],[25.]]),rtol=0,atol=0)
        self.assertIs(out['dones'],masks)
        self.assertIs(out['observations'],batch['observations'])
        out['rewards'].zero_()
        self.assertNotEqual(float(rewards.sum()),0.)
        for scale in [0.,-1.,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):scaled_batch(batch,scale)

    def test_bound_units_require_scaling_entropy_temperature_too(self):
        scale=.04;low=[0]+[-1]*6;high=[1]*7
        original=soft_upper_bound(.3,.9995,1375,low,high,potential=.4)
        transformed=soft_upper_bound(.3*scale,.9995,1375,low,high,potential=.4,
                                    terminal_cap=30*scale,shaping_weight=5*scale)
        np.testing.assert_allclose(transformed/scale,original,rtol=1e-12)
        same_alpha=soft_upper_bound(.3,.9995,1375,low,high,potential=.4,
                                   terminal_cap=30*scale,shaping_weight=5*scale)
        self.assertGreater(same_alpha/scale,original)


if __name__=='__main__':unittest.main()
