"""One finite faster-release follow-up after the complete .25s failure.

Only recovery.release_s changes, .25 -> .05 seconds. In the existing exact
exponential update this accelerates decay only when nominal intent is below
one. Five identical training controls plus the same disclosed office regression;
no new collection, labels, fitting, physics/gate change, or validation tuning.
"""
import argparse
import copy
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now, run
from review_special_teacher_midpoint_20261028 import inactive


def prepare(root):
    assert not root.exists()
    parent=ROOT/'outputs/special_recovery_release_20261028_v1'
    inactive('sii-special-recovery-release-v1-20261028.service')
    reg,state=read(parent/'REGISTRATION.json'),read(parent/'execution.json')
    assert state['status']=='complete_pending_review'
    assert state['registration_sha256']==sha(parent/'REGISTRATION.json')
    assert len(state['episodes'])==reg['maximum_episodes']==6
    reviews=[]
    for case,row in zip(reg['cases'],state['episodes']):
        assert case['id']==row['id'] and row['returncode']==0
        folder=parent/case['id']
        if case['kind']=='scene':
            folder/=case['scene'];q=read(folder/'DEMONSTRATION_QUALIFICATION.json')
            assert sha(folder/'DEMONSTRATION_QUALIFICATION.json')==row['qualification_sha256']
            for name,digest in q['input_hashes'].items():assert sha(folder/name)==digest
            assert q['status']=='qualified'
            reviews.append(dict(id=case['id'],status=q['status'],qualification_sha256=row['qualification_sha256']))
        else:
            a=read(folder/'AUDIT.json')
            assert sha(folder/'AUDIT.json')==row['audit_sha256']
            assert not a['task_success'] and a['stage']=='carry' and a['full_horizon']
            assert a['action_replay_max_abs']==a['common_filter_replay_max_abs']==0
            assert sha(folder/'rollout.npz')==a['trace_sha256']
            with np.load(folder/'rollout.npz',allow_pickle=False) as z, np.load(folder/'teacher_internal.npz',allow_pickle=False) as t:
                assert np.all(z['stage'][-250:]==4)
                reviews.append(dict(id=case['id'],task=False,strict=a['strict_success'],audit_sha256=row['audit_sha256'],
                    last250_pose_error_mean=z['observation'][-250:,20:26].mean(0).tolist(),
                    last250_recovery_memory_mean=float(t['recovery_memory'][-250:].mean()),
                    trace_sha256=a['trace_sha256'],teacher_internal_sha256=sha(folder/'teacher_internal.npz')))
    teacher=read(Path(reg['cases'][0]['config']))
    assert teacher['recovery']['release_s']==.25
    teacher['recovery']['release_s']=.05
    root.mkdir(parents=True)
    write(root/'PARENT_COMPLETE_REVIEW.json',dict(reviewed_utc=now(),rows=reviews,
        parent_execution_sha256=sha(parent/'execution.json'),
        conclusion='All five training controls remain qualified, office still fails. Actual closed-loop recovery memory grew despite smaller same-history counterfactual, falsifying the earlier sufficiency hypothesis. Do not dispatch full30 or train.'))
    path=root/'teacher_release005.json';write(path,teacher)
    successor=copy.deepcopy(reg)
    cases=copy.deepcopy(reg['cases'])
    for case in cases:
        case.update(id=('release005_'+case['identity'] if case['kind']=='scene' else 'office_release005'),config=str(path))
    successor.update(schema='sii-finite-fast-recovery-release-control-v1',registered_utc=now(),
        parent=str(parent),parent_review_sha256=sha(root/'PARENT_COMPLETE_REVIEW.json'),
        parent_execution_sha256=sha(parent/'execution.json'),cases=cases,
        config_sha256={str(path):sha(path)},changed_parameter=dict(name='recovery.release_s',before=.25,after=.05),
        interpretation=__doc__,selection_rule='Single candidate and six fixed controls. All original training qualifications plus original office Task/Strict required; otherwise retain failures and diagnose. No automatic collection or training.',
        next_step='Review every completed receipt and the actual recovery history. New30 must be separately registered only after full six-case review.')
    successor['source_sha256']={name:sha(ROOT/name) for name in reg['source_sha256']}
    successor['source_sha256'][str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    write(root/'REGISTRATION.json',successor)
    print(root,sha(root/'REGISTRATION.json'))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--run',action='store_true')
    a=p.parse_args()
    (run if a.run else prepare)(a.root.resolve())
