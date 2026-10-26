"""Guard candidate construction and the restricted arithmetic contract."""
import ast
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from prepare_published_contact_math_20261026 import (
    HELPER, patch_environment, patch_evaluator, patch_adapter, replace_count)


class ContactMathTests(unittest.TestCase):
    def test_helper_preserves_float64_bits_including_special_values(self):
        namespace = {'np': np}
        exec(HELPER, namespace)
        rng = np.random.default_rng(47)
        values = list(rng.normal(size=(512, 3))) + [
            np.array([0., -0., 0.]), np.array([1e-320]*3),
            np.array([1e308]*3), np.array([np.inf, 0., 0.]), np.array([np.nan, 0., 0.])]
        with np.errstate(all='ignore'):
            for value in values:
                self.assertEqual(np.float64(np.linalg.norm(value)).tobytes(),
                                 np.float64(namespace['_contact_norm3'](value)).tobytes())

    def test_seam_guard_rejects_missing_and_ambiguous_inputs(self):
        for source in ('unrelated', 'expected expected'):
            with self.assertRaises(ValueError):
                replace_count(source, 'expected', 'replacement')
        for fn in (patch_environment, patch_evaluator, patch_adapter):
            with self.assertRaises(ValueError):
                fn('def unrelated():\n    pass\n')

    def test_real_source_transforms_are_scoped_and_not_repeatable(self):
        base = Path(__file__).resolve().parents[1]
        for relative, patch, start, end in [
            ('scripts/audited_velocity_env.py', patch_environment,
             '            contact_records = data.contact\n', '            if push_contact:\n'),
            ('scripts/validate_office_apparatus_v5_20260917.py', patch_evaluator,
             '        contact_records=d.contact\n', '        for key,force in pair_forces.items():\n'),
        ]:
            source = (base/relative).read_text()
            result = patch(source)
            ast.parse(result)
            index = source.index(start)
            self.assertEqual(result[:result.index('        '+('    ' if 'audited_' in relative else '')+'contact_body_ids')].replace(HELPER, ''), source[:index])
            self.assertEqual(result[result.index(end):], source[source.index(end, index):])
            with self.assertRaises(ValueError):
                patch(result)
        adapter = (base/'tools/published_compliance_episode_20261025.py').read_text()
        changed = patch_adapter(adapter)
        self.assertEqual(changed.replace('_contact_norm3(f[:3])', 'float(np.linalg.norm(f[:3]))'), adapter)


if __name__ == '__main__':
    unittest.main()
