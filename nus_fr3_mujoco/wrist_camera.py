"""Wrist-mounted RGB-D observation and a minimal velocity-aware view scheduler."""

from __future__ import annotations

from dataclasses import dataclass

import mujoco
import numpy as np


@dataclass(frozen=True)
class WristObservation:
    rgb: np.ndarray
    depth_m: np.ndarray
    camera_position: np.ndarray
    camera_rotation_matrix: np.ndarray


@dataclass(frozen=True)
class ActiveViewDecision:
    focus_name: str
    focus_point: np.ndarray
    score: float
    risk_weight: float


@dataclass(frozen=True)
class ActivePerceptionDecision:
    focus_name: str
    focus_point: np.ndarray
    score: float
    predicted_speed_m_s: float
    uncertainty_m: float
    action_required: bool


class WristRGBDCamera:
    """Render the camera attached to the FR3 Panda hand.

    The camera has no independent world pose. MuJoCo updates its pose from
    the hand body, so the observation is causal with respect to the robot
    configuration and follows the same viewpoint that a real wrist sensor
    would have.
    """

    def __init__(self, model: mujoco.MjModel, camera_name: str = "wrist_rgbd", *, width: int = 320, height: int = 240) -> None:
        self.model = model
        self.camera_name = camera_name
        self.camera_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, camera_name)
        if self.camera_id < 0:
            raise ValueError(f"MuJoCo model is missing camera: {camera_name}")
        self.renderer = mujoco.Renderer(model, height=height, width=width)

    def render(self, data: mujoco.MjData) -> WristObservation:
        self.renderer.update_scene(data, camera=self.camera_name)
        rgb = self.renderer.render().copy()
        self.renderer.enable_depth_rendering()
        self.renderer.update_scene(data, camera=self.camera_name)
        depth_buffer = self.renderer.render().copy()
        self.renderer.disable_depth_rendering()
        depth_m = self._metric_depth(depth_buffer)
        return WristObservation(
            rgb=rgb,
            depth_m=depth_m,
            camera_position=data.cam_xpos[self.camera_id].copy(),
            camera_rotation_matrix=data.cam_xmat[self.camera_id].reshape(3, 3).copy(),
        )

    def close(self) -> None:
        self.renderer.close()

    def _metric_depth(self, depth_buffer: np.ndarray) -> np.ndarray:
        # Recent MuJoCo Python bindings return metric depth directly. Keep a
        # fallback for bindings that still expose the normalized depth buffer.
        near = float(self.model.vis.map.znear) * float(self.model.stat.extent)
        far = float(self.model.vis.map.zfar) * float(self.model.stat.extent)
        depth_buffer = np.asarray(depth_buffer, dtype=np.float32)
        if float(np.nanmax(depth_buffer)) > 1.01:
            return depth_buffer
        return (near * far) / np.maximum(far - depth_buffer * (far - near), 1.0e-6)


