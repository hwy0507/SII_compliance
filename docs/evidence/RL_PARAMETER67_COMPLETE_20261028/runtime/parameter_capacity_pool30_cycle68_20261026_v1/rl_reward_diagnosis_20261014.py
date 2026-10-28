"""Bounded local paired reward diagnosis; dynamic parameter RL is never static.

Uses frozen repaired physics and policies' canonical48 interface. Two reward
arms start from scratch with paired seeds; all failures and raw traces retained.
No scheduler/heartbeat, no server computation, no held-out condition reads.
"""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

TOOLS = Path(__file__).resolve().parent
BENCH = TOOLS.parent
PYTHON = Path('/home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python')
START = datetime(2026, 10, 14, 1, 27, 15, tzinfo=timezone.utc)
END = START + timedelta(hours=12)
GIB = 1024**3


def now():
    return datetime.now(timezone.utc)


def read(path):
    return json.loads(Path(path).read_text())


def write(path, obj):
    path = Path(path)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    temp.replace(path)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def tree_hashes(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}


def memory_available():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1])*1024
    raise RuntimeError('MemAvailable missing')


def prepare(root):
    assert platform.node() == 'airpig' and now() < END
    old = BENCH/'outputs/baseline_local_rl_20261009/campaign_v2'
    source = BENCH/'outputs/baseline_local_rl_20261009/recovery_20261011_v1/source'
    root.mkdir(parents=True, exist_ok=False)
    shutil.copytree(source, root/'source', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('rl_reward_diagnosis_20261014.py', 'train_baseline_repair_rl_20261008.py',
                 'baseline_repair_online_worker_20261008.py',
                 'payload_reward_potential_20261014.py',
                 'audit_decoupled_task_safety_reward_20261009.py',
                 'decoupled_task_safety_reward_20261009.py',
                 'audit_local_rl_development_20261009.py',
                 'audit_repair_parameter_trace_20261008.py'):
        shutil.copy2(TOOLS/name, root/'source/tools'/name)
    assert 'external_penetration_peak_m' in (root/'source/tools/baseline_repair_online_worker_20261008.py').read_text()
    shutil.copytree(old/'parameter_fullrange', root/'parameter_fullrange',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('CONDITIONS.json', 'teacher.json'):
        shutil.copy2(old/name, root/name)
    p = read(old/'PROTOCOL.json')
    p.update(registered_utc=now().isoformat(), authorization='2026-10-14 user grants 12 hours to distinguish reward versus exploration/action-interface limitations, local compute only',
        authorization_start_utc=START.isoformat(), authorization_end_utc=END.isoformat(),
        training_dispatch_deadline_utc=(END-timedelta(minutes=75)).isoformat(),
        evaluation_dispatch_deadline_utc=(END-timedelta(minutes=30)).isoformat(),
        deadline_basis='User 12 hours from first verified clock; reserve final time for audit and archive; finish started episode at deadline',
        source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=BENCH,text=True).strip(),
        source_scope='Frozen recovery physics plus documented trainer reward-arm permission and campaign/audit tools',
        parent_protocol_sha256=sha(old/'PROTOCOL.json'), reward_variants=['original','task_safety','payload_shaping'],
        min_free_disk_bytes=40*GIB, cooperative_stop_file=str(root/'STOP_REQUESTED'),
        hypothesis='Changing task/safety learning signal may help; a negative result does not prove RL universally unsuitable',
        parameter_semantics='Agent emits a new parameter action each 40ms actor tick; native shield/rate/tank constraints unchanged',
        evaluation_conditions=[f'repair_development_{i:03d}' for i in range(4)],
        final_conditions_read=False, selection='All planned arms retained; latest completed episode-boundary checkpoint, no best-of-test selection')
    p['budgets'].update(training_seeds=[2026101411,2026101412],
        rl_steps_per_family_seed=500000, planned_max_new_interactions=176000,
        optimizer_schedule_steps=500000, diagnostic_segment_steps=11000)
    p['resources'] = dict(host='airpig', server_compute=False, simulators=2,
        numerical_threads=1, per_lane_memory_max_bytes=3*GIB, swap_max_bytes=0,
        admission='MemAvailable >= new 3GiB hard cap + remaining reservation of running lanes + .75 GiB; serialize paired arms if needed; never close desktop apps',
        gpu='existing local RTX5080, no preallocation, <=.20 fraction per lane')
    pairs=[]
    for family, controller, reward, seed, limit in [
        ('direct',None,'office_task',2026101411,22000),
        ('impedance','impedance','metric',2026101411,22000),
        ('admittance','admittance','metric',2026101411,11000),
        ('vmc','vmc','metric',2026101411,11000),
        ('direct',None,'office_task',2026101412,11000),
        ('impedance','impedance','metric',2026101412,11000)]:
        pairs.append(dict(id=f'{family}_s{seed}',family=family,controller=controller,
                          reward=reward,seed=seed,limit=limit,
                          arms=['original','task_safety' if controller is None else 'payload_shaping']))
    p['pairs']=pairs
    p['jobs']=[dict(pair,name=pair['id']+'_'+arm,hp='exploratory',arm=arm)
               for pair in pairs for arm in pair['arms']]
    p['reward_design_basis']='Historical train-only census: 3 parameter families each120/120 task failures but0/120 penetration violations, so parameter pair tests payload-aligned shaping ONLY; direct pair tests terminal/safety decoupling. Registered before this run training.'
    write(root/'PROTOCOL.json',p)
    write(root/'SOURCE_HASHES.json',tree_hashes(root/'source'))
    write(root/'PARAMETER_HASHES.json',tree_hashes(root/'parameter_fullrange'))
    write(root/'execution.json',dict(status='registered',started_utc=now().isoformat(),pairs=[]))
    print(json.dumps(dict(root=str(root),protocol_sha256=sha(root/'PROTOCOL.json'),deadline=END.isoformat())))


def command(root, label, argv):
    receipt=root/(label+'.execution.json')
    if receipt.exists():
        old=read(receipt)
        assert old['status']=='complete' and old['command']==argv, 'Preserve failed/unfinished attempt'
        for file,digest in old.get('artifacts',{}).items():
            assert sha(file)==digest
        return
    assert shutil.disk_usage(root).free > 40*GIB
    rec=dict(status='running',started_utc=now().isoformat(),command=argv)
    write(receipt,rec)
    with (root/(label+'.log')).open('x') as f:
        proc=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT)
    rec.update(status='complete' if proc.returncode==0 else 'failed_preserved',
               returncode=proc.returncode,ended_utc=now().isoformat())
    if (root/label/'execution.json').exists():
        rec['artifacts']={str(root/label/'execution.json'):sha(root/label/'execution.json')}
    write(receipt,rec)
    if proc.returncode:
        raise RuntimeError(f'{label} failed: {proc.returncode}')


