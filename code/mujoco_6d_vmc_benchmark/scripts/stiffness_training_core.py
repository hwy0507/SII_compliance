"""Dependency-light contracts for safe six-dimensional stiffness learning.

The module intentionally contains no MuJoCo import: unit tests and manifest
generation can run anywhere.  A future PPO/CMA-ES worker should use these
functions instead of silently changing the action bounds, observation layout,
or invalid-episode treatment.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np


CHANNELS = ("x", "y", "z", "roll", "pitch", "yaw")
OBSERVATION_FIELDS = (
    "position_error_world_3",
    "orientation_error_world_3",
    "twist_error_world_6",
    "joint_position_7",
    "joint_velocity_7",
    "carriage_displacement_6",
    "carriage_velocity_6",
    "applied_torque_ratio_7",
    "previous_action_6",
)
PRIVILEGED_DIAGNOSTICS = (
    "rod_contact",
    "rod_force",
    "rod_penetration",
    "rod_displacement",
    "rod_command_velocity",
    "future_collision_phase",
    "obstacle_geometry_or_pose",
)
EFFECTIVE_COLLISION_GATE = {
    "minimum_peak_contact_force_n": 15.0,
    "minimum_contact_impulse_ns": 0.45,
}


@dataclass(frozen=True)
class StiffnessActionConfig:
    """Safety envelope for low-rate log-stiffness policy actions."""

    base_kappa: tuple[float, float, float, float, float, float] = (35.0,) * 6
    minimum_kappa: tuple[float, float, float, float, float, float] = (8.0,) * 6
    maximum_kappa: tuple[float, float, float, float, float, float] = (70.0,) * 6
    action_log_span: float = 0.8
    update_hz: float = 25.0
    max_log_rate_per_s: float = 1.6


def _vector(values: np.ndarray | tuple[float, ...] | list[float], size: int, label: str) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    if result.shape != (size,) or not np.all(np.isfinite(result)):
        raise ValueError(f"{label} must be a finite {size}-vector")
    return result


def _six(values: np.ndarray | tuple[float, ...] | list[float], label: str) -> np.ndarray:
    return _vector(values, 6, label)


def action_target_to_kappa(
    action: np.ndarray | list[float],
    config: StiffnessActionConfig = StiffnessActionConfig(),
) -> np.ndarray:
    """Map an RL action to a positive bounded kappa target, before rate limiting."""

    action_array = _six(action, "action")
    base = _six(config.base_kappa, "base_kappa")
    minimum = _six(config.minimum_kappa, "minimum_kappa")
    maximum = _six(config.maximum_kappa, "maximum_kappa")
    if np.any(minimum <= 0.0) or np.any(maximum < minimum):
        raise ValueError("invalid stiffness safety envelope")
    return np.clip(base * np.exp(np.clip(action_array, -1.0, 1.0) * config.action_log_span), minimum, maximum)


def action_to_kappa(
    action: np.ndarray | list[float],
    previous_kappa: np.ndarray | list[float],
    config: StiffnessActionConfig = StiffnessActionConfig(),
) -> np.ndarray:
    """Map an RL action to a positive, bounded, rate-limited kappa vector.

    The policy emits six values in ``[-1, 1]`` at ``update_hz``.  Mapping in
    log space prevents a fixed additive change from meaning very different
    things near soft and stiff operating points.  The rate limiter is a
    controller-side safety shield, not a learned behavior.
    """

    previous = _six(previous_kappa, "previous_kappa")
    minimum = _six(config.minimum_kappa, "minimum_kappa")
    maximum = _six(config.maximum_kappa, "maximum_kappa")
    if np.any(minimum <= 0.0) or np.any(maximum < minimum) or config.update_hz <= 0.0 or config.max_log_rate_per_s <= 0.0:
        raise ValueError("invalid stiffness safety envelope")
    target = action_target_to_kappa(action, config)
    max_delta = config.max_log_rate_per_s / config.update_hz
    log_next = np.clip(np.log(target), np.log(previous) - max_delta, np.log(previous) + max_delta)
    return np.clip(np.exp(log_next), minimum, maximum)


def deployment_observation(
    *,
    position_error_world: np.ndarray | list[float],
    orientation_error_world: np.ndarray | list[float],
    twist_error_world: np.ndarray | list[float],
    joint_position: np.ndarray | list[float],
    joint_velocity: np.ndarray | list[float],
    carriage_displacement: np.ndarray | list[float],
    carriage_velocity: np.ndarray | list[float],
    applied_torque_ratio: np.ndarray | list[float],
    previous_action: np.ndarray | list[float],
) -> np.ndarray:
    """Build the 51-D policy observation using deployable proprioception only."""

    fields = (
        (_vector(position_error_world, 3, "position_error_world"), 0.06),
        (_vector(orientation_error_world, 3, "orientation_error_world"), 0.20),
        (np.asarray(twist_error_world, dtype=float), np.array([0.60] * 3 + [2.0] * 3)),
        (np.asarray(joint_position, dtype=float), 3.0),
        (np.asarray(joint_velocity, dtype=float), 3.0),
        (_six(carriage_displacement, "carriage_displacement"), np.array([0.06] * 3 + [0.20] * 3)),
        (_six(carriage_velocity, "carriage_velocity"), np.array([0.60] * 3 + [2.0] * 3)),
        (np.asarray(applied_torque_ratio, dtype=float), 1.0),
        (_six(previous_action, "previous_action"), 1.0),
    )
    expected = (3, 3, 6, 7, 7, 6, 6, 7, 6)
    normalized: list[np.ndarray] = []
    for (value, scale), shape in zip(fields, expected, strict=True):
        if value.shape != (shape,) or not np.all(np.isfinite(value)):
            raise ValueError("observation component has an invalid shape or non-finite value")
        normalized.append(np.clip(value / scale, -10.0, 10.0))
    observation = np.concatenate(normalized)
    if observation.shape != (51,):
        raise AssertionError("unexpected policy observation dimension")
    return observation


def latin_hypercube(samples: int, dimensions: int, seed: int) -> np.ndarray:
    """Deterministic dependency-free Latin hypercube in [0, 1]."""
    if samples < 1 or dimensions < 1:
        raise ValueError("samples and dimensions must be positive")
    rng = np.random.default_rng(seed)
    design = np.empty((samples, dimensions), dtype=float)
    for dimension in range(dimensions):
        design[:, dimension] = (rng.permutation(samples) + rng.random(samples)) / samples
    return design


def scenario_from_unit(unit: np.ndarray, action_config: StiffnessActionConfig = StiffnessActionConfig()) -> dict[str, Any]:
    """Create one valid-fixture curriculum sample from ten LHS coordinates."""
    values = np.asarray(unit, dtype=float)
    if values.shape != (10,) or np.any(values < 0.0) or np.any(values > 1.0):
        raise ValueError("unit sample must be a ten-vector in [0, 1]")
    # These ranges deliberately remain close to calibrated valid contact
    # geometry. Wider geometry changes are held out for robustness testing.
    stroke = 0.155 + 0.025 * values[0]
    height = 0.538 + 0.004 * values[1]
    start = 1.04 + 0.08 * values[2]
    static_action = -0.9 + 1.8 * values[4:10]
    kappa = action_target_to_kappa(static_action, action_config)
    return {
        "rod_stroke_m": float(stroke),
        "rod_height_m": float(height),
        "rod_start_time_s": float(start),
        "grasp_time_s": 2.40,
        "initial_action": static_action.tolist(),
        "initial_kappa_vector": kappa.tolist(),
    }


def training_contract(action_config: StiffnessActionConfig = StiffnessActionConfig()) -> dict[str, Any]:
    """Serializable contract stored beside all future training runs."""
    return {
        "channels": list(CHANNELS),
        "observation_dimension": 51,
        "observation_fields": list(OBSERVATION_FIELDS),
        "excluded_privileged_diagnostics": list(PRIVILEGED_DIAGNOSTICS),
        "action": {
            "dimension": 6,
            "range": [-1.0, 1.0],
            "mapping": "kappa = clip(base * exp(action_log_span * action)); log-space rate-limited",
            **asdict(action_config),
        },
        "validity_gate": "finite + rod-hand contact + stable rejoin + lift + hold + no hard torque limit + valid matched no-rod task",
        "effective_collision_gate": EFFECTIVE_COLLISION_GATE,
        "objective": "Constrained Pareto: minimize paired offset, recovery RMSE and rejoin latency subject to task success, no hard torque limit, torque/jerk safety budgets.",
    }
