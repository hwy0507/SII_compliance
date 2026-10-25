from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from validate_published_contact_candidate_20261025 import compare_npz, normalize_event_robot_sets
from prepare_published_contact_candidate_20261025 import patch_environment, patch_evaluator


class ContactCandidateTests(unittest.TestCase):
    def test_only_declared_robot_parts_set_order_is_ignored(self):
        a = dict(stats=dict(events=dict(contact=dict(robot_parts=['hand', 'link7']))),
                 task_events=['lift', 'carry'])
        b = dict(stats=dict(events=dict(contact=dict(robot_parts=['link7', 'hand']))),
                 task_events=['lift', 'carry'])
        self.assertEqual(normalize_event_robot_sets(a), normalize_event_robot_sets(b))
        self.assertEqual(a['stats']['events']['contact']['robot_parts'], ['hand', 'link7'])
        b['task_events'].reverse()
        self.assertNotEqual(normalize_event_robot_sets(a), normalize_event_robot_sets(b))
        b['task_events'].reverse()
        b['stats']['events']['contact']['robot_parts'] = ['hand', 'other']
        self.assertNotEqual(normalize_event_robot_sets(a), normalize_event_robot_sets(b))

    def test_duplicate_or_invalid_robot_parts_are_not_hidden(self):
        for parts in [['hand', 'hand'], [1, 'hand'], 'hand']:
            with self.assertRaisesRegex(AssertionError, 'robot_parts'):
                normalize_event_robot_sets(dict(stats=dict(events=dict(contact=dict(robot_parts=parts)))))

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
