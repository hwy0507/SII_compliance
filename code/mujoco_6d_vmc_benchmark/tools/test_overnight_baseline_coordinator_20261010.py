"""Small coordinator safety checks without starting simulations."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from overnight_baseline_coordinator_20261010 import classical_state, write


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


if __name__ == '__main__':
    unittest.main()
