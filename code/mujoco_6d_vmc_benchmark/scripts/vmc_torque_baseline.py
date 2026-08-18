"""Torque-mode VMC: spring-carriage wrench → joint torque (v3, stable).

The SpringCarriageVMC's internal dynamics already provide damping through
viscous friction and drive damping. Adding explicit damping in the torque
output creates over-damping and instability. This version maps ONLY the
spring reaction through the Jacobian, which is stable and effective.

τ = J^T · (−σ·tanh(K·offset/σ))
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

from vmc_compliance_baseline import SpringCarriageVMC, SpringCarriageConfig


class VMCTorqueBaseline:
    """Spring-carriage wrench mapped to joint torque (stable, no explicit damper)."""

    family = "vmc_torque_baseline"

    def __init__(self, config: SpringCarriageConfig, residual_torque_limits: np.ndarray) -> None:
        self.baseline = SpringCarriageVMC(config)
        self.config = config
        self.residual_torque_limits = np.asarray(residual_torque_limits, dtype=float).copy()

    def reset(self) -> None:
        self.baseline.reset()

    def act(self, joint_position, joint_velocity, nominal_twist,
            hand_jacobian, pose_error=None, twist_error=None):
        if pose_error is None or twist_error is None:
            raise ValueError("torque VMC requires WBC pose/twist errors")
        if hand_jacobian is None:
            raise ValueError("torque VMC requires the hand Jacobian")

        # Advance the carriage (its internal dynamics provide damping)
        self.baseline.act(pose_error, twist_error)

        # Map the spring reaction wrench to joint torque
        # The carriage offset represents how far the "virtual reference" has
        # yielded. The spring pulls the carriage back; the REACTION on the
        # hand is in the yield direction, softening the impact.
        J = np.asarray(hand_jacobian, dtype=float)
        spring = self.baseline.saturation * np.tanh(
            self.baseline.ee_stiffness * self.baseline.offset / self.baseline.saturation)
        wrench = -spring  # reaction on hand (yield direction)
        torque = J.T @ wrench
        bounded = np.clip(torque, -self.residual_torque_limits, self.residual_torque_limits)
        clipped = np.clip(bounded / self.residual_torque_limits, -1.0, 1.0)

        from vmc_compliance_baseline import VMCComplianceAction
        return VMCComplianceAction(
            bounded_filter_action=clipped, wbc_scale=1.0,
            yielding_twist=np.zeros(6), raw_readout=clipped.copy(),
        )

    def save_npz(self, path: Path) -> None:
        np.savez_compressed(
            path, controller_family=np.asarray([self.family]),
            config_json=np.asarray([json.dumps(asdict(self.config))]),
            residual_limits=self.residual_torque_limits)

    @classmethod
    def from_npz(cls, path: Path) -> "VMCTorqueBaseline":
        with np.load(path, allow_pickle=False) as archive:
            if str(archive["controller_family"][0]) != cls.family:
                raise ValueError(f"{path}: not a {cls.family} checkpoint")
            config = SpringCarriageConfig(**json.loads(str(archive["config_json"][0])))
            return cls(config, archive["residual_limits"])
