"""Diagnostic compute counts, but is never a task-success/failure denominator."""
import json
from pathlib import Path
import tempfile
import unittest
from research72_exposure_ledger_20261003 import physics, sha


class DiagnosticAccountingTests(unittest.TestCase):
    def check_role(self, role, success):
        with tempfile.TemporaryDirectory() as directory:
            phase = Path(directory); queue = phase/'queue_0'; run = queue/'example'
            run.mkdir(parents=True)
            (phase/'execution.json').write_text('{"status":"complete"}')
            (run/'AUDIT.json').write_text(json.dumps(dict(task_success=success, strict_success=success)))
            (run/'rollout.json').write_text(json.dumps(dict(full_task_horizon_completed=False,
                abort_reason=None, final_task_stage='lift')))
            row = dict(name='example', role=role, returncode=0,
                started_utc='2026-10-03T00:00:00+00:00', ended_utc='2026-10-03T00:00:10+00:00',
                audit_sha256=sha(run/'AUDIT.json'), trace_sha256='synthetic')
            (queue/'execution.json').write_text(json.dumps(dict(status='complete', rows=[row])))
            return physics(phase)['totals']

    def test_short_diagnostic_and_known_success_rehearsal_are_not_task_trials(self):
        for role, success in [('numerical_diagnostic', False), ('diagnostic_rehearsal', True)]:
            totals = self.check_role(role, success)
            self.assertEqual(totals['diagnostic_attempted'], 1)
            self.assertEqual(totals['task_evaluation_completed'], 0)
            self.assertEqual(totals['task'], 0)
            self.assertEqual(totals['failed_task'], 0)
            self.assertEqual(totals['wall_seconds_completed'], 10)
            self.assertEqual(totals['completed'], 1)

    def test_ordinary_failed_trial_remains_in_denominator(self):
        totals = self.check_role('development', False)
        self.assertEqual(totals['task_evaluation_completed'], 1)
        self.assertEqual(totals['failed_task'], 1)
        self.assertEqual(totals['diagnostic_attempted'], 0)


if __name__ == '__main__':
    unittest.main()