class VelocityAwareViewScheduler:
    """Select and score a wrist-camera focus point from future arm motion.

    The wrist camera has no independent pan/tilt joint. Its viewpoint is
    therefore controlled through the FR3 hand pose. ``choose_focus`` is the
    first explicit NUS-style bridge: it scores the target and future swept
    volume using phase priority, distance, temporal discount, and predicted
    arm speed, then returns a point for pose IK to face.
    """

    TARGET_PHASES = frozenset({"PRE-GRASP", "DESCEND", "CLOSE GRIPPER"})
    SWEPT_VOLUME_PHASES = frozenset({"APPROACH ABOVE CLUTTER", "LIFT", "CARRY AROUND CLUTTER", "RETURN HOME"})

    def select(self, phase: str, qdot: np.ndarray, *, ee_speed_m_s: float = 0.0) -> tuple[str, float]:
        speed = float(np.linalg.norm(qdot)) + float(max(ee_speed_m_s, 0.0))
        if phase in self.TARGET_PHASES:
            return "TARGET", speed
        if phase in self.SWEPT_VOLUME_PHASES or speed > 0.20:
            return "SWEPT_VOLUME", speed
        return "SCENE", speed

    def choose_focus(
        self,
        phase: str,
        hand_position: np.ndarray,
        target_position: np.ndarray,
        future_positions: np.ndarray,
        future_speeds: np.ndarray,
    ) -> ActiveViewDecision:
        """Choose the point the wrist camera should face for one waypoint."""

        hand_position = np.asarray(hand_position, dtype=np.float64)
        target_position = np.asarray(target_position, dtype=np.float64)
        future_positions = np.asarray(future_positions, dtype=np.float64).reshape(-1, 3)
        future_speeds = np.asarray(future_speeds, dtype=np.float64).reshape(-1)
        if len(future_positions) != len(future_speeds):
            raise ValueError("future_positions and future_speeds must have equal length")

        target_priority = 3.0 if phase in self.TARGET_PHASES else 0.35
        target_distance = float(np.linalg.norm(target_position - hand_position))
        target_score = target_priority / (target_distance + 0.12)
        candidates = [("TARGET", target_position, target_score, target_priority)]

        if len(future_positions):
            for index, (point, speed) in enumerate(zip(future_positions, future_speeds)):
                temporal_discount = 0.92 ** index
                risk_weight = max(float(speed), 0.02) * temporal_discount
                distance = float(np.linalg.norm(point - hand_position))
                score = (0.65 + 1.8 * risk_weight) / (distance + 0.15)
                candidates.append(("SWEPT_VOLUME", point, score, risk_weight))

        name, point, score, risk_weight = max(candidates, key=lambda item: item[2])
        return ActiveViewDecision(name, np.asarray(point, dtype=np.float64).copy(), float(score), float(risk_weight))

    def choose_active_focus(
        self,
        phase: str,
        hand_position: np.ndarray,
        target_position: np.ndarray,
        obstacle_state,
        future_positions: np.ndarray | None = None,
    ) -> ActivePerceptionDecision:
        """Select the next wrist view using velocity and prediction uncertainty.

        The obstacle state is an RGB-D track, not a simulator state. The view
        value increases when an obstacle is moving quickly, its predicted
        position is uncertain, and the arm will soon enter the same corridor.
        """

        hand_position = np.asarray(hand_position, dtype=np.float64)
        target_position = np.asarray(target_position, dtype=np.float64)
        obstacle_position = np.asarray(obstacle_state.position_world, dtype=np.float64)
        obstacle_velocity = np.asarray(obstacle_state.velocity_world, dtype=np.float64)
        speed = float(np.linalg.norm(obstacle_velocity))
        uncertainty = float(np.sqrt(max(float(obstacle_state.covariance_m2), 0.0)))
        obstacle_distance = float(np.linalg.norm(obstacle_position - hand_position))
        arm_corridor_score = 0.0
        future_positions = np.empty((0, 3), dtype=np.float64) if future_positions is None else np.asarray(future_positions, dtype=np.float64).reshape(-1, 3)
        if len(future_positions):
            distances = np.linalg.norm(future_positions - obstacle_position, axis=1)
            arm_corridor_score = float(np.exp(-np.min(distances) / 0.12))
        dynamic_score = (
            2.4 * speed
            + 2.8 * uncertainty
            + 1.8 * arm_corridor_score
            + (0.8 if not bool(obstacle_state.visible) else 0.0)
        ) / (obstacle_distance + 0.18)
        target_score = (2.8 if phase in self.TARGET_PHASES else 0.35) / (np.linalg.norm(target_position - hand_position) + 0.16)
        track_is_credible = bool(
            obstacle_state.confidence >= 0.30
            and (obstacle_state.visible or speed >= 0.20)
        )
        if track_is_credible and dynamic_score > target_score and phase in self.SWEPT_VOLUME_PHASES:
            return ActivePerceptionDecision(
                "PREDICTED_OBSTACLE",
                obstacle_position.copy(),
                float(dynamic_score),
                speed,
                uncertainty,
                bool(dynamic_score > 0.55),
            )
        # Before an obstacle is confirmed, actively scan the next fast-motion
        # corridor. This is the fixed-base analogue of NUS gaze actions: the
        # robot moves its wrist pose to reduce scene uncertainty before the
        # nominal planner commits to the next segment.
        if phase in {"LIFT", "CARRY AROUND CLUTTER"} and len(future_positions):
            distances_to_hand = np.linalg.norm(future_positions - hand_position, axis=1)
            # A future waypoint is often the current carry waypoint or the
            # placement point, so it is a poor camera target. Instead form a
            # lookout point in the unobserved part of the tabletop workspace.
            # This is a task-level spatial prior, not obstacle state: RGB-D is
            # still the only source that can confirm or track an obstacle.
            corridor_points = future_positions[distances_to_hand > 0.08]
            corridor_center = (
                np.mean(corridor_points, axis=0)
                if len(corridor_points)
                else hand_position.copy()
            )
            workspace_lookout = np.array([0.56, 0.18, 1.12], dtype=np.float64)
            search_point = 0.35 * corridor_center + 0.65 * workspace_lookout
            view_vector = search_point - hand_position
            view_distance = float(np.linalg.norm(view_vector))
            if view_distance < 0.28:
                view_vector /= max(view_distance, 1.0e-9)
                search_point = hand_position + 0.28 * view_vector
            search_score = (0.55 + 0.55 * min(speed, 1.0)) / (np.linalg.norm(search_point - hand_position) + 0.20)
            if search_score > 0.62:
                return ActivePerceptionDecision(
                    "SWEPT_VOLUME_SEARCH",
                    search_point,
                    float(search_score),
                    speed,
                    uncertainty,
                    True,
                )
        return ActivePerceptionDecision(
            "TARGET" if phase in self.TARGET_PHASES else "SWEPT_VOLUME",
            target_position.copy() if phase in self.TARGET_PHASES else (future_positions[0].copy() if len(future_positions) else target_position.copy()),
            float(target_score),
            speed,
            uncertainty,
            False,
        )


def depth_preview(depth_m: np.ndarray, *, max_depth_m: float = 2.0) -> np.ndarray:
    """Convert metric depth to a displayable grayscale RGB image."""

    normalized = 1.0 - np.clip(np.asarray(depth_m, dtype=np.float32) / max_depth_m, 0.0, 1.0)
    image = np.rint(normalized * 255.0).astype(np.uint8)
    return np.repeat(image[..., None], 3, axis=2)
