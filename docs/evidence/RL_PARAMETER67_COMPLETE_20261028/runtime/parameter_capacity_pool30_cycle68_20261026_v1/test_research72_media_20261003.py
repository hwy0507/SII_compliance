import unittest
from research72_media_20261003 import choose


class MediaTests(unittest.TestCase):
    def test_first_identity_all_models_including_failure_and_missing(self):
        models = [dict(name='esn', category='esn', seed=1), dict(name='mlp', category='mlp', seed=1),
                  dict(name='zero', category='zero')]
        def row(name, condition, success):
            return dict(candidate=name, condition_id=condition, run='/synthetic/'+name,
                metrics=dict(trace_sha256='trace', model_sha256='model', task_success=success,
                    strict_success=success, full_horizon=success, abort_reason=None if success else 'abort'))
        report = dict(conditions=['second', 'first'], raw_rows=[row('esn', 'first', False),
            row('mlp', 'first', True), row('zero', 'second', True)])
        selected = choose(dict(candidates=models), report)
        self.assertEqual(len(selected), 3)
        self.assertEqual({r['condition_id'] for r in selected}, {'first'})
        self.assertFalse(selected[0]['strict_success'])
        self.assertTrue(selected[1]['strict_success'])
        self.assertEqual(selected[2]['status'], 'missing_audited_episode')


if __name__ == '__main__':
    unittest.main()
