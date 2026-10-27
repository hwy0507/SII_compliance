"""Finite read-only follow-through for the registered72-episode campaign.

Waits for each six-controller condition, audits and archives it, then audits the
final180 report. Never dispatches simulation, changes a controller, or writes Git.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime,timezone

HOST='arm1@192.168.31.70'
REMOTE='/home/arm1/sii_shared/SII_compliance/runs/main'
SOURCE_NAMES=('watch_nonrl_classical_archives_20261027.py','audit_nonrl_classical_extension_20261027.py',
              'archive_nonrl_classical_condition_20261027.py','archive_nonrl_new30_physics_20261026.py')


def read(p):return json.loads(p.read_text())
def now():return datetime.now(timezone.utc).isoformat()


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def write(p,value):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n');os.replace(tmp,p)


def require(ok,message):
    if not ok:raise RuntimeError(message)


def prepare(root):
    dest=root/'published/archive_pipeline_v1';require(not dest.exists(),'Archive pipeline already registered')
    reg=read(root/'REGISTRATION.json');require(reg['schema']=='sii-nonrl-task-conditional-classical-v1','Wrong experiment')
    require(len(read(root/'MODEL_LOCK.json')['models'])==6,'Expected6 classical configurations')
    require(len(read(root/'CONDITIONS.json')['conditions'])==12,'Expected12 conditions')
    dest.mkdir(parents=True);(dest/'source').mkdir();(dest/'logs').mkdir();(dest/'audits').mkdir()
    for name in SOURCE_NAMES:shutil.copy2(Path(__file__).with_name(name),dest/'source'/name)
    first=Path(reg['benchmark']).parents[1]/'docs/evidence/nonrl_classical_task_spt_20261027/CONDITION000_PHYSICS_AUDIT.json'
    require(first.exists(),'First condition audit required for adoption of existing archive')
    shutil.copy2(first,dest/'audits/condition000.json')
    registration=dict(created_utc=now(),campaign=str(root),campaign_registration_sha256=sha(root/'REGISTRATION.json'),
        python=sys.executable,host=HOST,remote_root=REMOTE,
        source_hashes={n:sha(dest/'source'/n) for n in SOURCE_NAMES},
        work='Only complete condition audits, immutable packages, SSH archive verification; final180 read-only audit. No simulation or Git writes.',
        resources=dict(cpu=2,threads=1,memory_max=3*1024**3,swap_max=0),
        exit='All12 classical condition packages verified plus final180 audit; or any infrastructure/physical campaign failure. No automatic simulator recovery.')
    write(dest/'REGISTRATION.json',registration)
    write(dest/'execution.json',dict(status='prepared',registration_sha256=sha(dest/'REGISTRATION.json'),archives=[]))
    print(json.dumps(dict(pipeline=str(dest),status='prepared')))


def run(root):
    dest=root/'published/archive_pipeline_v1';reg=read(dest/'REGISTRATION.json');state=read(dest/'execution.json')
    require(state['status']=='prepared','No duplicate or silent resume')
    require(sha(dest/'REGISTRATION.json')==state['registration_sha256'],'Pipeline registration changed')
    require(sys.executable==reg['python'],'Wrong interpreter')
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    require(int((cg/'memory.max').read_text())<=3*1024**3 and int((cg/'memory.swap.max').read_text())==0,'3GiB/no-swap cgroup required')
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    conditions=read(root/'CONDITIONS.json')['conditions'];models=read(root/'MODEL_LOCK.json')['models']
    with (root/'.archive-pipeline.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state.update(status='running',pid=os.getpid(),started_utc=now());write(dest/'execution.json',state)
        def command(argv,label):
            log=dest/'logs'/f'{label}.log'
            with log.open('x') as f:
                result=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,env=env,pass_fds=(lock.fileno(),))
            require(result.returncode==0,f'Failed rc={result.returncode}: {log}')
            return log.read_text().strip()
        def ssh(code,label):
            return command(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',reg['host'],code],label)
        def verify(remote,receipt,label):
            result=ssh('sha256sum '+shlex.quote(remote)+' && stat -c %s '+shlex.quote(remote),label)
            lines=result.splitlines()
            require(len(lines)==2 and lines[0].split()[0]==receipt['sha256'] and int(lines[1])==receipt['bytes'],'Remote hash/size mismatch')
        def frozen():
            require(sha(root/'REGISTRATION.json')==reg['campaign_registration_sha256'],'Campaign registration changed')
            for n,h in reg['source_hashes'].items():require(sha(dest/'source'/n)==h,'Archive source changed')
        try:
            for index,condition in enumerate(conditions):
                names={m['name']+'__'+condition['id'] for m in models}
                while True:
                    frozen();campaign=read(root/'execution.json')
                    complete={e['name'] for e in campaign['evaluation'] if e['status']=='complete'}
                    if names<=complete:break
                    require(campaign['status'] in ('prepared','running'),'Campaign terminal before condition complete: '+campaign['status'])
                    # The watcher does not infer death from a stale progress file.
                    # It only waits; the monitoring agent checks actual process liveness.
                    state.update(status='waiting_for_condition',condition=condition['id'],updated_utc=now(),campaign_completed=len(complete))
                    write(dest/'execution.json',state);time.sleep(30)
                if (dest/'STOP_REQUESTED').exists():
                    state.update(status='stopped_at_condition_boundary',ended_utc=now());write(dest/'execution.json',state);return
                frozen();state.update(status='auditing_or_archiving',condition=condition['id'],updated_utc=now());write(dest/'execution.json',state)
                audit=dest/'audits'/f'condition{index:03}.json'
                if not audit.exists():
                    command([sys.executable,str(dest/'source/audit_nonrl_classical_extension_20261027.py'),
                             '--root',str(root),'--progress','--condition',condition['id'],'--output',str(audit)],f'{index:03}_audit')
                require(read(audit)['status']=='completed_classical_condition_audit_passed_not_final','Condition audit not passed')
                package=root/'published'/f'condition{index:03}_physics';receipt_path=package/'LOCAL_PACKAGE_RECEIPT.json'
                if not package.exists():
                    command([sys.executable,str(dest/'source/archive_nonrl_classical_condition_20261027.py'),
                             '--root',str(root),'--audit',str(audit),'--output',str(package)],f'{index:03}_package')
                require(receipt_path.exists(),'Incomplete existing package; preserve and stop')
                receipt=read(receipt_path);local=package/'PHYSICS_BUNDLE.tar.gz'
                require(receipt['condition']==condition['id'] and receipt['episodes']==6,'Wrong package identities')
                require(sha(local)==receipt['sha256'] and local.stat().st_size==receipt['bytes'],'Local package drift')
                remote_dir=reg['remote_root']+'/'+root.name+f'_physics{index:03}'
                remote=remote_dir+'/PHYSICS_BUNDLE.tar.gz'
                exists=ssh('if test -f '+shlex.quote(remote)+'; then echo present; else echo absent; fi',f'{index:03}_exists')
                require(exists in ('present','absent'),'Unexpected remote response')
                if exists=='absent':
                    # Independent directory: an incomplete transfer from another
                    # attempt is preserved and requires explicit recovery.
                    ssh('test ! -e '+shlex.quote(remote_dir)+' && mkdir '+shlex.quote(remote_dir),f'{index:03}_mkdir')
                    command(['scp','-q',str(local),reg['host']+':'+remote+'.partial'],f'{index:03}_transfer')
                    verify(remote+'.partial',receipt,f'{index:03}_verify_partial')
                    ssh('test ! -e '+shlex.quote(remote)+' && mv '+shlex.quote(remote+'.partial')+' '+shlex.quote(remote),f'{index:03}_publish')
                verify(remote,receipt,f'{index:03}_verify_final')
                record=dict(status='verified',condition=condition['id'],episodes=6,host=reg['host'],archive=remote,
                            sha256=receipt['sha256'],bytes=receipt['bytes'],verified_utc=now(),
                            local_package_receipt_sha256=sha(receipt_path),condition_audit_sha256=sha(audit))
                write(dest/f'ARCHIVE_{index:03}.json',record);state['archives'].append(record)
                state.update(status='condition_archived',updated_utc=now());write(dest/'execution.json',state)
            while read(root/'execution.json')['status']=='running':time.sleep(5)
            require(read(root/'execution.json')['status']=='complete','Campaign did not complete final report')
            frozen()
            command([sys.executable,str(dest/'source/audit_nonrl_classical_extension_20261027.py'),
                     '--root',str(root),'--output',str(dest/'FINAL_AUDIT.json')],'final180_audit')
            require(read(dest/'FINAL_AUDIT.json')['status']=='final180_saved_physics_audit_passed','Final audit failed')
            state.update(status='raw_archives_and_final_audit_complete_pending_publication',ended_utc=now(),
                         final_audit_sha256=sha(dest/'FINAL_AUDIT.json'),report_sha256=sha(root/'REPORT.json'))
            write(dest/'execution.json',state)
        except BaseException as exc:
            state.update(status='failed_preserved',error=repr(exc),ended_utc=now());write(dest/'execution.json',state);raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    mode=p.add_mutually_exclusive_group(required=True);mode.add_argument('--prepare',action='store_true');mode.add_argument('--run',action='store_true')
    a=p.parse_args();(prepare if a.prepare else run)(a.root.resolve())
