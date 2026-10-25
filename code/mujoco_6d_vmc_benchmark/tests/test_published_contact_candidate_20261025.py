from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from validate_published_contact_candidate_20261025 import compare_npz
from prepare_published_contact_candidate_20261025 import patch_environment, patch_evaluator


class ContactCandidateTests(unittest.TestCase):
    def test_exact_array_contract_rejects_value_dtype_shape_and_signed_zero(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder)/'a.npz', Path(folder)/'b.npz'
            np.savez(a, q=np.array([0., 1.], dtype=np.float64))
            np.savez(b, q=np.array([0., 1.], dtype=np.float64))
            self.assertTrue(compare_npz(a, b)['exact'])
            for changed in [np.array([0., 2.]), np.array([-0., 1.]),
                            np.array([0., 1.], dtype=np.float32), np.array([[0., 1.]])]:
                np.savez(b, q=changed)
                with self.assertRaisesRegex(AssertionError, 'Array differs'):
                    compare_npz(a, b)
            np.savez(b, other=np.array([0., 1.]))
            with self.assertRaisesRegex(AssertionError, 'keys differ'):
                compare_npz(a, b)

    def test_missing_source_seams_fail_instead_of_partial_rewrite(self):
        for patch in (patch_environment, patch_evaluator):
            with self.assertRaises(ValueError):
                patch('def unrelated():\n    pass\n')


if __name__ == '__main__':
    unittest.main()
