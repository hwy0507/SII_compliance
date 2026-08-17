"""Tests for the Direct ESN primary compliance controller contract."""

import sys
from pathlib import Path

import numpy as np

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from direct_esn_compliance import (  # noqa: E402
    DirectESNConfig,
    DirectESNController,
    build_privileged_teacher_trace,
    privileged_teacher_action,
)
from esn_compliance import ESNObservation  # noqa: E402


def _observation(value: float = 0.0) -> ESNObservation:
    return ESNObservation(np.full(7, value), np.full(7, value), np.full(6, value))


def test_direct_esn_zero_readout_is_fixed_wbc_and_uses_no_privileged_input():
    controller = DirectESNController(DirectESNConfig(reservoir_size=24, seed=4))
    action = controller.act(np.zeros(7), np.zeros(7), np.zeros(6))
    assert action.wbc_scale == 1.0
    np.testing.assert_allclose(action.yielding_twist, 0.0)
    contract = controller.contract()
    assert contract["esn_role"].startswith("primary")
    assert contract["ppo_used_in_proposed"] is False
    assert "contact_force" in contract["forbidden_online_inputs"]


def test_direct_esn_fit_save_load_and_reset_are_deterministic(tmp_path):
    config = DirectESNConfig(reservoir_size=32, seed=5)
    controller = DirectESNController(config)
    observations = [_observation(index / 20.0) for index in range(30)]
    features = controller.features(observations, washout_steps=4)
    targets = np.zeros((len(features), 7), dtype=float)
    targets[:, 0] = 0.4
    targets[:, 1] = -0.2
    mse = controller.fit_readout(features, targets)
    assert np.isfinite(mse)
    controller.reset()
    first = controller.act(np.full(7, 0.1), np.full(7, 0.1), np.full(6, 0.1))
    path = tmp_path / "direct_esn.npz"
    controller.save_npz(path)
    restored = DirectESNController.from_npz(path)
    restored.reset()
    controller.reset()
    second = restored.act(np.full(7, 0.1), np.full(7, 0.1), np.full(6, 0.1))
    np.testing.assert_allclose(first.bounded_filter_action, second.bounded_filter_action)
    assert 0.20 <= second.wbc_scale <= 1.0
    assert np.all(np.abs(second.yielding_twist[:3]) <= config.maximum_linear_yield_mps + 1e-12)


def test_direct_esn_proximal_readout_remains_close_to_parent():
    controller = DirectESNController(DirectESNConfig(reservoir_size=24, seed=11))
    parent = np.full((7, controller.feature_dimension), 0.25)
    features = np.zeros((8, controller.feature_dimension))
    features[:, 0] = 1.0
    controller.fit_readout(features, np.zeros((8, 7)), prior_readout=parent, prior_weight=1.0e6)
    np.testing.assert_allclose(controller.readout_copy(), parent, atol=3.0e-5)


def test_direct_esn_aligns_yield_with_measured_wbc_deviation_only():
    controller = DirectESNController(DirectESNConfig(reservoir_size=24, seed=8, error_aligned_yield=True))
    readout = np.zeros((7, controller.feature_dimension))
    readout[1:4, 0] = [0.35, -0.65, 0.25]
    controller.set_readout(readout)
    feature = np.zeros(controller.feature_dimension)
    feature[0] = 1.0
    action = controller.action_from_feature(
        feature, activation=1.0, pose_error=np.array([0.0, -0.010, 0.0, 0.0, 0.0, 0.0]),
    )
    # ``target - measured = -y`` means a physical push toward +y, so the
    # compliant yielding command must be aligned with +y and have no x/z part.
    assert action.bounded_filter_action[2] > 0.0
    np.testing.assert_allclose(action.bounded_filter_action[[1, 3]], 0.0, atol=1e-12)


def test_direct_esn_rejoin_fade_uses_deployable_error_derivative_only():
    config = DirectESNConfig(reservoir_size=24, seed=12, rejoin_fade_enabled=True, rejoin_fade_maximum=0.80)
    controller = DirectESNController(config)
    readout = np.zeros((7, controller.feature_dimension))
    readout[1, 0] = 1.0
    controller.set_readout(readout)
    feature = np.zeros(controller.feature_dimension)
    feature[0] = 1.0
    faded = controller.action_from_feature(
        feature, activation=1.0, residual_gain=0.20,
    )
    nominal = controller.action_from_feature(feature, activation=1.0)
    assert np.linalg.norm(faded.yielding_twist) < np.linalg.norm(nominal.yielding_twist)


def test_privileged_teacher_yields_away_from_contact_and_rejoins_after_release():
    impact = privileged_teacher_action(10.0, np.array([0.0, 1.0, 0.0]), 0.08, -0.004, np.zeros(6))
    assert impact[0] > 0.0
    assert impact[2] < 0.0
    release = privileged_teacher_action(0.0, np.array([0.0, 1.0, 0.0]), 0.0, 0.01, np.array([0.004, 0.0, 0.0, 0.0, 0.0, 0.0]))
    assert release[1] < 0.0
    assert np.all(np.abs(release) <= 1.0)


def test_teacher_trace_has_equal_length_and_bounded_actions():
    n = 12
    actions = build_privileged_teacher_trace(
        np.linspace(0.0, 10.0, n),
        np.tile([0.0, 1.0, 0.0], (n, 1)),
        np.linspace(0.0, 0.1, n),
        np.linspace(0.01, -0.002, n),
        np.zeros((n, 6)),
    )
    assert actions.shape == (n, 7)
    assert np.all(np.isfinite(actions))
    assert np.all(np.abs(actions) <= 1.0)


def test_phase_aware_teacher_is_exactly_neutral_before_first_contact():
    actions = build_privileged_teacher_trace(
        np.array([0.0, 0.0, 8.0, 0.0]),
        np.tile([0.0, 1.0, 0.0], (4, 1)),
        np.array([0.0, 0.0, 0.04, 0.0]),
        np.array([0.02, 0.02, -0.002, 0.02]),
        np.tile([0.005, 0.0, 0.0, 0.0, 0.0, 0.0], (4, 1)),
    )
    np.testing.assert_allclose(actions[:2], 0.0)
    assert np.linalg.norm(actions[2]) > 0.0
    assert actions[3, 1] < 0.0
