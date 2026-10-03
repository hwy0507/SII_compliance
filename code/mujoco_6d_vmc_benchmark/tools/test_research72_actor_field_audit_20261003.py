"""Negative controls for field audits, not evidence about trained controllers."""
import unittest
from unittest.mock import patch
import numpy as np
import research72_actor_field_audit_20261003 as audit_module


class Actor:
    def __init__(self, field=39, hidden_only=False, mutate=False):
        self.field, self.hidden_only, self.mutate = field, hidden_only, mutate

    def reset(self):
        self.state = np.zeros(1)

    def act(self, obs):
        if self.mutate:
            obs[39] = 0.
        self.state += obs[self.field]
        action = np.zeros(7)
        if not self.hidden_only:
            action[1] = np.tanh(obs[self.field])
        return action


class FieldAuditTests(unittest.TestCase):
    def test_permitted_signal_passes_with_exact_replay(self):
        observations = np.zeros((3, 48)); observations[:, 39] = .5
        expected = np.zeros((3, 7)); expected[:, 1] = np.tanh(.5)
        with patch.object(audit_module, 'load_current', side_effect=lambda _: Actor()):
            result = audit_module.audit('synthetic', observations, expected)
        self.assertEqual(result['hidden_state_checks'], 3)
        self.assertEqual(result['exported_replay_max_abs'], 0.)

    def test_hidden_use_of_forbidden_field_fails_even_with_zero_action(self):
        with patch.object(audit_module, 'load_current', side_effect=lambda _: Actor(field=0, hidden_only=True)):
            with self.assertRaises(AssertionError):
                audit_module.audit('synthetic', np.zeros((3, 48)), np.zeros((3, 7)))

    def test_input_mutation_fails(self):
        with patch.object(audit_module, 'load_current', side_effect=lambda _: Actor(mutate=True)):
            with self.assertRaisesRegex(ValueError, 'read-only'):
                audit_module.audit('synthetic', np.zeros((3, 48)), np.zeros((3, 7)))


if __name__ == '__main__':
    unittest.main()
