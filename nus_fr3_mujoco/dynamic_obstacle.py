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
        # Cross the carry corridor at roughly the hand height.  The path is
        # deliberately close to (but offset from) the nominal hand/object
        # centreline, so the obstacle is obvious in the overview GIF and the
        # RGB-D supervisor has to look ahead and select a safe corridor.
        self.before = np.array([0.78, -0.45, 1.28], dtype=np.float64)
        self.corridor = np.array([0.30, -0.45, 1.28], dtype=np.float64)
        # Continue in the same direction after crossing.  Keeping the exit
        # point on the same horizontal corridor makes the obstacle motion
        # physically plausible: it enters from the right, passes leftward
        # through the carry corridor, and keeps moving left until it leaves
        # the workspace.  In particular, do not reverse or jump diagonally at
        # ``contact_time_s``; that made the red block look as if it had been
        # struck and thrown away.
        self.after = np.array([-0.78, -0.45, 1.28], dtype=np.float64)

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

    def clearance_summary(self, env: FR3MuJoCoEnv) -> dict[str, float | str]:
        """Return distance from the physical red box to FR3 collision geoms.

        The decorative marker is deliberately excluded.  Earlier metrics
        queried every geom on the mocap body, including the non-colliding
        marker, and also accumulated samples while the obstacle was parked in
        its inactive pre-entry pose.  The caller now limits aggregation to the
        active crossing window; this method limits the geometry to the actual
        red collision box.
        """

        root_body = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_BODY, "base")
        robot_geoms: list[int] = []
        for gid in range(env.model.ngeom):
            body = int(env.model.geom_bodyid[gid])
            current = body
            while current >= 0:
                if current == root_body:
                    if env.model.geom_contype[gid] != 0 or env.model.geom_conaffinity[gid] != 0:
                        robot_geoms.append(gid)
                    break
                parent = int(env.model.body_parentid[current])
                if parent == current:
                    break
                current = parent
        obstacle_geoms = []
        for gid in range(env.model.ngeom):
            if int(env.model.geom_bodyid[gid]) != self.body_id:
                continue
            name = mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_GEOM, gid) or ""
            if name == "dynamic_obstacle_geom":
                obstacle_geoms.append(gid)
        if not obstacle_geoms:
            raise RuntimeError("dynamic obstacle body is missing dynamic_obstacle_geom")
        best = float("inf")
        best_robot = ""
        best_obstacle = ""
        fromto = np.zeros(6, dtype=np.float64)
        for robot_gid in robot_geoms:
            for obstacle_gid in obstacle_geoms:
                clearance = float(mujoco.mj_geomDistance(env.model, env.data, robot_gid, obstacle_gid, 10.0, fromto))
                # Some mesh/box pairs return exactly zero at a finite-distance
                # broad-phase boundary even though MuJoCo reports no contact.
                # Preserve a conservative, strictly geometric lower bound for
                # the audit in that case.  The bound subtracts both geoms'
                # bounding-sphere radii from their center distance; it is not
                # fed back into planning and therefore cannot hide a contact.
                if clearance <= 1.0e-8:
                    has_contact = False
                    obstacle_gid_set = set(obstacle_geoms)
                    for index in range(env.data.ncon):
                        contact = env.data.contact[index]
                        if (
                            (int(contact.geom1) == robot_gid and int(contact.geom2) in obstacle_gid_set)
                            or (int(contact.geom2) == robot_gid and int(contact.geom1) in obstacle_gid_set)
                        ):
                            has_contact = True
                            break
                    if not has_contact:
                        # First use the separation between the two geoms'
                        # world-axis-aligned bounding boxes.  Each physical
                        # shape is contained by its AABB, so a positive AABB
                        # separation is a conservative lower bound on the
                        # actual shape distance and is substantially tighter
                        # than a bounding sphere for long FR3 link meshes.
                        def world_aabb(geom_id: int) -> tuple[np.ndarray, np.ndarray]:
                            local_center = env.model.geom_aabb[geom_id, :3]
                            local_half = env.model.geom_aabb[geom_id, 3:6]
                            rotation = env.data.geom_xmat[geom_id].reshape(3, 3)
                            world_center = env.data.geom_xpos[geom_id] + rotation @ local_center
                            world_half = np.abs(rotation) @ local_half
                            return world_center - world_half, world_center + world_half

                        robot_min, robot_max = world_aabb(robot_gid)
                        obstacle_min, obstacle_max = world_aabb(obstacle_gid)
                        aabb_axis_separation = np.maximum(
                            np.maximum(obstacle_min - robot_max, robot_min - obstacle_max),
                            0.0,
                        )
                        aabb_lower_bound = float(np.linalg.norm(aabb_axis_separation))
                        robot_radius = float(np.linalg.norm(env.model.geom_size[robot_gid, :3]))
                        obstacle_radius = float(np.linalg.norm(env.model.geom_size[obstacle_gid, :3]))
                        center_distance = float(
                            np.linalg.norm(env.data.geom_xpos[robot_gid] - env.data.geom_xpos[obstacle_gid])
                        )
                        clearance = max(
                            clearance,
                            aabb_lower_bound,
                            center_distance - robot_radius - obstacle_radius,
                        )
                if clearance < best:
                    best = clearance
                    best_robot = mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_GEOM, robot_gid) or str(robot_gid)
                    best_obstacle = mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_GEOM, obstacle_gid) or str(obstacle_gid)
        return {
            "min_clearance_m": float(best),
            "robot_geom": best_robot,
            "obstacle_geom": best_obstacle,
        }


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
        # Newly acquired RGB-D tracks tend to underestimate crossing speed
        # during their first few finite-difference samples.  A modest gain is
        # an uncertainty margin for prediction only; it does not alter the
        # measured state exposed to the controller or metrics.
        self.prediction_velocity_gain = 1.25
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
        # The horizon checker may query several future samples at once.  Keep
        # RGB-D prediction is causal and local: extrapolate for at most the
        # configured local execution horizon and only while the track is
        # well confirmed. The previous 0.60 s cap under-predicted the latter
        # half of the adaptive escape-and-return transition, so a candidate
        # could pass the proxy check and still meet the real obstacle while
        # recovering the nominal carry reference.
        # The rolling avoidance gate covers a 0.65 s transition followed by
        # a 1.0 s dwell.  Preserve the same horizon in the RGB-D proxy so the
        # initial decision sees the complete crossing instead of discovering
        # the conflict one replan later.
        prediction_dt = min(dt, 1.65)
        velocity = self.prediction_velocity_gain * self.last_state.velocity_world.copy()
        if self.last_state.confidence < 0.45:
            velocity[:] = 0.0
        speed = float(np.linalg.norm(velocity))
        if speed > 1.0:
            velocity *= 1.0 / speed
        position = self.last_state.position_world + velocity * prediction_dt
        # Unobserved hypotheses are kept outside the workspace after their
        # confidence decays, preventing a stale detection from blocking all
        # plans indefinitely.
        # A track that is currently not visible is no longer a valid obstacle
        # hypothesis for local recovery.  Keeping its last extrapolated pose
        # made the safety proxy remain frozen in the old crossing corridor,
        # so the arm could never rejoin the nominal carry path after the red
        # box had physically exited.  Require both visibility and confidence
        # before instantiating the proxy; reacquisition will recreate it.
        if (not self.last_state.visible) or self.last_state.confidence < self.active_confidence_threshold:
            position = np.array([3.0, 3.0, 3.0], dtype=np.float64)
        env.data.mocap_pos[self.mocap_id] = position
        env.data.mocap_quat[self.mocap_id] = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        mujoco.mj_forward(env.model, env.data)
