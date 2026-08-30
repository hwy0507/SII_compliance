"""Small, dependency-free contracts for the NUS -> FR3 migration.

The upstream project mixes Fetch base/torso/arm waypoints with ROS and
ManiSkill objects.  These contracts keep the migration boundary explicit so
the MuJoCo controller never receives a silently mis-shaped Fetch action.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple


def _vector(values: Iterable[float], size: int, name: str) -> Tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if len(result) != size:
        raise ValueError(f"{name} must contain {size} values, got {len(result)}")
    return result


@dataclass(frozen=True)
class FetchWaypoint:
    """A waypoint emitted by the NUS/Fetch side of the pipeline.

    ``whole_body`` follows the repository convention:
    ``[base_x, base_y, base_yaw, torso, arm_1, ..., arm_7]``.
    ``arm`` is also accepted for an 8-DoF ``[torso, arm_1, ..., arm_7]`` path.
    """

    time_s: float
    whole_body: Tuple[float, ...]

    def __post_init__(self) -> None:
        if self.time_s < 0.0:
            raise ValueError("waypoint time must be non-negative")
        values = tuple(float(value) for value in self.whole_body)
        if len(values) not in (8, 11):
            raise ValueError(
                "Fetch waypoint must be [torso + 7 arm] or "
                "[base x/y/yaw + torso + 7 arm]"
            )
        object.__setattr__(self, "whole_body", values)

    @property
    def base(self) -> Tuple[float, float, float]:
        return (0.0, 0.0, 0.0) if len(self.whole_body) == 8 else self.whole_body[:3]

    @property
    def fetch_arm(self) -> Tuple[float, ...]:
        return self.whole_body[1:8] if len(self.whole_body) == 8 else self.whole_body[4:11]


@dataclass(frozen=True)
class FR3Waypoint:
    """A fixed-base FR3 joint waypoint in ``fr3_joint1..fr3_joint7`` order."""

    time_s: float
    q: Tuple[float, ...]
    phase: str = "track"

    def __post_init__(self) -> None:
        if self.time_s < 0.0:
            raise ValueError("FR3 waypoint time must be non-negative")
        object.__setattr__(self, "q", _vector(self.q, 7, "FR3 q"))


@dataclass(frozen=True)
class PoseWaypoint:
    """Task-space waypoint used between Fetch FK and FR3 IK."""

    time_s: float
    position_xyz: Tuple[float, float, float]
    quaternion_xyzw: Tuple[float, float, float, float]
    phase: str = "track"

    def __post_init__(self) -> None:
        if self.time_s < 0.0:
            raise ValueError("pose waypoint time must be non-negative")
        object.__setattr__(self, "position_xyz", _vector(self.position_xyz, 3, "position_xyz"))
        object.__setattr__(self, "quaternion_xyzw", _vector(self.quaternion_xyzw, 4, "quaternion_xyzw"))


@dataclass(frozen=True)
class MigrationConfig:
    """Configuration that defines what is and is not migrated."""

    fixed_base_xyz: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    fixed_base_yaw: float = 0.0
    reject_base_motion: bool = True
    nominal_dt_s: float = 0.04
    max_joint_speed_rad_s: float = 1.25

    def __post_init__(self) -> None:
        object.__setattr__(self, "fixed_base_xyz", _vector(self.fixed_base_xyz, 3, "fixed_base_xyz"))
        if self.nominal_dt_s <= 0.0:
            raise ValueError("nominal_dt_s must be positive")
        if self.max_joint_speed_rad_s <= 0.0:
            raise ValueError("max_joint_speed_rad_s must be positive")
