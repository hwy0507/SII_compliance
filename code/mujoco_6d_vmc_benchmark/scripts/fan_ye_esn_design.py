"""Fan Ye et al.-inspired ESN reservoir design for WBC-aware compliance.

This module implements the *design-before-training* part of
``Reservoir controllers design through robot-reservoir timescale alignment``
(Fan Ye et al., Communications Engineering, 2025), adapted to the Panda
compliance task.

The paper's cart-pole controller first generates random reservoirs, rejects
ones whose frequency response does not contain the robot's dynamics (CR), and
checks initial-state sensitivity (ESPI).  Only a selected reservoir receives a
ridge-trained readout.  Here a WBC-aware, deployable proprioceptive trace is
the robot probe.  This is deliberately not a claim of reproducing the paper's
cart-pole result or its task-specific CR threshold.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

import numpy as np

from esn_compliance import ACTION_DIMENSION, ESNObservation, STUDENT_INPUT_DIMENSION, encode_student_observation


FAN_YE_REFERENCE = "Fan Ye et al., Reservoir controllers design through robot-reservoir timescale alignment, Communications Engineering 4:81 (2025), doi:10.1038/s44172-025-00418-1"


def _finite_matrix(values: np.ndarray, columns: int, label: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 2 or array.shape[1] != columns or len(array) < 4 or not np.all(np.isfinite(array)):
        raise ValueError(f"{label} must be a finite T x {columns} array with T >= 4")
    return array


@dataclass(frozen=True)
class FanYeESNConfig:
    """Fixed ESN parameters corresponding to Eq. (7)-(9) in Fan Ye et al."""

    reservoir_size: int
    spectral_radius: float
    input_scale: float
    time_constant_s: float
    connection_probability: float
    bias_scale: float
    ridge_lambda: float
    dt_s: float = 0.040
    seed: int = 0

    def __post_init__(self) -> None:
        if self.reservoir_size < STUDENT_INPUT_DIMENSION:
            raise ValueError("reservoir_size must be at least the 20-D deployable input dimension")
        if not 0.0 < self.spectral_radius <= 2.0 or not 0.0 < self.input_scale <= 2.0:
            raise ValueError("spectral_radius and input_scale must be in (0, 2]")
        if not 0.0 < self.connection_probability <= 1.0 or not 0.0 <= self.bias_scale <= 1.0:
            raise ValueError("connection_probability must be in (0, 1] and bias_scale in [0, 1]")
        if self.dt_s <= 0.0 or self.time_constant_s < self.dt_s:
            raise ValueError("time_constant_s must be at least one integration step")
        if self.ridge_lambda < 0.0:
            raise ValueError("ridge_lambda must be non-negative")

    @property
    def leak(self) -> float:
        """Euler discretization of Fan Ye's continuous leaky ESN equation."""

        return self.dt_s / self.time_constant_s


@dataclass(frozen=True)
class FanYeReservoirMetrics:
    """Pre-training diagnostics; no controller label or test reward is used."""

    containment_ratio: float
    echo_state_property_index: float
    robot_bandwidth_hz: float
    reservoir_bandwidth_hz: float
    candidate_index: int
    config: FanYeESNConfig

    def __post_init__(self) -> None:
        values = np.array((self.containment_ratio, self.echo_state_property_index, self.robot_bandwidth_hz, self.reservoir_bandwidth_hz), dtype=float)
        if not np.all(np.isfinite(values)) or self.containment_ratio < 0.0 or self.echo_state_property_index < 0.0:
            raise ValueError("Fan-Ye metrics must be finite and non-negative")

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_index": self.candidate_index,
            "containment_ratio": self.containment_ratio,
            "echo_state_property_index": self.echo_state_property_index,
            "robot_bandwidth_hz": self.robot_bandwidth_hz,
            "reservoir_bandwidth_hz": self.reservoir_bandwidth_hz,
            "config": asdict(self.config),
        }


