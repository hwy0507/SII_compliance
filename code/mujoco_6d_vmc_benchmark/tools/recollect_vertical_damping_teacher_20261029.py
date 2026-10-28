"""Register the unchanged original30 only after the seven damping controls pass."""
import argparse
import copy
from pathlib import Path

from collect_special_scene_actions_20261028 import ROOT, read, sha, validate, write
from diagnose_special_scene_regression_20261028 import now
from review_special_teacher_midpoint_20261028 import inactive


def prepare(root, output):
    assert not output.exists(), 'Never overwrite a collection'
    assert (root/'REVIEW.json').exists(), 'Complete seven-control review required'
    review, reg, state = (read(root/n) for n in ('REVIEW.json','REGISTRATION.json','execution.json'))
    assert review['status']=='complete_seven_controls_review' and review['candidate_eligible']
    assert review['all_seven_qualified'] and review['candidate_train_tail_energy']<review['parent_train_tail_energy']
    assert review['registration_sha256']==sha(root/'REGISTRATION.json')==state['registration_sha256']
    assert review['execution_sha256']==sha(root/'execution.json')
    assert review['source_sha256']==sha(ROOT/'tools/teacher_vertical_damping_control_20261029.py')
    assert state['status']=='complete_pending_review' and len(state['episodes'])==len(review['rows'])==7
    inactive(reg['service'])
    for name, digest in reg['source_sha256'].items():assert sha(ROOT/name)==digest,name
    for case, row, receipt in zip(reg['cases'],review['rows'],state['episodes']):
        assert case['id']==row['id']==receipt['id'] and receipt['returncode']==0
        folder=root/case['id']
        if case['kind']=='scene':
            folder/=case['scene'];q=read(folder/'DEMONSTRATION_QUALIFICATION.json')
            assert q['status']=='qualified'
            assert sha(folder/'DEMONSTRATION_QUALIFICATION.json')==row['qualification_sha256']==receipt['qualification_sha256']
            for name,digest in q['input_hashes'].items():assert sha(folder/name)==digest
        else:
            assert row['task'] and row['strict']
            assert sha(folder/'AUDIT.json')==row['audit_sha256']==receipt['audit_sha256']
    previous=ROOT/'outputs/special_scene_vmc_collection_20261029_v7'
    old=validate(previous/'COLLECTION_PLAN.json')
    assert read(previous/'COLLECTION_PROGRESS.json')['status']=='finished_with_nonqualified_demonstrations'
    teacher=Path(reg['cases'][0]['config'])
    assert len(reg['config_sha256'])==1 and reg['config_sha256'][str(teacher)]==sha(teacher)
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
            rationale='Only teacher z damping110->220 after six training controls and inspected office regression; '
            'same30 real scenes/seeds/24train6validation/gates. Original failed validation remains preserved; '
            'no office labels, no automatic fitting and no claim that all30 will qualify.'))
    plan['source_sha256']={name:sha(ROOT/name) for name in old['source_sha256']}
    for name in ('teacher_vertical_damping_control_20261029.py',Path(__file__).name):
        plan['source_sha256']['tools/'+name]=sha(ROOT/'tools'/name)
    for before, after in zip(old['episodes'],plan['episodes']):
        after['folder']=str(output/after['id']/after['scene'])
        assert {k:v for k,v in before.items() if k!='folder'}=={k:v for k,v in after.items() if k!='folder'}
    output.mkdir(parents=True);write(output/'COLLECTION_PLAN.json',plan)
    validate(output/'COLLECTION_PLAN.json')
    print(output,sha(output/'COLLECTION_PLAN.json'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();prepare(args.root.resolve(),args.output.resolve())
