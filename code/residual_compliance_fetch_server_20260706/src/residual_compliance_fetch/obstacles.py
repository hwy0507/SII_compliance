from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from residual_compliance_fetch.controllers import ObstacleState


@dataclass
class CrossingSphereSpec:
    radius: float = 0.105
    spawn_time: float = 1.4
    end_time: float | None = None
    start: tuple[float, float, float] = (-0.54, -0.34, 1.48)
    velocity: tuple[float, float, float] = (0.0, 0.36, 0.0)
    hidden: tuple[float, float, float] = (0.0, 0.0, -10.0)


class CrossingSphereObstacle:
    """One kinematic sphere crossing the arm path."""

    def __init__(self, spec: CrossingSphereSpec, actor=None):
        self.spec = spec
        self.actor = actor
        self._last_position = np.asarray(spec.hidden, dtype=np.float32)

    @property
    def radius(self) -> float:
        return float(self.spec.radius)

    def position_at(self, t: float) -> tuple[np.ndarray, bool]:
        if t < float(self.spec.spawn_time):
            return np.asarray(self.spec.hidden, dtype=np.float32), False
        if self.spec.end_time is not None and t > float(self.spec.end_time):
            return np.asarray(self.spec.hidden, dtype=np.float32), False
        dt = float(t) - float(self.spec.spawn_time)
        pos = np.asarray(self.spec.start, dtype=np.float32) + dt * np.asarray(
            self.spec.velocity, dtype=np.float32
        )
        return pos.astype(np.float32), True

    def update(self, t: float) -> ObstacleState:
        position, active = self.position_at(t)
        self._last_position = position

        if self.actor is not None:
            import sapien

            self.actor.set_pose(sapien.Pose(p=position))

        velocity = np.asarray(self.spec.velocity if active else (0.0, 0.0, 0.0), dtype=np.float32)
        return ObstacleState(
            position=position,
            velocity=velocity,
            radius=float(self.spec.radius),
            active=bool(active),
            visible=bool(active),
            confidence=1.0 if active else 0.0,
            source="sim_true_state",
        )

    @classmethod
    def build_in_scene(
        cls,
        scene,
        spec: CrossingSphereSpec,
        *,
        add_visual: bool = True,
    ) -> "CrossingSphereObstacle":
        import sapien

        builder = scene.create_actor_builder()
        builder.add_sphere_collision(radius=float(spec.radius))
        if add_visual:
            builder.add_sphere_visual(
                radius=float(spec.radius),
                material=sapien.render.RenderMaterial(
                    base_color=[0.92, 0.12, 0.10, 1.0],
                ),
            )
        builder.set_initial_pose(sapien.Pose(p=np.asarray(spec.hidden, dtype=np.float32)))
        actor = builder.build_kinematic(name="dynamic_residual_obstacle")
        return cls(spec=spec, actor=actor)


def randomized_crossing_sphere(rng: np.random.Generator) -> CrossingSphereSpec:
    """Sampling hook for future dataset/RL rollouts."""
    radius = float(rng.uniform(0.08, 0.14))
    spawn_time = float(rng.uniform(1.2, 3.0))
    y0 = float(rng.uniform(-0.60, -0.35))
    speed = float(rng.uniform(0.24, 0.42))
    x = float(rng.uniform(-0.68, -0.44))
    z = float(rng.uniform(1.34, 1.66))
    return CrossingSphereSpec(
        radius=radius,
        spawn_time=spawn_time,
        start=(x, y0, z),
        velocity=(0.0, speed, 0.0),
    )


def randomized_contact_heavy_crossing_sphere(rng: np.random.Generator) -> CrossingSphereSpec:
    """Sample obstacles biased toward forearm/wrist contact in the Empty-v1 Fetch path.

    The default nominal path sweeps the distal arm through roughly x=0.7..1.1,
    y=0.0..0.35, z=0.85..1.2.  This sampler crosses that corridor from negative
    y to positive y so PPO receives enough contact/recovery signal.
    """
    radius = float(rng.uniform(0.135, 0.195))
    spawn_time = float(rng.uniform(0.45, 1.20))
    y0 = float(rng.uniform(-0.22, -0.08))
    speed = float(rng.uniform(0.16, 0.30))
    x = float(rng.uniform(0.80, 1.04))
    z = float(rng.uniform(0.93, 1.13))
    return CrossingSphereSpec(
        radius=radius,
        spawn_time=spawn_time,
        start=(x, y0, z),
        velocity=(0.0, speed, 0.0),
    )
