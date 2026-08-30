"""Minimal native MuJoCo FR3 environment for the migration experiments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import mujoco
import numpy as np


@dataclass(frozen=True)
class FR3State:
    time_s: float
    q: np.ndarray
    qdot: np.ndarray
    q_cmd: np.ndarray
    qdot_cmd: np.ndarray
    ee_position: np.ndarray
    ee_quaternion_wxyz: np.ndarray


class FR3MuJoCoEnv:
    """Torque-actuated fixed-base FR3 wrapper.

    The class intentionally exposes only causal robot/controller state to the
    policy. Contact information is available through ``contact_summary`` for
    evaluation and teacher generation, but is never required by ``step``.
    """

    JOINT_NAMES = tuple(f"fr3_joint{i}" for i in range(1, 8))

    def __init__(
        self,
        model_path: str | Path,
        *,
        physics_dt_s: float = 0.002,
        policy_dt_s: float = 0.040,
        ee_body_name: str = "fr3_link7",
    ) -> None:
        if physics_dt_s <= 0.0 or policy_dt_s <= 0.0:
            raise ValueError("time steps must be positive")
        ratio = policy_dt_s / physics_dt_s
        if abs(ratio - round(ratio)) > 1.0e-9:
            raise ValueError("policy_dt_s must be an integer multiple of physics_dt_s")
        self.model = mujoco.MjModel.from_xml_path(str(model_path))
        self.data = mujoco.MjData(self.model)
        self.physics_dt_s = float(physics_dt_s)
        self.policy_dt_s = float(policy_dt_s)
        self.substeps = int(round(ratio))
        self.joint_ids = np.array(
            [self._require_id(mujoco.mjtObj.mjOBJ_JOINT, name) for name in self.JOINT_NAMES],
            dtype=np.int32,
        )
        self.qpos_adrs = np.array(self.model.jnt_qposadr[self.joint_ids], dtype=np.int32)
        self.dof_adrs = np.array(self.model.jnt_dofadr[self.joint_ids], dtype=np.int32)
        self.actuator_ids = np.array(
            [self._require_id(mujoco.mjtObj.mjOBJ_ACTUATOR, name) for name in self.JOINT_NAMES],
            dtype=np.int32,
        )
        self.ee_body_id = self._require_id(mujoco.mjtObj.mjOBJ_BODY, ee_body_name)
        self.q_cmd = np.zeros(7, dtype=np.float64)
        self.qdot_cmd = np.zeros(7, dtype=np.float64)
        self.reset()

    def _require_id(self, object_type: mujoco.mjtObj, name: str) -> int:
        value = mujoco.mj_name2id(self.model, object_type, name)
        if value < 0:
            raise ValueError(f"MuJoCo model is missing {object_type.name}: {name}")
        return int(value)

    @property
    def q(self) -> np.ndarray:
        return self.data.qpos[self.qpos_adrs].copy()

    @property
    def qdot(self) -> np.ndarray:
        return self.data.qvel[self.dof_adrs].copy()

    def reset(self, q: Optional[Iterable[float]] = None) -> FR3State:
        mujoco.mj_resetData(self.model, self.data)
        if q is not None:
            values = np.asarray(tuple(q), dtype=np.float64)
            if values.shape != (7,):
                raise ValueError("FR3 reset q must have shape (7,)")
            self.data.qpos[self.qpos_adrs] = values
        self.data.qvel[self.dof_adrs] = 0.0
        self.data.ctrl[:] = 0.0
        self.q_cmd = self.q.copy()
        self.qdot_cmd = np.zeros(7, dtype=np.float64)
        mujoco.mj_forward(self.model, self.data)
        return self.state()

    def step(
        self,
        torque: Iterable[float],
        *,
        q_cmd: Optional[Iterable[float]] = None,
        qdot_cmd: Optional[Iterable[float]] = None,
    ) -> FR3State:
        values = np.asarray(tuple(torque), dtype=np.float64)
        if values.shape != (7,) or not np.all(np.isfinite(values)):
            raise ValueError("torque must be a finite seven-vector")
        if q_cmd is not None:
            self.q_cmd = self._seven_vector(q_cmd, "q_cmd")
        if qdot_cmd is not None:
            self.qdot_cmd = self._seven_vector(qdot_cmd, "qdot_cmd")
        self.data.ctrl[self.actuator_ids] = values
        for _ in range(self.substeps):
            mujoco.mj_step(self.model, self.data)
        return self.state()

    def state(self) -> FR3State:
        return FR3State(
            time_s=float(self.data.time),
            q=self.q,
            qdot=self.qdot,
            q_cmd=self.q_cmd.copy(),
            qdot_cmd=self.qdot_cmd.copy(),
            ee_position=self.data.xpos[self.ee_body_id].copy(),
            ee_quaternion_wxyz=self.data.xquat[self.ee_body_id].copy(),
        )

    def jacobian(self) -> tuple[np.ndarray, np.ndarray]:
        jac_position = np.zeros((3, self.model.nv), dtype=np.float64)
        jac_rotation = np.zeros((3, self.model.nv), dtype=np.float64)
        mujoco.mj_jacBody(self.model, self.data, jac_position, jac_rotation, self.ee_body_id)
        return jac_position[:, self.dof_adrs].copy(), jac_rotation[:, self.dof_adrs].copy()

    def contact_summary(self) -> dict[str, float | int]:
        """Return evaluation-only contact data, never a policy observation."""

        max_force = 0.0
        impulse_proxy = 0.0
        contact_count = int(self.data.ncon)
        force = np.zeros(6, dtype=np.float64)
        for index in range(self.data.ncon):
            mujoco.mj_contactForce(self.model, self.data, index, force)
            magnitude = float(np.linalg.norm(force[:3]))
            max_force = max(max_force, magnitude)
            impulse_proxy += magnitude * self.physics_dt_s
        return {
            "contact_count": contact_count,
            "max_contact_force_n": max_force,
            "contact_impulse_proxy_ns": impulse_proxy,
        }

    @staticmethod
    def _seven_vector(values: Iterable[float], name: str) -> np.ndarray:
        result = np.asarray(tuple(values), dtype=np.float64)
        if result.shape != (7,) or not np.all(np.isfinite(result)):
            raise ValueError(f"{name} must be a finite seven-vector")
        return result
