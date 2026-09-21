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
BASE_INPUT_DIMENSION = 32
TORQUE_INPUT_SCALE = np.array([87.0, 87.0, 87.0, 87.0, 12.0, 12.0, 12.0], dtype=float)


@dataclass(frozen=True)
class MLPBaselineConfig:
    hidden_units: int = 64
    hidden_units2: int = 128
    architecture: str = "deep_residual"
    activation_error_start_m: float = 0.004
    activation_error_full_m: float = 0.012
    minimum_wbc_scale: float = 0.20
    maximum_linear_yield_mps: float = 0.16
    maximum_angular_yield_radps: float = 0.60
    include_torque_estimate: bool = False
    # Kept symmetric with DirectESNConfig.  ``delta`` is formed causally from
    # two consecutive motor-current / torque estimates, not from contact truth.
    torque_feature_mode: str = "motor"
    output_gain: float = 1.0
    torque_onset_gate_nm: float = 0.0
    # Same action-derived, deployable intervention decision used by the ESN
    # experiment.  It prevents small continuous-regression bias from becoming
    # a persistent residual motion during nominal grasp approach.
    intervention_gate_enabled: bool = False
    intervention_gate_threshold: float = 0.50
    # ``history_steps=1`` is the original memoryless MLP.  Larger values form
    # a causal fixed-window history baseline, used to test whether an ESN's
    # reservoir improves on explicit history rather than static inputs alone.
    history_steps: int = 1
    activation_mode: str = "absolute_position_error"
    activation_pose_rate_start: float = 0.015
    activation_pose_rate_full: float = 0.080
    activation_twist_rate_start: float = 0.015
    activation_twist_rate_full: float = 0.100


