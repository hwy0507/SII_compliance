"""Run only the explicitly reviewed SAC13 plan; zero7 parity gates all policies."""
from __future__ import annotations
import argparse
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
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'scripts')]
import prepare_sac_deployment_20260925 as prep
import run_paired_six_fixture_deployment_20260924 as old
from run_paired_multiseed_deployment_20260925 import stop_owned_process
from canonical48_sac_deployment_20260925 import frozen_training,sha
from audit_paired_transitions_20260924 import read,require


def key(job):return f"{job['method']}/{job['fixture']['seed']}"


def validate_metadata(metadata,record,job):
    require(metadata['algorithm']=='standard SAC' and metadata['branch']==job['method']==record['branch'],'SAC algorithm/branch mismatch')
    require(metadata['mode']=='direct7' and metadata['device']==metadata['trained_device']==record['device']=='cuda','SAC mode/device mismatch')
    require(metadata['seed']==record['seed']==20260923 and metadata['training_steps']==8192 and metadata['training_updates']==8092,'SAC final budget differs')
    for field in ('checkpoint_sha256','normalizer_sha256'):require(metadata[field]==record[field],'SAC final artifact differs')
    require(metadata['training_manifest_sha256']==record['manifest_sha256'] and metadata['training_complete_sha256']==record['complete_sha256'],'SAC manifest/COMPLETE differs')
    require(metadata['nominal_options']==record['nominal_options'] and not metadata['adapter_active'],'SAC backend options differ')
    require(metadata['runtime_fixture_CORE_VMC_CONFIG']==json.loads(job['environment']['CORE_VMC_CONFIG']),'SAC runtime fixture differs')


def validate_job(job,plan):
    if job['method'] in prep.BRANCHES:
        record=plan['training'][job['method']]
        validate_metadata(read(Path(job['result']).with_suffix('.paired_deployment.json')),record,job)
        # This projection calls only unchanged direct7 physics/trace checks. SAC
        # provenance and 8092 optimizer budget are separately enforced above.
        projected=dict(job,method='direct7')
        result=old.validate_job(projected,dict(training={'direct7':record},source_sha256=plan['source_sha256']))
        return dict(result,algorithm='standard SAC',branch=job['method'],training_seed=20260923)
    require(job['method']=='zero7','Undeclared job')
    folder=Path(job['job']);result=read(job['result']);reference=read(job['reference_result'])
    require(sha(job['reference_result'])==job['reference_result_sha256'],'Zero fixture reference changed')
    require(sha(Path(job['result']).with_suffix('.mjb'))==job['expected_mjb_sha256'],'Zero MJB differs')
    for field in ('scene','controller_6d_config','experiment_contract','simulation_timestep_s','source_sha256'):
        require(result[field]==reference[field],'Zero physical configuration differs')
    require(not result['teacher_called'] and result['student_mixture']==0. and result['contract']=='proprio48_action7_6d_v1','Zero7 contract differs')
    for name,value in result['source_sha256'].items():require(plan['source_sha256'].get('scripts/'+name)==value,'Zero physics source differs')
    with np.load(Path(job['result']).with_suffix('.npz'),allow_pickle=False) as raw:
        require(raw['action'].shape==(600,7) and not np.any(raw['action']) and raw['observation'].shape==(600,48),'Zero must be full600 zero7')
    physical=read(folder/'metrics/episode_0/substep_metrics.json');measurement=read(folder/'metrics/audit_manifest.json')
    require(measurement['enabled'] and measurement['error'] is None and measurement['episodes']==[physical],'Zero measurement failure')
    for name,value in measurement['source_sha256'].items():require(plan['source_sha256'].get('scripts/'+name)==value,'Zero measurement source differs')
    audit=old.physical_raw_audit(folder/'metrics/episode_0/substep_metrics.npz',physical,result['duration_s'])
    return dict(task_success=bool(result['success']),physical=physical,raw_metric_audit=audit,
        model_mjb_sha256=sha(Path(job['result']).with_suffix('.mjb')),result_sha256=sha(job['result']),completed_24s=True)