@dataclass(frozen=True)
class FanYeInputNormalizer:
    """Fan Ye's robust absolute-median actuation-test normalization."""

    scales: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "scales", np.asarray(self.scales, dtype=float))
        if self.scales.shape != (STUDENT_INPUT_DIMENSION,) or not np.all(np.isfinite(self.scales)) or np.any(self.scales <= 0.0):
            raise ValueError("scales must be a positive finite 20-vector")

    @classmethod
    def from_actuation_traces(cls, traces: Iterable[np.ndarray], *, floor: float = 1.0e-3) -> "FanYeInputNormalizer":
        data = np.concatenate([_finite_matrix(trace, STUDENT_INPUT_DIMENSION, "actuation trace") for trace in traces], axis=0)
        return cls(np.maximum(np.median(np.abs(data), axis=0), floor))

    def transform(self, trace: np.ndarray) -> np.ndarray:
        return np.clip(_finite_matrix(trace, STUDENT_INPUT_DIMENSION, "trace") / self.scales, -10.0, 10.0)


def deployable_trace_from_arrays(
    joint_position: np.ndarray,
    joint_velocity: np.ndarray,
    wbc_task_twist: np.ndarray,
) -> np.ndarray:
    """Build the only trace accepted by the Fan-Ye alignment procedure.

    This explicit constructor prevents diagnostic arrays present in a MuJoCo
    archive from accidentally becoming reservoir inputs.
    """

    q = _finite_matrix(joint_position, 7, "joint_position")
    qdot = _finite_matrix(joint_velocity, 7, "joint_velocity")
    twist = _finite_matrix(wbc_task_twist, 6, "wbc_task_twist")
    if not (len(q) == len(qdot) == len(twist)):
        raise ValueError("deployable trace arrays must have matching time length")
    return np.asarray([encode_student_observation(ESNObservation(qi, qdoti, twisti)) for qi, qdoti, twisti in zip(q, qdot, twist)], dtype=float)


class FanYeAlignedESN:
    """Leaky ESN with Fan Ye's fixed reservoir and linear [1; In; s] readout.

    Unlike the earlier generic compliance prototype, there is deliberately no
    learned action feedback in the reservoir.  The state update follows the
    continuous leaky form used in the cited paper:

        tau * ds/dt = -s + tanh(W_in In + W_r s + b).
    """

    def __init__(self, config: FanYeESNConfig) -> None:
        self.config = config
        rng = np.random.default_rng(config.seed)
        recurrent = rng.uniform(-1.0, 1.0, (config.reservoir_size, config.reservoir_size))
        recurrent *= rng.random(recurrent.shape) < config.connection_probability
        radius = float(np.max(np.abs(np.linalg.eigvals(recurrent))))
        if not np.isfinite(radius) or radius < 1.0e-8:
            recurrent = np.roll(np.eye(config.reservoir_size), shift=1, axis=1)
            radius = 1.0
        self._recurrent = recurrent * (config.spectral_radius / radius)
        self._input = rng.uniform(-config.input_scale, config.input_scale, (config.reservoir_size, STUDENT_INPUT_DIMENSION))
        self._bias = rng.uniform(-config.bias_scale, config.bias_scale, config.reservoir_size)
        self._state = np.zeros(config.reservoir_size, dtype=float)
        self._readout = np.zeros((ACTION_DIMENSION, 1 + STUDENT_INPUT_DIMENSION + config.reservoir_size), dtype=float)

    @property
    def state(self) -> np.ndarray:
        return self._state.copy()

    @property
    def feature_dimension(self) -> int:
        return self._readout.shape[1]

    def reset(self, state: np.ndarray | None = None) -> None:
        if state is None:
            self._state.fill(0.0)
            return
        state_array = np.asarray(state, dtype=float)
        if state_array.shape != self._state.shape or not np.all(np.isfinite(state_array)):
            raise ValueError("initial reservoir state has invalid shape or values")
        self._state = np.clip(state_array, -1.0, 1.0)

    def advance(self, encoded_input: np.ndarray) -> np.ndarray:
        input_array = np.asarray(encoded_input, dtype=float)
        if input_array.shape != (STUDENT_INPUT_DIMENSION,) or not np.all(np.isfinite(input_array)):
            raise ValueError("encoded input must be finite and 20-dimensional")
        proposal = np.tanh(self._input @ input_array + self._recurrent @ self._state + self._bias)
        self._state = (1.0 - self.config.leak) * self._state + self.config.leak * proposal
        if not np.all(np.isfinite(self._state)):
            raise RuntimeError("Fan-Ye reservoir state became non-finite")
        return np.concatenate((np.array([1.0]), input_array, self._state))

    def features(self, inputs: np.ndarray, *, washout_steps: int = 0) -> np.ndarray:
        trace = _finite_matrix(inputs, STUDENT_INPUT_DIMENSION, "input trace")
        if not 0 <= washout_steps < len(trace):
            raise ValueError("washout_steps must be non-negative and smaller than trace length")
        self.reset()
        output = [self.advance(row) for row in trace]
        return np.asarray(output[washout_steps:], dtype=float)

    def states(self, inputs: np.ndarray, *, initial_state: np.ndarray | None = None) -> np.ndarray:
        trace = _finite_matrix(inputs, STUDENT_INPUT_DIMENSION, "input trace")
        self.reset(initial_state)
        output = []
        for row in trace:
            self.advance(row)
            output.append(self.state)
        return np.asarray(output, dtype=float)

    def fit_readout(self, features: np.ndarray, targets: np.ndarray) -> None:
        design = np.asarray(features, dtype=float)
        target_array = np.asarray(targets, dtype=float)
        if design.ndim != 2 or design.shape[1] != self.feature_dimension or not np.all(np.isfinite(design)):
            raise ValueError("features have invalid shape or non-finite values")
        if target_array.shape != (len(design), ACTION_DIMENSION) or not np.all(np.isfinite(target_array)):
            raise ValueError("targets must be a finite N x 7 array")
        gram = design.T @ design + self.config.ridge_lambda * np.eye(self.feature_dimension)
        readout = np.linalg.solve(gram, design.T @ np.clip(target_array, -1.0, 1.0)).T
        if not np.all(np.isfinite(readout)):
            raise RuntimeError("Fan-Ye ridge readout became non-finite")
        self._readout = readout

    def action(self, encoded_input: np.ndarray) -> np.ndarray:
        action = self._readout @ self.advance(encoded_input)
        if not np.all(np.isfinite(action)):
            raise RuntimeError("Fan-Ye readout action became non-finite")
        return action


