"""Review finite damping controls and conditionally register the same new30.

Never launch collection/fitting. Preserve all original identities, split,
physics, gates and failures. Office traces are excluded from imitation data.
"""
import argparse
import copy
from pathlib import Path

from collect_special_scene_actions_20261028 import ROOT, read, sha, validate, write
from diagnose_special_scene_regression_20261028 import now
from review_legacy_units_controls_20261029 import review


def checked_review(root):
    reg = read(root/'REGISTRATION.json')
    assert reg['schema'] == 'sii-teacher-original-static-gain-damping-control-v1'
    teacher = read(Path(reg['cases'][0]['config']))
    original = read(Path(reg['reference_v6_config']))
    assert teacher['options'] == dict(damping_6d=[56.,56.,110.,2.8,2.4,3.])
    assert {k:v for k,v in teacher.items() if k!='options'} == original
    assert len({c['config'] for c in reg['cases']}) == 1
    return review(root)


def recollect(root, output):
    result = checked_review(root)
    assert result['all_six_qualified'], 'Failed finite controls; preserve failures, no collection'
    assert not output.exists()
    previous = ROOT/'outputs/special_scene_vmc_collection_20261028_v6'
    old = read(previous/'COLLECTION_PLAN.json')
    assert read(previous/'COLLECTION_PROGRESS.json')['status'] == 'finished_with_nonqualified_demonstrations'
    reg = read(root/'REGISTRATION.json')
    teacher = Path(reg['cases'][0]['config'])
    references = {}
    for scene in ('rod', 'ball', 'corner'):
        case = next(c for c in reg['cases'] if c.get('identity') == scene+'_00')
        folder = root/case['id']/scene
        references[scene] = dict(folder=str(folder), qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json'))
    plan = copy.deepcopy(old)
    plan.update(registered_utc=now(), teacher_config=str(teacher), teacher_file_sha256=sha(teacher),
        teacher_config_sha256=sha(teacher), development_references=references,
        supersedes=dict(previous_plan_sha256=sha(previous/'COLLECTION_PLAN.json'),
            previous_progress_sha256=sha(previous/'COLLECTION_PROGRESS.json'),
            teacher_control_review_sha256=sha(root/'REVIEW.json'),
            rationale='Original v6 recovery/velocity1/averaging/readout gains; only translational virtual damping doubled. Same30 physical identities/seeds/24+6 split/gates; all failures retained. Office regression inspected but excluded from imitation.'))
    plan['source_sha256'] = {name:sha(ROOT/name) for name in old['source_sha256']}
    for name in ('intent_recovery_teacher_20261029.py', 'intent_equilibrium_teacher_20261029.py',
                 'review_legacy_units_controls_20261029.py', Path(__file__).name):
        plan['source_sha256']['tools/'+name] = sha(ROOT/'tools'/name)
    for before, after in zip(old['episodes'], plan['episodes']):
        after['folder'] = str(output/after['id']/after['scene'])
        assert {k:v for k,v in before.items() if k!='folder'} == {k:v for k,v in after.items() if k!='folder'}
    output.mkdir(parents=True)
    write(output/'COLLECTION_PLAN.json', plan)
    validate(output/'COLLECTION_PLAN.json')
    print(output, sha(output/'COLLECTION_PLAN.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--collection-output', type=Path)
    args = parser.parse_args()
    if args.collection_output:
        recollect(args.root.resolve(), args.collection_output.resolve())
    else:
        result = checked_review(args.root.resolve())
        print('all_six_qualified', result['all_six_qualified'])
        for row in result['rows']:
            print({k:v for k,v in row.items() if k!='rod_audit'})
