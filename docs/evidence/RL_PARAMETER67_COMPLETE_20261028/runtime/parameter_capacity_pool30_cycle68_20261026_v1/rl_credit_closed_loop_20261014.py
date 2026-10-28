"""Complete development evaluation of four existing, fixed-data RL cells.

Runs only after the current online diagnostic finishes and within the SAME
12-hour authorization. No new training, no historical checkpoint alteration.
"""
import argparse
from datetime import timedelta
import fcntl
from pathlib import Path
import platform
import shutil
import subprocess
import time
from rl_reward_diagnosis_20261014 import (PYTHON,END,GIB,now,read,write,sha,
    tree_hashes,unit_state,memory_available,command)
from research72_checkpoint_20261003 import checkpoint_hashes


def prepare(root,parent,history):
    assert platform.node()=='airpig' and now()<END and not root.exists()
    p=read(parent/'PROTOCOL.json');old=read(history/'REGISTRATION.json')
    assert old['offline_only'] and len(old['jobs'])==4
    root.mkdir(parents=True)
    shutil.copytree(parent/'source',root/'source',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ('rl_credit_closed_loop_20261014.py','multistep_official_adapter_20261009.py'):
        shutil.copy2(Path(__file__).with_name(name),root/'source/tools'/name)
    for name in ('CONDITIONS.json','teacher.json','RUNTIME_VERSIONS.json'):
        shutil.copy2(parent/name,root/name)
    jobs=[]
    for entry in old['jobs']:
        cell=Path(entry['root']);training=cell/'direct_office_task_segment011k'
        state=read(training/'execution.json');spec=read(training/'PROTOCOL.json')
        assert state['status']=='complete' and state['new_physics_steps']==0
        assert state['steps']==11000 and state['updates']==12002
        assert spec['teacher_labels_used'] is False and spec['bc'] is False
        assert spec['controller'] is None and spec['agent_config']['n_step']==entry['n_step']
        assert sha(cell/'PROTOCOL.json')==entry['protocol_sha256']
        assert read(cell/'PROTOCOL.json')['formal_model_sha256']==p['formal_model_sha256']
        assert sha(cell/'CONDITIONS.json')==p['condition_file_sha256']
        cp=state['checkpoint_rows'][-1];assert checkpoint_hashes(Path(cp['path']))==cp['hashes']
        dest=root/'cells'/cell.name;dest.mkdir(parents=True)
        shutil.copytree(cell/'parameter_fullrange',dest/'parameter_fullrange',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        shutil.copytree(Path(cp['path']),dest/'checkpoint_0011000')
        shutil.copy2(training/'PROTOCOL.json',dest/'TRAINING_PROTOCOL.json')
        shutil.copy2(training/'execution.json',dest/'HISTORICAL_TRAINING_EXECUTION.json')
        parameter=dest/'parameter_fullrange'
        assert sha(parameter/'PRIORS.json')==spec['prior_file_sha256']
        assert checkpoint_hashes(dest/'checkpoint_0011000')==cp['hashes']
        manifest=dict(checkpoint=str(dest/'checkpoint_0011000'),hashes=cp['hashes'],controller=None,
            training_protocol=str(dest/'TRAINING_PROTOCOL.json'),training_protocol_sha256=sha(dest/'TRAINING_PROTOCOL.json'))
        write(dest/'CHECKPOINT_MANIFEST.json',manifest)
        write(dest/'PARAMETER_HASHES.json',tree_hashes(parameter))
        jobs.append(dict(name=cell.name,n_step=entry['n_step'],reward_variant=entry['reward_variant'],
            parameter_source=str(parameter),checkpoint_manifest=str(dest/'CHECKPOINT_MANIFEST.json'),
            historical_root=str(cell),training_steps=11000,gradient_updates=12002,
            new_training_interactions=0,seed=spec['seed']))
    p.pop('pairs',None);p.pop('reward_design_basis',None)
    p.update(registered_utc=now().isoformat(),schema='sii-existing-credit-cells-development-v1',
        primary_run=str(parent),historical_registration=str(history/'REGISTRATION.json'),
        historical_registration_sha256=sha(history/'REGISTRATION.json'),jobs=jobs,
        latest_start_utc=(END-timedelta(hours=2,minutes=30)).isoformat(),
        primary_must_finish_first=True,maximum_new_training_interactions=0,maximum_new_evaluations=16,
        evaluation_conditions=[f'repair_development_{i:03d}' for i in range(4)],
        evaluation_dispatch_deadline_utc=(END-timedelta(minutes=30)).isoformat(),
        source_scope='Current frozen evaluation physics plus n-step adapter import and this dispatcher; old trained weights/config retained byte-for-byte',
        selection='All four pre-existing cells, all four development identities. No outcome selection or final-set access.',
        interpretation='Fixed-data off-policy learning diagnostic, separate from current online seed/budget. Uncorrected n-step has behavior-policy bias; failure cannot establish RL unsuitability.',
        primary_progress_at_registration=read(parent/'LIVE.json'),
        primary_outcomes_known_at_registration='Primary progress snapshot disclosed; no outcome selection among these four historical offline cells.',
        budgets=dict(new_training_interactions=0,maximum_evaluations=16,historical_data_steps_per_cell=11000,
            historical_updates_per_cell=12002),reward_variants=['original','task_safety'],
        cooperative_stop_file=str(root/'STOP_REQUESTED'))
    write(root/'PROTOCOL.json',p);write(root/'SOURCE_HASHES.json',tree_hashes(root/'source'))
    write(root/'execution.json',dict(status='registered_waiting_for_primary',jobs=[]))
    print(sha(root/'PROTOCOL.json'),flush=True)


def lane(root,name):
    p=read(root/'PROTOCOL.json');job=next(j for j in p['jobs'] if j['name']==name)
    source=root/'source/tools';runtime=Path(p['runtime']);results=[]
    from audit_local_rl_development_20261009 import audit_run
    manifest=read(job['checkpoint_manifest'])
    assert checkpoint_hashes(Path(manifest['checkpoint']))==manifest['hashes']
    parameter=Path(job['parameter_source'])
    assert tree_hashes(parameter)==read(parameter.parent/'PARAMETER_HASHES.json')
    for condition in p['evaluation_conditions']:
        if now().isoformat()>=p['evaluation_dispatch_deadline_utc'] or (root/'STOP_REQUESTED').exists():break
        label=name+'__'+condition
        argv=[str(PYTHON),str(source/'baseline_repair_worker_20261008.py'),
            '--research-protocol',str(root/'PROTOCOL.json'),'--protocol-sha256',sha(root/'PROTOCOL.json'),
            '--research-condition',condition,'--phase','development','--worker-kind','adapted_rl',
            '--v6-input',str(runtime/'v6'),'--reference',str(runtime/'v6/esn_original_v2/rollout.json'),
            '--config',str(root/'teacher.json'),'--output',str(root/label),'--contact-audit',
            '--physics-dt','.00005','--parameter-source',job['parameter_source'],
            '--agent-checkpoint',manifest['checkpoint'],'--checkpoint-manifest',job['checkpoint_manifest']]
        command(root,label,argv)
        result=audit_run(root/label,read(root/(label+'.execution.json')),p)
        results.append(dict(condition=condition,**result))
        write(root/(name+'.results.json'),dict(job=job,status='complete' if len(results)==4 else 'partial',evaluations=results))
    write(root/(name+'.lane.json'),dict(status='complete' if len(results)==4 else 'deadline_partial',evaluations=len(results)))


def run(root):
    assert platform.node()=='airpig';p=read(root/'PROTOCOL.json');units=[]
    state=dict(status='waiting_for_primary',started_utc=now().isoformat(),units=units)
    write(root/'execution.json',state)
    while True:
        primary=read(Path(p['primary_run'])/'execution.json')
        if now().isoformat()>=p['latest_start_utc'] or (root/'STOP_REQUESTED').exists():
            state.update(status='not_dispatched_deadline_or_stop',ended_utc=now().isoformat());write(root/'execution.json',state);return
        if primary['status']=='complete_review_required':break
        if primary['status']=='failed_preserved':
            state.update(status='not_dispatched_primary_failure',ended_utc=now().isoformat());write(root/'execution.json',state);return
        time.sleep(20)
    assert tree_hashes(root/'source')==read(root/'SOURCE_HASHES.json')
    bench=root.parent.parent
    lock=(bench/'outputs/baseline_local_rl_20261009/.local-rl-compute.lock').open('a')
    while True:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
        except BlockingIOError:
            if now().isoformat()>=p['latest_start_utc'] or (root/'STOP_REQUESTED').exists():
                state.update(status='not_dispatched_lock_deadline',ended_utc=now().isoformat());write(root/'execution.json',state);return
            state['status']='waiting_for_global_lock';write(root/'execution.json',state);time.sleep(20)
    state['status']='running';write(root/'execution.json',state)
    pending=list(p['jobs']);active={}
    try:
        while pending or active:
            for unit in list(active):
                s=unit_state(unit)
                if s.get('ActiveState') in ('active','activating','deactivating'):continue
                assert s.get('Result')=='success',f'Failed managed evaluation {unit}: {s}'
                del active[unit]
            if now().isoformat()>=p['evaluation_dispatch_deadline_utc'] or (root/'STOP_REQUESTED').exists():pending=[]
            while pending and len(active)<2:
                reserve=0
                for u in active:
                    memory=unit_state(u).get('MemoryCurrent','0')
                    reserve+=max(0,3*GIB-(int(memory) if memory.isdigit() else 0))
                if memory_available()<int(3.75*GIB)+reserve:break
                job=pending.pop(0);slot=next(c for c in ('1','6') if c not in active.values())
                unit='sii-rl-credit-eval-1014-'+root.name.rsplit('_',1)[-1]+'-'+job['name'].replace('_','-')
                assert unit_state(unit).get('ActiveState') not in ('active','activating')
                args=['systemd-run','--user','--unit='+unit,'-p','MemoryMax=3G','-p','MemorySwapMax=0',
                    '-p','CPUQuota=100%','-p','CPUAffinity='+slot,'--working-directory='+str(bench)]
                env=dict(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',
                    JAX_PLATFORMS='cuda',XLA_PYTHON_CLIENT_PREALLOCATE='false',XLA_PYTHON_CLIENT_MEM_FRACTION='.20',
                    SII_LOCAL_RUNTIME=p['runtime'],MUJOCO_MENAGERIE_PATH=str(Path(p['runtime'])/'menagerie'))
                args+=['--setenv='+k+'='+v for k,v in env.items()]
                args+=[str(PYTHON),str(root/'source/tools/rl_credit_closed_loop_20261014.py'),'lane','--root',str(root),'--job',job['name']]
                subprocess.run(args,check=True);active[unit]=slot;units.append(unit)
            state.update(checked_utc=now().isoformat(),active=active,pending=[j['name'] for j in pending]);write(root/'execution.json',state)
            if active or pending:time.sleep(20)
        state['status']='complete_review_required'
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc));write(root/'STOP_REQUESTED',dict(error=repr(exc)))
        while any(unit_state(u).get('ActiveState') in ('active','activating','deactivating') for u in active):time.sleep(20)
        raise
    finally:
        state['ended_utc']=now().isoformat();write(root/'execution.json',state)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=('prepare','run','lane'))
    p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path);p.add_argument('--history',type=Path);p.add_argument('--job')
    a=p.parse_args();root=a.root.resolve()
    if a.phase=='prepare':prepare(root,a.parent.resolve(),a.history.resolve())
    elif a.phase=='run':run(root)
    else:lane(root,a.job)
