from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from residual_compliance_fetch.utils import normalize


@dataclass
class JointTrackerConfig:
    kp: float = 1.8
    waypoint_tolerance: float = 0.07
    max_qdot: float = 0.75
    lookahead: int = 2


class JointPathTracker:
    """Low-level nominal joint waypoint tracker for a 7D Fetch arm path."""

    def __init__(self, path: np.ndarray, config: JointTrackerConfig):
        if path.ndim != 2 or path.shape[1] != 7:
            raise ValueError(f"Expected path shape (N, 7), got {path.shape}")
        if len(path) < 2:
            raise ValueError("Need at least two arm waypoints.")
        self.path = path.astype(np.float32)
        self.config = config
        self.index = 0

    @property
    def final_target(self) -> np.ndarray:
        return self.path[-1]

    @property
    def current_target(self) -> np.ndarray:
        idx = min(self.index + int(self.config.lookahead), len(self.path) - 1)
        return self.path[idx]

    def reset(self) -> None:
        self.index = 0

    def command(self, q_arm: np.ndarray) -> tuple[np.ndarray, np.ndarray, bool]:
        while self.index < len(self.path) - 1:
            err = float(np.linalg.norm(self.path[self.index] - q_arm))
            if err > self.config.waypoint_tolerance:
                break
            self.index += 1

        q_target = self.current_target
        qdot = self.config.kp * (q_target - q_arm)
        qdot = np.clip(qdot, -self.config.max_qdot, self.config.max_qdot)
        done = (
            self.index >= len(self.path) - 1
            and np.linalg.norm(self.final_target - q_arm) < self.config.waypoint_tolerance
        )
        return qdot.astype(np.float32), q_target.astype(np.float32), bool(done)


@dataclass
class SmootherConfig:
    dt: float = 1.0 / 30.0
    lowpass_alpha: float = 0.30
    max_velocity: float = 0.90
    max_accel: float = 2.40


class VelocitySmoother:
    """Low-pass + acceleration limiter to avoid the jitter seen in the toy prototype."""

    def __init__(self, dim: int, config: SmootherConfig):
        self.dim = int(dim)
        self.config = config
        self.previous = np.zeros(self.dim, dtype=np.float32)

    def reset(self) -> None:
        self.previous[:] = 0.0

    def filter(self, desired: np.ndarray) -> np.ndarray:
        desired = np.asarray(desired, dtype=np.float32).reshape(self.dim)
        desired = np.clip(desired, -self.config.max_velocity, self.config.max_velocity)

        alpha = float(np.clip(self.config.lowpass_alpha, 0.0, 1.0))
        blended = (1.0 - alpha) * self.previous + alpha * desired

        max_delta = float(self.config.max_accel) * float(self.config.dt)
        delta = np.clip(blended - self.previous, -max_delta, max_delta)
        out = self.previous + delta
        out = np.clip(out, -self.config.max_velocity, self.config.max_velocity)
        self.previous = out.astype(np.float32)
        return self.previous.copy()


@dataclass
class LinkState:
    name: str
    index: int
    position: np.ndarray


@dataclass
class ObstacleState:
    position: np.ndarray
    velocity: np.ndarray
    radius: float
    active: bool
    visible: bool = True
    confidence: float = 1.0
    source: str = "true_state"


@dataclass
class ContactComplianceConfig:
    link_radius: float = 0.055
    contact_trigger_clearance: float = 0.0
    penetration_scale: float = 0.035
    normal_gain: float = 1.50
    tangential_gain: float = 0.30
    vertical_gain: float = 0.08
    obstacle_velocity_gain: float = 0.10
    nominal_soften_gain: float = 1.00
    damping: float = 0.04
    max_residual_qdot: float = 0.90
    lowpass_alpha: float = 0.45
    recovery_decay: float = 0.82
    force_proxy_depth_scale: float = 0.035
    force_proxy_threshold: float = 0.35
    force_proxy_scale: float = 0.45
    force_proxy_max_clearance: float = 0.035
    force_memory_decay: float = 0.60


