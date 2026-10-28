"""Finite continuation: screen -> confirm -> two-seed RL -> dev -> locked final.

Not a recurring scheduler. This campaign ends within the existing 15h budget.
Any missing/failed evidence stops the dependent stage for explicit inspection.
"""
import argparse
from datetime import datetime,timezone
import fcntl
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np
from office_v7_uniform24_20261008 import read,write,sha,now
from run_baseline_repair_screen_20261008 import managed
from research72_checkpoint_20261003 import checkpoint_hashes
from evaluate_baseline_repair_20261008 import freeze,run as evaluate,BASELINES

TRAIN_STOP='2026-10-08T22:00:00+00:00'


def file_hashes(path):
    return {str(p.relative_to(path)):sha(p) for p in path.rglob('*') if p.is_file() and p.suffix in ('.py','.json')}


def score(audits):
    return [sum(a['strict_success'] for a in audits),sum(a['task_success'] for a in audits),
        sum(a['full_horizon'] for a in audits),-max(a['placement_distance_m'] for a in audits),
        -sum(a['placement_distance_m'] for a in audits),sum(max(map(int,a.get('stages',{})),default=0) for a in audits),
        -max(a['penetration_mm'] for a in audits),-sum(a['rmse_mm'] for a in audits),-sum(a['peak_torque_nm'] for a in audits)]


def physical_placement(audit,run):
    summary=read(run/'rollout.json')
    target=np.asarray(summary['placement_destination']);position=np.asarray(audit['object_final_position'])
    assert target.shape==position.shape==(3,) and np.isfinite(target).all() and np.isfinite(position).all()
    np.testing.assert_array_equal(position,summary['object_final_position'])
    return dict(audit,placement_distance_m=float(np.linalg.norm(position-target)))


def rerank_classical(directory):
    original=read(directory/'SUMMARY.json');ranked={}
    for method,candidates in original['ranked'].items():
        ranked[method]=[]
        for c in candidates:
            rows=[r for r in original['rows'] if r['candidate']['name']==c['name'] and r['status']=='complete']
            audits=[physical_placement(r['audit'],directory/(c['name']+'__'+r['condition'])) for r in rows]
            ranked[method].append(dict(c,original_score=c['score'],score=score(audits)))
        ranked[method].sort(key=lambda c:(c['score'],c['name']),reverse=True)
    return dict(ranked=ranked,original_summary_sha256=sha(directory/'SUMMARY.json'),
        reason='Diagnostic payload loss shows arm stage alone is not physical task progress; actual final payload3D distance precedes arm-stage tie-break. Original ranking and all failures retained.')


def active(unit):
    p=subprocess.run(['systemctl','--user','is-active',unit],capture_output=True,text=True)
    assert p.returncode in (0,3,4),p.stderr
    return p.returncode==0


def wait_complete(path,deadline):
    while True:
        if path.exists():
            state=read(path)
            if state['status']=='complete':return state
            if state['status'] not in ('running','registered'):raise RuntimeError(str(path)+': '+state['status'])
        assert datetime.now(timezone.utc)<deadline,'Deadline waiting for '+str(path)
        time.sleep(30)


