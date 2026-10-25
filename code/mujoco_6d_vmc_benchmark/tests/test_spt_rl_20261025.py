"""Scientific reward invariants and runnable handoff contract; no simulation."""
import ast
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

TOOLS = Path(__file__).resolve().parents[1]/'tools'
sys.path.insert(0,str(TOOLS))
from spt_rl_reward_20261025 import CONFIG, SPTReward, contact_integrals, spt_value
from prepare_rl_spt_campaign_20261025 import command, prepare, verify, read, relocated_adapter, launch
from audit_spt_reward_20261025 import audit_rows


def interval(dt=.04, ratio=.1, force=0., penetration=0.):
    torque=np.full((2,7),ratio*10.)
    return dict(elapsed_s=dt,peak_torque_ratio=ratio,
        external_penetration_peak_m=penetration,torque_slew_cost=0.,
        spt_contact=contact_integrals([dt/2,dt/2],torque,np.full(7,10.),[force,force]))


class RewardTests(unittest.TestCase):
    def test_contact_denominator_and_coincident_torque(self):
        # A large torque OUTSIDE contact must not contaminate the contact ratio.
        data=contact_integrals([.01,.03],np.array([[9.]*7,[2.]*7]),[10.]*7,[0.,20.])
        self.assertAlmostEqual(data['human_contact_s'],.03)
        self.assertEqual(data['human_compliance_proxy'],1.)
        self.assertEqual(data['human_torque_cost_integral_s'],0.)
        empty=contact_integrals([.04],np.full((1,7),9.),[10.]*7,[0.])
        self.assertIsNone(empty['human_compliance_proxy'])

    def test_physical_integrals_independent_of_sampling_density(self):
        a=contact_integrals([.04],np.full((1,7),8.),[10.]*7,[25.])
        b=contact_integrals([.00005]*800,np.full((800,7),8.),[10.]*7,[25.]*800)
        for key in a:self.assertAlmostEqual(a[key],b[key],places=10)

    def test_terminal_requires_both_gates_and_spt_uses_completion(self):
        values=[]
        for task,strict in ((False,False),(True,False),(True,True)):
            _,t=SPTReward()(current_potential=.5,next_potential=.8,interval=interval(),
                terminated=True,task_success=task,strict_success=strict)
            values.append(t['terminal'])
        self.assertEqual(values,[-25.,-25.,25.])
        self.assertEqual(spt_value(task_success=True,strict_success=True,completion_time_s=20.,reference_time_s=10.),.5)
        self.assertEqual(spt_value(task_success=False,strict_success=False,completion_time_s=None,reference_time_s=10.),0.)

    def test_potential_telescopes_and_costs_give_dense_signal(self):
        def total(phi):
            reducer=SPTReward();total=0.;shaping=0.
            for i in range(1375):
                reward,t=reducer(current_potential=phi,next_potential=phi,interval=interval(),
                    terminated=i==1374,task_success=False,strict_success=False)
                total+=CONFIG['gamma']**i*reward
                shaping+=CONFIG['gamma']**i*t['progress']
            self.assertAlmostEqual(shaping,-5*phi,places=9)
            return total-shaping
        self.assertGreater(total(.8),total(.2))

    def test_aborting_cannot_escape_worst_remaining_cost(self):
        reducer=SPTReward()
        _,t=reducer(current_potential=0.,next_potential=0.,interval=interval(),
            terminated=True,task_success=False,strict_success=False)
        dense=sum(CONFIG[k] for k in ('occupancy_weight','time_weight','comfort_weight','contact_force_weight','slew_weight'))
        expected=-sum(CONFIG['gamma']**i*dense*.04/55 for i in range(1,1375))
        # Peak budgets are additionally exhausted on early failure.
        peak=-CONFIG['penetration_weight']-CONFIG['peak_torque_weight']*(1-.1/1.1)
        self.assertAlmostEqual(t['failure_tail'],expected+peak,places=9)

    def test_reject_missing_nonfinite_mismatched_and_duplicate_terminal(self):
        for mutation in ({'spt_contact':{}},{'elapsed_s':float('nan')}, {'peak_torque_ratio':-1.}):
            iv=interval();iv.update(mutation)
            with self.assertRaises((ValueError,KeyError)):
                SPTReward()(current_potential=.2,next_potential=.3,interval=iv,
                    terminated=False,task_success=False,strict_success=False)
        with self.assertRaises(ValueError):SPTReward(dict(CONFIG,comfort_weight=4.))
        reducer=SPTReward()
        kw=dict(current_potential=.2,next_potential=.3,interval=interval(),
                terminated=True,task_success=False,strict_success=False)
        reducer(**kw)
        with self.assertRaises(ValueError):reducer(**kw)


