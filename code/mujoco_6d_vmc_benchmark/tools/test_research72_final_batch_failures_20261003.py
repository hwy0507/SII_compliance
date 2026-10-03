"""Exercise final coordinator failure handling with synthetic subprocesses."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import research72_final_batch_20261003 as batch


class FinalBatchFailureTests(unittest.TestCase):
    def exercise(self, missing_queue):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); output = root/'final'; (root/'sealed').mkdir()
            def write(path, data):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(data))
            conditions = [dict(id=f'synthetic_{i:02d}', role='heldout') for i in range(24)]
            write(root/'sealed/HELDOUT.json', dict(conditions=conditions))
            protocol = dict(dispatch_deadline_utc='2099-01-01T00:00:00+00:00',
                sealed_condition_sha256=batch.sha(root/'sealed/HELDOUT.json'), formal_model_sha256='synthetic')
            write(root/'PROTOCOL.json', protocol)
            lock = dict(candidates=[dict(name='model', category='synthetic')],
                        completion_receipts=[], runtime_source_sha256={})
            launched = []; audits = []
            def subprocess(command, **kwargs):
                if command[0] == 'systemd-run':
                    index = int(command[-1]); launched.append(index)
                    if missing_queue and index == 0:
                        return SimpleNamespace(returncode=1)
                    phase = output/f'queue_{index}'; rows = []
                    selected = conditions[index::4]
                    for condition in selected[:3] if index == 0 else selected:
                        rows.append(dict(name='model__'+condition['id'], candidate='model',
                            condition_id=condition['id'], audit_sha256='synthetic',
                            audit=dict(task_success=False, strict_success=False)))
                    if index == 0:
                        rows.append(dict(name='model__'+selected[3]['id'], candidate='model',
                            condition_id=selected[3]['id'], returncode=1))
                    write(phase/'execution.json', dict(status='failed_preserved' if index == 0 else 'complete', rows=rows))
                    return SimpleNamespace(returncode=1 if index == 0 else 0)
                self.assertIn('--allow-partial', command)
                phase = Path(command[command.index('--phase')+1]); audits.append(phase.name)
                return SimpleNamespace(returncode=0)
            argv = ['batch', '--root', str(root), '--output', str(output),
                    '--model-lock', str(root/'LOCK.json'), '--lock-sha256', 'synthetic_lock']
            with patch.object(batch, 'verify_lock', return_value=(lock, protocol)), \
                 patch.object(batch, 'no_development_processes'), \
                 patch.object(batch, 'runtime_hashes', return_value={}), \
                 patch.object(batch.subprocess, 'run', side_effect=subprocess), \
                 patch.object(batch.sys, 'argv', argv), \
                 patch.dict(os.environ, {'SII_SOURCE_BASE_COMMIT': 'synthetic'}):
                with self.assertRaisesRegex(AssertionError, 'successful peers'):
                    batch.main()
            summary = json.loads((output/'SUMMARY.json').read_text())
            execution = json.loads((output/'execution.json').read_text())
            self.assertEqual(execution['status'], 'failed_preserved')
            self.assertEqual(summary['expected'], 24)
            self.assertEqual(summary['completed'], 18 if missing_queue else 21)
            self.assertEqual(set(audits), {'queue_1', 'queue_2', 'queue_3'} if missing_queue else {f'queue_{i}' for i in range(4)})
            self.assertEqual(sorted(launched), [0, 1, 2, 3])
            plan = json.loads((output/'PLANNED.json').read_text())
            self.assertEqual(len(plan['rows']), 24)
            self.assertEqual(batch.sha(output/'PLANNED.json'), execution['planned_sha256'])

    def test_failed_queue_does_not_block_completed_peers(self):
        self.exercise(False)

    def test_never_initialized_queue_stays_in_plan(self):
        self.exercise(True)


if __name__ == '__main__':
    unittest.main()
