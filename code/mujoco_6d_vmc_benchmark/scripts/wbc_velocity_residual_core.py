"""Safety-bounded WBC velocity-residual command adapter.

This module is deliberately independent of the VMC implementation.  It has no
virtual spring, virtual carriage, stiffness, damping, or spring-force state.
Its only input is a fixed WBC joint command plus a learned, bounded Cartesian
yield command; its only output is a rate-limited joint-velocity/torque command.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


ARM_DOF = 7
TORQUE_LIMITS_NM = np.array([87.0, 87.0, 87.0, 87.0, 12.0, 12.0, 12.0])


@dataclass(frozen=True)
class VelocityResidualSafetyConfig:
    """Deployment-time bounds shared by the MLP and ESN actors."""

    minimum_wbc_scale: float = 0.20
    maximum_linear_yield_mps: float = 0.16
    maximum_angular_yield_radps: float = 0.60
    maximum_scale_rate_per_s: float = 4.0
    maximum_linear_yield_rate_mps2: float = 1.20
    maximum_angular_yield_rate_radps2: float = 4.0
    pseudoinverse_damping: float = 0.04
    maximum_joint_speed_radps: float = 1.25
    maximum_joint_acceleration_radps2: float = 8.0
    authority_gate_start_error_m: float = 0.004
    authority_gate_full_error_m: float = 0.012
    predictive_authority_enabled: bool = False
    predictive_authority_min_multiplier: float = 0.35
    predictive_authority_max_multiplier: float = 1.0
    predictive_authority_recovery_deadband: float = 0.05
    predictive_authority_release_gain: float = 1.0
    directional_phase_projection: bool = False
    directional_phase_minimum_error_m: float = 0.004
    directional_phase_rate_deadband_m2ps: float = 2.0e-5
    velocity_gain_nm_per_radps: np.ndarray = field(
        default_factory=lambda: np.array([42.0, 42.0, 36.0, 32.0, 9.0, 8.0, 6.0])
    )
    maximum_torque_rate_nmps: np.ndarray = field(
        default_factory=lambda: np.array([700.0, 700.0, 700.0, 700.0, 160.0, 160.0, 160.0])
    )

    def __post_init__(self) -> None:
        scalars = np.array([
            self.minimum_wbc_scale,
            self.maximum_linear_yield_mps,
            self.maximum_angular_yield_radps,
            self.maximum_scale_rate_per_s,
            self.maximum_linear_yield_rate_mps2,
            self.maximum_angular_yield_rate_radps2,
            self.pseudoinverse_damping,
            self.maximum_joint_speed_radps,
            self.maximum_joint_acceleration_radps2,
            self.authority_gate_start_error_m,
            self.authority_gate_full_error_m,
            self.directional_phase_minimum_error_m,
            self.directional_phase_rate_deadband_m2ps,
            self.predictive_authority_min_multiplier,
            self.predictive_authority_max_multiplier,
            self.predictive_authority_recovery_deadband,
            self.predictive_authority_release_gain,
        ])
        gains = np.asarray(self.velocity_gain_nm_per_radps, dtype=float)
        rates = np.asarray(self.maximum_torque_rate_nmps, dtype=float)
        if not np.all(np.isfinite(scalars)) or np.any(scalars <= 0.0):
            raise ValueError("velocity-residual safety scalars must be finite and positive")
        if self.minimum_wbc_scale >= 1.0:
            raise ValueError("minimum_wbc_scale must be below one")
        if self.authority_gate_full_error_m <= self.authority_gate_start_error_m:
            raise ValueError("authority gate full-error threshold must exceed its start threshold")
        if self.predictive_authority_min_multiplier > self.predictive_authority_max_multiplier:
            raise ValueError("predictive authority minimum must not exceed maximum")
        if self.predictive_authority_max_multiplier > 1.0:
            raise ValueError("predictive authority maximum cannot amplify policy authority")
        if gains.shape != (ARM_DOF,) or rates.shape != (ARM_DOF,):
            raise ValueError("velocity gains and torque rates must be seven-vectors")
        if not np.all(np.isfinite(gains)) or not np.all(np.isfinite(rates)) or np.any(gains <= 0.0) or np.any(rates <= 0.0):
            raise ValueError("velocity gains and torque rates must be finite and positive")


@dataclass(frozen=True)
class FilteredVelocityResidualAction:
    """Physical action applied after amplitude and slew-rate filtering."""

    wbc_scale: float
    cartesian_yield_twist: np.ndarray
    raw_action_clipped: np.ndarray
    amplitude_saturated: bool
    slew_limited: bool


class VelocityResidualActionFilter:
    """Convert a neutral-zero policy action into a bounded physical command.

    The policy action is seven-dimensional and lies in ``[-1, 1]``.  Positive
    channel zero requests slowing; non-positive values retain full nominal WBC
    speed.  Channels 1--6 request signed world-frame Cartesian yield velocity.
    Consequently the all-zero action is exactly the fixed-WBC controller.
    """

    def __init__(self, config: VelocityResidualSafetyConfig | None = None) -> None:
        self.config = config or VelocityResidualSafetyConfig()
        self.reset()

    def reset(self) -> None:
        self.wbc_scale = 1.0
        self.cartesian_yield_twist = np.zeros(6, dtype=float)

    def filter(self, action: np.ndarray, dt: float) -> FilteredVelocityResidualAction:
        values = np.asarray(action, dtype=float)
        if values.shape != (7,) or not np.all(np.isfinite(values)):
            raise ValueError("velocity-residual action must be a finite seven-vector")
        if not np.isfinite(dt) or dt <= 0.0:
            raise ValueError("action-filter dt must be finite and positive")
        clipped = np.clip(values, -1.0, 1.0)
        amplitude_saturated = not bool(np.array_equal(values, clipped))
        desired_scale = 1.0 - max(0.0, float(clipped[0])) * (1.0 - self.config.minimum_wbc_scale)
        maximum_twist = np.array([
            self.config.maximum_linear_yield_mps,
            self.config.maximum_linear_yield_mps,
            self.config.maximum_linear_yield_mps,
            self.config.maximum_angular_yield_radps,
            self.config.maximum_angular_yield_radps,
            self.config.maximum_angular_yield_radps,
        ])
        desired_yield = clipped[1:] * maximum_twist
        scale_delta = np.clip(
            desired_scale - self.wbc_scale,
            -self.config.maximum_scale_rate_per_s * dt,
            self.config.maximum_scale_rate_per_s * dt,
        )
        maximum_yield_delta = np.array([
            self.config.maximum_linear_yield_rate_mps2 * dt,
            self.config.maximum_linear_yield_rate_mps2 * dt,
            self.config.maximum_linear_yield_rate_mps2 * dt,
            self.config.maximum_angular_yield_rate_radps2 * dt,
            self.config.maximum_angular_yield_rate_radps2 * dt,
            self.config.maximum_angular_yield_rate_radps2 * dt,
        ])
        yield_delta = np.clip(
            desired_yield - self.cartesian_yield_twist,
            -maximum_yield_delta,
            maximum_yield_delta,
        )
        slew_limited = bool(
            not np.isclose(scale_delta, desired_scale - self.wbc_scale)
            or not np.allclose(yield_delta, desired_yield - self.cartesian_yield_twist)
        )
        self.wbc_scale = float(np.clip(self.wbc_scale + scale_delta, self.config.minimum_wbc_scale, 1.0))
        self.cartesian_yield_twist = np.clip(self.cartesian_yield_twist + yield_delta, -maximum_twist, maximum_twist)
        return FilteredVelocityResidualAction(
            wbc_scale=self.wbc_scale,
            cartesian_yield_twist=self.cartesian_yield_twist.copy(),
            raw_action_clipped=clipped.copy(),
            amplitude_saturated=amplitude_saturated,
            slew_limited=slew_limited,
        )


def damped_pseudoinverse(jacobian: np.ndarray, damping: float) -> np.ndarray:
    matrix = np.asarray(jacobian, dtype=float)
    if matrix.shape != (6, ARM_DOF) or not np.all(np.isfinite(matrix)):
        raise ValueError("Panda task Jacobian must be a finite 6x7 matrix")
    if not np.isfinite(damping) or damping <= 0.0:
        raise ValueError("pseudoinverse damping must be finite and positive")
    gram = matrix @ matrix.T + damping**2 * np.eye(6)
    return matrix.T @ np.linalg.solve(gram, np.eye(6))


def deployable_authority_gate(
    tracking_error_m: float, config: VelocityResidualSafetyConfig,
) -> float:
    """Smooth residual authority from the WBC's measured Cartesian departure."""

    if not np.isfinite(tracking_error_m) or tracking_error_m < 0.0:
        raise ValueError("tracking error must be finite and non-negative")
    phase = np.clip(
        (tracking_error_m - config.authority_gate_start_error_m)
        / (config.authority_gate_full_error_m - config.authority_gate_start_error_m),
        0.0,
        1.0,
    )
    return float(phase * phase * (3.0 - 2.0 * phase))


