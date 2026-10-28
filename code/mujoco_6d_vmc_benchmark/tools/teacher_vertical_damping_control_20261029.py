"""One bounded vertical-damping control after the v7 terminal-motion failure.

Only virtual z damping changes 110 -> 220 Ns/m. Preserve static compliance,
all recovery parameters, actor inputs, common filter and physical limits.
Select four ball training controls: original00 and the three largest last250
speed-RMS training cases. No validation trajectory is used to rank controls.
Rod00, corner00 and inspected office000 protect the prior teacher repairs.
"""
import argparse
import copy
from pathlib import Path
import shutil
import subprocess

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now, run as run_cases
from prepare_teacher_damping_control_20261029 import checks
from review_special_collection_probe_20261028 import evidence

COLLECTION=ROOT/'outputs/special_scene_vmc_collection_20261029_v7'
HANDOFF=ROOT/'outputs/special_scene_learning_handoff_20261029_v7'
PARENT=ROOT/'outputs/special_teacher_clearance_offset_20261029_v1'
DIAGNOSIS=ROOT/'outputs/special_scene_v7_ball_tail_20261029_v1/REVIEW.json'
SERVICE='sii-special-teacher-vertical-damping-v1-20261029.service'


def require_originals_terminal():
    assert read(COLLECTION/'COLLECTION_PROGRESS.json')['status']=='finished_with_nonqualified_demonstrations'
    assert read(HANDOFF/'execution.json')['status']=='failed_preserved'
    for service in ('sii-special-collection-v7-20261029.service','sii-special-learning-handoff-v7-20261029.service'):
        p=dict(s.split('=',1) for s in subprocess.check_output(['systemctl','--user','show',service,
            '-p','MainPID','-p','ActiveState'],text=True).splitlines())
        assert p['MainPID']=='0' and p['ActiveState'] in ('inactive','failed'),p


