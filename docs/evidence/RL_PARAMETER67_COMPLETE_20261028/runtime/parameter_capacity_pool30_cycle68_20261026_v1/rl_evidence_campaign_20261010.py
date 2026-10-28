"""Finite local 2x2 online experiment: reward information x credit horizon.

All four cells start from scratch with the same seed, conditions and budgets.
First verify a synthetic optimizer control, then collect paired 11k/55k
development curves. Stop after this diagnostic phase; do not silently promote
single-seed zero success to 'RL unsuitable' or allocate an unbounded extension.
"""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from office_v7_uniform24_20261008 import read, write, sha, now
from local_rl_campaign_20261009 import hashes
from launch_rl_convergence_20261010 import environment, verify_checkpoint, audit_segment

TOOLS = Path(__file__).resolve().parent
OVERLAYS = (
    'rl_evidence_campaign_20261010.py', 'rl_optimizer_positive_control_20261010.py',
    'train_baseline_repair_rl_20261008.py', 'baseline_repair_online_worker_20261008.py',
    'multistep_official_adapter_20261009.py', 'multistep_rl_replay_20261009.py',
    'decoupled_task_safety_reward_20261009.py', 'audit_decoupled_task_safety_reward_20261009.py',
    'audit_rebuild_repair_reward_20261008.py', 'audit_local_rl_development_20261009.py',
    'launch_rl_convergence_20261010.py', 'extend_local_rl_training_20261009.py',
)


def cells():
    return [dict(name=f'n{n:02d}_{variant}',n_step=n,reward_variant=variant)
        for n,variant in ((1,'original'),(25,'original'),(1,'task_safety'),(25,'task_safety'))]


def assess_phase(rows):
    """Incomplete or unaudited data never constitute a ranking or convergence."""
    required={(c['name'],limit) for c in cells() for limit in (11000,55000)}
    keys=[(r['cell'],r['scheduled_limit']) for r in rows]
    assert len(keys)==len(set(keys))
    complete = set(keys)==required and all(r['completed']==8 and r['audit_passed'] for r in rows)
    return dict(paired_phase_complete=complete,convergence_demonstrated=False,
        tuning_sufficient=False,rl_generally_unsuitable=False,final_test_reads=0,
        next_action='Review paired task/strict and stage curves; register cross-algorithm and independent-seed confirmation'
            if complete else 'Complete missing registered cells without replacing failures')


