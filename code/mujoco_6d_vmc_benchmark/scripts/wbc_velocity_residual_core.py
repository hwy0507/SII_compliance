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
        ])
        gains = np.asarray(self.velocity_gain_nm_per_radps, dtype=float)
        rates = np.asarray(self.maximum_torque_rate_nmps, dtype=float)
        if not np.all(np.isfinite(scalars)) or np.any(scalars <= 0.0):
            raise ValueError("velocity-residual safety scalars must be finite and positive")
        if self.minimum_wbc_scale >= 1.0:
            raise ValueError("minimum_wbc_scale must be below one")
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
