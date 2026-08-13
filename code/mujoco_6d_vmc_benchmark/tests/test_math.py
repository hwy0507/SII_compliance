"""Small dependency-free checks for VMC geometry and saturation utilities."""

import importlib.util
from pathlib import Path

import numpy as np


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_benchmark.py"
SPEC = importlib.util.spec_from_file_location("vmc_benchmark", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
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
