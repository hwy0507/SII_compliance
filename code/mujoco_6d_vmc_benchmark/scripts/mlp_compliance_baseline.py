#!/usr/bin/env python3
"""Memoryless MLP compliance baseline: same contract as Direct ESN, no reservoir.

This is the "why an ESN?" control: an ordinary two-layer MLP is behavior-cloned
on exactly the same expert traces, reads exactly the same 32-D deployable
input, and passes through the same error-based activation gate and physical
action bounds as the Direct ESN.  The only architectural difference is the
absence of the leaky reservoir — the MLP is memoryless, so it cannot integrate
contact history the way a reservoir does.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ACTION_DIMENSION = 7


@dataclass(frozen=True)
class MLPBaselineConfig:
    hidden_units: int = 64
    activation_error_start_m: float = 0.004
    activation_error_full_m: float = 0.012
    minimum_wbc_scale: float = 0.20
    maximum_linear_yield_mps: float = 0.16
    maximum_angular_yield_radps: float = 0.60


class MLPComplianceController:
    """Numpy-inference 32-D -> MLP -> bounded 7-D compliance action."""

    family = "mlp_baseline"

    def __init__(self, config: MLPBaselineConfig, mean: np.ndarray, std: np.ndarray,
                 w1: np.ndarray, b1: np.ndarray, w2: np.ndarray, b2: np.ndarray) -> None:
        self.config = config
        self.mean = np.asarray(mean, dtype=float).copy()
        self.std = np.asarray(std, dtype=float).copy()
        self.w1 = np.asarray(w1, dtype=float).copy()
        self.b1 = np.asarray(b1, dtype=float).copy()
        self.w2 = np.asarray(w2, dtype=float).copy()
        self.b2 = np.asarray(b2, dtype=float).copy()
        dim = self.mean.shape[0] if self.mean.ndim == 1 else 0
        if self.std.shape != (dim,) or dim == 0 or np.any(self.std <= 0.0):
            raise ValueError(f"normalization statistics must be a consistent positive-std vector, got {dim}-D")
        if self.w1.shape != (config.hidden_units, dim) or self.b1.shape != (config.hidden_units,):
            raise ValueError("first-layer weights have invalid shape")
        if self.w2.shape != (ACTION_DIMENSION, config.hidden_units) or self.b2.shape != (ACTION_DIMENSION,):
            raise ValueError("second-layer weights have invalid shape")

    def reset(self) -> None:
        """Stateless controller; present for interface parity."""

    def act(self, joint_position, joint_velocity, wbc_task_twist, *,
            pose_error=None, twist_error=None):
        observation = np.concatenate([
            np.asarray(joint_position, dtype=float),
            np.asarray(joint_velocity, dtype=float),
            np.asarray(wbc_task_twist, dtype=float),
            np.asarray(pose_error, dtype=float) if pose_error is not None else np.zeros(6),
            np.asarray(twist_error, dtype=float) if twist_error is not None else np.zeros(6),
        ])
        if observation.shape != (self.mean.shape[0],):
            raise ValueError(f"MLP baseline observation must be {self.mean.shape[0]}-D")
        normalized = (observation - self.mean) / self.std
        hidden = np.tanh(normalized @ self.w1.T + self.b1)
        bounded = np.tanh(hidden @ self.w2.T + self.b2)
        activation = 1.0
        if pose_error is not None:
            position_error = float(np.linalg.norm(np.asarray(pose_error, dtype=float)[:3]))
            phase = np.clip(
                (position_error - self.config.activation_error_start_m)
                / (self.config.activation_error_full_m - self.config.activation_error_start_m),
                0.0, 1.0,
            )
            activation = float(phase * phase * (3.0 - 2.0 * phase))
        bounded = bounded * activation
        slowdown = max(0.0, float(bounded[0]))
        wbc_scale = 1.0 - slowdown * (1.0 - self.config.minimum_wbc_scale)
        limits = np.array([self.config.maximum_linear_yield_mps] * 3
                          + [self.config.maximum_angular_yield_radps] * 3)
        from direct_esn_compliance import DirectESNAction

        return DirectESNAction(
            raw_readout=bounded.copy(),
            bounded_filter_action=np.concatenate([[max(0.0, float(bounded[0]))], np.clip(bounded[1:], -1.0, 1.0)]),
            wbc_scale=float(np.clip(wbc_scale, self.config.minimum_wbc_scale, 1.0)),
            yielding_twist=bounded[1:] * limits,
        )

    def save_npz(self, path: Path) -> None:
        np.savez_compressed(
            path, controller_family=np.asarray([self.family]),
            config_json=np.asarray([json.dumps(self.config.__dict__)]),
            input_mean=self.mean, input_std=self.std,
            w1=self.w1, b1=self.b1, w2=self.w2, b2=self.b2,
        )

    @classmethod
    def from_npz(cls, path: Path) -> "MLPComplianceController":
        with np.load(path, allow_pickle=False) as archive:
            if str(archive["controller_family"][0]) != cls.family:
                raise ValueError(f"{path}: not an {cls.family} checkpoint")
            config = MLPBaselineConfig(**json.loads(str(archive["config_json"][0])))
            return cls(config, archive["input_mean"], archive["input_std"],
                       archive["w1"], archive["b1"], archive["w2"], archive["b2"])