def lane(root, jobid):
    p=read(root/'PROTOCOL.json');job=next(j for j in p['jobs'] if j['name']==jobid)
    source=root/'source/tools'; runtime=Path(p['runtime'])
    label=jobid+'_train'
    argv=[str(PYTHON),str(source/'train_baseline_repair_rl_20261008.py'),
          '--root',str(root),'--output',str(root/label),'--parameter-source',str(root/'parameter_fullrange'),
          '--seed',str(job['seed']),'--steps','500000','--stop-at-step',str(job['limit']),
          '--reward',job['reward'],'--reward-variant',job['arm'],'--hyperparameter-id','exploratory']
    if job['controller']:
        argv+=['--controller',job['controller']]
    command(root,label,argv)
    trained=read(root/label/'execution.json')
    assert trained['status']=='complete' and trained['rows'] and trained['checkpoint_rows']
    checkpoint=trained['checkpoint_rows'][-1]
    manifest=root/(jobid+'.checkpoint.json')
    cpdata=dict(checkpoint=checkpoint['path'],hashes=checkpoint['hashes'],controller=job['controller'],
        training_protocol=str(root/label/'PROTOCOL.json'),training_protocol_sha256=sha(root/label/'PROTOCOL.json'))
    if manifest.exists():
        assert read(manifest)==cpdata
    else:
        write(manifest,cpdata)
    from audit_local_rl_development_20261009 import audit_run
    results=[]
    for condition in p['evaluation_conditions']:
        if now()>=datetime.fromisoformat(p['evaluation_dispatch_deadline_utc']) or (root/'STOP_REQUESTED').exists():
            break
        ev=jobid+'__'+condition
        argv=[str(PYTHON),str(source/'baseline_repair_worker_20261008.py'),
            '--research-protocol',str(root/'PROTOCOL.json'),'--protocol-sha256',sha(root/'PROTOCOL.json'),
            '--research-condition',condition,'--phase','development','--worker-kind','adapted_rl',
            '--v6-input',str(runtime/'v6'),'--reference',str(runtime/'v6/esn_original_v2/rollout.json'),
            '--config',str(root/'teacher.json'),'--output',str(root/ev),'--contact-audit',
            '--physics-dt','.00005','--parameter-source',str(root/'parameter_fullrange'),
            '--agent-checkpoint',checkpoint['path'],'--checkpoint-manifest',str(manifest)]
        if job['controller']:
            argv+=['--controller',job['controller']]
        command(root,ev,argv)
        result=audit_run(root/ev,read(root/(ev+'.execution.json')),p)
        if job['controller']:
            command(root,ev+'_parameter_audit',[str(PYTHON),str(source/'audit_repair_parameter_trace_20261008.py'),
                '--run',str(root/ev),'--parameter-source',str(root/'parameter_fullrange'),
                '--output',str(root/ev/'INDEPENDENT_PARAMETER_AUDIT.json')])
        results.append(dict(condition=condition,**result))
        write(root/(jobid+'.results.json'),dict(job=job,checkpoint=cpdata,training_steps=trained['steps'],
            status='complete' if len(results)==4 else 'partial',evaluations=results))
    write(root/(jobid+'.lane.json'),dict(status='complete' if len(results)==4 else 'deadline_partial',
        ended_utc=now().isoformat(),training_steps=trained['steps'],evaluations=len(results),job=job))