def validate_plan(plan,path,expected):
    require(sha(path)==expected and plan['status']=='prepared_not_started' and plan['simulations_started']==0 and plan['preconditions_all_passed'],'Plan not reviewed/unstarted')
    require(plan['algorithm']=='standard SAC' and (plan['total_new_episodes'],plan['learned_episodes'],plan['parity_episodes'])==(13,12,1),'Changed SAC13 scope')
    require(plan['global_worker_cap']==4 and plan['max_workers']==2 and plan['job_timeout_s']==1800,'Resource budget drift')
    prep.matrix_keys(plan['jobs']);root=prep.absolute(plan['output']);require(not path.resolve().is_relative_to(root),'Plan inside execution root')
    for job in plan['jobs']:
        folder=root/job['method']/str(job['fixture']['seed']);require(Path(job['job'])==folder and Path(job['result'])==folder/'rollout/rollout.json','Job path escaped matrix')
        command=job['command'];zero=job['method']=='zero7'
        require(command[0]==sys.executable and command[1]==str(ROOT/'scripts/run_with_substep_metrics_20260923.py'),'Wrong interpreter/wrapper')
        flags={'--runner':ROOT/'scripts'/('run_panel_zero_20260924.py' if zero else 'run_panel_sac_deployment_20260925.py'),
               '--metrics-output':folder/'metrics','--output':folder/'rollout/rollout'}
        if not zero:flags.update({'--sac-branch':job['method'],'--training-directory':plan['training'][job['method']]['directory'],'--deployment-device':'cuda'})
        for flag,value in flags.items():require(command.count(flag)==1 and command[command.index(flag)+1]==str(value),'Wrong frozen command flag: '+flag)
        if zero:require('--sac-branch' not in command and '--training-directory' not in command and '--model' not in command,'Zero may not load an actor')
    return root


def verify_frozen(plan,path,expected,deep=False):
    require(sha(path)==expected and sha(ROOT/prep.PROTOCOL)==plan['protocol_sha256'],'Plan/protocol drift')
    for name,value in plan['source_sha256'].items():require((ROOT/name).resolve().is_relative_to(ROOT) and sha(ROOT/name)==value,'Frozen source drift: '+name)
    for branch,record in plan['training'].items():
        manifest,complete,_=frozen_training(record['directory'],branch)
        require(sha(Path(record['directory'])/'manifest.json')==record['manifest_sha256'] and sha(Path(record['directory'])/'COMPLETE.json')==record['complete_sha256'],'Training manifest/COMPLETE drift')
        require(manifest['data_budget']==record['data_budget'],'Training data budget drift')
        for field in ('checkpoint_sha256','normalizer_sha256'):require(complete[field]==record[field],'Final artifact drift')
    if deep:
        for name,value in plan['input_sha256'].items():require(sha(name)==value,'Bound input drift: '+name)
        require(not (Path(plan['zero_archive'])/'FAILED.json').exists(),'Reference archive failed')
        import torch
        runtime=dict(python=sys.version,mujoco=importlib.metadata.version('mujoco'),numpy=np.__version__,torch=torch.__version__,
            sb3=importlib.metadata.version('stable_baselines3'),cuda_available=torch.cuda.is_available(),cuda_runtime=torch.version.cuda,
            gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)
        require(all(record['runtime']==runtime for record in plan['training'].values()),'Same-DGX runtime differs from SAC training')


