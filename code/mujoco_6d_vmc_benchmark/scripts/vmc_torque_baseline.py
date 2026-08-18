#!/usr/bin/env python3
"""Torque-mode VMC baseline: J^T w residual injection on the WBC servo.

In execution_mode="torque_residual" the environment interprets the policy
action as a per-joint residual torque (units of the residual budget).  This
baseline maps the spring--carriage coupling wrench w (the saturating EE
spring + damper reaction, identical to the twist-layer variant) through the
hand Jacobian:  tau = clip(J^T w, budget).  The WBC velocity servo keeps
tracking the nominal path underneath, so the collision is softened in the
force domain -- the impedance-style compliance the original VMC papers use.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from vmc_compliance_baseline import SpringCarriageVMC, SpringCarriageConfig


class VMCTorqueBaseline:
    """Spring-carriage wrench -> joint-torque residual controller."""

    family = "vmc_torque_baseline"

    def __init__(self, config: SpringCarriageConfig, residual_torque_limits: np.ndarray) -> None:
        self.baseline = SpringCarriageVMC(config)
        self.config = config
        self.residual_torque_limits = np.asarray(residual_torque_limits, dtype=float).copy()

    def reset(self) -> None:
        self.baseline.reset()

    def act(
        self,
        joint_position: np.ndarray,
        joint_velocity: np.ndarray,
        nominal_twist: np.ndarray,
        hand_jacobian: np.ndarray,
        pose_error: np.ndarray | None = None,
        twist_error: np.ndarray | None = None,
    ) -> np.ndarray:
        """Return the 7-D bounded action (per-joint torque in budget units)."""

        if pose_error is None or twist_error is None:
            raise ValueError("the torque VMC baseline requires WBC pose/twist errors")
        if hand_jacobian is None or hand_jacobian.shape != (6, 7):
            raise ValueError("the torque VMC baseline requires the 6x7 hand Jacobian")
        # Advance the carriage and read the coupling wrench (the saturated
        # spring--damper reaction on the carriage offset dynamics).
        action_twist = self.baseline.act(pose_error, twist_error)
        offset_rate = action_twist[1:]
        # The coupling wrench magnitude: the spring reaction on the carriage
        # equals the same saturating spring evaluated at the offset state.
        spring = self.baseline.saturation * np.tanh(
            self.baseline.ee_stiffness * self.baseline.offset / self.baseline.saturation)
        damper = self.baseline.ee_damping * (offset_rate - self.baseline.offset_rate)
        wrench = -(spring + damper)  # acts on the hand along the yield axis
        torque = hand_jacobian.T @ wrench
        bounded = np.clip(torque, -self.residual_torque_limits, self.residual_torque_limits)
        clipped = np.clip(bounded / self.residual_torque_limits, -1.0, 1.0)
        # Wrap in a DirectESNAction-compatible namedtuple for the rollout
        from vmc_compliance_baseline import VMCComplianceAction

        return VMCComplianceAction(
            bounded_filter_action=clipped, wbc_scale=1.0,
            yielding_twist=np.zeros(6), raw_readout=clipped.copy(),
        )

    def save_npz(self, path: Path) -> None:
        import json
        from dataclasses import asdict

        np.savez_compressed(
            path, controller_family=np.asarray([self.family]),
            config_json=np.asarray([json.dumps(asdict(self.config))]),
            residual_limits=self.residual_torque_limits,
        )

    @classmethod
    def from_npz(cls, path: Path) -> "VMCTorqueBaseline":
        import json

        with np.load(path, allow_pickle=False) as archive:
            if str(archive["controller_family"][0]) != cls.family:
                raise ValueError(f"{path}: not a {cls.family} checkpoint")
            config = SpringCarriageConfig(**json.loads(str(archive["config_json"][0])))
            return cls(config, archive["residual_limits"])