class MLPComplianceController:
    """Numpy-inference 32-D -> MLP -> bounded 7-D compliance action."""

    family = "mlp_baseline"

    def __init__(self, config: MLPBaselineConfig, mean: np.ndarray, std: np.ndarray,
                 w1: np.ndarray, b1: np.ndarray, w2: np.ndarray, b2: np.ndarray,
                 w3: np.ndarray | None = None, b3: np.ndarray | None = None,
                 skip: np.ndarray | None = None,
                 intervention_w: np.ndarray | None = None,
                 intervention_b: np.ndarray | None = None) -> None:
        self.config = config
        self.mean = np.asarray(mean, dtype=float).copy()
        self.std = np.asarray(std, dtype=float).copy()
        self.w1 = np.asarray(w1, dtype=float).copy()
        self.b1 = np.asarray(b1, dtype=float).copy()
        self.w2 = np.asarray(w2, dtype=float).copy()
        self.b2 = np.asarray(b2, dtype=float).copy()
        self.w3 = None if w3 is None else np.asarray(w3, dtype=float).copy()
        self.b3 = None if b3 is None else np.asarray(b3, dtype=float).copy()
        self.skip = None if skip is None else np.asarray(skip, dtype=float).copy()
        self.intervention_w = (None if intervention_w is None
                               else np.asarray(intervention_w, dtype=float).reshape(-1).copy())
        self.intervention_b = (None if intervention_b is None
                               else float(np.asarray(intervention_b, dtype=float).reshape(())))
        self._previous_torque_estimate = None
        self._previous_torque_feature_source = None
        self._previous_pose_error = None
        self._previous_twist_error = None
        self._observation_history: list[np.ndarray] = []
        self.last_intervention_probability = 0.0
        if config.history_steps < 1:
            raise ValueError("history_steps must be positive")
        if not 0.0 < config.intervention_gate_threshold < 1.0:
            raise ValueError("intervention_gate_threshold must lie strictly in (0, 1)")
        input_dim = (BASE_INPUT_DIMENSION + (7 if config.include_torque_estimate else 0)) * config.history_steps
        if self.mean.shape != (input_dim,) or self.std.shape != (input_dim,) or np.any(self.std <= 0.0):
            raise ValueError(f"normalization statistics must be {input_dim}-D with positive std")
        if self.w1.shape != (config.hidden_units, input_dim) or self.b1.shape != (config.hidden_units,):
            raise ValueError("first-layer weights have invalid shape")
        if self.intervention_w is not None and self.intervention_w.shape != (input_dim,):
            raise ValueError("intervention_w must match normalized input dimension")
        if config.intervention_gate_enabled and (self.intervention_w is None or self.intervention_b is None):
            raise ValueError("enabled intervention gate requires intervention weights")
        if self.w3 is None:
            if self.w2.shape != (ACTION_DIMENSION, config.hidden_units) or self.b2.shape != (ACTION_DIMENSION,):
                raise ValueError("second-layer weights have invalid shape")
        else:
            if self.w2.shape != (config.hidden_units2, config.hidden_units) or self.b2.shape != (config.hidden_units2,):
                raise ValueError("hidden-layer weights have invalid shape")
            if self.w3.shape != (ACTION_DIMENSION, config.hidden_units2) or self.b3.shape != (ACTION_DIMENSION,):
                raise ValueError("output-layer weights have invalid shape")

    def reset(self) -> None:
        """Stateless controller; present for interface parity."""
        self._previous_torque_estimate = None
        self._previous_torque_feature_source = None
        self._previous_pose_error = None
        self._previous_twist_error = None
        self._observation_history = []
        self.last_intervention_probability = 0.0

    def act(self, joint_position, joint_velocity, wbc_task_twist, *,
            pose_error=None, twist_error=None, joint_torque_estimate=None):
        observation = np.concatenate([
            np.asarray(joint_position, dtype=float),
            np.asarray(joint_velocity, dtype=float),
            np.asarray(wbc_task_twist, dtype=float),
            np.asarray(pose_error, dtype=float) if pose_error is not None else np.zeros(6),
            np.asarray(twist_error, dtype=float) if twist_error is not None else np.zeros(6),
        ])
        if self.config.include_torque_estimate:
            torque = np.zeros(7) if joint_torque_estimate is None else np.asarray(joint_torque_estimate, dtype=float)
            if torque.shape != (7,) or not np.all(np.isfinite(torque)):
                raise ValueError("joint torque estimate must be a finite 7-vector")
            if self.config.torque_feature_mode == "motor":
                torque_feature = torque
            elif self.config.torque_feature_mode == "delta":
                torque_feature = (np.zeros(7, dtype=float) if self._previous_torque_feature_source is None
                                  else torque - self._previous_torque_feature_source)
            else:
                raise ValueError("unsupported torque_feature_mode")
            self._previous_torque_feature_source = torque.copy()
            observation = np.concatenate((observation, torque_feature / TORQUE_INPUT_SCALE))
        per_step_input_dim = BASE_INPUT_DIMENSION + (7 if self.config.include_torque_estimate else 0)
        if observation.shape != (per_step_input_dim,):
            raise ValueError(f"MLP baseline per-step observation must be {per_step_input_dim}-D")
        self._observation_history.append(observation.copy())
        if len(self._observation_history) > self.config.history_steps:
            self._observation_history.pop(0)
        padded = [self._observation_history[0]] * (self.config.history_steps - len(self._observation_history))
        observation = np.concatenate([*padded, *self._observation_history])
        input_dim = per_step_input_dim * self.config.history_steps
        normalized = (observation - self.mean) / self.std
        hidden = np.tanh(normalized @ self.w1.T + self.b1)
        hidden = np.tanh(hidden @ self.w2.T + self.b2) if self.w3 is not None else hidden
        pre = hidden @ self.w3.T + self.b3 if self.w3 is not None else hidden @ self.w2.T + self.b2
        if self.skip is not None:
            pre = pre + 0.15 * normalized @ self.skip.T
        bounded = np.tanh(pre) * float(np.clip(self.config.output_gain, 0.0, 1.0))
        if self.config.intervention_gate_enabled:
            score = float(np.clip(normalized @ self.intervention_w + self.intervention_b, -40.0, 40.0))
            probability = float(1.0 / (1.0 + np.exp(-score)))
            self.last_intervention_probability = probability
            bounded *= float(probability >= self.config.intervention_gate_threshold)
        activation = 1.0
        if pose_error is not None:
            pose = np.asarray(pose_error, dtype=float)
            twist = np.zeros(6) if twist_error is None else np.asarray(twist_error, dtype=float)
            if self.config.activation_mode == "always_on":
                phase = 1.0
            elif self.config.activation_mode == "absolute_position_error":
                value = float(np.linalg.norm(pose[:3]))
                phase = np.clip((value - self.config.activation_error_start_m)
                                / (self.config.activation_error_full_m - self.config.activation_error_start_m), 0.0, 1.0)
            elif self.config.activation_mode == "transient_error_rate":
                pose_phase = 0.0; twist_phase = 0.0
                if self._previous_pose_error is not None:
                    pose_scales = np.array([0.012] * 3 + [0.20] * 3)
                    value = float(np.linalg.norm((pose - self._previous_pose_error) / pose_scales))
                    pose_phase = np.clip((value - self.config.activation_pose_rate_start)
                                         / (self.config.activation_pose_rate_full - self.config.activation_pose_rate_start), 0.0, 1.0)
                if self._previous_twist_error is not None:
                    twist_scales = np.array([0.40] * 3 + [1.20] * 3)
                    value = float(np.linalg.norm((twist - self._previous_twist_error) / twist_scales))
                    twist_phase = np.clip((value - self.config.activation_twist_rate_start)
                                          / (self.config.activation_twist_rate_full - self.config.activation_twist_rate_start), 0.0, 1.0)
                phase = max(float(pose_phase), float(twist_phase))
            else:
                raise ValueError("unsupported MLP activation mode")
            self._previous_pose_error = pose.copy()
            self._previous_twist_error = twist.copy()
            activation = float(phase * phase * (3.0 - 2.0 * phase))
        bounded = bounded * activation
        if self.config.include_torque_estimate and self.config.torque_onset_gate_nm > 0.0:
            torque = np.zeros(7) if joint_torque_estimate is None else np.asarray(joint_torque_estimate, dtype=float)
            if self._previous_torque_estimate is None:
                gate = 0.0
            else:
                delta = float(np.linalg.norm(torque - self._previous_torque_estimate))
                gate = float(np.clip(delta / self.config.torque_onset_gate_nm, 0.0, 1.0))
            bounded = bounded * gate
            self._previous_torque_estimate = torque.copy()
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
            **({"w3": self.w3, "b3": self.b3} if self.w3 is not None else {}),
            **({"skip": self.skip} if self.skip is not None else {}),
            **({"intervention_w": self.intervention_w, "intervention_b": np.asarray(self.intervention_b)}
               if self.intervention_w is not None else {}),
        )

    @classmethod
    def from_npz(cls, path: Path) -> "MLPComplianceController":
        with np.load(path, allow_pickle=False) as archive:
            if str(archive["controller_family"][0]) != cls.family:
                raise ValueError(f"{path}: not an {cls.family} checkpoint")
            config = MLPBaselineConfig(**json.loads(str(archive["config_json"][0])))
            return cls(config, archive["input_mean"], archive["input_std"],
                       archive["w1"], archive["b1"], archive["w2"], archive["b2"],
                       archive["w3"] if "w3" in archive else None,
                       archive["b3"] if "b3" in archive else None,
                       archive["skip"] if "skip" in archive else None,
                       archive["intervention_w"] if "intervention_w" in archive else None,
                       archive["intervention_b"] if "intervention_b" in archive else None)
