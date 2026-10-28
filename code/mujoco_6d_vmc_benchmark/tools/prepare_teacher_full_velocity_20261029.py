"""One finite restoration of the original virtual-velocity readout weight.

Keep matched normalization, input averaging and intent equilibrium unchanged.
Earlier matched historical controls succeeded with velocity weight1 while
the reduced .75 readout failed office000. Test this one existing value after
the normalization control; do not introduce a sweep, new gate or new data.
"""
import argparse
import copy
import shutil
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now, run
from intent_recovery_teacher_20261029 import make_teacher
from review_special_teacher_midpoint_20261028 import inactive


def prepare(root):
    assert not root.exists()
    parent=ROOT/'outputs/special_teacher_velocity_units_20261029_v1'
    reg,state,review=[read(parent/n) for n in ('REGISTRATION.json','execution.json','REVIEW.json')]
    inactive(reg['service'])
    assert state['status']=='complete_pending_review' and len(state['episodes'])==6
    assert state['registration_sha256']==sha(parent/'REGISTRATION.json')
    assert review['execution_sha256']==sha(parent/'execution.json')
    assert len([r for r in review['rows'] if r.get('status')=='qualified'])==5
    assert not review['all_six_qualified'] and not review['rows'][-1]['task']
    diagnosis=ROOT/'outputs/special_velocity_units_comparison_20261029_v1/REVIEW.json'
    assert read(diagnosis)['status']=='complete'
    before=read(Path(reg['cases'][0]['config']));after=copy.deepcopy(before)
    assert before['velocity_weight']==.75 and before['pair_average'] is True
    assert before['options']['action_limit_6d']==[.32,.32,.32,.6,.6,.6]
    after['velocity_weight']=1.
    old,new=make_teacher(before),make_teacher(after)
    rng=np.random.default_rng(2026102904)
    maximum=0.
    for _ in range(400):
        obs=rng.normal(0,.004,48);obs[45:48]=[1.,0.,0.]
        obs[14]=.02;obs[26]=.01;obs[39:45]=rng.normal(0,1,6)
        for actor in (old,new):actor.observe(obs)
        old.act(obs[39:45]);action=new.act(obs[39:45])
        for name in ('velocity','offset','filtered','effective_wrench','recovery_memory'):
            np.testing.assert_array_equal(getattr(old,name),getattr(new,name))
        base=np.clip(new.R6@(new.velocity+new.offset_gain*new.offset)/new.action_limits,-1,1)
        expected=base*new.channel_gain[1:]
        indices=np.array([0,1,3,4,5])
        maximum=max(maximum,float(np.max(np.abs(action[1:][indices]-expected[indices]))))
        np.testing.assert_allclose(action[1:][indices],expected[indices],rtol=0,atol=1e-15)
        assert np.isfinite(action).all() and np.abs(action).max()<=1.
    root.mkdir(parents=True)
    write(root/'ACTOR_CHECKS.json',dict(status='passed',same_history_steps=400,
        unchanged='Virtual dynamics, filtered wrench and recovery memory',
        non_recovery_channel_readout_max_abs=maximum,
        limitation='Same-history arithmetic only. Velocity and derived slowdown change; no physical stability or success claim.'))
    teacher=root/'teacher_full_velocity.json';write(teacher,after)
    source=root/'source'
    shutil.copytree(parent/'source',source,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    original={str(p.relative_to(parent/'source')):sha(p) for p in (parent/'source').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    assert all(sha(source/n)==h for n,h in original.items())
    write(root/'SOURCE_COPY_REVIEW.json',dict(files=original,original_source=str(parent/'source')))
    cases=copy.deepcopy(reg['cases'])
    for case in cases:
        case.update(config=str(teacher),id='full_velocity_'+case.get('identity','office000'))
        if case['kind']=='office':case['command'][1]=str(source/'tools/intent_equilibrium_office_driver_20261029.py')
    successor=copy.deepcopy(reg)
    successor.update(schema='sii-teacher-full-velocity-control-v1',registered_utc=now(),
        service='sii-special-teacher-full-velocity-v1-20261029.service',cases=cases,
        config_sha256={str(teacher):sha(teacher)},parent_review_sha256=sha(parent/'REVIEW.json'),
        parent_execution_sha256=sha(parent/'execution.json'),interpretation=__doc__,
        changed_parameter=dict(name='velocity_weight',before=.75,after=1.),
        actor_checks_sha256=sha(root/'ACTOR_CHECKS.json'),source_copy_review_sha256=sha(root/'SOURCE_COPY_REVIEW.json'),
        diagnosis_sha256=sha(diagnosis),
        selection_rule='One restoration candidate, original five training identities plus inspected office000 regression. All six original qualifications required before new30. No validation tuning, automatic collection, fitting or parameter sweep; retain all failures.')
    successor['source_sha256']={n:sha(ROOT/n) for n in reg['source_sha256'] if not n.startswith('outputs/')}
    for name in (Path(__file__).name,'review_teacher_velocity_units_20261029.py'):
        successor['source_sha256']['tools/'+name]=sha(ROOT/'tools'/name)
    successor['source_sha256'].update({str(p.relative_to(ROOT)):sha(p) for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'})
    write(root/'REGISTRATION.json',successor)
    print(root,sha(root/'REGISTRATION.json'),maximum)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--run',action='store_true')
    args=parser.parse_args();(run if args.run else prepare)(args.root.resolve())
