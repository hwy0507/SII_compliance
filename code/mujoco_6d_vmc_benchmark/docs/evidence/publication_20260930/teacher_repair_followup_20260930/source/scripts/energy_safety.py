"""Causal energy-budget safety filter for virtual-carriage return drive.

The nominal trajectory is moving, so this module deliberately does not claim a
global passivity proof for the entire robot/reference system.  It constrains
only the *incremental recovery-drive* wrench: a small energy tank is charged
from measurable drive damping and is spent when that incremental wrench does
positive mechanical work on the virtual carriage.  A direction-aware smooth
gate prevents abrupt authority changes when the carriage is already closing
the trajectory error.

No contact flag, contact force, obstacle state, or future trajectory phase is
accepted by this interface.  It is therefore usable as a deployment-time
safety shield for static VMC, PPO, or a future ESN residual policy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


EPS = 1e-12


@dataclass(frozen=True)
class EnergySafetyConfig:
    """Conservative configuration for one translational return-drive tank."""

    initial_energy_j: float = 0.80
    minimum_energy_j: float = 0.08
    maximum_energy_j: float = 1.20
    damping_recharge_efficiency: float = 0.60
    minimum_direction_scale: float = 0.30
    direction_transition_speed_mps: float = 0.08
    smoothing_time_constant_s: float = 0.040

    def __post_init__(self) -> None:
        if not (
            0.0 <= self.minimum_energy_j <= self.initial_energy_j <= self.maximum_energy_j
            and 0.0 <= self.damping_recharge_efficiency <= 1.0
            and 0.0 < self.minimum_direction_scale <= 1.0
            and self.direction_transition_speed_mps > 0.0
            and self.smoothing_time_constant_s > 0.0
        ):
            raise ValueError("invalid energy-budget safety configuration")


@dataclass(frozen=True)
class EnergySafetyDiagnostics:
    """Per-step quantities to log; none is an actor observation."""

    tank_energy_j: float
    requested_boost_norm_n: float
    applied_boost_norm_n: float
    direction_scale: float
    energy_scale: float
    damping_recharge_j: float
    requested_positive_work_j: float


class EnergyBudgetSafety:
    """Stateful causal filter for the incremental virtual-carriage drive."""

    def __init__(self, config: EnergySafetyConfig | None = None) -> None:
        self.config = EnergySafetyConfig() if config is None else config
        self.reset()

    def reset(self) -> None:
        self.energy_j = self.config.initial_energy_j
        self._direction_scale = 0.0

    @staticmethod
    def _smoothstep(value: float) -> float:
        value = float(np.clip(value, 0.0, 1.0))
        return value * value * (3.0 - 2.0 * value)

    def filter_increment(
        self,
        base_drive_force: np.ndarray,
        requested_drive_force: np.ndarray,
        position_error: np.ndarray,
        velocity_error: np.ndarray,
        carriage_velocity: np.ndarray,
        drive_damping: float,
        dt_s: float,
    ) -> tuple[np.ndarray, EnergySafetyDiagnostics]:
        """Filter only requested-minus-base drive force using measurable state.

        ``position_error`` and ``velocity_error`` are nominal minus carriage
        values.  A negative ``dot(position_error, velocity_error)`` means that
        the carriage is already closing the position error, so the requested
        boost is smoothly reduced before it can create a reversal jerk.
        """

        base = np.asarray(base_drive_force, dtype=float)
        requested = np.asarray(requested_drive_force, dtype=float)
        error = np.asarray(position_error, dtype=float)
        velocity = np.asarray(velocity_error, dtype=float)
        carriage_velocity = np.asarray(carriage_velocity, dtype=float)
        if base.shape != (3,) or requested.shape != (3,) or error.shape != (3,) or velocity.shape != (3,) or carriage_velocity.shape != (3,):
            raise ValueError("energy safety expects finite three-dimensional translational vectors")
        if not all(np.all(np.isfinite(value)) for value in (base, requested, error, velocity, carriage_velocity)) or drive_damping < 0.0 or dt_s <= 0.0:
            raise ValueError("energy safety received invalid physical values")

        boost = requested - base
        error_norm = float(np.linalg.norm(error))
        closing_speed = float(np.dot(error, velocity) / max(error_norm, EPS))
        # Error growth receives full authority.  When the carriage is already
        # closing the error, retain a non-zero authority but avoid an abrupt
        # pull-back.  The state is low-pass filtered at the physics rate.
        phase = self._smoothstep(
            0.5 + 0.5 * closing_speed / self.config.direction_transition_speed_mps
        )
        target_direction_scale = self.config.minimum_direction_scale + (1.0 - self.config.minimum_direction_scale) * phase
        alpha = 1.0 - float(np.exp(-dt_s / self.config.smoothing_time_constant_s))
        self._direction_scale += alpha * (target_direction_scale - self._direction_scale)
        direction_scale = float(np.clip(self._direction_scale, self.config.minimum_direction_scale, 1.0))
        direction_limited_boost = direction_scale * boost

        # Damping acts on nominal-minus-carriage velocity.  Treat a fixed
        # conservative fraction of the dissipated energy as tank recharge.
        recharge_j = self.config.damping_recharge_efficiency * drive_damping * float(np.dot(velocity, velocity)) * dt_s
        available_j = max(0.0, self.energy_j - self.config.minimum_energy_j + recharge_j)
        requested_work_j = max(0.0, float(np.dot(direction_limited_boost, carriage_velocity))) * dt_s
        energy_scale = 1.0 if requested_work_j <= available_j + EPS else available_j / requested_work_j
        applied_boost = energy_scale * direction_limited_boost
        applied_work_j = max(0.0, float(np.dot(applied_boost, carriage_velocity))) * dt_s
        self.energy_j = float(np.clip(
            self.energy_j + recharge_j - applied_work_j,
            self.config.minimum_energy_j,
            self.config.maximum_energy_j,
        ))
        return base + applied_boost, EnergySafetyDiagnostics(
            tank_energy_j=self.energy_j,
            requested_boost_norm_n=float(np.linalg.norm(boost)),
            applied_boost_norm_n=float(np.linalg.norm(applied_boost)),
            direction_scale=direction_scale,
            energy_scale=float(energy_scale),
            damping_recharge_j=float(recharge_j),
            requested_positive_work_j=float(requested_work_j),
        )
