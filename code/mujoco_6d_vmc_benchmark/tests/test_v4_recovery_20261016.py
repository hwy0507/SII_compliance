"""Regressions for the observed double-update and unsafe recovery dispatch."""
import ast
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
import math
from pathlib import Path
import tempfile
import unittest

TOOLS=Path(__file__).resolve().parents[1]/'tools'
spec=importlib.util.spec_from_file_location('recovery_control',TOOLS/'rl_recovery_control_20261016.py')
control=importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


class RecoveryTests(unittest.TestCase):
    def test_actual_trainer_update_loop_honors_registration(self):
        tree=ast.parse((TOOLS/'train_v4_recovery_rl_20261016.py').read_text())
        # Execute the optimizer loop that actually calls agent.update, not a
        # separate test implementation. The historical range(2) fails UTD=1.
        loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and
                  any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and
                      ast.unparse(x.func)=='agent.update' for x in ast.walk(n)))
        class Agent:
            updates=0
            def update(self,batch):
                self.updates+=1
                return {'loss':1.}
        class Replay:
            def sample(self,n):return {}
        for utd in (1,2):
            with self.subTest(utd=utd):
                agent=Agent();log=io.StringIO()
                env=dict(utd=utd,agent=agent,replay=Replay(),BATCH_SIZE=256,step=5000,
                         flatten_metrics=lambda x:x,np=type('NP',(),{'isfinite':staticmethod(math.isfinite)}),
                         json=json,optlog=log)
                exec(compile(ast.Module(body=[loop],type_ignores=[]),'<trainer>','exec'),env)
                self.assertEqual(agent.updates,utd)
                self.assertEqual(len(log.getvalue().splitlines()),utd)

    def test_deadline_and_memory_and_duplicates_fail_closed(self):
        now=datetime.now(timezone.utc);deadline=now+timedelta(hours=1)
        self.assertEqual(control.dispatch_reason(now,now,8*control.GIB,[]),'dispatch_deadline_elapsed')
        self.assertEqual(control.dispatch_reason(deadline,now,8*control.GIB,[123]),'existing_rl_worker')
        self.assertEqual(control.dispatch_reason(deadline,now,3*control.GIB,[]),'insufficient_memory_with_reserve')
        self.assertIsNone(control.dispatch_reason(deadline,now,control.MEMORY_MAX+control.RESERVE,[]))

    def test_proc_detection_ignores_search_command_but_finds_trainer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for pid,comm,cmd in [('10','bash','rg train_v4_recovery_rl_20261016.py'),
                                 ('11','python','python\0/path/train_v4_recovery_rl_20261016.py\0--root\0/run')]:
                p=root/pid;p.mkdir();(p/'comm').write_text(comm);(p/'cmdline').write_bytes(cmd.encode())
            self.assertEqual(control.active_workers(root),[11])

    def test_launch_uses_host_interpreter_and_hard_subtree_limits(self):
        reg=dict(parent_root='/run',unit='test',output='/new',seed=1,maximum_steps=1000000,checkpoint='/cp')
        command=control.systemd_command(reg)
        self.assertTrue(control.PYTHON.is_file())
        for item in ['--property=MemoryMax=3G','--property=MemorySwapMax=0','--setenv=SII_RL_UTD=1',str(control.PYTHON)]:
            self.assertIn(item,command)
        self.assertNotIn('--scope',command)  # service lifetime is independent of launch shell

    def test_checkpoint_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cp=root/'checkpoint';cp.mkdir()
            runner=cp/'office_runner.json';runner.write_text(json.dumps(dict(step=10,episode_boundary=True,pending_transition=None)))
            (cp/'weights').write_bytes(b'valid')
            row=dict(path=str(cp),step=10,hashes={n:control.digest(cp/n) for n in ['office_runner.json','weights']})
            (root/'execution.json').write_text(json.dumps(dict(checkpoint_rows=[row])))
            self.assertEqual(control.verify_checkpoint(cp)['step'],10)
            (cp/'weights').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):control.verify_checkpoint(cp)


if __name__=='__main__':unittest.main()