class ContactComplianceController:
    """Contact-only compliance controller.

    This controller deliberately does not react to positive clearance. It only
    generates a residual after contact/penetration has been detected by the
    simulator contact proxy. That matches the no-vision force-feedback setting:
    track the nominal path until contact, then soften tracking and retreat/slide.
    """

    def __init__(self, config: ContactComplianceConfig):
        self.config = config
        self.previous = np.zeros(7, dtype=np.float32)

    def reset(self) -> None:
        self.previous[:] = 0.0

    def _map_cartesian_to_arm_qdot(
        self,
        *,
        q_full: np.ndarray,
        arm_indices: Sequence[int],
        link: LinkState,
        v_cart: np.ndarray,
        pinocchio_model,
    ) -> tuple[np.ndarray, np.ndarray | None]:
        try:
            jac = np.asarray(pinocchio_model.get_link_jacobian(link.index, local=False), dtype=np.float32)
        except Exception:
            return np.zeros(7, dtype=np.float32), None

        best_dq = None
        best_j_arm = None
        best_score = -float("inf")
        for row_slice in (slice(0, 3), slice(3, 6)):
            j_arm = jac[row_slice, list(arm_indices)]
            lhs = j_arm @ j_arm.T + float(self.config.damping) * np.eye(3, dtype=np.float32)
            candidate = j_arm.T @ np.linalg.solve(lhs, v_cart)
            achieved = j_arm @ candidate
            score = float(np.dot(achieved, v_cart) - 0.01 * np.linalg.norm(candidate))
            if score > best_score:
                best_score = score
                best_dq = candidate
                best_j_arm = j_arm

        if best_dq is None:
            return np.zeros(7, dtype=np.float32), None
        return np.asarray(best_dq, dtype=np.float32), best_j_arm

    def compute(
        self,
        q_full: np.ndarray,
        arm_indices: Sequence[int],
        link_states: Iterable[LinkState],
        obstacle: ObstacleState,
        qdot_nominal: np.ndarray,
        pinocchio_model,
        external_contact_depth: float = 0.0,
        external_force_level: float = 0.0,
    ) -> tuple[np.ndarray, dict]:
        min_clearance = float("inf")
        active_link = None
        active_diff = None

        if obstacle.active:
            for link in link_states:
                diff = np.asarray(link.position, dtype=np.float32) - obstacle.position
                center_dist = float(np.linalg.norm(diff))
                clearance = center_dist - float(obstacle.radius) - float(self.config.link_radius)
                if clearance < min_clearance:
                    min_clearance = clearance
                    active_link = link
                    active_diff = diff

        geometric_contact_depth = max(
            0.0,
            float(self.config.contact_trigger_clearance) - min_clearance,
        )
        force_contact_depth = float(np.clip(external_force_level, 0.0, 1.0)) * float(
            self.config.force_proxy_depth_scale
        )
        contact_depth = max(
            float(geometric_contact_depth),
            float(external_contact_depth),
            float(force_contact_depth),
        )
        if (
            not obstacle.active
            or active_link is None
            or contact_depth <= 0.0
        ):
            self.previous *= float(np.clip(self.config.recovery_decay, 0.0, 1.0))
            return self.previous.copy(), {
                "contact_level": 0.0,
                "contact_depth": 0.0,
                "force_level": float(external_force_level),
                "min_clearance": float(min_clearance),
                "active_link": None,
                "nominal_scale": 1.0,
                "source": "contact_recovery" if np.linalg.norm(self.previous) > 1e-4 else "nominal",
            }

        try:
            pinocchio_model.compute_full_jacobian(q_full)
        except Exception:
            self.previous *= float(np.clip(self.config.recovery_decay, 0.0, 1.0))
            return self.previous.copy(), {
                "contact_level": 0.0,
                "contact_depth": float(contact_depth),
                "force_level": float(external_force_level),
                "min_clearance": float(min_clearance),
                "active_link": "pinocchio_failed",
                "nominal_scale": 0.25,
                "source": "contact_compliance_failed",
            }

        normal = normalize(np.asarray(active_diff, dtype=np.float32))
        if np.linalg.norm(normal) < 1e-6:
            normal = np.array([0.0, 0.0, 1.0], dtype=np.float32)

        contact_level = float(
            np.clip(contact_depth / max(float(self.config.penetration_scale), 1e-6), 0.0, 1.0)
        )
        contact_level = max(contact_level, float(np.clip(external_force_level, 0.0, 1.0)))
        # Even shallow contact should trigger an immediate reflex. The exact
        # force magnitude will be learned later; this analytic reflex is the
        # safe first behavior.
        contact_level = max(0.35, contact_level)

        normal_v = float(self.config.normal_gain) * contact_level * normal
        _, j_arm_for_tangent = self._map_cartesian_to_arm_qdot(
            q_full=q_full,
            arm_indices=arm_indices,
            link=active_link,
            v_cart=normal_v.astype(np.float32),
            pinocchio_model=pinocchio_model,
        )

        tangent = np.zeros(3, dtype=np.float32)
        if j_arm_for_tangent is not None:
            nominal_cart = j_arm_for_tangent @ np.asarray(qdot_nominal, dtype=np.float32)
            tangent = nominal_cart - float(np.dot(nominal_cart, normal)) * normal
        if np.linalg.norm(tangent) < 1e-5:
            tangent = np.array([0.0, 0.0, 1.0], dtype=np.float32)
            tangent = tangent - float(np.dot(tangent, normal)) * normal
        tangent = normalize(tangent)

        v_cart = (
            normal_v
            + float(self.config.tangential_gain) * contact_level * tangent
            + float(self.config.vertical_gain) * contact_level * np.array([0.0, 0.0, 1.0], dtype=np.float32)
            - float(self.config.obstacle_velocity_gain) * np.asarray(obstacle.velocity, dtype=np.float32)
        ).astype(np.float32)

        qdot_reflex, _ = self._map_cartesian_to_arm_qdot(
            q_full=q_full,
            arm_indices=arm_indices,
            link=active_link,
            v_cart=v_cart,
            pinocchio_model=pinocchio_model,
        )
        qdot_reflex = np.clip(
            qdot_reflex,
            -float(self.config.max_residual_qdot),
            float(self.config.max_residual_qdot),
        )

        alpha = float(np.clip(self.config.lowpass_alpha, 0.0, 1.0))
        qdot_reflex = (1.0 - alpha) * self.previous + alpha * qdot_reflex
        qdot_reflex = np.clip(
            qdot_reflex,
            -float(self.config.max_residual_qdot),
            float(self.config.max_residual_qdot),
        )
        self.previous = qdot_reflex.astype(np.float32)

        nominal_scale = max(
            0.05,
            1.0 - float(self.config.nominal_soften_gain) * contact_level,
        )
        return self.previous.copy(), {
            "contact_level": float(contact_level),
            "contact_depth": float(contact_depth),
            "force_level": float(external_force_level),
            "min_clearance": float(min_clearance),
            "active_link": active_link.name,
            "nominal_scale": float(nominal_scale),
            "source": (
                f"contact_compliance_force_proxy:{active_link.name}"
                if float(external_force_level) > 0.0
                else
                f"contact_compliance_memory:{active_link.name}"
                if float(external_contact_depth) > float(geometric_contact_depth)
                else f"contact_compliance:{active_link.name}"
            ),
        }