def unit_state(name):
    result=subprocess.run(['systemctl','--user','show',name,'-p','ActiveState','-p','SubState',
            '-p','Result','-p','MemoryCurrent','-p','MemoryPeak','-p','MainPID'],text=True,capture_output=True)
    return dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)


def summary(root):
    p=read(root/'PROTOCOL.json'); rows=[]
    for job in p['jobs']:
        tr=root/(job['name']+'_train/execution.json');ev=root/(job['name']+'.results.json')
        state=read(tr) if tr.exists() else {}
        results=read(ev).get('evaluations',[]) if ev.exists() else []
        rows.append(dict(job=job['name'],steps=state.get('steps',0),updates=state.get('updates',0),
            training_status=state.get('status','not_started'),episodes=state.get('episodes',0),
            train_task=sum(bool(r.get('result',{}).get('task_success')) for r in state.get('rows',[])),
            train_strict=sum(bool(r.get('result',{}).get('strict_success')) for r in state.get('rows',[])),
            evaluations=len(results),task=sum(r['task'] for r in results),strict=sum(r['strict'] for r in results)))
    result=dict(updated_utc=now().isoformat(),deadline_utc=END.isoformat(),methods=rows,
        caution='Finite reward/online-parameter diagnostic; no universal RL unsuitability claim. Compare only paired equal-budget arms.')
    write(root/'LIVE.json',result)
    return result


