"""Tests for Fan Ye-style pre-training reservoir selection."""

import sys
from pathlib import Path

import numpy as np


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
from fan_ye_esn_design import (  # noqa: E402
    FanYeAlignedESN,
    FanYeESNConfig,
    FanYeInputNormalizer,
    deployable_trace_from_arrays,
    echo_state_property_index,
    evaluate_fan_ye_candidate,
    pareto_frontier,
)
from train_fan_ye_esn_readout import GatedVMCTeacherConfig, teacher_actions_from_gate  # noqa: E402
from fan_ye_esn_policy import FanYeVMCPolicyConfig  # noqa: E402
from fan_ye_esn_rl_adapter import (  # noqa: E402
    CURRENT_WBC_FEATURE_DIMENSION,
    FanYeESNRLObservationAdapter,
    encode_wbc_current_feature,
)
from esn_compliance import ESNObservation  # noqa: E402


def _trace(rows: int = 80) -> np.ndarray:
    time = np.arange(rows, dtype=float) * 0.04
    return deployable_trace_from_arrays(
        np.column_stack([np.sin((index + 1) * time) for index in range(7)]),
        np.column_stack([np.cos((index + 1) * time) for index in range(7)]),
        np.column_stack([np.sin((index + 1) * time) for index in range(6)]),
    )


def _config(seed: int = 3) -> FanYeESNConfig:
    return FanYeESNConfig(
        reservoir_size=24, spectral_radius=0.9, input_scale=0.8, time_constant_s=0.08,
        connection_probability=0.4, bias_scale=0.1, ridge_lambda=1e-4, seed=seed,
    )


def test_actuation_normalization_and_fan_ye_features_are_finite():
    trace = _trace()
    normalized = FanYeInputNormalizer.from_actuation_traces([trace]).transform(trace)
    reservoir = FanYeAlignedESN(_config())
    features = reservoir.features(normalized, washout_steps=10)
    assert features.shape == (70, 45)
    assert np.all(np.isfinite(features))
    assert normalized[:1].shape == (1, 20)


def test_espi_and_containment_are_finite_without_teacher_labels():
    trace = _trace()
    normalized = FanYeInputNormalizer.from_actuation_traces([trace]).transform(trace)
    reservoir = FanYeAlignedESN(_config())
    assert echo_state_property_index(reservoir, normalized, washout_steps=10, initializations=3) >= 0.0
    metrics = evaluate_fan_ye_candidate(_config(), normalized, candidate_index=0, washout_steps=10, max_frequency_hz=8.0, espi_initializations=3)
    assert 0.0 <= metrics.containment_ratio <= 1.0 + 1e-12
    assert metrics.robot_bandwidth_hz <= 8.0


def test_pareto_frontier_keeps_high_cr_low_espi_tradeoffs():
    trace = _trace()
    normalized = FanYeInputNormalizer.from_actuation_traces([trace]).transform(trace)
    first = evaluate_fan_ye_candidate(_config(1), normalized, candidate_index=0, washout_steps=10, max_frequency_hz=8.0, espi_initializations=2)
    second = evaluate_fan_ye_candidate(_config(2), normalized, candidate_index=1, washout_steps=10, max_frequency_hz=8.0, espi_initializations=2)
    frontier = pareto_frontier([first, second])
    assert frontier
    assert all(item.containment_ratio >= 0.0 and item.echo_state_property_index >= 0.0 for item in frontier)


def test_causal_gate_teacher_is_bounded_and_has_no_contact_input():
    actions = teacher_actions_from_gate(np.array([0.0, 0.5, 1.0]), GatedVMCTeacherConfig())
    assert actions.shape == (3, 7)
    assert np.all((-1.0 <= actions) & (actions <= 1.0))
    np.testing.assert_allclose(actions[0], 0.0)
    assert actions[-1, 6] > 0.0


