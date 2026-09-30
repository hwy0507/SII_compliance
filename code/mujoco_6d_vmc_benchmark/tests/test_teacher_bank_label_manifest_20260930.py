"""Train-only manifests fail closed on leakage, provenance drift and duplicate conflicts."""
import copy
import json
from pathlib import Path
import shutil
import sys
import zipfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import teacher_bank_label_manifest_20260930 as exporter


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True))


def fixture():
    return dict(id='active_short_train_0000', split='train', category='active_short',
                seed=123, physical_config_sha256='fixed-physical-config')


def inputs():
    f = fixture()
    selected = dict(x=[.5]*7, index=0)
    config = {'velocity_weight':.25, 'options':{'k':[1.,2.]}}
    request = dict(fixture=f, method='vmc', phase='search', x=selected['x'], teacher=config, plan_sha256='plan')
    execution = dict(status='completed', returncode=0, plan_sha256='plan')
    audit = dict(split='train', method='vmc', fixture_id=f['id'], audit_source_sha256='source')
    audit.update({key:True for key in exporter.SUCCESS_KEYS})
    audit['exposure'] = {'passed':True}
    return request, execution, audit, {f['id']:f}, selected, config


def test_legacy_validation_true_is_never_a_train_label():
    request, execution, audit, fixtures, selected, config = inputs()
    request['fixture']['split'] = 'validation'
    audit['split'] = 'validation'
    assert audit['esn_label_eligible'] is True
    errors = exporter.parameter_eligibility(request, execution, audit, fixtures, selected, config, 'plan', 'source')
    assert 'not_train_even_if_legacy_label_flag_true' in errors


@pytest.mark.parametrize('change, expected', [
    ('unfinished', 'not_completed_rc0'), ('wrong_x', 'not_locked_coordinates_and_config'),
    ('wrong_config', 'not_locked_coordinates_and_config'), ('wrong_source', 'audit_source_binding_mismatch'),
    ('wrong_plan', 'plan_binding_mismatch'), ('wrong_fixture', 'fixture_not_exact_original_train_manifest_entry')])
def test_excludes_unfinished_and_wrong_provenance(change, expected):
    request, execution, audit, fixtures, selected, config = copy.deepcopy(inputs())
    # Break aliasing intentionally so the immutable expected configuration is independent.
    request = copy.deepcopy(request)
    if change == 'unfinished':execution['status'] = 'running'
    if change == 'wrong_x':request['x'][0] = .1
    if change == 'wrong_config':request['teacher']['velocity_weight'] = .4
    if change == 'wrong_source':audit['audit_source_sha256'] = 'wrong'
    if change == 'wrong_plan':execution['plan_sha256'] = 'wrong'
    if change == 'wrong_fixture':request['fixture']['seed'] = 999
    errors = exporter.parameter_eligibility(request, execution, audit, fixtures, selected, config, 'plan', 'source')
    assert expected in errors


def duplicate(phase, success=True):
    return dict(identity_sha256='same', fixture_id='train0', folder=phase+'/train0',
        priority=0 if phase == 'search' else 1, success_signature=[success]*6,
        model_sha256='same-model', expected_model_sha256='same-model',
        failure_reasons=[] if success else ['task_failed'])


def test_duplicates_do_not_increase_samples_and_search_has_fixed_precedence():
    selected, excluded, quarantine = exporter.deduplicate([duplicate('collection'), duplicate('search')])
    assert len(selected) == 1 and selected[0]['folder'] == 'search/train0'
    assert excluded[0]['reasons'] == ['duplicate_identity_not_extra_sample']
    assert not quarantine


@pytest.mark.parametrize('successful_phase', ['search', 'collection'])
def test_contradictory_complete_duplicates_never_choose_the_success(successful_phase):
    rows = [duplicate(phase, phase == successful_phase) for phase in ('search', 'collection')]
    selected, excluded, quarantine = exporter.deduplicate(rows)
    assert not selected and not excluded
    assert len(quarantine) == 1
    assert quarantine[0]['reason'] == 'contradictory_or_invalid_complete_success_labels'


def test_model_difference_quarantines_same_fixture_instead_of_creating_new_sample():
    rows = [duplicate('search'),duplicate('collection')]
    rows[1]['model_sha256'] = 'different-model'
    chosen, excluded, quarantine = exporter.deduplicate(rows)
    assert not chosen and not excluded and len(quarantine) == 1
    assert quarantine[0]['reason'] == 'different_or_unbound_compiled_model_for_same_fixture_and_parameters'


