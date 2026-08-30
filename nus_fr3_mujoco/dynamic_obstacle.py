"""Deterministic kinematic moving-obstacle profiles for the FR3 benchmark."""

from __future__ import annotations

from dataclasses import dataclass

import mujoco
import numpy as np

from .mujoco_env import FR3MuJoCoEnv


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
        enter_time_s: float = 7.0,
        contact_time_s: float = 7.8,
        exit_time_s: float = 9.6,
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
        self.corridor = np.array([0.26, -0.13, 0.99], dtype=np.float64)
        self.after = np.array([-0.20, -0.13, 1.20], dtype=np.float64)

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

    def contact_summary(self, env: FR3MuJoCoEnv) -> dict[str, float | int]:
        obstacle_geoms = {
            int(gid)
            for gid in range(env.model.ngeom)
            if int(env.model.geom_bodyid[gid]) == self.body_id
        }
        count = 0
        max_force = 0.0
        force = np.zeros(6, dtype=np.float64)
        for index in range(env.data.ncon):
            contact = env.data.contact[index]
            if int(contact.geom1) not in obstacle_geoms and int(contact.geom2) not in obstacle_geoms:
                continue
            count += 1
            mujoco.mj_contactForce(env.model, env.data, index, force)
            max_force = max(max_force, float(np.linalg.norm(force[:3])))
        return {"contact_count": count, "max_contact_force_n": max_force}
