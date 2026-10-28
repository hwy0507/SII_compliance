"""Original v6 teacher plus matched readout normalization, six finite controls.

The original velocity1/averaged teacher passed office but four v6 ball
identities failed. Test only normalization relative to that original config.
This restores the original recovery and its .015 default intent release,
not just one parameter relative to the immediately preceding intent version.
No test trajectory fitting or validation-based parameter selection.
"""
import argparse
import copy
import shutil
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import ROOT,read,sha,write
from diagnose_special_scene_regression_20261028 import now,run
from intent_recovery_teacher_20261029 import make_teacher
from review_special_teacher_midpoint_20261028 import inactive


def prepare(root):
    assert not root.exists()
    parent=ROOT/'outputs/special_teacher_full_velocity_20261029_v1'
    reg,state,review=[read(parent/n) for n in ('REGISTRATION.json','execution.json','REVIEW.json')]
    inactive(reg['service'])
    assert state['status']=='complete_pending_review' and len(state['episodes'])==6
    assert state['registration_sha256']==sha(parent/'REGISTRATION.json')
    assert review['execution_sha256']==sha(parent/'execution.json')
    assert not review['all_six_qualified'] and not review['rows'][-1]['task']
    assert sum(r.get('status')=='qualified' for r in review['rows'])==5
    v6=ROOT/'outputs/special_scene_vmc_collection_20261028_v6'
    plan=read(v6/'COLLECTION_PLAN.json')
    original=Path(plan['teacher_config'])
    assert sha(original)==plan['teacher_file_sha256']
    before=read(original);after=copy.deepcopy(before)
    assert before['velocity_weight']==1 and before['pair_average'] is True
    assert 'teacher_mechanism' not in before and 'options' not in before
    assert 'intent_velocity_mps' not in before['recovery']
    after['options']=dict(action_limit_6d=[.32,.32,.32,.6,.6,.6])
    assert {k:v for k,v in after.items() if k!='options'}==before
    old,new=make_teacher(before),make_teacher(after)
    rng=np.random.default_rng(2026102905);maximum=0.
    for _ in range(400):
        obs=rng.normal(0,.004,48);obs[45:48]=[1.,0.,0.]
        obs[14]=.02;obs[26]=.01;obs[39:45]=rng.normal(0,1,6)
        for actor in (old,new):actor.observe(obs)
        old.act(obs[39:45]);actual=new.act(obs[39:45])
        for name in ('velocity','offset','filtered','effective_wrench','recovery_memory'):
            np.testing.assert_array_equal(getattr(old,name),getattr(new,name))
        base=np.clip(new.R6@(new.velocity+new.offset_gain*new.offset)/new.action_limits,-1,1)
        expected=np.r_[np.clip(np.linalg.norm(base)/np.sqrt(6.),0,1),base]*new.channel_gain
        c=after['recovery'];activation=new.recovery_memory
        correction=np.clip(c['gain_per_s']*(c['offset_m']+obs[22])-obs[16],-c['velocity_mps'],c['velocity_mps'])
        expected[3]=(1-activation)*expected[3]+activation*correction/.32
        expected=np.clip(expected,-1,1)
        np.testing.assert_allclose(actual,expected,rtol=0,atol=1e-15)
        maximum=max(maximum,float(np.max(np.abs(actual-expected))))
    diagnosis=ROOT/'outputs/special_teacher_edge_persistence_20261029_v2/REVIEW.json'
    assert read(diagnosis)['status']=='complete' and len(read(diagnosis)['rows'])==5
    root.mkdir(parents=True)
    write(root/'ACTOR_CHECKS.json',dict(status='passed',same_history_steps=400,
        independent_readout_max_abs=maximum,reference_config_sha256=sha(original),
        unchanged='Original v6 dynamics, averaged wrench, recovery memory and all parameters except internal normalization',
        limitation='Same-history arithmetic only. Readout and derived slowdown change, no physics success or stability claim.'))
    teacher=root/'teacher_legacy_units.json';write(teacher,after)
    source=root/'source'
    shutil.copytree(parent/'source',source,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    original_files={str(p.relative_to(parent/'source')):sha(p) for p in (parent/'source').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    assert all(sha(source/n)==h for n,h in original_files.items())
    driver=ROOT/'tools/legacy_teacher_office_driver_20261029.py'
    shutil.copy2(driver,source/'tools'/driver.name)
    write(root/'SOURCE_COPY_REVIEW.json',dict(files=original_files,original_source=str(parent/'source'),
        added_driver_sha256=sha(driver),unchanged_original_files=True))
    cases=copy.deepcopy(reg['cases'])
    for case in cases:
        case.update(config=str(teacher),id='legacy_units_'+case.get('identity','office000'))
        if case['kind']=='office':case['command'][1]=str(source/'tools'/driver.name)
    successor=copy.deepcopy(reg)
    successor.update(schema='sii-teacher-legacy-normalization-control-v1',registered_utc=now(),
        service='sii-special-teacher-legacy-units-v1-20261029.service',cases=cases,
        teacher_mechanism='legacy_parameter_teacher_v1',
        config_sha256={str(teacher):sha(teacher)},parent_review_sha256=sha(parent/'REVIEW.json'),
        parent_execution_sha256=sha(parent/'execution.json'),interpretation=__doc__,
        reference_v6_config=str(original),reference_v6_config_sha256=sha(original),
        changed_parameter=dict(relative_to='original v6 teacher',name='options.action_limit_6d',before=[.16,.16,.20,.6,.6,.6],after=after['options']['action_limit_6d']),
        changes_from_immediate_parent=['Remove intent-scaled equilibrium mechanism','Restore original implicit .015 memory-release intent threshold'],
        actor_checks_sha256=sha(root/'ACTOR_CHECKS.json'),source_copy_review_sha256=sha(root/'SOURCE_COPY_REVIEW.json'),
        diagnosis_sha256=sha(diagnosis),
        selection_rule='One original-teacher normalization candidate; original five training identities plus inspected office000. Require all six original qualifications before new30; no sweep, validation tuning, automatic collection or fitting. Preserve all failures.')
    successor['source_sha256']={n:sha(ROOT/n) for n in reg['source_sha256'] if not n.startswith('outputs/')}
    for name in (Path(__file__).name,driver.name,'review_legacy_units_controls_20261029.py','audit_teacher_edge_persistence_20261029.py'):
        successor['source_sha256']['tools/'+name]=sha(ROOT/'tools'/name)
    successor['source_sha256'].update({str(p.relative_to(ROOT)):sha(p) for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'})
    write(root/'REGISTRATION.json',successor)
    print(root,sha(root/'REGISTRATION.json'),maximum)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--run',action='store_true')
    a=p.parse_args();(run if a.run else prepare)(a.root.resolve())
