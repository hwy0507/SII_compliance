"""Validation plots must retain failures and use a common metric cohort."""
import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import plot_teacher_bank_validation_20260930 as plot


def report():
    rows = []
    for fixture in ('f0', 'f1'):
        for method in plot.METHODS:
            rows.append(dict(folder=fixture+'/'+method, fixture_id=fixture,
                scope=plot.SCOPE, method=method, category='passive_corner',
                paired_metric_episode=True, pair_state='paired', model_sha256='a'*64,
                same_full_duration=True, completed_execution=True, matches_locked_parameters=True,
                task=True, strict=True, exposure=method!='admittance', eligible=method!='admittance',
                rmse_m=.02, peak_torque_nm=45., peak_speed_mps=.1,
                metric_exclusion_reason=''))
    return dict(rows=rows, bank_certified_locked=True, input_review_sha256='b'*64, expected_duration_s=55.)


def extract(tmp_path, data):
    path = tmp_path/'comparison.json'
    path.write_text(json.dumps(data))
    return plot.extract(path, plot.sha(path))


def test_failure_points_retained_and_hash_required(tmp_path):
    data = extract(tmp_path, report())
    assert len(data['points']) == 6
    assert sum(not r['eligible'] for r in data['points']) == 2
    with pytest.raises(ValueError, match='SHA256'):
        plot.extract(tmp_path/'comparison.json', '0'*64)


def test_short_case_excluded_for_all_methods_but_outcomes_retained(tmp_path):
    data = report()
    for row in data['rows']:
        if row['fixture_id'] == 'f1':
            row['paired_metric_episode'] = False
            row['metric_exclusion_reason'] = 'not_same_full_duration_all_methods'
    data['rows'][-1]['same_full_duration'] = False
    result = extract(tmp_path, data)
    assert len(result['points']) == 3 and len(result['omitted_fixture_groups']) == 1
    summaries = [r for r in result['paired_outcomes'] if r['category'] == 'passive_corner']
    assert all(r['paired_n'] == 2 and r['metric_n'] == 1 for r in summaries)


@pytest.mark.parametrize('corrupt', ['cohort', 'missing_method', 'model', 'metric', 'outcome', 'unlocked', 'horizon'])
def test_invalid_metric_evidence_refused(tmp_path, corrupt):
    data = report()
    if corrupt == 'cohort': data['rows'][0]['paired_metric_episode'] = False
    elif corrupt == 'missing_method': data['rows'].pop(0)
    elif corrupt == 'model': data['rows'][0]['model_sha256'] = 'c'*64
    elif corrupt == 'metric': data['rows'][0]['rmse_m'] = None
    elif corrupt == 'outcome': data['rows'][0]['eligible'] = 'unknown'
    elif corrupt == 'unlocked': data['bank_certified_locked'] = False
    elif corrupt == 'horizon': data['expected_duration_s'] = 10.
    with pytest.raises(ValueError):
        extract(tmp_path, data)


def test_duplicate_folders_refused(tmp_path):
    data = report()
    data['rows'].append(copy.deepcopy(data['rows'][0]))
    with pytest.raises(ValueError, match='Duplicate'):
        extract(tmp_path, data)


def test_invalid_initial_attempt_is_explicitly_retained_outside_metric_plot(tmp_path):
    data = report()
    invalid = dict(folder='invalid/vmc', phase='validation', scope='excluded',
                   execution_status='failed', task='unknown', rmse_m=None)
    data['rows'].append(invalid)
    result = extract(tmp_path, data)
    assert len(result['points']) == 6
    assert result['excluded_validation_attempts'] == [invalid]
