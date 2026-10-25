from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from published_compliance_learner_20261025 import assert_finite_parameters
from train_published_compliance_20261025 import validate_resume_protocol


class PerformanceContinuationTests(unittest.TestCase):
    def test_finite_parameters_and_missing_gradients_pass(self):
        assert_finite_parameters(torch.nn.Linear(3, 2))

    def test_nonfinite_parameter_and_gradient_are_both_rejected(self):
        for gradient, value in ((False, float('inf')), (False, float('-inf')),
                                (True, float('nan')), (True, float('inf'))):
            net = torch.nn.Linear(3, 2)
            with torch.no_grad():
                if gradient:
                    net.weight.grad = torch.zeros_like(net.weight)
                    net.weight.grad[0, 0] = value
                else:
                    net.weight[0, 0] = value
            with self.assertRaisesRegex(FloatingPointError, 'weight'):
                assert_finite_parameters(net)

    def test_mixed_dtype_noncontiguous_and_failure_name(self):
        net = torch.nn.Module()
        net.register_parameter('first', torch.nn.Parameter(torch.ones(3, 2).T))
        # Finite float64 values above float32 range must not be cast to infinity.
        net.register_parameter('second', torch.nn.Parameter(torch.full((2,), 1e100, dtype=torch.float64)))
        assert_finite_parameters(net)
        net.second.grad = torch.tensor([0., float('-inf')], dtype=torch.float64)
        with self.assertRaisesRegex(FloatingPointError, 'second'):
            assert_finite_parameters(net)
        with torch.no_grad():
            net.first[0, 0] = float('nan')
        with self.assertRaisesRegex(FloatingPointError, 'first'):
            assert_finite_parameters(net)

    def test_registered_performance_continuation_rejects_reward_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'parent.json'
            old_root, new_root = Path(directory)/'old', Path(directory)/'new'
            for root in (old_root, new_root):
                root.mkdir()
                for name in ('PARAMETER_HASHES.json', 'ROBOT_ASSET_HASHES.json',
                        'CHEQ_HASHES.json', 'SOURCE_HASHES.json'):
                    (root/name).write_text(json.dumps({'scripts/physics.py': 'unchanged'}))
            old = dict(runtime=str(old_root), runtime_sha256='a', reward=dict(success_bonus=25), gamma=.9995)
            path.write_text(json.dumps(old))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            new = dict(old, runtime=str(new_root), runtime_sha256='b',
                resume_parent_registration=dict(path=str(path), sha256=digest),
                performance_amendment=dict(kind='batched_finite_checks_only'))
            validate_resume_protocol(digest, new, 'new_registration_digest')
            new['reward'] = dict(success_bonus=50)
            with self.assertRaisesRegex(ValueError, 'training contract'):
                validate_resume_protocol(digest, new, 'new_registration_digest')
            new['reward'] = old['reward']
            (new_root/'SOURCE_HASHES.json').write_text(json.dumps({'scripts/physics.py': 'changed'}))
            with self.assertRaisesRegex(ValueError, 'protected runtime source'):
                validate_resume_protocol(digest, new, 'new_registration_digest')

    def test_unregistered_parent_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'verified registered parent'):
            validate_resume_protocol('old_digest', {}, 'new_digest')


if __name__ == '__main__':
    unittest.main()
