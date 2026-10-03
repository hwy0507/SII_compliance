"""Cost accounting checks: no simulation, fitted candidates or sealed reads."""
import unittest
from research72_budget_forecast_20261003 import forecast


def fixture():
    phases = ['learning_development_v1', 'controller_confirmation_v1', 'nominal_development',
        'neural_lr_development', 'development', 'collection', 'evaluation']
    snapshot = dict(created_utc='2026-10-03T21:30:00+00:00', sealed_contents_read=False,
        physics=[dict(path='/synthetic/'+label, rows=[], totals={'completed': 0}) for label in phases],
        rl=dict(registered_models=15, rows=[], totals={'completed_interaction_steps': 0}))
    snapshot['physics'][0].update(totals={'completed': 3}, rows=[
        dict(completed=True, full_horizon=True, wall_seconds=360),
        dict(completed=True, full_horizon=True, wall_seconds=360),
        dict(completed=True, full_horizon=False, wall_seconds=1)])
    protocol = dict(authorization_start_utc='2026-10-03T11:30:00+00:00',
        dispatch_deadline_utc='2026-10-06T11:30:00+00:00',
        budget_caps={'rl_adaptation_steps_per_family_seed': 80000})
    throughput = dict(rows=[dict(steady_action_mean_s=.001, steady_two_updates_mean_s=.019)])
    return snapshot, protocol, throughput


class BudgetTests(unittest.TestCase):
    def test_short_failure_stays_completed_but_cannot_shrink_full_horizon_cost(self):
        result = forecast(*fixture())
        self.assertEqual(result['full_horizon_timing_samples'], 2)
        self.assertEqual(result['pending_phases'][0]['remaining_including_inflight'], 261)
        row = result['scenarios'][0]
        self.assertEqual(row['episode_wall_s'], 360)
        self.assertAlmostEqual(row['final_physics_ideal_hours'], 22.8)
        self.assertAlmostEqual(row['optional_development_ideal_hours'], 3.6)
        self.assertEqual(row['latest_final_start_with_assumed_reserve_utc'], '2026-10-05T10:42:00+00:00')
        self.assertFalse(result['optional_fits_authorized_by_this_report'])

    def test_cumulative_rl_is_not_added_twice_and_unstarted_models_remain(self):
        snapshot, protocol, throughput = fixture()
        snapshot['rl']['rows'] = [dict(cumulative_steps=27500,
            segments=[dict(cumulative_steps=5500), dict(cumulative_steps=27500)])]
        snapshot['rl']['totals']['completed_interaction_steps'] = 27500
        result = forecast(snapshot, protocol, throughput)
        self.assertEqual(result['rl_remaining_interactions_to_all_caps'], 15*80000-27500)

    def test_missing_phase_or_inconsistent_ledger_refuses_forecast(self):
        snapshot, protocol, throughput = fixture()
        snapshot['physics'].pop()
        with self.assertRaisesRegex(AssertionError, 'Missing public phase'):
            forecast(snapshot, protocol, throughput)
        snapshot, protocol, throughput = fixture()
        snapshot['rl']['totals']['completed_interaction_steps'] = 100
        with self.assertRaises(AssertionError):
            forecast(snapshot, protocol, throughput)


if __name__ == '__main__':
    unittest.main()
