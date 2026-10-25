from pathlib import Path
import sys
import unittest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from diagnose_published_training_20261025 import registered_target_minimum


class TargetDiagnosticTests(unittest.TestCase):
    def test_candidate_uses_all_targets_and_legacy_pair_is_preserved(self):
        q=torch.tensor([[5., 6.], [7., 4.], [1., 8.], [3., 2.], [9., 0.]])
        torch.testing.assert_close(registered_target_minimum(q,'cheq',2),torch.tensor([5.,4.]))
        torch.testing.assert_close(registered_target_minimum(q,'cheq',5),torch.tensor([1.,0.]))
        torch.testing.assert_close(registered_target_minimum(q[:2],'sac',2),torch.tensor([5.,4.]))

    def test_incompatible_rules_and_ensemble_shapes_rejected(self):
        for q,algorithm,count in [(torch.zeros(2,4),'sac',5),
                (torch.zeros(4,4),'cheq',5),(torch.zeros(5,4),'cheq',3),
                (torch.zeros(5,4),'unknown',2)]:
            with self.assertRaises(ValueError):registered_target_minimum(q,algorithm,count)


if __name__=='__main__':unittest.main()
