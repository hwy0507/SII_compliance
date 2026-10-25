"""Regression coverage for the observed CHEQ warmup boundary failure."""
import os
from pathlib import Path
import sys
import unittest

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from published_compliance_learner_20261025 import PublishedLearner
from train_published_compliance_20261025 import Replay, plateau_status


class RecoveryTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('SII_PUBLISHED_RUNTIME'), 'requires pinned published-code runtime')
    def test_adaptive_weight_after_warmup_is_a_scalar_in_every_stream(self):
        torch.set_num_threads(1)
        agent = PublishedLearner(Path(os.environ['SII_PUBLISHED_RUNTIME']), dimension=7,
                                 direct=True, seed=1, device='cpu', algorithm='cheq')
        # Interior uncertainty executes the upstream branch that returns an
        # ndarray, unlike saturated bounds and the initial uniform warmup.
        agent.learner.get_epistemic_uncertainty = lambda **kwargs: (
            torch.tensor([[0.]]), torch.tensor([[.1]]))
        for stream in range(3):
            agent.reset_episode(stream)
            for step in (4999, 5000, 9999, 10000, 10001, 11000):
                obs, raw, action, weight = agent.act(np.zeros(48), step=step, stream=stream)
                np.testing.assert_allclose(action, weight*raw, rtol=1e-6, atol=1e-7)
                self.assertIsInstance(agent.mixers[stream].weight, float)
                self.assertAlmostEqual(float(obs[-1]), weight, places=6)
            self.assertAlmostEqual(agent.mixers[stream].weight, .64444444, places=6)
        self.assertIsNot(agent.mixers[0], agent.mixers[1])

    def test_ring_replay_resume_preserves_next_sample(self):
        replay = Replay(7, 49, seed=3, capacity=9)
        for i in range(17):
            replay.add(observations=np.full(49, i), next_observations=np.full(49, i+1),
                       actions=np.zeros(7), rewards=[i], dones=[i % 2])
        state = replay.state_dict()
        expected = replay.sample(256)
        restored = Replay(7, 49, seed=99, capacity=9)
        restored.load_state_dict(state)
        actual = restored.sample(256)
        for key in expected:
            np.testing.assert_array_equal(actual[key], expected[key])

    def test_flat_bad_reward_is_not_a_plateau_candidate(self):
        self.assertFalse(plateau_status([dict(reward_mean=-25)]*8)['candidate'])


if __name__ == '__main__':
    unittest.main()
