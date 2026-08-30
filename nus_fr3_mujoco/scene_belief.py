"""Local scene belief extracted from the FR3 wrist RGB-D observation."""

from __future__ import annotations

from dataclasses import dataclass

import mujoco
import numpy as np

from .wrist_camera import WristObservation


@dataclass(frozen=True)
class LocalSceneBelief:
    """Camera-local geometry available to the nominal perception loop."""

    obstacle_points_world: np.ndarray
    target_pixel_uv: np.ndarray
    target_depth_m: float
    target_visibility: float
    valid_depth_ratio: float


class WristSceneBeliefEstimator:
    """Turn a wrist depth frame into a sparse local world point cloud.

    This is deliberately a geometric baseline. It has no access to MuJoCo
    obstacle poses or contacts; the optional target point is used only for
    evaluation of target visibility in the simulator benchmark.
    """

    def __init__(self, model: mujoco.MjModel, camera_name: str = "wrist_rgbd") -> None:
        self.model = model
        self.camera_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, camera_name)
        if self.camera_id < 0:
            raise ValueError(f"MuJoCo model is missing camera: {camera_name}")
        self.fovy_rad = np.deg2rad(float(model.cam_fovy[self.camera_id]))

    def estimate(
        self,
        observation: WristObservation,
        *,
        target_position_world: np.ndarray | None = None,
        stride: int = 6,
    ) -> LocalSceneBelief:
        depth = np.asarray(observation.depth_m, dtype=np.float32)
        height, width = depth.shape[:2]
        valid = np.isfinite(depth) & (depth > 0.05) & (depth < 3.0)
        valid_depth_ratio = float(np.mean(valid))
        points_world = self._depth_to_world(observation, valid, stride)

        target_pixel = np.array([-1.0, -1.0], dtype=np.float64)
        target_depth = float("nan")
        target_visibility = 0.0
        if target_position_world is not None:
            target_pixel, target_depth = self.project_world_point(observation, target_position_world, width, height)
            target_visibility = self._visibility_score(depth, valid, target_pixel, target_depth)
            if len(points_world):
                distances = np.linalg.norm(points_world - np.asarray(target_position_world), axis=1)
                points_world = points_world[distances > 0.055]

        return LocalSceneBelief(
            obstacle_points_world=points_world,
            target_pixel_uv=target_pixel,
            target_depth_m=target_depth,
            target_visibility=target_visibility,
            valid_depth_ratio=valid_depth_ratio,
        )

    def project_world_point(
        self,
        observation: WristObservation,
        point_world: np.ndarray,
        width: int,
        height: int,
    ) -> tuple[np.ndarray, float]:
        rotation_world_from_camera = observation.camera_rotation_matrix
        point_camera = rotation_world_from_camera.T @ (np.asarray(point_world) - observation.camera_position)
        forward_depth = -float(point_camera[2])
        if forward_depth <= 1.0e-6:
            return np.array([-1.0, -1.0], dtype=np.float64), forward_depth
        focal = 0.5 * float(width) / np.tan(0.5 * self.fovy_rad)
        u = 0.5 * (width - 1) + focal * float(point_camera[0]) / forward_depth
        v = 0.5 * (height - 1) - focal * float(point_camera[1]) / forward_depth
        return np.array([u, v], dtype=np.float64), forward_depth

    def _depth_to_world(self, observation: WristObservation, valid: np.ndarray, stride: int) -> np.ndarray:
        depth = np.asarray(observation.depth_m, dtype=np.float32)
        height, width = depth.shape
        stride = max(int(stride), 1)
        rows, cols = np.nonzero(valid[::stride, ::stride])
        rows *= stride
        cols *= stride
        if len(rows) == 0:
            return np.empty((0, 3), dtype=np.float64)
        focal = 0.5 * float(width) / np.tan(0.5 * self.fovy_rad)
        forward_depth = depth[rows, cols].astype(np.float64)
        x = (cols - 0.5 * (width - 1)) * forward_depth / focal
        y = -(rows - 0.5 * (height - 1)) * forward_depth / focal
        points_camera = np.column_stack((x, y, -forward_depth))
        return observation.camera_position + points_camera @ observation.camera_rotation_matrix.T

    @staticmethod
    def _visibility_score(
        depth: np.ndarray,
        valid: np.ndarray,
        pixel_uv: np.ndarray,
        target_depth: float,
    ) -> float:
        if target_depth <= 0.0 or pixel_uv[0] < 0.0 or pixel_uv[1] < 0.0:
            return 0.0
        height, width = depth.shape
        u, v = np.rint(pixel_uv).astype(int)
        if not (0 <= u < width and 0 <= v < height):
            return 0.0
        radius = 5
        u0, u1 = max(0, u - radius), min(width, u + radius + 1)
        v0, v1 = max(0, v - radius), min(height, v + radius + 1)
        patch_depth = depth[v0:v1, u0:u1]
        patch_valid = valid[v0:v1, u0:u1]
        if not np.any(patch_valid):
            return 0.0
        consistency = np.abs(patch_depth - target_depth) < 0.10
        front_of_target = patch_depth < target_depth + 0.12
        return float(np.mean((consistency & front_of_target)[patch_valid]))