def prepare(parent,out):
    assert platform.node()=='airpig' and not out.exists()
    p=read(parent/'PROTOCOL.json')
    assert hashes(parent/'source')==read(parent/'SOURCE_HASHES.json')
    assert hashes(parent/'parameter_fullrange')==read(parent/'PARAMETER_HASHES.json')
    assert sha(parent/'CONDITIONS.json')==p['condition_file_sha256']
    out.mkdir(parents=True)
    start=datetime.now(timezone.utc)
    deadline=(start+timedelta(hours=48)).isoformat()
    stop=out/'STOP_REQUESTED'
    seed=2026101011
    jobs=cells()
    for cell in jobs:
        root=out/cell['name'];root.mkdir()
        shutil.copytree(parent/'source',root/'source',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for name in OVERLAYS:shutil.copy2(TOOLS/name,root/'source/tools'/name)
        parameter=root/'parameter_fullrange'
        shutil.copytree(parent/'parameter_fullrange',parameter,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        (parameter/'official_parameter_agent.py').rename(parameter/'official_parameter_agent_base.py')
        (parameter/'official_parameter_agent.py').write_text(
            'from pathlib import Path\nfrom multistep_official_adapter_20261009 import make_adapter\n'
            'BATCH_SIZE=256\nOfficialParameterAgent=make_adapter(Path(__file__).with_name('
            '"official_parameter_agent_base.py"),n_step='+str(cell['n_step'])+')\n')
        for name in ('CONDITIONS.json','teacher.json','RUNTIME_HASHES.json'):
            shutil.copy2(parent/name,root/name)
        protocol=dict(p,registered_utc=now(),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),
            authorization='2026-10-10 user: use local compute to investigate defensible RL evidence, not engineer negative results',
            source_scope='Frozen parent physics plus named learner/reward-telemetry/audit overlays; per-file hashes govern reproduction',
            overlay_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=TOOLS,text=True).strip(),
            training_dispatch_deadline_utc=deadline,cooperative_stop_file=str(stop),min_free_disk_bytes=50*1024**3,
            deadline_basis='Agent-selected 48h dispatch safety horizon for finite diagnostic phase, not user budget or convergence',
            budgets=dict(training_seeds=[seed],rl_steps_per_family_seed=500000,
                planned_max_new_interactions=55000,optimizer_schedule_steps=500000),
            jobs=[dict(name='direct_office_task',controller=None,reward='office_task',hp='exploratory')],
            reward_variants=[cell['reward_variant']],n_step=cell['n_step'],
            resources=dict(host='airpig',server_compute=False,simulators=1,numerical_threads=1,
                memory_max_bytes=3*1024**3,swap_max_bytes=0),
            readiness='This phase diagnoses learning mechanisms, not sufficient tuning or statistical convergence',
            completion='All four fresh cells at11k and55k plus eight development identities each; no automatic extension',
            registration_kind='Prospective paired online reward x n-step ablation; NOT the historical offline-prefix trial')
        write(root/'PROTOCOL.json',protocol)
        write(root/'SOURCE_HASHES.json',hashes(root/'source'))
        write(root/'PARAMETER_HASHES.json',hashes(parameter))
        cell.update(root=str(root),protocol_sha256=sha(root/'PROTOCOL.json'),
            source_manifest_sha256=sha(root/'SOURCE_HASHES.json'),parameter_manifest_sha256=sha(root/'PARAMETER_HASHES.json'))
    reg=dict(schema='sii-rl-evidence-phase1-v1',registered_utc=now(),compute_host='airpig',
        parent=str(parent),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),jobs=jobs,
        seed=seed,training_limits=[11000,55000],maximum_online_training_interactions=220000,
        maximum_development_episodes=64,maximum_development_interactions=88000,
        final_test_reads=0,teacher_labels_used=False,source_sha256=sha(__file__),
        dispatch_deadline_utc=deadline,cooperative_stop_file=str(stop),min_free_disk_bytes=50*1024**3,
        resources=dict(simulators=1,threads=1,memory_max_bytes=3*1024**3,swap_max_bytes=0,
            admission_available_kib=5*1024**2,server_compute=False),
        exposure='4 fresh paired cells; cumulative steps are not summed across nodes; all failures retained',
        positive_control=dict(seed=2026101021,evaluation_seed=2026101022,interactions=12000,
            reward_optimum=[.6,-.5,.4,-.3,.2,-.1,.5],maximum_mse=.05,maximum_initial_ratio=.5,
            definition='one-step synthetic reward -mean((action-optimum)^2), uniform48 observations; optimum never given to actor',
            limitation='Optimizer/adapter sanity only, not a robotic positive control'),
        selection='No winner promoted automatically; compare all cells Task/Strict and paired stage/physical metrics at both nodes',
        inference='Single seed; cannot establish adequate tuning, convergence, universality or final ESN superiority',
        next_phases=['robotic positive control with separate diagnostic protocol',
            'SAC/PPO and memory-capable RL under same actor contract with implementation tests',
            'registered finite hyperparameter search, then >=5 independent training seeds',
            'budget extension and meaningful-effect uncertainty, then separately frozen independent final evaluation'],
        multistep_caveat='Uncorrected off-policy n-step returns introduce behavior-policy bias; declared ablation, not an exact SAC-equivalent estimator')
    write(out/'REGISTRATION.json',reg)
    print('registered',out,sha(out/'REGISTRATION.json'))


