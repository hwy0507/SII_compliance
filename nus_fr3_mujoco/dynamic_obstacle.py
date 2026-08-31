"""Deterministic kinematic moving-obstacle profiles for the FR3 benchmark."""

from __future__ import annotations

from dataclasses import dataclass

import mujoco
import numpy as np

from .mujoco_env import FR3MuJoCoEnv
from .scene_belief import PerceivedObstacleState


@dataclass(frozen=True)
class ObstacleState:
    time_s: float
    position: np.ndarray
    velocity: np.ndarray
    active: bool


class PredictableCrossingObstacle:
    """A mocap box that enters the carry corridor, then exits again.

    The motion is intentionally piecewise linear and fully known to the
    nominal checker. It is the first dynamic benchmark, not the final
    unpredictable-obstacle compliance scenario.
    """

    def __init__(
        self,
        model: mujoco.MjModel,
        *,
        body_name: str = "dynamic_obstacle",
        enter_time_s: float = 10.4,
        contact_time_s: float = 11.2,
        exit_time_s: float = 13.0,
    ) -> None:
        self.body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
        if self.body_id < 0:
            raise ValueError(f"MuJoCo model is missing dynamic obstacle body: {body_name}")
        self.mocap_id = int(model.body_mocapid[self.body_id])
        if self.mocap_id < 0:
            raise ValueError(f"dynamic obstacle body {body_name} must be mocap=true")
        self.enter_time_s = float(enter_time_s)
        self.contact_time_s = float(contact_time_s)
        self.exit_time_s = float(exit_time_s)
        if not (0.0 < self.enter_time_s < self.contact_time_s < self.exit_time_s):
            raise ValueError("obstacle times must satisfy 0 < enter < contact < exit")
        self.before = np.array([0.85, 0.20, 1.20], dtype=np.float64)
        # Cross the rear edge of the carry corridor.  The obstacle remains
        # visible and moving during transport, but its centreline is offset
        # from the nominal hand/object path so the safety supervisor can keep
        # the object collision-free while it performs active-view updates.
        self.corridor = np.array([0.68, 0.36, 1.70], dtype=np.float64)
        self.after = np.array([0.10, 0.36, 1.70], dtype=np.float64)

    def state(self, time_s: float) -> ObstacleState:
        t = float(time_s)
        if t < self.enter_time_s:
            return ObstacleState(t, self.before.copy(), np.zeros(3), False)
        if t < self.contact_time_s:
            ratio = (t - self.enter_time_s) / (self.contact_time_s - self.enter_time_s)
            position = (1.0 - ratio) * self.before + ratio * self.corridor
            velocity = (self.corridor - self.before) / (self.contact_time_s - self.enter_time_s)
            return ObstacleState(t, position, velocity, True)
        if t < self.exit_time_s:
            ratio = (t - self.contact_time_s) / (self.exit_time_s - self.contact_time_s)
            position = (1.0 - ratio) * self.corridor + ratio * self.after
            velocity = (self.after - self.corridor) / (self.exit_time_s - self.contact_time_s)
            return ObstacleState(t, position, velocity, True)
        return ObstacleState(t, self.after.copy(), np.zeros(3), False)

    def apply(self, env: FR3MuJoCoEnv, time_s: float) -> None:
        state = self.state(time_s)
        env.data.mocap_pos[self.mocap_id] = state.position
        env.data.mocap_quat[self.mocap_id] = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        # Mocap poses are inputs to forward kinematics. Refresh x* and camera
        # geometry before RGB-D rendering or contact evaluation consumes them.
        mujoco.mj_forward(env.model, env.data)

    def contact_summary(self, env: FR3MuJoCoEnv) -> dict[str, float | int]:
        obstacle_geoms = {
            int(gid)
            for gid in range(env.model.ngeom)
            if int(env.model.geom_bodyid[gid]) == self.body_id
        }
        count = 0
        max_force = 0.0
        contact_pairs: list[str] = []
        force = np.zeros(6, dtype=np.float64)
        for index in range(env.data.ncon):
            contact = env.data.contact[index]
            if int(contact.geom1) not in obstacle_geoms and int(contact.geom2) not in obstacle_geoms:
                continue
            count += 1
            a = mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_GEOM, int(contact.geom1)) or f"geom_{contact.geom1}"
            b = mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_GEOM, int(contact.geom2)) or f"geom_{contact.geom2}"
            contact_pairs.append(f"{a}<->{b}")
            mujoco.mj_contactForce(env.model, env.data, index, force)
            max_force = max(max_force, float(np.linalg.norm(force[:3])))
        return {"contact_count": count, "max_contact_force_n": max_force, "contact_pairs": contact_pairs}


class RGBDObstaclePredictor:
    """MuJoCo proxy driven by the latest RGB-D track, never by ground truth."""

    def __init__(self, model: mujoco.MjModel, tracker, *, body_name: str = "obstacle_prediction_proxy") -> None:
        self.body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
        if self.body_id < 0:
            raise ValueError(f"MuJoCo model is missing obstacle proxy body: {body_name}")
        self.mocap_id = int(model.body_mocapid[self.body_id])
        if self.mocap_id < 0:
            raise ValueError(f"obstacle proxy body {body_name} must be mocap=true")
        self.tracker = tracker
        self.active_confidence_threshold = 0.30
        self.last_state = PerceivedObstacleState(
            time_s=0.0,
            position_world=np.array([0.85, 0.20, 1.20], dtype=np.float64),
            velocity_world=np.zeros(3, dtype=np.float64),
            covariance_m2=0.35**2,
            confidence=0.0,
            visible=False,
        )

    def update(self, state: PerceivedObstacleState) -> None:
        self.last_state = state

    def apply(self, env: FR3MuJoCoEnv, time_s: float) -> None:
        dt = max(float(time_s) - self.last_state.time_s, 0.0)
        position = self.last_state.position_world + self.last_state.velocity_world * dt
        # Unobserved hypotheses are kept outside the workspace after their
        # confidence decays, preventing a stale detection from blocking all
        # plans indefinitely.
        if self.last_state.confidence < self.active_confidence_threshold:
            position = np.array([0.85, 0.20, 1.20], dtype=np.float64)
        env.data.mocap_pos[self.mocap_id] = position
        env.data.mocap_quat[self.mocap_id] = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        mujoco.mj_forward(env.model, env.data)
