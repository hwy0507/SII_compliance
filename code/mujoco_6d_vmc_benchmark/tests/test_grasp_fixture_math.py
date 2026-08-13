"""Dependency-light checks for the physical grasp-and-impact fixture utilities."""

import importlib.util
import sys
from pathlib import Path

import numpy as np


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
MODULE_PATH = SCRIPTS_DIR / "run_grasp_impact_benchmark.py"
SPEC = importlib.util.spec_from_file_location("grasp_impact_benchmark", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_smoothstep_has_zero_slope_at_segment_boundaries():
    assert MODULE.smoothstep(0.0) == (0.0, 0.0)
    assert MODULE.smoothstep(1.0) == (1.0, 0.0)


def test_smoothstep_clamps_outside_trajectory_segment():
    np.testing.assert_allclose(MODULE.smoothstep(-3.0), (0.0, 0.0))
    np.testing.assert_allclose(MODULE.smoothstep(4.0), (1.0, 0.0))


def test_gripper_closes_only_after_the_grasp_phase_starts():
    assert MODULE.PickLiftCarryReference.gripper_target(MODULE.GRASP_TIME_S) == 0.04
    assert MODULE.PickLiftCarryReference.gripper_target(MODULE.GRASP_TIME_S + 1.0) == 0.0


def test_impact_is_scheduled_before_gripper_closure():
    assert MODULE.IMPACT_TIME_S < MODULE.GRASP_TIME_S
