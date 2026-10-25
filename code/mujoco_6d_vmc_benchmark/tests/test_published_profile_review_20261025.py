import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from review_published_live_profile_20261025 import review, sha, summarize


class ProfileReviewTests(unittest.TestCase):
    def test_empty_stacks_do_not_dilute_framed_fraction(self):
        result = summarize(' 8\nroot;step (adam.py:1) 2\n')
        self.assertEqual(result['empty_stack_samples'], 8)
        self.assertEqual(result['framed_samples'], 2)
        self.assertEqual(result['inclusive']['adam_step']['fraction_all'], .2)
        self.assertEqual(result['inclusive']['adam_step']['fraction_framed'], 1.)

    def test_overlapping_categories_count_samples_once_per_category(self):
        result = summarize('update (published_compliance_learner:1);step (adam.py:1);step (adam.py:2) 3\n')
        for key in ('learner_update', 'adam_step'):
            self.assertEqual(result['inclusive'][key]['samples'], 3)
        self.assertEqual(result['total_samples'], 3)

    def test_empty_only_has_undefined_framed_fractions(self):
        result = summarize(' 7\n')
        self.assertIsNone(result['inclusive']['adam_step']['fraction_framed'])
        self.assertEqual(result['top_framed_leaves'], [])

    def test_malformed_samples_rejected(self):
        for raw in ('', 'frame 0', 'frame -1', 'frame; 1', '  ;frame 1', 'frame NaN'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                summarize(raw)

    def test_review_checks_raw_integrity_and_preserves_original(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = root/'direct.folded'
            raw.write_text(' 8\nroot;step (adam.py:1) 2\n')
            reg = root/'REGISTRATION.json'
            reg.write_text(json.dumps(dict(targets={'direct': {}}, duration_s=60, rate_hz=50)))
            summary = root/'SUMMARY.json'
            summary.write_text(json.dumps(dict(registration_sha256=sha(reg), methods={'direct': dict(
                total_samples=10, raw_sha256=sha(raw), inclusive_fractions={'adam_step': .2},
                target_identity_verified=True, before={'wall_time_utc': 1},
                after={'wall_time_utc': 81}, observed_new_steps=10, observed_new_updates=20)})))
            before = {p.name: sha(p) for p in root.iterdir()}
            result = review(root, reg)
            self.assertEqual(result['methods']['direct']['progress_timestamp_delta_s'], 80)
            self.assertEqual(before, {p.name: sha(p) for p in root.iterdir()})
            raw.write_text(' 9\nroot;step (adam.py:1) 1\n')
            with self.assertRaisesRegex(ValueError, 'Raw profile hash mismatch'):
                review(root, reg)


if __name__ == '__main__':
    unittest.main()
