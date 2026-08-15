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
