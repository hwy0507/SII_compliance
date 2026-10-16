import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from report_goal_tracking_pair_20261016 import METRICS, compare, episode_record, summarize, validate_protocol


def record():
    return dict(episode=4, condition_id='train_a', step_before=5500, step_after=6875,
        closed=True, receipt_valid=True, joint_success=False, return_value=-20,
        result=dict(task_success=True, strict_success=False, full_task_horizon_completed=True),
        metrics={key: 2. for key in METRICS})


class PairReportTests(unittest.TestCase):
    def test_executed_protocol_must_match_registered_reward_and_exposure(self):
        job = dict(seed=42, controller='impedance', reward_variant='payload_shaping',
                   hp='parameter_balanced', limit=11000, reward='metric')
        protocol = dict(goal_registration_sha256='hash', seed=42, controller='impedance',
            reward_variant='payload_shaping', hyperparameter_id='parameter_balanced',
            segment_limit=11000, maximum_steps=1000000, warmup_steps=5000, utd=1,
            agent_config=dict(n_step=25), reward=dict(mode='metric'))
        validate_protocol(protocol, job, 'hash')
        for change in (dict(seed=43), dict(warmup_steps=100), dict(utd=2),
                       dict(tracking_guidance={'weight': 36})):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_protocol(dict(protocol, **change), job, 'hash')

    def test_condition_mismatch_is_retained_not_paired(self):
        a = record(); b = record(); b['condition_id'] = 'train_b'
        result = compare([a], [b])
        self.assertEqual(len(result['pairs']), 2)
        self.assertTrue(all(p['reasons'] == ['counterpart_missing'] for p in result['pairs']))
        self.assertEqual(result['by_phase']['learned']['pairs'], 0)

    def test_short_and_incomplete_are_retained_without_metric_comparison(self):
        a = record(); b = record()
        b['result']['full_task_horizon_completed'] = False
        b['step_after'] = 6000
        result = compare([a], [b])
        self.assertEqual(len(result['pairs']), 1)
        self.assertFalse(result['pairs'][0]['comparable'])
        self.assertEqual(len(result['pairs'][0]['reasons']), 2)
        b.update(closed=False, receipt_valid=False)
        self.assertEqual(compare([a], [b])['pairs'][0]['reasons'], ['incomplete_or_invalid_receipt'])
        self.assertEqual(summarize([a, b])['incomplete_attempts'], 1)

    def test_failed_full_episodes_are_compared_without_reward_ranking(self):
        a = record(); b = record()
        b['metrics']['rmse_mm'] = 1.
        b['return_value'] = -100000
        result = compare([a], [b])
        self.assertEqual(result['by_phase']['learned']['median_native_metric_delta']['rmse_mm'], -1.)
        self.assertEqual(summarize([a,b])['verified_joint_success_fraction_of_closed'], 0.)
        self.assertNotIn('reward_delta', json.dumps(result))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            compare([a, copy.deepcopy(a)], [b])

    def test_real_receipt_requires_both_gates_and_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            audit = dict(training=True, task_success=True, strict_success=False,
                         full_horizon=True, stage='carry', physical_seconds=55.,
                         **{key:1. for key in METRICS})
            path = Path(tmp)/'AUDIT.json'; path.write_text(json.dumps(audit))
            row = dict(record(), run=tmp, ended_utc='done',
                       audit_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            item = episode_record(row)
            self.assertTrue(item['receipt_valid'])
            self.assertFalse(item['joint_success'])
            path.write_text(json.dumps(dict(audit, strict_success=True)))
            item = episode_record(row)
            self.assertFalse(item['receipt_valid'])
            self.assertEqual(item['errors'], ['audit_hash_mismatch'])
            self.assertEqual(summarize([item])['invalid_closed_receipts'], 1)

    def test_warmup_is_not_combined_with_learned_pairs(self):
        a = record(); a.update(episode=0, step_before=0, step_after=1375)
        b = copy.deepcopy(a)
        result = compare([a,record()], [b,record()])
        self.assertEqual(result['by_phase']['warmup']['pairs'],1)
        self.assertEqual(result['by_phase']['mixed']['pairs'],0)
        self.assertEqual(result['by_phase']['learned']['pairs'],1)


if __name__ == '__main__':
    unittest.main()
