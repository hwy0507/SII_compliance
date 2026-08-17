"""Unit tests for the spring--carriage VMC compliance baseline (no MuJoCo)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from vmc_compliance_baseline import (  # noqa: E402
    KAPPA_6D,
    RL_DT,
    SpringCarriageVMC,
    SpringCarriageConfig,
    VMCComplianceAdapter,
    load_controller,
)


def test_zero_error_gives_zero_action():
    controller = SpringCarriageVMC(SpringCarriageConfig())
    for _ in range(50):
        action = controller.act(np.zeros(6), np.zeros(6))
    assert action[0] == 1.0
    assert np.allclose(action[1:], 0.0, atol=1e-12)


def test_proprioceptive_collision_pushes_carriage_away_from_rod():
    controller = SpringCarriageVMC(SpringCarriageConfig())
    # Rod presses from -y: the WBC pose error (nominal - ee) turns negative in y.
    error = np.zeros(6)
    error[1] = -0.02
    peak_yield = 0.0
    for step in range(400):
        if step < 10:
            action = controller.act(error, np.zeros(6))
            peak_yield = max(peak_yield, float(action[2]))
        else:
            action = controller.act(np.zeros(6), np.zeros(6))
    assert peak_yield > 1e-4, "collision error must push the carriage (+y yield)"
    assert abs(action[2]) < 1e-4, "carriage must rejoin after the error vanishes"


def test_force_feedback_uses_measured_wrench_directly():
    controller = SpringCarriageVMC(SpringCarriageConfig(drive_source="force_feedback"))
    wrench = np.zeros(6)
    wrench[1] = 20.0  # rod pushes the hand toward +y
    peak_yield = 0.0
    for step in range(400):
        active = step < 10
        action = controller.act(
            np.zeros(6), np.zeros(6), contact_wrench_world=wrench if active else np.zeros(6))
        if active:
            peak_yield = max(peak_yield, float(action[2]))
    assert peak_yield > 1e-4, "a +y wrench must yield toward +y"
    assert abs(action[2]) < 1e-4


def test_force_feedback_requires_wrench():
    controller = SpringCarriageVMC(SpringCarriageConfig(drive_source="force_feedback"))
    with pytest.raises(ValueError):
        controller.act(np.zeros(6), np.zeros(6))


def test_proprioceptive_rejects_wrench_input():
    adapter = VMCComplianceAdapter(SpringCarriageVMC(SpringCarriageConfig()))
    with pytest.raises(ValueError):
        adapter.act(np.zeros(7), np.zeros(7), np.zeros(6),
                    pose_error=np.zeros(6), twist_error=np.zeros(6),
                    contact_wrench_world=np.zeros(6))


def test_carriage_offset_bounded_and_speed_limited():
    controller = SpringCarriageVMC(SpringCarriageConfig())
    error = np.zeros(6)
    error[1] = -0.05
    for _ in range(4000):
        action = controller.act(error, np.zeros(6))
    assert abs(controller.offset[1]) < 0.4
    assert np.all(np.abs(controller.offset_rate) <= controller.speed_limits + 1e-12)
    assert np.all(np.isfinite(controller.offset))


def test_frozen_kappa_and_config_defaults():
    config = SpringCarriageConfig()
    assert config.kappa_6d == KAPPA_6D
    assert config.k_translation_base == pytest.approx(220.0)
    assert config.virtual_mass == pytest.approx(1.25)
    assert config.carriage_drive_k_translation == pytest.approx(75.0)
    assert config.zeta == pytest.approx(1.05)


def test_invalid_config_rejected():
    with pytest.raises(ValueError):
        SpringCarriageConfig(drive_source="mystic")
    with pytest.raises(ValueError):
        SpringCarriageConfig(zeta=0.0)
    with pytest.raises(ValueError):
        SpringCarriageConfig(kappa_6d=(1.0, 2.0, 3.0))


def test_npz_roundtrip(tmp_path: Path):
    controller = SpringCarriageVMC(SpringCarriageConfig(drive_source="force_feedback"))
    path = tmp_path / "spring_carriage.npz"
    controller.save_npz(path)
    restored = SpringCarriageVMC.from_npz(path)
    assert restored.config.drive_source == "force_feedback"
    assert restored.config.kappa_6d == KAPPA_6D
    wrench = np.zeros(6)
    wrench[1] = 10.0
    controller.reset()
    restored.reset()
    for _ in range(10):
        a = controller.act(np.zeros(6), np.zeros(6), contact_wrench_world=wrench)
        b = restored.act(np.zeros(6), np.zeros(6), contact_wrench_world=wrench)
    assert np.allclose(a, b)
    loaded = load_controller(path)
    assert isinstance(loaded, VMCComplianceAdapter)


def test_adapter_normalization():
    adapter = VMCComplianceAdapter(SpringCarriageVMC(SpringCarriageConfig()))
    adapter.set_yield_limits(0.16, 0.60)
    error = np.zeros(6)
    error[1] = -0.03
    action = adapter.act(np.zeros(7), np.zeros(7), np.zeros(6),
                         pose_error=error, twist_error=np.zeros(6))
    assert action.bounded_filter_action.shape == (7,)
    assert action.wbc_scale == 1.0
    assert np.all(np.abs(action.bounded_filter_action) <= 1.0)
    assert RL_DT == pytest.approx(0.040)


def test_constant_pull_reaches_viscous_equilibrium():
    controller = SpringCarriageVMC(SpringCarriageConfig(carriage_drive="constant_force", constant_pull_n=1.0))
    nominal = np.zeros(6)
    nominal[0] = 0.05
    for _ in range(3000):
        controller.act(np.zeros(6), np.zeros(6), nominal_twist=nominal)
    # Steady state: pull, viscous friction, and the EE-coupling reaction on
    # the carriage offset balance, so the carriage settles at the nominal
    # speed with a bounded sub-mm offset (verified analytically: the spring
    # absorbs b*|v_nominal| - pull).
    assert controller.offset_rate[0] == pytest.approx(0.0, abs=1e-6)
    assert abs(controller.offset[0]) < 1.0e-3
    assert np.all(np.isfinite(controller.offset))


def test_constant_pull_vanishes_when_nominal_rests():
    controller = SpringCarriageVMC(SpringCarriageConfig(carriage_drive="constant_force"))
    for _ in range(300):
        action = controller.act(np.zeros(6), np.zeros(6), nominal_twist=np.zeros(6))
    assert np.allclose(action[1:], 0.0, atol=1e-9)
    assert np.allclose(controller.offset, 0.0, atol=1e-9)


def test_constant_pull_requires_nominal_twist():
    controller = SpringCarriageVMC(SpringCarriageConfig(carriage_drive="constant_force"))
    with pytest.raises(ValueError):
        controller.act(np.zeros(6), np.zeros(6))


def test_constant_pull_collision_still_yields():
    controller = SpringCarriageVMC(SpringCarriageConfig(carriage_drive="constant_force"))
    nominal = np.zeros(6)
    nominal[0] = 0.05
    error = np.zeros(6)
    error[1] = -0.02
    peak = 0.0
    for step in range(300):
        active = step < 10
        action = controller.act(error if active else np.zeros(6), np.zeros(6),
                                nominal_twist=nominal if step < 200 else np.zeros(6))
        if active:
            peak = max(peak, float(action[2]))
    assert peak > 1e-4, "the EE coupling reaction must still yield during contact"
