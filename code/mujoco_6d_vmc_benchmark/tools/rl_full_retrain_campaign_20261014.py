"""From-scratch online retraining of all four frozen RL baseline interfaces.

This campaign intentionally keeps the frozen office-v5 model, task gates,
canonical48 actor input, common action filter, actuator limits, and formal
dt=5e-5.  Each method learns only from its own live MuJoCo transitions.  The
two lane wrapper uses RLIMIT_AS as a local fallback when the desktop app's
read-only cgroup has no memory.max; the trainer records and verifies that
limit before the first simulation step.
"""
from datetime import datetime, timedelta, timezone
import argparse, hashlib, json, os, platform, shutil, subprocess, sys, time
from pathlib import Path

from office_v7_uniform24_20261008 import read, write, sha

PY = Path('/home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python')
BENCH = Path(__file__).resolve().parents[1]
RUNTIME = BENCH/'outputs/baseline_local_rl_20261009/runtime'
PARAMETER = BENCH/'outputs/rl_online_convergence_20261014_v7/parameter_fullrange'
REFERENCE = BENCH/'outputs/rl_online_convergence_20261014_v7/teacher.json'
SEED = 2026101421
STEPS = 500000


def prepare(root: Path, parent: Path):
    if root.exists():
        raise FileExistsError(root)
    root.mkdir(parents=True)
    old = read(parent/'PROTOCOL.json')
    shutil.copy2(parent/'CONDITIONS.json', root/'CONDITIONS.json')
    shutil.copy2(parent/'teacher.json', root/'teacher.json')
    shutil.copy2(parent/'RUNTIME_VERSIONS.json', root/'RUNTIME_VERSIONS.json')
    shutil.copytree(PARAMETER, root/'parameter_fullrange',
                    ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    start = datetime.now(timezone.utc)
    protocol = dict(old)
    protocol.update(
        schema='sii-baseline-strengthening-v1',
        registered_utc=start.isoformat(),
        authorization='2026-10-14 user: retrain every RL method from live MuJoCo interaction and report only after all methods complete and pass Task+Strict; local compute only',
        compute_host='airpig',
        source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=BENCH,text=True).strip(),
        condition_file_sha256=sha(root/'CONDITIONS.json'),
        training_dispatch_deadline_utc=(start+timedelta(hours=72)).isoformat(),
        deadline_basis='Finite 72h safety horizon for the user-authorized open-ended retraining; finish started episodes and preserve failures',
        budgets=dict(training_seeds=[SEED], rl_steps_per_family_seed=STEPS,
                     diagnostic_segment_steps=0, smoke_steps=1375,
                     planned_max_new_interactions=4*STEPS, optimizer_schedule_steps=STEPS),
        resources=dict(host='airpig', server_compute=False, simulators=2,
                       numerical_threads=1, per_lane_memory_max_bytes=3*1024**3,
                       swap_max_bytes=0, memory_enforcement='RLIMIT_AS fallback only when inherited desktop cgroup is read-only; otherwise MemoryMax=3GiB',
                       cpu_affinity=['1','6'], gpu='disabled; JAX_PLATFORMS=cpu'),
        unchanged=['MJB geometry/contact/friction','planner/target','task and strict gates',
                   'actor canonical48 proprioceptive fields','actuator amplitude/slew','common action filter'],
        purity='From-scratch online RL only; no teacher demonstrations, BC, replay imports, or privileged actor fields',
        selection='Latest complete episode-boundary checkpoint at the registered 500000-interaction limit; no best-of-test selection',
        evaluation=dict(phase='acceptance', condition='repair_acceptance_000', task_and_strict_required=True,
                        frozen_test_after_all_training=True),
        cooperative_stop_file=str(root/'STOP_REQUESTED'),
        min_free_disk_bytes=20*1024**3,
        jobs=[
            dict(name='direct_original',family='direct',controller=None,reward='office_task',reward_variant='original',hp='exploratory'),
            dict(name='impedance_original',family='impedance',controller='impedance',reward='metric',reward_variant='original',hp='exploratory'),
            dict(name='admittance_original',family='admittance',controller='admittance',reward='metric',reward_variant='original',hp='exploratory'),
            dict(name='vmc_original',family='vmc',controller='vmc',reward='metric',reward_variant='original',hp='exploratory'),
        ])
    write(root/'PROTOCOL.json',protocol)
    write(root/'REGISTRATION.json',dict(schema='sii-full-rl-retrain-v1',registered_utc=start.isoformat(),
        authorization=protocol['authorization'],root=str(root),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),
        protocol_sha256=sha(root/'PROTOCOL.json'),seed=SEED,steps=STEPS,jobs=protocol['jobs'],
        host='airpig',server_compute=False,resources=protocol['resources'],
        status='registered',training_only_live_mujoco=True))
    write(root/'execution.json',dict(status='registered',created_utc=start.isoformat(),jobs=[]))
    print(json.dumps(dict(root=str(root), protocol_sha256=sha(root/'PROTOCOL.json')),indent=2),flush=True)