def run(root):
    assert platform.node()=='airpig' and now()<END
    bench=root.parent.parent
    assert (bench/'tools').is_dir() and root.parent.name=='outputs'
    lock=(bench/'outputs/baseline_local_rl_20261009/.local-rl-compute.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    p=read(root/'PROTOCOL.json')
    assert tree_hashes(root/'source')==read(root/'SOURCE_HASHES.json')
    assert tree_hashes(root/'parameter_fullrange')==read(root/'PARAMETER_HASHES.json')
    assert sha(root/'CONDITIONS.json')==p['condition_file_sha256']
    state=dict(status='running',started_utc=now().isoformat(),pairs=[])
    write(root/'execution.json',state)
    try:
        for index,pair in enumerate(p['pairs']):
            if now()>=datetime.fromisoformat(p['training_dispatch_deadline_utc']) or (root/'STOP_REQUESTED').exists():
                break
            units=[]
            record=dict(pair=pair,started_utc=now().isoformat(),units=units)
            state['pairs'].append(record);write(root/'execution.json',state)
            for arm,cpu in zip(pair['arms'],['1','6']):
                while True:
                    reserve=0
                    for u in units:
                        s=unit_state(u)
                        if s.get('ActiveState') in ('active','activating','deactivating'):
                            current=s.get('MemoryCurrent','0')
                            reserve+=max(0,3*GIB-(int(current) if current.isdigit() else 0))
                    needed=int(3.75*GIB)+reserve
                    if memory_available()>=needed:
                        break
                    summary(root)
                    write(root/'RESOURCE_WAIT.json',dict(at=now().isoformat(),available=memory_available(),needed=needed))
                    if now()>=datetime.fromisoformat(p['training_dispatch_deadline_utc']) or (root/'STOP_REQUESTED').exists():
                        raise RuntimeError('Resource/deadline: unpaired arm remains explicitly incomplete')
                    time.sleep(20)
                jobid=pair['id']+'_'+arm
                unit=f'sii-rl-diagnosis-1014-{root.name.rsplit("_",1)[-1]}-p{index}-{arm.replace("_","-")}'
                assert unit_state(unit).get('ActiveState','inactive') not in ('active','activating'), 'Never duplicate a live lane'
                args=['systemd-run','--user','--unit='+unit,'-p','MemoryMax=3G','-p','MemorySwapMax=0',
                      '-p','CPUQuota=100%','-p','CPUAffinity='+cpu,
                      '--working-directory='+str(bench)]
                env=dict(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
                    NUMEXPR_NUM_THREADS='1',JAX_PLATFORMS='cuda',XLA_PYTHON_CLIENT_PREALLOCATE='false',
                    XLA_PYTHON_CLIENT_MEM_FRACTION='.20',SII_LOCAL_RUNTIME=p['runtime'],
                    SII_REWARD_PAYLOAD_TELEMETRY='1',
                    MUJOCO_MENAGERIE_PATH=str(Path(p['runtime'])/'menagerie'),PYTHONDONTWRITEBYTECODE='1')
                args+=['--setenv='+k+'='+v for k,v in env.items()]
                args+=[str(PYTHON),str(root/'source/tools/rl_reward_diagnosis_20261014.py'),
                       'lane','--root',str(root),'--job',jobid]
                subprocess.run(args,check=True)
                units.append(unit);write(root/'execution.json',state)
            while True:
                statuses={u:unit_state(u) for u in units}
                record['unit_statuses']=statuses;record['checked_utc']=now().isoformat()
                write(root/'execution.json',state);summary(root)
                active=[s for s in statuses.values() if s.get('ActiveState') in ('active','activating','deactivating')]
                if not active:
                    break
                time.sleep(20)
            if any(s.get('Result')!='success' for s in statuses.values()):
                raise RuntimeError('Lane infrastructure/audit failure; preserve pair and stop new dispatch')
            record['ended_utc']=now().isoformat();write(root/'execution.json',state)
        state['status']='complete_review_required'
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc))
        write(root/'STOP_REQUESTED',dict(reason='Coordinator failure; finish current episodes, no new dispatch',error=repr(exc)))
        # Preserve the global lock until any already-started lane closes its
        # episode/checkpoint. Do not signal the simulator process group.
        all_units=[u for record in state['pairs'] for u in record['units']]
        while any(unit_state(u).get('ActiveState') in ('active','activating','deactivating') for u in all_units):
            summary(root);time.sleep(20)
        raise
    finally:
        state['ended_utc']=now().isoformat();write(root/'execution.json',state);summary(root)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['prepare','run','lane','summary'])
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--job')
    a=parser.parse_args();root=a.root.resolve()
    if a.phase=='prepare':prepare(root)
    elif a.phase=='run':run(root)
    elif a.phase=='lane':lane(root,a.job)
    else:print(json.dumps(summary(root),ensure_ascii=False,indent=2))
