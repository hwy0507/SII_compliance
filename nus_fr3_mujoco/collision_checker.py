"""Swept-volume clearance checks for fixed-base FR3 trajectories."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

import mujoco
import numpy as np

from .mujoco_env import FR3MuJoCoEnv


@dataclass(frozen=True)
class ClearanceEvent:
    time_s: float
    clearance_m: float
    robot_geom: str
    obstacle_geom: str


@dataclass(frozen=True)
class SweptVolumeReport:
    sampled_steps: int
    pair_checks: int
    min_clearance_m: float
    min_clearance_time_s: float
    min_clearance_robot_geom: str
    min_clearance_obstacle_geom: str
    collision_count: int
    near_collision_count: int
    events: tuple[ClearanceEvent, ...]

    @property
    def collision_free(self) -> bool:
        return self.collision_count == 0


class FR3SweptVolumeChecker:
    """Evaluate all FR3 collision geoms against non-target scene obstacles."""

    def __init__(
        self,
        env: FR3MuJoCoEnv,
        *,
        robot_root_body: str = "base",
        excluded_obstacle_bodies: Iterable[str] = ("target_object",),
        excluded_obstacle_geoms: Iterable[str] = ("fr3_mount_plate",),
        safety_margin_m: float = 0.015,
        obstacle_state_fn: Callable[[FR3MuJoCoEnv, float], None] | None = None,
        strict_zero_clearance: bool = False,
        included_obstacle_geoms: Iterable[str] | None = None,
    ) -> None:
        self.env = env
        self.model = env.model
        self.safety_margin_m = float(safety_margin_m)
        self.obstacle_state_fn = obstacle_state_fn
        self.strict_zero_clearance = bool(strict_zero_clearance)
        included = None if included_obstacle_geoms is None else set(included_obstacle_geoms)
        if self.safety_margin_m < 0.0:
            raise ValueError("safety_margin_m must be non-negative")
        root_body = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, robot_root_body)
        if root_body < 0:
            raise ValueError(f"MuJoCo model is missing robot root body: {robot_root_body}")
        excluded = set(excluded_obstacle_bodies)
        excluded_geoms = set(excluded_obstacle_geoms)
        self.robot_geom_ids = tuple(
            gid
            for gid in range(self.model.ngeom)
            if self._is_descendant(int(self.model.geom_bodyid[gid]), int(root_body))
            and (self.model.geom_contype[gid] != 0 or self.model.geom_conaffinity[gid] != 0)
        )
        self.obstacle_geom_ids = tuple(
            gid
            for gid in range(self.model.ngeom)
            if not self._is_descendant(int(self.model.geom_bodyid[gid]), int(root_body))
            and self._body_name(gid) not in excluded
            and self._geom_name(gid) not in excluded_geoms
            and (included is None or self._geom_name(gid) in included)
            and (self.model.geom_contype[gid] != 0 or self.model.geom_conaffinity[gid] != 0)
        )
        if not self.robot_geom_ids:
            raise ValueError("no robot collision geoms found")
        if not self.obstacle_geom_ids:
            raise ValueError("no obstacle collision geoms found")

    def check_trajectory(
        self,
        q_samples: np.ndarray,
        time_samples: np.ndarray,
        *,
        near_collision_margin_m: float | None = None,
        max_events: int = 64,
        obstacle_state_fn: Callable[[FR3MuJoCoEnv, float], None] | None = None,
    ) -> SweptVolumeReport:
        q_samples = np.asarray(q_samples, dtype=np.float64)
        time_samples = np.asarray(time_samples, dtype=np.float64)
        if q_samples.ndim != 2 or q_samples.shape[1] != 7:
            raise ValueError("q_samples must have shape [N, 7]")
        if time_samples.shape != (len(q_samples),):
            raise ValueError("time_samples must have shape [N]")
        if len(q_samples) == 0:
            raise ValueError("trajectory must contain at least one sample")
        if not np.all(np.isfinite(q_samples)) or not np.all(np.isfinite(time_samples)):
            raise ValueError("trajectory samples must be finite")
        if np.any(np.diff(time_samples) < 0.0):
            raise ValueError("time_samples must be nondecreasing")

        near_margin = self.safety_margin_m if near_collision_margin_m is None else float(near_collision_margin_m)
        if near_margin < 0.0:
            raise ValueError("near_collision_margin_m must be non-negative")

        original_qpos = self.env.data.qpos.copy()
        original_qvel = self.env.data.qvel.copy()
        original_mocap_pos = self.env.data.mocap_pos.copy()
        original_mocap_quat = self.env.data.mocap_quat.copy()
        original_time = float(self.env.data.time)
        min_clearance = float("inf")
        min_time = float(time_samples[0])
        min_robot = ""
        min_obstacle = ""
        collision_count = 0
        near_collision_count = 0
        events: list[ClearanceEvent] = []
        pair_checks = 0
        try:
            for q, time_s in zip(q_samples, time_samples):
                state_fn = self.obstacle_state_fn if obstacle_state_fn is None else obstacle_state_fn
                if state_fn is not None:
                    state_fn(self.env, float(time_s))
                self.env.data.qpos[self.env.qpos_adrs] = q
                mujoco.mj_forward(self.model, self.env.data)
                for robot_gid in self.robot_geom_ids:
                    for obstacle_gid in self.obstacle_geom_ids:
                        fromto = np.zeros(6, dtype=np.float64)
                        clearance = float(mujoco.mj_geomDistance(self.model, self.env.data, robot_gid, obstacle_gid, 10.0, fromto))
                        pair_checks += 1
                        if clearance < min_clearance:
                            min_clearance = clearance
                            min_time = float(time_s)
                            min_robot = self._geom_name(robot_gid)
                            min_obstacle = self._geom_name(obstacle_gid)
                        # MuJoCo reports exactly zero for touching/degenerate
                        # distance queries.  For the prediction proxy a zero
                        # gap is not acceptable for an execution candidate:
                        # even if the simulator does not emit a contact at
                        # that sample, the rendered trajectory is visually
                        # tangent and time discretization can turn it into a
                        # collision.  The proxy-specific strict-zero switch
                        # below turns that boundary case into a hard
                        # collision; ordinary scene geoms retain the legacy
                        # near-clearance semantics.
                        obstacle_name = self._geom_name(obstacle_gid)
                        proxy_zero_contact = bool(
                            self.strict_zero_clearance
                            and clearance <= 1.0e-6
                            and obstacle_name in {
                                "obstacle_prediction_proxy_geom",
                                "dynamic_obstacle_geom",
                            }
                        )
                        if clearance < -1.0e-8 or proxy_zero_contact:
                            collision_count += 1
                            if len(events) < max_events:
                                events.append(
                                    ClearanceEvent(
                                        time_s=float(time_s),
                                        clearance_m=clearance,
                                        robot_geom=self._geom_name(robot_gid),
                                        obstacle_geom=self._geom_name(obstacle_gid),
                                    )
                                )
                        elif 0.0 < clearance < near_margin:
                            near_collision_count += 1
                            if len(events) < max_events:
                                events.append(
                                    ClearanceEvent(
                                        time_s=float(time_s),
                                        clearance_m=clearance,
                                        robot_geom=self._geom_name(robot_gid),
                                        obstacle_geom=self._geom_name(obstacle_gid),
                                    )
                                )
        finally:
            self.env.data.qpos[:] = original_qpos
            self.env.data.qvel[:] = original_qvel
            self.env.data.mocap_pos[:] = original_mocap_pos
            self.env.data.mocap_quat[:] = original_mocap_quat
            self.env.data.time = original_time
            mujoco.mj_forward(self.model, self.env.data)

        return SweptVolumeReport(
            sampled_steps=len(q_samples),
            pair_checks=pair_checks,
            min_clearance_m=float(min_clearance),
            min_clearance_time_s=min_time,
            min_clearance_robot_geom=min_robot,
            min_clearance_obstacle_geom=min_obstacle,
            collision_count=collision_count,
            near_collision_count=near_collision_count,
            events=tuple(events),
        )

    @staticmethod
    def interpolate_segments(segments: list, q_start: np.ndarray, sample_dt_s: float = 0.02) -> tuple[np.ndarray, np.ndarray]:
        """Densely sample DemoSegment-like objects for a swept-volume check."""

        if sample_dt_s <= 0.0:
            raise ValueError("sample_dt_s must be positive")
        q_start = np.asarray(q_start, dtype=np.float64)
        if q_start.shape != (7,):
            raise ValueError("q_start must have shape [7]")
        samples: list[np.ndarray] = []
        times: list[float] = []
        elapsed = 0.0
        previous = q_start.copy()
        for segment in segments:
            count = max(1, int(np.ceil(float(segment.duration_s) / sample_dt_s)))
            for index in range(count):
                ratio = (index + 1) / count
                smooth = ratio * ratio * (3.0 - 2.0 * ratio)
                samples.append((1.0 - smooth) * previous + smooth * np.asarray(segment.q, dtype=np.float64))
                times.append(elapsed + ratio * float(segment.duration_s))
            elapsed += float(segment.duration_s)
            previous = np.asarray(segment.q, dtype=np.float64).copy()
        return np.asarray(samples, dtype=np.float64), np.asarray(times, dtype=np.float64)

    def _is_descendant(self, body_id: int, root_body_id: int) -> bool:
        current = body_id
        while current >= 0:
            if current == root_body_id:
                return True
            parent = int(self.model.body_parentid[current])
            if parent == current:
                break
            current = parent
        return False

    def _body_name(self, geom_id: int) -> str:
        return mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_BODY, int(self.model.geom_bodyid[geom_id])) or ""

    def _geom_name(self, geom_id: int) -> str:
        return mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, geom_id) or f"geom_{geom_id}"
