from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from goal_compute_backend_20261016 import (GPU_RESOURCES, backend, environment,
    check_environment, check_backend_resume, gpu_admission_reason)
from rl_goal_stage_20261016 import (prepare_next, verify_inputs, verify_preflight,
    worker_command, validate_gpu_training_closure, read, write, digest)
import test_goal_stage_continuation_20261016 as fixtures


class BackendTests(unittest.TestCase):
    def test_backend_requires_explicit_envelope_and_actual_affinity(self):
        reg = {'resources': dict(GPU_RESOURCES)}
        self.assertEqual(backend(None), 'cpu')
        self.assertEqual(backend(reg), 'cuda')
        with self.assertRaises(ValueError):
            backend({'resources': {'learning_backend': 'cuda'}})
        check_environment(reg, expected_cpu=6, environ=environment(reg), affinity={6})
        with self.assertRaisesRegex(ValueError, 'affinity'):
            check_environment(reg, expected_cpu=6, environ=environment(reg), affinity={1,6})
        with self.assertRaisesRegex(ValueError, 'environment'):
            check_environment(reg, expected_cpu=6, environ=environment(None), affinity={6})

    def test_backend_migration_is_explicit_and_one_way(self):
        reg = {'resources': dict(GPU_RESOURCES)}
        with self.assertRaises(ValueError):
            check_backend_resume({}, reg, {})
        check_backend_resume({}, reg, {'backend_migration': True})
        check_backend_resume({'learning_backend':'cuda'}, reg, {})
        with self.assertRaises(ValueError):
            check_backend_resume({'learning_backend':'cuda'}, None, {'backend_migration':True})

    def test_gpu_admission_guards_memory_and_temperature(self):
        reg = {'resources': dict(GPU_RESOURCES)}
        snapshot = dict(index=0, free_mib=4096, temperature_c=79)
        self.assertIsNone(gpu_admission_reason(reg, snapshot))
        self.assertEqual(gpu_admission_reason(reg, dict(snapshot,free_mib=4095)), 'gpu_memory_reserve')
        self.assertEqual(gpu_admission_reason(reg, dict(snapshot,temperature_c=80)), 'gpu_temperature')
        self.assertEqual(gpu_admission_reason(reg, dict(snapshot,index=1)), 'gpu_device_mismatch')

    def test_gpu_command_retains_host_limits_and_cpu_affinity(self):
        reg = dict(resources=dict(GPU_RESOURCES),runtime='/runtime',python='/venv/python',source='/source',
            parent_root='/parent',parameter_source='/parameter',optimizer_schedule_steps=1000000,run_root='/new')
        job = dict(unit='test',output='/new/direct',seed=1,limit=12375,reward='office_task',
            reward_variant='task_safety',hp='direct_explore',controller=None,checkpoint='/old/cp')
        cmd = worker_command(reg,job)
        for value in ('--property=MemoryMax=3G','--property=MemorySwapMax=0','--property=CPUAffinity=1',
                      '--setenv=JAX_PLATFORMS=cuda','--setenv=CUDA_VISIBLE_DEVICES=0',
                      '--setenv=XLA_PYTHON_CLIENT_MEM_FRACTION=0.125'):
            self.assertIn(value,cmd)

    def test_gpu_stage_preparation_preserves_parent_and_physics(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, _, _ = fixtures.StageContinuationTests().fixture(Path(tmp))
            before = digest(old/'REGISTRATION.json')
            reg = prepare_next(old,Path(tmp)/'gpu',gpu_preflight=True)
            self.assertEqual(digest(old/'REGISTRATION.json'),before)
            self.assertEqual(reg['new_interactions_per_family'],1375)
            self.assertEqual(reg['maximum_new_interactions'],5500)
            self.assertEqual(reg['experiment_kind'],'gpu_training_preflight')
            self.assertTrue(all(j['backend_migration'] and j['limit']==12375 for j in reg['jobs']))
            self.assertEqual(digest(old/'source/tools/baseline_repair_worker_20261008.py'),
                             digest(Path(reg['source'])/'tools/baseline_repair_worker_20261008.py'))
            verify_inputs(reg)
            self.assertFalse((Path(reg['run_root'])/'LAUNCH.json').exists())

    def gpu_closure(self, base):
        root,reg,state = fixtures.StageContinuationTests().fixture(base)
        reg.update(experiment_kind='gpu_training_preflight',new_interactions_per_family=1375,
                   resources=dict(reg['resources'],**GPU_RESOURCES))
        for job in reg['jobs']:
            job.update(inherited_steps=9625, backend_migration=True)
        write(root/'REGISTRATION.json',reg)
        state['registration_sha256']=digest(root/'REGISTRATION.json')
        write(root/'execution.json',state)
        for job in reg['jobs']:
            p=Path(job['output']);s=read(p/'PROTOCOL.json')
            s['goal_registration_sha256']=state['registration_sha256'];write(p/'PROTOCOL.json',s)
            e=read(p/'execution.json')
            e.update(rows=[dict(ended_utc='closed',result={'full_task_horizon_completed':True})],
                compute_runtime=dict(learning_backend='cuda',platforms=['gpu'],cpu_affinity=[1]),
                resource_snapshot=dict(memory_events={'oom':0,'oom_kill':0},memory_swap_current=0,memory_peak=2*1024**3))
            write(p/'execution.json',e)
        return root,reg,state

    def test_full_loop_validation_requires_all_full_episodes_no_oom(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,reg,state = self.gpu_closure(Path(tmp))
            validate_gpu_training_closure(reg,state)
            p=root/'vmc/execution.json';good=read(p)
            for kind in ('short','oom','swap','cpu'):
                bad=deepcopy(good)
                if kind=='short':bad['rows'][0]['result']['full_task_horizon_completed']=False
                if kind=='oom':bad['resource_snapshot']['memory_events']['oom']=1
                if kind=='swap':bad['resource_snapshot']['memory_swap_current']=1
                if kind=='cpu':bad['compute_runtime']['platforms']=['cpu']
                write(p,bad)
                with self.assertRaises(AssertionError):validate_gpu_training_closure(reg,state)
            write(p,good)
            next_reg=prepare_next(root,Path(tmp)/'next')
            self.assertEqual(next_reg['new_interactions_per_family'],11000)
            self.assertNotIn('experiment_kind',next_reg)
            self.assertIn('gpu_training_validation',next_reg)
            verify_inputs(next_reg)

    def test_short_gpu_episode_requires_new_bounded_validation_not_full_training(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,reg,state=self.gpu_closure(Path(tmp))
            p=root/'direct/execution.json';e=read(p)
            e['rows'][0]['result']['full_task_horizon_completed']=False;write(p,e)
            with self.assertRaises(AssertionError):prepare_next(root,Path(tmp)/'invalid_full')
            self.assertFalse((Path(tmp)/'invalid_full').exists())
            repeated=prepare_next(root,Path(tmp)/'repeat',gpu_preflight=True)
            self.assertEqual(repeated['new_interactions_per_family'],1375)
            self.assertTrue(all(not j['backend_migration'] for j in repeated['jobs']))
            self.assertEqual(read(p),e)


if __name__ == '__main__':
    unittest.main()
