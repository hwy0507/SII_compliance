"""Selection must account for failed tasks and never silently drop budget rows."""
import numpy as np
import pytest

from run_classical_fixed_budget_20260923 import average_ranks, candidates, select, validation_fixtures, verify_model_pairing


def example():
    configurations = candidates()
    fixtures = [dict(seed=s) for s in (9300,9301,9302)]
    rows = [dict(candidate=c, fixture=f, strict_success=False, task_success=True,
                 tracking_rmse_25hz_m=.1, actuator_torque_peak_nm=35.,
                 linear_speed_peak_substep_mps=.12)
            for c in configurations for f in fixtures]
    return configurations, fixtures, rows


def test_task_failures_with_low_motion_cannot_beat_success():
    configurations, fixtures, rows = example()
    winner = configurations[2]['id']
    for row in rows:
        if row['candidate']['id'] == winner:
            row.update(strict_success=True, tracking_rmse_25hz_m=.5)
    result = select(rows, configurations, fixtures)
    assert result['impedance']['selected']['id'] == winner
    assert result['impedance']['reliable_on_all_development_conditions']
    assert not result['admittance']['reliable_on_all_development_conditions']


def test_execution_errors_and_missing_or_duplicate_rows_reject_selection():
    configurations, fixtures, rows = example()
    for bad in (rows[:-1], rows+[rows[0]]):
        with pytest.raises(ValueError, match='Incomplete or duplicate'):
            select(bad, configurations, fixtures)
    rows[0]['execution_error'] = 'timeout'
    with pytest.raises(ValueError, match='Execution failures'):
        select(rows, configurations, fixtures)


def test_nonfinite_scores_rejected():
    configurations, fixtures, rows = example()
    rows[0]['actuator_torque_peak_nm'] = float('nan')
    with pytest.raises(ValueError, match='Nonfinite'):
        select(rows, configurations, fixtures)


def test_preregistered_budget_holdout_and_tie_ranks():
    configurations, fixtures, rows = example()
    assert len(configurations) == 16
    assert len(rows) == 48
    assert not {f['seed'] for f in fixtures} & {f['seed'] for f in validation_fixtures()}
    np.testing.assert_array_equal(average_ranks([4., 2., 2., 1.]), [4., 2.5, 2.5, 1.])


def test_model_pairing_rejects_cross_method_physics_changes():
    rows = [dict(fixture=dict(seed=9300), model_mjb_sha256=value) for value in ('abc','abc')]
    verify_model_pairing(rows)
    rows[1]['model_mjb_sha256'] = 'changed'
    with pytest.raises(ValueError, match='Compiled physical model differs'):
        verify_model_pairing(rows)
