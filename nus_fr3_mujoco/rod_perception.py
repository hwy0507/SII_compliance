"""RGB-D perception for the orange rod in the tabletop benchmark.

The detector intentionally has no access to MuJoCo body poses.  It uses only
the rendered RGB-D frame and the camera calibration supplied by the
observation.  A small workspace gate removes the other orange scene prop
(the pencil) before a PCA fit estimates the rod centre and principal axis.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .wrist_camera import WristObservation


@dataclass(frozen=True)
class RodDetection:
    position_world: np.ndarray
    axis_world: np.ndarray
    extent_m: np.ndarray
    confidence: float
    pixel_count: int
    visible: bool = True


@dataclass(frozen=True)
class RodBelief:
    position_world: np.ndarray
    axis_world: np.ndarray
    confidence: float
    visible_camera_count: int
    detections: tuple[dict[str, object], ...]


class RGBDRodDetector:
    """Detect an orange, horizontal rod from one RGB-D observation."""

    def __init__(self, fovy_rad: float, *, min_pixels: int = 6) -> None:
        self.fovy_rad = float(fovy_rad)
        self.min_pixels = int(min_pixels)

    def detect(self, observation: WristObservation) -> RodDetection | None:
        rgb = np.asarray(observation.rgb, dtype=np.uint8)
        depth = np.asarray(observation.depth_m, dtype=np.float32)
        valid = np.isfinite(depth) & (depth > 0.05) & (depth < 3.0)
        red = rgb[..., 0].astype(np.int16)
        green = rgb[..., 1].astype(np.int16)
        blue = rgb[..., 2].astype(np.int16)
        # target_orange is approximately (230, 64, 11) under the benchmark
        # lighting.  Chromatic dominance is more stable than an absolute RGB
        # threshold and rejects the brown desk and red robot trim.
        orange = (
            (red > 45)
            & (red > 1.45 * green)
            & (red > 1.75 * blue)
            & (green < 115)
            & (blue < 0.42 * np.maximum(green, 1))
            & (blue < 0.34 * red)
        )
        mask = orange & valid
        components = self._components(mask)
        candidates: list[RodDetection] = []
        for pixels in components:
            if len(pixels) < self.min_pixels:
                continue
            rows = np.asarray([p[0] for p in pixels], dtype=int)
            cols = np.asarray([p[1] for p in pixels], dtype=int)
            d = depth[rows, cols]
            good = np.isfinite(d) & (d > 0.05) & (d < 3.0)
            if int(np.sum(good)) < self.min_pixels:
                continue
            rows, cols, d = rows[good], cols[good], d[good]
            points = self._pixels_to_world(observation, rows, cols, d)
            center = np.median(points, axis=0)
            extent = np.ptp(points, axis=0)
            # Search region: the rod is on the front-left desk area.  This
            # excludes the orange pencil behind the monitor and plant pot.
            if not (-0.05 <= center[0] <= 0.36 and -0.38 <= center[1] <= -0.15 and 0.69 <= center[2] <= 0.86):
                continue
            centered = points - np.mean(points, axis=0)
            if len(points) >= 3:
                covariance = centered.T @ centered / max(len(points) - 1, 1)
                eigenvalues, eigenvectors = np.linalg.eigh(covariance)
                axis = eigenvectors[:, int(np.argmax(eigenvalues))]
            else:
                axis = np.array([0.0, 1.0, 0.0], dtype=np.float64)
            axis = np.asarray(axis, dtype=np.float64)
            axis /= max(float(np.linalg.norm(axis)), 1.0e-9)
            # Horizontal elongated support is the defining cue.  Partial
            # occlusion may shorten the apparent extent, hence the modest
            # 7 cm threshold rather than the nominal 24 cm rod length.
            longitudinal = float(np.max(extent))
            horizontal = float(np.linalg.norm(axis[:2]))
            if longitudinal < 0.07 or horizontal < 0.72 or abs(float(axis[1])) < 0.78:
                continue
            if float(np.dot(axis, np.array([0.0, 1.0, 0.0]))) < 0.0:
                axis = -axis
            pixel_support = min(1.0, len(points) / 30.0)
            elongation = min(1.0, longitudinal / 0.16)
            horizontal_score = min(1.0, horizontal)
            confidence = float(np.clip(0.30 * pixel_support + 0.45 * elongation + 0.25 * horizontal_score, 0.0, 1.0))
            candidates.append(RodDetection(center, axis, np.maximum(extent, 0.005), confidence, len(points)))
        if not candidates:
            return None
        return max(candidates, key=lambda detection: detection.confidence)

    def _pixels_to_world(self, observation: WristObservation, rows: np.ndarray, cols: np.ndarray, depth: np.ndarray) -> np.ndarray:
        height, width = observation.depth_m.shape
        focal = 0.5 * float(width) / np.tan(0.5 * self.fovy_rad)
        x = (cols - 0.5 * (width - 1)) * depth / focal
        y = -(rows - 0.5 * (height - 1)) * depth / focal
        points_camera = np.column_stack((x, y, -depth))
        return observation.camera_position + points_camera @ observation.camera_rotation_matrix.T

    @staticmethod
    def _components(mask: np.ndarray) -> list[list[tuple[int, int]]]:
        visited = np.zeros(mask.shape, dtype=bool)
        components: list[list[tuple[int, int]]] = []
        height, width = mask.shape
        for row, col in zip(*np.nonzero(mask)):
            if visited[row, col]:
                continue
            stack = [(int(row), int(col))]
            visited[row, col] = True
            pixels: list[tuple[int, int]] = []
            while stack:
                current_row, current_col = stack.pop()
                pixels.append((current_row, current_col))
                for drow in (-1, 0, 1):
                    for dcol in (-1, 0, 1):
                        if drow == 0 and dcol == 0:
                            continue
                        next_row, next_col = current_row + drow, current_col + dcol
                        if 0 <= next_row < height and 0 <= next_col < width and mask[next_row, next_col] and not visited[next_row, next_col]:
                            visited[next_row, next_col] = True
                            stack.append((next_row, next_col))
            components.append(pixels)
        return components


def fuse_rod_detections(named_detections: list[tuple[str, RodDetection | None]], *, min_confidence: float = 0.24) -> RodBelief | None:
    """Fuse independent camera detections with confidence weighting."""
    credible = [(name, detection) for name, detection in named_detections if detection is not None and detection.confidence >= min_confidence]
    if not credible:
        return None
    weights = np.asarray([max(float(detection.confidence), 0.05) for _, detection in credible], dtype=np.float64)
    weights /= max(float(np.sum(weights)), 1.0e-9)
    position = sum(weight * detection.position_world for weight, (_, detection) in zip(weights, credible))
    reference_axis = max((detection for _, detection in credible), key=lambda detection: detection.confidence).axis_world
    aligned_axes = []
    for _, detection in credible:
        axis = detection.axis_world.copy()
        if float(np.dot(axis, reference_axis)) < 0.0:
            axis = -axis
        aligned_axes.append(axis)
    axis = sum(weight * value for weight, value in zip(weights, aligned_axes))
    axis /= max(float(np.linalg.norm(axis)), 1.0e-9)
    confidence = 1.0 - float(np.prod([1.0 - np.clip(detection.confidence, 0.0, 1.0) for _, detection in credible]))
    return RodBelief(
        np.asarray(position, dtype=np.float64),
        np.asarray(axis, dtype=np.float64),
        float(np.clip(confidence, 0.0, 1.0)),
        len(credible),
        tuple({
            "camera": name,
            "position_world": detection.position_world.tolist(),
            "axis_world": detection.axis_world.tolist(),
            "extent_m": detection.extent_m.tolist(),
            "confidence": float(detection.confidence),
            "pixel_count": int(detection.pixel_count),
        } for name, detection in credible),
    )
