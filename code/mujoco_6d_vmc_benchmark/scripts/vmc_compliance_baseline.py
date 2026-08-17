#!/usr/bin/env python3
"""Twist-layer VMC compliance baseline for the fixed-WBC Direct ESN environment.

This is the paper's VMC baseline.  It reuses the six-dimensional saturating
spring--damper law of the frozen VMC benchmark, but executes it in the same
twist interface as the Direct ESN policy: the controller consumes only
proprioceptive signals that the WBC already exposes (pose/twist tracking
error, nominal twist) and emits the same bounded 7-D action
``[wbc_slowdown, yield_twist]``.  No contact force, normal, or obstacle
information is read, so its observation contract matches the Direct ESN
contract exactly and the comparison isolates the compliance law itself.

Dynamics (per channel i, integrated at the physics substep):

    M xdd + D xd + sigma_i tanh(K_i x / sigma_i)
        = sigma_i tanh(K_e dead(e) / sigma_i) + D_e edot

where ``e`` is the WBC pose error with a deadband ``dead(e)`` that suppresses
the controller's standing tracking error, and ``edot`` is the WBC twist
error.  The twist term is what actually discriminates a collision: the
rod impact produces a velocity-mismatch pulse roughly 3.5x larger than the
largest no-rod transient, while pose errors overlap between the two regimes.
Both the drive and the return spring saturate at the same channel limits, so
a persistent error bounds the offset steady state instead of diverging.
While WBC tracks well the offset relaxes to zero and the emitted action is
zero, so a no-rod rollout stays close to Fixed WBC.  During a collision the
drive surge pushes the offset, the emitted ``yield_twist = xd`` lets the
end-effector yield, and once the rod releases the saturating spring pulls the
offset back (rejoin).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

PHYSICS_DT = 0.004
RL_DT = 0.040
SUBSTEPS = int(round(RL_DT / PHYSICS_DT))


@dataclass(frozen=True)
class VMCComplianceConfig:
    """Parameters mirror the frozen VMC benchmark where dimensions allow."""

    kappa_translation: float = 1.0
    kappa_rotation: float = 1.0
    k_translation_base: float = 1200.0
    k_rotation_base: float = 60.0
    zeta: float = 1.0
    virtual_mass: float = 6.0
    virtual_inertia: float = 0.12
    max_force: float = 45.0
    max_moment: float = 6.0
    error_drive_scale: float = 1.0
    drive_deadband_m: float = 0.008
    drive_deadband_rad: float = 0.032
    rate_deadband_mps: float = 0.030
    rate_deadband_radps: float = 0.100
    gated_stiffness_scale: float = 1.0
    gate_error_threshold_m: float = 0.004
    gate_error_threshold_rad: float = 0.035

    def stiffness(self) -> np.ndarray:
        return np.asarray(
            [self.kappa_translation * self.k_translation_base] * 3
            + [self.kappa_rotation * self.k_rotation_base] * 3,
            dtype=float,
        )

    def __post_init__(self) -> None:
        values = np.asarray(list(asdict(self).values()), dtype=float)
        if not np.all(np.isfinite(values)) or np.any(values <= 0.0):
            raise ValueError("VMC compliance parameters must be finite and positive")


class VMCComplianceBaseline:
    """Stateful twist-layer VMC compliance law with the ESN action interface."""

    family = "vmc_compliance_baseline"

    def __init__(self, config: VMCComplianceConfig) -> None:
        self.config = config
        self.stiffness = config.stiffness()
        self.mass = np.asarray([config.virtual_mass] * 3 + [config.virtual_inertia] * 3)
        self.saturation = np.asarray([config.max_force] * 3 + [config.max_moment] * 3)
        self.damping = 2.0 * config.zeta * np.sqrt(self.mass * self.stiffness)
        self.error_gain = config.error_drive_scale * self.stiffness
        self.error_damping = 2.0 * config.zeta * np.sqrt(self.mass * self.error_gain)
        self.offset = np.zeros(6)
        self.offset_rate = np.zeros(6)

    def reset(self) -> None:
        self.offset = np.zeros(6)
        self.offset_rate = np.zeros(6)

    def act(
        self,
        pose_error: np.ndarray,
        twist_error: np.ndarray,
    ) -> np.ndarray:
        """Advance the offset dynamics one RL step and return the 7-D action."""

        error = np.asarray(pose_error, dtype=float).copy()
        error_rate = np.asarray(twist_error, dtype=float).copy()
        if error.shape != (6,) or error_rate.shape != (6,):
            raise ValueError("pose/twist errors must be six-dimensional")
        deadband = np.asarray(
            [self.config.drive_deadband_m] * 3 + [self.config.drive_deadband_rad] * 3,
        )
        rate_deadband = np.asarray(
            [self.config.rate_deadband_mps] * 3 + [self.config.rate_deadband_radps] * 3,
        )
        # Hard deadbands calibrated to the no-rod WBC noise floor (p95) keep
        # standing transients silent; collision-sized signals pass through.
        gated_error = np.sign(error) * np.maximum(np.abs(error) - deadband, 0.0)
        gated_rate = np.sign(error_rate) * np.maximum(np.abs(error_rate) - rate_deadband, 0.0)
        drive = self.saturation * np.tanh(self.error_gain * gated_error / self.saturation) \
            + self.error_damping * gated_rate
        # Contact-gated softening: relax the return spring while the WBC
        # tracking error is large (rod pressing), restore it during recovery.
        soft = np.ones(6)
        if self.config.gated_stiffness_scale != 1.0:
            thresholds = np.asarray(
                [self.config.gate_error_threshold_m] * 3
                + [self.config.gate_error_threshold_rad] * 3,
            )
            active = np.abs(error) > thresholds
            soft[active] = self.config.gated_stiffness_scale
        for _ in range(SUBSTEPS):
            spring = self.saturation * np.tanh(self.stiffness * soft * self.offset / self.saturation)
            acceleration = (drive - spring - self.damping * self.offset_rate) / self.mass
            self.offset_rate = self.offset_rate + PHYSICS_DT * acceleration
            self.offset = self.offset + PHYSICS_DT * self.offset_rate
        action = np.zeros(7)
        action[0] = 1.0
        action[1:] = self.offset_rate
        return action

    def save_npz(self, path: Path) -> None:
        import json

        np.savez_compressed(
            path,
            controller_family=np.asarray([self.family]),
            config_json=np.asarray([json.dumps(asdict(self.config))]),
        )

    @classmethod
    def from_npz(cls, path: Path) -> "VMCComplianceBaseline":
        import json

        with np.load(path, allow_pickle=False) as archive:
            if str(archive["controller_family"][0]) != cls.family:
                raise ValueError(f"{path}: not a {cls.family} checkpoint")
            config = VMCComplianceConfig(**json.loads(str(archive["config_json"][0])))
        return cls(config)


@dataclass(frozen=True)
class VMCComplianceAction:
    """Duck-typed counterpart of ``DirectESNAction`` for the rollout adapter."""

    bounded_filter_action: np.ndarray
    wbc_scale: float
    yielding_twist: np.ndarray
    raw_readout: np.ndarray


class VMCComplianceAdapter:
    """Expose the VMC baseline through the Direct ESN controller interface."""

    family = "vmc_compliance_baseline"

    def __init__(self, baseline: VMCComplianceBaseline) -> None:
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
    ) -> VMCComplianceAction:
        if pose_error is None or twist_error is None:
            raise ValueError("the VMC baseline requires WBC pose/twist tracking errors")
        physical = self.baseline.act(pose_error, twist_error)
        limits = np.asarray(
            [self.linear_yield_limit_mps] * 3 + [self.angular_yield_limit_radps] * 3,
            dtype=float,
        )
        normalized = np.zeros(7)
        normalized[1:] = np.clip(physical[1:] / limits, -1.0, 1.0)
        return VMCComplianceAction(
            bounded_filter_action=normalized,
            wbc_scale=1.0,
            yielding_twist=physical[1:],
            raw_readout=normalized.copy(),
        )


def load_controller(path: Path):
    """Load either a Direct ESN checkpoint or the twist-layer VMC baseline.

    Both controller families live behind the same rollout interface, so the
    matched benchmark treats them identically.
    """

    with np.load(path, allow_pickle=False) as archive:
        if "controller_family" in archive.files and str(archive["controller_family"][0]) == VMCComplianceAdapter.family:
            return VMCComplianceAdapter(VMCComplianceBaseline.from_npz(path))
    from direct_esn_compliance import DirectESNController

    return DirectESNController.from_npz(path)
