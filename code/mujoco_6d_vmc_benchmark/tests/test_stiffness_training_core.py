"""Unit tests for the pre-training safety and reproducibility contracts."""

import sys
from pathlib import Path

import numpy as np


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
from stiffness_training_core import (  # noqa: E402
    StiffnessActionConfig,
    action_target_to_kappa,
    action_to_kappa,
    deployment_observation,
    latin_hypercube,
    scenario_from_unit,
    training_contract,
)


def test_action_target_obeys_six_channel_safety_bounds():
    config = StiffnessActionConfig()
    target = action_target_to_kappa(np.ones(6), config)
    assert np.all(target <= np.asarray(config.maximum_kappa))
    assert np.all(target >= np.asarray(config.minimum_kappa))


def test_action_rate_limiter_prevents_an_instantaneous_stiffness_jump():
    config = StiffnessActionConfig(update_hz=25.0, max_log_rate_per_s=1.0)
    previous = np.asarray(config.base_kappa)
    result = action_to_kappa(np.ones(6), previous, config)
    np.testing.assert_allclose(np.log(result / previous), np.full(6, 1.0 / 25.0))


def test_latin_hypercube_is_deterministic_and_bounded():
    first = latin_hypercube(8, 10, 17)
    second = latin_hypercube(8, 10, 17)
    np.testing.assert_allclose(first, second)
    assert np.all((0.0 <= first) & (first <= 1.0))


def test_manifest_scenario_stays_inside_calibrated_fixture_range():
    scenario = scenario_from_unit(np.full(10, 0.5))
    assert 0.155 <= scenario["rod_stroke_m"] <= 0.180
    assert 0.538 <= scenario["rod_height_m"] <= 0.542
    assert 1.040 <= scenario["rod_start_time_s"] <= 1.120
    assert len(scenario["initial_kappa_vector"]) == 6


def test_deployment_observation_is_51d_and_excludes_contact_truth():
    observation = deployment_observation(
        position_error_world=np.zeros(3), orientation_error_world=np.zeros(3), twist_error_world=np.zeros(6),
        joint_position=np.zeros(7), joint_velocity=np.zeros(7), carriage_displacement=np.zeros(6),
        carriage_velocity=np.zeros(6), applied_torque_ratio=np.zeros(7), previous_action=np.zeros(6),
    )
    assert observation.shape == (51,)
    contract = training_contract()
    assert "rod_contact" in contract["excluded_privileged_diagnostics"]
    assert "rod_contact" not in contract["observation_fields"]
