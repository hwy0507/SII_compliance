import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from research72_final_delivery_20261004 import ready, replay_plan, run_delivery


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.transition = self.root/'transition'; self.phase = self.root/'final'
        self.out = self.root/'delivery'; self.out.mkdir()
        self.calls = []
        self.candidates = [dict(name='model_'+str(i), category='synthetic',
            **(dict(adapted_rl=dict(manifest='m'+str(i), parameter_source='source')) if i < 15 else {}))
            for i in range(38)]
        self.rows = [dict(candidate='model_0', condition_id='final_0', run='failed_short_run',
                          metrics=dict(task_success=False, strict_success=False, full_horizon=False))]

    def write(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data))

    def test_live_predecessor_waits_without_final_read(self):
        self.write(self.transition/'execution.json', dict(status='waiting_for_predecessors'))
        self.assertFalse(ready(self.transition, self.phase, lambda _: True))
        self.assertFalse(self.phase.exists())

    def test_dead_predecessor_is_not_endless_wait(self):
        self.write(self.transition/'execution.json', dict(status='running_final_evaluation'))
        with self.assertRaises(AssertionError): ready(self.transition, self.phase, lambda _: False)

    def test_failed_final_can_be_reported_only_after_terminal_batch(self):
        self.write(self.transition/'execution.json', dict(status='failed_preserved'))
        with self.assertRaises(AssertionError): ready(self.transition, self.phase, lambda _: True)
        self.write(self.phase/'execution.json', dict(status='running'))
        with self.assertRaises(AssertionError): ready(self.transition, self.phase, lambda _: True)
        self.write(self.phase/'execution.json', dict(status='failed_preserved'))
        self.assertTrue(ready(self.transition, self.phase, lambda _: False))

    def test_plan_keeps_short_failures_and_missing_models(self):
        plan = replay_plan(self.candidates, self.rows)
        self.assertEqual(len(plan), 15)
        self.assertEqual(plan[0]['runs'], ['failed_short_run'])
        self.assertEqual(sum(not p['runs'] for p in plan), 14)

    def test_missing_model_and_duplicate_observation_rejected(self):
        with self.assertRaises(AssertionError): replay_plan(self.candidates[:-1], self.rows)
        with self.assertRaises(AssertionError): replay_plan(self.candidates, self.rows*2)

    def execute(self, label, command, fail_replay=False, fail_figures=False):
        self.calls.append((label, command))
        target = Path(command[command.index('--output')+1])
        if label.startswith('replay_'):
            self.write(target, dict(status='failed_preserved' if fail_replay else 'complete'))
            return int(fail_replay)
        if label == 'comparison':
            self.write(target/'REPORT.json', dict(audited=1, independent_rl_actor_replay=dict(status='incomplete')))
            (target/'MATRIX.md').write_text('Synthetic report, not a research result')
        if label == 'figures': return int(fail_figures)
        if label == 'media': self.write(target/'execution.json', dict(status='complete_with_missing'))
        return 0

    def deliver(self, execute=None):
        self.write(self.transition/'MODEL_LOCK.json', {})
        runtime = Path(__file__).resolve().parents[1]
        with patch('research72_comparison_report_20261003.load_evidence',
                   return_value=(self.candidates, [str(i) for i in range(24)], self.rows, [], [])):
            return run_delivery(runtime, self.root, self.transition, self.phase, self.out,
                                execute or self.execute, lambda: None)

    def test_partial_evidence_is_not_complete_and_order_is_fixed(self):
        result = self.deliver()
        self.assertEqual(result['status'], 'complete_with_gaps')
        self.assertEqual([x[0] for x in self.calls], ['replay_model_0','comparison','figures','media'])
        self.assertFalse((self.root/'sealed').exists())
        self.assertEqual(self.calls[0][1][self.calls[0][1].index('--runs')+1], 'failed_short_run')

    def test_replay_and_figure_failure_do_not_discard_other_outputs(self):
        result = self.deliver(lambda label, cmd: self.execute(label, cmd, fail_replay=True, fail_figures=True))
        self.assertEqual(result['status'], 'complete_with_gaps')
        comparison = next(cmd for label, cmd in self.calls if label == 'comparison')
        self.assertTrue(comparison[-1].endswith('model_0.replay.json'))
        self.assertEqual(self.calls[-1][0], 'media')

    def test_bad_report_stops_figures_and_media_without_retry(self):
        def execute(label, command):
            if label == 'comparison': self.calls.append((label, command)); return 1
            return self.execute(label, command)
        with self.assertRaises(AssertionError): self.deliver(execute)
        self.assertEqual([x[0] for x in self.calls], ['replay_model_0','comparison'])

    def test_complete_requires_every_model_and_final_coverage(self):
        self.rows = [dict(candidate=c['name'], condition_id=f'final_{i:02d}', run=c['name']+str(i))
                     for c in self.candidates for i in range(24)]
        def execute(label, command):
            result = self.execute(label, command)
            target = Path(command[command.index('--output')+1])
            if label == 'comparison':
                self.write(target/'REPORT.json', dict(audited=912,
                    independent_rl_actor_replay=dict(status='complete')))
            if label == 'media': self.write(target/'execution.json', dict(status='complete'))
            return result
        result = self.deliver(execute)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(len([x for x in self.calls if x[0].startswith('replay_')]), 15)
        self.assertIn('researcher review', result['scope'])


if __name__ == '__main__': unittest.main()
