"""Ensure a scientific critic restart cannot silently alter actor or RNG state."""
import copy
import os
from pathlib import Path
import sys
import unittest

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from prepare_published_critic_restart_20261025 import reset_critic_state
from validate_published_finite_check_20261025 import digest


class RestartTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('SII_PUBLISHED_RUNTIME'), 'requires pinned authors runtime')
    def test_real_trained_state_preserves_every_noncritic_field(self):
        from published_compliance_learner_20261025 import PublishedLearner
        torch.set_num_threads(1)
        for dimension, direct in [(7, True), (5, False), (7, False)]:
            kwargs = dict(runtime=Path(os.environ['SII_PUBLISHED_RUNTIME']), dimension=dimension,
                direct=direct, device='cpu', algorithm='cheq', critic_layer_norm=True,
                numerical_amendments=True)
            old = PublishedLearner(**kwargs, seed=19)
            old.update(dict(observations=np.zeros((16,49), np.float32),
                next_observations=np.ones((16,49), np.float32), actions=np.zeros((16,dimension), np.float32),
                rewards=np.ones((16,1), np.float32), dones=np.zeros((16,1), np.float32),
                masks=np.ones((16,5), np.float32)))
            parent = old.state_dict()
            before = digest(parent)
            self.assertTrue(parent['q_optimizer']['state'])
            new = PublishedLearner(**kwargs, seed=23)
            fresh = new.state_dict()
            restored, replaced = reset_critic_state(parent, fresh)
            self.assertEqual(before, digest(parent))
            self.assertFalse(restored['q_optimizer']['state'])
            for key in parent:
                if key not in ('agent', 'q_optimizer'):
                    self.assertEqual(digest(restored[key]), digest(parent[key]))
            self.assertTrue(all(k.startswith(('ensemble.', 'ensemble_targets.')) for k in replaced))
            new.load_state_dict(copy.deepcopy(restored))
            self.assertEqual(digest(new.state_dict()), digest(restored))
            bad = copy.deepcopy(fresh)
            bad['q_optimizer']['param_groups'][0]['lr'] *= .5
            with self.assertRaises(ValueError):
                reset_critic_state(parent, bad)
            bad = copy.deepcopy(fresh)
            first_target = next(k for k in bad['agent'] if k.startswith('ensemble_targets.'))
            bad['agent'][first_target] += 1
            with self.assertRaises(ValueError):
                reset_critic_state(parent, bad)


if __name__ == '__main__':
    unittest.main()
