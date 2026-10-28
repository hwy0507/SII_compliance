import os
import signal
import subprocess
import sys
import unittest
from research72_slot_handoff_20261004 import idle_pause,process_info,stopped


@unittest.skipUnless(hasattr(os,'pidfd_open') and hasattr(signal,'pidfd_send_signal'),'pidfd required')
class HandoffTests(unittest.TestCase):
    def test_only_idle_unleased_child_pauses_and_resumes(self):
        with subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']) as child:
            fd=os.pidfd_open(child.pid)
            try:
                info=process_info(child.pid)
                self.assertFalse(idle_pause(info,fd,lambda:{child.pid:0}))
                self.assertFalse(stopped(child.pid))
                self.assertTrue(idle_pause(info,fd,lambda:{}))
                self.assertTrue(stopped(child.pid))
                signal.pidfd_send_signal(fd,signal.SIGCONT)
            finally:
                signal.pidfd_send_signal(fd,signal.SIGCONT);child.terminate();child.wait(timeout=5);os.close(fd)


if __name__=='__main__':unittest.main()