def env(root):
    return {**os.environ,
        'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1',
        'JAX_PLATFORMS':'cpu','XLA_PYTHON_CLIENT_PREALLOCATE':'false','XLA_PYTHON_CLIENT_MEM_FRACTION':'.20',
        'SII_LOCAL_RUNTIME':str(RUNTIME),'MUJOCO_MENAGERIE_PATH':str(RUNTIME/'menagerie'),
        'SII_MEMORY_MAX_BYTES':str(3*1024**3),'SII_MEMORY_LIMIT_MODE':'rss_monitor',
        'SII_SOURCE_BASE_COMMIT':read(root/'PROTOCOL.json')['source_base_commit']}


def run_job(root: Path, job: dict, cpu: str):
    out = root/job['name']
    if out.exists():
        raise FileExistsError(out)
    command=[str(PY),str(BENCH/'tools/train_baseline_repair_rl_20261008.py'),
             '--root',str(root),'--output',str(out),'--parameter-source',str(root/'parameter_fullrange'),
             '--seed',str(SEED),'--steps',str(STEPS),'--reward',job['reward'],
             '--reward-variant','original','--hyperparameter-id','exploratory']
    if job['controller']: command += ['--controller',job['controller']]
    log=root/(job['name']+'.log')
    record=dict(status='running',job=job,started_utc=datetime.now(timezone.utc).isoformat(),
                command=command,host='airpig',cpu=cpu,memory_limit_bytes=3*1024**3)
    write(root/(job['name']+'.execution.json'),record)
    wrapped=['taskset','-c',cpu]+command
    with log.open('w') as stream:
        p=subprocess.run(wrapped,cwd=BENCH,env=env(root),stdout=stream,stderr=subprocess.STDOUT)
    record.update(status='complete' if p.returncode==0 else 'failed_preserved',returncode=p.returncode,
                  ended_utc=datetime.now(timezone.utc).isoformat(),output=str(out))
    write(root/(job['name']+'.execution.json'),record)
    return p.returncode


def last_checkpoint(out: Path):
    cps=sorted(out.glob('checkpoint_*'))
    if not cps: raise FileNotFoundError('no checkpoint: '+str(out))
    state=read(out/'execution.json')
    assert state['status']=='complete'
    cp=cps[-1]; runner=read(cp/'office_runner.json')
    assert runner['episode_boundary'] and runner['step']==state['steps']
    return cp


def make_lock(root, checkpoints):
    lock=dict(schema='sii-full-rl-retrain-lock-v1',status='frozen',created_utc=datetime.now(timezone.utc).isoformat(),
              protocol_sha256=sha(root/'PROTOCOL.json'),models=checkpoints,
              test_condition='repair_acceptance_000',task_and_strict_required=True)
    write(root/'FINAL_MODEL_LOCK.json',lock)
    return lock


