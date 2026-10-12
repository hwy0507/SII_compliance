"""Regression checks for safe one-node completion; no MuJoCo or GPU needed."""
import tempfile
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from complete_rl_node_20261012 import managed, validate_parent
from office_v7_uniform24_20261008 import read


class CompletionSafety(unittest.TestCase):
    def test_only_closed_incomplete_node_is_accepted(self):
        validate_parent(dict(status='complete',stop_reason='deadline',steps=97625),165000)
        for state in (dict(status='running',stop_reason='deadline',steps=97625),
                      dict(status='complete',stop_reason='step_budget',steps=97625),
                      dict(status='complete',stop_reason='deadline',steps=165000)):
            with self.assertRaises(AssertionError):validate_parent(state,165000)

    def test_child_failure_propagates_and_preserves_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);target=out/'attempt';state=dict(registration_sha256='test',active={})
            with (out/'lock').open('a') as lock, patch('complete_rl_node_20261012.subprocess.run',
                    return_value=subprocess.CompletedProcess([],23)):
                with self.assertRaises(AssertionError):
                    managed(target,['false'],source=out,env={},lock=lock,state=state,out=out)
            receipt=read(out/'attempt.execution.json')
            self.assertEqual(receipt['returncode'],23)
            self.assertEqual(receipt['status'],'failed_preserved')
            self.assertEqual(state['active'],{})
            before=(out/'attempt.execution.json').read_bytes()
            with (out/'lock').open('a') as lock:
                with self.assertRaises(AssertionError):
                    managed(target,['true'],source=out,env={},lock=lock,state=state,out=out)
            self.assertEqual(before,(out/'attempt.execution.json').read_bytes())

    def test_spawn_failure_is_not_success(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);state=dict(registration_sha256='test',active={})
            with (out/'lock').open('a') as lock, patch('complete_rl_node_20261012.subprocess.run',
                    side_effect=OSError('bus unavailable')):
                with self.assertRaises(OSError):
                    managed(out/'attempt',['missing'],source=out,env={},lock=lock,state=state,out=out)
            receipt=read(out/'attempt.execution.json')
            self.assertEqual(receipt['status'],'failed_preserved')
            self.assertIn('bus unavailable',receipt['error'])


if __name__=='__main__':unittest.main()
