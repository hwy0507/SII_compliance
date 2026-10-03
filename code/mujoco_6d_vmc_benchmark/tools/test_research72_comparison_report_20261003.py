"""Synthetic evidence only. Never accesses actual sealed conditions."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from research72_comparison_report_20261003 import assemble, markdown, load_evidence, EVENTS, SCALARS, sha


def metrics(success=True, full=True, exposed=True, force=10.):
    record = dict(task_success=success, strict_success=success, full_horizon=full,
        final_stage='placed' if success else 'carry', abort_reason=None if full else 'penetration',
        contact={event: dict(exposure=exposed, contact_p95_force_n=force if exposed else None,
            peak_force_n=force if exposed else 0., impulse_ns=force if exposed else 0.,
            contact_duration_s=1. if exposed else 0., extended_no_contact_longest_s=None) for event in EVENTS},
        recovery={event: dict(exposed=exposed, settled_rejoin_time_s=None,
            right_censored=exposed, observation_window_s=2.) for event in ('ball', 'human', 'rod')})
    record.update({field: 1. for field in SCALARS})
    return record


def models():
    return [dict(name='esn1', category='esn', seed=1), dict(name='esn2', category='esn', seed=2),
            dict(name='zero', category='nominal_zero')]


def row(model, condition='c0', **kwargs):
    return dict(candidate=model, category='nominal_zero' if model == 'zero' else 'esn',
                condition_id=condition, metrics=metrics(**kwargs))


class ReportTests(unittest.TestCase):
    def test_missing_retains_denominator_and_separates_failure(self):
        report = assemble(models(), ['c0', 'c1'], [row('esn1'), row('esn2', success=False)])
        esn = report['families']['esn']
        self.assertEqual(esn['strict']['planned'], 4)
        self.assertEqual(esn['strict']['missing'], 2)
        self.assertEqual(esn['strict']['planned_rate_bounds'], [.25, .75])
        self.assertIsNone(esn['strict']['rate'])
        self.assertEqual(esn['failed_task_stages'], {'carry': 1})
        self.assertEqual(report['families']['nominal_zero']['strict']['planned'], 2)
        self.assertEqual(len(report['missing_pairs']), 4)
        json.dumps(report, allow_nan=False)

    def test_no_contact_is_na_not_a_zero_force_win(self):
        report = assemble(models(), ['c0'], [row('esn1', exposed=False), row('esn2'), row('zero', force=12)])
        contact = report['families']['esn']['contacts']['rod']
        self.assertEqual(contact['full_horizon_exposed'], 1)
        self.assertEqual(contact['metrics']['peak_force_n']['mean'], 10)
        paired = report['esn_minus_baseline']['nominal_zero']['jointly_strict_full_exposed_contacts']['rod']['peak_force_n']
        self.assertEqual(paired['paired_cells'], 1)
        self.assertEqual(paired['difference'], -2)
        self.assertEqual(paired['right_seed_count'], 1)

    def test_short_failure_does_not_reduce_full_mean(self):
        short = row('esn1', success=False, full=False)
        short['metrics']['rmse_mm'] = .001
        report = assemble(models(), ['c0'], [short, row('esn2'), row('zero')])
        esn = report['families']['esn']
        self.assertEqual(esn['full_horizon_metrics']['rmse_mm']['mean'], 1)
        self.assertEqual(esn['short_horizon_metrics']['rmse_mm']['mean'], .001)
        self.assertEqual(esn['strict']['successes'], 1)
        recovery = esn['recovery']['rod']
        self.assertEqual(recovery['full_horizon']['right_censored'], 1)
        self.assertEqual(recovery['short_horizon']['right_censored'], 1)

    def test_outcome_subset_is_explicit(self):
        report = assemble(models(), ['c0'], [row('esn1'), row('esn2'), row('zero')])
        paired = report['esn_minus_baseline']['nominal_zero']
        self.assertFalse(paired['strict_success']['outcome_conditioned'])
        self.assertTrue(paired['full_horizon_metrics']['rmse_mm']['outcome_conditioned'])
        self.assertTrue(paired['jointly_strict_full_exposed_contacts']['rod']['peak_force_n']['outcome_conditioned'])

    def test_mismatched_training_seed_rejected(self):
        extra = [dict(name='mlp1', category='mlp', seed=2), dict(name='mlp2', category='mlp', seed=3)]
        with self.assertRaisesRegex(ValueError, 'seed identities'):
            assemble(models()+extra, ['c0'], [])

    def test_duplicate_candidate_condition_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            assemble(models(), ['c0'], [row('esn1'), row('esn1')])
        with self.assertRaisesRegex(ValueError, 'one model per seed'):
            assemble(models()+[dict(name='esn1alt', category='esn', seed=1)], ['c0'], [])

    def test_empty_contact_pairs_are_not_dropped_from_report(self):
        report = assemble(models(), ['c0'], [row('esn1', success=False), row('esn2', success=False), row('zero')])
        paired = report['esn_minus_baseline']['nominal_zero']['jointly_strict_full_exposed_contacts']['rod']['peak_force_n']
        self.assertIsNone(paired['difference'])
        self.assertEqual(paired['paired_cells'], 0)
        self.assertIn('nominal_zero', markdown(report))

    def test_publication_loader_without_audit_keeps_missing_and_never_opens_sealed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); phase = root/'final'; phase.mkdir()
            def write(path, data):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(data))
            write(root/'PROTOCOL.json', {})
            write(root/'FINAL_UNSEAL_RECEIPT.json', dict(model_lock_sha256='lock',
                protocol_sha256=sha(root/'PROTOCOL.json'), sealed_condition_sha256='sealed', output=str(phase)))
            plans = [dict(candidate=c['name'], condition=f'c{d:02d}') for d in range(24) for c in models()]
            write(phase/'PLANNED.json', dict(model_lock_sha256='lock', rows=[
                dict(candidate=p['candidate'], condition_id=p['condition'], queue=i%4) for i,p in enumerate(plans)]))
            write(phase/'execution.json', dict(model_lock_sha256='lock', status='failed_preserved',
                planned_sha256=sha(phase/'PLANNED.json')))
            for index in range(4):
                subset = plans[index::4]
                if index == 3:
                    continue  # Failed before queue initialization; its full denominator remains.
                write(phase/f'queue_{index}/execution.json', dict(model_lock_sha256='lock',
                    status='failed_preserved', planned=subset,
                    rows=[dict(candidate=subset[0]['candidate'], condition_id=subset[0]['condition'], name='failed', returncode=1)]))
            # There is deliberately no sealed directory, raw trace or model.
            with patch('research72_comparison_report_20261003.verify_lock', return_value=(
                dict(candidates=models()), dict(sealed_condition_sha256='sealed', formal_model_sha256='model'))):
                candidates, conditions, rows, evidence, failures = load_evidence(root, phase, root/'lock', 'lock')
            self.assertEqual(len(conditions), 24)
            self.assertEqual(rows, [])
            self.assertEqual(len(failures), 4)
            report = assemble(candidates, conditions, rows)
            self.assertEqual(report['planned'], 72)
            self.assertEqual(report['audited'], 0)
            self.assertEqual(report['families']['esn']['strict']['planned_rate_bounds'], [0., 1.])

            # Add one fully linked synthetic audit, then corrupt its metric
            # receipt. A model's self-reported success alone is insufficient.
            qpath = phase/'queue_0/execution.json'; q = json.loads(qpath.read_text())
            first = q['rows'][0]; run = qpath.parent/first['name']
            write(run/'AUDIT.json', {'synthetic': True})
            first.update(audit_sha256=sha(run/'AUDIT.json'), trace_sha256='trace')
            write(qpath, q)
            write(run/'FINAL_ROLE.json', dict(test_only=True, candidate=first['candidate'],
                condition={'id': first['condition_id']}, model_lock_sha256='lock',
                protocol_sha256=sha(root/'PROTOCOL.json')))
            audit = dict(run=str(run.resolve()), frozen_source_hashes_verified=True,
                actuator_amplitude_and_command_slew_valid=True, independent_contact_sidecar_verified=True,
                model_sha256='model', trace_sha256='trace', audit_sha256=first['audit_sha256'],
                task_success=True, strict_success=True, full_horizon=True,
                rmse_mm=1., peak_torque_nm=1., peak_speed_mps=1.)
            analysis = phase/'queue_0_analysis'
            write(analysis/'INDEPENDENT_AUDIT.json', dict(rows=[audit], pending=[]))
            metric_path = analysis/(first['name']+'.metrics.json')
            metric = metrics(); metric.update(trace_sha256='trace', model_sha256='model')
            write(metric_path, metric)
            write(analysis/'execution.json', dict(status='complete', phase_execution_sha256=sha(qpath),
                outputs={p.name: sha(p) for p in (metric_path, analysis/'INDEPENDENT_AUDIT.json')}))
            with patch('research72_comparison_report_20261003.verify_lock', return_value=(
                dict(candidates=models()), dict(sealed_condition_sha256='sealed', formal_model_sha256='model'))):
                _, _, rows, _, failures = load_evidence(root, phase, root/'lock', 'lock')
                self.assertEqual(len(rows), 1)
                self.assertEqual(len(failures), 3)
                metric['peak_torque_nm'] = 0.
                write(metric_path, metric)
                with self.assertRaises(AssertionError):
                    load_evidence(root, phase, root/'lock', 'lock')


if __name__ == '__main__':
    unittest.main()
