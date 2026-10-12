"""Finish one interrupted registered RL node, then audit eight development runs.

Single local lane; original CUDA runtime; immutable source/checkpoint receipts.
No final-test reads, automatic budget extension, or reuse of CPU probe scores.
"""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from office_v7_uniform24_20261008 import read, write, sha, now
from local_rl_campaign_20261009 import hashes
from launch_rl_convergence_20261010 import verify_checkpoint, environment, audit_segment
from report_rl_longrun_20261011 import verified_node

NAME = 'parameter_impedance_historical_entropy'


def check_runtime(root):
    protocol = read(root/'PROTOCOL.json')
    expected = read(root/'RUNTIME_HASHES.json')
    assert {k: hashes(Path(protocol['runtime'])/k) for k in expected} == expected, 'Frozen runtime changed'
    assert hashes(root/'source') == read(root/'SOURCE_HASHES.json')
    assert hashes(root/'parameter_fullrange') == read(root/'PARAMETER_HASHES.json')
    assert sha(root/'CONDITIONS.json') == protocol['condition_file_sha256']


def validate_parent(state, limit):
    assert state['status'] == 'complete' and state['stop_reason'] == 'deadline'
    assert 0 < limit-state['steps'] <= 100000, 'Only finish the interrupted node'


def prepare(root, parent, out):
    assert platform.node() == 'airpig' and not out.exists()
    check_runtime(root)
    old_reg = read(parent/'REGISTRATION.json')
    assert hashes(parent/'source') == read(parent/'SOURCE_HASHES.json')
    segment = parent/(NAME+'_step165000')
    state, cp = verify_checkpoint(segment)
    validate_parent(state, 165000)
    conditions = read(root/'CONDITIONS.json')['conditions']
    ids = {c['id'] for c in conditions if c['role'] == 'development'}
    history = read(parent/'execution.json')['histories']
    reuse = {}
    for job in old_reg['jobs']:
        if job['name'] == NAME:
            continue
        entry = history[job['name']][-1]
        assert entry['scheduled_limit'] == 165000
        reuse[job['name']] = dict(entry=entry, verified=verified_node(entry, ids, {}))
    assert len(reuse) == 6
    out.mkdir(parents=True)
    shutil.copytree(parent/'source', out/'source', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    # These helpers postdate the parent snapshot. Freeze them with the runner
    # so an isolated launch never imports a changing working-tree module.
    for name in (Path(__file__).name, 'report_rl_longrun_20261011.py',
                 'overnight_baseline_coordinator_20261010.py', 'monitor_rl_recovery_20261011.py'):
        shutil.copy2(Path(__file__).parent/name, out/'source/tools'/name)
    stamp = datetime.now(timezone.utc)
    job = next(j for j in old_reg['jobs'] if j['name'] == NAME)
    reg = dict(schema='sii-local-rl-convergence-v2', registered_utc=stamp.isoformat(),
        authorization='2026-10-12 user: continue baseline work; finish incomplete node before reviewing further budgets',
        parent_root=str(root), run_root=str(out), parent_run=str(parent),
        parent_protocol_sha256=sha(root/'PROTOCOL.json'), condition_sha256=sha(root/'CONDITIONS.json'),
        parent_registration_sha256=sha(parent/'REGISTRATION.json'), host='airpig',
        seed=old_reg['seed'], jobs=[job], parents={NAME: dict(segment=str(segment), checkpoint=cp,
            execution_sha256=sha(segment/'execution.json'), steps=state['steps'])},
        optimizer_schedule_steps=500000, training_limits=[165000], reused_nodes=reuse,
        dispatch_deadline_utc=(stamp+timedelta(hours=12)).isoformat(),
        deadline_basis='Agent-chosen 12h dispatch ceiling under renewed continuation authority; not a convergence target',
        cooperative_stop_file=str(out/'STOP_REQUESTED'), min_free_disk_bytes=40*1024**3,
        resources=dict(server_compute=False, simulators=1, numerical_threads=1,
            memory_max_per_lane=3*1024**3, memory_swap_max=0, admission_available_kib=4*1024**2),
        final_test_reads=0, cpu_probe_included=False,
        source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    write(out/'REGISTRATION.json', reg)
    write(out/'SOURCE_HASHES.json', hashes(out/'source'))
    print('registered', str(out), sha(out/'REGISTRATION.json'), flush=True)


def managed(target, argv, *, source, env, lock, state, out, training=False):
    receipt = Path(str(target)+'.execution.json')
    assert not receipt.exists() and not target.exists(), 'Never overwrite an attempt'
    unit = 'sii-local-rl-node-'+hashlib.sha256(str(target).encode()).hexdigest()[:16]
    command = ['systemd-run','--user','--wait','--pipe','--collect','--unit='+unit,
        '--property=MemoryMax=3G','--property=MemorySwapMax=0','--property=TasksMax=256',
        '--property=CPUAffinity=1,6','--working-directory='+str(source)]
    command += ['--setenv='+k+'='+v for k,v in env.items()]+argv
    record = dict(status='running', started_utc=now(), command=argv, managed_command=command,
        host='airpig', unit=unit, registration_sha256=state['registration_sha256'])
    write(receipt, record)
    state['active']={'0':dict(target=str(target),unit=unit,training=training,started_utc=now())}
    write(out/'execution.json', state)
    try:
        with Path(str(target)+'.log').open('x') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, pass_fds=(lock.fileno(),))
        record.update(status='complete' if result.returncode == 0 else 'failed_preserved',
            returncode=result.returncode)
        assert result.returncode == 0, 'Managed child failed: '+str(receipt)
    except BaseException as exc:
        record.update(status='failed_preserved',error=repr(exc))
        raise
    finally:
        paths = [target] if target.is_file() else [target/'execution.json',target/'AUDIT.json']
        record.update(ended_utc=now(),artifacts={str(p):sha(p) for p in paths if p.is_file()})
        write(receipt,record)
        state['active']={};write(out/'execution.json',state)


def run(root, out):
    assert not (out/'execution.json').exists(), 'Preserve previous execution'
    reg=read(out/'REGISTRATION.json'); protocol=read(root/'PROTOCOL.json')
    state=dict(status='running', started_utc=now(), host='airpig', server_compute=False,
        registration_sha256=sha(out/'REGISTRATION.json'),active={},histories={},failures=[],final_test_reads=0)
    write(out/'execution.json',state)
    lock=(root.parent/'.local-rl-compute.lock').open('a')
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        live=subprocess.check_output(['systemctl','--user','list-units','--type=service',
            '--state=running','--no-legend','--plain','sii-local-rl*'],text=True)
        assert not live.strip(), 'An existing RL worker must finish first'
        assert platform.node()==reg['host']=='airpig'
        assert str(root)==reg['parent_root'] and str(out)==reg['run_root']
        assert sha(root/'PROTOCOL.json')==reg['parent_protocol_sha256']
        assert hashes(out/'source')==read(out/'SOURCE_HASHES.json')
        check_runtime(root)
        available=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))
        assert available>=reg['resources']['admission_available_kib']
        state['initial_available_kib']=available
        source=out/'source';env=environment(protocol)
        deadline=datetime.fromisoformat(reg['dispatch_deadline_utc'])
        def dispatch(target, argv, training=False):
            assert datetime.now(timezone.utc)<deadline, 'Dispatch deadline reached'
            assert not Path(reg['cooperative_stop_file']).exists(), 'Cooperative stop requested'
            assert shutil.disk_usage(out).free>=reg['min_free_disk_bytes'], 'Disk reserve'
            managed(target,argv,source=source,env=env,lock=lock,state=state,out=out,training=training)
        parent=reg['parents'][NAME]
        assert sha(Path(parent['segment'])/'execution.json')==parent['execution_sha256']
        _,cp=verify_checkpoint(Path(parent['segment']))
        assert cp==parent['checkpoint']
        segment=out/(NAME+'_step165000');job=reg['jobs'][0]
        dispatch(segment,[sys.executable,str(source/'tools/train_baseline_repair_rl_20261008.py'),
            '--root',str(root),'--output',str(segment),'--parameter-source',str(root/'parameter_fullrange'),
            '--seed',str(reg['seed']),'--steps','500000','--stop-at-step','165000',
            '--reward',job['reward'],'--hyperparameter-id',job['hp'],'--controller',job['controller'],
            '--resume-checkpoint',cp['path'],'--continuation-registration',str(out/'REGISTRATION.json')],training=True)
        trained,cp=verify_checkpoint(segment)
        if trained['stop_reason']!='step_budget':
            state.update(status='stopped_at_deadline' if trained['stop_reason']=='deadline' else 'stopped_requested',
                checkpoint=cp,stop_reason=trained['stop_reason'])
            return
        def parameter_audit(target):
            dispatch(target/'INDEPENDENT_PARAMETER_AUDIT.json',[sys.executable,
                str(source/'tools/audit_repair_parameter_trace_20261008.py'),'--run',str(target),
                '--parameter-source',str(root/'parameter_fullrange'),
                '--output',str(target/'INDEPENDENT_PARAMETER_AUDIT.json')])
        for row in trained['rows']:
            parameter_audit(Path(row['run']))
        manifest=Path(str(segment)+'.checkpoint.json')
        write(manifest,dict(checkpoint=cp['path'],hashes=cp['hashes'],controller=job['controller'],
            training_protocol=str(segment/'PROTOCOL.json'),training_protocol_sha256=sha(segment/'PROTOCOL.json')))
        runtime=Path(protocol['runtime'])
        ids=[c['id'] for c in read(root/'CONDITIONS.json')['conditions'] if c['role']=='development']
        for identity in ids:
            target=Path(str(segment)+'__'+identity)
            dispatch(target,[sys.executable,str(source/'tools/baseline_repair_worker_20261008.py'),
                '--research-protocol',str(root/'PROTOCOL.json'),'--protocol-sha256',sha(root/'PROTOCOL.json'),
                '--research-condition',identity,'--phase','development','--worker-kind','adapted_rl',
                '--v6-input',str(runtime/'v6'),'--reference',str(runtime/'v6/esn_original_v2/rollout.json'),
                '--config',str(root/'teacher.json'),'--output',str(target),'--contact-audit','--physics-dt','.00005',
                '--parameter-source',str(root/'parameter_fullrange'),'--agent-checkpoint',cp['path'],
                '--checkpoint-manifest',str(manifest),'--controller',job['controller']])
            parameter_audit(target)
        audit=Path(str(segment)+'.development_audit.json')
        dispatch(audit,[sys.executable,str(source/'tools/launch_rl_convergence_20261010.py'),
            'audit','--root',str(root),'--run-root',str(out),'--segment',str(segment),'--output',str(audit)])
        result=read(audit)
        entry=dict(steps=result['steps'],scheduled_limit=165000,completed=8,task=result['task'],strict=result['strict'],
            audit=str(audit),audit_sha256=sha(audit))
        state['histories'][NAME]=[entry]
        matrix={name:verified_node(v['entry'],set(ids),{}) for name,v in reg['reused_nodes'].items()}
        matrix[NAME]=verified_node(entry,set(ids),{})
        write(out/'SEVEN_METHOD_DEVELOPMENT.json',dict(created_utc=now(),methods=matrix,
            cpu_probe_included=False,final_test_reads=0,convergence_claim=False,
            limitation='Single-seed development at actual episode-boundary budgets; not final uniform heldout evaluation.'))
        state.update(status='complete_review_required',completed_methods=7)
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc))
        state['failures'].append(dict(error=repr(exc)))
        raise
    finally:
        state['ended_utc']=now();write(out/'execution.json',state);lock.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','run'))
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--parent',type=Path)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.mode=='prepare':prepare(a.root.resolve(),a.parent.resolve(),a.out.resolve())
    else:run(a.root.resolve(),a.out.resolve())


if __name__=='__main__':main()
