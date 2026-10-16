"""Selected continuation must preserve exact models and distinct objectives."""
from copy import deepcopy
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from goal_selected_continuation_20261016 import prepare_selected, verify_selected_lineages
from goal_tracking_reward_20261016 import CONFIG
from rl_goal_stage_20261016 import (read, write, digest, manifest, verify_inputs,
    interaction_budget, validate_training_job, prepare_next)
import test_goal_stage_continuation_20261016 as continuation_fixtures


class SelectedContinuationTests(unittest.TestCase):
    def fixture(self, directory, pilot=False):
        directory.mkdir()
        root,reg,state=continuation_fixtures.StageContinuationTests().fixture(directory)
        names=['rl_recovery_control_20261016.py','goal_tracking_reward_20261016.py']
        if pilot:
            names.append('goal_tracking_pilot_20261016.py')
        for name in names:
            shutil.copy2(Path(__file__).resolve().parents[1]/'tools'/name,root/'source/tools'/name)
        reg['source_manifest']=manifest(root/'source')
        reg.update(runtime='/frozen/runtime',python=sys.executable,
                   training_convergence={'window_episodes':32},server_compute=False,acceptance_allowed=False)
        if pilot:
            template=reg['jobs'][0]
            jobs=[];entries=[]
            for suffix in ('control','tracking'):
                name='direct_'+suffix
                output=root/name
                shutil.copytree(root/'direct',output)
                job=dict(template,name=name,output=str(output),unit=name,
                         reward='office_task',reward_variant='task_safety',hp='direct_explore')
                if suffix=='tracking':job['tracking_guidance']=dict(CONFIG)
                execution=read(output/'execution.json')
                cp=execution['checkpoint_rows'][0]
                cp['path']=str(output/'checkpoint_0011000')
                write(output/'execution.json',execution)
                entry=dict(state['jobs'][0],job=name,checkpoint=cp)
                jobs.append(job);entries.append(entry)
            reg.update(jobs=jobs,experiment_kind='fresh_direct_tracking_pilot',maximum_new_interactions=22000)
            state['jobs']=entries
        # Identical frozen task/runtime is required across the separate roots.
        reg['parent_root']=str(directory.parent/'parent')
        Path(reg['parent_root']).mkdir(exist_ok=True)
        write(Path(reg['parent_root'])/'PROTOCOL.json',{'budgets':{'rl_steps_per_family_seed':1000000}})
        reg['parent_protocol_sha256']=digest(Path(reg['parent_root'])/'PROTOCOL.json')
        self.bind(root,reg,state)
        return root

    def bind(self,root,reg,state):
        write(root/'REGISTRATION.json',reg)
        state['registration_sha256']=digest(root/'REGISTRATION.json')
        write(root/'execution.json',state)
        for job in reg['jobs']:
            path=Path(job['output'])/'PROTOCOL.json'
            spec=read(path)
            spec.update(goal_registration_sha256=state['registration_sha256'],
                protocol_sha256=reg['parent_protocol_sha256'],reward={'mode':job['reward']},
                reward_variant=job['reward_variant'],hyperparameter_id=job['hp'])
            if job.get('tracking_guidance'):spec['tracking_guidance']=job['tracking_guidance']
            write(path,spec)

    def setup_selection(self,base):
        four=self.fixture(base/'four')
        pair=self.fixture(base/'pair',pilot=True)
        selection=dict(decision='Synthetic explicit selection; not real reward ranking',methods={
            job['name']:dict(root=str(pair if job['controller'] is None else four),
                job='direct_tracking' if job['controller'] is None else job['name'],
                rationale='Preserve this exact registered training objective and checkpoint')
            for job in read(four/'REGISTRATION.json')['jobs']})
        return four,pair,selection

    def test_four_distinct_lineages_keep_selected_reward_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);four,pair,selection=self.setup_selection(base)
            self.assertFalse((four/'source/tools/goal_tracking_pilot_20261016.py').exists())
            before=(manifest(four),manifest(pair))
            reg=prepare_selected(four,selection,base/'new',22000)
            self.assertEqual((manifest(four),manifest(pair)),before)
            self.assertNotIn('previous_stage',reg)
            self.assertEqual(interaction_budget(reg),22000)
            self.assertEqual(reg['maximum_new_interactions'],88000)
            self.assertEqual(len(reg['preflight_required_jobs']),4)
            self.assertFalse((base/'new/LAUNCH.json').exists())
            self.assertFalse((base/'new/CREDIT_PREFLIGHT.json').exists())
            verify_inputs(reg)
            check=subprocess.run([sys.executable,'-I','-c',
                'import sys; sys.path.insert(0,sys.argv[1]); from rl_goal_stage_20261016 import read,verify_inputs; verify_inputs(read(sys.argv[2]))',
                str(base/'new/source/tools'),str(base/'new/REGISTRATION.json')],cwd=base,
                env=dict(os.environ,PYTHONPATH=''),capture_output=True,text=True,timeout=20)
            self.assertEqual(check.returncode,0,check.stderr)
            self.assertEqual(reg['source_manifest']['tools/goal_tracking_pilot_20261016.py'],
                digest(Path(__file__).resolve().parents[1]/'tools/goal_tracking_pilot_20261016.py'))
            for job in reg['jobs']:
                args=argparse.Namespace(goal_registration=base/'new/REGISTRATION.json',
                    root=Path(reg['parent_root']),steps=1000000,output=Path(job['output']),
                    parameter_source=Path(reg['parameter_source']),controller=job['controller'],
                    reward=job['reward'],reward_variant=job['reward_variant'],hyperparameter_id=job['hp'],
                    seed=job['seed'],stop_at_step=job['limit'],resume_checkpoint=Path(job['checkpoint']))
                validate_training_job(args,read(args.root/'PROTOCOL.json'),reg['parent_protocol_sha256'])
                self.assertEqual(job['inherited_steps'],11000)
                self.assertEqual(job['limit'],33000)
                self.assertFalse(job['credit_migration'])
                self.assertFalse(job['backend_migration'])
                if job['controller'] is None:
                    self.assertEqual(job['tracking_guidance'],CONFIG)
                    self.assertEqual(Path(job['checkpoint']).parent,pair/'direct_tracking')
                else:
                    self.assertNotIn('tracking_guidance',job)
                    self.assertEqual(Path(job['checkpoint']).parent,four/job['name'])

    def test_preflight_cannot_fall_back_to_checkout_for_missing_snapshot_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'source/tools').mkdir(parents=True)
            probe=Path(__file__).resolve().parents[1]/'tools/probe_goal_credit_20261016.py'
            check=subprocess.run([sys.executable,str(probe),'--root',str(root)],
                cwd=root,env=dict(os.environ,PYTHONPATH=''),capture_output=True,text=True,timeout=20)
            self.assertNotEqual(check.returncode,0)
            self.assertIn("ModuleNotFoundError: No module named 'rl_goal_stage_20261016'",check.stderr)

    def test_running_pilot_or_missing_family_rejected_before_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);four,pair,selection=self.setup_selection(base)
            state=read(pair/'execution.json')
            state.update(status='running',active={'job':'direct_tracking'})
            write(pair/'execution.json',state)
            with self.assertRaises(AssertionError):prepare_selected(four,selection,base/'bad')
            self.assertFalse((base/'bad').exists())
            selection['methods'].pop('vmc')
            with self.assertRaises(AssertionError):prepare_selected(four,selection,base/'missing')
            self.assertFalse((base/'missing').exists())

    def test_checkpoint_objective_family_and_protocol_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);four,pair,selection=self.setup_selection(base)
            reg=prepare_selected(four,selection,base/'new')
            for fields in ({'tracking_guidance':None},{'seed':99},{'controller':'impedance'},
                           {'checkpoint':str(pair/'direct_control/checkpoint_0011000')}):
                bad=deepcopy(reg);bad['jobs'][0].update(fields)
                with self.assertRaises(AssertionError):verify_selected_lineages(bad)
            path=pair/'direct_tracking/PROTOCOL.json'
            spec=read(path);spec['training_conditions']=['changed']
            write(path,spec)
            with self.assertRaises(AssertionError):verify_selected_lineages(reg)

    def test_incompatible_frozen_source_rejected_before_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);four,pair,selection=self.setup_selection(base)
            path=pair/'source/tools/baseline_repair_worker_20261008.py'
            path.write_text('different frozen physics\n')
            reg=read(pair/'REGISTRATION.json');reg['source_manifest']=manifest(pair/'source')
            self.bind(pair,reg,read(pair/'execution.json'))
            with self.assertRaisesRegex(AssertionError,'Frozen training source'):
                prepare_selected(four,selection,base/'bad')
            self.assertFalse((base/'bad').exists())

    def test_wrong_method_selection_and_overbudget_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);four,pair,selection=self.setup_selection(base)
            bad=deepcopy(selection)
            bad['methods']['impedance']=dict(root=str(pair),job='direct_control',rationale='invalid cross-family')
            with self.assertRaises(AssertionError):prepare_selected(four,bad,base/'wrong')
            with self.assertRaises(AssertionError):prepare_selected(four,selection,base/'oversized',1000000)
            self.assertFalse((base/'wrong').exists())
            self.assertFalse((base/'oversized').exists())

    def test_next_stage_uses_new_checkpoints_not_stale_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);four,pair,selection=self.setup_selection(base)
            root=base/'selected';reg=prepare_selected(four,selection,root)
            state=dict(status='finite_stage_complete',active=None,
                registration_sha256=digest(root/'REGISTRATION.json'),jobs=[])
            for job in reg['jobs']:
                output=Path(job['output']);output.mkdir()
                cp=output/'checkpoint_0022000'
                shutil.copytree(job['checkpoint'],cp)
                runner=read(cp/'office_runner.json');runner['step']=22000
                write(cp/'office_runner.json',runner)
                checked=dict(path=str(cp),step=22000,episode=16,hashes=manifest(cp))
                execution=dict(status='complete',stop_reason='step_budget',steps=22000,
                    rows=[dict(episode=8,ended_utc='closed',steps=11000)],checkpoint_rows=[checked])
                write(output/'execution.json',execution)
                spec=read(Path(job['checkpoint']).parent/'PROTOCOL.json')
                spec['goal_registration_sha256']=digest(root/'REGISTRATION.json')
                write(output/'PROTOCOL.json',spec)
                state['jobs'].append(dict(job=job['name'],returncode=0,stop_reason='step_budget',
                    steps=22000,checkpoint=checked))
            write(root/'execution.json',state)
            later=prepare_next(root,base/'later')
            self.assertNotIn('selected_lineages',later)
            self.assertEqual(later['previous_stage']['root'],str(root))
            for job in later['jobs']:
                self.assertEqual(job['inherited_steps'],22000)
                self.assertEqual(Path(job['checkpoint']).parent,root/job['name'])
            self.assertEqual(later['jobs'][0]['tracking_guidance'],CONFIG)
            verify_inputs(later)


if __name__=='__main__':
    unittest.main()
