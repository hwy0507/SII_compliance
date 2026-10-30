"""Independently verify the full12 eligibility extension, including all failures.

Prefix mode is explicitly incomplete. Neither mode is a final unseen-test audit.
"""
import argparse
import json
from pathlib import Path

from catalogue_v9_frozen_candidates_20261029 import build
from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from review_v9_paired_scene_closure_20261029 import verify_qualification

TERMINAL = {'selection_complete_pending_independent_audit', 'eligibility_exhausted_preserved'}


def validate_structure(reg, state, final):
    groups = state['groups']
    expected = reg['catalogue']['groups']
    assert reg['candidate_limit_per_family_seed'] == 12
    assert len(groups) <= len(expected) == 9
    assert len(reg['references']) == 9
    assert [r['identity'] for r in reg['references']] == [s+'_'+i for s in ('rod', 'ball', 'corner') for i in ('00', '08', '09')]
    if final:
        assert state['status'] in TERMINAL and len(groups) == 9
    selected = []
    for index, (actual, catalogue) in enumerate(zip(groups, expected)):
        assert (actual['family'], actual['seed']) == (catalogue['family'], catalogue['seed'])
        trials = actual['trials']
        assert 1 <= len(trials) <= 12
        for rank, trial in enumerate(trials):
            assert trial['candidate'] == catalogue['ordered_candidates'][rank]
            cases = trial['cases']
            assert len(cases) <= 9
            assert [c['identity'] for c in cases] == [r['identity'] for r in reg['references'][:len(cases)]]
            assert all(c['development_qualified'] for c in cases[:-1]), 'Continued after failed case'
            if trial['status'] == 'failed_eligibility_full_episode_preserved':
                assert cases and not cases[-1]['development_qualified']
            elif trial['status'] == 'development_qualified_all_nine':
                assert len(cases) == 9 and all(c['development_qualified'] for c in cases)
                assert rank == len(trials)-1 and actual['selected'] == trial['candidate']
                selected.append(trial['candidate'])
            else:
                assert not final and trial['status'] == 'running'
                assert index == len(groups)-1 and rank == len(trials)-1
                assert all(c['development_qualified'] for c in cases)
        if actual['selected'] is None:
            assert not any(t['status'] == 'development_qualified_all_nine' for t in trials)
            if actual.get('status') == 'candidate_budget_exhausted_preserved':
                assert len(trials) == 12 and all(t['status'] == 'failed_eligibility_full_episode_preserved' for t in trials)
            else:
                assert not final and index == len(groups)-1
        else:
            assert actual['selected'] == trials[-1]['candidate']
            assert trials[-1]['status'] == 'development_qualified_all_nine'
            assert actual.get('status') in (None, 'selected_development_qualified')
    models = state['selected_models']
    assert len(models) == len(selected)
    for model, candidate in zip(models, selected):
        for key in ('family', 'seed', 'validation_mse', 'checkpoint', 'checkpoint_sha256', 'metadata', 'metadata_sha256'):
            assert model[key] == candidate[key], key
        assert model['selected_trial'] == candidate['id']
    if final:
        expected_status = 'selection_complete_pending_independent_audit' if len(selected) == 9 else 'eligibility_exhausted_preserved'
        assert state['status'] == expected_status
    return selected