class HandoffTests(unittest.TestCase):
    def test_generated_worker_source_compiles(self):
        # Exercise every exact template replacement before a simulator is spawned.
        tree=ast.parse((TOOLS/'baseline_repair_online_worker_20261008.py').read_text())
        main=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='main')
        assignment=next(x for x in main.body if isinstance(x,ast.Assign)
                        and any(isinstance(t,ast.Name) and t.id=='changes' for t in x.targets))
        source=(TOOLS/'research72_online_worker_20261003.py').read_text()
        for old,new in ast.literal_eval(assignment.value):
            self.assertEqual(source.count(old),1)
            source=source.replace(old,new)
        compile(source,'generated-online-worker','exec')

    def test_reward_replay_checks_first_sample_and_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            run=Path(d);ivs=[];logs=[];reducer=SPTReward();phi=.2;total=0.
            for i,nxt in enumerate((.3,.4)):
                iv=dict(interval(),payload_potential=nxt)
                val,terms=reducer(current_potential=phi,next_potential=nxt,interval=iv,
                    terminated=i==1,task_success=False,strict_success=False)
                terms['interval']=iv;ivs.append(iv)
                logs.append(dict(episode=0,step=i+1,terms=terms));phi=nxt;total+=val
            spec=dict(spt_reward_spec=CONFIG)
            state=dict(rows=[dict(run=str(run),episode=0,steps=2,step_before=0,
                initial_payload_potential=.2,result=dict(task_success=False,strict_success=False),return_value=total)])
            for name,value in [('RL_INTERVALS.json',[None]+ivs),('RL_REWARD_METADATA.json',dict(initial_payload_potential=.2)),
                               ('PROTOCOL.json',spec),('execution.json',state)]:
                (run/name).write_text(json.dumps(value))
            def stream():return io.StringIO(''.join(json.dumps(x)+'\n' for x in logs))
            self.assertEqual(audit_rows(run,spec,state,stream())['transitions'],2)
            logs[0]['terms']['final_reward']+=1.
            with self.assertRaises(ValueError):audit_rows(run,spec,state,stream())

    def test_command_all_families_and_no_silent_restart(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            p=dict(python='/usr/bin/python3',source='/tmp/source with spaces',parameter_source='/tmp/parameter',
                   budgets=dict(training_seeds=[20261025],rl_steps_per_family_seed=1000000))
            for family in ('direct','impedance','admittance','vmc'):
                argv,out=command(root,p,family,11000)
                self.assertIn('spt_v1',argv)
                self.assertIn('spt_start',argv)
                self.assertEqual('--controller' in argv, family!='direct')
                self.assertIn('/tmp/source with spaces/tools/train_v4_recovery_rl_20261016.py',argv)
                out.mkdir(parents=True)
                with self.assertRaises(ValueError):command(root,p,family,11000)
                with self.assertRaises(ValueError):command(root,p,family,22000)

    def test_registered_protocol_passes_worker_contract_and_detects_tamper(self):
        from types import SimpleNamespace
        import prepare_rl_spt_campaign_20261025 as module
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);bench=base/'bench';parent=base/'parent';runtime=base/'runtime';param=base/'param'
            def save(path,value):
                path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))
            for folder in ('scripts','tools','assets'):(bench/folder).mkdir(parents=True)
            save(bench/'configs/rl_spt_training_20261025.json',{})
            save(parent/'CONDITIONS.json',dict(conditions=[dict(id=str(i),role='train') for i in range(32)]))
            save(parent/'PROTOCOL.json',dict(formal_model_sha256=module.FORMAL,physics_dt_s=.00005,
                condition_file_sha256=module.sha(parent/'CONDITIONS.json')))
            for path in (parent/'teacher.json',param/'PRIORS.json',param/'official_parameter_agent.py',
                         runtime/'v6/PROTOCOL.json',runtime/'v6/esn_original_v2/rollout.json',
                         runtime/'v6/construction/rollout.mjb',
                         runtime/'simba_reward_20260930/rewards.py'):save(path,{})
            (param/'official_parameter_agent.py').write_text("from pathlib import Path\nUPSTREAM = Path('/old')\n")
            (runtime/'menagerie').mkdir();(runtime/'SimbaV2').mkdir()
            a=SimpleNamespace(root=base/'run',parent=parent,parameter_source=param,runtime=runtime,
                              steps=1000000,seed=20261025,dispatch_hours=72,cpu=1)
            with patch.object(module,'BENCH',bench),patch.object(module.subprocess,'check_output',return_value='test'), \
                    patch.object(module,'V6_BINARY_HASH',module.sha(runtime/'v6/construction/rollout.mjb')):
                prepare(a)
            p=verify(a.root)
            self.assertEqual(p['schema'],'sii-baseline-strengthening-v1')
            self.assertIn('spt_v1',p['reward_variants'])
            self.assertEqual(p['physics_dt_s'],.00005)
            (a.root/'REWARD_SPEC.json').write_text('{}')
            with self.assertRaises(ValueError):verify(a.root)


