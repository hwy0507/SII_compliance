"""Guard against calling failed/unsafe/partial RL runs convergence."""
import unittest
from extend_local_rl_training_20261009 import assess, require_complete_training


def row(steps, task=0, strict=0):
    return dict(steps=steps, completed=8, task=task, strict=strict)


class ExtensionContracts(unittest.TestCase):
    def test_episode_boundary_shortfall_does_not_hide_failed_plateau(self):
        history = [row(9684), dict(row(54146), scheduled_limit=55000),
                   dict(row(109271), scheduled_limit=110000)]
        self.assertTrue(assess(history)['zero_task_learning_stall'])
        self.assertFalse(assess(history)['converged'])

    def test_failed_plateau_is_not_convergence(self):
        out = assess([row(11000), row(55000), row(110000)])
        self.assertTrue(out['zero_task_learning_stall'])
        self.assertFalse(out['candidate_usable_and_stable'])
        self.assertFalse(out['converged'])
        self.assertEqual(out['next_step'], 'reward_exploration_control_review')

    def test_single_good_checkpoint_is_not_stable(self):
        out = assess([row(11000), row(55000, 8, 8)])
        self.assertFalse(out['candidate_usable_and_stable'])

    def test_unsafe_task_success_is_not_usable(self):
        out = assess([row(s, 8, 0) for s in (55000, 110000, 220000)])
        self.assertFalse(out['candidate_usable_and_stable'])
        self.assertFalse(out['zero_task_learning_stall'])

    def test_stable_success_still_requires_independent_seeds(self):
        out = assess([row(55000, 7, 6), row(110000, 8, 7), row(220000, 8, 7)])
        self.assertTrue(out['candidate_usable_and_stable'])
        self.assertFalse(out['converged'])
        self.assertFalse(out['final_comparison_authorized'])
        self.assertEqual(out['next_step'], 'independent_seed_confirmation')

    def test_incomplete_development_is_rejected(self):
        bad = row(55000, 7, 6); bad['completed'] = 7
        with self.assertRaises(AssertionError): assess([bad])

    def test_budget_interruption_is_not_full_training(self):
        state = dict(status='complete', stop_reason='deadline', steps=11000,
                     checkpoint_rows=[dict(step=11000)], rows=[])
        with self.assertRaises(AssertionError): require_complete_training(state, 55000)
        state['stop_reason'] = 'step_budget'
        with self.assertRaises(AssertionError): require_complete_training(state, 55000)
        state.update(steps=55000, checkpoint_rows=[dict(step=55000)], rows=[dict(result={})])
        require_complete_training(state, 55000)
        state['rows'].append({})
        with self.assertRaises(AssertionError): require_complete_training(state, 55000)


if __name__ == '__main__': unittest.main()
