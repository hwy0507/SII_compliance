"""Review all ten midpoint training controls before a separate office regression.

The selection priority is in the pre-existing registration. Previously seen
office000 is a disclosed regression check, never unseen or imitation data.
No automatic fitting; preserve every original condition and failed receipt.
"""
import argparse
import copy
from pathlib import Path
import subprocess

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, validate, write
from diagnose_special_scene_regression_20261028 import now, run


def inactive(service):
    properties = dict(line.split('=', 1) for line in subprocess.check_output(
        ['systemctl', '--user', 'show', service, '-p', 'MainPID', '-p', 'ActiveState'], text=True).splitlines())
    assert properties == dict(MainPID='0', ActiveState='inactive'), properties


def review(root):
    reg, state = read(root/'REGISTRATION.json'), read(root/'execution.json')
    inactive('sii-special-teacher-midpoint-v1-20261028.service')
    assert state['status'] == 'complete_pending_review'
    assert state['registration_sha256'] == sha(root/'REGISTRATION.json')
    assert len(state['episodes']) == len(reg['cases']) == reg['maximum_episodes'] == 10
    rows = []
    for case, result in zip(reg['cases'], state['episodes']):
        assert case['id'] == result['id'] and result['returncode'] == 0
        folder = root/case['id']/case['scene']
        q = read(folder/'DEMONSTRATION_QUALIFICATION.json')
        assert sha(folder/'DEMONSTRATION_QUALIFICATION.json') == result['qualification_sha256']
        for name, digest in q['input_hashes'].items():
            assert sha(folder/name) == digest
        assert q['input_hashes']['scene.mjb'] == case['expected_model_sha256']
        row = dict(id=case['id'], identity=case['identity'], config=case['config'],
                   task=q['task_success'], safety=q['safety_valid'], contact=q['scene_contact_valid'],
                   status=q['status'], qualification_sha256=result['qualification_sha256'])
        if case['scene'] == 'ball':
            with np.load(folder/'legacy.npz', allow_pickle=False) as z:
                row['tail_object_speed_max_mps'] = float(np.max(np.linalg.norm(np.diff(z['object_position'][-10:], axis=0)/.04, axis=1)))
            row['original_motion_threshold_mps'] = .02
            row['legacy_npz_sha256'] = sha(folder/'legacy.npz')
        elif case['scene'] == 'rod':
            row['rod_audit'] = read(folder/'ROD_YIELD_REJOIN_AUDIT_V3.json')
        rows.append(row)
    eligibility = {label:all(r['status']=='qualified' for r in rows if r['id'].startswith(label+'_'))
                   for label in ('v075_avg0', 'v075_avg1')}
    assert all(sum(r['id'].startswith(label+'_') for r in rows)==5 for label in eligibility)
    selected = next((k for k,v in eligibility.items() if v), None)
    result = dict(reviewed_utc=now(), registration_sha256=sha(root/'REGISTRATION.json'),
                  execution_sha256=sha(root/'execution.json'), rows=rows,
                  eligibility=eligibility, selected=selected,
                  selection_rule=reg['selection_rule'],
                  limitation='Five training identities per setting only. Not all30 qualified, no student training, no final matrix; office is previously inspected.')
    if (root/'REVIEW.json').exists():
        saved = read(root/'REVIEW.json')
        assert {k:v for k,v in saved.items() if k!='reviewed_utc'} == {k:v for k,v in result.items() if k!='reviewed_utc'}
        return saved
    write(root/'REVIEW.json', result)
    return result


