"""Execute the reviewed25-job plan; never infer launch from preparation."""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'scripts')]
import run_paired_six_fixture_deployment_20260924 as old
import prepare_paired_multiseed_deployment_20260925 as prep
from audit_paired_transitions_20260924 import read, require
from canonical48_paired_deployment_20260924 import frozen_training, sha


def key(job):
    return f"{job['training_seed']}/{job['method']}/{job['fixture']['seed']}"


def stop_owned_process(process):
    """Bound both reap attempts; a stuck owned PID remains explicit evidence."""
    result=dict(pid=process.pid,terminate_sent=False,kill_sent=False,reaped=False,errors=[])
    for action in ('terminate','kill'):
        if process.poll() is not None:
            result['reaped']=True;result['returncode']=process.returncode;return result
        try:
            getattr(process,action)();result[action+'_sent']=True
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            result['errors'].append(action+' reap exceeded15s')
        except OSError as error:
            result['errors'].append(action+': '+repr(error))
    result['reaped']=process.poll() is not None
    result['returncode']=process.returncode
    return result


def validate_plan(plan, path, expected):
    require(sha(path) == expected, 'Plan SHA256 mismatch')
    require(plan['status']=='prepared_not_started' and plan['simulations_started']==0 and plan['preconditions_all_passed'], 'Not an audited unstarted plan')
    require(plan['total_new_episodes']==25 and plan['learned_episodes']==24 and plan['parity_episodes']==1 and plan['global_worker_cap']==4, 'Changed25-job scope')
    prep.matrix_keys(plan['jobs'])
    root = prep.absolute(plan['output'])
    require(not path.resolve().is_relative_to(root), 'Plan must be outside execution root')
    for job in plan['jobs']:
        directory = root/str(job['training_seed'])/job['method']/str(job['fixture']['seed'])
        require(Path(job['job']) == directory and Path(job['result']) == directory/'rollout/rollout.json', 'Job escaped fixed matrix path')
        command = job['command']
        branch = 'direct7' if job['method']=='direct7' else 'parameter6'
        record = plan['training'][str(job['training_seed'])][branch]
        expected_flags = {'--runner': ROOT/'scripts/run_panel_paired_deployment_20260924.py',
            '--metrics-output': directory/'metrics', '--output': directory/'rollout/rollout',
            '--paired-mode':job['method'], '--training-directory':record['directory'], '--deployment-device':record['device']}
        require(command[0]==sys.executable and command[1]==str(ROOT/'scripts/run_with_substep_metrics_20260923.py'), 'Unexpected execution wrapper/interpreter')
        for flag,value in expected_flags.items():
            require(command.count(flag)==1 and command[command.index(flag)+1]==str(value), 'Wrong command flag '+flag)
    return root


def verify_frozen(plan, path, expected, deep=False):
    require(sha(path)==expected and sha(ROOT/prep.PROTOCOL)==plan['protocol_sha256'], 'Plan/protocol drift')
    for name,value in plan['source_sha256'].items():
        candidate = (ROOT/name).resolve()
        require(candidate.is_relative_to(ROOT) and sha(candidate)==value, 'Frozen source drift: '+name)
    for seed, records in plan['training'].items():
        for mode, record in records.items():
            manifest,complete,_ = frozen_training(record['directory'], mode)
            require(manifest['training']['seed']==int(seed) and sha(Path(record['directory'])/'manifest.json')==record['manifest_sha256'], 'Training source seed/manifest drift')
            for field in ('checkpoint_sha256','normalizer_sha256'):
                require(complete[field]==record[field], 'Final artifact changed')
    if deep:
        for name,value in plan['input_sha256'].items(): require(sha(name)==value, 'Audited input changed: '+name)
        require(not (Path(plan['old_archive'])/'FAILED.json').exists(), 'Old archive gained FAILED marker')