def predictive_authority_multiplier(
    pose_error: np.ndarray,
    predicted_delta_pose_error: np.ndarray,
    config: VelocityResidualSafetyConfig,
) -> float:
    """Reduce residual authority when a causal forecast predicts rejoin.

    Both vectors use the normalized coordinates of the fixed ESN forecaster
    (translation and rotation are scaled before entering the reservoir).  The
    radial projection is therefore dimensionless and combines all six
    task-space channels without reading
    force, contact, rod state, obstacle geometry, reward, or future phase.
    Positive radial change means the WBC error is predicted to grow, so the
    base authority is retained.  Negative radial change means predicted
    rejoin, so authority is smoothly released.
    """

    error = np.asarray(pose_error, dtype=float)
    delta = np.asarray(predicted_delta_pose_error, dtype=float)
    if error.shape != (6,) or delta.shape != (6,) or not np.all(np.isfinite(error)) or not np.all(np.isfinite(delta)):
        raise ValueError("predictive authority inputs must be finite six-vectors")
    if not config.predictive_authority_enabled:
        return 1.0
    error_norm = float(np.linalg.norm(error))
    if error_norm <= 1.0e-9:
        return 1.0
    radial_change = float(np.dot(error, delta) / error_norm)
    recovery_fraction = max(0.0, -radial_change / error_norm)
    deadband = config.predictive_authority_recovery_deadband
    normalized_recovery = np.clip(
        (recovery_fraction - deadband) / max(1.0 - deadband, 1.0e-9), 0.0, 1.0
    )
    release = config.predictive_authority_release_gain * normalized_recovery
    multiplier = config.predictive_authority_max_multiplier - (
        config.predictive_authority_max_multiplier - config.predictive_authority_min_multiplier
    ) * np.clip(release, 0.0, 1.0)
    return float(np.clip(multiplier, config.predictive_authority_min_multiplier, config.predictive_authority_max_multiplier))


