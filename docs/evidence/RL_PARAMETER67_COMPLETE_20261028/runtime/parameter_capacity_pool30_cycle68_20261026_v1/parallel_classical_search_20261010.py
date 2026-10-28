"""Resume the SAME registered 90 trials on two bounded local CPU lanes.

Only the coordinator changes. Wait for the original safe episode boundary;
retain its receipt and frozen worker/source/config/seed/model/selection rules.
Never retry a partial job, enlarge the budget or start server computation.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import fcntl
import hashlib
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

from classical_acceptance_20261010 import read, write, sha, hashes, now, confirmation_jobs
from monitor_classical_search_20261010 import Monitor, require

GIB = 1024**3


def available_memory():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1])*1024
    raise RuntimeError('MemAvailable missing')


def may_dispatch(available, active_count):
    # First admission budgets 6 GiB total plus 1 GiB reserve. With one lane
    # active, conservatively require 4 GiB available before admitting another.
    return active_count < 2 and available >= (7 if active_count == 0 else 4)*GIB


def pending_jobs(jobs, completed, active_names):
    names = [r['job']['name'] for r in completed]
    require(len(names)==len(set(names)), 'Duplicate completed job')
    return [j for j in jobs if j['name'] not in set(names) | set(active_names)]


def run_one(root, runtime, reg, job, lane):
    out = root/job['name']
    receipt = root/(job['name']+'.execution.json')
    require(not receipt.exists() and not out.exists(), 'Preserve existing attempt: '+job['name'])
    source = root/'source'
    config = root/(job['name']+'.config.json')
    require(not config.exists(), 'Preserve existing config: '+job['name'])
    write(config,dict(parameters=job['parameters']))
    command = [sys.executable,str(source/'tools/classical_acceptance_20261010.py'),'worker',
        '--root',str(root),'--runtime',str(runtime),'--fixture',job['fixture'],
        '--controller',job['controller'],'--condition',job['condition_id'],
        '--registration-sha256',sha(root/'REGISTRATION.json'),
        '--v6-input',str(runtime/'v6'),'--reference',str(runtime/'v6/esn_original_v2/rollout.json'),
        '--config',str(config),'--output',str(out),'--physics-dt','.00005','--contact-audit']
    env = dict(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
        MUJOCO_GL='egl',JAX_PLATFORMS='cpu',SII_LOCAL_RUNTIME=str(runtime),
        MUJOCO_MENAGERIE_PATH=str(runtime/'menagerie'),SII_SOURCE_BASE_COMMIT=reg['source_base_commit'])
    unit = 'sii-classical-accept-'+hashlib.sha256(str(out).encode()).hexdigest()[:12]
    launch = ['systemd-run','--user','--wait','--pipe','--collect','--unit='+unit,
        '--property=MemoryMax=3G','--property=MemorySwapMax=0','--property=TasksMax=128',
        '--property=CPUAffinity='+str((1,6)[lane]),'--working-directory='+str(source)]
    launch += ['--setenv='+k+'='+v for k,v in env.items()]
    row = dict(job=job,status='running',started_utc=now(),command=command,unit=unit,lane=lane,
        dispatch_amendment_sha256=sha(root/'DISPATCH_V2.json'))
    write(receipt,row)
    try:
        with (root/(job['name']+'.log')).open('x') as log:
            rc = subprocess.run(launch+command,stdout=log,stderr=subprocess.STDOUT).returncode
        row.update(returncode=rc,ended_utc=now())
        require(rc==0,'Worker exited unsuccessfully')
        audit = read(out/'AUDIT.json')
        require(read(out/'execution.json')['status']=='complete','Worker receipt incomplete')
        require(0<audit['physical_seconds']<=55.000001,'Invalid physical duration')
        require(not audit['task_success'] or audit['full_horizon'],'Short success invalid')
        checks = []
        scripts = [('shield','audit_repair_parameter_trace_20261008.py')]
        if job['controller'] in ('vmc','admittance'):
            scripts.append(('dynamic','replay_repair_dynamic_controllers_20261009.py'))
        for label,script in scripts:
            target = root/(job['name']+'.'+label+'.json')
            cmd = [sys.executable,str(source/'tools'/script),'--run',str(out),
                '--parameter-source',str(root/'parameter'),'--output',str(target)]
            audit_launch = [x if x!='--unit='+unit else '--unit='+unit+'-'+label for x in launch]
            with (root/(job['name']+'.'+label+'.log')).open('x') as log:
                rc = subprocess.run(audit_launch+cmd,stdout=log,stderr=subprocess.STDOUT).returncode
            checks.append(dict(kind=label,command=cmd,returncode=rc))
            row['checks']=checks
            require(rc==0 and read(target)['status']=='passed','Independent audit failed')
            checks[-1]['sha256']=sha(target)
        row.update(status='complete',audit=audit,audit_sha256=sha(out/'AUDIT.json'),
            trace_sha256=sha(out/'rollout.npz'),checks=checks)
    except BaseException as exc:
        row.update(status='failed_preserved',error=repr(exc),ended_utc=now())
        write(receipt,row)
        raise
    write(receipt,row)
    return row


def run(root,runtime):
    require(platform.node()=='airpig','Local host only')
    old = read(root/'execution.json')
    require(old['status']=='stopped_at_safe_boundary','Original coordinator must stop safely first')
    Monitor(root).snapshot(rehash=True)
    reg = read(root/'REGISTRATION.json')
    require(available_memory()>=7*GIB,'Need at least 7 GiB available for two lanes')
    require(not (root/'DISPATCH_V2.json').exists(),'Resource amendment already exists; inspect, do not restart')
    archive = root/'serial_handoff_v1'
    archive.mkdir(exist_ok=False)
    for name in ('execution.json','CHAIN_EXECUTION.json','STOP_REQUESTED'):
        shutil.copy2(root/name,archive/name)
    amendment = dict(created_utc=now(),authorization='2026-10-10 user requests better local utilization after authorizing local baseline work',
        registration_sha256=sha(root/'REGISTRATION.json'),prior_execution_sha256=sha(archive/'execution.json'),
        simulators=2,threads_per_worker=1,worker_memory_max_bytes=3*GIB,worker_swap_max_bytes=0,
        worker_cpu_affinities=[1,6],available_memory_before_start=available_memory(),
        total_worker_cap_bytes=6*GIB,admission='7GiB available with no active lane; 4GiB with one; no third lane',
        unchanged=['worker source','parameter source','model','gate','inputs','parameters','seed','90 episode budget','screen and confirmation rules'],
        source_hashes=hashes(Path(__file__).parent),server_compute=False)
    write(root/'DISPATCH_V2.json',amendment)
    # Preserve the old stop marker; it is consumed only for this explicit handoff.
    (root/'STOP_REQUESTED').rename(archive/'STOP_REQUESTED.consumed')
    state = dict(status='running',started_utc=old['started_utc'],resumed_utc=now(),host='airpig',
        registration_sha256=sha(root/'REGISTRATION.json'),dispatch_amendment_sha256=sha(root/'DISPATCH_V2.json'),
        completed=old['completed'],active=None,active_jobs=[],parallel_lanes=2)
    jobs=list(reg['jobs']);futures={};errors=[]
    def save():
        order={j['name']:i for i,j in enumerate(jobs)}
        state['completed'].sort(key=lambda r:order[r['job']['name']])
        state['active_jobs']=[v[0] for v in futures.values()]
        write(root/'execution.json',state)
    save()
    with ThreadPoolExecutor(max_workers=2) as pool:
        while True:
            if not futures and len(state['completed'])==len(reg['jobs']) and len(jobs)==len(reg['jobs']):
                jobs.extend(confirmation_jobs(root,reg,state['completed']))
                require(len(jobs)==reg['max_episodes'],'Confirmation budget changed')
                save()
            stop = (root/'STOP_REQUESTED').exists()
            active_names=[v[0]['name'] for v in futures.values()]
            pending=pending_jobs(jobs,state['completed'],active_names)
            while pending and not errors and not stop and may_dispatch(available_memory(),len(futures)):
                if shutil.disk_usage(root).free<30*GIB:
                    errors.append('Preserve 30 GiB free disk');break
                used={v[1] for v in futures.values()};lane=next(i for i in (0,1) if i not in used)
                job=pending.pop(0)
                f=pool.submit(run_one,root,runtime,reg,job,lane)
                futures[f]=(job,lane)
                save()
            if not futures:
                if errors or stop or not pending:
                    state.update(status='failed_preserved' if errors else ('stopped_at_safe_boundary' if stop else 'complete'),
                        errors=errors,ended_utc=now())
                    save();break
                state['waiting_reason']='memory admission guard';save();time.sleep(30);continue
            ready,_=wait(futures,timeout=10,return_when=FIRST_COMPLETED)
            for f in ready:
                job,lane=futures.pop(f)
                try:state['completed'].append(f.result())
                except BaseException as exc:errors.append(job['name']+': '+repr(exc))
            # After any infrastructure/audit error, drain the other already
            # running lane before stopping. Physical failures are normal rows.
            save()
    print(state['status'],len(state['completed']),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--runtime',type=Path,required=True)
    a=p.parse_args();a.root=a.root.resolve();a.runtime=a.runtime.resolve()
    with (a.runtime.parent/'.local-rl-compute.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run(a.root,a.runtime)


if __name__=='__main__':main()