def review(root, output, prefix=False):
    assert not output.exists(), 'Preserve prior reviews'
    execution_bytes = (root/'execution.json').read_bytes()
    state = json.loads(execution_bytes)
    reg = read(root/'REGISTRATION.json')
    assert state['registration_sha256'] == sha(root/'REGISTRATION.json')
    for name, digest in reg['source_sha256'].items():
        assert sha(ROOT/name) == digest, name
    parent = Path(reg['parent'])
    assert sha(parent/'execution.json') == reg['parent_execution_sha256']
    assert sha(parent/'REGISTRATION.json') == reg['parent_registration_sha256']
    assert sha(parent/'REVIEW.json') == reg['parent_review_sha256']
    assert all(r['teacher_qualified'] for r in read(parent/'REVIEW.json')['rows'])
    # Rebuild from immutable fit metadata rather than trusting runner catalogue.
    training = Path(reg['catalogue']['groups'][0]['ordered_candidates'][0]['metadata']).parents[2]
    assert build(training) == reg['catalogue']
    previous = Path(reg['previous_selection'])
    assert sha(previous/'execution.json') == reg['previous_execution_sha256']
    assert sha(previous/'REGISTRATION.json') == reg['previous_registration_sha256']
    assert sha(previous/'FINAL_REVIEW.json') == reg['previous_review_sha256']
    previous_report = read(previous/'FINAL_REVIEW.json')
    assert previous_report['status'] == 'verified_complete_development_selection'
    assert previous_report['execution_snapshot_sha256'] == reg['previous_execution_sha256']
    selected = validate_structure(reg, state, final=not prefix)
    parent_cases = read(parent/'REGISTRATION.json')['cases']
    allowed_parent = {(c['model']['checkpoint_sha256'], c['identity']): parent/c['id']/c['scene'] for c in parent_cases}
    for previous_group in read(previous/'execution.json')['groups']:
        for trial in previous_group['trials']:
            for case in trial['cases']:
                key = (trial['candidate']['checkpoint_sha256'], case['identity'])
                folder = Path(case['folder'])
                if key in allowed_parent:
                    assert allowed_parent[key] == folder
                else:
                    allowed_parent[key] = folder
    rows = []
    for group in state['groups']:
        for trial in group['trials']:
            candidate = trial['candidate']
            assert sha(Path(candidate['checkpoint'])) == candidate['checkpoint_sha256']
            assert sha(Path(candidate['metadata'])) == candidate['metadata_sha256']
            for receipt, reference in zip(trial['cases'], reg['references']):
                folder = Path(receipt['folder'])
                if receipt['reused_parent_episode']:
                    assert folder == allowed_parent[(candidate['checkpoint_sha256'], reference['identity'])]
                    assert receipt['reused_origin_run'] == str(parent if parent in folder.parents else previous)
                else:
                    name = candidate['family']+'_s'+str(candidate['seed'])+'_rank'+str(candidate['validation_rank'])
                    assert folder == root/'evaluations'/name/reference['identity']/reference['scene']
                qualification = verify_qualification(folder, receipt['qualification_sha256'])
                teacher = Path(reference['folder'])
                teacher_q = verify_qualification(teacher, reference['qualification_sha256'])
                assert teacher_q['status'] == 'qualified'
                assert sha(teacher/'execution.json') == reference['execution_sha256']
                assert sha(teacher/'teacher.json') == reference['config_sha256'] == sha(folder/'teacher.json')
                execution, teacher_execution = read(folder/'execution.json'), read(teacher/'execution.json')
                assert execution['status'] == 'complete'
                assert sha(folder/'scene.mjb') == execution['model_sha256'] == teacher_execution['model_sha256'] == reference['model_sha256']
                assert sha(folder/'student_checkpoint.npz') == candidate['checkpoint_sha256']
                assert execution['filter_config'] == teacher_execution['filter_config']
                for key, value in reference['parameters'].items():
                    assert execution['experiment_environment'][key] == teacher_execution['experiment_environment'][key] == str(value)
                assert receipt['split'] == reference['split']
                assert receipt['development_qualified'] == (qualification['status'] == 'qualified')
                for field, source in [('task_success', 'task_success'), ('safety_valid', 'safety_valid'), ('scene_behavior_valid', 'scene_contact_valid')]:
                    assert receipt[field] == qualification[source]
                rows.append(dict(family=group['family'], seed=group['seed'], rank=candidate['validation_rank'],
                    identity=reference['identity'], qualified=receipt['development_qualified'],
                    reused=receipt['reused_parent_episode'], qualification_sha256=receipt['qualification_sha256']))
    if not prefix:
        assert (root/'execution.json').read_bytes() == execution_bytes
        selection = read(root/'DEVELOPMENT_SELECTION.json')
        assert selection['models'] == state['selected_models']
        assert selection['registration_sha256'] == state['registration_sha256']
        assert selection['status'] == state['status'] and selection['final_test_performed'] is False
    import hashlib
    result = dict(status='verified_incomplete_prefix' if prefix else 'verified_complete_development_selection',
        execution_snapshot_sha256=hashlib.sha256(execution_bytes).hexdigest(), registration_sha256=sha(root/'REGISTRATION.json'),
        reviewer_sha256=sha(Path(__file__)), completed_cases=len(rows), reused_cases=sum(r['reused'] for r in rows),
        failed_cases=sum(not r['qualified'] for r in rows), selected_groups=len(selected), rows=rows,
        final_test_performed=False, limitations=['Development train/validation qualification only.',
            'No final Strict, unseen-test success, SPT, or overall repair conclusion follows from this review.'])
    write(output, result)
    print({k:v for k,v in result.items() if k != 'rows'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--prefix', action='store_true')
    args = parser.parse_args()
    review(args.root.resolve(), args.output.resolve(), args.prefix)