def project_yield_action_to_error_phase(
    action: np.ndarray, pose_error: np.ndarray, twist_error: np.ndarray, config: VelocityResidualSafetyConfig,
) -> np.ndarray:
    """Keep residual velocity in the causal yield/rejoin half-space.

    The WBC tracking error is ``target - measured``.  When its squared norm is
    increasing, a compliant response may only move further from the nominal
    target (the yield half-space).  When it is decreasing, the residual may
    only move toward the nominal target (the rejoin half-space).  The decision
    depends solely on current WBC target and robot proprioception, never on a
    contact, force, rod, obstacle, or future-release signal.
    """

    values = np.asarray(action, dtype=float)
    error = np.asarray(pose_error, dtype=float)
    derivative = np.asarray(twist_error, dtype=float)
    if values.shape != (7,) or error.shape != (6,) or derivative.shape != (6,):
        raise ValueError("phase projection requires 7-D action and two 6-D WBC errors")
    if not np.all(np.isfinite(values)) or not np.all(np.isfinite(error)) or not np.all(np.isfinite(derivative)):
        raise ValueError("phase projection inputs must be finite")
    if not config.directional_phase_projection:
        return values.copy()
    projected = values.copy()
    for action_slice, error_slice, derivative_slice in ((slice(1, 4), slice(0, 3), slice(0, 3)), (slice(4, 7), slice(3, 6), slice(3, 6))):
        local_error = error[error_slice]
        norm = float(np.linalg.norm(local_error))
        if norm < config.directional_phase_minimum_error_m:
            continue
        direction = local_error / norm
        radial_rate = float(np.dot(local_error, derivative[derivative_slice]))
        if abs(radial_rate) <= config.directional_phase_rate_deadband_m2ps:
            continue
        component = float(np.dot(projected[action_slice], direction))
        # Increasing error: retain only the outward/yield component.  Decreasing
        # error: retain only the inward/rejoin component.
        if radial_rate > 0.0 and component > 0.0:
            projected[action_slice] -= component * direction
        elif radial_rate < 0.0 and component < 0.0:
            projected[action_slice] -= component * direction
    return projected


