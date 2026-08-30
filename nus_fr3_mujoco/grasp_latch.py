"""Deterministic grasp attachment for the scripted FR3 validation task."""

from __future__ import annotations

import mujoco
import numpy as np

from .mujoco_env import FR3MuJoCoEnv


class MuJoCoGraspLatch:
    """Kinematically follow the target after a validated finger closure.

    The first scene uses an explicit follow latch rather than an instantaneous
    MuJoCo weld. This avoids a large solver impulse when a free object is still
    touching the tabletop. The measured hand/object transform is preserved,
    and the freejoint pose is updated at every policy step while engaged. This
    is a scripted visualization/evaluation aid; the research version should
    replace it with contact-only grasp success and friction stability checks.
    """

    def __init__(self, env: FR3MuJoCoEnv, *, hand_name: str = "fr3_hand", object_name: str = "target_object", weld_name: str = "target_grasp_weld") -> None:
        self.env = env
        self.hand_id = self._require(mujoco.mjtObj.mjOBJ_BODY, hand_name)
        self.object_id = self._require(mujoco.mjtObj.mjOBJ_BODY, object_name)
        self.weld_id = self._require(mujoco.mjtObj.mjOBJ_EQUALITY, weld_name)
        if env.model.eq_type[self.weld_id] != mujoco.mjtEq.mjEQ_WELD:
            raise ValueError(f"equality {weld_name} is not a weld")
        self.object_joint_id = int(env.model.body_jntadr[self.object_id])
        if self.object_joint_id < 0 or env.model.jnt_type[self.object_joint_id] != mujoco.mjtJoint.mjJNT_FREE:
            raise ValueError(f"object body {object_name} must have a freejoint")
        self.object_qposadr = int(env.model.jnt_qposadr[self.object_joint_id])
        self.object_dofadr = int(env.model.jnt_dofadr[self.object_joint_id])
        self.relative_position = np.zeros(3, dtype=np.float64)
        self.relative_quaternion = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        self.engaged = False

    def engage(self, *, reference_position: np.ndarray | None = None) -> None:
        if self.engaged:
            return
        if reference_position is not None:
            qpos = self.env.data.qpos[self.object_qposadr : self.object_qposadr + 7]
            qpos[:3] = np.asarray(reference_position, dtype=np.float64)
            self.env.data.qvel[self.object_dofadr : self.object_dofadr + 6] = 0.0
            mujoco.mj_forward(self.env.model, self.env.data)
        hand_position = self.env.data.xpos[self.hand_id].copy()
        object_position = self.env.data.xpos[self.object_id].copy()
        hand_rotation = self.env.data.xmat[self.hand_id].reshape(3, 3)
        object_rotation = self.env.data.xmat[self.object_id].reshape(3, 3)
        relative_position = hand_rotation.T @ (object_position - hand_position)
        relative_rotation = hand_rotation.T @ object_rotation
        relative_quaternion = np.zeros(4, dtype=np.float64)
        mujoco.mju_mat2Quat(relative_quaternion, relative_rotation.reshape(-1))
        self.relative_position = relative_position
        self.relative_quaternion = relative_quaternion
        self.engaged = True

    def release(self) -> None:
        if not self.engaged:
            return
        self.engaged = False

    def update(self) -> None:
        """Apply the captured hand/object transform after each physics step."""

        if not self.engaged:
            return
        hand_position = self.env.data.xpos[self.hand_id]
        hand_rotation = self.env.data.xmat[self.hand_id].reshape(3, 3)
        object_position = hand_position + hand_rotation @ self.relative_position
        object_rotation = hand_rotation @ self._quat_to_matrix(self.relative_quaternion)
        object_quaternion = np.zeros(4, dtype=np.float64)
        mujoco.mju_mat2Quat(object_quaternion, object_rotation.reshape(-1))
        qpos = self.env.data.qpos[self.object_qposadr : self.object_qposadr + 7]
        qpos[:3] = object_position
        qpos[3:7] = object_quaternion
        self.env.data.qvel[self.object_dofadr : self.object_dofadr + 6] = 0.0
        mujoco.mj_forward(self.env.model, self.env.data)

    def tracking_error_m(self) -> float:
        """Return object-position error relative to the captured hand transform."""

        if not self.engaged:
            return 0.0
        hand_position = self.env.data.xpos[self.hand_id]
        hand_rotation = self.env.data.xmat[self.hand_id].reshape(3, 3)
        expected_position = hand_position + hand_rotation @ self.relative_position
        actual_position = self.env.data.xpos[self.object_id]
        return float(np.linalg.norm(actual_position - expected_position))

    @staticmethod
    def _quat_to_matrix(quaternion: np.ndarray) -> np.ndarray:
        matrix = np.zeros(9, dtype=np.float64)
        mujoco.mju_quat2Mat(matrix, quaternion)
        return matrix.reshape(3, 3)

    def _require(self, object_type: mujoco.mjtObj, name: str) -> int:
        value = mujoco.mj_name2id(self.env.model, object_type, name)
        if value < 0:
            raise ValueError(f"MuJoCo model is missing {object_type.name}: {name}")
        return int(value)
