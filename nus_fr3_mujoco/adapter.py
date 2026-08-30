"""Task-space migration adapter from the NUS Fetch pipeline to FR3.

This module intentionally requires FK and IK callables from the caller.  That
keeps it independent of ROS, VAMP, and a particular MuJoCo WBC implementation.
The crucial rule is that Fetch joint angles are never copied into FR3 joints;
the adapter transfers the end-effector pose through a common world frame.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, sin
from typing import Callable, Iterable, List, Sequence, Tuple

from .contracts import FetchWaypoint, FR3Waypoint, MigrationConfig, PoseWaypoint

Pose = Tuple[Tuple[float, float, float, float], ...]
FetchFK = Callable[[Sequence[float]], Pose]
FR3IK = Callable[[Pose, Sequence[float]], Sequence[float] | None]


def _matmul(left: Pose, right: Pose) -> Pose:
    return tuple(
        tuple(sum(left[row][k] * right[k][col] for k in range(4)) for col in range(4))
        for row in range(4)
    )


def _base_transform(x: float, y: float, yaw: float) -> Pose:
    c, s = cos(yaw), sin(yaw)
    return (
        (c, -s, 0.0, x),
        (s, c, 0.0, y),
        (0.0, 0.0, 1.0, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )


def _pose_tuple(matrix: Sequence[Sequence[float]]) -> Pose:
    rows = tuple(tuple(float(value) for value in row) for row in matrix)
    if len(rows) != 4 or any(len(row) != 4 for row in rows):
        raise ValueError("pose must be a 4x4 homogeneous matrix")
    return rows  # type: ignore[return-value]


@dataclass
class FetchToFR3Adapter:
    """Convert NUS Fetch waypoints into a fixed-base FR3 joint trajectory."""

    fetch_fk: FetchFK
    fr3_ik: FR3IK
    config: MigrationConfig = MigrationConfig()

    def to_pose_waypoints(self, waypoints: Iterable[FetchWaypoint]) -> List[PoseWaypoint]:
        result: List[PoseWaypoint] = []
        for waypoint in waypoints:
            base = waypoint.base
            fixed = self.config.fixed_base_xyz
            base_delta = ((base[0] - fixed[0]) ** 2 + (base[1] - fixed[1]) ** 2) ** 0.5
            yaw_delta = abs(base[2] - self.config.fixed_base_yaw)
            if self.config.reject_base_motion and (base_delta > 1.0e-6 or yaw_delta > 1.0e-6):
                raise ValueError(
                    "NUS waypoint contains mobile-base motion; fixed-base FR3 "
                    "migration requires a base-free trajectory or reject_base_motion=false"
                )
            fetch_ee_in_base = _pose_tuple(self.fetch_fk(waypoint.fetch_arm))
            world_from_base = _base_transform(
                self.config.fixed_base_xyz[0],
                self.config.fixed_base_xyz[1],
                self.config.fixed_base_yaw,
            )
            world_from_ee = _matmul(world_from_base, fetch_ee_in_base)
            position = (world_from_ee[0][3], world_from_ee[1][3], world_from_ee[2][3])
            quaternion = _rotation_to_quaternion(world_from_ee)
            result.append(PoseWaypoint(waypoint.time_s, position, quaternion))
        return result

    def to_fr3_waypoints(
        self,
        waypoints: Iterable[FetchWaypoint],
        q_seed: Sequence[float],
    ) -> List[FR3Waypoint]:
        seed = tuple(float(value) for value in q_seed)
        if len(seed) != 7:
            raise ValueError("q_seed must have 7 FR3 joints")
        result: List[FR3Waypoint] = []
        for pose in self.to_pose_waypoints(waypoints):
            q = self.fr3_ik(
                _pose_matrix(pose.position_xyz, pose.quaternion_xyzw),
                seed,
            )
            if q is None:
                raise RuntimeError(f"FR3 IK failed at t={pose.time_s:.3f}s, phase={pose.phase}")
            joint_values = tuple(float(value) for value in q)
            if len(joint_values) != 7:
                raise ValueError("FR3 IK callback must return 7 joint values")
            result.append(FR3Waypoint(pose.time_s, joint_values, pose.phase))
            seed = joint_values
        return result


def _pose_matrix(position: Sequence[float], quaternion_xyzw: Sequence[float]) -> Pose:
    x, y, z, w = (float(value) for value in quaternion_xyzw)
    norm = (x * x + y * y + z * z + w * w) ** 0.5
    if norm <= 1.0e-12:
        raise ValueError("quaternion must be non-zero")
    x, y, z, w = x / norm, y / norm, z / norm, w / norm
    px, py, pz = (float(value) for value in position)
    return (
        (1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), px),
        (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), py),
        (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), pz),
        (0.0, 0.0, 0.0, 1.0),
    )


def _rotation_to_quaternion(matrix: Pose) -> Tuple[float, float, float, float]:
    """Convert a proper rotation matrix to xyzw without scipy."""

    trace = matrix[0][0] + matrix[1][1] + matrix[2][2]
    if trace > 0.0:
        scale = (trace + 1.0) ** 0.5 * 2.0
        w = 0.25 * scale
        x = (matrix[2][1] - matrix[1][2]) / scale
        y = (matrix[0][2] - matrix[2][0]) / scale
        z = (matrix[1][0] - matrix[0][1]) / scale
    elif matrix[0][0] > matrix[1][1] and matrix[0][0] > matrix[2][2]:
        scale = (1.0 + matrix[0][0] - matrix[1][1] - matrix[2][2]) ** 0.5 * 2.0
        w = (matrix[2][1] - matrix[1][2]) / scale
        x = 0.25 * scale
        y = (matrix[0][1] + matrix[1][0]) / scale
        z = (matrix[0][2] + matrix[2][0]) / scale
    elif matrix[1][1] > matrix[2][2]:
        scale = (1.0 + matrix[1][1] - matrix[0][0] - matrix[2][2]) ** 0.5 * 2.0
        w = (matrix[0][2] - matrix[2][0]) / scale
        x = (matrix[0][1] + matrix[1][0]) / scale
        y = 0.25 * scale
        z = (matrix[1][2] + matrix[2][1]) / scale
    else:
        scale = (1.0 + matrix[2][2] - matrix[0][0] - matrix[1][1]) ** 0.5 * 2.0
        w = (matrix[1][0] - matrix[0][1]) / scale
        x = (matrix[0][2] + matrix[2][0]) / scale
        y = (matrix[1][2] + matrix[2][1]) / scale
        z = 0.25 * scale
    return (x, y, z, w)
