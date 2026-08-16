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
    predictive_authority_require_kinematic_agreement: bool = False
    predictive_authority_require_measured_recovery: bool = False
    directional_phase_projection: bool = False
    directional_phase_minimum_error_m: float = 0.004
    directional_phase_rate_deadband_m2ps: float = 2.0e-5
    rejoin_velocity_envelope: bool = False
    rejoin_linear_velocity_per_m: float = 5.0
    rejoin_angular_velocity_per_rad: float = 4.0
    phase_memory_floor_maximum: float = 0.55
    phase_memory_floor_error_start_m: float = 0.003
    phase_memory_floor_error_full_m: float = 0.008
    phase_memory_floor_rise_per_s: float = 8.0
    phase_memory_floor_release_per_s: float = 1.20
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
            self.rejoin_linear_velocity_per_m,
            self.rejoin_angular_velocity_per_rad,
            self.phase_memory_floor_maximum,
            self.phase_memory_floor_error_start_m,
            self.phase_memory_floor_error_full_m,
            self.phase_memory_floor_rise_per_s,
            self.phase_memory_floor_release_per_s,
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
        if self.phase_memory_floor_error_full_m <= self.phase_memory_floor_error_start_m:
            raise ValueError("phase-memory floor full-error threshold must exceed its start threshold")
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


@dataclass
class ResidualEnergyTank:
    """Continuous authority budget for a learned WBC residual.

    The tank is deliberately stateful but non-privileged: it sees only the
    proposed residual action and measured WBC pose/twist errors.  It spends
    budget on residual work and fast action changes, recharges near the nominal
    path, and returns a continuously slew-limited authority multiplier.
    """

    enabled: bool = False
    capacity: float = 1.0
    initial: float = 1.0
    reserve: float = 0.20
    spend_rate: float = 0.55
    action_change_rate: float = 0.18
    phase_spend_rate: float = 0.25
    recharge_rate: float = 0.20
    minimum_multiplier: float = 0.25
    multiplier_slew_per_s: float = 3.0
    stable_error_threshold: float = 0.40
    previous_action: np.ndarray = field(default_factory=lambda: np.zeros(7, dtype=float))
    energy: float = field(init=False)
    multiplier: float = field(init=False)

    def __post_init__(self) -> None:
        values = np.asarray([
            self.capacity, self.initial, self.reserve, self.spend_rate,
            self.action_change_rate, self.recharge_rate, self.minimum_multiplier,
            self.phase_spend_rate,
            self.multiplier_slew_per_s, self.stable_error_threshold,
        ], dtype=float)
        if not np.all(np.isfinite(values)) or np.any(values <= 0.0):
            raise ValueError("energy-tank parameters must be finite and positive")
        if self.initial > self.capacity or self.reserve > self.capacity:
            raise ValueError("energy-tank initial/reserve must not exceed capacity")
        if self.minimum_multiplier > 1.0:
            raise ValueError("energy-tank minimum multiplier must not exceed one")
        self.reset()

    def reset(self) -> None:
        self.energy = float(np.clip(self.initial, 0.0, self.capacity))
        self.multiplier = 1.0
        self.previous_action = np.zeros(7, dtype=float)

    def apply(
        self, action: np.ndarray, pose_error: np.ndarray, twist_error: np.ndarray,
        dt: float, phase_memory_score: float = 0.0,
    ) -> tuple[np.ndarray, float, float]:
        values = np.asarray(action, dtype=float)
        error = np.asarray(pose_error, dtype=float)
        twist = np.asarray(twist_error, dtype=float)
        if values.shape != (7,) or error.shape != (6,) or twist.shape != (6,):
            raise ValueError("energy-tank inputs must be action-7 and error/twist-6")
        if not np.all(np.isfinite(values)) or not np.all(np.isfinite(error)) or not np.all(np.isfinite(twist)):
            raise ValueError("energy-tank inputs must be finite")
        if not np.isfinite(dt) or dt <= 0.0:
            raise ValueError("energy-tank dt must be finite and positive")
        if not np.isfinite(phase_memory_score) or not 0.0 <= phase_memory_score <= 1.0:
            raise ValueError("phase-memory score must be finite and in [0, 1]")
        clipped = np.clip(values, -1.0, 1.0)
        if not self.enabled:
            self.previous_action = clipped.copy()
            return values.copy(), 1.0, self.energy

        # Normalize translation and orientation in the same causal task-space
        # units used by the ESN feature adapter.  The error radial rate is a
        # measured phase signal: positive means departure, negative means
        # rejoin.
        scaled_error = np.concatenate((error[:3] / 0.012, error[3:] / 0.20))
        scaled_twist = np.concatenate((twist[:3] / 0.40, twist[3:] / 1.20))
        error_norm = float(np.linalg.norm(scaled_error))
        radial_rate = float(np.dot(scaled_error, scaled_twist))
        residual_norm_sq = float(np.mean(clipped[1:] ** 2))
        action_change_sq = float(np.mean((clipped - self.previous_action) ** 2))
        rejoin_factor = float(np.clip(-radial_rate, 0.0, 2.0))
        spend = dt * (
            self.spend_rate * residual_norm_sq * (1.0 + 0.35 * rejoin_factor)
            + self.action_change_rate * action_change_sq
            + self.phase_spend_rate * float(phase_memory_score) * residual_norm_sq
        )
        stable_factor = float(np.clip(1.0 - error_norm / self.stable_error_threshold, 0.0, 1.0))
        stable_factor *= float(np.clip(1.0 - phase_memory_score, 0.0, 1.0))
        recharge = dt * self.recharge_rate * stable_factor * (1.0 - residual_norm_sq)
        self.energy = float(np.clip(self.energy + recharge - spend, 0.0, self.capacity))
        available = float(np.clip(self.energy / max(self.reserve, 1.0e-9), 0.0, 1.0))
        desired_multiplier = self.minimum_multiplier + (1.0 - self.minimum_multiplier) * available
        delta = self.multiplier_slew_per_s * dt
        self.multiplier = float(np.clip(
            self.multiplier + np.clip(desired_multiplier - self.multiplier, -delta, delta),
            self.minimum_multiplier, 1.0,
        ))
        output = clipped.copy()
        output[0] *= self.multiplier
        output[1:] *= self.multiplier
        self.previous_action = clipped.copy()
        return output, self.multiplier, self.energy


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


