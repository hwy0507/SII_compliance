"""Nominal FR3 velocity servo used below the migrated NUS trajectory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .contracts import FR3Waypoint
from .mujoco_env import FR3MuJoCoEnv, FR3State


@dataclass(frozen=True)
class NominalCommand:
    q_cmd: np.ndarray
    qdot_cmd: np.ndarray
    torque: np.ndarray


class FR3NominalVelocityServo:
    """Causal joint-space servo with gravity/bias compensation.

    This is the low-level nominal controller only. It does not inspect the
    scene or contacts. A learned controller can add a bounded torque residual
    after ``compute`` and before ``FR3MuJoCoEnv.step``.
    """

    def __init__(
        self,
        env: FR3MuJoCoEnv,
        *,
        kp: Iterable[float] = (18.0,) * 7,
        kv: Iterable[float] = (8.0,) * 7,
        max_joint_speed_rad_s: float = 1.25,
        max_torque_nm: Iterable[float] = (87.0, 87.0, 87.0, 87.0, 12.0, 12.0, 12.0),
    ) -> None:
        self.env = env
        self.kp = self._seven(kp, "kp")
        self.kv = self._seven(kv, "kv")
        self.max_joint_speed_rad_s = float(max_joint_speed_rad_s)
        self.max_torque_nm = self._seven(max_torque_nm, "max_torque_nm")
        if self.max_joint_speed_rad_s <= 0.0:
            raise ValueError("max_joint_speed_rad_s must be positive")

    def compute(self, state: FR3State, waypoint: FR3Waypoint) -> NominalCommand:
        q_ref = np.asarray(waypoint.q, dtype=np.float64)
        qdot_cmd = np.clip(self.kp * (q_ref - state.q), -self.max_joint_speed_rad_s, self.max_joint_speed_rad_s)
        torque = self.env.data.qfrc_bias[self.env.dof_adrs] + self.kv * (qdot_cmd - state.qdot)
        torque = np.clip(torque, -self.max_torque_nm, self.max_torque_nm)
        return NominalCommand(q_ref, qdot_cmd, torque)

    @staticmethod
    def _seven(values: Iterable[float], name: str) -> np.ndarray:
        result = np.asarray(tuple(values), dtype=np.float64)
        if result.shape != (7,) or not np.all(np.isfinite(result)):
            raise ValueError(f"{name} must be a finite seven-vector")
        return result
