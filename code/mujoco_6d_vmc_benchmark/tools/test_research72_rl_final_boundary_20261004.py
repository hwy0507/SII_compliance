"""Prospective cutoff guards and real signal handling in a disposable child."""
import copy
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest

from research72_rl_final_boundary_20261004 import (
    AMENDMENT, STAGE, check_target, final_policy, find_command, selected_boundary, sha, signal_stop)


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.root=Path('/research');self.campaign=self.root/'rl_office_adaptation_v2'
        self.model='parameter_vmc_301';self.stage='cumulative_0071500'
        self.command=['python','/frozen/tools/research72_train_rl_20261003.py','--root',str(self.root),
            '--output',str(self.campaign/'queue_0'/self.model/self.stage),'--steps','80000',
            '--stop-at-step','71500','--seed','301']
        self.parent=dict(pid=123,queue=0,argv=['python','/frozen/tools/research72_rl_campaign_20261003.py'])
        self.info=dict(pid=456,parent=123,uid=os.getuid(),argv=self.command,
                       caught=1<<(signal.SIGUSR1-1),start_ticks=10)

    def check(self):
        check_target(self.info,self.command,self.parent,self.root,self.campaign,self.model,self.stage)

    def test_valid_excess_stage(self): self.check()

    def test_target_training_round_cannot_be_signaled(self):
        self.stage=STAGE
        with self.assertRaises(AssertionError): self.check()

    def test_wrong_parent_or_absent_handler_rejected(self):
        original=copy.deepcopy(self.info)
        for key,value in [('parent',999),('caught',0),('uid',os.getuid()+1)]:
            self.info=copy.deepcopy(original);self.info[key]=value
            with self.assertRaises(AssertionError): self.check()

    def test_wrong_runtime_or_seed_rejected(self):
        self.command[1]='/other/research72_train_rl_20261003.py'
        with self.assertRaises(AssertionError): self.check()
        self.command[1]='/frozen/tools/research72_train_rl_20261003.py';self.command[-1]='302'
        with self.assertRaises(AssertionError): self.check()

    def test_incomplete_or_early_stopped_boundary_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            q=Path(directory); model=q/self.model; stage=model/STAGE;stage.mkdir(parents=True)
            proto=stage/'PROTOCOL.json';proto.write_text(json.dumps(dict(segment_step_limit=49500,maximum_new_physics_steps=80000)))
            cp=str(stage/'checkpoint');execution=stage/'execution.json'
            manifest=model/(STAGE+'_CHECKPOINT.json')
            data=dict(status='complete',stop_reason='remaining_budget_less_than_one_full_episode',
                      steps=49000,checkpoint_rows=[dict(path=cp)])
            manifest.write_text(json.dumps(dict(checkpoint=cp,cumulative_physics_steps=49000,
                training_protocol=str(proto),training_protocol_sha256=sha(proto))))
            execution.write_text(json.dumps(data))
            row=dict(name=self.model,segments=[dict(stage=STAGE,returncode=0,cumulative_steps=49000,execution_sha256=sha(execution))])
            self.assertEqual(selected_boundary(q,row)['selected_steps'],49000)
            row['segments'].append(dict(stage='cumulative_0080000',cumulative_steps=51000))
            row['latest_manifest']='/later/unused/checkpoint.json'
            self.assertEqual(selected_boundary(q,row)['selected_steps'],49000)
            for key,value in [('stop_reason','requested'),('status','running'),('steps',47000)]:
                changed=dict(data,**{key:value});execution.write_text(json.dumps(changed))
                row['segments'][0]['execution_sha256']=sha(execution)
                with self.assertRaises(AssertionError): selected_boundary(q,row)

    @unittest.skipUnless(hasattr(os,'pidfd_open') and hasattr(signal,'pidfd_send_signal'),'Linux pidfd required')
    def test_exact_signal_allows_own_disposable_child_to_finish(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);campaign=root/'rl_office_adaptation_v2'
            script=root/'research72_train_rl_20261003.py'
            script.write_text('import signal,time\nstop=False\ndef request(*args):\n global stop\n stop=True\nsignal.signal(signal.SIGUSR1,request)\nprint("ready",flush=True)\nend=time.monotonic()+1.0\nwhile time.monotonic()<end: time.sleep(.01)\nprint("finished" if stop else "unsignaled",flush=True)\n')
            command=[sys.executable,str(script),'--root',str(root),'--output',str(campaign/'queue_0'/self.model/self.stage),
                     '--steps','80000','--stop-at-step','71500','--seed','301']
            parent=dict(pid=os.getpid(),queue=0,argv=[sys.executable,str(root/'research72_rl_campaign_20261003.py')])
            with subprocess.Popen(command,stdout=subprocess.PIPE,text=True) as child:
                self.assertEqual(child.stdout.readline().strip(),'ready')
                info=find_command(command);self.assertIsNotNone(info)
                self.assertTrue(signal_stop(info,command,parent,root,campaign,self.model,self.stage))
                self.assertEqual(child.stdout.readline().strip(),'finished')
                self.assertEqual(child.wait(timeout=5),0)

    def test_final_policy_requires_complete_hash_bound_closure(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); campaign=root/'rl_office_adaptation_v2';output=root/'boundary'
            def write(path,data):
                path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data))
            self.assertIsNone(final_policy(root,campaign))
            write(root/'PROTOCOL.json',{})
            jobs=[dict(name=f'model_{i}') for i in range(15)]
            write(campaign/'SPECIFICATION.json',dict(jobs=jobs))
            amendment=dict(protocol_sha256=sha(root/'PROTOCOL.json'),output=str(output),
                scope='outcome_independent_common_rl_final_boundary',active_campaign=campaign.name,
                selected_stage=STAGE,selected_step_limit=49500,all_fifteen_models_required=True,
                selection_uses_rewards_or_task_results=False,sealed_contents_read=False,
                specification_sha256=sha(campaign/'SPECIFICATION.json'))
            for name in ('registration','forecast','governor_source'):
                path=root/name;write(path,{})
                amendment[name]=str(path);amendment[name+'_sha256']=sha(path)
            write(root/AMENDMENT,amendment)
            with self.assertRaises(FileNotFoundError):final_policy(root,campaign)
            queues=[]
            for index in range(3):
                path=campaign/f'queue_{index}/execution.json';write(path,dict(status='complete'))
                queues.append(dict(path=str(path),sha256=sha(path)))
            closure=dict(status='complete',amendment_sha256=sha(root/AMENDMENT),
                source_sha256=amendment['governor_source_sha256'],queue_executions=queues,models=jobs)
            write(output/'CLOSURE.json',closure)
            execution=dict(status='complete',dry_run=False,amendment_sha256=sha(root/AMENDMENT),
                source_sha256=amendment['governor_source_sha256'],closure_sha256=sha(output/'CLOSURE.json'))
            write(output/'execution.json',execution)
            self.assertEqual(len(final_policy(root,campaign)['closure']['models']),15)
            write(root/'governor_source',dict(tampered=True))
            with self.assertRaises(AssertionError):final_policy(root,campaign)
            write(root/'governor_source',{})
            write(output/'execution.json',dict(execution,status='watching'))
            with self.assertRaises(AssertionError):final_policy(root,campaign)
            write(output/'execution.json',execution)
            closure['queue_executions']=[queues[0]]*3
            write(output/'CLOSURE.json',closure)
            write(output/'execution.json',dict(execution,closure_sha256=sha(output/'CLOSURE.json')))
            with self.assertRaises(AssertionError):final_policy(root,campaign)


if __name__=='__main__': unittest.main()
