"""Pure-array tests: no MuJoCo environment or physics integration."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from teacher_bank_exposure_20260930 import TrainingExposure, audit_saved, summarize_arrays


def fixture(category='active_long', apparatus='rod'):
    return dict(category=category, apparatus=apparatus, axis=[1., 0., 0.],
                start_s=0., press_s=.3, hold_s=.7)


def trace(observer, contact_end=.6, tangent=.02, normal=0., end=1.2, stage=3):
    for t in np.arange(0., end, .001):
        fraction=min(t/contact_end, 1.)
        observer.record(float(t), .001, 2. if t < contact_end else 0.,
                        [normal*fraction, tangent*fraction, .6], stage)
    return observer


def test_rod_slide_before_retract_and_saved_replay(tmp_path):
    observer=trace(TrainingExposure(fixture()))
    result=observer.summary()
    assert result['passed']
    assert result['diagnostics']['separation_before_retract_s'][0] == pytest.approx(.4)
    path=observer.save(tmp_path)
    assert audit_saved(path) == result
    assert audit_saved(tmp_path, fixture()) == result
    with np.load(path, allow_pickle=False) as rows:
        assert len(rows['time']) == 300
        assert rows['dt'].sum() == pytest.approx(1.2)
        assert rows['contact_duration'].sum() == pytest.approx(.6)
        assert rows['force'].shape == rows['time'].shape
    with pytest.raises(ValueError, match='fixture mismatch'):
        audit_saved(path, fixture(apparatus='person'))


def test_rod_normal_yield_does_not_count_as_tangential_slide():
    result=trace(TrainingExposure(fixture()), tangent=0., normal=.03).summary()
    assert not result['passed']
    assert 'rod_contact_tangent_displacement_below_1cm' in result['reasons']


def test_contact_ending_at_retraction_cannot_claim_self_escape():
    result=trace(TrainingExposure(fixture()), contact_end=.9).summary()
    assert not result['passed']
    assert 'no_0p2s_separation_after_slide_before_rod_retract' in result['reasons']


def test_person_can_yield_without_pre_retraction_separation():
    result=trace(TrainingExposure(fixture(apparatus='person')), contact_end=1.1,
                 normal=-.02, tangent=0.).summary()
    assert result['passed']
    assert result['diagnostics']['task_success_checked_here'] is False
    assert result['diagnostics']['person_max_signed_push_m'] > .01


@pytest.mark.parametrize('normal,tangent', [(.02, 0.), (0., .02)])
def test_person_approach_or_pure_tangent_is_not_directional_yield(normal, tangent):
    result=trace(TrainingExposure(fixture(apparatus='person')), contact_end=.6,
                 normal=normal, tangent=tangent).summary()
    assert not result['passed']
    assert result['diagnostics']['max_displacement_m'] > .019
    assert 'signed_hand_yield_along_push_below_1cm' in result['reasons']


def test_person_contact_only_after_retract_is_not_long_push():
    observer=TrainingExposure(fixture(apparatus='person'))
    for i in range(2000):
        t=i*.001
        observer.record(t, .001, 2. if 1.1 <= t < 1.8 else 0.,
                        [-.03*max(0., t-1.1), 0., .6], 3)
    result=observer.summary()
    assert not result['passed']
    assert result['diagnostics']['longest_contact_s'] > .6
    assert result['diagnostics']['person_window_contact_duration_s'] == 0.
    assert 'continuous_press_hold_hand_contact_not_over_0p4s' in result['reasons']


def test_person_displacement_after_retract_cannot_rescue_pre_retract_contact():
    observer=TrainingExposure(fixture(apparatus='person'))
    for i in range(1500):
        t=i*.001
        observer.record(t, .001, 2., [-.05*max(0., t-1.), 0., .6], 3)
    result=observer.summary()
    assert result['diagnostics']['person_window_longest_contact_s'] > .9
    assert result['diagnostics']['max_displacement_m'] > .02
    assert not result['passed']


def test_person_world_push_axis_rotates_and_raw_evidence_reaudits(tmp_path):
    config=fixture(apparatus='person')
    config['axis']=[np.cos(.7), np.sin(.7), 0.]
    observer=TrainingExposure(config)
    for i in range(1200):
        t=i*.001
        hand=-np.asarray(config['axis'])*.03*min(t, .6)
        observer.record(t, .001, 2. if t < .6 else 0., hand, 3)
    result=observer.summary()
    assert result['passed']
    path=observer.save(tmp_path)
    assert audit_saved(path, config) == result
    with np.load(path, allow_pickle=False) as saved:
        assert int(saved['schema']) == 2
        assert saved['person_physics'].shape == (1200, 6)
        assert saved['person_window_runs'].shape == (1, 8)
    arrays=observer.arrays()
    arrays['person_window_runs'][0, 7]+=.001
    with pytest.raises(ValueError, match='differ from physical evidence'):
        summarize_arrays(arrays, config)


def test_legacy_person_requires_directional_verification_but_rod_is_unchanged():
    for apparatus in ('person', 'rod'):
        config=fixture(apparatus=apparatus)
        observer=trace(TrainingExposure(config), normal=-.03, tangent=.03)
        arrays=observer.arrays()
        arrays['schema']=np.array(1)
        for key in ('person_physics', 'person_physics_fields', 'person_window_runs', 'person_window_run_fields'):
            del arrays[key]
        result=summarize_arrays(arrays, config)
        if apparatus == 'person':
            assert not result['passed']
            assert 'directional_yield_unverified' in result['reasons']
        else:
            assert result['passed']


def test_person_submillisecond_gap_splits_window_contact_runs():
    observer=TrainingExposure(fixture(apparatus='person'))
    for i in range(6000):
        t=i*.0001
        observer.record(t, .0001, 2. if i != 2501 else 0., [-t*.1, 0., .6], 3)
    result=observer.summary()
    assert not result['passed']
    assert result['diagnostics']['person_window_run_count'] == 2
    assert result['diagnostics']['person_window_longest_contact_s'] < .4


def test_person_nonfinite_or_missing_raw_substep_cannot_be_verified():
    config=fixture(apparatus='person')
    for corrupt in ('nan', 'gap'):
        arrays=trace(TrainingExposure(config), normal=-.03, tangent=0.).arrays()
        if corrupt == 'nan':
            arrays['person_physics'][100, 3]=np.nan
        else:
            arrays['person_physics']=np.delete(arrays['person_physics'], 100, axis=0)
        with pytest.raises(ValueError):
            summarize_arrays(arrays, config)


def test_person_raw_outside_contact_must_still_match_saved_display_buckets():
    config=fixture(apparatus='person')
    arrays=trace(TrainingExposure(config), normal=-.03, tangent=0.).arrays()
    arrays['person_physics'][1003, 3]+=.005  # after contact: window result alone is unchanged
    with pytest.raises(ValueError, match='physical values differ'):
        summarize_arrays(arrays, config)


def test_passive_top_placement_stage_cannot_count():
    observer=TrainingExposure(fixture('passive_corner'))
    for i in range(50):
        observer.record(i*.001, .001, 3., [0., 0., .5+i*.001], 5)
    assert not observer.summary()['passed']
    assert observer.summary()['diagnostics']['contact_duration_s'] == 0.


def test_passive_requires_upward_movement_during_contact():
    for rise, expected in ((0., False), (.001, True)):
        observer=TrainingExposure(fixture('passive_corner'))
        for i in range(20):
            observer.record(i*.001, .001, 3., [0., 0., .5+i*rise], 3)
        assert observer.summary()['passed'] is expected


def test_submillisecond_gap_not_lost_by_four_ms_sampling():
    observer=TrainingExposure(fixture())
    for i in range(12000):
        t=i*.0001
        contact=t < .6 and i != 2501
        observer.record(t, .0001, 2. if contact else 0., [0., min(t, .6)*.1, .6], 3)
    result=observer.summary()
    assert result['diagnostics']['contact_run_count'] == 2
    assert not result['passed']  # Neither of the split contact runs exceeds .4s.


def test_ball_prelaunch_contact_rejected_and_no_rebound_claim():
    config=fixture('active_short');config['start_s']=.1
    observer=trace(TrainingExposure(config), contact_end=.01)
    result=observer.summary()
    assert 'ball_contact_before_launch' in result['reasons']
    assert result['diagnostics']['ball_rebound_checked_here'] is False


def test_missing_substep_is_rejected():
    observer=TrainingExposure(fixture())
    observer.record(0., .001, 0., [0., 0., .6], 3)
    with pytest.raises(ValueError, match='every physical substep'):
        observer.record(.003, .001, 0., [0., 0., .6], 3)


@pytest.mark.parametrize('field', ['time', 'interval_end', 'dt', 'force', 'force_peak',
                                   'contact_duration', 'hand', 'stage', 'contact_runs'])
def test_nonfinite_saved_evidence_is_rejected(field):
    arrays=trace(TrainingExposure(fixture())).arrays()
    arrays[field]=arrays[field].astype(float)
    arrays[field].flat[0]=np.nan
    with pytest.raises(ValueError, match='Nonfinite'):
        summarize_arrays(arrays, fixture())


def test_aggregated_run_duration_cannot_exceed_time_interval():
    arrays=trace(TrainingExposure(fixture())).arrays()
    arrays['contact_runs'][0, 2]=.8
    with pytest.raises(ValueError, match='run ordering or duration'):
        summarize_arrays(arrays, fixture())


def test_inconsistent_saved_terminal_and_contact_totals_rejected():
    for field, value in [('terminal_time_s', np.array(1.201)),
                         ('contact_duration', np.zeros(300))]:
        arrays=trace(TrainingExposure(fixture())).arrays();arrays[field]=value
        with pytest.raises(ValueError):
            summarize_arrays(arrays, fixture())
