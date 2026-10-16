"""Continuation must preserve four distinct checkpoints and reject partial stages."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rl_goal_stage_20261016 import (completed_stage_checkpoints, digest, manifest,
    prepare_next, read, seal_preflight, verify_inputs, verify_preflight, write)


class StageContinuationTests(unittest.TestCase):
    def fixture(self, base):
        parent=base/'protocol'
        parent.mkdir()
        write(parent/'PROTOCOL.json',{'budgets':{'rl_steps_per_family_seed':1000000}})
        old=base/'old'
        (old/'source/tools').mkdir(parents=True)
        (old/'source/tools/train_v4_recovery_rl_20261016.py').write_text('frozen trainer\n')
        (old/'source/tools/baseline_repair_worker_20261008.py').write_text('frozen physics worker\n')
        (old/'parameter_n25').mkdir()
        (old/'parameter_n25/official_parameter_agent.py').write_text('frozen adapter\n')
        jobs=[]
        for controller in (None,'impedance','admittance','vmc'):
            name=controller or 'direct'
            jobs.append(dict(name=name,controller=controller,seed=5,reward='office_task',
                reward_variant='original',hp='historical',inherited_steps=0,limit=11000,
                checkpoint=None,credit_migration=False,output=str(old/name),unit=name))
        reg=dict(schema='sii-rl-persistent-goal-stage-v1',run_root=str(old),
            source=str(old/'source'),source_manifest=manifest(old/'source'),
            parameter_source=str(old/'parameter_n25'),parameter_manifest=manifest(old/'parameter_n25'),
            parent_root=str(parent),parent_protocol_sha256=digest(parent/'PROTOCOL.json'),
            compute_host='airpig',jobs=jobs,new_interactions_per_family=11000,optimizer_schedule_steps=1000000,
            resources=dict(cpu='1',simulators=1,numerical_threads=1,memory_max=3*1024**3,swap_max=0))
        write(old/'REGISTRATION.json',reg)
        state=dict(status='finite_stage_complete',active=None,
            registration_sha256=digest(old/'REGISTRATION.json'),jobs=[])
        for job in jobs:
            output=Path(job['output'])
            cp=output/'checkpoint_0011000'
            cp.mkdir(parents=True)
            write(cp/'office_runner.json',dict(step=11000,episode_boundary=True,pending_transition=None))
            (cp/'actor.bin').write_bytes(job['name'].encode())
            checked=dict(path=str(cp),step=11000,episode=8,hashes=manifest(cp))
            write(output/'execution.json',dict(status='complete',stop_reason='step_budget',steps=11000,
                rows=[dict(episode=i,ended_utc='closed',steps=1375) for i in range(8)],checkpoint_rows=[checked]))
            write(output/'PROTOCOL.json',dict(protocol_sha256=reg['parent_protocol_sha256'],
                goal_registration_sha256=digest(old/'REGISTRATION.json'),agent_config={'n_step':25},
                utd=1,controller=job['controller'],seed=5,reward_variant='original',hyperparameter_id='historical'))
            state['jobs'].append(dict(job=job['name'],returncode=0,stop_reason='step_budget',
                steps=11000,checkpoint=checked))
        write(old/'execution.json',state)
        return old,reg,state

    def test_preserves_each_family_and_frozen_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            old,reg,state=self.fixture(base)
            before=manifest(old)
            new=prepare_next(old,base/'next')
            self.assertEqual(manifest(old),before)
            self.assertEqual(set(new['preflight_required_jobs']),{'direct','impedance','admittance','vmc'})
            for job in new['jobs']:
                self.assertEqual(Path(job['checkpoint']).parent.name,job['name'])
                self.assertEqual(job['inherited_steps'],11000)
                self.assertEqual(job['limit'],22000)
                self.assertFalse(job['credit_migration'])
            for filename in ('train_v4_recovery_rl_20261016.py','baseline_repair_worker_20261008.py'):
                self.assertEqual(digest(old/'source/tools'/filename),digest(base/'next/source/tools'/filename))
            self.assertEqual(new['parameter_manifest'],reg['parameter_manifest'])
            self.assertFalse((base/'next/LAUNCH.json').exists())
            verify_inputs(new)
            with self.assertRaises(AssertionError):
                prepare_next(old,base/'next')

    def test_rejects_running_failed_missing_or_incomplete_family(self):
        with tempfile.TemporaryDirectory() as tmp:
            old,reg,state=self.fixture(Path(tmp))
            for mutation in (dict(state,status='running'),dict(state,active={'job':'direct'}),
                             dict(state,jobs=state['jobs'][:-1])):
                with self.assertRaises(AssertionError):
                    completed_stage_checkpoints(reg,mutation)
            bad=deepcopy(state)
            bad['jobs'][2]['returncode']=1
            with self.assertRaises(AssertionError):
                completed_stage_checkpoints(reg,bad)
            path=old/'vmc/execution.json'
            execution=read(path)
            execution['rows'][-1].pop('ended_utc')
            write(path,execution)
            with self.assertRaises(AssertionError):
                completed_stage_checkpoints(reg,state)

    def test_rejects_checkpoint_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            old,reg,state=self.fixture(Path(tmp))
            (old/'admittance/checkpoint_0011000/actor.bin').write_bytes(b'wrong weights')
            with self.assertRaises(ValueError):
                completed_stage_checkpoints(reg,state)

    def test_all_four_preflights_required_and_hash_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            old,_,_=self.fixture(base)
            root=base/'next'
            reg=prepare_next(old,root)
            for index,job in enumerate(reg['jobs']):
                write(root/f'CREDIT_PREFLIGHT_{job["name"]}.json',dict(status='passed',
                    registration_sha256=digest(root/'REGISTRATION.json'),job=job['name'],
                    checkpoint=job['checkpoint'],checkpoint_hashes=job['checkpoint_hashes'],
                    checkpoint_hashes_unchanged=True,inherited_steps=11000,actual_n_step=25,
                    restored_raw_replay_count=11000,finite_update_metrics=True,
                    terminal_windows_match=True,no_cross_episode_bootstrap=True))
                if index<3:
                    with self.assertRaises(FileNotFoundError):
                        seal_preflight(root)
                    self.assertFalse((root/'CREDIT_PREFLIGHT.json').exists())
            seal_preflight(root)
            verify_preflight(reg)
            path=root/'CREDIT_PREFLIGHT_vmc.json'
            result=read(path)
            result['checkpoint']=reg['jobs'][0]['checkpoint']
            write(path,result)
            with self.assertRaises(AssertionError):
                verify_preflight(reg)


if __name__=='__main__':
    unittest.main()
