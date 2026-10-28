"""Finite teacher-readout normalization control, common filter unchanged.

Keep intent030 equilibrium teacher and all dynamics/recovery parameters.
Only set internal action normalization denominators to the common filter
scales (.32 linear/.6 angular). These denominators are controller readout
gains, not the physical actuator or virtual velocity saturation limits.
The original 2/2/1.6 component gains may be historical tuning; this is a
causal control, not an unproven declaration of a unit-conversion bug.
"""
import argparse
import copy
import shutil
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now, run
from intent_recovery_teacher_20261029 import make_teacher, LegacyParameterTeacher
from review_special_teacher_midpoint_20261028 import inactive


def check(before, after):
    previous, current = make_teacher(before), make_teacher(after)
    rng = np.random.default_rng(2026102903)
    original_limits = previous.action_limits.copy()
    assert np.array_equal(original_limits,[.16,.16,.20,.60,.60,.60])
    for _ in range(400):
        obs = rng.normal(0,.004,48)
        obs[45:48] = [1.,0.,0.]
        obs[14],obs[26] = .02,.01
        obs[39:45] = rng.normal(0,1,6)
        for actor in (previous,current): actor.observe(obs)
        previous.act(obs[39:45]); actual = current.act(obs[39:45])
        for name in ('velocity','offset','filtered','effective_wrench','recovery_memory'):
            np.testing.assert_array_equal(getattr(previous,name),getattr(current,name))
        assert np.isfinite(actual).all() and np.max(np.abs(actual)) <= 1.
    base_cfg = copy.deepcopy(after)
    base_cfg.pop('teacher_mechanism');base_cfg.pop('recovery')
    base = LegacyParameterTeacher(base_cfg)
    max_error = 0.
    for _ in range(400):
        wrench = rng.normal(0,.3,6)
        action = base.act(wrench)
        residual = base.R6@(base.velocity_weight*base.velocity+base.offset_gain*base.offset)
        assert np.max(np.abs(residual/base.action_limits)) < 1.
        physical_request = action[1:]*np.array([.32,.32,.32,.6,.6,.6])
        max_error = max(max_error,float(np.max(np.abs(physical_request-residual))))
        np.testing.assert_allclose(physical_request,residual,rtol=0,atol=1e-15)
    return dict(status='passed', same_history_dynamics_memory_steps=400,
        unsaturated_physical_request_arithmetic_steps=400,max_conversion_error=max_error,
        before_gain=(np.array([.32,.32,.32,.6,.6,.6])/original_limits).tolist(),
        after_gain=[1.]*6,
        caveat='Readout gains and derived slowdown can change; common filter can still rate/norm-limit the request. No claim of exact physical end-effector tracking or stability.')


def prepare(root):
    assert not root.exists()
    parent = ROOT/'outputs/special_equilibrium_intent030_20261029_v1'
    inactive('sii-special-equilibrium-intent030-v1-20261029.service')
    reg,state,review = [read(parent/name) for name in ('REGISTRATION.json','execution.json','REVIEW.json')]
    assert state['status']=='complete_pending_review' and len(state['episodes'])==6
    assert state['registration_sha256']==sha(parent/'REGISTRATION.json')
    assert review['execution_sha256']==sha(parent/'execution.json') and not review['all_six_qualified']
    before=read(Path(reg['cases'][0]['config']));after=copy.deepcopy(before)
    assert 'action_limit_6d' not in after.get('options',{})
    after.setdefault('options',{})['action_limit_6d']=[.32,.32,.32,.6,.6,.6]
    checked=check(before,after)
    diagnosis=ROOT/'outputs/special_teacher_feedback_diagnosis_20261029_v1/DIAGNOSIS.json'
    assert len(read(diagnosis)['rows'])==9
    root.mkdir(parents=True)
    write(root/'ACTOR_CHECKS.json',checked)
    teacher=root/'teacher_velocity_units.json';write(teacher,after)
    source=root/'source'
    shutil.copytree(parent/'source',source,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    originals={str(p.relative_to(parent/'source')):sha(p) for p in (parent/'source').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    assert all(sha(source/name)==digest for name,digest in originals.items())
    write(root/'SOURCE_COPY_REVIEW.json',dict(files=originals,original_source=str(parent/'source')))
    cases=copy.deepcopy(reg['cases'])
    for case in cases:
        case.update(config=str(teacher),id='velocity_units_'+case.get('identity','office000'))
        if case['kind']=='office':case['command'][1]=str(source/'tools/intent_equilibrium_office_driver_20261029.py')
    successor=copy.deepcopy(reg)
    successor.update(schema='sii-teacher-velocity-unit-control-v1',registered_utc=now(),
        service='sii-special-teacher-velocity-units-v1-20261029.service',cases=cases,
        config_sha256={str(teacher):sha(teacher)},parent_review_sha256=sha(parent/'REVIEW.json'),
        parent_execution_sha256=sha(parent/'execution.json'),interpretation=__doc__,
        changed_parameter=dict(name='options.action_limit_6d',before=[.16,.16,.20,.6,.6,.6],after=after['options']['action_limit_6d']),
        actor_checks_sha256=sha(root/'ACTOR_CHECKS.json'),source_copy_review_sha256=sha(root/'SOURCE_COPY_REVIEW.json'),
        diagnosis_sha256=sha(diagnosis),
        selection_rule='One candidate; same five train identities and already inspected office000. All six original gates required before new30. No validation tuning, automatic collection or fitting; retain all failures.')
    successor['source_sha256']={name:sha(ROOT/name) for name in reg['source_sha256'] if not name.startswith('outputs/')}
    for name in (Path(__file__).name,'analyze_special_teacher_feedback_20261029.py'):
        successor['source_sha256']['tools/'+name]=sha(ROOT/'tools'/name)
    successor['source_sha256'].update({str(p.relative_to(ROOT)):sha(p) for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'})
    write(root/'REGISTRATION.json',successor)
    print(root,sha(root/'REGISTRATION.json'),checked)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--run',action='store_true')
    a=p.parse_args();(run if a.run else prepare)(a.root.resolve())