def stable_phase_memory_floor(
    phase_memory_score: float,
    rejoin_confidence: float,
    tracking_error_m: float,
    previous_floor: float,
    dt: float,
    config: VelocityResidualSafetyConfig,
) -> float:
    """Causally latch phase-memory authority through a noisy rejoin.

    The desired floor requires both fixed-reservoir phase memory and measured
    inward WBC motion.  It rises quickly when rejoin starts, releases more
    slowly through short velocity-sign reversals, and vanishes continuously as
    the translational tracking error approaches the nominal path.
    """

    values = np.asarray([phase_memory_score, rejoin_confidence, tracking_error_m, previous_floor, dt], dtype=float)
    if not np.all(np.isfinite(values)) or np.any(values < 0.0) or dt <= 0.0:
        raise ValueError("phase-memory floor inputs must be finite and non-negative with positive dt")
    memory = float(np.clip(phase_memory_score, 0.0, 1.0))
    rejoin = float(np.clip(rejoin_confidence, 0.0, 1.0))
    error_phase = np.clip(
        (tracking_error_m - config.phase_memory_floor_error_start_m)
        / (config.phase_memory_floor_error_full_m - config.phase_memory_floor_error_start_m),
        0.0, 1.0,
    )
    error_envelope = error_phase * error_phase * (3.0 - 2.0 * error_phase)
    desired = config.phase_memory_floor_maximum * memory * rejoin * error_envelope
    previous = float(np.clip(previous_floor, 0.0, config.phase_memory_floor_maximum))
    rate = config.phase_memory_floor_rise_per_s if desired >= previous else config.phase_memory_floor_release_per_s
    return float(np.clip(
        previous + np.clip(desired - previous, -rate * dt, rate * dt),
        0.0, config.phase_memory_floor_maximum,
    ))