def evaluate(root, job, cp):
    manifest=root/(job['name']+'.checkpoint.json')
    write(manifest,dict(checkpoint=str(cp.resolve()),hashes=_checkpoint_hashes(cp),controller=job['controller'],
        training_protocol=str((cp.parent/'PROTOCOL.json').resolve()),training_protocol_sha256=sha(cp.parent/'PROTOCOL.json')))
    out=root/(job['name']+'_acceptance')
    command=[str(PY),str(BENCH/'tools/baseline_repair_worker_20261008.py'),
             '--research-protocol',str(root/'PROTOCOL.json'),'--protocol-sha256',sha(root/'PROTOCOL.json'),
             '--research-condition','repair_acceptance_000','--phase','acceptance','--worker-kind','adapted_rl',
             '--v6-input',str(BENCH/'outputs/rl_online_convergence_20261014_v7'), '--physics-dt','.00005',
             '--agent-checkpoint',str(cp.resolve()),'--checkpoint-manifest',str(manifest),
             '--parameter-source',str(root/'parameter_fullrange'),'--output',str(out)]
    if job['controller']: command += ['--controller',job['controller']]
    log=root/(job['name']+'_acceptance.log')
    with log.open('w') as stream:
        p=subprocess.run(['taskset','-c','1']+command,cwd=BENCH,env=env(root),stdout=stream,stderr=subprocess.STDOUT)
    result=dict(status='complete' if p.returncode==0 else 'failed_preserved',returncode=p.returncode,output=str(out),log=str(log))
    if p.returncode==0 and (out/'rollout.json').exists():
        result['rollout']=read(out/'rollout.json').get('result',read(out/'rollout.json'))
    write(root/(job['name']+'_acceptance.json'),result)
    return result


def _checkpoint_hashes(cp):
    from research72_checkpoint_20261003 import checkpoint_hashes
    return checkpoint_hashes(cp)


def run(root: Path):
    protocol=read(root/'PROTOCOL.json'); jobs=protocol['jobs']
    state=read(root/'execution.json'); state.update(status='training',started_utc=datetime.now(timezone.utc).isoformat())
    write(root/'execution.json',state)
    # Two independent lanes, then two more, to keep the registered 6 GiB cap.
    for pair,cpus in ((jobs[:2],('1','6')),(jobs[2:],('1','6'))):
        procs=[]
        for job,cpu in zip(pair,cpus):
            # use a child process so a completed pair can be monitored and
            # failures remain isolated without overwriting another output.
            procs.append(subprocess.Popen([str(PY),str(Path(__file__)),'_job','--root',str(root),
                                           '--job',job['name'],'--cpu',cpu],cwd=BENCH,env=env(root)))
        while any(p.poll() is None for p in procs):
            for p in procs:
                if p.poll() is None:
                    try:
                        rss=int(next(x.split()[1] for x in Path(f'/proc/{p.pid}/status').read_text().splitlines() if x.startswith('VmRSS:')))*1024
                        if rss>3*1024**3:
                            p.send_signal(__import__('signal').SIGUSR1)
                    except (FileNotFoundError,StopIteration): pass
            time.sleep(5)
        codes=[p.returncode for p in procs]
        state=read(root/'execution.json');state.setdefault('pairs',[]).append(dict(jobs=[j['name'] for j in pair],returncodes=codes,ended_utc=datetime.now(timezone.utc).isoformat()));write(root/'execution.json',state)
        if any(c!=0 for c in codes):
            state.update(status='training_failed_preserved',ended_utc=datetime.now(timezone.utc).isoformat());write(root/'execution.json',state);return
    cps={j['name']:str(last_checkpoint(root/j['name']).resolve()) for j in jobs}
    make_lock(root,cps)
    state=read(root/'execution.json');state.update(status='training_complete_testing',checkpoints=cps);write(root/'execution.json',state)
    results=[]
    for job in jobs:
        results.append(dict(job=job['name'],**evaluate(root,job,Path(cps[job['name']]))))
        write(root/'evaluation_summary.json',dict(results=results,updated_utc=datetime.now(timezone.utc).isoformat()))
    state=read(root/'execution.json');state.update(status='complete_review_required',evaluations=results,ended_utc=datetime.now(timezone.utc).isoformat());write(root/'execution.json',state)


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
    q=sub.add_parser('prepare');q.add_argument('--root',type=Path,required=True);q.add_argument('--parent',type=Path,required=True)
    q=sub.add_parser('run');q.add_argument('--root',type=Path,required=True)
    q=sub.add_parser('_job');q.add_argument('--root',type=Path,required=True);q.add_argument('--job',required=True);q.add_argument('--cpu',required=True)
    a=p.parse_args()
    if a.mode=='prepare': prepare(a.root,a.parent)
    elif a.mode=='run': run(a.root)
    else:
        protocol=read(a.root/'PROTOCOL.json');job=next(j for j in protocol['jobs'] if j['name']==a.job)
        raise SystemExit(run_job(a.root,job,a.cpu))

if __name__=='__main__': main()