class ServerTests(unittest.TestCase):
    def test_portable_adapter_changes_only_runtime_assignment(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'adapter.py'
            original="from pathlib import Path\nUPSTREAM = Path('/old')\nGAMMA = .9995\n"
            path.write_text(original)
            self.assertEqual(relocated_adapter(path,Path('/new runtime/SimbaV2')),
                original.replace("Path('/old')", "Path('/new runtime/SimbaV2')"))
            self.assertEqual(path.read_text(),original)

    def test_gpu_command_uses_registered_device_and_hard_memory(self):
        from types import SimpleNamespace
        import prepare_rl_spt_campaign_20261025 as launcher
        p=dict(python='/python',source='/source',runtime='/runtime',source_base_commit='test',
               resources=dict(server_compute=True,gpu_uuid='GPU-0123',gpu_pool_fraction='0.8',
                              memory_max_bytes=8*1024**3,cpus=[2,3]))
        a=SimpleNamespace(root=Path('/new-run'),family='direct',stop_at_step=1375,
                          resume_checkpoint=None,dry_run=False)
        with patch.object(launcher,'verify',return_value=p),patch.object(launcher,'command'), \
                patch.object(launcher.subprocess,'call',return_value=0) as call:
            with self.assertRaises(SystemExit):launch(a)
        argv=call.call_args.args[0]
        for arg in ('--setenv=JAX_PLATFORMS=cuda','--setenv=CUDA_VISIBLE_DEVICES=GPU-0123',
                    '--property=MemoryMax=8589934592','--property=CPUAffinity=2 3'):
            self.assertIn(arg,argv)
        self.assertNotIn('--setenv=JAX_PLATFORMS=cpu',argv)

    def test_gpu_lease_overlap_and_ram_headroom(self):
        import spt_server_resources_20261025 as resource
        self.assertEqual(resource.memory_requirement(8*resource.GIB,[(8*resource.GIB,3*resource.GIB)]),
                         17*resource.GIB)
        with tempfile.TemporaryDirectory() as d:
            r=dict(lease_directory=d,gpu_uuid='GPU-0123',cpus=[1],max_parallel_jobs=5,
                   memory_max_bytes=8*resource.GIB,gpu_min_free_mib=8192,gpu_max_temperature_c=80)
            with patch.object(resource,'gpu_info',return_value=dict(free_mib=22000,temperature_c=40)), \
                    patch.object(resource.subprocess,'check_output',return_value=''), \
                    patch.object(resource,'memory_requirement',return_value=0):
                with resource.lease(r,Path('/run1'),'direct'):
                    with self.assertRaises(BlockingIOError):
                        with resource.lease(r,Path('/run2'),'vmc'):pass
                # The failed second lease must not retain CPU/GPU/slot locks.
                with resource.lease(r,Path('/run3'),'vmc'):pass

    def test_parallel_queue_stops_new_jobs_after_failure(self):
        from run_spt_server_parallel_20261025 import run_lanes
        calls=[]
        def execute(row):
            calls.append(row);return row!='bad'
        self.assertFalse(run_lanes({'GPU-one':['good','bad','never']},execute))
        self.assertEqual(calls,['good','bad'])


if __name__=='__main__':unittest.main()