def predictive_authority_multiplier(
    pose_error: np.ndarray,
    predicted_delta_pose_error: np.ndarray,
    config: VelocityResidualSafetyConfig,
    kinematic_delta_pose_error: np.ndarray | None = None,
    measured_pose_error_rate: np.ndarray | None = None,
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
    if config.predictive_authority_require_kinematic_agreement:
        if kinematic_delta_pose_error is None:
            raise ValueError("predictive authority agreement requires a kinematic forecast")
        kinematic = np.asarray(kinematic_delta_pose_error, dtype=float)
        if kinematic.shape != (6,) or not np.all(np.isfinite(kinematic)):
            raise ValueError("kinematic forecast must be a finite six-vector")
        kinematic_radial_change = float(np.dot(error, kinematic) / error_norm)
        kinematic_recovery_fraction = max(0.0, -kinematic_radial_change / error_norm)
        if kinematic_recovery_fraction <= deadband:
            return 1.0
    if config.predictive_authority_require_measured_recovery:
        if measured_pose_error_rate is None:
            raise ValueError("predictive authority confirmation requires measured WBC error rate")
        measured_rate = np.asarray(measured_pose_error_rate, dtype=float)
        if measured_rate.shape != (6,) or not np.all(np.isfinite(measured_rate)):
            raise ValueError("measured WBC error rate must be a finite six-vector")
        # The measured WBC twist error is the causal time derivative of the
        # target-minus-measured pose error to first order.  A prediction alone
        # must not suppress authority until the physical state confirms rejoin.
        if float(np.dot(error, measured_rate)) >= 0.0:
            return 1.0
    normalized_recovery = np.clip(
        (recovery_fraction - deadband) / max(1.0 - deadband, 1.0e-9), 0.0, 1.0
    )
    release = config.predictive_authority_release_gain * normalized_recovery
    multiplier = config.predictive_authority_max_multiplier - (
        config.predictive_authority_max_multiplier - config.predictive_authority_min_multiplier
    ) * np.clip(release, 0.0, 1.0)
    return float(np.clip(multiplier, config.predictive_authority_min_multiplier, config.predictive_authority_max_multiplier))


def predictive_wbc_feedback_scale(
    pose_error: np.ndarray,
    predicted_delta_pose_error: np.ndarray,
    *,
    minimum_feedback_scale: float = 0.60,
    growth_deadband: float = 0.05,
) -> float:
    """Causally soften WBC feedback only for predicted outward departure.

    Both inputs are normalized six-dimensional WBC pose-error coordinates.
    Feedforward motion is untouched: this function only reduces the fixed WBC
    feedback correction while the ESN predicts the measured tracking departure
    will continue to grow.  Once predicted radial growth subsides, the scale
    returns smoothly to one and the fixed WBC regains nominal tracking gains.
    """

    error = np.asarray(pose_error, dtype=float)
    delta = np.asarray(predicted_delta_pose_error, dtype=float)
    if error.shape != (6,) or delta.shape != (6,) or not np.all(np.isfinite(error)) or not np.all(np.isfinite(delta)):
        raise ValueError("predictive WBC feedback inputs must be finite six-vectors")
    if not np.isfinite(minimum_feedback_scale) or not 0.0 < minimum_feedback_scale <= 1.0:
        raise ValueError("minimum WBC feedback scale must be in (0, 1]")
    if not np.isfinite(growth_deadband) or not 0.0 <= growth_deadband < 1.0:
        raise ValueError("WBC feedback growth deadband must be in [0, 1)")
    norm = float(np.linalg.norm(error))
    if norm <= 1.0e-9:
        return 1.0
    radial_growth_fraction = max(0.0, float(np.dot(error, delta) / (norm * norm)))
    normalized_growth = np.clip(
        (radial_growth_fraction - growth_deadband) / max(1.0 - growth_deadband, 1.0e-9),
        0.0, 1.0,
    )
    return float(1.0 - (1.0 - minimum_feedback_scale) * normalized_growth)


def phase_predictive_wbc_feedback_scale(
    pose_error: np.ndarray,
    predicted_delta_pose_error: np.ndarray,
    phase_memory_score: float,
    previous_scale: float,
    dt: float,
    *,
    minimum_feedback_scale: float = 0.60,
    growth_deadband: float = 0.05,
    phase_start: float = 0.12,
    phase_full: float = 0.55,
    engage_per_s: float = 6.0,
    release_per_s: float = 2.5,
) -> float:
    """Causally modulate WBC feedback only during ESN-predicted loading.

    The fixed Fan Ye forecast estimates future WBC-error growth while the
    independent fast/slow disagreement is a phase-memory confidence.  Both
    must agree before feedback is softened.  The returned scale is slew
    limited, so feedback reinjection remains continuous through rejoin.
    """
    error = np.asarray(pose_error, dtype=float)
    delta = np.asarray(predicted_delta_pose_error, dtype=float)
    values = np.asarray([
        phase_memory_score, previous_scale, dt, minimum_feedback_scale,
        growth_deadband, phase_start, phase_full, engage_per_s, release_per_s,
    ], dtype=float)
    if error.shape != (6,) or delta.shape != (6,) or not np.all(np.isfinite(error)) or not np.all(np.isfinite(delta)):
        raise ValueError("phase-predictive WBC inputs must be finite six-vectors")
    if not np.all(np.isfinite(values)) or not 0.0 <= phase_memory_score <= 1.0 or not 0.0 < previous_scale <= 1.0 or dt <= 0.0:
        raise ValueError("phase-predictive WBC scalars are invalid")
    if not 0.0 < minimum_feedback_scale <= 1.0 or not 0.0 <= growth_deadband < 1.0 or not 0.0 <= phase_start < phase_full <= 1.0:
        raise ValueError("phase-predictive WBC bounds are invalid")
    norm = float(np.linalg.norm(error))
    if norm <= 1.0e-9:
        desired = 1.0
    else:
        growth = max(0.0, float(np.dot(error, delta) / (norm * norm)))
        growth_gate = float(np.clip((growth - growth_deadband) / max(1.0 - growth_deadband, 1.0e-9), 0.0, 1.0))
        phase_gate = float(np.clip((phase_memory_score - phase_start) / (phase_full - phase_start), 0.0, 1.0))
        desired = float(1.0 - (1.0 - minimum_feedback_scale) * growth_gate * phase_gate)
    rate = engage_per_s if desired < previous_scale else release_per_s
    return float(np.clip(
        previous_scale + np.clip(desired - previous_scale, -rate * dt, rate * dt),
        minimum_feedback_scale, 1.0,
    ))


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


def apply_rejoin_velocity_envelope(
    action: np.ndarray, pose_error: np.ndarray, twist_error: np.ndarray,
    config: VelocityResidualSafetyConfig,
) -> np.ndarray:
    """Cap inward residual velocity by remaining proprioceptive WBC error.

    The cap is active only during measured rejoin and only on the component
    directed toward the nominal target. It uses no contact, force, fixture, or
    future-phase signal, so it can be deployed with the same observation
    contract as the independent ESN actor.
    """
    values = np.asarray(action, dtype=float)
    error = np.asarray(pose_error, dtype=float)
    derivative = np.asarray(twist_error, dtype=float)
    if values.shape != (7,) or error.shape != (6,) or derivative.shape != (6,):
        raise ValueError("rejoin velocity envelope requires 7-D action and two 6-D errors")
    if not np.all(np.isfinite(values)) or not np.all(np.isfinite(error)) or not np.all(np.isfinite(derivative)):
        raise ValueError("rejoin velocity envelope inputs must be finite")
    if not config.rejoin_velocity_envelope:
        return values.copy()
    bounded = values.copy()
    for action_slice, error_slice, derivative_slice, gain, scale in (
        (slice(1, 4), slice(0, 3), slice(0, 3), config.rejoin_linear_velocity_per_m, config.maximum_linear_yield_mps),
        (slice(4, 7), slice(3, 6), slice(3, 6), config.rejoin_angular_velocity_per_rad, config.maximum_angular_yield_radps),
    ):
        local_error = error[error_slice]
        error_norm = float(np.linalg.norm(local_error))
        if error_norm <= 1.0e-9 or float(np.dot(local_error, derivative[derivative_slice])) >= 0.0:
            continue
        direction = local_error / error_norm
        inward_component = float(np.dot(bounded[action_slice], direction))
        maximum_inward_action = float(gain * error_norm / scale)
        if inward_component > maximum_inward_action:
            bounded[action_slice] -= (inward_component - maximum_inward_action) * direction
    return bounded


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
