"""Local finite RL continuation with checkpoint development and independent audit.

prepare writes a new immutable registration; run owns the existing compute lock.
Every lane serializes learning, all eight development identities, and auditing.
No remote computation, recurring scheduler, final-test access or teacher labels.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import threading

from office_v7_uniform24_20261008 import read, write, sha, now
from research72_checkpoint_20261003 import checkpoint_hashes
from local_rl_campaign_20261009 import hashes
from extend_local_rl_training_20261009 import assess


def environment(protocol):
    runtime = Path(protocol['runtime'])
    return dict(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
        MUJOCO_GL='egl', JAX_PLATFORMS='cuda', XLA_PYTHON_CLIENT_PREALLOCATE='false',
        XLA_PYTHON_CLIENT_MEM_FRACTION='0.12', SII_LOCAL_RUNTIME=str(runtime),
        MUJOCO_MENAGERIE_PATH=str(runtime/'menagerie'),
        SII_SOURCE_BASE_COMMIT=protocol['source_base_commit'])


def verify_checkpoint(segment):
    state = read(segment/'execution.json')
    assert state['status'] == 'complete' and all('result' in r for r in state['rows'])
    latest = state['checkpoint_rows'][-1]
    assert latest['step'] == state['steps']
    cp = Path(latest['path'])
    assert checkpoint_hashes(cp) == latest['hashes']
    runner = read(cp/'office_runner.json')
    assert runner['episode_boundary'] and runner['step'] == latest['step']
    return state, latest


def decision(history):
    result = assess(history)
    # Give the renewed continuation three >=110k checkpoints before classifying
    # a zero-success plateau. It remains a failure needing algorithm review.
    later = [r for r in history if r['scheduled_limit'] >= 110000]
    result['stop_failed_plateau'] = len(later) >= 3 and all(r['task'] == 0 for r in later[-3:])
    return result


def prepare(root, out):
    assert platform.node() == 'airpig' and not out.exists()
    protocol = read(root/'PROTOCOL.json')
    assert hashes(root/'source') == read(root/'SOURCE_HASHES.json')
    assert hashes(root/'parameter_fullrange') == read(root/'PARAMETER_HASHES.json')
    assert sha(root/'CONDITIONS.json') == protocol['condition_file_sha256']
    parents = {}
    for job in protocol['jobs']:
        suffix = 'extended110000' if job['name'] in ('direct_office_task', 'parameter_impedance') else 'extended055000'
        segment = root/(job['name']+'_'+suffix)
        state, cp = verify_checkpoint(segment)
        parents[job['name']] = dict(segment=str(segment), steps=state['steps'],
            scheduled_limit=110000 if suffix.endswith('110000') else 55000,
            checkpoint=cp, execution_sha256=sha(segment/'execution.json'))
    out.mkdir(parents=True)
    # Preserve the exact original worker and physics; only replace the learner
    # entry point and add the continuation/audit helpers in this new snapshot.
    shutil.copytree(root/'source', out/'source', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    tools = Path(__file__).resolve().parent
    overlays = ('launch_rl_convergence_20261010.py', 'train_baseline_repair_rl_20261008.py',
        'audit_local_rl_development_20261009.py', 'extend_local_rl_training_20261009.py',
        'multistep_rl_replay_20261009.py', 'decoupled_task_safety_reward_20261009.py')
    for name in overlays:
        shutil.copy2(tools/name, out/'source/tools'/name)
    start = datetime.now(timezone.utc)
    registration = dict(schema='sii-local-rl-convergence-v2', registered_utc=start.isoformat(),
        authorization='2026-10-10 user: continue RL locally to convergence/usable policy, then compare; renewed authority after closed 15h window',
        parent_root=str(root), run_root=str(out), parent_protocol_sha256=sha(root/'PROTOCOL.json'),
        host='airpig', seed=2026100911, jobs=protocol['jobs'], parents=parents,
        source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=tools,text=True).strip(),
        overlays=list(overlays), condition_sha256=sha(root/'CONDITIONS.json'),
        optimizer_schedule_steps=500000, training_limits=[110000,165000,220000,330000,499125],
        dispatch_deadline_utc=(start+timedelta(hours=72)).isoformat(),
        deadline_basis='Agent-chosen finite 72h safety horizon under renewed open-ended user authority, NOT an inherited or user-specified 15h limit; review and renew if unfinished',
        min_free_disk_bytes=40*1024**3,
        cooperative_stop_file=str(out/'STOP_REQUESTED'),
        resources=dict(server_compute=False, simulators=2, numerical_threads=1,
            memory_max_per_lane=3*1024**3, memory_swap_max=0, admission_available_kib=7*1024**2),
        schedule='Evaluate the two saved 110k nodes first, immediately resume both to165k; remaining five resume55k to165k as lanes free; all seven then share165k/220k/330k/499125 development checkpoints',
        convergence='Three development checkpoints spanning >=22k interactions, each Task>=7/8 and Strict>=6/8 with Strict range<=1, are a candidate only; independent training seeds still required',
        failed_plateau='Three >=110k development checkpoints all Task=0 trigger learning-mechanism review, never convergence; no change to environment or gates',
        checkpoint_limit='499125 approximates 500k at whole-episode boundaries, not a success condition',
        final_test_reads=0, teacher_labels_used=False, reward_variant='original',
        unchanged=['formal MJB/dt5e-5','canonical48 actor','Task/Strict','actuator amplitude/slew','common filter',
            'optimizer/replay/RNG exact continuation','reward and original 500k learning schedule'])
    write(out/'REGISTRATION.json', registration)
    write(out/'SOURCE_HASHES.json', hashes(out/'source'))
    print('registered',out,sha(out/'REGISTRATION.json'))


def audit_segment(root, segment, output):
    from audit_local_rl_development_20261009 import audit_run
    assert not output.exists()
    protocol = read(root/'PROTOCOL.json')
    state, cp = verify_checkpoint(segment)
    ids = [c['id'] for c in read(root/'CONDITIONS.json')['conditions'] if c['role']=='development']
    assert len(ids) == len(set(ids)) == 8
    rows = []
    conditions = read(root/'CONDITIONS.json')['conditions']
    manifest = read(Path(str(segment)+'.checkpoint.json'))
    assert manifest['checkpoint']==cp['path'] and manifest['hashes']==cp['hashes']
    assert sha(manifest['training_protocol'])==manifest['training_protocol_sha256']
    for identity in ids:
        run = Path(str(segment)+'__'+identity)
        receipt = read(Path(str(run)+'.execution.json'))
        assert receipt['status']=='complete'
        argv = receipt['command']
        assert argv[argv.index('--research-condition')+1] == identity
        assert argv[argv.index('--agent-checkpoint')+1] == cp['path']
        assert read(run/'ADAPTED_RL_CHECKPOINT.json')==manifest
        role=read(run/'REPAIR_ROLE.json')
        assert role['condition']==next(c for c in conditions if c['id']==identity)
        assert role['protocol_sha256']==sha(root/'PROTOCOL.json') and role['worker_kind']=='adapted_rl'
        row = audit_run(run, receipt, protocol)
        if '--controller' in argv:
            pa = read(run/'INDEPENDENT_PARAMETER_AUDIT.json')
            assert pa['status']=='passed'
        rows.append(dict(row, condition=identity))
    assert checkpoint_hashes(cp['path']) == cp['hashes']
    result = dict(status='passed',created_utc=now(),steps=state['steps'],completed=8,
        task=sum(r['task'] for r in rows),strict=sum(r['strict'] for r in rows),rows=rows,
        checkpoint=cp, protocol_sha256=sha(root/'PROTOCOL.json'),
        new_physics_steps=0,gradient_updates=0,final_test_reads=0)
    write(output,result)
    print('audited',segment.name,result['task'],result['strict'])


def reuse_development(root, out, reg, name):
    """Re-audit exact prior trajectories; never infer success from a cached flag."""
    cached = reg['reuse_development'][name]
    segment = Path(cached['segment'])
    parent = reg['parents'][name]
    assert segment.resolve() == Path(parent['segment']).resolve()
    assert sha(cached['audit']) == cached['audit_sha256']
    prior = read(cached['audit'])
    assert prior['status'] == 'passed' and prior['completed'] == 8
    assert prior['checkpoint'] == parent['checkpoint']
    output = out / (name + '.reused_development_audit.json')
    audit_segment(root, segment, output)
    fresh = read(output)
    assert fresh['rows'] == prior['rows'] and fresh['checkpoint'] == prior['checkpoint']
    return output, fresh


def run(root, out):
    reg = read(out/'REGISTRATION.json'); protocol = read(root/'PROTOCOL.json')
    assert platform.node() == reg['host'] == 'airpig'
    assert str(root)==reg['parent_root'] and str(out)==reg['run_root']
    assert sha(root/'PROTOCOL.json')==reg['parent_protocol_sha256']
    assert sha(root/'CONDITIONS.json')==reg['condition_sha256']
    assert hashes(out/'source')==read(out/'SOURCE_HASHES.json')
    assert hashes(root/'source')==read(root/'SOURCE_HASHES.json')
    assert hashes(root/'parameter_fullrange')==read(root/'PARAMETER_HASHES.json')
    assert {k:hashes(Path(protocol['runtime'])/k) for k in read(root/'RUNTIME_HASHES.json')}==read(root/'RUNTIME_HASHES.json')
    assert not (out/'execution.json').exists(), 'Use explicit recovery; preserve interrupted receipt'
    lock = (root.parent/'.local-rl-compute.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    live = subprocess.check_output(['systemctl','--user','list-units','--type=service',
        '--state=running','--no-legend','--plain','sii-local-rl*'],text=True)
    assert not live.strip(), 'Existing local RL unit found; no duplicate simulation'
    available = int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))
    assert available>=reg['resources']['admission_available_kib']
    deadline = datetime.fromisoformat(reg['dispatch_deadline_utc'])
    state = dict(status='running',started_utc=now(),host='airpig',server_compute=False,
        registration_sha256=sha(out/'REGISTRATION.json'),initial_available_kib=available,
        histories={},decisions={},active={},failures=[],final_test_reads=0)
    mutex = threading.Lock(); stop = threading.Event(); lane_id = threading.local()
    source = out/'source'; env = environment(protocol)
    def save():
        state['updated_utc']=now();write(out/'execution.json',state)
    def check_dispatch():
        assert not stop.is_set(), 'Another lane failed; preserve and review'
        assert not Path(reg.get('cooperative_stop_file', out/'STOP_REQUESTED')).exists(), 'Cooperative stop requested'
        assert datetime.now(timezone.utc)<deadline, 'Finite safety horizon reached; not convergence'
        assert shutil.disk_usage(out).free>=reg['min_free_disk_bytes'], 'Disk reserve; archive without deleting failures'
    def managed(target, argv, training=False):
        check_dispatch()
        receipt = Path(str(target)+'.execution.json')
        assert not receipt.exists() and not target.exists(), 'Never overwrite an earlier attempt'
        unit = 'sii-local-rl-conv-'+hashlib.sha256(str(target).encode()).hexdigest()[:16]
        command = ['systemd-run','--user','--wait','--pipe','--collect','--unit='+unit,
            '--property=MemoryMax=3G','--property=MemorySwapMax=0','--property=TasksMax=256',
            '--property=CPUAffinity='+['1,6','2,7'][lane_id.number],
            '--working-directory='+str(source)]+['--setenv='+k+'='+v for k,v in env.items()]+argv
        record=dict(status='running',started_utc=now(),command=argv,managed_command=command,
            host='airpig',lane=lane_id.number,unit=unit,registration_sha256=state['registration_sha256'])
        write(receipt,record)
        with mutex:state['active'][str(lane_id.number)]=dict(target=str(target),unit=unit,training=training,started_utc=record['started_utc']);save()
        with Path(str(target)+'.log').open('x') as log:
            result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,pass_fds=(lock.fileno(),))
        artifacts=[target/'execution.json',target/'AUDIT.json'] if not target.is_file() else [target]
        record.update(status='complete' if result.returncode==0 else 'failed_preserved',
            returncode=result.returncode,ended_utc=now(),artifacts={str(p):sha(p) for p in artifacts if p.is_file()})
        write(receipt,record)
        with mutex:state['active'].pop(str(lane_id.number),None);save()
        assert result.returncode==0, 'Job failed: '+str(receipt)
    def evaluate(job, segment):
        _, cp=verify_checkpoint(segment)
        manifest=Path(str(segment)+'.checkpoint.json')
        write(manifest,dict(checkpoint=cp['path'],hashes=cp['hashes'],controller=job['controller'],
            training_protocol=str(segment/'PROTOCOL.json'),training_protocol_sha256=sha(segment/'PROTOCOL.json')))
        runtime=Path(protocol['runtime'])
        for c in read(root/'CONDITIONS.json')['conditions']:
            if c['role']!='development':continue
            target=Path(str(segment)+'__'+c['id'])
            argv=[sys.executable,str(source/'tools/baseline_repair_worker_20261008.py'),
                '--research-protocol',str(root/'PROTOCOL.json'),'--protocol-sha256',sha(root/'PROTOCOL.json'),
                '--research-condition',c['id'],'--phase','development','--worker-kind','adapted_rl',
                '--v6-input',str(runtime/'v6'),'--reference',str(runtime/'v6/esn_original_v2/rollout.json'),
                '--config',str(root/'teacher.json'),'--output',str(target),'--contact-audit','--physics-dt','.00005',
                '--parameter-source',str(root/'parameter_fullrange'),'--agent-checkpoint',cp['path'],
                '--checkpoint-manifest',str(manifest)]
            if job['controller']:argv+=['--controller',job['controller']]
            managed(target,argv)
            if job['controller']:
                managed(target/'INDEPENDENT_PARAMETER_AUDIT.json',[sys.executable,
                    str(source/'tools/audit_repair_parameter_trace_20261008.py'),'--run',str(target),
                    '--parameter-source',str(root/'parameter_fullrange'),'--output',str(target/'INDEPENDENT_PARAMETER_AUDIT.json')])
        audit=Path(str(segment)+'.development_audit.json')
        managed(audit,[sys.executable,str(source/'tools/launch_rl_convergence_20261010.py'),
            'audit','--root',str(root),'--run-root',str(out),'--segment',str(segment),'--output',str(audit)])
        return read(audit)
    latest={name:Path(parent['segment']) for name,parent in reg['parents'].items()}
    # References to closed parents are explicit symlinks, never edited. All new
    # development outputs are in this run, not beside old historical receipts.
    for name, parent in reg['parents'].items():
        if parent['scheduled_limit']==110000:
            alias=out/(name+'_closed110000');alias.symlink_to(parent['segment'],target_is_directory=True)
            latest[name]=alias
    save()
    try:
        for limit in reg['training_limits']:
            jobs=[j for j in reg['jobs'] if not state['decisions'].get(j['name'],{}).get('candidate_usable_and_stable')
                  and not state['decisions'].get(j['name'],{}).get('stop_failed_plateau')]
            if limit==110000:
                jobs=[j for j in jobs if reg['parents'][j['name']]['scheduled_limit']==110000]
            def lane(number):
                lane_id.number=number
                for job in jobs[number::2]:
                    name=job['name']
                    try:
                        check_dispatch()
                        segment=latest[name]
                        old,cp=verify_checkpoint(segment)
                        if not (limit==110000 and reg['parents'][name]['scheduled_limit']==110000):
                            expected_episodes=(limit-old['steps']+1374)//1375+8
                            assert shutil.disk_usage(out).free>reg['min_free_disk_bytes']+2*expected_episodes*192*1024**2
                            segment=out/(name+f'_step{limit:06d}')
                            argv=[sys.executable,str(source/'tools/train_baseline_repair_rl_20261008.py'),
                                '--root',str(root),'--output',str(segment),'--parameter-source',str(root/'parameter_fullrange'),
                                '--seed',str(reg['seed']),'--steps','500000','--stop-at-step',str(limit),
                                '--reward',job['reward'],'--hyperparameter-id',job['hp'],
                                '--resume-checkpoint',cp['path'],'--continuation-registration',str(out/'REGISTRATION.json')]
                            if job['controller']:argv+=['--controller',job['controller']]
                            managed(segment,argv,training=True)
                            trained,_=verify_checkpoint(segment)
                            assert trained['stop_reason']=='step_budget', 'Finite/resource stop: preserve checkpoint and review'
                            if job['controller']:
                                for row in trained['rows']:
                                    target=Path(row['run'])
                                    managed(target/'INDEPENDENT_PARAMETER_AUDIT.json',[sys.executable,
                                        str(source/'tools/audit_repair_parameter_trace_20261008.py'),'--run',str(target),
                                        '--parameter-source',str(root/'parameter_fullrange'),
                                        '--output',str(target/'INDEPENDENT_PARAMETER_AUDIT.json')])
                        if limit == 110000 and name in reg.get('reuse_development', {}):
                            audit_path, report = reuse_development(root, out, reg, name)
                        else:
                            report=evaluate(job,segment)
                            audit_path=Path(str(segment)+'.development_audit.json')
                        row=dict(steps=report['steps'],scheduled_limit=limit,completed=8,task=report['task'],strict=report['strict'],
                            audit=str(audit_path),audit_sha256=sha(audit_path))
                        latest[name]=segment
                        with mutex:
                            state['histories'].setdefault(name,[]).append(row)
                            state['decisions'][name]=decision(state['histories'][name]);save()
                    except BaseException as exc:
                        stop.set()
                        write(Path(reg.get('cooperative_stop_file', out/'STOP_REQUESTED')),
                              dict(reason='Lane failed; finish current episode and preserve checkpoint',error=repr(exc)))
                        with mutex:state['failures'].append(dict(name=name,limit=limit,error=repr(exc)));save()
                        return
            with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lane,range(2)))
            if state['failures']:raise RuntimeError('Failed jobs preserved; explicit recovery needed')
        state.update(status='candidate_seed_confirmation_or_learning_review_required',ended_utc=now())
    except BaseException as exc:
        state.update(status='interrupted_or_failed_preserved',error=repr(exc),ended_utc=now());raise
    finally:save()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','run','audit'))
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--run-root',type=Path,required=True)
    p.add_argument('--segment',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args();root=a.root.resolve();out=a.run_root.resolve()
    if a.mode=='prepare':prepare(root,out)
    elif a.mode=='audit':audit_segment(root,a.segment,a.output)
    else:run(root,out)


if __name__=='__main__':main()
