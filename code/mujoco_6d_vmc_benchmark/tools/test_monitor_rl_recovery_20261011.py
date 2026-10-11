import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from overnight_baseline_coordinator_20261010 import write
from monitor_rl_recovery_20261011 import snapshot


class RecoveryMonitorTests(unittest.TestCase):
    def test_failed_receipt_overrides_successful_systemd_exit(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);outer=root/'outer';outer.mkdir();run=root/'run';run.mkdir()
            write(outer/'execution.json',dict(status='failed_preserved'))
            with patch('monitor_rl_recovery_20261011.unit_state',return_value=dict(ActiveState='inactive',Result='success')):
                result=snapshot(outer,run,'unit')
            self.assertTrue(result['failures'])

    def test_actual_step_and_checkpoint_are_reported_and_staleness_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);outer=root/'outer';outer.mkdir();run=root/'run';run.mkdir();train=run/'train';train.mkdir()
            write(outer/'execution.json',dict(status='running_rl'))
            write(run/'execution.json',dict(status='running',active={'0':dict(target=str(train),unit='worker',training=True)}))
            write(train/'execution.json',dict(status='running',steps=110250,updates=210000,episodes=82,
                                            checkpoint_rows=[dict(step=110000,path='checkpoint')]))
            with patch('monitor_rl_recovery_20261011.unit_state',return_value=dict(ActiveState='active',Result='success')):
                result=snapshot(outer,run,'unit')
                self.assertEqual(result['active'][0]['steps'],110250)
                self.assertFalse(result['failures'])
                old=time.time()-1300;os.utime(train/'execution.json',(old,old))
                self.assertTrue(snapshot(outer,run,'unit')['failures'])

    def test_missing_terminal_receipt_with_dead_service_is_failure(self):
        with tempfile.TemporaryDirectory() as d:
            with patch('monitor_rl_recovery_20261011.unit_state',return_value=dict(ActiveState='inactive')):
                self.assertTrue(snapshot(Path(d),Path(d),'unit')['failures'])


if __name__=='__main__':unittest.main()