def _aggregate_spectrum(signals: np.ndarray, dt_s: float, max_frequency_hz: float) -> tuple[np.ndarray, np.ndarray]:
    values = _finite_matrix(signals, signals.shape[1], "spectrum signals")
    if dt_s <= 0.0 or max_frequency_hz <= 0.0:
        raise ValueError("dt_s and max_frequency_hz must be positive")
    # We compare dynamic content rather than static postures, which otherwise
    # dominate Panda joint-position spectra but are not a control timescale.
    dynamic = values - np.mean(values, axis=0, keepdims=True)
    dynamic *= np.hanning(len(dynamic))[:, None]
    frequencies = np.fft.rfftfreq(len(dynamic), dt_s)
    amplitude = np.max(np.abs(np.fft.rfft(dynamic, axis=0)), axis=1)
    mask = frequencies <= max_frequency_hz
    return frequencies[mask], amplitude[mask]


def frequency_containment_ratio(robot_signals: np.ndarray, reservoir_states: np.ndarray, *, dt_s: float, max_frequency_hz: float) -> tuple[float, float, float]:
    """Fan Ye's normalized spectral containment ratio (CR), task-adapted."""

    frequencies, robot = _aggregate_spectrum(robot_signals, dt_s, max_frequency_hz)
    reservoir_frequencies, reservoir = _aggregate_spectrum(reservoir_states, dt_s, max_frequency_hz)
    if frequencies.shape != reservoir_frequencies.shape or not np.allclose(frequencies, reservoir_frequencies):
        raise ValueError("robot and reservoir spectra have incompatible sampling")
    robot_norm = robot / max(float(np.max(robot)), 1.0e-12)
    reservoir_norm = reservoir / max(float(np.max(reservoir)), 1.0e-12)
    containment = float(np.sum(np.minimum(robot_norm, reservoir_norm)) / max(float(np.sum(robot_norm)), 1.0e-12))
    dynamic_floor = 0.05
    robot_bandwidth = float(frequencies[np.where(robot_norm >= dynamic_floor)[0][-1]]) if np.any(robot_norm >= dynamic_floor) else 0.0
    reservoir_bandwidth = float(frequencies[np.where(reservoir_norm >= dynamic_floor)[0][-1]]) if np.any(reservoir_norm >= dynamic_floor) else 0.0
    return containment, robot_bandwidth, reservoir_bandwidth