class Execution:
    def __init__(self,plan,path,expected,root):
        self.plan,self.path,self.expected,self.root=plan,path,expected,root
        self.stop=threading.Event();self.lock=threading.RLock();self.rows=[];self.active={};self.phase='zero7_parity';self.started=time.time()

    def status(self):
        with self.lock:old.dump(self.root/'status.json',dict(status='stopping' if self.stop.is_set() else 'running',phase=self.phase,pid=os.getpid(),completed=len(self.rows),total=13,active=self.active,elapsed_s=time.time()-self.started,plan_sha256=self.expected))

    def record(self,row):
        with self.lock:
            self.rows.append(row);old.dump(self.root/'results.json',dict(rows=self.rows));self.status()
            print(json.dumps(dict(job=key(row),completed=len(self.rows),task=row.get('task_success'),strict=row.get('strict_success'),execution_error=row.get('execution_error'))),flush=True)

    def worker(self,job):
        row=dict(job);folder=Path(job['job']);process=None;owned=False;started=time.time()
        try:
            verify_frozen(self.plan,self.path,self.expected);require(not self.stop.is_set(),'Stopped before launch')
            folder.mkdir(parents=True,exist_ok=False);owned=True;old.dump(folder/'command.json',job)
            env=dict(os.environ)
            for name in list(env):
                if name.startswith(('PUSH_','PANEL_','CORE_VMC_','UNIFIED_','VMC_MODEL_CACHE_')) or name=='SKIP_MODEL_ARCHIVE':env.pop(name)
            env.update(job['environment'],OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',MUJOCO_GL='egl',PYTHONDONTWRITEBYTECODE='1',SKIP_MODEL_ARCHIVE='0')
            old.dump(folder/'runtime_environment.json',{n:env[n] for n in set(job['environment'])|{'OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','MUJOCO_GL','PYTHONDONTWRITEBYTECODE','SKIP_MODEL_ARCHIVE'}})
            with (folder/'run.log').open('x') as log:
                process=subprocess.Popen(job['command'],env=env,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT);row['worker_pid']=process.pid
                old.dump(folder/'PID.json',dict(pid=process.pid,parent_pid=os.getpid(),started_unix=started,command=job['command']))
                with self.lock:self.active[key(job)]=dict(pid=process.pid,job=str(folder));self.status()
                try:code=process.wait(timeout=1800)
                except subprocess.TimeoutExpired:
                    row['owned_process_cleanup']=stop_owned_process(process);raise RuntimeError('Owned worker exceeded1800s')
            old.dump(folder/'exit.json',dict(returncode=code,pid=process.pid,elapsed_s=time.time()-started));require(code==0,'Runner nonzero exit: '+str(code))
            row.update(validate_job(job,self.plan));verify_frozen(self.plan,self.path,self.expected)
            row['artifact_sha256']={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
        except BaseException as error:
            if process is not None and process.poll() is None and 'owned_process_cleanup' not in row:row['owned_process_cleanup']=stop_owned_process(process)
            row.update(execution_error=repr(error),traceback=traceback.format_exc());self.stop.set()
        finally:
            row['elapsed_s']=time.time()-started
            if owned and not (folder/'result.json').exists():old.dump(folder/'result.json',row)
            with self.lock:
                if process is not None and process.poll() is None:self.active[key(job)]=dict(pid=process.pid,job=str(folder),unreaped_owned_process=True,cleanup=row.get('owned_process_cleanup'))
                else:self.active.pop(key(job),None)
                self.status()
        return row


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',type=Path,required=True);parser.add_argument('--expected-plan-sha256',required=True)
    parser.add_argument('--available-worker-slots',type=int,required=True);parser.add_argument('--max-workers',type=int,default=2);args=parser.parse_args();args.plan=args.plan.resolve()
    require(1<=args.max_workers<=2 and args.max_workers<=args.available_worker_slots<=4,'Exceeds reviewed worker budget')
    plan=read(args.plan);root=validate_plan(plan,args.plan,args.expected_plan_sha256);require(not root.exists(),'Fresh output required; no overwrite/retry')
    require(prep.prepare(Path(plan['request']),root)==plan,'Concrete reviewed plan no longer reconstructs');verify_frozen(plan,args.plan,args.expected_plan_sha256,deep=True)
    root.mkdir(parents=True,exist_ok=False);execution=Execution(plan,args.plan,args.expected_plan_sha256,root)
    try:
        shutil.copy2(args.plan,root/'frozen_plan.json');shutil.copy2(ROOT/prep.PROTOCOL,root/'deployment_protocol.md')
        for name,value in plan['source_sha256'].items():
            destination=root/'source_snapshot'/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,destination);require(sha(destination)==value,'Archive source copy drift')
        old.dump(root/'execution_manifest.json',dict(plan_sha256=args.expected_plan_sha256,source_sha256=plan['source_sha256'],driver_sha256=sha(__file__),max_workers=args.max_workers,
            coordinator_confirmed_available_slots=args.available_worker_slots,job_timeout_s=1800,global_worker_cap=4,pid=os.getpid(),argv=sys.argv,started_unix=execution.started,
            runtime={name:importlib.metadata.version(name) for name in ('numpy','mujoco','torch','stable_baselines3')}))
        def stop(_signum,_frame):execution.stop.set();execution.status()
        for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,stop)
        zero=[j for j in plan['jobs'] if j['method']=='zero7'];old.run_stage(zero,execution.worker,1,execution.stop,execution.record)
        require(not execution.stop.is_set() and len(execution.rows)==1,'Zero7 execution failed; no learned launch')
        parity=prep.zero_parity(plan['zero_reference'],zero[0]['job'])
        old.dump(root/'ZERO7_REUSE_PARITY.json',dict(parity,zero_report_sha256=plan['zero_report_sha256'],reference=plan['zero_reference'],current=zero[0]['job'],reuse_fixture_seeds=list(prep.FIXTURES)))
        execution.phase='both_sac9400';execution.status();learned=[j for j in plan['jobs'] if j['method'] in prep.BRANCHES]
        old.run_stage([j for j in learned if j['fixture']['seed']==9400],execution.worker,args.max_workers,execution.stop,execution.record)
        require(not execution.stop.is_set() and len(execution.rows)==3,'SAC9400 execution failed; remaining10 not launched')
        old.dump(root/'PREFLIGHT_PASSED.json',dict(jobs=3,zero7_parity=True,task_failures_retained=True))
        execution.phase='remaining10';execution.status();old.run_stage([j for j in learned if j['fixture']['seed']!=9400],execution.worker,args.max_workers,execution.stop,execution.record)
        require(not execution.stop.is_set() and len(execution.rows)==13,'Incomplete SAC13');verify_frozen(plan,args.plan,args.expected_plan_sha256,deep=True)
        old.dump(root/'COMPLETE.json',dict(status='complete',algorithm='standard SAC',episodes=13,learned_episodes=12,parity_episodes=1,
            zero7_reuse_parity_sha256=sha(root/'ZERO7_REUSE_PARITY.json'),plan_sha256=args.expected_plan_sha256,source_unchanged=True,elapsed_s=time.time()-execution.started))
        old.dump(root/'status.json',dict(status='complete',pid=os.getpid(),completed=13,total=13,active={}))
    except BaseException as error:
        old.dump(root/'FAILED.json',dict(error=repr(error),traceback=traceback.format_exc(),completed=len(execution.rows),not_launched=[key(j) for j in plan['jobs'] if key(j) not in {key(r) for r in execution.rows}],all_started_jobs_retained=True,plan_sha256=args.expected_plan_sha256))
        old.dump(root/'status.json',dict(status='failed',pid=os.getpid(),completed=len(execution.rows),total=13,active=execution.active));raise
    finally:old.dump(root/'FINAL_RESULT.json',dict(rows=execution.rows,execution_errors=sum('execution_error' in r for r in execution.rows),plan_sha256=args.expected_plan_sha256,planned_episodes=13))


if __name__=='__main__':main()
