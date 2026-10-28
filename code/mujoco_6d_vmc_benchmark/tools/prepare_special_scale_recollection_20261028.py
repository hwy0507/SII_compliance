"""Register common-scale recollection after complete teacher-factor review.

Prefer the previously established readout, then retaining input averaging,
then retaining reduced velocity alone, then the current two changes. A setting
is eligible only if all three real training-scene controls qualify, including
rod pass-before-withdrawal. This is a regression repair, not test-set selection.
All original30 physical conditions, seeds and splits remain unchanged.
"""
import argparse
import copy
from pathlib import Path

from collect_special_scene_actions_20261028 import ROOT, read, sha, validate, write
from diagnose_special_scene_regression_20261028 import now


def prepare(original, factors, output):
    if output.exists():
        raise FileExistsError(output)
    plan = validate(original/'COLLECTION_PLAN.json')
    state = read(factors/'execution.json')
    reg = read(factors/'REGISTRATION.json')
    assert state['status'] == 'complete_pending_review'
    assert len(state['episodes']) == reg['maximum_episodes'] == 9
    assert state['registration_sha256'] == sha(factors/'REGISTRATION.json')
    # Bind every failure as well as every success before making the decision.
    for case, row in zip(reg['cases'], state['episodes']):
        assert case['id'] == row['id'] and row['returncode'] == 0
        folder = factors/case['id']/case['scene']
        assert sha(folder/'DEMONSTRATION_QUALIFICATION.json') == row['qualification_sha256']
        for name, digest in row['qualification']['input_hashes'].items():
            assert sha(folder/name) == digest, str(folder/name)
        assert row['qualification']['input_hashes']['scene.mjb'] == case['expected_model_sha256']
    reference = Path(reg['reference'])
    ref_state = read(reference/'execution.json')
    assert sha(reference/'execution.json') == reg['reference_execution_sha256']
    settings = []
    for label in ('v1_avg0', 'v1_avg1', 'v0.5_avg0', 'v0.5_avg1'):
        source_state = ref_state if label == 'v0.5_avg1' else state
        ids = [scene+'_teacher' if label == 'v0.5_avg1' else label+'_'+scene for scene in ('rod', 'ball', 'corner')]
        rows = [next(r for r in source_state['episodes'] if r['id'] == id_) for id_ in ids]
        settings.append(dict(setting=label, qualified=all(r['qualification']['status']=='qualified' for r in rows), rows=rows))
    selected = next((s for s in settings if s['qualified']), None)
    if selected is None:
        raise ValueError('No teacher qualified on all three real scenes; no collection dispatched')
    label = selected['setting']
    base = reference if label == 'v0.5_avg1' else factors
    references = {}
    for scene, row in zip(('rod', 'ball', 'corner'), selected['rows']):
        folder = base/row['id']/scene
        assert sha(folder/'DEMONSTRATION_QUALIFICATION.json') == row['qualification_sha256']
        for name, digest in row['qualification']['input_hashes'].items():
            assert sha(folder/name) == digest
        if scene == 'rod':
            assert read(folder/'ROD_YIELD_REJOIN_AUDIT_V3.json')['status'] == 'passed'
        references[scene] = dict(folder=str(folder), qualification_sha256=row['qualification_sha256'])
    teacher = reference/'teacher_new.json' if label == 'v0.5_avg1' else factors/(label+'.json')
    config = read(teacher)
    assert config['velocity_weight'] in (.5, 1.) and type(config['pair_average']) is bool
    original_reg = read(reference/'REGISTRATION.json') if label == 'v0.5_avg1' else reg
    assert sha(teacher) == original_reg['config_sha256'][str(teacher)]
    successor = copy.deepcopy(plan)
    successor.update(registered_utc=now(), teacher_config=str(teacher),
                     teacher_file_sha256=sha(teacher), teacher_config_sha256=sha(teacher),
                     development_references=references,
                     action_contract=dict(linear_yield_mps=.32, angular_yield_radps=.6,
                                          actor_dt_s=.04, label='unfiltered normalized requested action'),
                     supersedes=dict(original_plan=str(original/'COLLECTION_PLAN.json'),
                                     original_plan_sha256=sha(original/'COLLECTION_PLAN.json'),
                                     factors_registration_sha256=sha(factors/'REGISTRATION.json'),
                                     factors_execution_sha256=sha(factors/'execution.json'),
                                     setting_priority=[s['setting'] for s in settings],
                                     setting_eligibility={s['setting']:s['qualified'] for s in settings},
                                     selected_setting=label,
                                     rationale='Fix cross-scene action scale; restore historical teacher components where all three actual development scene controls qualify, including rod pass/rejoin. No narrowing of conditions, no test labels, no gate or physics relaxation. Current12 are previously inspected regression tests, not unseen.'))
    sources = list((ROOT/'scripts').glob('*.py'))
    sources += [ROOT/'tools'/n for n in (
        'collect_special_scene_actions_20261028.py', 'run_video_reference_vmc_20261028.py',
        'audit_video_reference_vmc_20261028.py', 'qualify_special_scene_demo_20261028.py',
        'audit_rod_yield_rejoin_v3_20261028.py', 'optimize_tool_contact_20261002.py',
        'prepare_special_scale_recollection_20261028.py')]
    successor['source_sha256'] = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    for old, new in zip(plan['episodes'], successor['episodes']):
        new['folder'] = str(output/new['id']/new['scene'])
        assert {k:v for k,v in old.items() if k != 'folder'} == {k:v for k,v in new.items() if k != 'folder'}
    output.mkdir(parents=True)
    write(output/'COLLECTION_PLAN.json', successor)
    validate(output/'COLLECTION_PLAN.json')
    print(output, sha(output/'COLLECTION_PLAN.json'))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for field in ('original', 'factors', 'output'):
        p.add_argument('--'+field, required=True, type=Path)
    a = p.parse_args()
    prepare(a.original.resolve(), a.factors.resolve(), a.output.resolve())
