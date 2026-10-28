"""Guard regressions; synthetic state is not actual continuation evidence."""
import copy
from types import SimpleNamespace
import unittest

import numpy as np

from research72_rl_resume_audit_20261004 import check_lineage, replay_first


class ResumeAuditTests(unittest.TestCase):
    def setUp(self):
        self.manifest = dict(checkpoint='/immutable/parent', hashes={'a': 'hash'}, cumulative_physics_steps=5500)
        self.protocol = dict(protocol_sha256='protocol', seed=301, controller='impedance', reward={'mode': 'metric'},
            agent_config={'action_dimension': 5}, utd=2, maximum_new_physics_steps=80000,
            prior_file_sha256='prior', training_condition_ids=['train_'+str(i) for i in range(32)],
            warmup_steps=5000, source_sha256={'source': 'hash'})
        self.parent = dict(status='complete', steps=5500, episodes=4, updates=1002)
        self.runner = dict(episode_boundary=True, automatic_exact_resume_supported=True,
                           pending_transition=None, step=5500, episode=4)
        self.child = dict(status='running', steps=6875, episodes=5, updates=3752,
            new_segment_steps=1375, new_segment_episodes=1,
            resumed_from=dict(checkpoint='/immutable/parent', hashes={'a': 'hash'}, inherited_steps=5500, inherited_episodes=4),
            rows=[dict(ended_utc='2026-10-04T03:00:00+00:00', step_before=5500, step_after=6875,
                       episode=4, steps=1375, condition_id='train_4')])

    def check(self, protocol=None):
        return check_lineage(self.manifest, self.protocol, self.parent, self.runner,
                             protocol or self.protocol, self.child)

    def test_actual_new_boundary_required(self):
        self.assertEqual(self.check()['step_before'], 5500)
        self.child['rows'][0].pop('ended_utc')
        with self.assertRaises(AssertionError): self.check()

    def test_wrong_seed_or_source_rejected(self):
        for key, value in [('seed', 302), ('source_sha256', {'source': 'changed'})]:
            changed = copy.deepcopy(self.protocol); changed[key] = value
            with self.assertRaises(AssertionError): self.check(changed)

    def test_repeat_previous_condition_rejected(self):
        self.child['rows'][0]['condition_id'] = 'train_3'
        with self.assertRaises(AssertionError): self.check()

    def test_counter_reset_rejected(self):
        self.child['updates'] = 0
        with self.assertRaises(AssertionError): self.check()

    def test_incomplete_parent_rejected(self):
        self.parent['status'] = 'running'
        with self.assertRaises(AssertionError): self.check()

    def test_stochastic_action_and_pending_transition_contract(self):
        class Agent:
            def __init__(self):
                self.interactions = 5500; self.updates = 1002; self.reward_samples = 5500
                self.raw_agent = SimpleNamespace(_rng=np.array([1, 2], np.uint32))
            def diagnostics(self):
                return dict(interactions=self.interactions, updates=self.updates, reward_samples=self.reward_samples)
            def sample_action(self, observation, previous_transition, training):
                assert previous_transition is None and training is True
                self.interactions += 1
                return np.full(5, .125, np.float32)
        saved = dict(interactions=5500, updates=1002, reward_samples=5500, jax_rng=[1, 2])
        self.assertEqual(replay_first(Agent(), np.zeros(48), np.full(5, .125), saved)['first_action_max_abs'], 0.)
        with self.assertRaises(AssertionError):
            replay_first(Agent(), np.zeros(48), np.zeros(5), saved)
        saved['jax_rng'] = [3, 4]
        with self.assertRaises(AssertionError):
            replay_first(Agent(), np.zeros(48), np.full(5, .125), saved)


if __name__ == '__main__':
    unittest.main()
