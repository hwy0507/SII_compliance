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
