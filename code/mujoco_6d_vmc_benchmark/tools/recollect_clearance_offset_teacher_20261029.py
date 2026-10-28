"""Register the original30 real-scene identities only after all six controls pass."""
import argparse
import copy
from pathlib import Path

from collect_special_scene_actions_20261028 import ROOT,read,sha,validate,write
from diagnose_special_scene_regression_20261028 import now
from teacher_clearance_offset_control_20261029 import checked_review


def prepare(root,output):
    assert not output.exists()
    checked_review(root)
    result=read(root/'REVIEW.json')
    assert result['all_six_qualified'], 'Keep failed teacher receipts; no collection'
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
            rationale='All six finite controls passed: v6 averaged readout, doubled translational damping, .003m/s intent release and reference-relative offset .034568199770793496m. Same30 scenes/seeds/24train+6val/gates. Inspected office is development regression, never imitation labels; every prior failure preserved.'))
    plan['source_sha256']={name:sha(ROOT/name) for name in old['source_sha256']}
    for name in ('intent_recovery_teacher_20261029.py','intent_equilibrium_teacher_20261029.py',
                 'review_legacy_units_controls_20261029.py','teacher_clearance_offset_control_20261029.py',Path(__file__).name):
        plan['source_sha256']['tools/'+name]=sha(ROOT/'tools'/name)
    for before,after in zip(old['episodes'],plan['episodes']):
        after['folder']=str(output/after['id']/after['scene'])
        assert {k:v for k,v in before.items() if k!='folder'}=={k:v for k,v in after.items() if k!='folder'}
    assert len(plan['episodes'])==30
    assert sum(e['split']=='train' for e in plan['episodes'])==24
    assert sum(e['split']=='validation' for e in plan['episodes'])==6
    output.mkdir(parents=True);write(output/'COLLECTION_PLAN.json',plan)
    validate(output/'COLLECTION_PLAN.json')
    print(output,sha(output/'COLLECTION_PLAN.json'))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path);a=p.parse_args();prepare(a.root.resolve(),a.output.resolve())