def echo_state_property_index(reservoir: FanYeAlignedESN, inputs: np.ndarray, *, washout_steps: int, initializations: int = 10, seed: int = 0) -> float:
    """Fan Ye's ESPI: post-washout state MSE over multiple initial states."""

    trace = _finite_matrix(inputs, STUDENT_INPUT_DIMENSION, "input trace")
    if not 0 <= washout_steps < len(trace) or initializations < 1:
        raise ValueError("invalid washout or initialization count")
    baseline = reservoir.states(trace)
    rng = np.random.default_rng(seed)
    errors = []
    for _ in range(initializations):
        alternative = reservoir.states(trace, initial_state=rng.uniform(-1.0, 1.0, reservoir.config.reservoir_size))
        errors.append(float(np.mean((alternative[washout_steps:] - baseline[washout_steps:]) ** 2)))
    return float(np.mean(errors))


def evaluate_fan_ye_candidate(
    config: FanYeESNConfig,
    normalized_robot_trace: np.ndarray,
    *,
    candidate_index: int,
    washout_steps: int,
    max_frequency_hz: float,
    espi_initializations: int = 10,
) -> FanYeReservoirMetrics:
    """Evaluate a reservoir without fitting a control readout or reading labels."""

    trace = _finite_matrix(normalized_robot_trace, STUDENT_INPUT_DIMENSION, "normalized robot trace")
    reservoir = FanYeAlignedESN(config)
    states = reservoir.states(trace)
    cr, robot_bandwidth, reservoir_bandwidth = frequency_containment_ratio(trace, states, dt_s=config.dt_s, max_frequency_hz=max_frequency_hz)
    espi = echo_state_property_index(reservoir, trace, washout_steps=washout_steps, initializations=espi_initializations, seed=config.seed + 10_000)
    return FanYeReservoirMetrics(cr, espi, robot_bandwidth, reservoir_bandwidth, candidate_index, config)


def random_fan_ye_configs(
    count: int,
    *,
    dt_s: float,
    seed: int,
) -> list[FanYeESNConfig]:
    """Generate the paper-informed random design family before filtering."""

    if count < 1 or dt_s <= 0.0:
        raise ValueError("count and dt_s must be positive")
    rng = np.random.default_rng(seed)
    configs = []
    for index in range(count):
        size = int(rng.choice((24, 32, 48, 64)))
        configs.append(FanYeESNConfig(
            reservoir_size=size,
            spectral_radius=float(rng.uniform(0.5, 2.0)),
            input_scale=float(rng.uniform(0.1, 2.0)),
            time_constant_s=float(rng.uniform(dt_s, 0.320)),
            connection_probability=float(rng.uniform(2.0 / size, min(20.0 / size, 1.0))),
            bias_scale=float(rng.uniform(0.01, 1.0)),
            ridge_lambda=float(10.0 ** rng.uniform(-8.0, -2.0)),
            dt_s=dt_s,
            seed=seed + index + 1,
        ))
    return configs


def pareto_frontier(metrics: list[FanYeReservoirMetrics]) -> list[FanYeReservoirMetrics]:
    """Keep CR-high / ESPI-low nondominated reservoirs before readout training."""

    frontier = []
    for candidate in metrics:
        dominated = any(
            other.containment_ratio >= candidate.containment_ratio
            and other.echo_state_property_index <= candidate.echo_state_property_index
            and (other.containment_ratio > candidate.containment_ratio or other.echo_state_property_index < candidate.echo_state_property_index)
            for other in metrics
        )
        if not dominated:
            frontier.append(candidate)
    return sorted(frontier, key=lambda item: (-item.containment_ratio, item.echo_state_property_index, item.candidate_index))
