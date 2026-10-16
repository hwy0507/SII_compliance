"""Selected regularized models retain their actual implementation and history."""
from copy import deepcopy
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rl_goal_stage_20261016 import read,write,digest,manifest,verify_inputs,prepare_next,job_parameter_source
from goal_actor_regularization_pilot_20261016 import prepare
from goal_selected_continuation_20261016 import prepare_selected,closed_source
from screen_goal_rl_convergence_20261016 import collect
from report_goal_tracking_pair_20261016 import report,METRICS
import test_goal_actor_regularization_pilot_20261016 as pilot_fixtures
from test_goal_convergence_screen_20261016 import CRITERIA,CONDITIONS,rows


class RegularizedContinuationTests(unittest.TestCase):
    def fixture(self,base):
        old,probe,cp=pilot_fixtures.ActorRegularizationTests().fixture(base)
        reg=read(old/'REGISTRATION.json')
        reg.update(training_convergence=CRITERIA,server_compute=False,acceptance_allowed=False)
        write(old/'REGISTRATION.json',reg)
        state=read(old/'execution.json');state['registration_sha256']=digest(old/'REGISTRATION.json')
        write(old/'execution.json',state)
        for job in reg['jobs']:
            output=Path(job['output']);spec=read(output/'PROTOCOL.json')
            spec.update(goal_registration_sha256=state['registration_sha256'],reward={'mode':job['reward']},
                prior_file_sha256='prior',training_conditions=CONDITIONS)
            write(output/'PROTOCOL.json',spec)
            execution=read(output/'execution.json');execution['rows']=rows(8)
            # All inherited episodes are failures, never silently successful.
            for row in execution['rows']:row['result'].update(task_success=False,strict_success=False)
            write(output/'execution.json',execution)
        pair=base/'pair';prepare(old,cp,probe,pair)
        self.close(pair)
        return old,pair

    def close(self,root):
        reg=read(root/'REGISTRATION.json')
        state=dict(status='finite_stage_complete',active=None,registration_sha256=digest(root/'REGISTRATION.json'),jobs=[])
        for job in reg['jobs']:
            output=Path(job['output']);output.mkdir()
            cp=output/f"checkpoint_{job['limit']:07d}"
            shutil.copytree(job['checkpoint'],cp)
            runner=read(cp/'office_runner.json');runner['step']=job['limit'];write(cp/'office_runner.json',runner)
            checked=dict(path=str(cp),step=job['limit'],episode=job['limit']//1375,hashes=manifest(cp))
            spec=read(Path(job['checkpoint']).parent/'PROTOCOL.json')
            spec.update(goal_registration_sha256=state['registration_sha256'],
                agent_config=dict(spec['agent_config'],actor_bc_alpha=job.get('actor_bc_alpha',0.)),
                parameter_source=job_parameter_source(reg,job),
                actor_regularization_migration=job.get('actor_regularization_migration',False),
                segment_limit=job['limit'],maximum_steps=1000000,warmup_steps=5000)
            write(output/'PROTOCOL.json',spec)
            data=rows(job['limit']//1375)[job['inherited_steps']//1375:]
            for row in data:
                row['return_value']=2. if job.get('actor_bc_alpha') else 1.
                row['result'].update(task_success=False,strict_success=False)
                run=output/f"episode_{row['episode']:04d}";run.mkdir()
                audit=dict(training=True,task_success=False,strict_success=False,full_horizon=True,
                    stage='carry',physical_seconds=55.,**{key:1. for key in METRICS})
                write(run/'AUDIT.json',audit)
                row.update(run=str(run),audit_sha256=digest(run/'AUDIT.json'))
            execution=dict(status='complete',stop_reason='step_budget',steps=job['limit'],rows=data,checkpoint_rows=[checked],
                resumed_from=dict(checkpoint=job['checkpoint'],hashes=job['checkpoint_hashes'],
                    inherited_steps=job['inherited_steps'],parent_execution_sha256=digest(Path(job['checkpoint']).parent/'execution.json')))
            write(output/'execution.json',execution)
            state['jobs'].append(dict(job=job['name'],returncode=0,stop_reason='step_budget',steps=job['limit'],checkpoint=checked))
        write(root/'execution.json',state)

    def selection(self,old,pair,arm='direct_regularized'):
        return dict(decision='Synthetic finite protocol test, not a real candidate decision',methods={
            j['name']:dict(root=str(pair if j['controller'] is None else old),
                job=arm if j['controller'] is None else j['name'],rationale='Preserve exact chosen checkpoint')
            for j in read(old/'REGISTRATION.json')['jobs']})

    def test_selected_model_and_next_stage_preserve_alpha1_without_remigration(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,pair=self.fixture(base);before=(manifest(old),manifest(pair))
            selected=base/'selected';reg=prepare_selected(old,self.selection(old,pair),selected)
            self.assertEqual((manifest(old),manifest(pair)),before)
            job=reg['jobs'][0]
            self.assertEqual(job['actor_bc_alpha'],1.)
            self.assertFalse(job['actor_regularization_migration'])
            self.assertEqual(job['inherited_steps'],22000)
            self.assertEqual(manifest(Path(job['parameter_source'])),manifest(pair/'parameter_bc1'))
            verify_inputs(reg)
            check=subprocess.run([sys.executable,'-I','-c',
                'import sys;sys.path.insert(0,sys.argv[1]);from rl_goal_stage_20261016 import read,verify_inputs;verify_inputs(read(sys.argv[2]))',
                str(selected/'source/tools'),str(selected/'REGISTRATION.json')],cwd=base,
                env=dict(os.environ,PYTHONPATH=''),capture_output=True,text=True,timeout=20)
            self.assertEqual(check.returncode,0,check.stderr)
            self.close(selected)
            later=prepare_next(selected,base/'later');verify_inputs(later)
            self.assertEqual(later['jobs'][0]['actor_bc_alpha'],1.)
            self.assertFalse(later['jobs'][0]['actor_regularization_migration'])
            self.assertEqual(later['jobs'][0]['inherited_steps'],33000)
            self.assertNotEqual(later['jobs'][0]['parameter_source'],job['parameter_source'])
            self.assertEqual(later['jobs'][0]['parameter_manifest'],job['parameter_manifest'])
            self.close(base/'later')
            screen=collect(base/'later')
            direct=screen['methods']['direct']
            self.assertEqual(direct['screen']['closed']['count'],24)
            self.assertEqual(direct['screen']['closed']['joint'],0)
            self.assertEqual(len(direct['inherited_experimental_history']['execution_snapshot']['rows']),8)
            self.assertFalse(direct['inherited_experimental_history']['included_in_return_windows'])
            self.assertFalse(screen['all_training_candidates'])
            # Explicitly selecting the older alpha0 model must not retain stale
            # alpha1 metadata from the four-family template used for dispatch.
            original=dict(decision='Synthetic explicit original-checkpoint selection',methods={
                j['name']:dict(root=str(old),job=j['name'],rationale='Choose original model')
                for j in read(old/'REGISTRATION.json')['jobs']})
            reset_selection=prepare_selected(selected,original,base/'original_selected')
            self.assertEqual(reset_selection['jobs'][0]['actor_bc_alpha'],0.)
            self.assertNotIn('parameter_source',reset_selection['jobs'][0])
            verify_inputs(reset_selection)

    def test_wrong_alpha_parameter_or_trainer_cannot_masquerade_as_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,pair=self.fixture(base)
            reg=prepare_selected(old,self.selection(old,pair),base/'selected')
            bad=deepcopy(reg);bad['jobs'][0]['actor_bc_alpha']=0.
            with self.assertRaises(AssertionError):verify_inputs(bad)
            bad=deepcopy(reg);bad['jobs'][0]['parameter_source']=reg['parameter_source']
            with self.assertRaises(AssertionError):verify_inputs(bad)
            bad=deepcopy(reg);bad['source_manifest']['tools/train_v4_recovery_rl_20261016.py']='changed'
            with self.assertRaises(AssertionError):verify_inputs(bad)
            spec_path=pair/'direct_regularized/PROTOCOL.json'
            spec=read(spec_path);spec['agent_config']['actor_bc_alpha']=0.;write(spec_path,spec)
            with self.assertRaises(AssertionError):closed_source(pair)

    def test_running_pair_cannot_be_selected_and_control_remains_alpha0(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,pair=self.fixture(base)
            state=read(pair/'execution.json');write(pair/'execution.json',dict(state,status='running'))
            with self.assertRaises(AssertionError):prepare_selected(old,self.selection(old,pair),base/'bad')
            self.assertFalse((base/'bad').exists())
            write(pair/'execution.json',state)
            reg=prepare_selected(old,self.selection(old,pair,'direct_control'),base/'control')
            self.assertEqual(reg['jobs'][0]['actor_bc_alpha'],0.)
            self.assertNotIn('parameter_source',reg['jobs'][0]);verify_inputs(reg)

    def test_pair_report_compares_same_reward_and_screen_preserves_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,pair=self.fixture(base)
            # Replay preflights are tested on real CUDA checkpoints separately;
            # this fixture exercises report protocol and training receipts only.
            with patch('report_goal_tracking_pair_20261016.verify_preflight'):
                result=report(pair)
            self.assertTrue(result['same_reward_definition'])
            self.assertEqual(len(result['comparison']['pairs']),8)
            self.assertEqual(result['comparison']['pairs'][0]['same_reward_return_delta_treatment_minus_control'],1.)
            self.assertFalse(result['convergence_proven'])
            screen=collect(pair)
            self.assertFalse(screen['four_family_scope'])
            self.assertFalse(screen['all_training_candidates'])
            for method in screen['methods'].values():
                self.assertEqual(method['screen']['closed']['count'],8)
                self.assertEqual(method['screen']['closed']['joint'],0)
                self.assertEqual(len(method['inherited_experimental_history']['execution_snapshot']['rows']),8)
            path=pair/'direct_regularized/PROTOCOL.json';protocol=read(path)
            protocol['reward']['unregistered_weight']=10.;write(path,protocol)
            with patch('report_goal_tracking_pair_20261016.verify_preflight'),self.assertRaises(AssertionError):
                report(pair)


if __name__=='__main__':unittest.main()
