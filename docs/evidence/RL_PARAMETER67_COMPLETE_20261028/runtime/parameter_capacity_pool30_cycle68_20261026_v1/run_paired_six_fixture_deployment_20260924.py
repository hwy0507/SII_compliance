"""Execute an already audited18-job plan, only on explicit coordinator launch.

Default2 workers; global cap4 is coordinated using --available-worker-slots.
Task/gate failure is a valid result. Execution/alignment errors stop new launches;
already running jobs finish and remain archived. No overwrite/resume mode exists.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time
import traceback
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'tools'))
from canonical48_paired_deployment_20260924 import frozen_training,sha
from audit_paired_transitions_20260924 import exact,require,read
from prepare_paired_six_fixture_deployment_20260924 import verify_transition_audit

MODES=('parameter6','direct7','nominal_train_vmc')
UPSTREAM={f'fr3_link{i}' for i in range(5)}


def dump(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    temporary.replace(path)


def validate_plan(plan,path,expected):
    require(sha(path)==expected,'Plan SHA256 mismatch')
    require(plan['status']=='prepared_not_started' and plan['simulations_started']==0,'Plan is not an unstarted prepared matrix')
    require(plan['total_new_episodes']==18 and plan['global_worker_cap']==4,'Wrong frozen execution scope')
    jobs=plan['jobs']
    require(len(jobs)==18 and {(r['method'],r['fixture']['seed']) for r in jobs}=={(m,s) for m in MODES for s in range(9400,9406)},'Wrong18-job matrix')
    root=Path(jobs[0]['job']).resolve().parents[1]
    require(not path.resolve().is_relative_to(root),'Plan must be outside fresh execution output')
    for job in jobs:
        directory=root/job['method']/str(job['fixture']['seed'])
        require(Path(job['job']).resolve()==directory,'Job output escaped fixed matrix root')
        require(Path(job['result']).resolve()==directory/'rollout/rollout.json','Unexpected result path')
        command=job['command']
        require(command[1]==str(ROOT/'scripts/run_with_substep_metrics_20260923.py'),'Unexpected metrics wrapper')
        require(command[command.index('--runner')+1]==str(ROOT/'scripts/run_panel_paired_deployment_20260924.py'),'Unexpected policy runner')
        for flag,value in (('--output',directory/'rollout/rollout'),('--metrics-output',directory/'metrics'),('--paired-mode',job['method'])):
            require(command.count(flag)==1 and command[command.index(flag)+1]==str(value),'Unexpected command flag '+flag)
        branch='direct7' if job['method']=='direct7' else 'parameter6'
        for flag,value in (('--training-directory',plan['training'][branch]['directory']),('--deployment-device',plan['training'][branch]['device'])):
            require(command.count(flag)==1 and command[command.index(flag)+1]==value,'Training/device flag drift')
    return root


def verify_frozen(plan,path,expected,deep=False):
    require(sha(path)==expected,'Plan changed during execution')
    require(sha(ROOT/'docs/RL_PAIRED_SIX_FIXTURE_DEPLOYMENT_PROTOCOL_20260924.md')==plan['protocol_sha256'],'Deployment protocol changed')
    for name,value in plan['source_sha256'].items():
        candidate=(ROOT/name).resolve()
        require(candidate.is_relative_to(ROOT) and sha(candidate)==value,'Frozen deployment source changed: '+name)
    for mode,record in plan['training'].items():
        directory=Path(record['directory'])
        _,complete,_=frozen_training(directory,mode)
        require(sha(directory/'manifest.json')==record['manifest_sha256'],'Training manifest changed')
        for key in ('checkpoint_sha256','normalizer_sha256'):
            require(complete[key]==record[key],'Frozen training artifact changed')
    if deep:
        for name,value in plan['input_sha256'].items():
            require(sha(name)==value,'Frozen input changed: '+name)
        for mode,record in plan['training'].items():
            matches=[Path(name) for name,value in plan['input_sha256'].items() if value==record['transition_audit']['audit_sha256']]
            require(len(matches)==1,'Transition audit binding ambiguous')
            require(verify_transition_audit(matches[0],Path(record['directory']))==record['transition_audit'],'Transition audit source drift')
            replays=[Path(name) for name,value in plan['input_sha256'].items() if value==record['replay_sha256']]
            require(len(replays)==1,'Replay binding ambiguous')
            replay=read(replays[0])
            for name,value in replay['input_sha256'].items():
                require(sha(name)==value,'Replay original input/source drift')


def physical_raw_audit(path,physical,duration_s):
    """Same frozen metrics/formulas as report_classical_fixed_budget_20260923.

    Float32 raw vs float64 accumulators use its existing rtol1e-6/atol1e-7;
    permit genuine safety-short windows without relabeling them full24s.
    """
    count=round(duration_s/5e-5)
    require(physical['timestep_s']==5e-5 and physical['samples']==count and count>0,'Wrong50us sample count')
    with np.load(path,allow_pickle=False) as raw:
        require(set(raw.files)=={'time','stage','error','twist','qfrc_actuator','actuator_force'},'Physical array contract differs')
        require(all(raw[k].shape[0]==count and np.isfinite(raw[k]).all() for k in raw.files),'Missing/nonfinite physical data')
        require(raw['error'].shape==(count,3) and raw['twist'].shape==(count,6) and raw['qfrc_actuator'].shape==raw['actuator_force'].shape==(count,7),'Wrong physical vector shapes')
        times=raw['time']
        require(np.allclose(np.diff(times),5e-5,rtol=0,atol=1e-12),'Wrong50us timestamps')
        require(abs(times[0]-5e-5)<1e-10 and abs(times[-1]-duration_s)<1e-7,'Physical time endpoints differ')
        squared=np.square(raw['error'],dtype=np.float64)
        recomputed=dict(position_rmse_3d_m=float(np.sqrt(np.mean(squared.sum(axis=1)))),
            position_rmse_xyz_m=np.sqrt(np.mean(squared,axis=0)).tolist(),
            linear_speed_peak_mps=float(np.linalg.norm(raw['twist'][:,:3].astype(float),axis=1).max()),
            generalized_actuator_torque_peak_nm=float(np.abs(raw['qfrc_actuator']).max()))
        for key,value in recomputed.items():
            require(np.allclose(value,physical[key],rtol=1e-6,atol=1e-7),'Raw metric mismatch: '+key)
        stages=raw['stage']
        require(set(np.unique(stages))=={int(k) for k in physical['stages']},'Stage set mismatch')
        for stage,stats in physical['stages'].items():
            selected=stages==int(stage)
            require(int(selected.sum())==stats['count'],'Physical stage count mismatch')
            require(np.isclose(np.sqrt(np.mean(squared[selected].sum(axis=1))),stats['position_rmse_3d_m'],rtol=1e-6,atol=1e-7),'Physical stage RMSE mismatch')
    return dict(passed=True,samples=count,timestep_s=5e-5,recomputed=recomputed)


def validate_job(job,plan):
    path=Path(job['result']);root=Path(job['job'])
    result=read(path)
    require(sha(job['reference_result'])==job['reference_result_sha256'],'Original reference result changed')
    reference=read(job['reference_result'])
    require(result['source_sha256']==reference['source_sha256'],'Core runner source set/hash differs from original fixture')
    model_hash=sha(path.with_suffix('.mjb'))
    require(model_hash==job['expected_mjb_sha256'],'Per-fixture MJB differs')
    for field in ('scene','controller_6d_config','experiment_contract','simulation_timestep_s'):
        require(result[field]==reference[field],'Common configuration differs: '+field)
    for name,value in result['source_sha256'].items():
        require(sha(ROOT/'scripts'/name)==value,'Live runner source mismatch: '+name)
    require(not result['teacher_called'] and result['student_mixture']==0.,'Teacher intervention')
    require(result['contract']=='proprio48_action7_6d_v1','Wrong observation contract')
    branch='direct7' if job['method']=='direct7' else 'parameter6'
    training=plan['training'][branch]
    metadata=read(path.with_suffix('.paired_deployment.json'))
    manifest=read(Path(training['directory'])/'manifest.json')
    for key in ('checkpoint_sha256','normalizer_sha256'):
        require(metadata[key]==training[key],'Deployed artifact does not match frozen plan')
    require(metadata['mode']==job['method'] and metadata['device']==training['device'],'Deployment mode/device mismatch')
    require(metadata['training_manifest_sha256']==training['manifest_sha256'] and metadata['training_steps']==8192,'Wrong training origin')
    require(metadata['nominal_options']==manifest['nominal_options'],'Adapter did not use full training options')
    require(metadata['runtime_fixture_CORE_VMC_CONFIG']==json.loads(job['environment']['CORE_VMC_CONFIG']),'Fixture CORE changed')
    with np.load(path.with_suffix('.npz'),allow_pickle=False) as rollout,np.load(root/'rollout/paired_policy_trace.npz',allow_pickle=False) as policy,np.load(Path(job['reference_result']).with_suffix('.npz'),allow_pickle=False) as old:
        count=len(rollout['time'])
        require(1<=count<=600 and rollout['observation'].shape==(count,48) and rollout['action'].shape==(count,7),'Invalid actual rollout length/shape')
        require(count==600 or result['invalid_physics'],'Partial rollout without genuine safety termination')
        require(np.allclose(rollout['time'],np.arange(1,count+1)*.04,rtol=0,atol=1e-8),'Rollout25Hz grid mismatch')
        exact(rollout['observation'][0],old['observation'][0],'Original initial48D actor state')
        exact(policy['observation'],rollout['observation'],'Policy raw observation vs rollout')
        exact(policy['execution_action'],rollout['action'],'Policy action7 vs rollout')
        require(policy['observation'].dtype==np.float64,'Raw backend observation is not float64')
        dimension=7 if job['method']=='direct7' else 6
        require(policy['policy_action'].shape==(count,dimension),'Wrong learned request dimension')
        low=np.array([0]+[-1]*6) if dimension==7 else -np.ones(6)
        require(np.all(policy['policy_action']>=low) and np.all(policy['policy_action']<=1),'Policy requests outside Box')
        for key in ('log_scale','stiffness','damping'):
            require(policy[key].shape==(count,6),'Invalid parameter trace shape')
        if job['method']=='nominal_train_vmc':
            require(not np.any(policy['policy_action']) and not np.any(policy['log_scale']),'Nominal_train_vmc is not zero6')
        rmse25=float(np.sqrt(np.mean(np.sum((rollout['position']-rollout['target'])**2,axis=1))))
    require(abs(result['duration_s']-.04*count)<1e-6,'Duration/action count mismatch')
    numeric_arrays=0
    for file in root.rglob('*.npz'):
        with np.load(file,allow_pickle=False) as data:
            for key in data.files:
                if data[key].dtype.kind in 'fciu':
                    require(np.isfinite(data[key]).all(),'Nonfinite archived array: '+str(file)+':'+key)
                    numeric_arrays+=1
    metric_manifest=read(root/'metrics/audit_manifest.json')
    physical=read(root/'metrics/episode_0/substep_metrics.json')
    require(metric_manifest['enabled'] and metric_manifest['error'] is None and metric_manifest['episodes']==[physical],'Invalid physical measurement manifest')
    for name,value in metric_manifest['source_sha256'].items():
        require(plan['source_sha256']['scripts/'+name]==value,'Instrumented source mismatch')
    raw_audit=physical_raw_audit(root/'metrics/episode_0/substep_metrics.npz',physical,result['duration_s'])
    contacts=result['panel_audit']['contacts']
    external=[c for name,c in contacts.items() if name!='target_object_geom']
    upstream=any(set(c['bodies']) & UPSTREAM for c in external)
    return dict(task_success=bool(result['success']),strict_success=bool(result['accepted_panel_demo'] and not upstream),
        invalid_physics=bool(result['invalid_physics']),upstream=upstream,completed_24s=count==600,
        safety_terminated_early=count<600,actor_samples=count,physical=physical,raw_metric_audit=raw_audit,
        tracking_rmse_25hz_m=rmse25,tracking_rmse_substep_m=physical['position_rmse_3d_m'],
        actuator_torque_peak_nm=physical['generalized_actuator_torque_peak_nm'],linear_speed_peak_substep_mps=physical['linear_speed_peak_mps'],
        final_stage=result['final_stage'],fixture_triggered=result['fixture_triggered'],fixture_trigger_time_s=result['fixture_trigger_time_s'],
        rod_contact_s=contacts['push_rod_geom']['duration_s'],rod_first_contact_s=contacts['push_rod_geom']['first_s'],
        max_penetration_mm=1000*max(c['max_penetration_m'] for c in external),model_mjb_sha256=model_hash,
        result_sha256=sha(path),initial_actor_observation_exact=True,policy_trace_exact=True,numeric_arrays_finite=numeric_arrays)


def run_stage(jobs,worker,max_workers,stop,on_result):
    """Submit at most workers; never queue remaining work past an observed error."""
    remaining=iter(jobs)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        pending={}
        def fill():
            while len(pending)<max_workers and not stop.is_set():
                job=next(remaining,None)
                if job is None:break
                pending[pool.submit(worker,job)]=job
        fill()
        while pending:
            completed,_=wait(pending,return_when=FIRST_COMPLETED)
            for future in completed:
                job=pending.pop(future)
                try:row=future.result()
                except BaseException as error:
                    row=dict(job,execution_error=repr(error),traceback=traceback.format_exc())
                if 'execution_error' in row:stop.set()
                on_result(row)
            fill()


class Execution:
    def __init__(self,plan,path,expected,root,workers,timeout):
        self.plan,self.path,self.expected,self.root=plan,path,expected,root
        self.workers,self.timeout=workers,timeout
        self.stop=threading.Event();self.lock=threading.RLock()
        self.rows=[];self.active={};self.phase='preflight';self.started=time.time()
        self.driver_sha=sha(__file__)
        self.extra_sources={}

    def status(self):
        with self.lock:
            dump(self.root/'status.json',dict(status='stopping' if self.stop.is_set() else 'running',phase=self.phase,
                pid=os.getpid(),completed=len(self.rows),total=18,active=self.active,elapsed_s=time.time()-self.started,
                errors=sum('execution_error' in r for r in self.rows),plan_sha256=self.expected))

    def record(self,row):
        with self.lock:
            self.rows.append(row)
            dump(self.root/'results.json',dict(rows=self.rows))
            self.status()
            print(json.dumps(dict(completed=len(self.rows),method=row['method'],seed=row['fixture']['seed'],
                task=row.get('task_success'),gate=row.get('strict_success'),execution_error=row.get('execution_error'))),flush=True)

    def worker(self,job):
        row=dict(job);directory=Path(job['job']);key=job['method']+'/'+str(job['fixture']['seed'])
        started=time.time();process=None;owned=False
        try:
            directory.mkdir(parents=True,exist_ok=False)
            owned=True
            dump(directory/'command.json',job)
            require(sha(__file__)==self.driver_sha,'Execution driver changed')
            require(all(sha(ROOT/name)==value for name,value in self.extra_sources.items()),'Execution helper source changed')
            verify_frozen(self.plan,self.path,self.expected)
            if self.stop.is_set():raise RuntimeError('Coordinator stopped before launch')
            env=dict(os.environ)
            for name in list(env):
                if name.startswith(('PUSH_','PANEL_','CORE_VMC_','UNIFIED_','VMC_MODEL_CACHE_')) or name=='SKIP_MODEL_ARCHIVE':env.pop(name)
            env.update(job['environment'],OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',MUJOCO_GL='egl',PYTHONDONTWRITEBYTECODE='1',SKIP_MODEL_ARCHIVE='0')
            dump(directory/'runtime_environment.json',{name:env[name] for name in set(job['environment'])|{'OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','MUJOCO_GL','PYTHONDONTWRITEBYTECODE','SKIP_MODEL_ARCHIVE'}})
            with (directory/'run.log').open('x') as log:
                process=subprocess.Popen(job['command'],env=env,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
                row['worker_pid']=process.pid
                dump(directory/'PID.json',dict(pid=process.pid,parent_pid=os.getpid(),started_unix=started,command=job['command']))
                with self.lock:
                    self.active[key]=dict(pid=process.pid,started_unix=started,job=str(directory));self.status()
                try:returncode=process.wait(timeout=self.timeout)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    try:process.wait(timeout=15)
                    except subprocess.TimeoutExpired:process.kill();process.wait()
                    raise RuntimeError('Owned worker exceeded predeclared timeout')
            dump(directory/'exit.json',dict(returncode=returncode,pid=process.pid,elapsed_s=time.time()-started))
            require(returncode==0,'Runner nonzero exit: '+str(returncode))
            row.update(validate_job(job,self.plan))
            verify_frozen(self.plan,self.path,self.expected)
            require(sha(__file__)==self.driver_sha,'Driver changed while job ran')
            require(all(sha(ROOT/name)==value for name,value in self.extra_sources.items()),'Execution helper source changed')
            row['artifact_sha256']={str(p.relative_to(directory)):sha(p) for p in sorted(directory.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
        except BaseException as error:
            if process is not None and process.poll() is None:
                process.terminate()
                try:process.wait(timeout=15)
                except subprocess.TimeoutExpired:process.kill();process.wait()
            row.update(execution_error=repr(error),traceback=traceback.format_exc())
            self.stop.set()
        finally:
            row['elapsed_s']=time.time()-started
            # A collision with an existing job directory must never overwrite it.
            if owned and not (directory/'result.json').exists():
                dump(directory/'result.json',row)
            with self.lock:
                self.active.pop(key,None);self.status()
        return row


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--expected-plan-sha256',required=True)
    p.add_argument('--max-workers',type=int,default=2)
    p.add_argument('--available-worker-slots',type=int,required=True,help='Coordinator confirmed free slots under global cap4')
    p.add_argument('--job-timeout-s',type=int,default=1800)
    args=p.parse_args();args.plan=args.plan.resolve()
    require(1<=args.max_workers<=args.available_worker_slots<=4,'Workers must fit coordinator-confirmed slots and cap4')
    require(args.job_timeout_s>0,'Positive timeout required')
    plan=read(args.plan);root=validate_plan(plan,args.plan,args.expected_plan_sha256)
    require(not root.exists(),'Fresh output required; no overwrite/restart is supported')
    verify_frozen(plan,args.plan,args.expected_plan_sha256,deep=True)
    root.mkdir(parents=True,exist_ok=False)
    try:
        shutil.copy2(args.plan,root/'frozen_plan.json')
        snapshot=root/'source_snapshot'
        source_files={**plan['source_sha256'],str(Path(__file__).relative_to(ROOT)):sha(__file__),
            'tools/audit_paired_transitions_20260924.py':sha(ROOT/'tools/audit_paired_transitions_20260924.py')}
        for name,expected in source_files.items():
            destination=snapshot/name;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/name,destination)
            require(sha(destination)==expected,'Execution source snapshot differs')
        shutil.copy2(ROOT/'docs/RL_PAIRED_SIX_FIXTURE_DEPLOYMENT_PROTOCOL_20260924.md',root/'deployment_protocol.md')
        execution=Execution(plan,args.plan,args.expected_plan_sha256,root,args.max_workers,args.job_timeout_s)
        execution.extra_sources=source_files
        dump(root/'execution_manifest.json',dict(pid=os.getpid(),argv=sys.argv,started_unix=execution.started,
            plan_sha256=args.expected_plan_sha256,source_sha256=source_files,driver_sha256=execution.driver_sha,
            max_workers=args.max_workers,coordinator_confirmed_available_slots=args.available_worker_slots,global_worker_cap=4,
            runtime={name:importlib.metadata.version(name) for name in ('numpy','mujoco','torch','stable_baselines3')},
            python=sys.version,job_timeout_s=args.job_timeout_s,method='frozen final8192 with independent training nominal VMC; no selection'))
    except BaseException as error:
        dump(root/'FAILED.json',dict(phase='initialization_before_any_launch',error=repr(error),traceback=traceback.format_exc(),completed=0,simulations_started=0))
        dump(root/'status.json',dict(status='failed',phase='initialization',pid=os.getpid(),completed=0,total=18,active={}))
        raise
    def stop_requested(signum,_frame):
        execution.stop.set();execution.status()
    for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,stop_requested)
    try:
        execution.status()
        preflight=[job for job in plan['jobs'] if job['fixture']['seed']==9400]
        run_stage(preflight,execution.worker,args.max_workers,execution.stop,execution.record)
        require(not execution.stop.is_set() and len(execution.rows)==3,'Preflight error/stop; remaining15 not launched')
        dump(root/'PREFLIGHT_PASSED.json',dict(jobs=3,task_failures_retained=True,all_alignment_checks_passed=True,
            result_hashes={r['method']:sha(Path(r['job'])/'result.json') for r in execution.rows}))
        execution.phase='remaining15';execution.status()
        run_stage([job for job in plan['jobs'] if job['fixture']['seed']!=9400],execution.worker,args.max_workers,execution.stop,execution.record)
        require(not execution.stop.is_set() and len(execution.rows)==18,'Execution/alignment error or coordinator stop; remaining jobs not launched')
        verify_frozen(plan,args.plan,args.expected_plan_sha256,deep=True)
        require(all(sha(ROOT/name)==value for name,value in source_files.items()),'Source changed during full execution')
        dump(root/'COMPLETE.json',dict(status='complete',episodes=18,task={m:sum(r['task_success'] for r in execution.rows if r['method']==m) for m in MODES},
            gate={m:sum(r['strict_success'] for r in execution.rows if r['method']==m) for m in MODES},
            safety_short_episodes=sum(r['safety_terminated_early'] for r in execution.rows),plan_sha256=args.expected_plan_sha256,
            source_unchanged=True,elapsed_s=time.time()-execution.started))
        dump(root/'status.json',dict(status='complete',pid=os.getpid(),completed=18,total=18,active={}))
    except BaseException as error:
        dump(root/'FAILED.json',dict(error=repr(error),traceback=traceback.format_exc(),completed=len(execution.rows),
            not_launched=[dict(method=j['method'],seed=j['fixture']['seed']) for j in plan['jobs'] if (j['method'],j['fixture']['seed']) not in {(r['method'],r['fixture']['seed']) for r in execution.rows}],
            all_started_jobs_retained=True,plan_sha256=args.expected_plan_sha256))
        dump(root/'status.json',dict(status='failed',pid=os.getpid(),completed=len(execution.rows),total=18,active=execution.active))
        raise
    finally:
        dump(root/'FINAL_RESULT.json',dict(rows=execution.rows,execution_errors=sum('execution_error' in r for r in execution.rows),
            plan_sha256=args.expected_plan_sha256,planned_episodes=18))


if __name__=='__main__':main()
