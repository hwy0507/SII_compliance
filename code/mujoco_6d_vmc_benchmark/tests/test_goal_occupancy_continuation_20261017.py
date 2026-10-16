"""Fresh reward histories must survive exact selection and later continuation."""
from copy import deepcopy
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rl_goal_stage_20261016 import read,write,digest,manifest,verify_inputs,prepare_next,seal_preflight,verify_preflight
from goal_selected_continuation_20261016 import prepare_selected,closed_source,training_source,TRAINER,OCCUPANCY_HELPER,STORAGE_HELPER
from goal_tracking_pilot_20261016 import prepare
from goal_payload_occupancy_reward_20261016 import CONFIG
from screen_goal_rl_convergence_20261016 import collect
import test_goal_selected_continuation_20261016 as selected_fixtures
from test_goal_convergence_screen_20261016 import CRITERIA,CONDITIONS,rows


class OccupancyContinuationTests(unittest.TestCase):
    def fixture(self,base,stream=False):
        helper=selected_fixtures.SelectedContinuationTests();old=helper.fixture(base/'four')
        reg=read(old/'REGISTRATION.json');reg['training_convergence']=CRITERIA
        job=next(j for j in reg['jobs'] if j['controller']=='impedance')
        job.update(reward='metric',reward_variant='payload_shaping',hp='parameter_balanced')
        helper.bind(old,reg,read(old/'execution.json'))
        for job in reg['jobs']:
            output=Path(job['output']);spec=read(output/'PROTOCOL.json')
            spec.update(prior_file_sha256='prior',training_conditions=CONDITIONS)
            if job['controller']=='impedance':spec['reward']['error_weight']=4
            write(output/'PROTOCOL.json',spec)
            execution=read(output/'execution.json');execution['rows']=rows(8)
            for row in execution['rows']:row['result'].update(task_success=False,strict_success=False)
            write(output/'execution.json',execution)
        cp=old/'impedance/checkpoint_0011000';spec=read(cp.parent/'PROTOCOL.json')
        receipt=base/'reward.json';write(receipt,dict(protocol_snapshot=spec,protocol_sha256=digest(cp.parent/'PROTOCOL.json'),
            execution_snapshot=dict(rows=[dict(ended_utc='closed',episode=7,step_after=11000)])))
        pair=base/'pair';prepare(old,pair,cp,receipt,'impedance',True)
        if stream:
            from goal_prospective_storage_20261017 import prepare as prepare_storage
            (base/'outputs').mkdir()
            destination=base/'outputs/rl_goal_stream_fixture'
            prepare_storage(pair,destination)
            pair=destination
        self.close(pair,cp)
        return old,pair

    def test_storage_migration_selects_and_continues_without_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,pair=self.fixture(base,stream=True)
            before=(manifest(old),manifest(pair))
            selected=base/'outputs/rl_goal_stream_selected'
            reg=prepare_selected(old,self.selection(old,pair),selected)
            self.assertEqual((manifest(old),manifest(pair)),before)
            self.assertEqual(training_source(reg),training_source(read(old/'REGISTRATION.json')))
            self.assertEqual(reg['source_manifest'][STORAGE_HELPER],read(pair/'REGISTRATION.json')['source_manifest'][STORAGE_HELPER])
            self.assertEqual(reg['jobs'][1]['inherited_steps'],44000)
            self.assertEqual(reg['jobs'][1]['payload_occupancy_guidance'],CONFIG)
            self.assertFalse((selected/'LAUNCH.json').exists())
            from goal_prospective_storage_20261017 import validate,verify_preflight as storage_preflight
            _,policy=validate(selected)
            self.assertEqual(policy['registration_sha256'],digest(selected/'REGISTRATION.json'))
            self.assertTrue(all(not Path(j['output']).exists() for j in reg['jobs']))
            with self.assertRaises(FileNotFoundError):storage_preflight(selected)
            check=subprocess.run([sys.executable,'-I','-c',
                'import sys;sys.path.insert(0,sys.argv[1]);from rl_goal_stage_20261016 import read,verify_inputs;verify_inputs(read(sys.argv[2]))',
                str(selected/'source/tools'),str(selected/'REGISTRATION.json')],cwd=base,
                env=dict(os.environ,PYTHONPATH=''),capture_output=True,text=True,timeout=20)
            self.assertEqual(check.returncode,0,check.stderr)
            self.close(selected)
            later_root=base/'outputs/rl_goal_stream_later'
            later=prepare_next(selected,later_root);verify_inputs(later)
            _,later_policy=validate(later_root)
            self.assertNotEqual(policy['registration_sha256'],later_policy['registration_sha256'])
            with self.assertRaises(FileNotFoundError):storage_preflight(later_root)
            self.assertEqual(later['jobs'][1]['inherited_steps'],55000)
            self.assertEqual(later['jobs'][1]['payload_occupancy_guidance'],CONFIG)

    def test_storage_migration_does_not_hide_source_or_ancestry_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,pair=self.fixture(base,stream=True)
            reg=prepare_selected(old,self.selection(old,pair),base/'outputs/rl_goal_stream_selected')
            for key in (TRAINER,STORAGE_HELPER,OCCUPANCY_HELPER,'tools/baseline_repair_worker_20261008.py'):
                bad=deepcopy(reg);bad['source_manifest'][key]='changed'
                with self.assertRaises(AssertionError):training_source(bad)
            original=read(pair/'REGISTRATION.json')['storage_predecessor']
            path=Path(original['root'])/'REGISTRATION.json'
            changed=read(path);changed['pilot_predecessor']['registration_sha256']='changed'
            write(path,changed)
            with self.assertRaisesRegex(AssertionError,'Storage predecessor changed'):training_source(reg)

    def test_storage_stage_rejects_nonstream_destination_before_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,pair=self.fixture(base,stream=True)
            for destination in (base/'selected',base/'outputs/selected',base/'rl_goal_stream_bad'):
                with self.assertRaisesRegex(ValueError,'prospective stream roots'):
                    prepare_selected(old,self.selection(old,pair),destination)
                self.assertFalse(destination.exists())
            selected=base/'outputs/rl_goal_stream_selected'
            prepare_selected(old,self.selection(old,pair),selected);self.close(selected)
            with self.assertRaisesRegex(ValueError,'prospective stream roots'):
                prepare_next(selected,base/'later')
            self.assertFalse((base/'later').exists())

    def test_reselection_keeps_base_storage_even_with_legacy_checkpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,pair=self.fixture(base,stream=True)
            selected=base/'outputs/rl_goal_stream_selected'
            prepare_selected(old,self.selection(old,pair),selected);self.close(selected)
            before=(manifest(old),manifest(pair),manifest(selected))
            choice=dict(decision='Explicit synthetic old checkpoint selection',methods={
                j['name']:dict(root=str(old),job=j['name'],rationale='Original untreated checkpoint')
                for j in read(old/'REGISTRATION.json')['jobs']})
            root=base/'outputs/rl_goal_stream_reselected'
            reg=prepare_selected(selected,choice,root)
            from goal_prospective_storage_20261017 import validate,verify_preflight as storage_preflight
            validate(root);verify_inputs(reg)
            self.assertEqual(reg['storage_resources'],dict(cpu=6,memory_max_bytes=1024**3,swap_max_bytes=0))
            self.assertNotIn('payload_occupancy_guidance',reg['jobs'][1])
            self.assertEqual((manifest(old),manifest(pair),manifest(selected)),before)
            with self.assertRaises(FileNotFoundError):storage_preflight(root)

    def close(self,root,fresh_cp=None):
        reg=read(root/'REGISTRATION.json');sha=digest(root/'REGISTRATION.json')
        state=dict(status='finite_stage_complete',active=None,registration_sha256=sha,jobs=[])
        for job in reg['jobs']:
            output=Path(job['output']);output.mkdir()
            parent=Path(job['checkpoint']) if job['checkpoint'] else fresh_cp
            cp=output/f"checkpoint_{job['limit']:07d}";shutil.copytree(parent,cp)
            runner=read(cp/'office_runner.json');runner['step']=job['limit'];write(cp/'office_runner.json',runner)
            checked=dict(path=str(cp),step=job['limit'],episode=job['limit']//1375,hashes=manifest(cp))
            spec=read(parent.parent/'PROTOCOL.json')
            spec.update(goal_registration_sha256=sha,controller=job['controller'],seed=job['seed'],
                reward_variant=job['reward_variant'],hyperparameter_id=job['hp'])
            spec.pop('payload_occupancy_guidance',None)
            if job.get('payload_occupancy_guidance'):spec['payload_occupancy_guidance']=job['payload_occupancy_guidance']
            write(output/'PROTOCOL.json',spec)
            data=rows(job['limit']//1375)[job['inherited_steps']//1375:]
            for row in data:row['result'].update(task_success=False,strict_success=False)
            execution=dict(status='complete',stop_reason='step_budget',steps=job['limit'],rows=data,checkpoint_rows=[checked])
            if job['checkpoint']:
                execution['resumed_from']=dict(inherited_steps=job['inherited_steps'],
                    parent_execution_sha256=digest(parent.parent/'execution.json'))
            write(output/'execution.json',execution)
            state['jobs'].append(dict(job=job['name'],returncode=0,stop_reason='step_budget',steps=job['limit'],checkpoint=checked))
        write(root/'execution.json',state)

    def selection(self,old,pair,arm='impedance_occupancy'):
        return dict(decision='Synthetic protocol test, not candidate selection',methods={
            j['name']:dict(root=str(pair if j['controller']=='impedance' else old),
                job=arm if j['controller']=='impedance' else j['name'],rationale='Exact parent')
            for j in read(old/'REGISTRATION.json')['jobs']})

    def test_selected_and_next_stage_preserve_reward_and_fresh_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,pair=self.fixture(base);before=(manifest(old),manifest(pair))
            selected=base/'selected';reg=prepare_selected(old,self.selection(old,pair),selected)
            self.assertEqual((manifest(old),manifest(pair)),before)
            job=next(j for j in reg['jobs'] if j['controller']=='impedance')
            self.assertEqual(job['payload_occupancy_guidance'],CONFIG)
            self.assertEqual(job['inherited_steps'],44000)
            self.assertEqual(reg['source_manifest'][TRAINER],read(pair/'REGISTRATION.json')['source_manifest'][TRAINER])
            verify_inputs(reg)
            check=subprocess.run([sys.executable,'-I','-c',
                'import sys;sys.path.insert(0,sys.argv[1]);from rl_goal_stage_20261016 import read,verify_inputs;verify_inputs(read(sys.argv[2]))',
                str(selected/'source/tools'),str(selected/'REGISTRATION.json')],cwd=base,
                env=dict(os.environ,PYTHONPATH=''),capture_output=True,text=True,timeout=20)
            self.assertEqual(check.returncode,0,check.stderr)
            self.close(selected)
            later=prepare_next(selected,base/'later');verify_inputs(later)
            self.assertEqual(later['jobs'][1]['payload_occupancy_guidance'],CONFIG)
            self.assertEqual(later['jobs'][1]['inherited_steps'],55000)
            self.close(base/'later')
            screen=collect(base/'later')['methods']['impedance']['screen']
            self.assertEqual(screen['closed']['count'],48)
            self.assertEqual(screen['closed']['joint'],0)
            self.assertFalse(screen['training_candidate'])

    def test_reward_or_source_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,pair=self.fixture(base)
            reg=prepare_selected(old,self.selection(old,pair),base/'selected')
            bad=deepcopy(reg);bad['jobs'][1].pop('payload_occupancy_guidance')
            with self.assertRaises(AssertionError):verify_inputs(bad)
            bad=deepcopy(reg);bad.pop('payload_occupancy_origin')
            with self.assertRaises(AssertionError):verify_inputs(bad)
            for key in (TRAINER,OCCUPANCY_HELPER,'tools/baseline_repair_worker_20261008.py'):
                bad=deepcopy(reg);bad['source_manifest'][key]='changed'
                with self.assertRaises(AssertionError):training_source(bad)
            spec_path=pair/'impedance_occupancy/PROTOCOL.json';spec=read(spec_path)
            spec.pop('payload_occupancy_guidance');write(spec_path,spec)
            with self.assertRaises(AssertionError):closed_source(pair)

    def test_running_pair_rejected_and_control_does_not_inherit_reward(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,pair=self.fixture(base);state=read(pair/'execution.json')
            write(pair/'execution.json',dict(state,status='running'))
            with self.assertRaises(AssertionError):prepare_selected(old,self.selection(old,pair),base/'bad')
            self.assertFalse((base/'bad').exists());write(pair/'execution.json',state)
            reg=prepare_selected(old,self.selection(old,pair,'impedance_control'),base/'control')
            self.assertNotIn('payload_occupancy_guidance',reg['jobs'][1]);verify_inputs(reg)

    def test_later_stage_cannot_remove_reward_and_explicit_reselection_can(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,pair=self.fixture(base);selected=base/'selected'
            prepare_selected(old,self.selection(old,pair),selected);self.close(selected)
            reg=prepare_next(selected,base/'later')
            bad=deepcopy(reg);bad['jobs'][1].pop('payload_occupancy_guidance')
            with self.assertRaises(AssertionError):verify_inputs(bad)
            choice=dict(decision='Explicit synthetic original checkpoint selection',methods={
                j['name']:dict(root=str(old),job=j['name'],rationale='Original untreated checkpoint')
                for j in read(old/'REGISTRATION.json')['jobs']})
            reg=prepare_selected(selected,choice,base/'original')
            self.assertNotIn('payload_occupancy_guidance',reg['jobs'][1]);verify_inputs(reg)

    def test_preflight_seal_checks_reward_identity_not_only_receipt_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,pair=self.fixture(base);root=base/'selected'
            reg=prepare_selected(old,self.selection(old,pair),root)
            for job in reg['jobs']:
                write(root/f'CREDIT_PREFLIGHT_{job["name"]}.json',dict(status='passed',
                    registration_sha256=digest(root/'REGISTRATION.json'),job=job['name'],
                    checkpoint=job['checkpoint'],checkpoint_hashes=job['checkpoint_hashes'],
                    checkpoint_hashes_unchanged=True,inherited_steps=job['inherited_steps'],actual_n_step=25,
                    restored_raw_replay_count=job['inherited_steps'],finite_update_metrics=True,
                    terminal_windows_match=True,no_cross_episode_bootstrap=True,
                    checkpoint_reward_identity={key:job.get(key) for key in ('tracking_guidance','payload_occupancy_guidance')}))
            path=root/'CREDIT_PREFLIGHT_impedance.json';good=read(path);bad=deepcopy(good)
            bad['checkpoint_reward_identity']['payload_occupancy_guidance']=None;write(path,bad)
            with self.assertRaises(AssertionError):seal_preflight(root)
            self.assertFalse((root/'CREDIT_PREFLIGHT.json').exists())
            write(path,good);seal_preflight(root);verify_preflight(reg)
            write(path,bad);sealed=read(root/'CREDIT_PREFLIGHT.json')
            sealed['jobs']['impedance']=digest(path);write(root/'CREDIT_PREFLIGHT.json',sealed)
            with self.assertRaises(AssertionError):verify_preflight(reg)


if __name__=='__main__':unittest.main()
