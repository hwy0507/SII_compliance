"""Tests for the deployable ESN student and its safety boundary."""

import sys
from pathlib import Path

import numpy as np
import pytest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
from esn_compliance import (  # noqa: E402
    ACTION_DIMENSION,
    STUDENT_INPUT_DIMENSION,
    ComplianceESN,
    ESNConfig,
    ESNObservation,
    encode_student_observation,
    project_compliance_action,
)
from stiffness_training_core import DriveResidualActionConfig, StiffnessActionConfig  # noqa: E402


def _observation(value: float = 0.0) -> ESNObservation:
    return ESNObservation(
        joint_position=np.full(7, value), joint_velocity=np.full(7, value),
        wbc_task_twist=np.full(6, value),
    )


def test_student_observation_is_exactly_deployable_twenty_dimensions():
    encoded = encode_student_observation(_observation())
    assert encoded.shape == (STUDENT_INPUT_DIMENSION,)
    assert np.all(np.isfinite(encoded))
    contract = ComplianceESN().contract()
    assert "rod_contact" in contract["student"]["forbidden_privileged_inputs"]
    assert "rod_force" in contract["student"]["forbidden_privileged_inputs"]
    assert contract["student"]["input_fields"] == ["joint_position_7", "joint_velocity_7", "wbc_task_twist_6"]


def test_esn_reset_is_deterministic_and_never_requires_privileged_truth():
    student = ComplianceESN(ESNConfig(reservoir_size=24, seed=7))
    first = student.step(_observation(0.1))
    student.reset()
    second = student.step(_observation(0.1))
    np.testing.assert_allclose(first, second)
    assert first.shape == (ACTION_DIMENSION,)


def test_readout_fit_and_online_action_are_finite():
    student = ComplianceESN(ESNConfig(reservoir_size=16, seed=8))
    features = student.collect_features([_observation(float(index) / 100.0) for index in range(12)], washout_steps=2)
    targets = np.tile(np.linspace(-0.2, 0.2, ACTION_DIMENSION), (len(features), 1))
    student.fit_readout(features, targets)
    action = student.step(_observation(0.07))
    assert action.shape == (ACTION_DIMENSION,)
    assert np.all(np.isfinite(action))


def test_sparse_near_acyclic_reservoir_has_a_stable_ring_fallback():
    student = ComplianceESN(ESNConfig(reservoir_size=2, sparsity=0.01, seed=1))
    for _ in range(20):
        assert np.all(np.isfinite(student.step(_observation(0.2))))


def test_projection_bounds_and_rate_limits_all_seven_channels():
    stiffness = StiffnessActionConfig(update_hz=20.0, max_log_rate_per_s=1.0)
    drive = DriveResidualActionConfig(update_hz=20.0, max_log_rate_per_s=1.0)
    result = project_compliance_action(
        np.full(ACTION_DIMENSION, 50.0), stiffness.base_kappa, drive.base_recovery_drive_scale,
        stiffness_config=stiffness, drive_config=drive,
    )
    assert np.all(result.bounded_action == 1.0)
    assert np.all(np.asarray(stiffness.minimum_kappa) <= result.kappa)
    assert np.all(result.kappa <= np.asarray(stiffness.maximum_kappa))
    assert np.all(np.log(result.kappa / np.asarray(stiffness.base_kappa)) <= 1.0 / 20.0 + 1e-12)
    assert result.recovery_drive_scale <= drive.maximum_recovery_drive_scale


def test_malformed_observation_and_action_are_rejected():
    with pytest.raises(ValueError):
        ESNObservation(np.zeros(6), np.zeros(7), np.zeros(6))
    with pytest.raises(ValueError):
        project_compliance_action(np.zeros(6), np.ones(6), 14.0)
