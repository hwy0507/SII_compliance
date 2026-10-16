from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
import shutil

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from goal_tracking_pilot_20261016 import (validate_pair, require_predecessor_complete,
    verify_pilot_preflight, prepare_gpu_pilot)
from goal_tracking_reward_20261016 import CONFIG, PARAMETER_CONFIG
from rl_goal_stage_20261016 import write, digest, read, manifest, verify_inputs
import test_goal_stage_continuation_20261016 as fixtures
import test_goal_compute_backend_20261016 as gpu_fixtures


class TrackingPilotTests(unittest.TestCase):
    def gpu_pair_fixture(self, base):
        gpu,reg,state=gpu_fixtures.BackendTests().gpu_closure(base)
        reg.update(runtime='/runtime',python=sys.executable,dispatch_lock='/unused/test-lock')
        write(gpu/'REGISTRATION.json',reg)
        state['registration_sha256']=digest(gpu/'REGISTRATION.json');write(gpu/'execution.json',state)
        for job in reg['jobs']:
            path=Path(job['output'])/'PROTOCOL.json';spec=read(path)
            spec['goal_registration_sha256']=state['registration_sha256'];write(path,spec)
        cpu=base/'cpu_pair';cpu.mkdir()
        shutil.copytree(gpu/'source',cpu/'source')
        shutil.copytree(gpu/'parameter_n25',cpu/'parameter_n25')
        pair=dict(reg,**self.pair())
        pair.update(run_root=str(cpu),source=str(cpu/'source'),parameter_source=str(cpu/'parameter_n25'),
            resources=dict(cpu='1',memory_max=3*1024**3,swap_max=0),
            pilot_predecessor=dict(root=str(gpu),registration_sha256=digest(gpu/'REGISTRATION.json')),
            pilot_probe=dict(checkpoint='/diagnostic/cp',hashes={'x':'h'},reward_receipt_sha256='r'))
        write(cpu/'REGISTRATION.json',pair)
        write(cpu/'CREDIT_PREFLIGHT.json',dict(status='passed',registration_sha256=digest(cpu/'REGISTRATION.json'),
            initial_networks_equal=True,checkpoint_hashes_unchanged=True,gradient_updates=2,
            model_saved=False,simulation=False,source_checkpoint='/diagnostic/cp',source_checkpoint_hashes={'x':'h'},
            reward_receipt_sha256='r',arms={j['name']:dict(fresh_before=True,n_step=25,finite_update=True,
                terminal_window_checked=True,guidance=j.get('tracking_guidance')) for j in pair['jobs']}))
        return cpu,gpu

    def test_cuda_pair_retains_freshness_physics_and_requires_own_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);cpu,gpu=self.gpu_pair_fixture(base);before=manifest(cpu)
            reg=prepare_gpu_pilot(cpu,gpu,base/'cuda_pair')
            self.assertEqual(manifest(cpu),before)
            self.assertEqual(reg['resources']['learning_backend'],'cuda')
            self.assertTrue(all(j['checkpoint'] is None and j['inherited_steps']==0 for j in reg['jobs']))
            self.assertEqual(digest(cpu/'source/tools/train_v4_recovery_rl_20261016.py'),
                digest(base/'cuda_pair/source/tools/train_v4_recovery_rl_20261016.py'))
            self.assertEqual(reg['maximum_new_interactions'],22000)
            verify_inputs(reg);validate_pair(reg)
            with self.assertRaises(FileNotFoundError):verify_pilot_preflight(reg)
            self.assertFalse((base/'cuda_pair/LAUNCH.json').exists())

    def test_cuda_pair_rejects_running_or_short_gpu_stage_before_creating_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);cpu,gpu=self.gpu_pair_fixture(base)
            path=gpu/'execution.json';good=read(path)
            write(path,dict(good,status='running'))
            with self.assertRaises(AssertionError):prepare_gpu_pilot(cpu,gpu,base/'bad_running')
            self.assertFalse((base/'bad_running').exists());write(path,good)
            path=gpu/'vmc/execution.json';state=read(path)
            state['rows'][0]['result']['full_task_horizon_completed']=False;write(path,state)
            with self.assertRaises(AssertionError):prepare_gpu_pilot(cpu,gpu,base/'bad_short')
            self.assertFalse((base/'bad_short').exists())

    def test_cuda_pair_rejects_used_cpu_pair_or_different_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);cpu,gpu=self.gpu_pair_fixture(base)
            write(cpu/'LAUNCH.json',{'preserve':'attempt'})
            with self.assertRaises(AssertionError):prepare_gpu_pilot(cpu,gpu,base/'bad_launched')
            self.assertFalse((base/'bad_launched').exists())
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);cpu,gpu=self.gpu_pair_fixture(base)
            path=cpu/'REGISTRATION.json';reg=read(path);reg['runtime']='/other';write(path,reg)
            path=cpu/'CREDIT_PREFLIGHT.json';receipt=read(path)
            receipt['registration_sha256']=digest(cpu/'REGISTRATION.json');write(path,receipt)
            with self.assertRaises(AssertionError):prepare_gpu_pilot(cpu,gpu,base/'bad_runtime')
            self.assertFalse((base/'bad_runtime').exists())

    def test_impedance_pair_is_fresh_and_only_extra_tracking_cost_differs(self):
        reg=self.pair();reg['experiment_kind']='fresh_parameter_tracking_pilot'
        for job in reg['jobs']:
            job.update(name=job['name'].replace('direct','impedance'),controller='impedance',
                       reward='metric',reward_variant='payload_shaping',hp='parameter_balanced')
        reg['jobs'][1]['tracking_guidance']=dict(PARAMETER_CONFIG)
        validate_pair(reg)
        for key,value in (('seed',6),('checkpoint','/old/model'),('hp','direct_explore'),('controller','admittance')):
            bad=deepcopy(reg);bad['jobs'][1][key]=value
            with self.assertRaises(AssertionError):validate_pair(bad)
        bad=deepcopy(reg);bad['jobs'][1]['tracking_guidance']=CONFIG
        with self.assertRaises(AssertionError):validate_pair(bad)

    def pair(self):
        jobs = [dict(name=name,output='/'+name,unit=name,checkpoint=None,inherited_steps=0,
            limit=11000,controller=None,reward='office_task',reward_variant='task_safety',
            hp='direct_explore',seed=5,credit_migration=False) for name in ('direct_control','direct_tracking')]
        jobs[1]['tracking_guidance'] = dict(CONFIG)
        return dict(experiment_kind='fresh_direct_tracking_pilot',jobs=jobs,maximum_new_interactions=22000,
                    new_interactions_per_family=11000,optimizer_schedule_steps=1000000)

    def test_only_reward_differs_and_both_arms_are_fresh(self):
        reg = self.pair(); validate_pair(reg)
        for key, value in (('seed',6),('checkpoint','/old/model'),('limit',22000),('controller','vmc')):
            bad = deepcopy(reg); bad['jobs'][1][key] = value
            with self.assertRaises(AssertionError): validate_pair(bad)
        bad = deepcopy(reg); bad['jobs'][0]['tracking_guidance'] = CONFIG
        with self.assertRaises(AssertionError): validate_pair(bad)

    def test_launch_gate_requires_all_four_predecessor_checkpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous, _, state = fixtures.StageContinuationTests().fixture(Path(tmp))
            reg = self.pair()
            reg['pilot_predecessor'] = dict(root=str(previous),registration_sha256=digest(previous/'REGISTRATION.json'))
            self.assertEqual(len(require_predecessor_complete(reg)),4)
            write(previous/'execution.json',dict(state,status='running',active={'job':'vmc'}))
            with self.assertRaises(AssertionError): require_predecessor_complete(reg)
            state['jobs'][0]['returncode'] = 1
            write(previous/'execution.json',state)
            with self.assertRaises(AssertionError): require_predecessor_complete(reg)

    def test_missing_arm_or_changed_guidance_cannot_pass_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); reg = self.pair(); reg['run_root'] = str(root)
            reg['pilot_probe'] = dict(checkpoint='/cp',hashes={'x':'h'},reward_receipt_sha256='r')
            write(root/'REGISTRATION.json',reg)
            result = dict(status='passed',registration_sha256=digest(root/'REGISTRATION.json'),
                initial_networks_equal=True,checkpoint_hashes_unchanged=True,gradient_updates=2,
                model_saved=False,simulation=False,source_checkpoint='/cp',source_checkpoint_hashes={'x':'h'},
                reward_receipt_sha256='r',arms={j['name']:dict(fresh_before=True,n_step=25,finite_update=True,
                    terminal_window_checked=True,guidance=j.get('tracking_guidance')) for j in reg['jobs']})
            write(root/'CREDIT_PREFLIGHT.json',result); verify_pilot_preflight(reg)
            result['arms']['direct_tracking']['guidance'] = None
            write(root/'CREDIT_PREFLIGHT.json',result)
            with self.assertRaises(AssertionError): verify_pilot_preflight(reg)
            del result['arms']['direct_tracking']
            write(root/'CREDIT_PREFLIGHT.json',result)
            with self.assertRaises(AssertionError): verify_pilot_preflight(reg)


if __name__ == '__main__': unittest.main()