def prepare_office(root, output):
    assert not output.exists()
    result = review(root)
    if result['selected'] is None:
        raise ValueError('No training-eligible midpoint teacher; no office or recollection dispatched')
    original = read(root/'REGISTRATION.json')
    tail = Path(original['parent'])
    template = read(tail/'REGISTRATION.json')
    case = copy.deepcopy(next(c for c in template['cases'] if c['id']=='office_v1_avg1'))
    case.update(id='office_'+result['selected'], config=str(root/(result['selected']+'.json')))
    reg = copy.deepcopy(original)
    reg.update(schema='sii-training-selected-teacher-office-regression-v1', registered_utc=now(),
               midpoint=str(root), midpoint_review_sha256=sha(root/'REVIEW.json'),
               cases=[case], maximum_episodes=1,
               config_sha256={case['config']:sha(Path(case['config']))},
               interpretation='Selected on five training identities by fixed priority; this single previously inspected office condition is a disclosed regression check, not unseen evaluation or a source of labels.',
               next_step='Review full original Task/Strict audit; do not fit or dispatch a new collection automatically.')
    reg['source_sha256'] = {name:sha(ROOT/name) for name in original['source_sha256']}
    reg['source_sha256'][str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    output.mkdir(parents=True)
    write(output/'REGISTRATION.json', reg)
    print(output, sha(output/'REGISTRATION.json'))


def prepare_collection(root, office, output):
    assert not output.exists()
    result = review(root)
    assert result['selected'] is not None
    inactive('sii-special-teacher-midpoint-office-v1-20261028.service')
    reg, state = read(office/'REGISTRATION.json'), read(office/'execution.json')
    assert state['status']=='complete_pending_review' and len(state['episodes'])==reg['maximum_episodes']==1
    assert state['registration_sha256']==sha(office/'REGISTRATION.json')
    assert reg['midpoint_review_sha256']==sha(root/'REVIEW.json')
    row=state['episodes'][0];case=reg['cases'][0]
    assert row['returncode']==0 and row['id']==case['id']
    assert sha(office/case['id']/'AUDIT.json')==row['audit_sha256']
    audit=read(office/case['id']/'AUDIT.json')
    assert audit['task_success'] and audit['strict_success'], 'Teacher office regression still fails; inspect, no automatic recollection'
    assert audit['action_replay_max_abs']==audit['common_filter_replay_max_abs']==0
    original=read(root/'REGISTRATION.json')
    previous=Path(original['collection'])
    plan=validate(previous/'COLLECTION_PLAN.json')
    assert read(previous/'COLLECTION_PROGRESS.json')['status']=='finished_with_nonqualified_demonstrations'
    teacher=root/(result['selected']+'.json')
    successor=copy.deepcopy(plan)
    refs={}
    for scene in ('rod','ball','corner'):
        folder=root/(result['selected']+'_'+scene+'_00')/scene
        refs[scene]=dict(folder=str(folder),qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json'))
    successor.update(registered_utc=now(),teacher_config=str(teacher),teacher_file_sha256=sha(teacher),
                     teacher_config_sha256=sha(teacher),development_references=refs,
                     supersedes=dict(previous_plan=str(previous/'COLLECTION_PLAN.json'),
                         previous_plan_sha256=sha(previous/'COLLECTION_PLAN.json'),
                         previous_progress_sha256=sha(previous/'COLLECTION_PROGRESS.json'),
                         midpoint_review_sha256=sha(root/'REVIEW.json'),
                         office_execution_sha256=sha(office/'execution.json'),
                         selected_setting=result['selected'],
                         rationale='Finite midpoint selected on training identities; office regression checked and disclosed. Preserve every30 identity/seed/split/MJB/action contract/gate. Retain all failed v6 and probe receipts; no teacher test trajectory becomes imitation data.'))
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
    p.add_argument('--office-output',type=Path)
    p.add_argument('--office',type=Path)
    p.add_argument('--collection-output',type=Path)
    p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if a.run:
        run(a.root.resolve())
    elif a.office_output:
        prepare_office(a.root.resolve(),a.office_output.resolve())
    elif a.collection_output:
        assert a.office is not None
        prepare_collection(a.root.resolve(),a.office.resolve(),a.collection_output.resolve())
    else:
        r=review(a.root.resolve());print(r['eligibility'],r['selected'])
