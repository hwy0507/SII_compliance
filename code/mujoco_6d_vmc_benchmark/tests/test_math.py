"""Small dependency-free checks for VMC geometry and saturation utilities."""

import importlib.util
import sys
from pathlib import Path

import numpy as np


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_benchmark.py"
SPEC = importlib.util.spec_from_file_location("vmc_benchmark", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_saturated_spring_is_bounded_and_odd():
    stiffness = np.array([100.0, 100.0])
    saturation = np.array([5.0, 2.0])
    error = np.array([1e3, -1e3])
    force = MODULE.saturated_spring(stiffness, saturation, error)
    np.testing.assert_allclose(force, [5.0, -2.0], atol=1e-6)


def test_so3_log_returns_zero_for_identity():
    np.testing.assert_allclose(MODULE.so3_log(np.eye(3)), 0.0, atol=1e-9)


def test_single_kappa_scales_translation_and_rotation_blocks():
    controller = MODULE.SixDVirtualCarriage(MODULE.VMCConfig(), 2.0, np.zeros(3), np.eye(3))
    np.testing.assert_allclose(controller.stiffness[:3], 2.0 * MODULE.VMCConfig().k_translation_base)
    np.testing.assert_allclose(controller.stiffness[3:], 2.0 * MODULE.VMCConfig().k_rotation_base)


def test_torque_feasible_scale_respects_each_joint_limit():
    bias = np.zeros(MODULE.ARM_DOF)
    contribution = np.ones(MODULE.ARM_DOF) * 2.0 * MODULE.TORQUE_LIMITS
    scale = MODULE.torque_feasible_scale(bias, contribution)
    np.testing.assert_allclose(scale, 0.5)
    assert np.all(np.abs(bias + scale * contribution) <= MODULE.TORQUE_LIMITS)


def test_torque_rate_limiter_caps_the_per_step_change():
    config = MODULE.VMCConfig(max_torque_rate_proximal=100.0, max_torque_rate_distal=20.0)
    limited = MODULE.rate_limit_torque(np.zeros(MODULE.ARM_DOF), np.full(MODULE.ARM_DOF, 10.0), 0.01, config)
    np.testing.assert_allclose(limited[:4], 1.0)
    np.testing.assert_allclose(limited[4:], 0.2)