def run(out):
    reg=read(out/'REGISTRATION.json')
    assert platform.node()==reg['compute_host']=='airpig'
    assert not (out/'execution.json').exists(),'Preserve previous attempt; no automatic retry'
    lock=(out.parent/'.local-rl-compute.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    live=subprocess.check_output(['systemctl','--user','list-units','--type=service','--state=running',
        '--no-legend','--plain','sii-local-rl*'],text=True)
    assert not live.strip(),'Another local RL unit is running'
    available=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))
    assert available>=reg['resources']['admission_available_kib']
    for cell in reg['jobs']:
        root=Path(cell['root'])
        assert sha(root/'PROTOCOL.json')==cell['protocol_sha256']
        assert sha(root/'SOURCE_HASHES.json')==cell['source_manifest_sha256']
        assert sha(root/'PARAMETER_HASHES.json')==cell['parameter_manifest_sha256']
        assert hashes(root/'source')==read(root/'SOURCE_HASHES.json')
        assert hashes(root/'parameter_fullrange')==read(root/'PARAMETER_HASHES.json')
        assert sha(root/'CONDITIONS.json')==read(root/'PROTOCOL.json')['condition_file_sha256']
    root=Path(reg['jobs'][0]['root']);p=read(root/'PROTOCOL.json');runtime=Path(p['runtime'])
    assert {n:hashes(runtime/n) for n in read(root/'RUNTIME_HASHES.json')}==read(root/'RUNTIME_HASHES.json')
    state=dict(status='running',started_utc=now(),host='airpig',server_compute=False,
        registration_sha256=sha(out/'REGISTRATION.json'),development=[],active=None,final_test_reads=0)
    def save():state['updated_utc']=now();write(out/'execution.json',state)
    def admit():
        if Path(reg['cooperative_stop_file']).exists():raise InterruptedError('Cooperative stop requested; completed episodes retained')
        if datetime.now(timezone.utc)>=datetime.fromisoformat(reg['dispatch_deadline_utc']):raise InterruptedError('Dispatch safety horizon reached')
        if shutil.disk_usage(out).free<reg['min_free_disk_bytes']:raise InterruptedError('Disk reserve reached; no deletion')
    def managed(root,target,argv):
        admit()
        receipt=Path(str(target)+'.managed.json')
        assert not target.exists() and not receipt.exists()
        unit='sii-local-rl-evidence-'+hashlib.sha256(str(target).encode()).hexdigest()[:12]
        command=['systemd-run','--user','--wait','--pipe','--collect','--unit='+unit,
            '--property=MemoryMax=3G','--property=MemorySwapMax=0','--property=TasksMax=256',
            '--property=CPUAffinity=1,6','--working-directory='+str(root/'source')]
        command+=['--setenv='+k+'='+v for k,v in environment(read(root/'PROTOCOL.json')).items()]+argv
        record=dict(status='running',started_utc=now(),command=argv,managed_command=command,unit=unit,
            registration_sha256=state['registration_sha256'],host='airpig')
        write(receipt,record);state['active']=dict(unit=unit,target=str(target));save()
        with Path(str(target)+'.log').open('x') as log:
            result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,pass_fds=(lock.fileno(),))
        record.update(status='complete' if result.returncode==0 else 'failed_preserved',returncode=result.returncode,ended_utc=now())
        write(receipt,record);state['active']=None;save()
        if result.returncode:raise RuntimeError('Failed job preserved: '+str(receipt))
    save()
    try:
        positive=out/'optimizer_positive_control'
        managed(root,positive,[sys.executable,str(root/'source/tools/rl_optimizer_positive_control_20261010.py'),
            '--root',str(root),'--output',str(positive)])
        assert read(positive/'execution.json')['passed'],'Synthetic optimizer control failed; investigate before robot training'
        latest={}
        for limit in reg['training_limits']:
            for cell in reg['jobs']:
                root=Path(cell['root']);source=root/'source';parameter=root/'parameter_fullrange'
                target=root/f'direct_office_task_step{limit:06d}'
                argv=[sys.executable,str(source/'tools/train_baseline_repair_rl_20261008.py'),
                    '--root',str(root),'--output',str(target),'--parameter-source',str(parameter),
                    '--seed',str(reg['seed']),'--steps','500000','--stop-at-step',str(limit),
                    '--reward','office_task','--reward-variant',cell['reward_variant'],'--hyperparameter-id','exploratory']
                if cell['name'] in latest:argv+=['--resume-checkpoint',latest[cell['name']]]
                managed(root,target,argv)
                state_train,cp=verify_checkpoint(target)
                latest[cell['name']]=cp['path']
                if state_train['stop_reason']!='step_budget':raise InterruptedError('Trainer ended at a safe boundary before requested node')
                manifest=Path(str(target)+'.checkpoint.json')
                write(manifest,dict(checkpoint=cp['path'],hashes=cp['hashes'],controller=None,
                    training_protocol=str(target/'PROTOCOL.json'),training_protocol_sha256=sha(target/'PROTOCOL.json')))
                for c in read(root/'CONDITIONS.json')['conditions']:
                    if c['role']!='development':continue
                    evaluation=Path(str(target)+'__'+c['id'])
                    argv=[sys.executable,str(source/'tools/baseline_repair_worker_20261008.py'),
                        '--research-protocol',str(root/'PROTOCOL.json'),'--protocol-sha256',cell['protocol_sha256'],
                        '--research-condition',c['id'],'--phase','development','--worker-kind','adapted_rl',
                        '--v6-input',str(runtime/'v6'),'--reference',str(runtime/'v6/esn_original_v2/rollout.json'),
                        '--config',str(root/'teacher.json'),'--output',str(evaluation),'--contact-audit','--physics-dt','.00005',
                        '--parameter-source',str(parameter),'--agent-checkpoint',cp['path'],'--checkpoint-manifest',str(manifest)]
                    managed(root,evaluation,argv)
                    # Existing independent audit expects this receipt suffix.
                    write(Path(str(evaluation)+'.execution.json'),read(Path(str(evaluation)+'.managed.json')))
                audit=Path(str(target)+'.development_audit.json')
                managed(root,audit,[sys.executable,str(source/'tools/rl_evidence_campaign_20261010.py'),
                    'audit','--root',str(root),'--segment',str(target),'--output',str(audit)])
                result=read(audit)
                state['development'].append(dict(cell=cell['name'],scheduled_limit=limit,steps=result['steps'],
                    completed=result['completed'],task=result['task'],strict=result['strict'],
                    audit_passed=result['status']=='passed',audit=str(audit),audit_sha256=sha(audit),
                    stages=[r['stage'] for r in result['rows']]))
                state['assessment']=assess_phase(state['development']);save()
        state.update(status='diagnostic_phase_complete',assessment=assess_phase(state['development']))
    except InterruptedError as exc:
        state.update(status='stopped_at_safe_boundary',reason=str(exc))
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        state['ended_utc']=now();save()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','run','audit'))
    p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path)
    p.add_argument('--segment',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if a.mode=='prepare':prepare(a.parent.resolve(),a.root.resolve())
    elif a.mode=='run':run(a.root.resolve())
    else:audit_segment(a.root.resolve(),a.segment.resolve(),a.output.resolve())
