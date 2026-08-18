"""Direct ESN compliant controller for the fixed-WBC impact task.

This module is the proposed-method contract for the new experiment line.  A
fixed WBC supplies the nominal end-effector velocity.  The ESN itself is the
compliance controller: it directly emits a slowdown request and a bounded
six-dimensional Cartesian yielding velocity.  A downstream safety adapter may
slew-limit and torque-limit that command, but it does not decide the
collision-response policy.

The deployed reservoir only receives proprioception and the nominal WBC
twist.  Contact force, impactor identity, obstacle geometry, and release time
are privileged teacher/evaluation quantities and are intentionally absent from
``DirectESNController.act``.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from esn_compliance import ESNObservation, encode_student_observation


ACTION_DIMENSION = 7
DEPLOYABLE_INPUT_DIMENSION = 32
DEPLOYABLE_INPUT_FIELDS = (
    "joint_position_7", "joint_velocity_7", "wbc_task_twist_6",
    "wbc_pose_error_6", "wbc_twist_error_6",
)
TEACHER_ONLY_FIELDS = (
    "contact_force", "contact_normal", "contact_duration", "signed_distance",
    "obstacle_pose", "obstacle_velocity", "impactor_type", "release_time",
)


def _finite_vector(value: np.ndarray | list[float] | tuple[float, ...], size: int, label: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.shape != (size,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{label} must be a finite {size}-vector")
    return array


def _finite_matrix(value: np.ndarray, columns: int, label: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 2 or array.shape[1] != columns or len(array) < 1 or not np.all(np.isfinite(array)):
        raise ValueError(f"{label} must be a finite T x {columns} matrix")
    return array


@dataclass(frozen=True)
class DirectESNConfig:
    """Fan-Ye-aligned fixed-reservoir parameters and physical action bounds."""

    reservoir_size: int = 160
    spectral_radius: float = 0.90
    input_scale: float = 0.45
    connection_probability: float = 0.12
    bias_scale: float = 0.05
    time_constant_s: float = 0.12
    dt_s: float = 0.04
    ridge_lambda: float = 1.0e-4
    seed: int = 20260817
    minimum_wbc_scale: float = 0.20
    maximum_linear_yield_mps: float = 0.16
    maximum_angular_yield_radps: float = 0.60
    activation_error_start_m: float = 0.004
    activation_error_full_m: float = 0.012
    # Experimental opt-in.  The published baseline/proposed checkpoints keep
    # the original world-frame readout unless this switch is explicitly set.
    error_aligned_yield: bool = False
    rejoin_fade_enabled: bool = False
    rejoin_fade_maximum: float = 0.85
    # First-order low-pass on the emitted yielding twist (1.0 disables it).
    # Deployment-side smoothing only: offline readout fitting never sees it.
    yield_smoothing_alpha: float = 1.0
    # Mirror-equivariant action gating: multiply the learned yield channels by
    # a soft sign of the matching pose-error channel.  Under the training
    # distribution (impacts from -y) the soft sign is +1, so the transform is
    # the identity and existing checkpoints are unaffected; under a mirrored
    # impact the learned action flips sign exactly, giving structural mirror
    # generalization instead of data augmentation.  "y" gates only the
    # lateral/yaw channels; "full" gates all six twist channels.
    mirror_gate_enabled: bool = False
    mirror_gate_channels: str = "y"
    mirror_gate_epsilon_m: float = 0.004
    mirror_gate_epsilon_rad: float = 0.020

    def __post_init__(self) -> None:
        values = np.asarray([
            self.spectral_radius, self.input_scale, self.connection_probability,
            self.bias_scale, self.time_constant_s, self.dt_s, self.ridge_lambda,
            self.minimum_wbc_scale, self.maximum_linear_yield_mps,
            self.maximum_angular_yield_radps,
            self.activation_error_start_m, self.activation_error_full_m,
            self.rejoin_fade_maximum,
        ], dtype=float)
        if self.reservoir_size < 1:
            raise ValueError("reservoir_size must be positive")
        if not np.all(np.isfinite(values)) or np.any(values <= 0.0):
            raise ValueError("Direct ESN parameters must be finite and positive")
        if self.minimum_wbc_scale >= 1.0:
            raise ValueError("minimum_wbc_scale must be below one")
        if self.time_constant_s < self.dt_s:
            raise ValueError("time_constant_s must be at least dt_s")
        if self.activation_error_full_m <= self.activation_error_start_m:
            raise ValueError("activation_error_full_m must exceed activation_error_start_m")
        if self.connection_probability > 1.0 or self.spectral_radius > 2.0:
            raise ValueError("reservoir probability/radius is out of bounds")
        if self.rejoin_fade_maximum > 1.0:
            raise ValueError("rejoin fade maximum cannot exceed one")
        if not 0.0 < self.yield_smoothing_alpha <= 1.0:
            raise ValueError("yield_smoothing_alpha must lie in (0, 1]")
        if self.mirror_gate_channels not in ("y", "full"):
            raise ValueError("mirror_gate_channels must be 'y' or 'full'")

    @property
    def leak(self) -> float:
        return self.dt_s / self.time_constant_s


@dataclass(frozen=True)
class DirectESNAction:
    """Semantic direct-ESN output plus its neutral-zero filter representation."""

    raw_readout: np.ndarray
    bounded_filter_action: np.ndarray
    wbc_scale: float
    yielding_twist: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "raw_readout", _finite_vector(self.raw_readout, ACTION_DIMENSION, "raw_readout"))
        object.__setattr__(self, "bounded_filter_action", _finite_vector(self.bounded_filter_action, ACTION_DIMENSION, "bounded_filter_action"))
        object.__setattr__(self, "yielding_twist", _finite_vector(self.yielding_twist, 6, "yielding_twist"))
        if not np.isfinite(self.wbc_scale) or not 0.0 < self.wbc_scale <= 1.0:
            raise ValueError("wbc_scale must be finite and in (0, 1]")


@dataclass(frozen=True)
class DirectESNObservation:
    """Deployable observation including measured WBC tracking deviation."""

    joint_position: np.ndarray
    joint_velocity: np.ndarray
    wbc_task_twist: np.ndarray
    wbc_pose_error: np.ndarray
    wbc_twist_error: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "joint_position", _finite_vector(self.joint_position, 7, "joint_position"))
        object.__setattr__(self, "joint_velocity", _finite_vector(self.joint_velocity, 7, "joint_velocity"))
        object.__setattr__(self, "wbc_task_twist", _finite_vector(self.wbc_task_twist, 6, "wbc_task_twist"))
        object.__setattr__(self, "wbc_pose_error", _finite_vector(self.wbc_pose_error, 6, "wbc_pose_error"))
        object.__setattr__(self, "wbc_twist_error", _finite_vector(self.wbc_twist_error, 6, "wbc_twist_error"))


def encode_direct_esn_observation(observation: DirectESNObservation) -> np.ndarray:
    """Encode proprioception, nominal twist, and measured WBC deviation."""

    base = encode_student_observation(ESNObservation(
        observation.joint_position, observation.joint_velocity, observation.wbc_task_twist,
    ))
    pose_scales = np.array([0.012] * 3 + [0.20] * 3)
    twist_scales = np.array([0.40] * 3 + [1.20] * 3)
    errors = np.concatenate((observation.wbc_pose_error / pose_scales, observation.wbc_twist_error / twist_scales))
    return np.clip(np.concatenate((base, errors)), -10.0, 10.0)


class DirectESNController:
    """Stateful fixed-reservoir controller with a direct compliance readout."""

    def __init__(self, config: DirectESNConfig = DirectESNConfig()) -> None:
        self.config = config
        rng = np.random.default_rng(config.seed)
        recurrent = rng.uniform(-1.0, 1.0, (config.reservoir_size, config.reservoir_size))
        recurrent *= rng.random(recurrent.shape) < config.connection_probability
        radius = float(np.max(np.abs(np.linalg.eigvals(recurrent))))
        if not np.isfinite(radius) or radius < 1.0e-8:
            recurrent = np.roll(np.eye(config.reservoir_size), shift=1, axis=1)
            radius = 1.0
        self._recurrent = recurrent * (config.spectral_radius / radius)
        self._input = rng.uniform(-config.input_scale, config.input_scale, (config.reservoir_size, DEPLOYABLE_INPUT_DIMENSION))
        self._bias = rng.uniform(-config.bias_scale, config.bias_scale, config.reservoir_size)
        self._state = np.zeros(config.reservoir_size, dtype=float)
        self._readout = np.zeros((ACTION_DIMENSION, self.feature_dimension), dtype=float)
        self._smoothed_yield_twist = np.zeros(6, dtype=float)

    @property
    def feature_dimension(self) -> int:
        return 1 + DEPLOYABLE_INPUT_DIMENSION + self.config.reservoir_size

    @property
    def state(self) -> np.ndarray:
        return self._state.copy()

    @property
    def readout(self) -> np.ndarray:
        return self._readout.copy()

    def reset(self, state: np.ndarray | None = None) -> None:
        self._smoothed_yield_twist.fill(0.0)
        if state is None:
            self._state.fill(0.0)
            return
        state_array = _finite_vector(state, self.config.reservoir_size, "initial reservoir state")
        self._state = np.clip(state_array, -1.0, 1.0)

    def _advance_encoded(self, encoded_input: np.ndarray) -> np.ndarray:
        encoded = _finite_vector(encoded_input, DEPLOYABLE_INPUT_DIMENSION, "encoded student input")
        proposal = np.tanh(self._input @ encoded + self._recurrent @ self._state + self._bias)
        self._state = (1.0 - self.config.leak) * self._state + self.config.leak * proposal
        if not np.all(np.isfinite(self._state)):
            raise RuntimeError("Direct ESN reservoir state became non-finite")
        return np.concatenate(([1.0], encoded, self._state))

    def advance(self, observation: DirectESNObservation | ESNObservation, pose_error: np.ndarray | None = None, twist_error: np.ndarray | None = None) -> np.ndarray:
        """Advance using deployment-available state and WBC deviation."""

        if isinstance(observation, DirectESNObservation):
            encoded = encode_direct_esn_observation(observation)
        else:
            pose = np.zeros(6) if pose_error is None else _finite_vector(pose_error, 6, "wbc_pose_error")
            twist = np.zeros(6) if twist_error is None else _finite_vector(twist_error, 6, "wbc_twist_error")
            encoded = encode_direct_esn_observation(DirectESNObservation(
                observation.joint_position, observation.joint_velocity, observation.wbc_task_twist, pose, twist,
            ))
        return self._advance_encoded(encoded)

    def features(self, observations: list[DirectESNObservation | ESNObservation], *, washout_steps: int = 0) -> np.ndarray:
        if not observations or not 0 <= washout_steps < len(observations):
            raise ValueError("observations must be non-empty and washout smaller than length")
        self.reset()
        values = [self.advance(observation) for observation in observations]
        return np.asarray(values[washout_steps:], dtype=float)

    def fit_readout(
        self, features: np.ndarray, targets: np.ndarray, *, prior_readout: np.ndarray | None = None,
        prior_weight: float = 0.0, smoothness_features: np.ndarray | None = None,
        smoothness_weight: float = 0.0, smoothness_targets: np.ndarray | None = None,
        smoothness_channel_scales: np.ndarray | None = None,
    ) -> float:
        """Fit ridge readout, optionally proximal to a trusted parent readout.

        ``smoothness_features`` holds consecutive-feature differences sampled
        within episodes; a positive ``smoothness_weight`` penalizes the action
        change they induce.  This trains temporal smoothness into the readout
        itself, unlike a deployment-side filter (which delays the response).

        ``smoothness_targets`` (derivative matching) supervises the action
        differences toward the TEACHER's differences instead of zero: the
        student may move exactly as fast as the teacher's necessary response,
        but no faster.  ``smoothness_channel_scales`` weights the penalty per
        action channel (e.g. relieving the direction-bearing lateral/yaw
        channels whose fast switching is task-necessary).
        """

        design = _finite_matrix(features, self.feature_dimension, "readout features")
        target_array = _finite_matrix(targets, ACTION_DIMENSION, "teacher actions")
        if len(design) != len(target_array):
            raise ValueError("features and targets must have equal length")
        if not np.isfinite(prior_weight) or prior_weight < 0.0:
            raise ValueError("prior readout weight must be finite and non-negative")
        if not np.isfinite(smoothness_weight) or smoothness_weight < 0.0:
            raise ValueError("smoothness weight must be finite and non-negative")
        if smoothness_weight > 0.0 and smoothness_features is None:
            raise ValueError("a positive smoothness weight requires smoothness_features")
        if smoothness_channel_scales is not None:
            scales = _finite_vector(smoothness_channel_scales, ACTION_DIMENSION, "channel scales")
            if np.any(scales < 0.0):
                raise ValueError("channel scales must be non-negative")
        right = design.T @ np.clip(target_array, -1.0, 1.0)
        if prior_readout is not None:
            prior = _finite_matrix(prior_readout, self.feature_dimension, "prior_readout")
            if prior.shape != (ACTION_DIMENSION, self.feature_dimension):
                raise ValueError("prior readout has invalid shape")
            right += prior_weight * prior.T
        elif prior_weight > 0.0:
            raise ValueError("a positive prior weight requires prior_readout")
        gram = design.T @ design + (self.config.ridge_lambda + prior_weight) * np.eye(self.feature_dimension)
        if smoothness_weight > 0.0:
            delta = _finite_matrix(smoothness_features, self.feature_dimension, "smoothness features")
            scales = np.ones(ACTION_DIMENSION) if smoothness_channel_scales is None else scales
            if smoothness_targets is not None:
                delta_targets = _finite_matrix(smoothness_targets, ACTION_DIMENSION, "smoothness targets")
                if len(delta) != len(delta_targets):
                    raise ValueError("smoothness features and targets must have equal length")
                delta_targets = np.clip(delta_targets, -2.0, 2.0)
            else:
                delta_targets = np.zeros((len(delta), ACTION_DIMENSION))
            if np.allclose(scales, scales[0]):
                # Uniform channel scaling: one shared solve.
                gram += smoothness_weight * scales[0] * (delta.T @ delta)
                right += smoothness_weight * (delta.T @ (delta_targets * scales[None, :]))
                self._readout = np.linalg.solve(gram, right).T
            else:
                # Exact per-channel solves: each output row has its own
                # regularizer strength, so solve the normal equations once
                # per action channel.
                base_right = right.copy()
                rows = []
                for channel in range(ACTION_DIMENSION):
                    channel_gram = gram + smoothness_weight * scales[channel] * (delta.T @ delta)
                    channel_right = base_right[:, channel] + smoothness_weight * scales[channel] * (
                        delta.T @ delta_targets[:, channel])
                    rows.append(np.linalg.solve(channel_gram, channel_right))
                self._readout = np.asarray(rows)
        else:
            self._readout = np.linalg.solve(gram, right).T
        if not np.all(np.isfinite(self._readout)):
            raise RuntimeError("Direct ESN readout became non-finite")
        prediction = np.tanh(design @ self._readout.T)
        return float(np.mean((prediction - np.clip(target_array, -1.0, 1.0)) ** 2))

    def action_from_feature(
        self, feature: np.ndarray, activation: float = 1.0, pose_error: np.ndarray | None = None,
        residual_gain: float = 1.0,
    ) -> DirectESNAction:
        feature_array = _finite_vector(feature, self.feature_dimension, "feature")
        raw = self._readout @ feature_array
        bounded = np.tanh(raw) * float(np.clip(activation, 0.0, 1.0)) * float(np.clip(residual_gain, 0.0, 1.0))
        if self.config.error_aligned_yield and pose_error is not None:
            error = _finite_vector(pose_error, 6, "pose_error")
            linear_error_norm = float(np.linalg.norm(error[:3]))
            if linear_error_norm >= self.config.activation_error_start_m:
                # The ESN chooses *when* and *how strongly* to yield.  The
                # world-frame translation direction is the measurable WBC
                # deviation away from nominal, which removes arbitrary
                # cross-axis readout components without using contact truth.
                magnitude = min(1.0, float(np.linalg.norm(bounded[1:4])))
                bounded[1:4] = -magnitude * error[:3] / linear_error_norm
            angular_error_norm = float(np.linalg.norm(error[3:]))
            if angular_error_norm >= 1.0e-3:
                magnitude = min(1.0, float(np.linalg.norm(bounded[4:7])))
                bounded[4:7] = -magnitude * error[3:] / angular_error_norm
        slowdown = max(0.0, float(bounded[0]))
        wbc_scale = 1.0 - slowdown * (1.0 - self.config.minimum_wbc_scale)
        max_twist = np.array([
            self.config.maximum_linear_yield_mps,
            self.config.maximum_linear_yield_mps,
            self.config.maximum_linear_yield_mps,
            self.config.maximum_angular_yield_radps,
            self.config.maximum_angular_yield_radps,
            self.config.maximum_angular_yield_radps,
        ])
        return DirectESNAction(raw, bounded, float(np.clip(wbc_scale, self.config.minimum_wbc_scale, 1.0)), bounded[1:] * max_twist)

    def act(
        self,
        joint_position: np.ndarray,
        joint_velocity: np.ndarray,
        wbc_task_twist: np.ndarray,
        *,
        pose_error: np.ndarray | None = None,
        twist_error: np.ndarray | None = None,
    ) -> DirectESNAction:
        """Return the direct compliance command.

        Pose and twist errors are measured WBC deviation signals. They are
        deployable (unlike contact force or obstacle truth) and are the key
        phase cue that lets the ESN stay neutral on nominal motion.
        """

        observation = ESNObservation(joint_position, joint_velocity, wbc_task_twist)
        feature = self.advance(observation, pose_error, twist_error)
        if pose_error is None:
            activation = 0.0
        else:
            position_error = float(np.linalg.norm(np.asarray(pose_error, dtype=float)[:3]))
            phase = np.clip(
                (position_error - self.config.activation_error_start_m)
                / (self.config.activation_error_full_m - self.config.activation_error_start_m),
                0.0,
                1.0,
            )
            activation = float(phase * phase * (3.0 - 2.0 * phase))
        residual_gain = 1.0
        if self.config.rejoin_fade_enabled and pose_error is not None and twist_error is not None:
            pose = _finite_vector(pose_error, 6, "pose_error")
            twist = _finite_vector(twist_error, 6, "twist_error")
            scaled_pose = np.concatenate((pose[:3] / 0.012, pose[3:] / 0.20))
            scaled_twist = np.concatenate((twist[:3] / 0.40, twist[3:] / 1.20))
            pose_norm = float(np.linalg.norm(scaled_pose))
            twist_norm = float(np.linalg.norm(scaled_twist))
            if pose_norm > 1.0e-8 and twist_norm > 1.0e-8:
                rejoin_confidence = float(np.clip(
                    -np.dot(scaled_pose, scaled_twist) / (pose_norm * twist_norm), 0.0, 1.0,
                ))
                residual_gain = 1.0 - self.config.rejoin_fade_maximum * rejoin_confidence
        action = self.action_from_feature(
            feature, activation=activation, pose_error=pose_error, residual_gain=residual_gain,
        )
        if self.config.mirror_gate_enabled and pose_error is not None:
            action = self._apply_mirror_gate(action, np.asarray(pose_error, dtype=float))
        if self.config.yield_smoothing_alpha < 1.0:
            # Deployment-side first-order low-pass on the yielding twist.
            # The slowdown channel keeps its direct path; jerk originates in
            # the fast yield transitions this filter attenuates.
            alpha = float(self.config.yield_smoothing_alpha)
            smoothed = alpha * action.yielding_twist + (1.0 - alpha) * self._smoothed_yield_twist
            self._smoothed_yield_twist = smoothed.copy()
            bounded = action.bounded_filter_action.copy()
            scale = np.array([
                self.config.maximum_linear_yield_mps,
                self.config.maximum_linear_yield_mps,
                self.config.maximum_linear_yield_mps,
                self.config.maximum_angular_yield_radps,
                self.config.maximum_angular_yield_radps,
                self.config.maximum_angular_yield_radps,
            ])
            bounded[1:] = np.clip(smoothed / scale, -1.0, 1.0)
            action = DirectESNAction(
                action.raw_readout, bounded, action.wbc_scale, smoothed,
            )
        return action

    def _apply_mirror_gate(self, action, pose_error: np.ndarray) -> DirectESNAction:
        """Flip learned yield channels by the soft sign of matching error channels.

        Equivariance: reflecting the world about the x--z plane sends
        e_y -> -e_y (and e_yaw -> -e_yaw), so the gate sends a_y -> -a_y while
        leaving every other channel untouched.  On the training distribution
        (impacts from -y, hence e_y < 0 during contact) the gate evaluates to
        +1 and the learned action passes through unchanged.
        """

        error = _finite_vector(pose_error, 6, "pose_error")
        epsilon = np.asarray(
            [self.config.mirror_gate_epsilon_m] * 3 + [self.config.mirror_gate_epsilon_rad] * 3)
        soft_sign = -np.tanh(error / epsilon)
        if self.config.mirror_gate_channels == "y":
            gates = np.ones(6)
            gates[1] = soft_sign[1]   # lateral translation follows e_y
            gates[5] = soft_sign[5]   # yaw follows e_yaw
        else:
            gates = soft_sign
        bounded = action.bounded_filter_action.copy()
        bounded[1:] = np.clip(bounded[1:] * gates, -1.0, 1.0)
        limits = np.array([
            self.config.maximum_linear_yield_mps,
            self.config.maximum_linear_yield_mps,
            self.config.maximum_linear_yield_mps,
            self.config.maximum_angular_yield_radps,
            self.config.maximum_angular_yield_radps,
            self.config.maximum_angular_yield_radps,
        ])
        return DirectESNAction(
            action.raw_readout, bounded, action.wbc_scale, bounded[1:] * limits,
        )

    def set_readout(self, readout: np.ndarray) -> None:
        matrix = _finite_matrix(readout, self.feature_dimension, "readout")
        if matrix.shape != (ACTION_DIMENSION, self.feature_dimension):
            raise ValueError("readout has invalid shape")
        self._readout = matrix.copy()

    def readout_copy(self) -> np.ndarray:
        """Return a copy for conservative offline DAgger refits."""

        return self._readout.copy()

    def contract(self) -> dict[str, Any]:
        return {
            "method": "direct_esn_compliant_controller",
            "wbc_role": "fixed nominal trajectory, nominal end-effector twist, and measured tracking error",
            "esn_role": "primary collision-response controller: slowdown, yielding, and rejoin command",
            "ppo_used_in_proposed": False,
            "vmc_used_in_proposed": False,
            "student_input_fields": list(DEPLOYABLE_INPUT_FIELDS),
            "student_input_dimension": DEPLOYABLE_INPUT_DIMENSION,
            "forbidden_online_inputs": list(TEACHER_ONLY_FIELDS),
            "action": {
                "dimension": ACTION_DIMENSION,
                "channels": ["wbc_slowdown", "yield_vx", "yield_vy", "yield_vz", "yield_wx", "yield_wy", "yield_wz"],
                "neutral_zero_action": "fixed WBC",
                "postprocessing": "tanh output with optional deployable WBC-error rejoin fade, then bounded Cartesian velocity and safety slew/torque adapter",
            },
            "reservoir": asdict(self.config),
        }

    def save_npz(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            target,
            readout=self._readout,
            recurrent=self._recurrent,
            input_matrix=self._input,
            bias=self._bias,
            config_json=json.dumps(asdict(self.config)),
            contract_json=json.dumps(self.contract()),
        )

    @classmethod
    def from_npz(cls, path: str | Path) -> "DirectESNController":
        with np.load(path, allow_pickle=False) as archive:
            required = {"readout", "recurrent", "input_matrix", "bias", "config_json"}
            missing = required - set(archive.files)
            if missing:
                raise ValueError(f"{path}: missing serialized fields {sorted(missing)}")
            config = DirectESNConfig(**json.loads(str(archive["config_json"])))
            controller = cls(config)
            recurrent = _finite_matrix(archive["recurrent"], config.reservoir_size, "recurrent")
            input_matrix = _finite_matrix(archive["input_matrix"], DEPLOYABLE_INPUT_DIMENSION, "input_matrix")
            bias = _finite_vector(archive["bias"], config.reservoir_size, "bias")
            if recurrent.shape != (config.reservoir_size, config.reservoir_size) or input_matrix.shape != (config.reservoir_size, DEPLOYABLE_INPUT_DIMENSION):
                raise ValueError("serialized reservoir matrix dimensions do not match config")
            controller._recurrent = recurrent.copy()
            controller._input = input_matrix.copy()
            controller._bias = bias.copy()
            controller.set_readout(archive["readout"])
            return controller


@dataclass(frozen=True)
class PrivilegedTeacherConfig:
    """Deterministic label generator; fields are never student observations."""

    force_onset_N: float = 2.0
    force_full_N: float = 12.0
    maximum_slowdown: float = 0.92
    yield_gain_mps_per_N: float = 0.012
    maximum_yield_mps: float = 0.16
    rejoin_gain_per_s: float = 2.5
    rejoin_error_scale_m: float = 0.012

    def __post_init__(self) -> None:
        values = np.asarray([self.force_onset_N, self.force_full_N, self.maximum_slowdown, self.yield_gain_mps_per_N, self.maximum_yield_mps, self.rejoin_gain_per_s, self.rejoin_error_scale_m])
        if not np.all(np.isfinite(values)) or np.any(values <= 0.0) or self.maximum_slowdown >= 1.0:
            raise ValueError("invalid privileged teacher configuration")
        if self.force_full_N <= self.force_onset_N:
            raise ValueError("force_full_N must exceed force_onset_N")


def privileged_teacher_action(
    contact_force: float,
    contact_normal: np.ndarray,
    contact_duration_s: float,
    signed_distance_m: float,
    pose_error: np.ndarray,
    *,
    config: PrivilegedTeacherConfig = PrivilegedTeacherConfig(),
) -> np.ndarray:
    """Generate one bounded canonical action from privileged collision labels."""

    if not np.isfinite(contact_force) or contact_force < 0.0 or not np.isfinite(contact_duration_s) or contact_duration_s < 0.0 or not np.isfinite(signed_distance_m):
        raise ValueError("teacher scalar inputs must be finite and non-negative where required")
    normal = _finite_vector(contact_normal, 3, "contact_normal")
    error = _finite_vector(pose_error, 6, "pose_error")
    norm = float(np.linalg.norm(normal))
    if norm > 1.0e-8:
        normal = normal / norm
    force_phase = np.clip((contact_force - config.force_onset_N) / (config.force_full_N - config.force_onset_N), 0.0, 1.0)
    penetration_phase = np.clip(max(0.0, -signed_distance_m) / 0.012, 0.0, 1.0)
    onset = float(np.clip(max(force_phase, penetration_phase), 0.0, 1.0))
    slowdown = config.maximum_slowdown * (1.0 - np.exp(-contact_duration_s / 0.06)) * onset
    yielding = -normal * config.yield_gain_mps_per_N * contact_force * (0.5 + 0.5 * onset)
    if onset < 1.0e-6:
        # After release the teacher commands a smooth, error-proportional
        # return to the fixed WBC trajectory instead of an abrupt switch.
        yielding = -config.rejoin_gain_per_s * error[:3] * config.rejoin_error_scale_m
    yielding = np.clip(yielding, -config.maximum_yield_mps, config.maximum_yield_mps)
    action = np.zeros(ACTION_DIMENSION, dtype=float)
    action[0] = np.clip(slowdown, 0.0, 1.0)
    action[1:4] = yielding / config.maximum_yield_mps
    return np.clip(action, -1.0, 1.0)


def build_privileged_teacher_trace(
    contact_force: np.ndarray,
    contact_normal: np.ndarray,
    contact_duration_s: np.ndarray,
    signed_distance_m: np.ndarray,
    pose_error: np.ndarray,
    *,
    config: PrivilegedTeacherConfig = PrivilegedTeacherConfig(),
) -> np.ndarray:
    forces = np.asarray(contact_force, dtype=float)
    normals = _finite_matrix(contact_normal, 3, "contact_normal")
    durations = np.asarray(contact_duration_s, dtype=float)
    distances = np.asarray(signed_distance_m, dtype=float)
    errors = _finite_matrix(pose_error, 6, "pose_error")
    if forces.ndim != 1 or durations.ndim != 1 or distances.ndim != 1 or not np.all(np.isfinite(forces)) or not np.all(np.isfinite(durations)) or not np.all(np.isfinite(distances)):
        raise ValueError("teacher scalar traces must be finite one-dimensional arrays")
    if not (len(forces) == len(normals) == len(durations) == len(distances) == len(errors)):
        raise ValueError("teacher trace fields must have equal length")
    actions = []
    contact_seen = False
    for force, normal, duration, distance, error in zip(forces, normals, durations, distances, errors):
        current_contact = bool(force >= config.force_onset_N or distance < 0.0)
        if current_contact:
            contact_seen = True
            action = privileged_teacher_action(force, normal, duration, distance, error, config=config)
        elif contact_seen:
            # Rejoin is allowed only after the same episode has actually
            # experienced contact. Before first contact, nominal WBC motion
            # must remain exactly neutral.
            action = privileged_teacher_action(force, normal, duration, distance, error, config=config)
        else:
            action = np.zeros(ACTION_DIMENSION, dtype=float)
        actions.append(action)
    return np.asarray(actions)
