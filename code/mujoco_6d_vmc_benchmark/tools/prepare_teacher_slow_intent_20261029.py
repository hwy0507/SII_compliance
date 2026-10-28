"""One finite low-speed intention-release control after damping review.

Keep the bounded recovery, damping, virtual dynamics and readout. Change only
the command normalization used by the existing memory-release term .015->.003.
The latter is below the observed few-mm/s stalled command, but positive so
zero-command release is unchanged. This is disclosed development tuning,
not unseen-test selection or a guarantee of physical improvement.
"""
import argparse
import copy
from pathlib import Path
import shutil

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now, run
from optimize_tool_contact_20261002 import ParameterTeacher
from review_special_teacher_midpoint_20261028 import inactive


def diagnose(parent, before, after):
    folder = parent/'damping_office000'
    receipt = read(folder/'AUDIT.json')
    assert sha(folder/'rollout.npz') == receipt['trace_sha256']
    assert sha(folder/'execution_chain.npz') == receipt['chain_sha256']
    old, new = ParameterTeacher(before), ParameterTeacher(after)
    terms, memories = [], []
    memory = 0.
    with np.load(folder/'rollout.npz', allow_pickle=False) as trace, np.load(folder/'execution_chain.npz', allow_pickle=False) as chain:
        for obs, expected in zip(trace['observation'], chain['requested_action']):
            for actor in (old,new): actor.observe(obs)
            action = old.act(obs[39:45]); candidate = new.act(obs[39:45])
            np.testing.assert_array_equal(action, expected)
            for name in ('offset','velocity','filtered','effective_wrench'):
                np.testing.assert_array_equal(getattr(old,name),getattr(new,name))
            np.testing.assert_array_equal(action[[0,1,2,4,5,6]],candidate[[0,1,2,4,5,6]])
            c=before['recovery']; path=obs[45:47]
            horizontal=min(1.,float(np.linalg.norm(path))); direction=path/max(float(np.linalg.norm(path)),1e-12)
            desired=float(obs[14:16]@direction); progress=float((obs[14:16]-obs[26:28])@direction)
            opposition=max(0.,-float(obs[39:41]@direction)-c['threshold_n'])
            evidence=float(np.clip(opposition,0,1))*float(np.clip((desired-progress)/.015,0,1))*horizontal**2
            rising=evidence/c['attack_s']; travel=max(0.,progress)/c['progress_distance_m']
            intent=float(np.clip(desired/.015,0,1))*horizontal**2
            releasing=(1-intent)/c['release_s']; total=rising+travel+releasing
            memory=np.exp(-.04*total)*memory+(1-np.exp(-.04*total))*rising/max(total,1e-12)
            np.testing.assert_allclose(memory,old.recovery_memory,atol=1e-14,rtol=0)
            terms.append([rising,travel,releasing,desired,progress,intent,old.recovery_memory])
            memories.append(new.recovery_memory)
    values=np.asarray(terms)
    # Synthetic rest and >=old-threshold motion must remain exactly unchanged.
    for desired in (0.,.03):
        a,b=ParameterTeacher(before),ParameterTeacher(after)
        a.recovery_memory=b.recovery_memory=.8
        for _ in range(250):
            obs=np.zeros(48);obs[45]=1.;obs[14]=desired;obs[26]=desired;obs[39]=-.8
            for actor in (a,b):actor.observe(obs)
            np.testing.assert_array_equal(a.act(obs[39:45]),b.act(obs[39:45]))
            assert a.recovery_memory==b.recovery_memory
    return dict(status='passed', replay_frames=len(values), original_actor_replay_max_abs=0.,
        independent_memory_atol=1e-14, unchanged_nonvertical_actions_and_virtual_states=True,
        zero_and_high_command_exact_steps=500,
        columns=['rise_per_s','travel_decay_per_s','intent_release_per_s','command_path_mps','actual_path_mps','intent','memory'],
        last250_mean=values[-250:].mean(0).tolist(),
        last250_release_exceeds_travel_fraction=float(np.mean(values[-250:,2]>values[-250:,1])),
        counterfactual_same_observation_last250_memory_mean=float(np.mean(memories[-250:])),
        inputs={name:sha(folder/name) for name in ('rollout.npz','execution_chain.npz','AUDIT.json')},
        interpretation='Disclosed inspected-office diagnosis; no fitting, contact oracle or new physics. Candidate replay is off-policy on the old trajectory, not a predicted physical outcome. Both virtual dynamics and rest/high-command release remain unchanged.')


