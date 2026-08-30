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

def depth_preview(depth_m: np.ndarray, *, max_depth_m: float = 2.0) -> np.ndarray:
    """Convert metric depth to a displayable grayscale RGB image."""

    normalized = 1.0 - np.clip(np.asarray(depth_m, dtype=np.float32) / max_depth_m, 0.0, 1.0)
    image = np.rint(normalized * 255.0).astype(np.uint8)
    return np.repeat(image[..., None], 3, axis=2)
