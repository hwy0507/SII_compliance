"""Closeout must fail closed on partial search and changed collection policy."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import teacher_bank_status_20260930 as status
import teacher_bank_terminal_review_20260930 as terminal


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def fixture_run(tmp_path, successes=((True, True), (False, False))):
    root = tmp_path/'run'
    fixtures = [dict(id='train'+str(i), category='corner', split='train') for i in range(2)]
    fixtures += [dict(id='validation0', category='corner', split='validation')]
    put(root/'fixtures.json', fixtures)
    source = root/'source/example.py'
    source.parent.mkdir(parents=True)
    source.write_text('# frozen source\n')
    put(root/'plan.json', dict(categories=['corner'], methods=['vmc'],
        train_per_category=1000, fixtures_sha256=status.sha(root/'fixtures.json'),
        deadline_epoch=100., search_candidates_per_category=2, anchor_indices=[0, 1],
        sources={'example.py': status.sha(source)}))
    history = []
    for index, flags in enumerate(successes):
        candidate = root/f'search/corner/vmc/c{index:02d}'
        put(candidate/'decision.json', dict(x=[float(index)], algorithm='latin_hypercube'))
        rows = [make_attempt(root, fixtures[i], str((candidate/str(i)).relative_to(root)),
            phase='search', x=[float(index)], eligible=flag, gain=index) for i, flag in enumerate(flags)]
        summary, errors = terminal.independent_candidate(rows, [float(index)], index)
        assert not errors
        history.append(summary)
    put(root/'search/corner/vmc/history.json', history)
    winner = min(history, key=terminal.rank)
    put(root/'teacher_bank.json', {'corner/vmc': [dict(winner, anchor_feasible=winner['constraint'] <= 0)]})
    put(root/'anchor_feasibility.json', dict(infeasible_method_categories=[] if winner['constraint'] <= 0 else ['corner/vmc']))
    return root, fixtures, history


def make_attempt(root, fixture, relative, *, phase, x, eligible=True, gain=0):
    folder = root/relative
    plan_hash = status.sha(root/'plan.json')
    put(folder/'request.json', dict(fixture=fixture, method='vmc', phase=phase,
        plan_sha256=plan_hash, teacher={'gain': gain}, x=x))
    put(folder/'execution.json', dict(status='completed', returncode=0, host='test-host',
        started=1. if phase == 'search' else 3., finished=2. if phase == 'search' else 4., plan_sha256=plan_hash))
    audit = dict(fixture_id=fixture['id'], split=fixture['split'], method='vmc',
        eligible=eligible, esn_label_eligible=eligible, model_sha256='a'*64,
        failure_reasons=[] if eligible else ['task_failed'], constraint=-1. if eligible else 1.,
        rmse_m=.01, torque_ratio=.5, completion_proxy_retreat_s=55., score=.45,
        peak_torque_nm=40., peak_speed_mps=.1, penetration_mm=.1)
    put(folder/'audit.json', audit)
    return audit


def inspect(root):
    return terminal.closeout(root, status.summarize(root, now=101.))


def test_complete_search_locks_and_checks_collection_config(tmp_path):
    root, fixtures, _ = fixture_run(tmp_path)
    make_attempt(root, fixtures[0], 'collection/train0/vmc', phase='collection', x=[0.], gain=0)
    make_attempt(root, fixtures[2], 'validation/validation0/vmc', phase='validation', x=[0.], gain=0)
    report = inspect(root)
    assert report['bank_certified_locked']
    assert all(row['verified_locked_parameters'] for row in report['post_selection_attempts'])
    assert [row['count'] for row in report['unique_eligible_with_verified_locked_parameters']] == [1, 1]


def test_parameter_drift_does_not_count_collection(tmp_path):
    root, fixtures, _ = fixture_run(tmp_path)
    make_attempt(root, fixtures[0], 'collection/train0/vmc', phase='collection', x=[0.], gain=9)
    report = inspect(root)
    assert report['bank_certified_locked']
    assert not report['unique_eligible_with_verified_locked_parameters']
    assert 'executed_parameters_differ_from_selected_search_candidate' in report['post_selection_attempts'][0]['errors']


def test_partial_candidate_and_premature_marker_cannot_lock(tmp_path):
    root, _, _ = fixture_run(tmp_path)
    execution = root/'search/corner/vmc/c01/1/execution.json'
    value = json.loads(execution.read_text())
    value.update(status='failed', returncode=1)
    put(execution, value)
    report = inspect(root)
    assert not report['bank_certified_locked']
    assert not report['reconstructed_groups']['corner/vmc']['candidates'][1]['verified']


def test_wrong_ranked_selection_rejected(tmp_path):
    root, _, history = fixture_run(tmp_path)
    put(root/'teacher_bank.json', {'corner/vmc': [dict(history[1], anchor_feasible=False)]})
    assert not inspect(root)['bank_certified_locked']


def test_disjoint_parameter_successes_never_combined_into_feasible_candidate(tmp_path):
    root, _, _ = fixture_run(tmp_path, successes=((True, False), (False, True)))
    report = inspect(root)
    assert report['bank_certified_locked']
    assert report['expected_infeasible_groups'] == ['corner/vmc']
    candidates = report['reconstructed_groups']['corner/vmc']['candidates']
    assert [c['independently_reconstructed']['eligible_count'] for c in candidates] == [1, 1]
    assert [c['unique_fixture_count'] for c in report['eligible_counts_per_fixed_parameter']] == [1, 1]


def test_tampered_history_score_cannot_lock(tmp_path):
    root, _, history = fixture_run(tmp_path)
    history[0]['score'] = -999.
    put(root/'search/corner/vmc/history.json', history)
    report = inspect(root)
    assert not report['bank_certified_locked']
    assert 'history_summary_mismatch_or_duplicate' in report['reconstructed_groups']['corner/vmc']['candidates'][0]['errors']


def test_deadline_snapshot_preserves_metadata_and_reports_archive_gap(tmp_path):
    root, _, _ = fixture_run(tmp_path)
    put(root/'deadline_reached.json', dict(stopped_dispatch=True, time=101.))
    before = {str(p.relative_to(root)): status.sha(p) for p in terminal.metadata_paths(root)}
    output = tmp_path/'review'
    report = terminal.run(root, output, now=101.)
    assert report['snapshot_kind'] == 'terminal_evidence'
    assert report['status']['total_definitions'] == 3
    assert report['status']['attempts_total'] == 4
    assert {str(p.relative_to(root)): status.sha(p) for p in terminal.metadata_paths(root)} == before
    gap = next(x for x in report['archive_metadata_inventory'] if x['path'] == 'deadline_reached.json')
    assert not gap['automatic_final_reports_scope']
    assert not gap['exact_final_reports_copy_present']
    with pytest.raises(ValueError):
        terminal.run(root, output)


def test_unstable_snapshot_never_certifies_bank(tmp_path):
    root, _, _ = fixture_run(tmp_path)
    report = terminal.closeout(root, status.summarize(root), stable=False)
    assert not report['bank_certified_locked']


def test_source_drift_prevents_lock_certification(tmp_path):
    root, _, _ = fixture_run(tmp_path)
    (root/'source/example.py').write_text('# changed source\n')
    report = terminal.run(root, tmp_path/'review')
    assert not report['closeout']['source_manifest_verified']
    assert not report['closeout']['bank_certified_locked']


def test_validation_before_search_finished_is_not_locked_evidence(tmp_path):
    root, fixtures, _ = fixture_run(tmp_path)
    make_attempt(root, fixtures[2], 'validation/validation0/vmc', phase='validation', x=[0.], gain=0)
    path = root/'validation/validation0/vmc/execution.json'
    execution = json.loads(path.read_text()); execution['started'] = 0.
    put(path, execution)
    report = inspect(root)
    assert not report['unique_eligible_with_verified_locked_parameters']
    assert 'post_selection_dispatch_precedes_complete_search_or_time_missing' in report['post_selection_attempts'][0]['errors']


def test_model_changes_across_candidates_prevent_lock(tmp_path):
    root, _, _ = fixture_run(tmp_path)
    path = root/'search/corner/vmc/c01/0/audit.json'
    audit = json.loads(path.read_text()); audit['model_sha256'] = 'b'*64
    put(path, audit)
    report = inspect(root)
    assert not report['compiled_model_metadata_consistent_across_methods_and_candidates']
    assert not report['bank_certified_locked']
