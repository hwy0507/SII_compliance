"""Small coordinator safety checks without starting simulations."""
import tempfile
import unittest
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from overnight_baseline_coordinator_20261010 import classical_state, write, read, run


class CoordinatorTest(unittest.TestCase):
    def test_failed_classical_search_blocks_rl(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); write(root/'execution.json', {'status':'failed_preserved'})
            with self.assertRaisesRegex(RuntimeError, 'Classical search failed'):
                classical_state(root)

    def test_incomplete_classical_is_waiting_state(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); write(root/'execution.json', {'status':'running','completed':[]})
            self.assertEqual(classical_state(root)['status'], 'running')

    @patch('overnight_baseline_coordinator_20261010.subprocess.run')
    def test_active_rl_detection_is_fail_closed(self, run):
        run.return_value.stdout = 'sii-local-rl-conv-test.service loaded active running\n'
        from overnight_baseline_coordinator_20261010 import active_rl_units
        self.assertTrue(active_rl_units())

    def exercise_handoff(self, exit_code=0, deadline_hours=15):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root/'tools').mkdir()
            # Real subprocess reacquires the same inode with an independent FD.
            child = root/'tools/launch_rl_convergence_20261010.py'
            child.write_text('import fcntl,sys\n'
                f'with open({str(root/"sim.lock")!r},"a") as f:\n'
                ' fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)\n'
                f' sys.exit({exit_code})\n')
            output = root/'out'; output.mkdir()
            classical = root/'classical'; classical.mkdir()
            write(classical/'execution.json', {'status':'complete','completed':[]})
            args=SimpleNamespace(benchmark=root,rl_parent=root,classical_root=classical,
                                 output=output,safety_hours=deadline_hours)
            def prepare(_b,_p,run_root,_d):
                run_root.mkdir(); write(run_root/'REGISTRATION.json', {})
            with patch('overnight_baseline_coordinator_20261010.prepare_rl',side_effect=prepare), \
                 patch('overnight_baseline_coordinator_20261010.active_rl_units',return_value=[]), \
                 patch('overnight_baseline_coordinator_20261010.Path.read_text', autospec=True) as reader:
                original = __import__('io').open
                def content(path, *a, **kw):
                    if str(path)=='/proc/meminfo':return 'MemAvailable: 9000000 kB\n'
                    with original(path,'r') as f:return f.read()
                reader.side_effect=content
                if exit_code:
                    with self.assertRaises(subprocess.CalledProcessError):run(args,root/'sim.lock')
                else:run(args,root/'sim.lock')
            return read(output/'execution.json')

    def test_real_child_can_acquire_released_simulator_lock(self):
        state=self.exercise_handoff()
        self.assertEqual(state['status'],'complete_review_required')
        self.assertEqual(state['rl_returncode'],0)

    def test_real_child_failure_propagates_and_is_preserved(self):
        state=self.exercise_handoff(exit_code=23)
        self.assertEqual(state['status'],'failed_preserved')
        self.assertEqual(state['rl_returncode'],23)

    def test_expired_window_never_dispatches(self):
        state=self.exercise_handoff(deadline_hours=-1)
        self.assertEqual(state['status'],'stopped_at_deadline')


if __name__ == '__main__':
    unittest.main()
