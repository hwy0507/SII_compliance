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
        self.target_geom_id = self._require(mujoco.mjtObj.mjOBJ_GEOM, "target_object_geom")
        self.left_finger_body_id = self._require(mujoco.mjtObj.mjOBJ_BODY, "fr3_left_finger")
        self.right_finger_body_id = self._require(mujoco.mjtObj.mjOBJ_BODY, "fr3_right_finger")
        self.robot_root_body_id = self._require(mujoco.mjtObj.mjOBJ_BODY, "base")
        self.left_finger_geom_id = self._require(mujoco.mjtObj.mjOBJ_GEOM, "fr3_left_finger_collision")
        self.right_finger_geom_id = self._require(mujoco.mjtObj.mjOBJ_GEOM, "fr3_right_finger_collision")
        self.relative_position = np.zeros(3, dtype=np.float64)
        self.relative_quaternion = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        self.validation_axis_world = np.array([0.0, 0.0, 1.0], dtype=np.float64)
        self.engaged = False
        self.last_validation: dict[str, object] = {"valid": False, "reason": "not_checked"}

    def validate_grasp(
        self,
        *,
        max_finger_distance_m: float = 0.032,
        max_hand_distance_m: float = 0.17,
        max_target_tilt_deg: float = 15.0,
    ) -> dict[str, object]:
        """Validate a physical two-finger grasp without changing object state.

        This deliberately uses only current MuJoCo geometry/contact state.  It
        prevents a failed grasp from being converted into a kinematic object
        attachment merely because the controller entered ``LIFT``.
        """

        hand_position = self.env.data.xpos[self.hand_id].copy()
        object_position = self.env.data.xpos[self.object_id].copy()
        hand_distance = float(np.linalg.norm(object_position - hand_position))
        left_distance = float(
            mujoco.mj_geomDistance(
                self.env.model, self.env.data, self.left_finger_geom_id, self.target_geom_id, 0.2, np.zeros(6)
            )
        )
        right_distance = float(
            mujoco.mj_geomDistance(
                self.env.model, self.env.data, self.right_finger_geom_id, self.target_geom_id, 0.2, np.zeros(6)
            )
        )
        object_axis = self.env.data.xmat[self.object_id].reshape(3, 3)[:, 2]
        reference_axis = np.asarray(self.validation_axis_world, dtype=np.float64)
        reference_axis /= max(float(np.linalg.norm(reference_axis)), 1.0e-9)
        tilt_cos = float(np.clip(abs(np.dot(object_axis, reference_axis)), -1.0, 1.0))
        target_tilt_deg = float(np.degrees(np.arccos(tilt_cos)))
        left_contact = self._has_body_contact(self.left_finger_body_id, self.target_geom_id)
        right_contact = self._has_body_contact(self.right_finger_body_id, self.target_geom_id)
        valid = bool(
            hand_distance <= max_hand_distance_m
            and left_distance <= max_finger_distance_m
            and right_distance <= max_finger_distance_m
            and left_contact
            and right_contact
            and target_tilt_deg <= max_target_tilt_deg
        )
        if valid:
            reason = "two_finger_contact"
        elif not left_contact or not right_contact:
            reason = "missing_two_finger_contact"
        elif target_tilt_deg > max_target_tilt_deg:
            reason = "target_tilted"
        elif hand_distance > max_hand_distance_m:
            reason = "hand_too_far"
        else:
            reason = "finger_clearance_too_large"
        self.last_validation = {
            "valid": valid,
            "reason": reason,
            "hand_target_distance_m": hand_distance,
            "left_finger_target_distance_m": left_distance,
            "right_finger_target_distance_m": right_distance,
            "left_finger_contact": left_contact,
            "right_finger_contact": right_contact,
            "target_tilt_deg": target_tilt_deg,
        }
        return dict(self.last_validation)

    def engage(self) -> bool:
        if self.engaged:
            return True
        validation = self.validate_grasp()
        if not bool(validation["valid"]):
            return False
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
        return True

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

    def target_contact_summary(self) -> dict[str, object]:
        """Summarize robot-target contacts for evaluation and debugging."""

        finger_body_ids = {self.left_finger_body_id, self.right_finger_body_id}
        target_pairs: list[dict[str, object]] = []
        illegal_pairs: list[dict[str, object]] = []
        for index in range(self.env.data.ncon):
            contact = self.env.data.contact[index]
            geom_ids = {int(contact.geom1), int(contact.geom2)}
            if self.target_geom_id not in geom_ids:
                continue
            other_geom = int(contact.geom2 if int(contact.geom1) == self.target_geom_id else contact.geom1)
            other_body = int(self.env.model.geom_bodyid[other_geom])
            if not self._is_descendant(other_body, self.robot_root_body_id):
                continue
            other_name = mujoco.mj_id2name(self.env.model, mujoco.mjtObj.mjOBJ_GEOM, other_geom) or f"geom_{other_geom}"
            pair = {
                "geom": other_name,
                "distance_m": float(contact.dist),
                "finger_contact": self._is_descendant(other_body, self.left_finger_body_id)
                or self._is_descendant(other_body, self.right_finger_body_id),
            }
            target_pairs.append(pair)
            if not pair["finger_contact"]:
                illegal_pairs.append(pair)
        return {
            "target_robot_contact_count": len(target_pairs),
            "target_contact_pairs": target_pairs,
            "illegal_target_contact_count": len(illegal_pairs),
        }

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

    def _has_contact(self, geom_a: int, geom_b: int) -> bool:
        for index in range(self.env.data.ncon):
            contact = self.env.data.contact[index]
            if {int(contact.geom1), int(contact.geom2)} == {int(geom_a), int(geom_b)}:
                return True
        return False

    def _has_body_contact(self, body_id: int, geom_id: int) -> bool:
        for index in range(self.env.data.ncon):
            contact = self.env.data.contact[index]
            if int(contact.geom1) == geom_id:
                other_geom = int(contact.geom2)
            elif int(contact.geom2) == geom_id:
                other_geom = int(contact.geom1)
            else:
                continue
            other_body = int(self.env.model.geom_bodyid[other_geom])
            if self._is_descendant(other_body, body_id):
                return True
        return False

    def _is_descendant(self, body_id: int, root_body_id: int) -> bool:
        current = int(body_id)
        while current >= 0:
            if current == int(root_body_id):
                return True
            parent = int(self.env.model.body_parentid[current])
            if parent == current:
                break
            current = parent
        return False
