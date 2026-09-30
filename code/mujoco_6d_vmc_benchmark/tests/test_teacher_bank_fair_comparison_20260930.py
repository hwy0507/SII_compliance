"""Fixed-parameter comparison must not hide exposure failures or missing data."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import teacher_bank_fair_comparison_20260930 as comparison


def make_review(tmp_path, *, locked=True, missing_method=False, model_mismatch=False,
                missing_task=False, short_method=False, parameter_drift=False):
    root = tmp_path/'review'
    snapshot = root/'metadata_snapshot'
    snapshot.mkdir(parents=True)
    hashes = {}
    def put(name, value):
        path = snapshot/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        hashes[name] = comparison.sha(path)
    methods = ['vmc', 'admittance', 'impedance']
    fixture = dict(id='train0', category='person', split='train')
    put('plan.json', dict(methods=methods, categories=['person'], duration_s=55., validation_indices=[]))
    put('fixtures.json', [fixture])
    attempts, post, groups = [], [], {}
    for method in methods:
        groups['person/'+method] = dict(best_complete_candidate=dict(index=0, x=[0.]),
            selected_controller_config={'gain':1.}, candidates=[dict(index=0, anchors=[])])
        if missing_method and method == 'impedance': continue
        folder = 'collection/train0/'+method
        audit = dict(task=True, strict=True, exposure={'passed':False}, eligible=False,
            model_sha256=('b'*64 if model_mismatch and method == 'impedance' else 'a'*64),
            rmse_m=.02, peak_torque_nm=40., peak_speed_mps=.1,
            failure_reasons=['required_contact_missing'])
        if missing_task and method == 'vmc': audit.pop('task')
        full = not (short_method and method == 'impedance')
        put(folder+'/audit.json', audit)
        put(folder+'/request.json', dict(fixture=fixture, method=method, phase='collection',
            x=[9.] if parameter_drift and method == 'vmc' else [0.], teacher={'gain':1.}))
        put(folder+'/execution.json', dict(status='completed', returncode=0))
        put(folder+'/rollout.json', dict(task_success=True, strict_success=True, physical_valid=True,
            full_task_horizon_completed=full, execution_complete=full, abort_reason=None if full else 'penetration',
            metrics=dict(timestep_sample_counts={'.0001':550000 if full else 100000},
                position_rmse_3d_m=.02, generalized_actuator_torque_peak_nm=40., linear_speed_peak_mps=.1)))
        attempts.append(dict(folder=folder, status='physical_failure'))
        post.append(dict(folder=folder, verified_locked_parameters=True))
    report = dict(metadata_sha256=hashes, closeout=dict(bank_certified_locked=locked,
        reconstructed_groups=groups, post_selection_attempts=post), status=dict(attempts=attempts))
    (root/'review.json').write_text(json.dumps(report))
    return root


def run(root):
    return comparison.export(root, root.parent/'export', comparison.sha(root/'review.json'))


def test_task_success_exposure_failure_remain_separate_and_in_metrics(tmp_path):
    root = make_review(tmp_path)
    result = run(root)
    rows = [r for r in result['method_summary'] if r['scope'] == 'collection']
    assert len(rows) == 3
    for row in rows:
        assert row['task_true'] == 1 and row['strict_true'] == 1
        assert row['exposure_false'] == 1 and row['eligible_false'] == 1
        assert row['rmse_m_n'] == 1 and row['rmse_m_mean'] == .02
    assert len((root.parent/'export/retained_failures.csv').read_text().splitlines()) == 4


def test_missing_task_is_unknown_never_inferred_from_strict(tmp_path):
    result = run(make_review(tmp_path, missing_task=True))
    row = next(r for r in result['rows'] if r['method'] == 'vmc')
    assert row['task'] == 'unknown' and row['strict'] is True
    summary = next(r for r in result['method_summary'] if r['method'] == 'vmc' and r['scope'] == 'collection')
    assert summary['task_unknown'] == 1 and summary['task_true'] == 0


@pytest.mark.parametrize('option', ['missing_method', 'model_mismatch', 'parameter_drift'])
def test_partial_model_or_parameter_mismatch_excluded_from_paired_comparison(tmp_path, option):
    result = run(make_review(tmp_path, **{option:True}))
    assert all(row['paired_episodes'] == 0 for row in result['method_summary'])
    assert not any(row['paired_metric_episode'] for row in result['rows'])


def test_one_short_abort_excludes_all_methods_from_same_duration_metrics(tmp_path):
    result = run(make_review(tmp_path, short_method=True))
    rows = [r for r in result['method_summary'] if r['scope'] == 'collection']
    assert all(r['paired_episodes'] == 1 for r in rows)
    assert all(r['rmse_m_n'] == 0 for r in rows)
    assert next(r for r in result['rows'] if r['method'] == 'impedance')['abort'] == 'penetration'


def test_unlocked_review_refuses_method_results_but_preserves_details(tmp_path):
    result = run(make_review(tmp_path, locked=False))
    assert result['method_summary'] == []
    assert result['locked_results_refused_reason'] == 'bank_not_certified_locked'
    assert len(result['rows']) == 3 and result['definitions'] == 1


def test_snapshot_tampering_detected(tmp_path):
    root = make_review(tmp_path)
    path = root/'metadata_snapshot/collection/train0/vmc/audit.json'
    path.write_text('{}')
    with pytest.raises(ValueError, match='Snapshot SHA mismatch'):
        run(root)


def test_review_hash_required(tmp_path):
    root = make_review(tmp_path)
    with pytest.raises(ValueError, match='Review SHA256 mismatch'):
        comparison.export(root, tmp_path/'export', '0'*64)


@pytest.mark.parametrize('defect', ['missing', 'mismatch'])
def test_one_method_metric_gap_excludes_entire_fixture_from_all_metric_means(tmp_path, defect):
    root = make_review(tmp_path)
    relative = 'collection/train0/vmc/rollout.json'
    path = root/'metadata_snapshot'/relative
    rollout = json.loads(path.read_text())
    if defect == 'missing':
        rollout['metrics'].pop('position_rmse_3d_m')
    else:
        rollout['metrics']['position_rmse_3d_m'] = .5
    path.write_text(json.dumps(rollout))
    review_path = root/'review.json'
    review = json.loads(review_path.read_text())
    review['metadata_sha256'][relative] = comparison.sha(path)
    review_path.write_text(json.dumps(review))
    result = run(root)
    summaries = [r for r in result['method_summary'] if r['scope'] == 'collection']
    assert len(summaries) == 3
    for row in summaries:
        assert row['paired_episodes'] == 1 and row['task_true'] == 1
        assert row['exposure_false'] == 1
        assert row['same_full_duration_metric_episodes'] == 0
        for metric in ('rmse_m', 'peak_torque_nm', 'peak_speed_mps'):
            assert row[metric+'_n'] == 0
            assert row[metric+'_mean'] is None and row[metric+'_max'] is None
    for row in result['rows']:
        assert row['pair_state'] == 'paired' and not row['paired_metric_episode']
        assert 'missing_or_unverified_metric_in_pair:vmc:rmse_m' in row['metric_exclusion_reason']
    vmc = next(r for r in result['rows'] if r['method'] == 'vmc')
    assert vmc['rmse_m'] is None and vmc['peak_torque_nm'] == 40.
    assert result['pairing'][0]['same_full_duration_all_methods']
    assert not result['pairing'][0]['all_three_metrics_verified_for_all_methods']
