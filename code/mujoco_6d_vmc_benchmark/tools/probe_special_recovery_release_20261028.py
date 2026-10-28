"""Single-field recovery release repair after diagnosed terminal offset.

Retain the training-eligible .75/averaged readout. Change release_s only from
1.257675717389726 to .25 seconds in the existing progress-memory equation.
Its decay is progress/distance + (1-intent)/release_s: when intent=1 this
change has no effect on the update. This is a hypothesis about near-goal
residual recovery, not a stability proof. Five fixed training identities plus
one disclosed, previously inspected office regression; no validation tuning,
new actor input, changed physics or gate, or automatic fitting.
"""
import argparse
import copy
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, validate, write
from diagnose_special_scene_regression_20261028 import now, run
from review_special_teacher_midpoint_20261028 import inactive


def prepare(root):
    assert not root.exists()
    midpoint=ROOT/'outputs/special_teacher_midpoint_20261028_v1'
    office=ROOT/'outputs/special_teacher_midpoint_office_20261028_v1'
    inactive('sii-special-teacher-midpoint-office-v1-20261028.service')
    state, office_reg=read(office/'execution.json'),read(office/'REGISTRATION.json')
    assert state['status']=='complete_pending_review' and len(state['episodes'])==1
    assert state['registration_sha256']==sha(office/'REGISTRATION.json')
    row=state['episodes'][0];folder=office/row['id'];audit=read(folder/'AUDIT.json')
    assert sha(folder/'AUDIT.json')==row['audit_sha256']
    assert not audit['task_success'] and audit['stage']=='carry' and audit['full_horizon']
    assert audit['action_replay_max_abs']==audit['common_filter_replay_max_abs']==0
    assert sha(folder/'rollout.npz')==audit['trace_sha256']
    with np.load(folder/'rollout.npz',allow_pickle=False) as z, np.load(folder/'teacher_internal.npz',allow_pickle=False) as t:
        # Use the last250 sampled frames, avoiding floating-point inclusion
        # of the 45.000000... boundary as an accidental 251st sample.
        keep=np.arange(len(z['time']))>=len(z['time'])-250
        assert keep.sum()==250 and np.all(z['stage'][keep]==4)
        np.testing.assert_allclose(np.diff(z['time'][keep]),.04,rtol=0,atol=1e-8)
        o=z['observation'][keep];path=o[:,45:47]
        horizontal=np.minimum(1,np.linalg.norm(path,axis=1))
        direction=path/np.maximum(np.linalg.norm(path,axis=1)[:,None],1e-12)
        desired=np.sum(o[:,14:16]*direction,axis=1)
        intent=np.clip(desired/.015,0,1)*horizontal**2
        diagnosis=dict(source=str(folder),audit_sha256=sha(folder/'AUDIT.json'),
            trace_sha256=sha(folder/'rollout.npz'),teacher_internal_sha256=sha(folder/'teacher_internal.npz'),
            frames=int(keep.sum()),position_error_quantiles_m=np.quantile(z['task_position_error_m'][keep],[0,.5,1]).tolist(),
            signed_pose_error_mean=o[:,20:26].mean(0).tolist(),
            recovery_memory_quantiles=np.quantile(t['recovery_memory'][keep],[0,.5,.9,1]).tolist(),
            intent_quantiles=np.quantile(intent,[0,.5,.9,1]).tolist(),
            gates=dict(position_m=.012,rotation_rad=.12,speed_mps=.025,hold_s=.20),
            interpretation='Persistent recovery contributes a positive z action while near the nominal target; observed negative z pose error exceeds original position gate. Single-field physical control needed for causal conclusion.')
        diagnosis['preparation_failure_preserved']='First preparation expected250 frames from absolute time>=45, but floating-point boundary included251; assertion stopped before output/registration/physics. Corrected to the actual final250 frames and verified .04s spacing. No physical data or gate changed.'
    original=read(midpoint/'REGISTRATION.json')
    review=read(midpoint/'REVIEW.json')
    assert review['selected']=='v075_avg1'
    config=read(midpoint/'v075_avg1.json')
    assert config['recovery']['activation_mode']=='progress'
    before=copy.deepcopy(config)
    assert config['recovery']['release_s']==1.257675717389726
    config['recovery']['release_s']=.25
    root.mkdir(parents=True)
    write(root/'DIAGNOSIS.json',diagnosis)
    teacher=root/'teacher_release025.json';write(teacher,config)
    cases=[copy.deepcopy(c) for c in original['cases'] if c['id'].startswith('v075_avg1_')]
    assert len(cases)==5
    for c in cases:
        c.update(id='release025_'+c['identity'],config=str(teacher))
    office_case=copy.deepcopy(office_reg['cases'][0])
    office_case.update(id='office_release025',config=str(teacher))
    cases.append(office_case)
    reg=copy.deepcopy(original)
    reg.update(schema='sii-single-recovery-release-control-v1',registered_utc=now(),
        midpoint_review_sha256=sha(midpoint/'REVIEW.json'),failed_office=str(office),
        failed_office_execution_sha256=sha(office/'execution.json'),diagnosis_sha256=sha(root/'DIAGNOSIS.json'),
        cases=cases,maximum_episodes=6,config_sha256={str(teacher):sha(teacher)},
        changed_parameter=dict(name='recovery.release_s',before=before['recovery']['release_s'],after=.25),
        selection_rule='Single candidate. All five training identities must qualify and the previously inspected office regression must pass original Task/Strict before new30. Otherwise preserve failures and inspect; no automatic collection or training.',
        interpretation=__doc__,next_step='Review all six original task/safety/contact receipts and near-goal recovery before any new collection.')
    reg['source_sha256']={name:sha(ROOT/name) for name in original['source_sha256']}
    reg['source_sha256'][str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    write(root/'REGISTRATION.json',reg)
    print(root,sha(root/'REGISTRATION.json'),len(cases))


def recollect(root,output):
    assert not output.exists()
    inactive('sii-special-recovery-release-v1-20261028.service')
    reg,state=read(root/'REGISTRATION.json'),read(root/'execution.json')
    assert state['status']=='complete_pending_review' and len(state['episodes'])==reg['maximum_episodes']==6
    assert state['registration_sha256']==sha(root/'REGISTRATION.json')
    for case,row in zip(reg['cases'],state['episodes']):
        assert case['id']==row['id'] and row['returncode']==0
        folder=root/case['id']
        if case['kind']=='scene':
            folder/=case['scene'];q=read(folder/'DEMONSTRATION_QUALIFICATION.json')
            assert sha(folder/'DEMONSTRATION_QUALIFICATION.json')==row['qualification_sha256']
            for name,digest in q['input_hashes'].items():assert sha(folder/name)==digest
            assert q['status']=='qualified','Training control still fails: '+case['id']
        else:
            assert sha(folder/'AUDIT.json')==row['audit_sha256']
            audit=read(folder/'AUDIT.json')
            for name,key in [('rollout.npz','trace_sha256'),('rollout.mjb','model_sha256'),('execution_chain.npz','chain_sha256'),('rollout_metrics/substep_metrics.npz','metrics_sha256')]:
                assert sha(folder/name)==audit[key]
            assert audit['task_success'] and audit['strict_success'],'Original office regression still fails'
    previous=Path(reg['collection']);plan=validate(previous/'COLLECTION_PLAN.json')
    teacher=Path(reg['cases'][0]['config'])
    assert sha(teacher)==reg['config_sha256'][str(teacher)]
    successor=copy.deepcopy(plan)
    successor.update(registered_utc=now(),teacher_config=str(teacher),teacher_file_sha256=sha(teacher),teacher_config_sha256=sha(teacher),
        development_references={scene:dict(folder=str(root/('release025_'+scene+'_00')/scene),qualification_sha256=sha(root/('release025_'+scene+'_00')/scene/'DEMONSTRATION_QUALIFICATION.json')) for scene in ('rod','ball','corner')},
        supersedes=dict(previous_plan=str(previous/'COLLECTION_PLAN.json'),previous_plan_sha256=sha(previous/'COLLECTION_PLAN.json'),
                        repair_registration_sha256=sha(root/'REGISTRATION.json'),repair_execution_sha256=sha(root/'execution.json'),
                        rationale='Uniform .32 interface, .75 averaged teacher readout and single-field near-goal recovery release repair. Same30 identities/seeds/splits/physics/gates. Previously inspected office regression disclosed, never training labels.'))
    successor['source_sha256']={name:sha(ROOT/name) for name in plan['source_sha256']}
    successor['source_sha256'][str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    for old,new in zip(plan['episodes'],successor['episodes']):
        new['folder']=str(output/new['id']/new['scene'])
        assert {k:v for k,v in old.items() if k!='folder'}=={k:v for k,v in new.items() if k!='folder'}
    output.mkdir(parents=True)
    write(output/'COLLECTION_PLAN.json',successor)
    validate(output/'COLLECTION_PLAN.json')
    print(output,sha(output/'COLLECTION_PLAN.json'))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--run',action='store_true')
    p.add_argument('--collection-output',type=Path)
    a=p.parse_args()
    if a.run:run(a.root.resolve())
    elif a.collection_output:recollect(a.root.resolve(),a.collection_output.resolve())
    else:prepare(a.root.resolve())