def prepare(root):
    assert not root.exists()
    parent=ROOT/'outputs/special_teacher_damping_20261029_v1'
    reg,state,review=[read(parent/n) for n in ('REGISTRATION.json','execution.json','REVIEW.json')]
    inactive(reg['service'])
    assert state['status']=='complete_pending_review' and len(state['episodes'])==6
    assert review['execution_sha256']==sha(parent/'execution.json') and not review['all_six_qualified']
    assert sum(r.get('status')=='qualified' for r in review['rows'])==5
    before=read(Path(reg['cases'][0]['config']));after=copy.deepcopy(before)
    assert 'intent_velocity_mps' not in before['recovery']
    after['recovery']['intent_velocity_mps']=.003
    checks=diagnose(parent,before,after)
    root.mkdir(parents=True)
    write(root/'ACTOR_CHECKS.json',checks)
    teacher=root/'teacher_slow_intent.json';write(teacher,after)
    source=root/'source'
    shutil.copytree(parent/'source',source,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    copied={str(p.relative_to(parent/'source')):sha(p) for p in (parent/'source').rglob('*')
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    assert all(sha(source/n)==h for n,h in copied.items())
    write(root/'SOURCE_COPY_REVIEW.json',dict(parent=str(parent/'source'),files=copied,all_identical=True))
    cases=copy.deepcopy(reg['cases'])
    for case in cases:
        case.update(config=str(teacher),id='slow_intent_'+case.get('identity','office000'))
        if case['kind']=='office':case['command'][1]=str(source/'tools/legacy_teacher_office_driver_20261029.py')
    successor=copy.deepcopy(reg)
    successor.update(schema='sii-teacher-slow-intent-control-v1',registered_utc=now(),
        service='sii-special-teacher-slow-intent-v1-20261029.service',cases=cases,
        config_sha256={str(teacher):sha(teacher)},parent_review_sha256=sha(parent/'REVIEW.json'),
        parent_execution_sha256=sha(parent/'execution.json'),parent_config_sha256=sha(Path(reg['cases'][0]['config'])),
        interpretation=__doc__,changed_parameter=dict(relative_to='immediate damping parent',
            name='recovery.intent_velocity_mps',before=.015,after=.003),
        changes_from_immediate_parent=['Existing intention-release normalization .015 to .003 m/s only'],
        actor_checks_sha256=sha(root/'ACTOR_CHECKS.json'),source_copy_review_sha256=sha(root/'SOURCE_COPY_REVIEW.json'),
        diagnosis_sha256=sha(ROOT/'outputs/special_teacher_clearance_audit_20261029_v1/REVIEW.json'),
        selection_rule='One candidate fixed before physics; same five training identities and inspected office000, no sweep/validation tuning/automatic collection. All six original qualifications required before new30; all previous failures retained.')
    successor['source_sha256']={n:sha(ROOT/n) for n in reg['source_sha256'] if not n.startswith('outputs/')}
    successor['source_sha256']['tools/'+Path(__file__).name]=sha(Path(__file__))
    successor['source_sha256'].update({str(p.relative_to(ROOT)):sha(p) for p in source.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'})
    write(root/'REGISTRATION.json',successor)
    print(root,sha(root/'REGISTRATION.json'),checks)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--run',action='store_true')
    a=p.parse_args();(run if a.run else prepare)(a.root.resolve())
