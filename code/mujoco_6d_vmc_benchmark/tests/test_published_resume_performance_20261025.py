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
from published_target_gradients_20261025 import freeze_target_parameters


class PerformanceContinuationTests(unittest.TestCase):
    def test_frozen_target_parameters_keep_action_gradient(self):
        from types import SimpleNamespace
        target = torch.nn.Linear(2, 1, bias=False)
        with torch.no_grad():
            target.weight.copy_(torch.tensor([[2., -3.]]))
        learner = SimpleNamespace(agent=SimpleNamespace(ensemble_targets=torch.nn.ModuleList([target])))
        self.assertEqual(freeze_target_parameters(learner), 2)
        action = torch.tensor([[.2, .4]], requires_grad=True)
        target(action).sum().backward()
        torch.testing.assert_close(action.grad, torch.tensor([[2., -3.]]), rtol=0, atol=0)
        self.assertIsNone(target.weight.grad)
        with torch.no_grad():
            target.weight.mul_(.995).add_(torch.ones_like(target.weight), alpha=.005)
        self.assertFalse(target.weight.requires_grad)

    def test_target_gradient_continuation_preserves_every_other_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            old_root, new_root = Path(directory)/'old', Path(directory)/'new'
            original = {'scripts/physics.py':'same', 'tools/spt_rl_reward_20261025.py':'same',
                'tools/published_replay_device_cache_20261025.py':'same',
                'tools/published_compliance_learner_20261025.py':'old',
                'tools/train_published_compliance_20261025.py':'old'}
            for root in (old_root, new_root):
                root.mkdir()
                for name in ('PARAMETER_HASHES.json','ROBOT_ASSET_HASHES.json','CHEQ_HASHES.json'):
                    (root/name).write_text('{}')
                (root/'SOURCE_HASHES.json').write_text(json.dumps(original))
            old = dict(runtime=str(old_root), runtime_sha256='old', algorithms=['cheq', 'sac'],
                reward={'success_bonus':25}, gamma=.9995,
                performance_amendment=dict(kind='device_replay_cache_only',replay_device_cache=True))
            parent = Path(directory)/'parent.json'; parent.write_text(json.dumps(old))
            digest = hashlib.sha256(parent.read_bytes()).hexdigest()
            new = dict(old, runtime=str(new_root), runtime_sha256='new',
                resume_parent_registration=dict(path=str(parent),sha256=digest),
                performance_amendment=dict(kind='frozen_target_gradients_only',replay_device_cache=True,
                                           freeze_target_gradients=True,algorithm_scope=['cheq']))
            allowed = dict(original, **{'tools/published_compliance_learner_20261025.py':'new',
                'tools/train_published_compliance_20261025.py':'new',
                'tools/published_target_gradients_20261025.py':'added'})
            (new_root/'SOURCE_HASHES.json').write_text(json.dumps(allowed))
            validate_resume_protocol(digest,new,'new')
            for name in ['scripts/physics.py','tools/spt_rl_reward_20261025.py',
                         'tools/published_replay_device_cache_20261025.py']:
                changed=dict(allowed); changed[name]='changed'
                (new_root/'SOURCE_HASHES.json').write_text(json.dumps(changed))
                with self.assertRaisesRegex(ValueError,'protected runtime source'):
                    validate_resume_protocol(digest,new,'new')
            (new_root/'SOURCE_HASHES.json').write_text(json.dumps(allowed))
            new['performance_amendment']['replay_device_cache']=False
            with self.assertRaisesRegex(ValueError,'replay cache setting'):
                validate_resume_protocol(digest,new,'new')
            new['performance_amendment']['replay_device_cache']=True
            new['performance_amendment']['freeze_target_gradients']=False
            with self.assertRaisesRegex(ValueError,'CHEQ-only'):
                validate_resume_protocol(digest,new,'new')
            new['performance_amendment']['freeze_target_gradients']=True
            new['performance_amendment']['algorithm_scope']=['cheq','sac']
            with self.assertRaisesRegex(ValueError,'CHEQ-only'):
                validate_resume_protocol(digest,new,'new')
            new['performance_amendment']['algorithm_scope']=['cheq']
            new['gamma']=.99
            with self.assertRaisesRegex(ValueError,'training contract'):
                validate_resume_protocol(digest,new,'new')

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

    def test_device_cache_continuation_preserves_learner_and_physics(self):
        with tempfile.TemporaryDirectory() as directory:
            old_root, new_root = Path(directory)/'old', Path(directory)/'new'
            original = {'scripts/physics.py':'same', 'tools/published_compliance_learner_20261025.py':'same'}
            for root in (old_root, new_root):
                root.mkdir()
                for name in ('PARAMETER_HASHES.json','ROBOT_ASSET_HASHES.json','CHEQ_HASHES.json'):
                    (root/name).write_text('{}')
                (root/'SOURCE_HASHES.json').write_text(json.dumps(original))
            old = dict(runtime=str(old_root), runtime_sha256='old', reward={'success_bonus':25})
            parent = Path(directory)/'parent.json'; parent.write_text(json.dumps(old))
            digest = hashlib.sha256(parent.read_bytes()).hexdigest()
            new = dict(old, runtime=str(new_root), runtime_sha256='new',
                resume_parent_registration=dict(path=str(parent),sha256=digest),
                performance_amendment=dict(kind='device_replay_cache_only',replay_device_cache=True))
            allowed = dict(original, **{'tools/published_replay_device_cache_20261025.py':'new',
                                       'tools/train_published_compliance_20261025.py':'new'})
            (new_root/'SOURCE_HASHES.json').write_text(json.dumps(allowed))
            validate_resume_protocol(digest,new,'new')
            for name in original:
                changed=dict(allowed); changed[name]='changed'
                (new_root/'SOURCE_HASHES.json').write_text(json.dumps(changed))
                with self.assertRaisesRegex(ValueError,'protected runtime source'):
                    validate_resume_protocol(digest,new,'new')
            (new_root/'SOURCE_HASHES.json').write_text(json.dumps(allowed))
            new['reward']={'success_bonus':50}
            with self.assertRaisesRegex(ValueError,'training contract'):
                validate_resume_protocol(digest,new,'new')
            new['reward']=old['reward']
            new['performance_amendment']['replay_device_cache']=False
            with self.assertRaisesRegex(ValueError,'explicitly enable'):
                validate_resume_protocol(digest,new,'new')


if __name__ == '__main__':
    unittest.main()