def test_teacher_envelope_changes_only_teacher_action_magnitudes():
    gate = np.array([0.0, 1.0])
    gentle = teacher_actions_from_gate(gate, GatedVMCTeacherConfig(-0.35, -0.10, 0.25))
    assert gentle.shape == (2, 7)
    np.testing.assert_allclose(gentle[0], 0.0)
    np.testing.assert_allclose(gentle[-1, :3], -0.35)
    np.testing.assert_allclose(gentle[-1, 3:6], -0.10)
    assert gentle[-1, 6] == 0.25


def test_teacher_gate_filter_is_causal_and_default_preserves_legacy_actions():
    gate = np.array([0.0, 1.0, 0.0])
    legacy = teacher_actions_from_gate(gate)
    unfiltered = teacher_actions_from_gate(gate, GatedVMCTeacherConfig(gate_filter_time_constant_s=0.0))
    filtered = teacher_actions_from_gate(gate, GatedVMCTeacherConfig(gate_filter_time_constant_s=0.04), sample_period_s=0.04)
    np.testing.assert_allclose(legacy, unfiltered)
    assert filtered[1, 6] < legacy[1, 6]
    assert filtered[2, 6] > 0.0


def test_fitted_readout_serialization_has_a_valid_shape():
    trace = _trace()
    normalized = FanYeInputNormalizer.from_actuation_traces([trace]).transform(trace)
    model = FanYeAlignedESN(_config())
    features = model.features(normalized, washout_steps=10)
    model.fit_readout(features, np.zeros((len(features), 7)))
    copied = FanYeAlignedESN(_config())
    copied.set_readout(model.readout)
    assert copied.action(normalized[0]).shape == (7,)


def test_fan_ye_vmc_policy_envelope_matches_common_vmc_boundary():
    config = FanYeVMCPolicyConfig()
    assert len(config.base_kappa) == 6
    assert config.contact_drive_scale == 8.0
    assert config.minimum_recovery_drive_scale <= config.base_recovery_drive_scale <= config.maximum_recovery_drive_scale


def test_fan_ye_rl_adapter_uses_only_fixed_reservoir_wbc_features(tmp_path: Path):
    config = _config()
    model = FanYeAlignedESN(config)
    npz = tmp_path / "model.npz"
    np.savez_compressed(npz, input_normalizer_scales=np.ones(20), readout=model.readout)
    summary = tmp_path / "summary.json"
    summary.write_text(__import__("json").dumps({"config": config.__dict__}))
    adapter = FanYeESNRLObservationAdapter(npz, summary)
    observation = ESNObservation(np.zeros(7), np.zeros(7), np.zeros(6))
    normalized = adapter.normalized_input(observation)
    assert normalized.shape == (20,)
    assert np.all(np.isfinite(normalized))
    current = encode_wbc_current_feature(observation, np.zeros(6), np.zeros(6))
    assert current.shape == (CURRENT_WBC_FEATURE_DIMENSION,)
    feature = adapter.observe(observation, np.zeros(6), np.zeros(6))
    assert feature.shape == (CURRENT_WBC_FEATURE_DIMENSION + config.reservoir_size,)
    assert np.all(np.isfinite(feature))
    adapter.reset()
    np.testing.assert_allclose(feature, adapter.observe(observation, np.zeros(6), np.zeros(6)))
    adapter.reset()
    multiscale = adapter.observe_multiscale(observation, np.zeros(6), np.zeros(6))
    assert multiscale.shape == (CURRENT_WBC_FEATURE_DIMENSION + 128,)
    assert np.all(np.isfinite(multiscale))
    adapter.reset()
    np.testing.assert_allclose(multiscale, adapter.observe_multiscale(observation, np.zeros(6), np.zeros(6)))


def test_wbc_error_feature_is_directional_and_rejects_non_six_vectors() -> None:
    observation = ESNObservation(np.zeros(7), np.zeros(7), np.zeros(6))
    feature = encode_wbc_current_feature(
        observation, np.array([0.006, 0.0, 0.0, 0.0, 0.0, 0.0]), np.zeros(6),
    )
    assert feature.shape == (CURRENT_WBC_FEATURE_DIMENSION,)
    assert feature[20] > 0.0
    with np.testing.assert_raises(ValueError):
        encode_wbc_current_feature(observation, np.zeros(5), np.zeros(6))
