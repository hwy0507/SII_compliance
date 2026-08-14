"""Timing checks for the physical rod perturbation fixture."""

import importlib.util
import sys
from pathlib import Path

import numpy as np


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
MODULE_PATH = SCRIPTS_DIR / "run_rod_perturbation_benchmark.py"
SPEC = importlib.util.spec_from_file_location("rod_perturbation_benchmark", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_rod_motion_is_zero_outside_the_scheduled_window():
    assert MODULE.rod_motion(MODULE.ROD_START_TIME_S, 0.16) == (0.0, 0.0)
    assert MODULE.rod_motion(MODULE.ROD_END_TIME_S, 0.16) == (0.0, 0.0)


def test_rod_holds_peak_stroke_before_smooth_retraction():
    displacement, velocity = MODULE.rod_motion((MODULE.ROD_PEAK_TIME_S + MODULE.ROD_RETRACT_TIME_S) / 2.0, 0.16)
    np.testing.assert_allclose(displacement, 0.16)
    np.testing.assert_allclose(velocity, 0.0)


def test_rod_retracts_before_gripper_closure():
    assert MODULE.ROD_END_TIME_S < MODULE.GRASP_TIME_S


def test_repeated_rod_motion_has_separate_full_profiles():
    start = 0.80
    period = 1.20
    first_peak, _ = MODULE.rod_motion(start + 0.30, 0.16, start, cycles=5, cycle_period_s=period)
    third_peak, _ = MODULE.rod_motion(start + 2 * period + 0.30, 0.16, start, cycles=5, cycle_period_s=period)
    between, _ = MODULE.rod_motion(start + 0.90, 0.16, start, cycles=5, cycle_period_s=period)
    np.testing.assert_allclose(first_peak, 0.16)
    np.testing.assert_allclose(third_peak, 0.16)
    np.testing.assert_allclose(between, 0.0)


def test_shared_six_channel_stiffness_ramps_after_rod_release():
    contact = 0.20
    recovery = 1.60
    ramp = 0.16
    assert MODULE.stiffness_schedule(MODULE.ROD_END_TIME_S, contact, recovery, ramp) == contact
    midpoint = MODULE.stiffness_schedule(MODULE.ROD_END_TIME_S + ramp / 2.0, contact, recovery, ramp)
    assert contact < midpoint < recovery
    assert MODULE.stiffness_schedule(MODULE.ROD_END_TIME_S + ramp, contact, recovery, ramp) == recovery


def test_stiffness_schedule_preserves_a_single_shared_scalar_without_a_phase_change():
    assert MODULE.stiffness_schedule(0.5, 1.25, 1.25, 0.08) == 1.25
    assert MODULE.stiffness_schedule(3.0, 1.25, 1.25, 0.08) == 1.25


def test_explicit_carriage_uses_one_shared_three_axis_body():
    """The physical prototype must be one 3D mass, not three unrelated masses."""
    source = MODULE_PATH.read_text()
    assert '<body name="explicit_carriage"' in source
    assert 'name="explicit_carriage_x_slide"' in source
    assert 'name="explicit_carriage_y_slide"' in source
    assert 'name="explicit_carriage_z_slide"' in source
    assert 'explicit_carriage_body_id' in source


def test_rod_height_is_an_explicit_recorded_fixture_variable():
    """Geometry changes must be traceable rather than hidden in scene XML."""
    source = MODULE_PATH.read_text()
    assert 'parser.add_argument(\n        "--rod-height"' in source
    assert '"height_m": rod_height_m' in source
    assert 'rod_height_m: float = 0.540' in source


def test_explicit_rotational_carriage_is_a_ball_joint_child_of_translation_body():
    """The physical 6D prototype must share the translational carriage pose."""
    source = MODULE_PATH.read_text()
    assert '<body name="explicit_rotation_carriage"' in source
    assert 'name="explicit_carriage_ball" type="ball"' in source
    assert 'explicit_rotation_carriage_body_id' in source
    assert 'peak_explicit_rotational_spring_moment_nm' in source


def test_rotational_damping_override_reaches_the_episode_interface():
    """CLI-only tuning knobs are invalid unless run_episode accepts them."""
    source = MODULE_PATH.read_text()
    # Do not freeze the entire signature: other independently valid controls
    # (for example controller_mode) may follow this argument.
    assert 'rotational_damping_ratio: float | None = None,' in source
    assert 'rotational_damping_ratio=args.rotational_damping_ratio' in source


def test_phase_analysis_marks_rejoin_after_contact_release_and_hold_window():
    time = np.arange(120, dtype=float) * 0.004
    contact = np.zeros(len(time), dtype=bool)
    contact[10:15] = True
    error = np.full(len(time), 0.010)
    error[15:] = 0.001
    phase, summary = MODULE._phase_analysis(time, contact, error, grasp_time_s=0.40)
    assert summary["primary_contact_start_s"] == time[10]
    assert summary["primary_contact_release_s"] == time[14]
    assert summary["rejoin_time_s"] == time[15]
    assert summary["secondary_contact_count"] == 0
    assert phase[10] == 1
    assert phase[15] == 3


def test_phase_analysis_records_secondary_contact_windows():
    time = np.arange(140, dtype=float) * 0.004
    contact = np.zeros(len(time), dtype=bool)
    contact[10:14] = True
    contact[50:54] = True
    error = np.full(len(time), 0.001)
    _, summary = MODULE._phase_analysis(time, contact, error, grasp_time_s=0.40)
    assert summary["secondary_contact_count"] == 1
    assert summary["secondary_contact_windows_s"] == [[time[50], time[53]]]


def test_phase_analysis_merges_solver_scale_contact_gaps_before_counting_secondary_contact():
    time = np.arange(140, dtype=float) * 0.004
    contact = np.zeros(len(time), dtype=bool)
    contact[10:14] = True
    contact[16:20] = True  # 12 ms gap: one physical collision episode.
    error = np.full(len(time), 0.001)
    _, summary = MODULE._phase_analysis(time, contact, error, grasp_time_s=0.40)
    assert summary["secondary_contact_count"] == 0
    assert summary["contact_windows_s"] == [[time[10], time[19]]]
