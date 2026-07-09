from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import numpy as np


def ensure_conda_lib_path() -> None:
    """Match the original project's workaround for Conda shared libraries."""
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if not conda_prefix:
        return

    conda_lib = str(Path(conda_prefix) / "lib")
    current = os.environ.get("LD_LIBRARY_PATH", "")
    if conda_lib in current.split(":"):
        return

    os.environ["LD_LIBRARY_PATH"] = f"{conda_lib}:{current}" if current else conda_lib
    os.execv(sys.executable, [sys.executable] + sys.argv)


def to_numpy(value: Any) -> np.ndarray:
    """Convert torch / ManiSkill / list-like values to a CPU numpy array."""
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    return np.asarray(value)


def flatten_state(value: Any) -> np.ndarray:
    arr = to_numpy(value).astype(np.float32)
    if arr.ndim >= 2 and arr.shape[0] == 1:
        arr = arr[0]
    return arr.reshape(-1)


def vector3(value: Any) -> np.ndarray:
    arr = to_numpy(value).astype(np.float32)
    while arr.ndim > 1 and arr.shape[0] == 1:
        arr = arr[0]
    return arr.reshape(-1)[:3]


def normalize(vec: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    norm = float(np.linalg.norm(vec))
    if norm < eps:
        return np.zeros_like(vec, dtype=np.float32)
    return (vec / norm).astype(np.float32)


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if abs(edge1 - edge0) < 1e-8:
        return 1.0 if x >= edge1 else 0.0
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return float(t * t * (3.0 - 2.0 * t))


def ensure_dir(path: str | Path) -> Path:
    out = Path(path)
    out.mkdir(parents=True, exist_ok=True)
    return out