def execute(root,source,attempt):
    protocol=read(root/'PROTOCOL.json');pdigest=sha(root/'PROTOCOL.json')
    cutoff=datetime.fromisoformat(TRAIN_STOP);end=datetime.fromisoformat(protocol['dispatch_deadline_utc'])
    assert cutoff<datetime.fromisoformat(protocol['training_dispatch_deadline_utc'])<end
    directory=root/attempt;directory.mkdir(exist_ok=False)
    write(directory/'SCHEDULE.json',dict(registered_utc=now(),protocol_sha256=pdigest,
        stop_new_training_utc=TRAIN_STOP,overall_deadline_utc=end.isoformat(),
        reason='Measured classical median ~387s/55s rollout. Reserve about one hour for80 development evaluations and >5h for384 final plus audit.',
        selection='Latest completed checkpoint per registered seed at cutoff, then same8 development conditions select one seed per RL family; all seed scores retained.',
        selection_correction='After strict/task/full, rank worst and summed final payload3D distance before arm stage, then penetration/RMSE/torque. Developed from acceptance slip diagnostic, not final outcomes; original ranking preserved.',
        resources='8 classical leases+2 direct RL, then10 RL, drain before10 development/final; each physics worker one thread and3GiB. No recurring task.',
        source=str(source),source_hashes=file_hashes(source)))
    def stage(name,**extra):
        write(directory/'execution.json',dict(status='running',stage=name,updated_utc=now(),**extra))
    stage('waiting_existing_classical_screen')
    wait_complete(root/'classical_screen/execution.json',cutoff)
    screen_rank=root/'CLASSICAL_SCREEN_PAYLOAD_RANK.json';write(screen_rank,rerank_classical(root/'classical_screen'))
    stage('classical_confirmation')
    confirmation=root/'classical_confirmation'
    assert not confirmation.exists(), 'Do not duplicate confirmation'
    subprocess.run([sys.executable,str(source/'tools/run_baseline_repair_screen_20261008.py'),
        '--root',str(root),'--mode','confirmation','--workers','8','--source-subdir',source.name,
        '--selection-file',str(screen_rank)],check=True)
    confirmation_rank=root/'CLASSICAL_CONFIRMATION_PAYLOAD_RANK.json';write(confirmation_rank,rerank_classical(confirmation))
    selected=read(confirmation_rank)['ranked']
    assert read(confirmation/'execution.json')['status']=='complete'
    parameter=root/'parameter_v2'
    shutil.copytree(root/'parameter_v1',parameter,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    # Numerical laws unchanged; bounded-memory telemetry for native torque RL.
    shutil.copy2(source/'tools/baseline_repair_controllers_20261008.py',parameter/'baseline_repair_controllers_20261008.py')
    priors=read(parameter/'PRIORS.json');chosen={}
    for method in ('vmc','admittance','impedance'):
        c=selected[method][0];assert c['episodes']==8
        priors['methods'][method]['center']=c['parameters'];chosen[method]=c
    priors['selection']='Repaired classical fixed budget24x2 then top2x8, same8 development; no final access'
    write(parameter/'PRIORS.json',priors);hashes=file_hashes(parameter)
    write(root/'PARAMETER_V2_HASHES.json',hashes)
    selection=dict(created_utc=now(),chosen=chosen,confirmation_sha256=sha(confirmation/'SUMMARY.json'),
        screen_sha256=sha(root/'classical_screen/SUMMARY.json'),parameter_source=str(parameter),parameter_hashes=hashes)
    selection['physical_ranking_evidence']={str(p):sha(p) for p in (screen_rank,confirmation_rank)}
    write(root/'CLASSICAL_SELECTION.json',selection)
    jobs=[];commands=[]
    for family in protocol['budgets']['rl_families']:
        for seed in protocol['budgets']['training_seeds']:
            controller=family.removeprefix('parameter_') if family.startswith('parameter_') else None
            reward='office_task' if family=='direct_office_task' else 'metric'
            base=root/'rl'/f'{family}_{seed}'
            exists=controller is None and seed==2026100811
            output=base/('continued_v5' if exists else 'trained_v8')
            param=parameter if controller else root/'parameter_v1'
            unit=('sii-r15-rl-direct-'+reward.replace('_','-')+'-s1-continued.service' if exists else
                'sii-r15-rl-'+family.replace('_','-')+'-'+str(seed)+'.service')
            jobs.append(dict(family=family,seed=seed,controller=controller,reward=reward,parameter_source=str(param),
                output=str(output),unit=unit,already_running=exists))
            if exists:
                assert (output/'execution.json').exists()
                continue
            assert not output.exists() and not active(unit)
            cmd=[sys.executable,str(source/'tools/train_baseline_repair_rl_20261008.py'),
                '--root',str(root),'--output',str(output),'--parameter-source',str(param),
                '--reward',reward,'--seed',str(seed),'--steps',str(protocol['budgets']['rl_steps_per_family_seed'])]
            if controller:cmd+=['--controller',controller]
            commands.append((unit,cmd))
    write(root/'RL_JOBS.json',dict(registered_utc=now(),protocol_sha256=pdigest,jobs=jobs,
        new_commands=[dict(unit=u,command=c) for u,c in commands]))
    assert len(jobs)==10 and len(commands)==8
    assert datetime.now(timezone.utc)<cutoff
    for unit,command in commands:
        launch=[x for x in managed(source,command,unit.removesuffix('.service')) if x not in ('--wait','--pipe','--collect')]
        subprocess.run(launch,check=True)
    finish_training(root,source,directory,jobs,stage)


def finish_training(root,source,directory,jobs,stage):
    protocol=read(root/'PROTOCOL.json')
    cutoff=datetime.fromisoformat(TRAIN_STOP);end=datetime.fromisoformat(protocol['dispatch_deadline_utc'])
    selection=read(root/'CLASSICAL_SELECTION.json')
    chosen=selection['chosen'];parameter=Path(selection['parameter_source']);hashes=file_hashes(parameter)
    assert hashes==selection['parameter_hashes']
    stage('ten_seed_family_training')
    while datetime.now(timezone.utc)<cutoff:
        states=[]
        for job in jobs:
            p=Path(job['output'])/'execution.json'
            s=read(p) if p.exists() else dict(status='starting')
            if s['status'] not in ('running','starting','complete'):raise RuntimeError(str(p)+': '+s['status'])
            states.append(dict(family=job['family'],seed=job['seed'],**{k:s.get(k) for k in ('status','steps','episodes','updates')}))
        stage('ten_seed_family_training',jobs=states)
        if all(s['status']=='complete' for s in states):break
        time.sleep(30)
    stage('draining_training_at_episode_boundary')
    for job in jobs:
        if active(job['unit']):
            subprocess.run(['systemctl','--user','kill','--kill-whom=main','--signal=SIGUSR1',job['unit']],check=True)
    for job in jobs:
        wait_complete(Path(job['output'])/'execution.json',end)
        while active(job['unit']):time.sleep(2)
    write(root/'TRAINING_DRAINED.json',dict(completed_utc=now(),jobs=jobs,
        execution_hashes={str(Path(j['output'])/'execution.json'):sha(Path(j['output'])/'execution.json') for j in jobs}))
    candidates=[];manifests=root/'rl_development_manifests';manifests.mkdir(exist_ok=False)
    for job in jobs:
        output=Path(job['output']);s=read(output/'execution.json')
        entry=max(s['checkpoint_rows'],key=lambda row:row['step']);cp=Path(entry['path'])
        assert checkpoint_hashes(cp)==entry['hashes']
        name=f"repaired_{job['family']}_{job['seed']}_{entry['step']}"
        manifest=manifests/(name+'.json')
        write(manifest,dict(checkpoint=str(cp),controller=job['controller'],hashes=entry['hashes'],
            training_protocol=str(output/'PROTOCOL.json'),training_protocol_sha256=sha(output/'PROTOCOL.json')))
        param=Path(job['parameter_source'])
        candidates.append(dict(name=name,family=job['family'],category=job['family'],seed=job['seed'],config={},
            cumulative_training_steps=entry['step'],updates=s['updates'],variant='latest_before_fixed_cutoff',
            parameter_source=str(param),parameter_source_hashes=file_hashes(param),
            selection_evidence={str(root/'TRAINING_DRAINED.json'):sha(root/'TRAINING_DRAINED.json')},
            adapted_rl=dict(checkpoint=str(cp),manifest=str(manifest),manifest_sha256=sha(manifest),
                parameter_source=str(param),controller=job['controller'])))
    dev_models=root/'RL_DEVELOPMENT_MODELS.json';write(dev_models,dict(candidates=candidates))
    stage('all_eight_development_conditions_for_all_ten_rl_models')
    dev=root/'rl_development'
    evaluate(root,dev_models,source,dev,'development',10,None)
    rows=[read(p) for p in (dev/'episodes').glob('*.execution.json')]
    ranked={}
    for family in protocol['budgets']['rl_families']:
        ranked[family]=[]
        for c in [c for c in candidates if c['family']==family]:
            observations=[r for r in rows if r['candidate']==c['name']]
            assert len(observations)==8 and all(r['status']=='complete' for r in observations)
            ranked[family].append(dict(candidate=c,score=score([physical_placement(r['audit'],dev/'episodes'/r['name']) for r in observations]),
                receipts={r['name']:sha(dev/'episodes'/(r['name']+'.execution.json')) for r in observations}))
        ranked[family].sort(key=lambda x:(x['score'],x['candidate']['name']),reverse=True)
    write(root/'RL_SELECTION.json',dict(selected_utc=now(),ranked=ranked,development_manifest_sha256=sha(dev_models),
        scope='Development-only selection of seed; final24 remains unopened; complete losing-seed outcomes retained'))
    final=[c for c in read(root/'REFERENCE_MODELS.json')['candidates'] if c['family'] not in BASELINES]
    for method,c in chosen.items():
        family='classical_'+method
        final.append(dict(name='repaired_'+c['name'],family=family,category=family,controller=method,
            config=dict(parameters=c['parameters']),parameter_source=str(parameter),parameter_source_hashes=hashes,
            selection_evidence={str(root/'CLASSICAL_SELECTION.json'):sha(root/'CLASSICAL_SELECTION.json')}))
    for family in protocol['budgets']['rl_families']:
        c=ranked[family][0]['candidate']
        c['selection_evidence'][str(root/'RL_SELECTION.json')]=sha(root/'RL_SELECTION.json');final.append(c)
    final_models=root/'FINAL_MODELS.json';write(final_models,dict(candidates=final))
    stage('model_lock_before_final_open')
    freeze(root,final_models,source)
    stage('locked_sixteen_by_twentyfour_final')
    evaluate(root,final_models,source,root/'final_evaluation','final',10,None)
    write(directory/'execution.json',dict(status='complete',ended_utc=now(),
        final_report=str(root/'final_evaluation/REPORT.json'),final_report_sha256=sha(root/'final_evaluation/REPORT.json'),
        note='Final statistical review and GitHub publication remain the supervising agent responsibility'))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--attempt',default='continuation_v2')
    p.add_argument('--resume-jobs',type=Path,help='Explicit audited replacement job registration; never relaunch old jobs')
    a=p.parse_args();root=a.root.resolve();assert '/' not in a.attempt
    lock=(root/'.continuation.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    try:
        if a.resume_jobs:
            protocol=read(root/'PROTOCOL.json');registration=read(a.resume_jobs);jobs=registration['jobs']
            assert registration['protocol_sha256']==sha(root/'PROTOCOL.json')
            assert len(jobs)==10 and len({j['unit'] for j in jobs})==10
            assert {(j['family'],j['seed']) for j in jobs}=={
                (f,s) for f in protocol['budgets']['rl_families'] for s in protocol['budgets']['training_seeds']}
            from baseline_repair_reward_clock_20261009 import TIME_BASE
            for j in jobs:
                output=Path(j['output']);assert output.is_relative_to(root/'rl')
                spec=read(output/'PROTOCOL.json')
                assert spec['seed']==j['seed'] and spec['controller']==j['controller'] and spec['reward']['mode']==j['reward']
                if j['reward']=='metric':assert spec['torque_slew_time_base']==TIME_BASE
                assert read(output/'execution.json')['status'] in ('running','complete')
            directory=root/a.attempt;directory.mkdir(exist_ok=False)
            write(directory/'SCHEDULE.json',dict(registered_utc=now(),protocol_sha256=sha(root/'PROTOCOL.json'),
                stop_new_training_utc=TRAIN_STOP,overall_deadline_utc=protocol['dispatch_deadline_utc'],
                resume_registration=str(a.resume_jobs),resume_registration_sha256=sha(a.resume_jobs),
                source=str(a.source.resolve()),source_hashes=file_hashes(a.source.resolve()),
                reason='Explicit servo-time reward correction. Reuse completed classical selection and all physical data; only affected metric learners rebuilt. Task learners unchanged. No deadline extension or heldout access.'))
            def stage(name,**extra):
                write(directory/'execution.json',dict(status='running',stage=name,updated_utc=now(),**extra))
            finish_training(root,a.source.resolve(),directory,jobs,stage)
        else:execute(root,a.source.resolve(),a.attempt)
    except BaseException as exc:
        d=root/a.attempt
        if d.exists():write(d/'FAILURE.json',dict(ended_utc=now(),error=repr(exc),old_evidence_preserved=True))
        raise


if __name__=='__main__':main()
