"""Online-only RL continuation with an explicit convergence-to-test gate.

The continuation resumes only from audited episode-boundary checkpoints. It
does not select a best checkpoint. Training reward statistics are used solely
to decide whether the pre-registered convergence gate is met; acceptance is
evaluated only after that gate passes.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from rl_reward_diagnosis_audit_20261014 import read, write, sha


def now(): return datetime.now(timezone.utc)


def prepare(root, parent):
    root = root.resolve(); parent = parent.resolve()
    assert not root.exists()
    pp = read(parent/'PROTOCOL.json')
    root.mkdir(parents=True)
    # Preserve the parent protocol byte-for-byte: resumed trainer verifies the
    # checkpoint lineage against this digest.
    for name in ('PROTOCOL.json', 'CONDITIONS.json', 'teacher.json', 'RUNTIME_VERSIONS.json'):
        shutil.copy2(parent/name, root/name)
    shutil.copytree(parent/'source', root/'source', ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copytree(parent/'parameter_fullrange', root/'parameter_fullrange', ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    jobs = [
        dict(name='direct_original', family='direct', controller=None, reward='office_task', hp='exploratory',
             reward_variant='original', checkpoint=str(parent/'direct_s2026101411_original_train/checkpoint_0022000')),
        dict(name='direct_task_safety', family='direct', controller=None, reward='office_task', hp='exploratory',
             reward_variant='task_safety', checkpoint=str(parent/'direct_s2026101411_task_safety_train/checkpoint_0022000')),
        dict(name='impedance_original', family='impedance', controller='impedance', reward='metric', hp='exploratory',
             reward_variant='original', checkpoint=str(parent/'impedance_s2026101411_original_train/checkpoint_0022000')),
        dict(name='impedance_payload_shaping', family='impedance', controller='impedance', reward='metric', hp='exploratory',
             reward_variant='payload_shaping', checkpoint=str(parent/'impedance_s2026101411_payload_shaping_train/checkpoint_0022000')),
    ]
    registration = dict(
        schema='sii-local-rl-convergence-v2', created_utc=now().isoformat(), host='airpig',
        # The trainer's continuation guard calls this the current run root;
        # retain the historical source separately for the coordinator wait.
        parent_root=str(root), historical_parent_root=str(parent),
        parent_protocol_sha256=sha(parent/'PROTOCOL.json'), run_root=str(root),
        resources=dict(simulator_lanes=2, threads_per_lane=1,
            memory_max_gib=3, swap=False, cpu_affinity=['1','6'], server_compute=False),
        min_free_disk_bytes=20*1024**3,
        seed=2026101411, optimizer_schedule_steps=500000,
        training_limits=[33000,44000,55000,66000,77000,88000],
        dispatch_deadline_utc=pp['training_dispatch_deadline_utc'],
        convergence=dict(min_completed_post_resume_episodes=8, window_episodes=4,
            max_relative_window_mean_change=0.05, max_window_coefficient_variation=0.25,
            statistic='undiscounted episode return; last two non-overlapping windows',
            no_checkpoint_selection=True, test_unlock='only after both paired arms pass'),
        test=dict(phase='acceptance', condition='repair_acceptance_000', heldout=False,
            note='Acceptance is untouched during training and evaluated once after convergence; final sealed set remains locked.'),
        jobs=jobs, training_interactions_are_online=True, teacher_labels_used=False,
        cooperative_stop_file=str(root/'STOP_REQUESTED'),
        limitation='Convergence is a finite reward-platform criterion, not proof of global optimum or universal RL suitability.')
    write(root/'CONTINUATION_REGISTRATION.json', registration)
    write(root/'execution.json', dict(status='registered_waiting_for_parent', created_utc=now().isoformat(), jobs=[]))
    print(sha(root/'CONTINUATION_REGISTRATION.json'), flush=True)


def stats(paths):
    rows=[]
    episodes={}
    for path in paths:
        if not (path/'training.jsonl').exists(): continue
        with (path/'training.jsonl').open() as f:
            for line in f:
                if not line.endswith('\n'): break
                x=json.loads(line); episodes.setdefault(x['episode'], 0.0); episodes[x['episode']] += x['terms']['final_reward']
    rows=[episodes[k] for k in sorted(episodes)]
    return rows


def converged(paths, reg):
    r=stats(paths); n=reg['convergence']['window_episodes'];
    if len(r)<2*n:return False,dict(episodes=len(r),reason='insufficient_complete_post_resume_episodes')
    a,b=r[-2*n:-n],r[-n:]
    ma,mb=sum(a)/n,sum(b)/n
    rel=abs(mb-ma)/max(1.,abs(ma)); cv=max((sum((x/mb-1)**2 for x in b)/n)**.5 if mb else float('inf'),0.)
    ok=rel<=reg['convergence']['max_relative_window_mean_change'] and cv<=reg['convergence']['max_window_coefficient_variation']
    return ok,dict(episodes=len(r),previous_window_mean=ma,last_window_mean=mb,
        relative_window_mean_change=rel,last_window_coefficient_variation=cv,converged=ok)


def run(root):
    root=root.resolve(); reg=read(root/'CONTINUATION_REGISTRATION.json'); parent=Path(reg['historical_parent_root'])
    while True:
        parent_state=read(parent/'execution.json')
        if parent_state['status'] in ('complete_review_required','failed_preserved'): break
        if now().isoformat() >= reg['dispatch_deadline_utc']: write(root/'execution.json',dict(status='not_dispatched_parent_deadline')); return
        time.sleep(20)
    if parent_state['status']=='failed_preserved': write(root/'execution.json',dict(status='not_dispatched_parent_failure')); return
    # Require that all four parent checkpoints are present and hashable.
    for job in reg['jobs']:
        cp=Path(job['checkpoint']); assert (cp/'office_runner.json').exists()
    pairs=[reg['jobs'][:2],reg['jobs'][2:]]
    state=dict(status='running',started_utc=now().isoformat(),pairs=[]); write(root/'execution.json',state)
    py='/home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python'
    for pair_index,pair in enumerate(pairs):
        limit=reg['training_limits'][0]
        while limit <= reg['training_limits'][-1]:
            units=[]
            for job in pair:
                out=root/(job['name']+'__'+str(limit))
                args=[py,str(root/'source/tools/train_baseline_repair_rl_20261008.py'),
                    '--root',str(root),'--output',str(out),'--parameter-source',str(root/'parameter_fullrange'),
                    '--seed',str(reg['seed']),'--steps','500000','--stop-at-step',str(limit),
                    '--reward',job['reward'],'--reward-variant',job['reward_variant'],
                    '--hyperparameter-id','exploratory','--resume-checkpoint',job['checkpoint'],
                    '--continuation-registration',str(root/'CONTINUATION_REGISTRATION.json')]
                if job['controller']: args += ['--controller',job['controller']]
                run_tag=root.name.rsplit('_',1)[-1].replace('-','')
                unit='sii-rl-convergence-1014-%s-p%d-%s'%(run_tag,pair_index,job['name'].replace('_','-'))
                cmd=['systemd-run','--user','--unit='+unit,'-p','MemoryMax=3G','-p','MemorySwapMax=0',
                     '-p','CPUQuota=100%','-p','CPUAffinity='+('1' if len(units)==0 else '6'),
                     '--working-directory='+str(root), '--setenv=OPENBLAS_NUM_THREADS=1',
                     '--setenv=OMP_NUM_THREADS=1','--setenv=MKL_NUM_THREADS=1',
                     '--setenv=SII_LOCAL_RUNTIME='+str(Path('/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/baseline_local_rl_20261009/runtime')),
                     '--setenv=MUJOCO_MENAGERIE_PATH='+str(Path('/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/baseline_local_rl_20261009/runtime/menagerie'))]+args
                subprocess.run(cmd,check=True); units.append(unit)
            while True:
                statuses=[]
                for u in units:
                    p=subprocess.run(['systemctl','--user','show',u,'-p','ActiveState','-p','Result'],capture_output=True,text=True)
                    statuses.append(dict(unit=u,text=p.stdout))
                if all('ActiveState=inactive' in x['text'] for x in statuses): break
                time.sleep(30)
            outcomes=[]; both=True
            for job in pair:
                paths=sorted(root.glob(job['name']+'__*'))
                ok,detail=converged(paths,reg); outcomes.append(dict(job=job['name'],limit=limit,**detail))
                both &= ok
            state['pairs'].append(dict(pair_index=pair_index,limit=limit,outcomes=outcomes)); write(root/'execution.json',state)
            if both: break
            limit=next((x for x in reg['training_limits'] if x>limit), None)
            if limit is None: break
            # Resume from the new segment's last checkpoint on the next pass.
            for job in pair:
                previous=limit
                job['checkpoint']=str(root/(job['name']+'__'+str(previous))/('checkpoint_%07d'%previous))
        else: both=False
        if not both:
            state.update(status='training_finished_without_convergence',ended_utc=now().isoformat()); write(root/'execution.json',state); return
    state.update(status='converged_training_test_pending',ended_utc=now().isoformat()); write(root/'execution.json',state)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=('prepare','run'));p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path)
    a=p.parse_args(); prepare(a.root,a.parent) if a.phase=='prepare' else run(a.root)
