#!/usr/bin/env python3
"""Spring--carriage VMC compliance baseline for the fixed-WBC environment.

Faithful twist-layer reproduction of the frozen VMC benchmark controller
(``run_benchmark.py::SixDVirtualCarriage``): a virtual carriage of finite
mass/inertia tracks the WBC nominal pose through a drive spring--damper, the
end-effector is coupled to the carriage by the six-dimensional *saturating*
spring--damper, and the reaction of that coupling pushes the carriage away
from the nominal path during a collision.  All physical parameters are the
frozen ``VMCConfig`` values and the tuned six-channel ``KAPPA_6D``; nothing is
re-tuned here except where the twist-layer execution itself demands it.

Execution mapping (torque layer -> twist layer): in the frozen benchmark the
EE spring wrench becomes joint torques.  Here the WBC already owns arm
velocities, so the carriage *is* the compliant reference — the emitted
``yield_twist`` equals the carriage velocity relative to the WBC nominal
twist, and the WBC speed loop plays the role of the EE spring.  The emitted
action therefore uses the same bounded 7-D interface and safety adapter as
the Direct ESN policy.

Two drive variants:

- ``proprioceptive`` (default): the carriage is pushed by the reaction of the
  EE coupling estimated from WBC pose/twist tracking error, mirroring the
  mechanical coupling of the original.  No contact force is read, matching
  the Direct ESN observation contract.
- ``force_feedback``: the carriage is pushed by the measured rod-on-hand
  wrench (world frame), i.e. the classical admittance reading.  This is the
  information-set upper bound; it reads a signal the deployed ESN forbids.

Differences from the frozen torque-layer benchmark (documented, not hidden):

1. A hard deadband on the WBC tracking-error channels suppresses the
   velocity-layer noise floor (the torque-layer proxy tracks at ~0.3 mm and
   needs none).  Deadbands are calibrated to the no-rod error distribution,
   not tuned on benchmark outcomes.
2. The arm no longer receives ``J^T w`` — the WBC velocity loop replaces the
   EE spring actuation, and the shared safety adapter still bounds yield
   magnitude and slew.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np

PHYSICS_DT = 0.004
RL_DT = 0.040
SUBSTEPS = int(round(RL_DT / PHYSICS_DT))

# Frozen values from scripts/run_benchmark_v2_ladder.py (never re-tuned here).
KAPPA_6D = (27.579838, 52.550787, 48.699427, 35.859580, 40.719830, 34.766858)


@dataclass(frozen=True)
class SpringCarriageConfig:
    """Frozen VMCConfig values plus the twist-layer adaptation switches."""

    kappa_6d: tuple[float, ...] = KAPPA_6D
    k_translation_base: float = 220.0
    k_rotation_base: float = 18.0
    zeta: float = 1.05
    virtual_mass: float = 1.25
    virtual_inertia: float = 0.08
    carriage_drive_k_translation: float = 75.0
    carriage_drive_k_rotation: float = 7.0
    carriage_drive_zeta: float = 1.15
    max_force: float = 24.0
    max_moment: float = 3.0
    max_carriage_speed: float = 0.55
    max_carriage_angular_speed: float = 1.25
    drive_source: str = "proprioceptive"
    deadband_m: float = 0.008
    deadband_rad: float = 0.032
    rate_deadband_mps: float = 0.030
    rate_deadband_radps: float = 0.100

    def __post_init__(self) -> None:
        if self.drive_source not in ("proprioceptive", "force_feedback"):
            raise ValueError("drive_source must be 'proprioceptive' or 'force_feedback'")
        if len(self.kappa_6d) != 6 or any(k <= 0.0 for k in self.kappa_6d):
            raise ValueError("kappa_6d must be six positive values")
        values = np.asarray(
            [self.k_translation_base, self.k_rotation_base, self.zeta, self.virtual_mass,
             self.virtual_inertia, self.carriage_drive_k_translation, self.carriage_drive_k_rotation,
             self.carriage_drive_zeta, self.max_force, self.max_moment, self.max_carriage_speed,
             self.max_carriage_angular_speed, self.deadband_m, self.deadband_rad,
             self.rate_deadband_mps, self.rate_deadband_radps], dtype=float,
        )
        if not np.all(np.isfinite(values)) or np.any(values <= 0.0):
            raise ValueError("spring-carriage parameters must be finite and positive")


class SpringCarriageVMC:
    """Stateful spring--carriage compliance law with the ESN action interface."""

    family = "spring_carriage_vmc"

    def __init__(self, config: SpringCarriageConfig) -> None:
        self.config = config
        kappa = np.asarray(config.kappa_6d, dtype=float)
        base = np.asarray([config.k_translation_base] * 3 + [config.k_rotation_base] * 3)
        self.ee_stiffness = kappa * base
        self.mass = np.asarray([config.virtual_mass] * 3 + [config.virtual_inertia] * 3)
        self.saturation = np.asarray([config.max_force] * 3 + [config.max_moment] * 3)
        self.ee_damping = 2.0 * config.zeta * np.sqrt(self.mass * self.ee_stiffness)
        self.drive_stiffness = np.asarray(
            [config.carriage_drive_k_translation] * 3 + [config.carriage_drive_k_rotation] * 3)
        self.drive_damping = 2.0 * config.carriage_drive_zeta * np.sqrt(self.mass * self.drive_stiffness)
        self.speed_limits = np.asarray(
            [config.max_carriage_speed] * 3 + [config.max_carriage_angular_speed] * 3)
        self.offset = np.zeros(6)       # carriage pose relative to WBC nominal
        self.offset_rate = np.zeros(6)  # carriage twist relative to WBC nominal twist

    def reset(self) -> None:
        self.offset = np.zeros(6)
        self.offset_rate = np.zeros(6)

    def act(
        self,
        pose_error: np.ndarray,
        twist_error: np.ndarray,
        contact_wrench_world: np.ndarray | None = None,
    ) -> np.ndarray:
        """Advance the carriage one RL step and return the 7-D action."""

        error = np.asarray(pose_error, dtype=float)
        error_rate = np.asarray(twist_error, dtype=float)
        if error.shape != (6,) or error_rate.shape != (6,):
            raise ValueError("pose/twist errors must be six-dimensional")
        if self.config.drive_source == "force_feedback":
            if contact_wrench_world is None:
                raise ValueError("force_feedback drive requires the measured contact wrench")
            measured = np.asarray(contact_wrench_world, dtype=float)
            if measured.shape != (6,):
                raise ValueError("contact wrench must be six-dimensional")
            # The frozen torque-layer carriage never feels the raw contact
            # force — only the saturated EE-coupling reaction.  Keep the same
            # channel saturation here so the variant differs solely in the
            # drive signal (measured vs estimated), not in force limits.
            measured_saturated = self.saturation * np.tanh(measured / self.saturation)
        else:
            # WBC noise-floor deadbands on the proprioceptive coupling estimate.
            deadband = np.asarray([self.config.deadband_m] * 3 + [self.config.deadband_rad] * 3)
            rate_deadband = np.asarray(
                [self.config.rate_deadband_mps] * 3 + [self.config.rate_deadband_radps] * 3)
            gated = np.sign(error) * np.maximum(np.abs(error) - deadband, 0.0)
            gated_rate = np.sign(error_rate) * np.maximum(np.abs(error_rate) - rate_deadband, 0.0)
        for _ in range(SUBSTEPS):
            if self.config.drive_source == "force_feedback":
                # Measured wrench replaces the estimated coupling drive, but
                # the carriage keeps the same EE-coupling self-limiting
                # reaction on its own offset.  In the frozen torque layer the
                # carriage only ever feels the EE spring, whose steady state
                # balances the contact force; without this term the soft drive
                # spring (75 N/m) alone lets a 24 N force drift the carriage
                # to ~0.3 m.
                external = measured_saturated \
                    - self.saturation * np.tanh(self.ee_stiffness * self.offset / self.saturation) \
                    - self.ee_damping * self.offset_rate
            else:
                # pose_error = nominal - ee, so (gated + offset) is the carriage-to-EE
                # separation negated; the coupling reaction on the carriage points
                # away from the rod exactly like the frozen torque-layer coupling.
                # This reaction depends on the live carriage state and must be
                # recomputed every substep for numerical stability.
                separation = -(gated + self.offset)
                separation_rate = -(gated_rate + self.offset_rate)
                external = self.saturation * np.tanh(self.ee_stiffness * separation / self.saturation) \
                    + self.ee_damping * separation_rate
            drive = -self.drive_stiffness * self.offset - self.drive_damping * self.offset_rate
            acceleration = (drive + external) / self.mass
            self.offset_rate = np.clip(
                self.offset_rate + PHYSICS_DT * acceleration, -self.speed_limits, self.speed_limits)
            self.offset = self.offset + PHYSICS_DT * self.offset_rate
        action = np.zeros(7)
        action[0] = 1.0
        action[1:] = self.offset_rate
        return action

    def save_npz(self, path: Path) -> None:
        np.savez_compressed(
            path,
            controller_family=np.asarray([self.family]),
            config_json=np.asarray([json.dumps(asdict(self.config))]),
        )

    @classmethod
    def from_npz(cls, path: Path) -> "SpringCarriageVMC":
        with np.load(path, allow_pickle=False) as archive:
            if str(archive["controller_family"][0]) != cls.family:
                raise ValueError(f"{path}: not a {cls.family} checkpoint")
            payload = json.loads(str(archive["config_json"][0]))
            config = SpringCarriageConfig(
                kappa_6d=tuple(payload["kappa_6d"]),
                **{k: v for k, v in payload.items() if k != "kappa_6d"})
        return cls(config)


@dataclass(frozen=True)
class VMCComplianceAction:
    """Duck-typed counterpart of ``DirectESNAction`` for the rollout adapter."""

    bounded_filter_action: np.ndarray
    wbc_scale: float
    yielding_twist: np.ndarray
    raw_readout: np.ndarray


class VMCComplianceAdapter:
    """Expose the spring--carriage VMC through the Direct ESN controller interface."""

    family = "spring_carriage_vmc"

    def __init__(self, baseline: SpringCarriageVMC) -> None:
        self.baseline = baseline
        self.config = baseline.config
        self.linear_yield_limit_mps = 0.16
        self.angular_yield_limit_radps = 0.60

    def reset(self) -> None:
        self.baseline.reset()

    def set_yield_limits(self, linear_mps: float, angular_radps: float) -> None:
        if linear_mps <= 0.0 or angular_radps <= 0.0:
            raise ValueError("yield limits must be positive")
        self.linear_yield_limit_mps = float(linear_mps)
        self.angular_yield_limit_radps = float(angular_radps)

    def act(
        self,
        joint_position: np.ndarray,
        joint_velocity: np.ndarray,
        nominal_twist: np.ndarray,
        pose_error: np.ndarray | None = None,
        twist_error: np.ndarray | None = None,
        contact_wrench_world: np.ndarray | None = None,
    ) -> VMCComplianceAction:
        if pose_error is None or twist_error is None:
            raise ValueError("the VMC baseline requires WBC pose/twist tracking errors")
        if self.baseline.config.drive_source == "proprioceptive" and contact_wrench_world is not None:
            raise ValueError("proprioceptive drive must not receive the measured contact wrench")
        physical = self.baseline.act(pose_error, twist_error, contact_wrench_world)
        limits = np.asarray(
            [self.linear_yield_limit_mps] * 3 + [self.angular_yield_limit_radps] * 3, dtype=float)
        normalized = np.zeros(7)
        normalized[1:] = np.clip(physical[1:] / limits, -1.0, 1.0)
        return VMCComplianceAction(
            bounded_filter_action=normalized,
            wbc_scale=1.0,
            yielding_twist=physical[1:],
            raw_readout=normalized.copy(),
        )


def load_controller(path: Path):
    """Load either a Direct ESN checkpoint or the spring--carriage VMC baseline."""

    with np.load(path, allow_pickle=False) as archive:
        if "controller_family" in archive.files and str(archive["controller_family"][0]) == VMCComplianceAdapter.family:
            return VMCComplianceAdapter(SpringCarriageVMC.from_npz(path))
    from direct_esn_compliance import DirectESNController

    return DirectESNController.from_npz(path)
