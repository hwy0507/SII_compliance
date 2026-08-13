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