def synthetic_snapshot(tmp_path, include_validation=True):
    run = tmp_path/'run'
    source = run/'source/tools/teacher_bank_rollout_20260930.py'
    source.parent.mkdir(parents=True)
    source.write_text('# frozen source\n')
    f = fixture()
    plan = dict(search_candidates_per_category=6, categories=['passive_corner','active_short','active_long'],
        sources={'tools/teacher_bank_rollout_20260930.py':exporter.sha(source)}, source_inputs={},
        server='arm1@192.168.31.70', remote='/home/arm1/sii_shared/SII_compliance/test_fixture')
    write(run/'plan.json', plan)
    write(run/'fixtures.json', [f])
    bank, groups = {}, {}
    config = {'velocity_weight':.25}
    for category in plan['categories']:
        for method in ('vmc','admittance','impedance'):
            selected = dict(index=0, x=[.5]*7, anchor_feasible=True)
            key = category+'/'+method
            bank[key] = [selected]
            groups[key] = dict(all_budget_candidates_verified=True, recorded_selection_matches_independent_rank=True,
                candidates=[{}]*6, recorded_selection=selected, best_complete_candidate=selected,
                selected_controller_config=config)
    write(run/'teacher_bank.json', bank)
    for phase in ('search','validation') if include_validation else ('search',):
        current = copy.deepcopy(f)
        if phase == 'validation':
            current['split'] = 'validation';current['id'] = 'active_short_validation_0000'
        relative = 'search/active_short/vmc/c00/0' if phase == 'search' else 'validation/active_short_validation_0000/vmc'
        folder = run/relative
        req = dict(fixture=current, method='vmc', phase=phase, x=[.5]*7, teacher=config, plan_sha256=exporter.sha(run/'plan.json'))
        write(folder/'request.json', req)
        write(folder/'execution.json', dict(status='completed', returncode=0, plan_sha256=req['plan_sha256']))
        for name, columns in exporter.RAW_CONTRACT.items():
            path = folder/name;path.parent.mkdir(parents=True,exist_ok=True)
            with zipfile.ZipFile(path, 'w') as archive:
                for column in columns:archive.writestr(column+'.npy', b'opaque test bytes; not a replay')
        raw = {name:exporter.sha(folder/name) for name in exporter.RAW_CONTRACT}
        (folder/'rollout.mjb').write_bytes(b'opaque compiled model fixture')
        raw['rollout.mjb'] = exporter.sha(folder/'rollout.mjb')
        raw['request.json'] = exporter.sha(folder/'request.json')
        audit = dict(method='vmc', split=current['split'], fixture_id=current['id'],
            audit_source_sha256=exporter.sha(source), files_sha256=raw, model_sha256=raw['rollout.mjb'],
            failure_reasons=[], exposure={'passed':True})
        audit.update({key:True for key in exporter.SUCCESS_KEYS})
        write(folder/'audit.json', audit)
        archive = dict(raw, **{name:exporter.sha(folder/name) for name in ('audit.json','execution.json')})
        write(folder/'archive_manifest.json', archive)
        write(run/f'archive_receipts/{relative}/receipt.json', dict(verified_path=f'{plan["server"]}:{plan["remote"]}/{relative}'))
    write(run/'fixture_model_identity.json', {f['id']:{'model_sha256':raw['rollout.mjb']}})
    snapshot = tmp_path/'review_bundle/metadata_snapshot'
    for path in run.rglob('*.json'):
        dest = snapshot/path.relative_to(run);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    review = dict(original_run=str(run), snapshot_consistency={'stable':True},
        closeout=dict(bank_certified_locked=True, all_candidate_summaries_and_rank_verified=True,
            source_manifest_verified=True, reconstructed_groups=groups),
        metadata_sha256={str(p.relative_to(snapshot)):exporter.sha(p) for p in snapshot.rglob('*.json')})
    review_path = tmp_path/'review_bundle/review.json';write(review_path,review)
    return run, review_path, snapshot


def test_full_export_rejects_legacy_validation_without_copying_raw(tmp_path):
    run, review, snapshot = synthetic_snapshot(tmp_path)
    output = tmp_path/'new_manifest.json'
    result = exporter.export(run,review,exporter.sha(review),snapshot,output)
    assert result['unique_total'] == 1
    assert result['unique_count_by_category']['active_short'] == 1
    assert any(row['folder'].startswith('validation/') for row in result['excluded'])
    assert not result['quarantined']
    assert not result['training_started'] and not result['raw_copied']
    sample = result['categories']['active_short'][0]
    assert sample['server_raw_directory'].startswith('arm1@192.168.31.70:/home/arm1/')
    with pytest.raises(FileExistsError):exporter.export(run,review,exporter.sha(review),snapshot,output)


def test_actual_source_tampering_fails_closed(tmp_path):
    run, review, snapshot = synthetic_snapshot(tmp_path,False)
    (run/'source/tools/teacher_bank_rollout_20260930.py').write_text('# changed\n')
    with pytest.raises(ValueError,match='Runtime source'):
        exporter.export(run,review,exporter.sha(review),snapshot,tmp_path/'manifest.json')


def test_pinned_snapshot_audit_tampering_fails_closed(tmp_path):
    run, review, snapshot = synthetic_snapshot(tmp_path,False)
    audit_path = snapshot/'search/active_short/vmc/c00/0/audit.json'
    audit = json.loads(audit_path.read_text());audit['task'] = False;write(audit_path,audit)
    with pytest.raises(ValueError,match='altered pinned metadata'):
        exporter.export(run,review,exporter.sha(review),snapshot,tmp_path/'manifest.json')


def test_actual_mjb_tampering_quarantines_without_fallback(tmp_path):
    run,review,snapshot = synthetic_snapshot(tmp_path,False)
    (run/'search/active_short/vmc/c00/0/rollout.mjb').write_bytes(b'different model')
    result = exporter.export(run,review,exporter.sha(review),snapshot,tmp_path/'manifest.json')
    assert result['unique_total'] == 0
    assert result['quarantined'][0]['no_fallback_to_other_duplicate'] is True
    assert 'actual_compiled_model_hash_mismatch' in result['quarantined'][0]['reasons']


@pytest.mark.parametrize('target', ['run','snapshot','review'])
def test_export_cannot_write_inside_frozen_evidence_trees(tmp_path,target):
    run,review,snapshot = synthetic_snapshot(tmp_path,False)
    tree = {'run':run,'snapshot':snapshot,'review':review.parent}[target]
    with pytest.raises(ValueError,match='Output must be outside'):
        exporter.export(run,review,exporter.sha(review),snapshot,tree/'new_manifest.json')
