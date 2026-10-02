"""FLASK-style differential-flat joint-space planning for fixed-base FR3/Panda.

For a fully actuated manipulator the joint configuration ``q`` is a flat
output.  Taking the pseudo-control to be ``q_ddot`` turns the flat state
``(q, q_dot)`` into a double integrator.  This module implements the closed
form cubic Hermite steering primitive from FLASK and a small RRT-Connect-like
planner around it.  The planner is deliberately independent of MuJoCo: a
caller supplies an optional ``collision_fn(q)`` and can therefore use the same
primitive with a simulator, a real robot scene, or a geometric checker.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

import numpy as np

Array = np.ndarray
CollisionFn = Callable[[Array], bool]


@dataclass(frozen=True)
class JointSegment:
    """A dynamically feasible cubic segment in joint space.

    The coefficients satisfy position and velocity boundary conditions at
    both ends, which is the fixed-time LQ minimum-acceleration solution for a
    double integrator (the ``r=2`` manipulator case in FLASK).
    """

    q0: Array
    v0: Array
    q1: Array
    v1: Array
    duration: float

    def __post_init__(self) -> None:
        q0, v0, q1, v1 = (np.asarray(x, dtype=float).copy() for x in (self.q0, self.v0, self.q1, self.v1))
        if q0.ndim != 1 or v0.shape != q0.shape or q1.shape != q0.shape or v1.shape != q0.shape:
            raise ValueError("all segment boundary vectors must have the same one-dimensional shape")
        if not np.all(np.isfinite(np.concatenate((q0, v0, q1, v1)))) or not np.isfinite(self.duration):
            raise ValueError("segment boundaries and duration must be finite")
        if self.duration <= 0.0:
            raise ValueError("segment duration must be positive")
        for value in (q0, v0, q1, v1):
            value.setflags(write=False)
        object.__setattr__(self, "q0", q0)
        object.__setattr__(self, "v0", v0)
        object.__setattr__(self, "q1", q1)
        object.__setattr__(self, "v1", v1)

    @property
    def dof(self) -> int:
        return int(self.q0.size)

    @property
    def _a2(self) -> Array:
        delta = self.q1 - self.q0
        t = self.duration
        return 3.0 * delta / t**2 - (2.0 * self.v0 + self.v1) / t

    @property
    def _a3(self) -> Array:
        delta = self.q1 - self.q0
        t = self.duration
        return -2.0 * delta / t**3 + (self.v0 + self.v1) / t**2

    def sample(self, time_s: float | Array) -> tuple[Array, Array, Array]:
        """Return ``(q, q_dot, q_ddot)`` at scalar or vector times."""

        tau = np.asarray(time_s, dtype=float)
        if not np.all(np.isfinite(tau)):
            raise ValueError("sample time must be finite")
        tau = np.clip(tau, 0.0, self.duration)
        a2, a3 = self._a2, self._a3
        q = self.q0 + tau[..., None] * self.v0 + tau[..., None] ** 2 * a2 + tau[..., None] ** 3 * a3
        v = self.v0 + 2.0 * tau[..., None] * a2 + 3.0 * tau[..., None] ** 2 * a3
        a = 2.0 * a2 + 6.0 * tau[..., None] * a3
        if tau.ndim == 0:
            return q[0] if q.ndim > 1 else q, v[0] if v.ndim > 1 else v, a[0] if a.ndim > 1 else a
        return q, v, a


@dataclass(frozen=True)
class FlaskTrajectory:
    """A continuous piecewise-cubic trajectory returned by the planner."""

    segments: tuple[JointSegment, ...]

    def __post_init__(self) -> None:
        if not self.segments:
            raise ValueError("a trajectory needs at least one segment")
        dof = self.segments[0].dof
        if any(segment.dof != dof for segment in self.segments):
            raise ValueError("all trajectory segments must have the same DOF")

    @property
    def dof(self) -> int:
        return self.segments[0].dof

    @property
    def duration(self) -> float:
        return float(sum(segment.duration for segment in self.segments))

    @property
    def start(self) -> tuple[Array, Array]:
        segment = self.segments[0]
        return segment.q0.copy(), segment.v0.copy()

    @property
    def goal(self) -> tuple[Array, Array]:
        segment = self.segments[-1]
        return segment.q1.copy(), segment.v1.copy()

    def sample(self, time_s: float | Array) -> tuple[Array, Array, Array]:
        """Evaluate the piecewise path, including its acceleration."""

        times = np.asarray(time_s, dtype=float)
        if times.ndim != 0:
            flat = times.reshape(-1)
            values = [self.sample(float(t)) for t in flat]
            q = np.stack([x[0] for x in values]).reshape(times.shape + (self.dof,))
            v = np.stack([x[1] for x in values]).reshape(times.shape + (self.dof,))
            a = np.stack([x[2] for x in values]).reshape(times.shape + (self.dof,))
            return q, v, a
        if not np.isfinite(times):
            raise ValueError("sample time must be finite")
        remaining = float(np.clip(times, 0.0, self.duration))
        for segment in self.segments:
            if remaining <= segment.duration:
                return segment.sample(remaining)
            remaining -= segment.duration
        return self.segments[-1].sample(self.segments[-1].duration)

    def sample_times(self, count_per_segment: int = 32) -> tuple[Array, Array, Array, Array]:
        if count_per_segment < 2:
            raise ValueError("count_per_segment must be at least two")
        all_t: list[float] = []
        all_q: list[Array] = []
        all_v: list[Array] = []
        all_a: list[Array] = []
        offset = 0.0
        for i, segment in enumerate(self.segments):
            local = np.linspace(0.0, segment.duration, count_per_segment)
            if i:
                local = local[1:]
            q, v, a = segment.sample(local)
            all_t.extend((offset + local).tolist())
            all_q.extend(q)
            all_v.extend(v)
            all_a.extend(a)
            offset += segment.duration
        return np.asarray(all_t), np.asarray(all_q), np.asarray(all_v), np.asarray(all_a)


@dataclass(frozen=True)
class FlaskPlannerConfig:
    """Limits and deterministic search settings for an FR3 planner."""

    velocity_limits: Array
    acceleration_limits: Array
    joint_lower: Array
    joint_upper: Array
    steering_time: float = 0.8
    min_steering_time: float = 0.08
    max_steering_time: float = 3.0
    samples_per_segment: int = 25
    max_iterations: int = 1500
    goal_bias: float = 0.15
    goal_position_tolerance: float = 0.025
    goal_velocity_tolerance: float = 0.08
    seed: int = 0

    def __post_init__(self) -> None:
        arrays = [np.asarray(x, dtype=float) for x in (self.velocity_limits, self.acceleration_limits, self.joint_lower, self.joint_upper)]
        if any(x.ndim != 1 for x in arrays) or len({x.size for x in arrays}) != 1:
            raise ValueError("joint limits must be one-dimensional arrays with equal length")
        if any(not np.all(np.isfinite(x)) for x in arrays):
            raise ValueError("joint limits must be finite")
        if np.any(arrays[0] <= 0.0) or np.any(arrays[1] <= 0.0) or np.any(arrays[3] <= arrays[2]):
            raise ValueError("velocity/acceleration limits must be positive and joint lower < upper")
        if not (0.0 < self.min_steering_time <= self.steering_time <= self.max_steering_time):
            raise ValueError("steering times must satisfy 0 < min <= default <= max")
        if self.samples_per_segment < 3 or self.max_iterations < 1:
            raise ValueError("segment sampling and iteration limits are too small")
        if not 0.0 <= self.goal_bias <= 1.0:
            raise ValueError("goal_bias must be in [0, 1]")
        for x in arrays:
            x.setflags(write=False)
        object.__setattr__(self, "velocity_limits", arrays[0])
        object.__setattr__(self, "acceleration_limits", arrays[1])
        object.__setattr__(self, "joint_lower", arrays[2])
        object.__setattr__(self, "joint_upper", arrays[3])

    @property
    def dof(self) -> int:
        return int(self.velocity_limits.size)


@dataclass
class _Node:
    q: Array
    v: Array
    parent: int | None
    segment: JointSegment | None


class FlaskJointPlanner:
    """Sampling-based planner using closed-form FLASK steering primitives.

    The planner's tree lives in the flat state ``(q, q_dot)``.  Every edge is
    a cubic Hermite BVP solution, so a returned edge is dynamically feasible
    up to the configured sampling resolution.  Set ``collision_fn`` to a
    function returning ``True`` for a colliding joint configuration.
    """

    def __init__(self, config: FlaskPlannerConfig, collision_fn: CollisionFn | None = None) -> None:
        self.config = config
        self.collision_fn = collision_fn
        self._rng = np.random.default_rng(config.seed)

    def _collision(self, q: Array) -> bool:
        return bool(self.collision_fn(q.copy())) if self.collision_fn is not None else False

    def _segment_valid(self, segment: JointSegment) -> bool:
        times = np.linspace(0.0, segment.duration, self.config.samples_per_segment)
        q, v, a = segment.sample(times)
        if np.any(q < self.config.joint_lower - 1e-9) or np.any(q > self.config.joint_upper + 1e-9):
            return False
        if np.any(np.abs(v) > self.config.velocity_limits + 1e-8):
            return False
        if np.any(np.abs(a) > self.config.acceleration_limits + 1e-7):
            return False
        return not any(self._collision(configuration) for configuration in q)

    def _steering_time(self, q0: Array, v0: Array, q1: Array, v1: Array, requested: float | None) -> float:
        time = float(self.config.steering_time if requested is None else requested)
        time = float(np.clip(time, self.config.min_steering_time, self.config.max_steering_time))
        # Increase T until the exact polynomial obeys velocity and acceleration
        # bounds.  This is cheap and avoids numerical dynamics integration.
        for _ in range(24):
            segment = JointSegment(q0, v0, q1, v1, time)
            sample_t = np.linspace(0.0, time, max(9, self.config.samples_per_segment // 2))
            _, velocity, acceleration = segment.sample(sample_t)
            if np.all(np.abs(velocity) <= self.config.velocity_limits + 1e-8) and np.all(np.abs(acceleration) <= self.config.acceleration_limits + 1e-7):
                return time
            if time >= self.config.max_steering_time - 1e-12:
                break
            time = min(self.config.max_steering_time, time * 1.25)
        return time

    def steer(self, q0: Array, v0: Array, q1: Array, v1: Array | None = None, duration: float | None = None) -> JointSegment | None:
        q0, v0, q1 = (np.asarray(x, dtype=float) for x in (q0, v0, q1))
        if v1 is None:
            v1 = np.zeros_like(q1)
        else:
            v1 = np.asarray(v1, dtype=float)
        if any(x.shape != (self.config.dof,) for x in (q0, v0, q1, v1)):
            raise ValueError("steering states must have shape (dof,)")
        time = self._steering_time(q0, v0, q1, v1, duration)
        segment = JointSegment(q0, v0, q1, v1, time)
        return segment if self._segment_valid(segment) else None

    def _sample_state(self, goal_q: Array) -> tuple[Array, Array]:
        if self._rng.random() < self.config.goal_bias:
            return goal_q.copy(), np.zeros(self.config.dof)
        q = self._rng.uniform(self.config.joint_lower, self.config.joint_upper)
        v = self._rng.uniform(-self.config.velocity_limits, self.config.velocity_limits)
        return q, v

    def _nearest(self, nodes: Sequence[_Node], q: Array, v: Array) -> int:
        scale_q = self.config.joint_upper - self.config.joint_lower
        distance = [np.linalg.norm((node.q - q) / scale_q) + 0.15 * np.linalg.norm((node.v - v) / self.config.velocity_limits) for node in nodes]
        return int(np.argmin(distance))

    def _build_trajectory(self, nodes: Sequence[_Node], index: int, final: JointSegment | None = None) -> FlaskTrajectory:
        segments: list[JointSegment] = []
        if final is not None:
            segments.append(final)
        while nodes[index].parent is not None:
            segment = nodes[index].segment
            assert segment is not None
            segments.append(segment)
            index = int(nodes[index].parent)
        segments.reverse()
        if not segments:
            raise RuntimeError("planner produced an empty trajectory")
        return FlaskTrajectory(tuple(segments))

    def plan(self, start_q: Array, goal_q: Array, start_qdot: Array | None = None, goal_qdot: Array | None = None) -> FlaskTrajectory | None:
        """Plan from a flat start state to a joint goal, or return ``None``."""

        start_q, goal_q = np.asarray(start_q, dtype=float), np.asarray(goal_q, dtype=float)
        start_qdot = np.zeros(self.config.dof) if start_qdot is None else np.asarray(start_qdot, dtype=float)
        goal_qdot = np.zeros(self.config.dof) if goal_qdot is None else np.asarray(goal_qdot, dtype=float)
        if any(x.shape != (self.config.dof,) or not np.all(np.isfinite(x)) for x in (start_q, goal_q, start_qdot, goal_qdot)):
            raise ValueError("start and goal states must be finite vectors with planner DOF")
        if np.any(start_q < self.config.joint_lower) or np.any(start_q > self.config.joint_upper) or np.any(goal_q < self.config.joint_lower) or np.any(goal_q > self.config.joint_upper):
            raise ValueError("start and goal configurations must lie inside joint limits")
        direct = self.steer(start_q, start_qdot, goal_q, goal_qdot)
        if direct is not None:
            return FlaskTrajectory((direct,))
        nodes = [_Node(start_q.copy(), start_qdot.copy(), None, None)]
        for _ in range(self.config.max_iterations):
            sample_q, sample_v = self._sample_state(goal_q)
            nearest = self._nearest(nodes, sample_q, sample_v)
            candidate = self.steer(nodes[nearest].q, nodes[nearest].v, sample_q, sample_v)
            if candidate is None:
                continue
            nodes.append(_Node(candidate.q1.copy(), candidate.v1.copy(), nearest, candidate))
            new_index = len(nodes) - 1
            finish = self.steer(candidate.q1, candidate.v1, goal_q, goal_qdot)
            if finish is not None:
                return self._build_trajectory(nodes, new_index, finish)
        return None


class MuJoCoFR3CollisionChecker:
    """MuJoCo collision callback for a fixed-base FR3/Panda model.

    ``robot_geom_names`` and ``obstacle_geom_names`` should be explicit in a
    safety-critical deployment.  If omitted, robot geoms are inferred from
    names beginning with ``fr3_`` or ``hand`` and every other geom is treated
    as an obstacle.
    """

    def __init__(self, model, robot_geom_names: Iterable[str] | None = None, obstacle_geom_names: Iterable[str] | None = None):
        import mujoco

        self.model = model
        self._mujoco = mujoco
        self.data = mujoco.MjData(model)
        inferred_robot = [model.geom(i).name for i in range(model.ngeom) if (model.geom(i).name or "").startswith(("fr3_", "hand", "finger"))]
        robot_names = set(inferred_robot if robot_geom_names is None else robot_geom_names)
        self.robot_ids = {mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, name) for name in robot_names}
        self.robot_ids.discard(-1)
        if obstacle_geom_names is None:
            self.obstacle_ids = set(range(model.ngeom)) - self.robot_ids
        else:
            self.obstacle_ids = {mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, name) for name in obstacle_geom_names}
            self.obstacle_ids.discard(-1)

    def __call__(self, q: Array) -> bool:
        q = np.asarray(q, dtype=float)
        if q.shape != (self.model.nq,) and q.shape != (7,):
            raise ValueError("FR3 collision checker expects seven joint angles or full model nq")
        if q.shape == (7,):
            self.data.qpos[:7] = q
        else:
            self.data.qpos[:] = q
        self.data.qvel[:] = 0.0
        self._mujoco.mj_forward(self.model, self.data)
        for i in range(self.data.ncon):
            contact = self.data.contact[i]
            pair = {int(contact.geom1), int(contact.geom2)}
            if pair & self.robot_ids and pair & self.obstacle_ids and contact.dist < 0.0:
                return True
        return False
