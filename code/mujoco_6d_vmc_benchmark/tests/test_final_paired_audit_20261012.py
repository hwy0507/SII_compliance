import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from audit_local_paired_comparison_20261012 import verify_grid, verify_values


def test_grid_rejects_missing_duplicate_and_swapped_identity():
    rows = [dict(method=m, condition=c) for m in ('esn', 'rl') for c in ('a', 'b')]
    verify_grid(rows, ('esn', 'rl'), ('a', 'b'))
    for bad in (rows[:-1], rows+[rows[0]], rows[:-1]+[dict(method='rl', condition='c')]):
        with pytest.raises(ValueError, match='grid'):
            verify_grid(bad, ('esn', 'rl'), ('a', 'b'))


def test_failed_short_episode_is_valid_but_not_success():
    values = dict(task_success=False, strict_success=False, full_horizon=False,
                  rmse_mm=20., peak_torque_nm=40., peak_speed_mps=.4)
    verify_values(values, values)
    invalid = dict(values, task_success=True)
    with pytest.raises(ValueError, match='Short'):
        verify_values(invalid, invalid)
    invalid = dict(values, strict_success=True)
    with pytest.raises(ValueError, match='Strict'):
        verify_values(invalid, invalid)


def test_forged_metric_or_outcome_rejected():
    values = dict(task_success=False, strict_success=False, full_horizon=True,
                  rmse_mm=20., peak_torque_nm=40., peak_speed_mps=.4)
    with pytest.raises(ValueError, match='Metric mismatch'):
        verify_values(values, dict(values, peak_torque_nm=4.))
    with pytest.raises(ValueError, match='Outcome mismatch'):
        verify_values(values, dict(values, task_success=True))