def prepare(root):
    assert not root.exists()
    require_originals_terminal()
    complete=read(COLLECTION/'FULL_REVIEW.json')
    assert len(complete['rows'])==30 and not complete['all30_qualified']
    oldreg=read(PARENT/'REGISTRATION.json')
    assert read(PARENT/'REVIEW.json')['all_six_qualified']
    plan=read(COLLECTION/'COLLECTION_PLAN.json');diagnosis=read(DIAGNOSIS)
    assert diagnosis['plan_sha256']==sha(COLLECTION/'COLLECTION_PLAN.json')
    assert diagnosis['source_sha256']==sha(ROOT/'tools/audit_special_ball_tail_20261029.py')
    train=sorted((r for r in diagnosis['rows'] if r['split']=='train'),
                 key=lambda r:(-r['last250_speed_rms_mps'],r['id']))
    assert [r['id'] for r in train]==diagnosis['training_tail_rms_rank']
    ids=['rod_00','ball_00']+[r['id'] for r in train[:3]]+['corner_00']
    assert len(set(ids))==6
    before=read(Path(plan['teacher_config']));after=copy.deepcopy(before)
    assert before['options']['damping_6d']==[56.,56.,110.,2.8,2.4,3.]
    assert sha(Path(plan['teacher_config']))==plan['teacher_config_sha256']
    after['options']['damping_6d'][2]=220.
    actor_checks=checks(before,after)
    root.mkdir(parents=True)
    teacher=root/'teacher_vertical_damping.json';write(teacher,after)
    write(root/'ACTOR_CHECKS.json',actor_checks)
    shutil.copytree(PARENT/'source',root/'source',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    copied={str(p.relative_to(PARENT/'source')):sha(p) for p in (PARENT/'source').rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    assert all(sha(root/'source'/n)==h for n,h in copied.items())
    write(root/'SOURCE_COPY_REVIEW.json',dict(parent=str(PARENT/'source'),files=copied,all_identical=True))
    cases=[]
    for identity in ids:
        entry=next(e for e in plan['episodes'] if e['id']==identity)
        assert entry['split']=='train'
        folder=Path(entry['folder']);q=read(folder/'DEMONSTRATION_QUALIFICATION.json')
        assert q['status']=='qualified'
        for n,h in q['input_hashes'].items():assert sha(folder/n)==h
        cases.append(dict(id='vertical_damping_'+identity,kind='scene',scene=entry['scene'],
            identity=identity,seed=entry['seed'],scene_parameters=entry['scene_parameters'],
            expected_model_sha256=read(folder/'execution.json')['model_sha256'],baseline=str(folder),
            baseline_execution_sha256=sha(folder/'execution.json'),config=str(teacher),model=None))
    office=copy.deepcopy(next(c for c in oldreg['cases'] if c['kind']=='office'))
    office.update(id='vertical_damping_office000',config=str(teacher))
    office['command'][1]=str(root/'source/tools/legacy_teacher_office_driver_20261029.py')
    cases.append(office)
    reg=copy.deepcopy(oldreg)
    reg.update(schema='sii-teacher-vertical-damping-seven-controls-v1',registered_utc=now(),service=SERVICE,
        cases=cases,maximum_episodes=7,config_sha256={str(teacher):sha(teacher)},
        collection_plan_sha256=sha(COLLECTION/'COLLECTION_PLAN.json'),
        collection_review_sha256=sha(COLLECTION/'FULL_REVIEW.json'),diagnosis_sha256=sha(DIAGNOSIS),
        parent=str(PARENT),parent_review_sha256=sha(PARENT/'REVIEW.json'),
        parent_execution_sha256=sha(PARENT/'execution.json'),
        parent_config_sha256=sha(Path(plan['teacher_config'])),interpretation=__doc__,
        changed_parameter=dict(name='options.damping_6d[2]',before=110.,after=220.),
        changes_from_immediate_parent=['Only virtual vertical damping 110 to 220 Ns/m'],
        actor_checks_sha256=sha(root/'ACTOR_CHECKS.json'),source_copy_review_sha256=sha(root/'SOURCE_COPY_REVIEW.json'),
        selection_rule='One fixed candidate; all six training scene qualifications and office Task/Strict required, '
        'plus lower total last250 speed squared sum across four ball training controls. '
        'Individual regressions reported. No validation parameter ranking, automatic collection or fitting.')
    reg['source_sha256']={n:sha(ROOT/n) for n in oldreg['source_sha256'] if not n.startswith('outputs/')}
    for p in (Path(__file__),ROOT/'tools/prepare_teacher_damping_control_20261029.py',DIAGNOSIS,COLLECTION/'FULL_REVIEW.json'):
        reg['source_sha256'][str(p.relative_to(ROOT))]=sha(p)
    reg['source_sha256'].update({str(p.relative_to(ROOT)):sha(p) for p in (root/'source').rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'})
    write(root/'REGISTRATION.json',reg)
    print(root,sha(root/'REGISTRATION.json'),ids,actor_checks)


def review(root):
    reg,state=read(root/'REGISTRATION.json'),read(root/'execution.json')
    assert state['status']=='complete_pending_review' and len(state['episodes'])==len(reg['cases'])==7
    assert state['registration_sha256']==sha(root/'REGISTRATION.json')
    for name,h in reg['source_sha256'].items():assert sha(ROOT/name)==h,name
    for name,h in reg['config_sha256'].items():assert sha(Path(name))==h,name
    before=read(Path(read(COLLECTION/'COLLECTION_PLAN.json')['teacher_config']))
    assert reg['parent_config_sha256']==sha(Path(read(COLLECTION/'COLLECTION_PLAN.json')['teacher_config']))
    expected=copy.deepcopy(before);expected['options']['damping_6d'][2]=220.
    assert read(Path(reg['cases'][0]['config']))==expected
    rows=[];old_energy=new_energy=0.
    for case,receipt in zip(reg['cases'],state['episodes']):
        assert case['id']==receipt['id'] and receipt['returncode']==0
        folder=root/case['id'];row=dict(id=case['id'],kind=case['kind'])
        if case['kind']=='scene':
            folder/=case['scene'];q=evidence(folder)
            assert q['qualification_sha256']==receipt['qualification_sha256']
            assert q['model_sha256']==case['expected_model_sha256']
            row.update(q)
            if case['scene']=='ball':
                pair={}
                for label,path in (('parent',Path(case['baseline'])),('candidate',folder)):
                    with np.load(path/'legacy.npz',allow_pickle=False) as z:
                        speed=np.linalg.norm(np.diff(z['object_position'],axis=0)/.04,axis=1)
                    pair[label]=dict(last9_speed_max_mps=float(speed[-9:].max()),
                        last250_speed_rms_mps=float(np.sqrt(np.mean(speed[-250:]**2))),
                        last250_speed_squared_sum=float(np.sum(speed[-250:]**2)),legacy_sha256=sha(path/'legacy.npz'))
                old_energy+=pair['parent']['last250_speed_squared_sum']
                new_energy+=pair['candidate']['last250_speed_squared_sum'];row['tail_pair']=pair
        else:
            audit=read(folder/'AUDIT.json');assert sha(folder/'AUDIT.json')==receipt['audit_sha256']
            for n,k in (('rollout.npz','trace_sha256'),('rollout.mjb','model_sha256'),
                        ('execution_chain.npz','chain_sha256'),('rollout_metrics/substep_metrics.npz','metrics_sha256')):
                assert sha(folder/n)==audit[k]
            assert audit['action_replay_max_abs']==audit['common_filter_replay_max_abs']==0. and audit['full_horizon']
            row.update(task=audit['task_success'],strict=audit['strict_success'],stage=audit['stage'],audit_sha256=sha(folder/'AUDIT.json'))
        rows.append(row)
    all_pass=all(r['status']=='qualified' if r['kind']=='scene' else r['task'] and r['strict'] for r in rows)
    result=dict(status='complete_seven_controls_review',rows=rows,all_seven_qualified=all_pass,
        parent_train_tail_energy=old_energy,candidate_train_tail_energy=new_energy,
        candidate_eligible=all_pass and new_energy<old_energy,registration_sha256=sha(root/'REGISTRATION.json'),
        execution_sha256=sha(root/'execution.json'),source_sha256=sha(Path(__file__)),
        limitation='Seven fixed development controls, including already inspected office. '
        'No validation tuning, full30/student success, passivity or unseen-generalization claim. All failures preserved.')
    assert not (root/'REVIEW.json').exists();write(root/'REVIEW.json',result)
    print('candidate_eligible',result['candidate_eligible'],'tail_energy',old_energy,new_energy)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True,type=Path)
    g=p.add_mutually_exclusive_group();g.add_argument('--run',action='store_true');g.add_argument('--review',action='store_true')
    a=p.parse_args()
    if a.run:
        require_originals_terminal();run_cases(a.root.resolve())
    elif a.review:review(a.root.resolve())
    else:prepare(a.root.resolve())
