"""Review the single slow-intent control and gate same30 recollection."""
import argparse
import copy
from pathlib import Path

from collect_special_scene_actions_20261028 import ROOT, read, sha, validate, write
from diagnose_special_scene_regression_20261028 import now
from review_legacy_units_controls_20261029 import review


def checked_review(root):
    reg=read(root/'REGISTRATION.json')
    assert reg['schema']=='sii-teacher-slow-intent-control-v1'
    parent=ROOT/'outputs/special_teacher_damping_20261029_v1'
    before=read(parent/'teacher_damping.json')
    assert sha(parent/'teacher_damping.json')==reg['parent_config_sha256']
    expected=copy.deepcopy(before);expected['recovery']['intent_velocity_mps']=.003
    assert len({c['config'] for c in reg['cases']})==1
    assert read(Path(reg['cases'][0]['config']))==expected
    return review(root)


def recollect(root,output):
    result=checked_review(root)
    assert result['all_six_qualified'], 'Original finite teacher gates failed; no new collection'
    assert not output.exists()
    previous=ROOT/'outputs/special_scene_vmc_collection_20261028_v6'
    old=read(previous/'COLLECTION_PLAN.json')
    assert read(previous/'COLLECTION_PROGRESS.json')['status']=='finished_with_nonqualified_demonstrations'
    reg=read(root/'REGISTRATION.json');teacher=Path(reg['cases'][0]['config'])
    references={}
    for scene in ('rod','ball','corner'):
        case=next(c for c in reg['cases'] if c.get('identity')==scene+'_00')
        folder=root/case['id']/scene
        references[scene]=dict(folder=str(folder),qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json'))
    plan=copy.deepcopy(old)
    plan.update(registered_utc=now(),teacher_config=str(teacher),teacher_file_sha256=sha(teacher),
        teacher_config_sha256=sha(teacher),development_references=references,
        supersedes=dict(previous_plan_sha256=sha(previous/'COLLECTION_PLAN.json'),
            previous_progress_sha256=sha(previous/'COLLECTION_PROGRESS.json'),
            teacher_control_review_sha256=sha(root/'REVIEW.json'),
            rationale='Original v6 recovery/readout/velocity1/averaging, doubled translational virtual damping and .003m/s intent-release normalization. Same30 physical identities/seeds/24+6 split/gates. Office regression inspected, never imitation labels; all prior failures retained.'))
    plan['source_sha256']={name:sha(ROOT/name) for name in old['source_sha256']}
    for name in ('intent_recovery_teacher_20261029.py','intent_equilibrium_teacher_20261029.py',
                 'review_legacy_units_controls_20261029.py',Path(__file__).name):
        plan['source_sha256']['tools/'+name]=sha(ROOT/'tools'/name)
    for before,after in zip(old['episodes'],plan['episodes']):
        after['folder']=str(output/after['id']/after['scene'])
        assert {k:v for k,v in before.items() if k!='folder'}=={k:v for k,v in after.items() if k!='folder'}
    output.mkdir(parents=True);write(output/'COLLECTION_PLAN.json',plan)
    validate(output/'COLLECTION_PLAN.json')
    print(output,sha(output/'COLLECTION_PLAN.json'))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--collection-output',type=Path)
    a=p.parse_args()
    if a.collection_output:recollect(a.root.resolve(),a.collection_output.resolve())
    else:
        result=checked_review(a.root.resolve());print('all_six_qualified',result['all_six_qualified'])
        for row in result['rows']:print({k:v for k,v in row.items() if k!='rod_audit'})
