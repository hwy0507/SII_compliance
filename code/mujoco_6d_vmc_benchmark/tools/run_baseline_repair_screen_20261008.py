"""Finite parallel controller screening; failed attempts never silently retried."""
import argparse
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time
from office_v7_uniform24_20261008 import read, write, sha, now, V6, MENAGERIE
from run_paper_final_validation_20261003 import ENV


@contextmanager
def physics_slot(root):
    """Eight shared classical leases; two additional slots reserved for RL."""
    directory=root/'classical_physics_slots'; directory.mkdir(exist_ok=True)
    deadline=datetime.fromisoformat(read(root/'PROTOCOL.json')['training_dispatch_deadline_utc'])
    lease=None
    while lease is None:
        if datetime.now(timezone.utc)>=deadline:
            raise RuntimeError('No new physics after training dispatch cutoff')
        for i in range(8):
            f=(directory/f'{i}.lock').open('a')
            try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:f.close();continue
            lease=f;break
        if lease is None:time.sleep(2)
    try:yield
    finally:fcntl.flock(lease,fcntl.LOCK_UN);lease.close()


def managed(source, command, label):
    env = dict(ENV, SII_SOURCE_BASE_COMMIT='d5627f49a94651962bdb3f0c5a75c4b503c325ab',
               MUJOCO_MENAGERIE_PATH=str(MENAGERIE))
    return ['systemd-run','--user','--wait','--pipe','--collect','--unit='+label,
            '--property=MemoryMax=3G','--property=MemorySwapMax=0',
            '--property=CPUAffinity=5-9,15-19','--property=AllowedCPUs=5-9,15-19',
            '--working-directory='+str(source)] + ['--setenv='+k+'='+v for k,v in env.items()] + command


def one(root, candidate, condition, phase, directory, source_name='source_v1'):
    source=root/source_name; name=candidate['name']+'__'+condition['id']
    run=directory/name; receipt=directory/(name+'.execution.json')
    if receipt.exists():
        old=read(receipt)
        assert old['status']=='complete', 'Incomplete attempt preserved: '+name
        assert sha(run/'AUDIT.json')==old['audit_sha256']
        return old
    protocol=read(root/'PROTOCOL.json')
    assert datetime.now(timezone.utc)<datetime.fromisoformat(protocol['training_dispatch_deadline_utc'])
    config=directory/(name+'.config.json'); write(config,dict(parameters=candidate['parameters']))
    command=[sys.executable,str(source/'tools/baseline_repair_worker_20261008.py'),
        '--research-protocol',str(root/'PROTOCOL.json'),'--protocol-sha256',sha(root/'PROTOCOL.json'),
        '--research-condition',condition['id'],'--phase',phase,'--worker-kind','classical',
        '--v6-input',str(V6),'--reference',str(V6/'esn_original_v2/rollout.json'),
        '--config',str(config),'--output',str(run),'--contact-audit','--physics-dt','.00005',
        '--controller',candidate['method'],'--parameter-source',str(root/'parameter_v1')]
    row=dict(status='running',started_utc=now(),candidate=candidate,condition=condition['id'],command=command)
    write(receipt,row)
    with physics_slot(root), (directory/(name+'.log')).open('x') as log:
        rc=subprocess.run(managed(source,command,'sii-r15-'+directory.name+'-'+name.replace('_','-')),stdout=log,stderr=subprocess.STDOUT).returncode
    row.update(returncode=rc,ended_utc=now())
    if rc:
        row['status']='infrastructure_failure_preserved';write(receipt,row)
        raise RuntimeError(name+' failed; see '+str(directory/(name+'.log')))
    audit=read(run/'AUDIT.json')
    assert audit['model_sha256']==protocol['formal_model_sha256']
    row.update(status='complete',audit=audit,audit_sha256=sha(run/'AUDIT.json'),trace_sha256=sha(run/'rollout.npz'))
    write(receipt,row)
    return row


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--mode',choices=('acceptance','screen','confirmation'),required=True)
    p.add_argument('--workers',type=int,default=10)
    p.add_argument('--source-subdir',default='source_v1')
    p.add_argument('--attempt-name')
    p.add_argument('--selection-file',type=Path,help='Explicit documented development reranking; confirmation only')
    a=p.parse_args(); root=a.root.resolve()
    assert 1<=a.workers<=10
    assert '/' not in a.source_subdir and (a.attempt_name is None or '/' not in a.attempt_name)
    directory=root/(a.attempt_name or 'classical_'+a.mode);directory.mkdir(exist_ok=True)
    lock=(directory/'.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    all_candidates=read(root/'CLASSICAL_CANDIDATES.json')['candidates']
    conditions=read(root/'CONDITIONS.json')['conditions']
    phase='acceptance' if a.mode=='acceptance' else 'development'
    conditions=[c for c in conditions if c['role']==phase]
    candidates=all_candidates
    if a.mode=='acceptance':
        candidates=[c for c in candidates if c['name'] in ('vmc_00','admittance_00','impedance_00','impedance_01','impedance_02','impedance_03')]
    elif a.mode=='screen':conditions=conditions[:2]
    else:
        selected=read(a.selection_file or root/'classical_screen/SUMMARY.json')['ranked']
        names={c['name'] for group in selected.values() for c in group[:2]}
        candidates=[c for c in candidates if c['name'] in names]
    jobs=[(c,d) for d in conditions for c in candidates]
    write(directory/'execution.json',dict(status='running',started_utc=now(),expected=len(jobs),workers=a.workers))
    failures=[]
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures=[pool.submit(one,root,c,d,phase,directory,a.source_subdir) for c,d in jobs]
        for f in as_completed(futures):
            try:f.result()
            except Exception as e:failures.append(repr(e))
    rows=[read(f) for f in directory.glob('*.execution.json')]
    ranked={}
    for method in ('vmc','admittance','impedance'):
        values=[]
        for c in [c for c in candidates if c['method']==method]:
            rr=[r['audit'] for r in rows if r['candidate']['name']==c['name'] and r['status']=='complete']
            if len(rr)!=len(conditions):continue
            stages=[max((int(s) for s in r.get('stages',{})),default=0) for r in rr]
            score=[sum(r['strict_success'] for r in rr),sum(r['task_success'] for r in rr),
                   sum(r['full_horizon'] for r in rr),sum(stages),-max(r['penetration_mm'] for r in rr),
                   -sum(r['rmse_mm'] for r in rr),-sum(r['peak_torque_nm'] for r in rr)]
            values.append(dict(c,score=score,episodes=len(rr)))
        ranked[method]=sorted(values,key=lambda x:x['score'],reverse=True)
    write(directory/'SUMMARY.json',dict(status='complete' if not failures else 'failed_preserved',rows=rows,ranked=ranked,failures=failures))
    write(directory/'execution.json',dict(status='complete' if not failures else 'failed_preserved',ended_utc=now(),expected=len(jobs),completed=sum(r['status']=='complete' for r in rows),failures=failures))
    if failures:raise RuntimeError(failures)


if __name__=='__main__':main()
