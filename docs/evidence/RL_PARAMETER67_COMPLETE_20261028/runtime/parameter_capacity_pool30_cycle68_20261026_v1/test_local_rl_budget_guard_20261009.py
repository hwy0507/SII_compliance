"""Exercise exact PID identity protection using only owned dummy subprocesses."""
import signal
import subprocess
import sys
import unittest
from local_rl_budget_guard_20261009 import identity, signal_exact


class GuardTests(unittest.TestCase):
    def test_reused_or_changed_identity_is_rejected(self):
        process=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'])
        try:
            actual=identity(process.pid)
            wrong=dict(actual,start_ticks='invalid')
            with self.assertRaises(AssertionError):signal_exact(wrong,signal.SIGTERM)
            self.assertIsNone(process.poll())
            signal_exact(actual,signal.SIGSTOP)
            self.assertIsNone(process.poll())
            signal_exact(actual,signal.SIGCONT)
            signal_exact(actual,signal.SIGTERM)
            self.assertEqual(process.wait(timeout=5),-signal.SIGTERM)
        finally:
            if process.poll() is None: process.kill();process.wait()


if __name__=='__main__':unittest.main()
