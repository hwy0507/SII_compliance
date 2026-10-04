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
        budget_caps={'rl_adaptation_steps_per_family_seed': 80000, 'training_seeds': [301,302,303],
                     'rl_families': ['admittance','impedance','vmc','direct_metric','direct_task']})
    throughput = dict(rows=[dict(steady_action_mean_s=.001, steady_two_updates_mean_s=.019)])
    return snapshot, protocol, throughput


class BudgetTests(unittest.TestCase):
    def test_common_boundary_charges_every_compatibility_step(self):
        snapshot, protocol, throughput = fixture()
        boundary=dict(scope='outcome_independent_common_rl_final_boundary',
            all_fifteen_models_required=True,selection_uses_rewards_or_task_results=False,
            sealed_contents_read=False,registered_utc='2026-10-03T20:30:00+00:00',
            original_exposure_cap=80000,original_optimizer_schedule_steps=80000,
            selected_step_limit=49500,maximum_compatibility_extra_steps_per_model=2750)
        snapshot['rl']['rows']=[dict(name='admittance_301',cumulative_steps=50000)]
        snapshot['rl']['totals']['completed_interaction_steps']=50000
        result=forecast(snapshot,protocol,throughput,optional_episodes=0,rl_boundary=boundary)
        self.assertEqual(result['rl_remaining_interactions_to_all_caps'],15*52250-50000)
        self.assertEqual(sum(q['remaining_interactions'] for q in result['rl_fixed_queues']),15*52250-50000)
        self.assertEqual(result['rl_budget']['original_cap'],80000)
        self.assertEqual(result['rl_budget']['selected_step_limit'],49500)
        self.assertEqual(protocol['budget_caps']['rl_adaptation_steps_per_family_seed'],80000)
        for change in [dict(selection_uses_rewards_or_task_results=True),
                       dict(registered_utc='2026-10-04T20:30:00+00:00'),
                       dict(maximum_compatibility_extra_steps_per_model=0)]:
            with self.assertRaises(AssertionError):
                forecast(snapshot,protocol,throughput,rl_boundary=dict(boundary,**change))
        snapshot['rl']['rows'][0]['cumulative_steps']=53000
        snapshot['rl']['totals']['completed_interaction_steps']=53000
        with self.assertRaises(AssertionError):forecast(snapshot,protocol,throughput,rl_boundary=boundary)

    def test_registered_short_diagnostics_are_conservatively_charged(self):
        snapshot, protocol, throughput = fixture()
        snapshot['physics'].append(dict(path='/synthetic/public_numerical_probe_v1',
            status='waiting_for_predecessor', totals={'completed': 1}, rows=[]))
        result = forecast(snapshot, protocol, throughput)
        self.assertEqual(result['pending_phases'][-1]['remaining_including_inflight'], 2)
        self.assertEqual(result['pending_phases'][-1]['maximum_registered_episodes'], 3)

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
        snapshot['rl']['rows'] = [dict(name='admittance_301', cumulative_steps=27500,
            segments=[dict(cumulative_steps=5500), dict(cumulative_steps=27500)])]
        snapshot['rl']['totals']['completed_interaction_steps'] = 27500
        result = forecast(snapshot, protocol, throughput)
        self.assertEqual(result['rl_remaining_interactions_to_all_caps'], 15*80000-27500)

    def test_unstarted_queue_cannot_be_divided_over_four_slots(self):
        snapshot, protocol, throughput = fixture()
        for phase in snapshot['physics']:
            counts = dict(learning_development_v1=264,controller_confirmation_v1=64,nominal_development=8,
                          neural_lr_development=168,development=168,collection=40,evaluation=1)
            phase['totals']['completed'] = counts[phase['path'].split('/')[-1]]
        jobs = [f'{family}_{seed}' for seed in [301,302,303] for family in protocol['budget_caps']['rl_families']]
        snapshot['rl']['rows'] = [dict(name=name,cumulative_steps=80000) for index,name in enumerate(jobs) if index%3!=1]
        snapshot['rl']['totals']['completed_interaction_steps'] = 800000
        result = forecast(snapshot, protocol, throughput, optional_episodes=0)
        row = result['scenarios'][0]
        expected = 400000*(360/1375+.020)/3600
        self.assertAlmostEqual(row['queue_constrained_ideal_development_hours'], expected)
        self.assertAlmostEqual(row['ideal_remaining_development_hours'], expected/4)
        self.assertEqual(result['rl_fixed_queues'][1]['remaining_interactions'], 400000)

    def test_duplicate_queue_accounting_rejected(self):
        snapshot, protocol, throughput = fixture()
        snapshot['rl']['rows'] = [dict(name='admittance_301',cumulative_steps=1)]*2
        snapshot['rl']['totals']['completed_interaction_steps'] = 2
        with self.assertRaisesRegex(AssertionError, 'Duplicate'):
            forecast(snapshot, protocol, throughput)

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