class Execution:
    def __init__(self, plan, path, expected, root, timeout):
        self.plan,self.path,self.expected,self.root,self.timeout = plan,path,expected,root,timeout
        self.stop = threading.Event(); self.lock = threading.RLock()
        self.rows=[]; self.active={}; self.phase='nominal_parity'; self.started=time.time()

    def status(self):
        with self.lock:
            old.dump(self.root/'status.json', dict(status='stopping' if self.stop.is_set() else 'running',
                phase=self.phase,pid=os.getpid(),completed=len(self.rows),total=25,active=self.active,
                elapsed_s=time.time()-self.started,plan_sha256=self.expected))

    def record(self,row):
        with self.lock:
            self.rows.append(row); old.dump(self.root/'results.json',dict(rows=self.rows)); self.status()
            print(json.dumps(dict(job=key(row),completed=len(self.rows),task=row.get('task_success'),
                strict=row.get('strict_success'),execution_error=row.get('execution_error'))),flush=True)

    def worker(self,job):
        row=dict(job); directory=Path(job['job']); process=None; owned=False; started=time.time()
        try:
            verify_frozen(self.plan,self.path,self.expected)
            require(not self.stop.is_set(),'Stop requested before new launch')
            directory.mkdir(parents=True,exist_ok=False); owned=True
            old.dump(directory/'command.json',job)
            env=dict(os.environ)
            for name in list(env):
                if name.startswith(('PUSH_','PANEL_','CORE_VMC_','UNIFIED_','VMC_MODEL_CACHE_')) or name=='SKIP_MODEL_ARCHIVE': env.pop(name)
            env.update(job['environment'],OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
                MUJOCO_GL='egl',PYTHONDONTWRITEBYTECODE='1',SKIP_MODEL_ARCHIVE='0')
            old.dump(directory/'runtime_environment.json',{n:env[n] for n in set(job['environment'])|{'OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','MUJOCO_GL','PYTHONDONTWRITEBYTECODE','SKIP_MODEL_ARCHIVE'}})
            with (directory/'run.log').open('x') as log:
                process=subprocess.Popen(job['command'],env=env,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
                row['worker_pid']=process.pid
                old.dump(directory/'PID.json',dict(pid=process.pid,parent_pid=os.getpid(),started_unix=started,command=job['command']))
                with self.lock:
                    self.active[key(job)]=dict(pid=process.pid,job=str(directory));self.status()
                try: code=process.wait(timeout=self.timeout)
                except subprocess.TimeoutExpired:
                    row['owned_process_cleanup']=stop_owned_process(process)
                    raise RuntimeError('Owned worker exceeded fixed timeout')
            old.dump(directory/'exit.json',dict(returncode=code,pid=process.pid,elapsed_s=time.time()-started))
            require(code==0,'Runner nonzero exit: '+str(code))
            view=dict(training=self.plan['training'][str(job['training_seed'])],source_sha256=self.plan['source_sha256'])
            row.update(old.validate_job(job,view))
            verify_frozen(self.plan,self.path,self.expected)
            row['artifact_sha256']={str(p.relative_to(directory)):sha(p) for p in sorted(directory.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
        except BaseException as error:
            if process is not None and process.poll() is None and 'owned_process_cleanup' not in row:
                row['owned_process_cleanup']=stop_owned_process(process)
            row.update(execution_error=repr(error),traceback=traceback.format_exc());self.stop.set()
        finally:
            row['elapsed_s']=time.time()-started
            if owned and not (directory/'result.json').exists(): old.dump(directory/'result.json',row)
            with self.lock:
                if process is not None and process.poll() is None:
                    self.active[key(job)]=dict(pid=process.pid,job=str(directory),unreaped_owned_process=True,
                        cleanup=row.get('owned_process_cleanup'))
                else:
                    self.active.pop(key(job),None)
                self.status()
        return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--expected-plan-sha256',required=True)
    parser.add_argument('--available-worker-slots',type=int,required=True)
    parser.add_argument('--max-workers',type=int,default=2)
    args=parser.parse_args();args.plan=args.plan.resolve()
    require(1<=args.max_workers<=args.available_worker_slots<=4,'Workers exceed confirmed free slots/global cap4')
    plan=read(args.plan);root=validate_plan(plan,args.plan,args.expected_plan_sha256)
    require(not root.exists(),'Fresh output required; no overwrite/resume')
    # Reconstruct every command and audit from original request before any launch.
    require(prep.prepare(Path(plan['request']),root)==plan,'Plan no longer reconstructs from reviewed input evidence')
    verify_frozen(plan,args.plan,args.expected_plan_sha256,deep=True)
    root.mkdir(parents=True,exist_ok=False)
    execution=Execution(plan,args.plan,args.expected_plan_sha256,root,1800)
    try:
        shutil.copy2(args.plan,root/'frozen_plan.json')
        shutil.copy2(ROOT/prep.PROTOCOL,root/'deployment_protocol.md')
        for name,digest in plan['source_sha256'].items():
            destination=root/'source_snapshot'/name;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/name,destination);require(sha(destination)==digest,'Snapshot copy drift')
        old.dump(root/'execution_manifest.json',dict(plan_sha256=args.expected_plan_sha256,source_sha256=plan['source_sha256'],
            driver_sha256=sha(__file__),max_workers=args.max_workers,coordinator_confirmed_available_slots=args.available_worker_slots,
            job_timeout_s=1800,global_worker_cap=4,pid=os.getpid(),argv=sys.argv,started_unix=execution.started,
            runtime={name:importlib.metadata.version(name) for name in ('numpy','mujoco','torch','stable_baselines3')}))
        def stop(_signum,_frame): execution.stop.set();execution.status()
        for sig in (signal.SIGINT,signal.SIGTERM): signal.signal(sig,stop)
        nominal=[j for j in plan['jobs'] if j['method']=='nominal_train_vmc']
        old.run_stage(nominal,execution.worker,1,execution.stop,execution.record)
        require(not execution.stop.is_set() and len(execution.rows)==1,'Nominal execution failed; no learned jobs started')
        parity=prep.nominal_parity(plan['nominal_reference'],nominal[0]['job'])
        old.dump(root/'NOMINAL_REUSE_PARITY.json',dict(parity,old_report_sha256=plan['old_report_sha256'],
            reference=plan['nominal_reference'],current=nominal[0]['job'],reuse_fixture_seeds=list(prep.FIXTURES)))
        execution.phase='four_model_preflight';execution.status()
        learned=[j for j in plan['jobs'] if j['method'] in prep.MODES]
        old.run_stage([j for j in learned if j['fixture']['seed']==9400],execution.worker,args.max_workers,execution.stop,execution.record)
        require(not execution.stop.is_set() and len(execution.rows)==5,'Model preflight error; remaining20 not started')
        old.dump(root/'PREFLIGHT_PASSED.json',dict(jobs=5,nominal_parity=True,task_failures_retained=True))
        execution.phase='remaining20';execution.status()
        old.run_stage([j for j in learned if j['fixture']['seed']!=9400],execution.worker,args.max_workers,execution.stop,execution.record)
        require(not execution.stop.is_set() and len(execution.rows)==25,'Incomplete deployment; retain all attempted jobs')
        verify_frozen(plan,args.plan,args.expected_plan_sha256,deep=True)
        old.dump(root/'COMPLETE.json',dict(status='complete',episodes=25,learned_episodes=24,parity_episodes=1,
            nominal_reuse_parity_sha256=sha(root/'NOMINAL_REUSE_PARITY.json'),plan_sha256=args.expected_plan_sha256,
            source_unchanged=True,elapsed_s=time.time()-execution.started))
        old.dump(root/'status.json',dict(status='complete',pid=os.getpid(),completed=25,total=25,active={}))
    except BaseException as error:
        old.dump(root/'FAILED.json',dict(error=repr(error),traceback=traceback.format_exc(),completed=len(execution.rows),
            not_launched=[key(j) for j in plan['jobs'] if key(j) not in {key(r) for r in execution.rows}],
            all_started_jobs_retained=True,plan_sha256=args.expected_plan_sha256))
        old.dump(root/'status.json',dict(status='failed',pid=os.getpid(),completed=len(execution.rows),total=25,active=execution.active))
        raise
    finally:
        old.dump(root/'FINAL_RESULT.json',dict(rows=execution.rows,execution_errors=sum('execution_error' in r for r in execution.rows),
            plan_sha256=args.expected_plan_sha256,planned_episodes=25))


if __name__=='__main__':main()
