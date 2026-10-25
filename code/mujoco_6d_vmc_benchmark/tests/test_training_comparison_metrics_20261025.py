"""Numerical comparison checks using synthetic data; no simulation or training."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from training_comparison_metrics_20261025 import (
    SCHEMA, completion_bonus, contact_torque_summary, summarize,
)


def fixture():
    records = []
    for method, times in [('rl', (20., None)), ('esn', (40., 30.))]:
        for case, time in zip(('condition1_seed1', 'condition2_seed1'), times):
            records.append(dict(method=method, case_id=case,
                task_success=time is not None, strict_success=time is not None,
                full_horizon=True, machine_safety_violation=False, elapsed_s=55.,
                completion_time_s=time,
                completion_time_definition='final_stable_placement_certification',
                torque_thresholds_nm=[5.]*7, peak_torque_nm_per_joint=[8.]*7,
                human_contact_s=2., human_below_threshold_s=1.))
    return dict(schema=SCHEMA, methods=['rl', 'esn'],
                case_ids=['condition1_seed1', 'condition2_seed1'],
                torque_thresholds_nm=[5.]*7, horizon_s=55., records=records)


class ComparisonTests(unittest.TestCase):
    def test_common_reference_and_failed_episode_denominator(self):
        out = summarize(fixture())
        self.assertEqual(out['reference_time_s'], 20.)
        self.assertEqual(out['methods']['rl']['spt_empirical'], .5)
        self.assertAlmostEqual(out['methods']['esn']['spt_empirical'], (.5+2/3)/2)
        self.assertEqual(out['methods']['rl']['task_success_rate'], .5)

    def test_fast_unsafe_task_does_not_set_success_reference(self):
        data = fixture()
        data['records'][2].update(completion_time_s=1., strict_success=False,
                                  machine_safety_violation=True)
        out = summarize(data)
        self.assertEqual(out['reference_time_s'], 20.)
        self.assertEqual(out['methods']['esn']['machine_safety_violation_rate'], .5)

    def test_all_failed_reference_is_unavailable_and_spt_zero(self):
        data = fixture()
        for row in data['records']:
            row.update(task_success=False, strict_success=False, completion_time_s=None)
        out = summarize(data)
        self.assertIsNone(out['reference_time_s'])
        self.assertTrue(all(r['spt_empirical'] == 0 for r in out['methods'].values()))

    def test_missing_duplicate_and_mismatched_threshold_rejected(self):
        data = fixture()
        for mutation in ('missing', 'duplicate', 'threshold'):
            changed = copy.deepcopy(data)
            if mutation == 'missing': changed['records'].pop()
            if mutation == 'duplicate': changed['records'].append(changed['records'][0])
            if mutation == 'threshold': changed['records'][0]['torque_thresholds_nm'][0] = 6.
            with self.assertRaises(ValueError): summarize(changed)

    def test_success_requires_measured_time_full_horizon_and_consistent_gates(self):
        for changes in [dict(completion_time_s=None), dict(completion_time_s=float('nan')),
                        dict(completion_time_s=56.), dict(full_horizon=False),
                        dict(completion_time_definition='audit_duration'),
                        dict(task_success=False), dict(machine_safety_violation=True)]:
            data = fixture(); data['records'][0].update(changes)
            with self.assertRaises(ValueError): summarize(data)

    def test_contact_ratio_pools_time_and_no_contact_is_na(self):
        data = fixture()
        data['records'][0].update(human_contact_s=1., human_below_threshold_s=1.)
        data['records'][1].update(human_contact_s=9., human_below_threshold_s=0.)
        for row in data['records'][2:]:
            row.update(human_contact_s=0., human_below_threshold_s=0.)
        out = summarize(data)['methods']
        self.assertAlmostEqual(out['rl']['human_compliance_ratio'], .1)
        self.assertIsNone(out['esn']['human_compliance_ratio'])

    def test_physical_sampling_time_and_noncontact_torque(self):
        rows = [dict(dt_s=.01, human_contact=False, torque_nm=[-20.]*7),
                dict(dt_s=.01, human_contact=True, torque_nm=[-4.]*7),
                dict(dt_s=.03, human_contact=True, torque_nm=[8.]*7)]
        out = contact_torque_summary(rows, [5.]*7)
        self.assertAlmostEqual(out['human_compliance_ratio'], .25)
        self.assertEqual(out['peak_torque_nm_per_joint'], [20.]*7)
        self.assertAlmostEqual(out['human_torque_excess_integral_nm_s_per_joint'][0], .09)
        dense = [dict(row, dt_s=row['dt_s']/10) for row in rows for _ in range(10)]
        other = contact_torque_summary(dense, [5.]*7)
        self.assertAlmostEqual(out['human_compliance_ratio'], other['human_compliance_ratio'])

    def test_nonfinite_physical_data_and_empty_samples_rejected(self):
        for rows in [[], [dict(dt_s=.01, human_contact=True, torque_nm=[float('inf')]*7)],
                     [dict(dt_s=0., human_contact=True, torque_nm=[1.]*7)]]:
            with self.assertRaises(ValueError): contact_torque_summary(rows, [5.]*7)

    def test_completion_reward_is_monotone_and_never_rewards_failed_tasks(self):
        def bonus(t):
            return completion_bonus(task_success=True, strict_success=True, completion_time_s=t)
        self.assertGreater(bonus(10.), bonus(30.))
        self.assertEqual(bonus(55.), 0.)
        self.assertEqual(completion_bonus(task_success=True, strict_success=False,
                                         completion_time_s=1.), 0.)
        with self.assertRaises(ValueError): bonus(None)


if __name__ == '__main__':
    unittest.main()