def safe_joint_velocity_command(
    nominal_joint_velocity: np.ndarray,
    jacobian: np.ndarray,
    action: FilteredVelocityResidualAction,
    previous_joint_velocity_command: np.ndarray,
    dt: float,
    config: VelocityResidualSafetyConfig,
) -> tuple[np.ndarray, np.ndarray]:
    """Compose WBC and yield commands, then enforce joint bounds and slew."""

    nominal = np.asarray(nominal_joint_velocity, dtype=float)
    previous = np.asarray(previous_joint_velocity_command, dtype=float)
    if nominal.shape != (ARM_DOF,) or previous.shape != (ARM_DOF,):
        raise ValueError("nominal and previous joint velocities must be seven-vectors")
    if not np.all(np.isfinite(nominal)) or not np.all(np.isfinite(previous)):
        raise ValueError("joint-velocity inputs must be finite")
    yield_joint_velocity = damped_pseudoinverse(jacobian, config.pseudoinverse_damping) @ action.cartesian_yield_twist
    raw = action.wbc_scale * nominal + yield_joint_velocity
    bounded = np.clip(raw, -config.maximum_joint_speed_radps, config.maximum_joint_speed_radps)
    maximum_delta = config.maximum_joint_acceleration_radps2 * dt
    command = previous + np.clip(bounded - previous, -maximum_delta, maximum_delta)
    return command, raw


def safe_velocity_tracking_torque(
    bias_torque: np.ndarray,
    measured_joint_velocity: np.ndarray,
    joint_velocity_command: np.ndarray,
    previous_torque: np.ndarray,
    dt: float,
    config: VelocityResidualSafetyConfig,
) -> tuple[np.ndarray, float]:
    """Velocity-servo torque with analytic box projection and torque slew."""

    bias = np.asarray(bias_torque, dtype=float)
    measured = np.asarray(measured_joint_velocity, dtype=float)
    command = np.asarray(joint_velocity_command, dtype=float)
    previous = np.asarray(previous_torque, dtype=float)
    if any(vector.shape != (ARM_DOF,) for vector in (bias, measured, command, previous)):
        raise ValueError("Panda torque adapter inputs must be seven-vectors")
    if not all(np.all(np.isfinite(vector)) for vector in (bias, measured, command, previous)):
        raise ValueError("Panda torque adapter inputs must be finite")
    servo = np.asarray(config.velocity_gain_nm_per_radps) * (command - measured)
    scale = 1.0
    for gravity, contribution, limit in zip(bias, servo, TORQUE_LIMITS_NM, strict=True):
        if contribution > 1e-9:
            scale = min(scale, max(0.0, (limit - gravity) / contribution))
        elif contribution < -1e-9:
            scale = min(scale, max(0.0, (-limit - gravity) / contribution))
    scale = float(np.clip(scale, 0.0, 1.0))
    desired = bias + scale * servo
    maximum_delta = np.asarray(config.maximum_torque_rate_nmps) * dt
    applied = previous + np.clip(desired - previous, -maximum_delta, maximum_delta)
    return np.clip(applied, -TORQUE_LIMITS_NM, TORQUE_LIMITS_NM), scale
