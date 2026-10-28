"""One bounded +8mm equilibrium-offset control, not a scene/gate change.

The slow-intent teacher remains 2--4mm below the edge in inspected office000.
At its ~.8 recovery activation an 8mm reference-relative offset increment is
a finite clearance hypothesis, not a predicted displacement or stability proof.
Keep the five training controls and office regression; never fit office labels.
"""
import argparse
import copy
from pathlib import Path
import shutil

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now, run
from optimize_tool_contact_20261002 import ParameterTeacher
from review_legacy_units_controls_20261029 import review
from review_special_teacher_midpoint_20261028 import inactive

PARENT = ROOT/'outputs/special_teacher_slow_intent_20261029_v1'
DELTA = .008
SCHEMA = 'sii-teacher-clearance-offset-control-v1'


def check_actions(before, after):
    folder = PARENT/'slow_intent_office000'
    audit = read(folder/'AUDIT.json')
    assert sha(folder/'rollout.npz') == audit['trace_sha256']
    assert sha(folder/'execution_chain.npz') == audit['chain_sha256']
    old, new = ParameterTeacher(before), ParameterTeacher(after)
    errors, increments = [], []
    with np.load(folder/'rollout.npz', allow_pickle=False) as trace, np.load(folder/'execution_chain.npz', allow_pickle=False) as chain:
        for obs, expected in zip(trace['observation'], chain['requested_action']):
            for actor in (old, new):
                actor.observe(obs)
            a, b = old.act(obs[39:45]), new.act(obs[39:45])
            np.testing.assert_array_equal(a, expected)
            for key in ('offset', 'velocity', 'filtered', 'effective_wrench', 'recovery_memory'):
                np.testing.assert_array_equal(getattr(old, key), getattr(new, key))
            np.testing.assert_array_equal(a[[0,1,2,4,5,6]], b[[0,1,2,4,5,6]])
            c = before['recovery']
            activation = old.recovery_memory * min(1., float(np.linalg.norm(obs[45:47])))**2
            u0 = np.clip(c['gain_per_s']*(c['offset_m']+obs[22])-obs[16], -c['velocity_mps'], c['velocity_mps'])
            u1 = np.clip(c['gain_per_s']*(c['offset_m']+DELTA+obs[22])-obs[16], -c['velocity_mps'], c['velocity_mps'])
            # In this recorded trace the old final z is strictly unsaturated.
            assert abs(a[3]) < 1.
            predicted = np.clip(a[3] + activation*(u1-u0)/.32, -1., 1.)
            errors.append(abs(predicted-b[3])); increments.append(b[3]-a[3])
    assert max(errors) < 1e-14
    return dict(status='passed', frames=len(errors), original_actor_replay_max_abs=0.,
        independent_delta_max_abs=max(errors), virtual_states_and_memory_unchanged=True,
        nonvertical_actions_identical=True, last250_z_action_increment_mean=float(np.mean(increments[-250:])),
        maximum_added_target_velocity_mps=before['recovery']['gain_per_s']*DELTA,
        inputs={n:sha(folder/n) for n in ('AUDIT.json','rollout.npz','execution_chain.npz')},
        limitation='Same old observations, off-policy arithmetic only; no predicted physics or passivity guarantee.')


def prepare(root):
    assert not root.exists()
    reg, state, result = [read(PARENT/n) for n in ('REGISTRATION.json','execution.json','REVIEW.json')]
    inactive(reg['service'])
    assert state['status']=='complete_pending_review' and len(state['episodes'])==6
    assert result['execution_sha256']==sha(PARENT/'execution.json') and not result['all_six_qualified']
    assert sum(r.get('status')=='qualified' for r in result['rows'])==5
    before=read(Path(reg['cases'][0]['config'])); after=copy.deepcopy(before)
    after['recovery']['offset_m'] += DELTA
    checks=check_actions(before,after)
    root.mkdir(parents=True)
    write(root/'ACTOR_CHECKS.json', checks)
    config=root/'teacher_clearance_offset.json'; write(config,after)
    source=root/'source'
    shutil.copytree(PARENT/'source',source,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    copied={str(p.relative_to(PARENT/'source')):sha(p) for p in (PARENT/'source').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    assert all(sha(source/n)==h for n,h in copied.items())
    write(root/'SOURCE_COPY_REVIEW.json',dict(parent=str(PARENT/'source'),files=copied,all_identical=True))
    cases=copy.deepcopy(reg['cases'])
    for case in cases:
        case.update(config=str(config),id='clearance_offset_'+case.get('identity','office000'))
        if case['kind']=='office': case['command'][1]=str(source/'tools/legacy_teacher_office_driver_20261029.py')
    successor=copy.deepcopy(reg)
    successor.update(schema=SCHEMA,registered_utc=now(),service='sii-special-teacher-clearance-offset-v1-20261029.service',cases=cases,
        config_sha256={str(config):sha(config)}, parent_review_sha256=sha(PARENT/'REVIEW.json'),
        parent_execution_sha256=sha(PARENT/'execution.json'),parent_config_sha256=sha(Path(reg['cases'][0]['config'])),
        interpretation=__doc__, changed_parameter=dict(name='recovery.offset_m',before=before['recovery']['offset_m'],after=after['recovery']['offset_m']),
        changes_from_immediate_parent=['Existing reference-relative recovery offset +.008m only'],
        actor_checks_sha256=sha(root/'ACTOR_CHECKS.json'),source_copy_review_sha256=sha(root/'SOURCE_COPY_REVIEW.json'),
        diagnosis_sha256=sha(ROOT/'outputs/special_teacher_clearance_audit_20261029_v2/REVIEW.json'))
    successor['source_sha256']={n:sha(ROOT/n) for n in reg['source_sha256'] if not n.startswith('outputs/')}
    successor['source_sha256']['tools/'+Path(__file__).name]=sha(Path(__file__))
    successor['source_sha256'].update({str(p.relative_to(ROOT)):sha(p) for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'})
    write(root/'REGISTRATION.json',successor)
    print(root,sha(root/'REGISTRATION.json'),checks)


def checked_review(root):
    reg=read(root/'REGISTRATION.json'); assert reg['schema']==SCHEMA
    parent_reg=read(PARENT/'REGISTRATION.json'); before_path=Path(parent_reg['cases'][0]['config'])
    assert sha(before_path)==reg['parent_config_sha256']
    expected=read(before_path); expected['recovery']['offset_m']+=DELTA
    assert len({c['config'] for c in reg['cases']})==1
    assert read(Path(reg['cases'][0]['config']))==expected
    result=review(root)
    print('all_six_qualified',result['all_six_qualified'])
    for row in result['rows']: print({k:v for k,v in row.items() if k!='rod_audit'})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    g=p.add_mutually_exclusive_group();g.add_argument('--run',action='store_true');g.add_argument('--review',action='store_true')
    a=p.parse_args();(run if a.run else checked_review if a.review else prepare)(a.root.resolve())
