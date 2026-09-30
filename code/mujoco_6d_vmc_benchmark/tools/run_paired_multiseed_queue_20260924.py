"""Freeze four predeclared paired runs, then execute two at a time by seed."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import traceback

os.environ.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
SOURCE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SOURCE/'tools'))
import run_canonical48_paired_multiseed_20260924 as entry
base=entry.base

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def dump(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    temporary.replace(path)

def require(ok,message):
    if not ok: raise ValueError(message)

def source_manifest():
    return {str(p.relative_to(SOURCE)):sha(p) for p in sorted(SOURCE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}

def run_seed_pairs(jobs,worker,stop):
    """Do not queue another seed after failure; await both already started runs."""
    for seed in entry.SEEDS:
        require(not stop.is_set(),'Previous paired seed failed; later seed not started')
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(worker,j) for j in jobs if j['seed']==seed]
            for future in futures:future.result()

def terminate_owned(process):
    """Bounded cleanup only of the new session created by this worker."""
    if process is None or process.poll() is not None:return
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=15)

def preflight(args):
    require(not (args.root/'PLAN.json').exists(),'Plan already exists')
    require(not (args.root/'training').exists(),'Training outputs must be fresh')
    base.resource_check()
    require(base.torch.cuda.is_available(),'DGX CUDA unavailable')
    require(len(os.sched_getaffinity(0))>6,'CPU5/6 unavailable')
    specs,intersections=base.load_fixture_specs(args.assets)
    nominal=json.loads(specs['train']['command']['environment']['CORE_VMC_CONFIG'])
    runtime=dict(python=sys.version,mujoco=base.mujoco.__version__,numpy=base.np.__version__,
        torch=base.torch.__version__,sb3=base.sb3.__version__,cuda_available=True,
        cuda_runtime=base.torch.version.cuda,gpu=base.torch.cuda.get_device_name())
    evidence=dict(source_hashes=base.source_hashes(),fixture_specs=specs,asset_hashes=base.asset_hashes(args.menagerie),
        runtime=runtime,device='cuda',nominal_options=nominal,
        base_protocol_sha256=sha(SOURCE/'docs/RL_PARAMETER_ACTION_PAIRED_PROTOCOL_20260924.md'))
    evidence['proof_reuse']=entry.validate_proofs(args.proof_root,evidence)
    evidence.update(passed=True,simulations_started=0,gradient_updates=0,source_sha256=source_manifest(),
        split_intersections=intersections,cpu_affinity_available=sorted(os.sched_getaffinity(0)),
        protocol_sha256=sha(SOURCE/entry.PROTOCOL))
    jobs=[]
    for seed in entry.SEEDS:
        for mode,cpu in (('parameter6',5),('direct7',6)):
            output=args.root/'training'/str(seed)/mode
            jobs.append(dict(seed=seed,mode=mode,cpu_offset=cpu,output=str(output),
                command=[sys.executable,str(SOURCE/'tools/run_canonical48_paired_multiseed_20260924.py'),
                    '--seed',str(seed),'--mode',mode,'--output',str(output),'--assets',str(args.assets),
                    '--menagerie',str(args.menagerie),'--proof-root',str(args.proof_root),'--cpu-offset',str(cpu)]))
    dump(args.root/'PREFLIGHT.json',evidence)
    plan=dict(status='prepared_not_started',simulations_started=0,jobs=jobs,max_workers=2,global_cap=4,
        job_timeout_s=7200,source_sha256=evidence['source_sha256'],asset_hashes=evidence['asset_hashes'],
        proof_reuse=evidence['proof_reuse'],preflight_sha256=sha(args.root/'PREFLIGHT.json'),
        protocol_sha256=evidence['protocol_sha256'],menagerie=str(args.menagerie),
        python=sys.executable,source=str(SOURCE),no_model_selection=True)
    with (args.root/'PLAN.json').open('x') as stream: json.dump(plan,stream,indent=2)
    print(json.dumps(dict(passed=True,jobs=4,simulations_started=0,plan_sha256=sha(args.root/'PLAN.json'))),flush=True)

def execute(args):
    path=args.root/'PLAN.json'
    require(sha(path)==args.expected_plan_sha256,'Wrong frozen plan')
    plan=json.loads(path.read_text())
    require(plan['status']=='prepared_not_started' and plan['max_workers']==2 and plan['global_cap']==4,'Wrong execution scope')
    require([(j['seed'],j['mode']) for j in plan['jobs']]==[(s,m) for s in entry.SEEDS for m in ('parameter6','direct7')],'Wrong four-run matrix')
    require(2<=args.available_worker_slots<=4,'Need two coordinator-confirmed slots')
    require(not (args.root/'training').exists() and not (args.root/'EXECUTION.json').exists(),'No overwrite/restart allowed')
    def frozen():
        require(sha(path)==args.expected_plan_sha256,'Plan drift')
        require(source_manifest()==plan['source_sha256'],'Source drift')
        require(base.asset_hashes(Path(plan['menagerie']))==plan['asset_hashes'],'Assets drift')
        require(sha(args.root/'PREFLIGHT.json')==plan['preflight_sha256'],'Preflight drift')
        for mode,record in plan['proof_reuse'].items():
            for name,key in (('manifest.json','manifest_sha256'),('PARITY.json','parity_sha256'),('COMPLETE.json','complete_sha256')):
                require(sha(args.proof_root/mode/name)==record[key],'Proof drift')
    frozen();base.resource_check()
    args.root.joinpath('logs').mkdir(exist_ok=False)
    dump(args.root/'EXECUTION.json',dict(pid=os.getpid(),argv=sys.argv,started_unix=time.time(),
        plan_sha256=args.expected_plan_sha256,available_worker_slots=args.available_worker_slots,max_workers=2))
    rows=[];active={};lock=threading.RLock();start=time.time();stop=threading.Event()
    def status(state='running'):
        with lock: dump(args.root/'status.json',dict(status=state,pid=os.getpid(),completed=len(rows),total=4,
            active=active,errors=sum('execution_error' in row for row in rows),elapsed_s=time.time()-start,
            plan_sha256=args.expected_plan_sha256))
    def worker(job):
        process=None;row=dict(job);key=str(job['seed'])+'/'+job['mode'];began=time.time()
        try:
            frozen()
            require(not stop.is_set(),'Queue stopped before launch')
            require(not Path(job['output']).exists(),'Output collision')
            env=dict(os.environ,MUJOCO_GL='egl',PYTHONDONTWRITEBYTECODE='1')
            for name in list(env):
                if name.startswith(('PUSH_','PANEL_','CORE_VMC_','UNIFIED_','VMC_MODEL_CACHE_')) or name=='SKIP_MODEL_ARCHIVE': env.pop(name)
            with (args.root/'logs'/f"{job['seed']}_{job['mode']}.log").open('x') as stream:
                process=subprocess.Popen(job['command'],cwd=SOURCE,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                row['pid']=process.pid
                with lock:
                    active[key]=dict(pid=process.pid,command=job['command'],started_unix=began);status()
                try: code=process.wait(timeout=plan['job_timeout_s'])
                except subprocess.TimeoutExpired:
                    terminate_owned(process)
                    raise RuntimeError('Predeclared7200s timeout; run retained, no retry')
            row['returncode']=code
            output=Path(job['output'])
            require(code==0 and not (output/'FAILED.json').exists() and (output/'COMPLETE.json').is_file(),'Run execution failed; inspect original log/FAILED')
            done=json.loads((output/'COMPLETE.json').read_text())
            require(done['seed']==job['seed'] and done['mode']==job['mode'] and done['training_steps']==done['recorded_transitions']==8192,'Final scope mismatch')
            require(done['updates']==384 and done['source_unchanged'] and done['normalization_frozen'],'Final contract mismatch')
            require(sha(output/'ppo_final.zip')==done['checkpoint_sha256'] and sha(output/'vecnormalize_train_only.pkl')==done['normalizer_sha256'],'Final artifacts drift')
            frozen();row['complete']=done;row['complete_sha256']=sha(output/'COMPLETE.json')
        except BaseException as error:
            stop.set();row.update(execution_error=repr(error),traceback=traceback.format_exc())
        finally:
            try:terminate_owned(process)
            except BaseException as cleanup_error:
                stop.set();row.setdefault('execution_error','Owned process cleanup failed')
                row['cleanup_error']=repr(cleanup_error)
            row['elapsed_s']=time.time()-began
            with lock:
                rows.append(row);active.pop(key,None);dump(args.root/'results.json',dict(rows=rows));status()
        return row
    try:
        status()
        run_seed_pairs(plan['jobs'],worker,stop)
        require(not stop.is_set() and len(rows)==4,'Execution failure; no retry')
        frozen();dump(args.root/'COMPLETE.json',dict(status='complete',runs=4,rows=rows,elapsed_s=time.time()-start));status('complete')
    except BaseException as error:
        dump(args.root/'FAILED.json',dict(error=repr(error),traceback=traceback.format_exc(),completed=len(rows),all_started_runs_retained=True));status('failed');raise

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--phase',choices=('prepare','run'),required=True)
    for name in ('root','assets','menagerie','proof-root'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--expected-plan-sha256');p.add_argument('--available-worker-slots',type=int,default=0)
    args=p.parse_args()
    for name in ('root','assets','menagerie','proof_root'):setattr(args,name,getattr(args,name).resolve())
    require(args.root.is_dir(),'Fresh isolated source root must already exist')
    preflight(args) if args.phase=='prepare' else execute(args)

if __name__=='__main__':main()
