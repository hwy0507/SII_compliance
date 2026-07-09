from __future__ import annotations

from pathlib import Path

import numpy as np


DEFAULT_GOAL_DELTA = np.array([0.42, -0.28, 0.25, -0.44, 0.26, 0.24, 0.38], dtype=np.float32)


def interpolate_path(start: np.ndarray, goal: np.ndarray, num_waypoints: int = 90) -> np.ndarray:
    start = np.asarray(start, dtype=np.float32).reshape(7)
    goal = np.asarray(goal, dtype=np.float32).reshape(7)
    alpha = np.linspace(0.0, 1.0, int(num_waypoints), dtype=np.float32)[:, None]
    return ((1.0 - alpha) * start[None, :] + alpha * goal[None, :]).astype(np.float32)


def default_path_from_current(
    q_arm: np.ndarray,
    q_limits: np.ndarray | None = None,
    num_waypoints: int = 90,
) -> np.ndarray:
    start = np.asarray(q_arm, dtype=np.float32).reshape(7)
    goal = start + DEFAULT_GOAL_DELTA
    if q_limits is not None:
        limits = np.asarray(q_limits, dtype=np.float32)
        if limits.shape == (7, 2):
            goal = np.clip(goal, limits[:, 0] + 0.05, limits[:, 1] - 0.05)
    return interpolate_path(start, goal, num_waypoints=num_waypoints)


def load_arm_path(path: str | Path) -> np.ndarray:
    raw = np.load(Path(path), allow_pickle=True)
    if isinstance(raw, np.ndarray) and raw.dtype == object and raw.shape == ():
        raw = raw.item()

    if isinstance(raw, dict):
        for key in ["arm_path", "trajectory", "states", "q_arm"]:
            if key in raw:
                raw = raw[key]
                break

    arr = np.asarray(raw, dtype=np.float32)
    if arr.ndim == 3 and arr.shape[0] == 1:
        arr = arr[0]
    if arr.ndim != 2:
        raise ValueError(f"Unsupported trajectory shape: {arr.shape}")

    if arr.shape[1] == 7:
        out = arr
    elif arr.shape[1] == 8:
        out = arr[:, 1:]
    elif arr.shape[1] >= 11:
        out = arr[:, -7:]
    else:
        raise ValueError(
            "Trajectory must be N x 7, N x 8 [torso+arm], or N x 11 [base+torso+arm]."
        )

    if len(out) < 2:
        raise ValueError("Trajectory must contain at least two waypoints.")
    return out.astype(np.float32)

