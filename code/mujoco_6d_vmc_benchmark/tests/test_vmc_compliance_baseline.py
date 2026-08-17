"""Unit tests for the twist-layer VMC compliance baseline (no MuJoCo needed)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from vmc_compliance_baseline import (  # noqa: E402
    RL_DT,
    VMCComplianceBaseline,
    VMCComplianceConfig,
)


def test_zero_error_gives_zero_action():
    controller = VMCComplianceBaseline(VMCComplianceConfig())
    for _ in range(50):
        action = controller.act(np.zeros(6), np.zeros(6))
    assert action[0] == 1.0
    assert np.allclose(action[1:], 0.0, atol=1e-12)


def test_deadband_suppresses_standing_tracking_error():
    controller = VMCComplianceBaseline(VMCComplianceConfig())
    # Below the deadband with no velocity mismatch: no response.
    standing = np.zeros(6)
    standing[0] = 0.005
    standing[3] = 0.02
    for _ in range(50):
        action = controller.act(standing, np.zeros(6))
    assert np.allclose(action[1:], 0.0, atol=1e-12)
    # The same standing error plus a collision-sized velocity pulse yields.
    pulse = np.zeros(6)
    pulse[0] = 0.08
    responded = False
    for _ in range(10):
        action = controller.act(standing, pulse)
        responded = responded or abs(action[1]) > 1e-3
    assert responded


def test_error_pulse_yields_then_rejoins():
    controller = VMCComplianceBaseline(VMCComplianceConfig())
    error = np.zeros(6)
    error[1] = -0.02  # rod pushes from -y
    peak_yield = 0.0
    for step in range(400):
        if step < 10:
            action = controller.act(error, np.zeros(6))
            peak_yield = max(peak_yield, abs(action[2]))
        else:
            action = controller.act(np.zeros(6), np.zeros(6))
    assert peak_yield > 1e-4, "collision error must produce a yielding twist"
    assert abs(action[2]) < 1e-4, "offset must rejoin after the error vanishes"


def test_offset_is_bounded_under_persistent_error():
    controller = VMCComplianceBaseline(VMCComplianceConfig())
    error = np.zeros(6)
    error[1] = -0.05
    max_offset = 0.0
    for _ in range(2000):
        controller.act(error, np.zeros(6))
        max_offset = max(max_offset, abs(controller.offset[1]))
    # Saturating spring bounds the offset; 0.4 m is a generous upper bound.
    assert max_offset < 0.4
    # Steady state tracks the error scale (both drives saturate alike).
    assert 0.01 < max_offset < 0.06
    assert np.all(np.isfinite(controller.offset))


def test_gated_variant_is_softer_during_contact():
    strict = VMCComplianceBaseline(VMCComplianceConfig(gated_stiffness_scale=1.0))
    gated = VMCComplianceBaseline(VMCComplianceConfig(gated_stiffness_scale=0.4))
    error = np.zeros(6)
    error[1] = -0.02
    for _ in range(10):
        yield_strict = strict.act(error, np.zeros(6))[2]
        yield_gated = gated.act(error, np.zeros(6))[2]
    assert abs(yield_gated) > abs(yield_strict), "softer gate must yield more during contact"


def test_npz_roundtrip(tmp_path: Path):
    controller = VMCComplianceBaseline(VMCComplianceConfig(kappa_translation=2.5, zeta=0.8))
    path = tmp_path / "vmc_baseline.npz"
    controller.save_npz(path)
    restored = VMCComplianceBaseline.from_npz(path)
    assert restored.config.kappa_translation == 2.5
    assert restored.config.zeta == 0.8
    # Checkpoints carry parameters only; rollouts always start from reset.
    error = np.zeros(6)
    error[1] = -0.02
    controller.reset()
    restored.reset()
    for _ in range(20):
        a = controller.act(error, np.zeros(6))
        b = restored.act(error, np.zeros(6))
    assert np.allclose(a, b)


def test_invalid_config_rejected():
    with pytest.raises(ValueError):
        VMCComplianceConfig(zeta=-1.0)


def test_rl_step_consistency():
    controller = VMCComplianceBaseline(VMCComplianceConfig())
    error = np.zeros(6)
    error[1] = -0.02
    action = controller.act(error, np.zeros(6))
    assert np.isfinite(action).all()
    assert RL_DT == pytest.approx(0.040)
