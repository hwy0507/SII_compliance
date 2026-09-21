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
TORQUE_INPUT_DIMENSION = 7
TORQUE_INPUT_SCALE = np.array([87.0, 87.0, 87.0, 87.0, 12.0, 12.0, 12.0], dtype=float)
DEPLOYABLE_INPUT_FIELDS = (
    "joint_position_7", "joint_velocity_7", "wbc_task_twist_6",
    "wbc_pose_error_6", "wbc_twist_error_6", "joint_torque_estimate_7",
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
    # Optional two-time-scale reservoir.  The same fixed recurrent matrix is
    # used for all units, but the first ``fast_fraction`` units use the first
    # leak time constant and the rest use the second.  This preserves the ESN
    # linear-readout deployment model while letting different state channels
    # encode impact onset versus unloading/recovery history.
    multiscale_time_constants_s: tuple[float, float] | None = None
    fast_fraction: float = 0.50
    dt_s: float = 0.04
    ridge_lambda: float = 1.0e-4
    seed: int = 20260817
    minimum_wbc_scale: float = 0.20
    maximum_linear_yield_mps: float = 0.16
    maximum_angular_yield_radps: float = 0.60
    activation_error_start_m: float = 0.004
    activation_error_full_m: float = 0.012
    # Collision onset is detected from short-time changes in measured WBC
    # tracking errors.  Absolute tracking error is deliberately not used:
    # fixed-WBC motion can carry a steady offset even with no impact.
    activation_pose_rate_start: float = 0.015
    activation_pose_rate_full: float = 0.080
    activation_twist_rate_start: float = 0.015
    activation_twist_rate_full: float = 0.100
    # Both learned baselines must use the same deployable action-activation
    # rule. ``always_on`` is required for action-complete distillation because
    # ``teacher_action`` already stores the final action actually applied by
    # the VMC; multiplying it by a second error gate makes some labels
    # unrepresentable. The error gates are retained only as matched ablations.
    activation_mode: str = "transient_error_rate"
    # Optional learned intervention head.  It is trained from whether the
    # teacher's *direct residual action* is nonzero, but at deployment uses
    # only the same encoded proprioceptive/WBC observation as the action
    # readout.  A hard threshold makes the neutral WBC action exact outside a
    # predicted compliance episode, avoiding small regression bias accumulating
    # during grasp approach.
    intervention_gate_enabled: bool = False
    intervention_gate_threshold: float = 0.50
    # Experimental opt-in.  The published baseline/proposed checkpoints keep
    # the original world-frame readout unless this switch is explicitly set.
    error_aligned_yield: bool = False
    error_aligned_lift_only: bool = False
    # Translational components used by error-aligned yielding.  Keeping only
    # xy preserves the learned vertical lift command in overhead-board tasks.
    error_aligned_yield_axes: str = "xyz"
    rejoin_fade_enabled: bool = False
    rejoin_fade_maximum: float = 0.85
    # First-order low-pass on the emitted yielding twist (1.0 disables it).
    # Deployment-side smoothing only: offline readout fitting never sees it.
    yield_smoothing_alpha: float = 1.0
    # Small deployable anticipatory gate during nominal upward motion.  This
    # uses only the commanded WBC twist and is useful when an obstacle already
    # occupies the lift corridor at the instant the lift begins; it does not
    # use contact force, signed distance, or obstacle state.
    lift_preview_activation: float = 0.0
    # Mirror-equivariant action gating: multiply the learned yield channels by
    # a soft sign of the matching pose-error channel.  Under the training
    # distribution (impacts from -y) the soft sign is +1, so the transform is
    # the identity and existing checkpoints are unaffected; under a mirrored
    # impact the learned action flips sign exactly, giving structural mirror
    # generalization instead of data augmentation.  "y" gates only the
    # lateral/yaw channels; "full" gates all six twist channels.
    # Memoryless ablation control: zeroing the recurrent weights turns the
    # reservoir into a stateless random-feature map at identical input scale,
    # dimension, and readout training (an ESN-vs-random-features control).
    disable_recurrence: bool = False
    # Partial-observation ablation: zero the twist-error channels in BOTH
    # training features and deployment, forcing any contact/phase inference
    # to come from motion history (reservoir memory) rather than the
    # velocity-error signal.
    zero_twist_error: bool = False
    zero_joint_velocity: bool = False
    include_torque_estimate: bool = False
    # ``motor`` is the causal motor-current / joint-torque estimate itself.
    # ``delta`` is its one-control-step innovation.  Both are deployment-
    # available and have the same seven-dimensional contract; neither is a
    # MuJoCo contact wrench or privileged obstacle feature.
    torque_feature_mode: str = "motor"
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
            self.activation_pose_rate_start, self.activation_pose_rate_full,
            self.activation_twist_rate_start, self.activation_twist_rate_full,
            self.rejoin_fade_maximum,
            self.intervention_gate_threshold,
        ], dtype=float)
        if self.reservoir_size < 1:
            raise ValueError("reservoir_size must be positive")
        if not np.all(np.isfinite(values)) or np.any(values <= 0.0):
            raise ValueError("Direct ESN parameters must be finite and positive")
        if self.minimum_wbc_scale >= 1.0:
            raise ValueError("minimum_wbc_scale must be below one")
        if self.torque_feature_mode not in ("motor", "delta"):
            raise ValueError("torque_feature_mode must be 'motor' or 'delta'")
        if self.time_constant_s < self.dt_s:
            raise ValueError("time_constant_s must be at least dt_s")
        if not np.isfinite(self.fast_fraction) or not 0.0 < self.fast_fraction < 1.0:
            raise ValueError("fast_fraction must lie strictly in (0,1)")
        if self.multiscale_time_constants_s is not None:
            scales = tuple(float(item) for item in self.multiscale_time_constants_s)
            if len(scales) != 2 or not np.all(np.isfinite(scales)) or min(scales) < self.dt_s:
                raise ValueError("multiscale_time_constants_s must hold two finite values at least dt_s")
            if not scales[0] < scales[1]:
                raise ValueError("multiscale time constants must be ordered fast < slow")
            object.__setattr__(self, "multiscale_time_constants_s", scales)
        if self.activation_error_full_m <= self.activation_error_start_m:
            raise ValueError("activation_error_full_m must exceed activation_error_start_m")
        if self.activation_pose_rate_full <= self.activation_pose_rate_start:
            raise ValueError("activation_pose_rate_full must exceed activation_pose_rate_start")
        if self.activation_twist_rate_full <= self.activation_twist_rate_start:
            raise ValueError("activation_twist_rate_full must exceed activation_twist_rate_start")
        if self.connection_probability > 1.0 or self.spectral_radius > 2.0:
            raise ValueError("reservoir probability/radius is out of bounds")
        if self.rejoin_fade_maximum > 1.0:
            raise ValueError("rejoin fade maximum cannot exceed one")
        if not 0.0 < self.yield_smoothing_alpha <= 1.0:
            raise ValueError("yield_smoothing_alpha must lie in (0, 1]")
        if not np.isfinite(self.lift_preview_activation) or not 0.0 <= self.lift_preview_activation <= 1.0:
            raise ValueError("lift_preview_activation must lie in [0, 1]")
        if self.mirror_gate_channels not in ("y", "full"):
            raise ValueError("mirror_gate_channels must be 'y' or 'full'")
        if self.activation_mode not in ("always_on", "transient_error_rate", "absolute_position_error"):
            raise ValueError("unsupported activation_mode")
        if not 0.0 < self.intervention_gate_threshold < 1.0:
            raise ValueError("intervention_gate_threshold must lie strictly in (0, 1)")
        if self.error_aligned_yield_axes not in ("xy", "xyz"):
            raise ValueError("error_aligned_yield_axes must be 'xy' or 'xyz'")

    @property
    def leak(self) -> float:
        return self.dt_s / self.time_constant_s

    @property
    def leak_vector(self) -> np.ndarray:
        if self.multiscale_time_constants_s is None:
            return np.full(self.reservoir_size, self.leak, dtype=float)
        fast, slow = self.multiscale_time_constants_s
        cut = int(round(self.fast_fraction * self.reservoir_size))
        cut = min(max(cut, 1), self.reservoir_size - 1)
        return np.concatenate((
            np.full(cut, self.dt_s / fast, dtype=float),
            np.full(self.reservoir_size - cut, self.dt_s / slow, dtype=float),
        ))


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
    joint_torque_estimate: np.ndarray | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "joint_position", _finite_vector(self.joint_position, 7, "joint_position"))
        object.__setattr__(self, "joint_velocity", _finite_vector(self.joint_velocity, 7, "joint_velocity"))
        object.__setattr__(self, "wbc_task_twist", _finite_vector(self.wbc_task_twist, 6, "wbc_task_twist"))
        object.__setattr__(self, "wbc_pose_error", _finite_vector(self.wbc_pose_error, 6, "wbc_pose_error"))
        object.__setattr__(self, "wbc_twist_error", _finite_vector(self.wbc_twist_error, 6, "wbc_twist_error"))
        torque = np.zeros(7, dtype=float) if self.joint_torque_estimate is None else self.joint_torque_estimate
        object.__setattr__(self, "joint_torque_estimate", _finite_vector(torque, 7, "joint_torque_estimate"))


def encode_direct_esn_observation(observation: DirectESNObservation, *, include_torque_estimate: bool = False) -> np.ndarray:
    """Encode proprioception, nominal twist, and measured WBC deviation."""

    base = encode_student_observation(ESNObservation(
        observation.joint_position, observation.joint_velocity, observation.wbc_task_twist,
    ))
    pose_scales = np.array([0.012] * 3 + [0.20] * 3)
    twist_scales = np.array([0.40] * 3 + [1.20] * 3)
    errors = np.concatenate((observation.wbc_pose_error / pose_scales, observation.wbc_twist_error / twist_scales))
    encoded = np.concatenate((base, errors))
    if include_torque_estimate:
        encoded = np.concatenate((encoded, observation.joint_torque_estimate / TORQUE_INPUT_SCALE))
    return np.clip(encoded, -10.0, 10.0)


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
        if config.disable_recurrence:
            self._recurrent = np.zeros_like(self._recurrent)
        self.input_dimension = DEPLOYABLE_INPUT_DIMENSION + (TORQUE_INPUT_DIMENSION if config.include_torque_estimate else 0)
        self._input = rng.uniform(-config.input_scale, config.input_scale, (config.reservoir_size, self.input_dimension))
        self._bias = rng.uniform(-config.bias_scale, config.bias_scale, config.reservoir_size)
        self._leak_vector = config.leak_vector
        self._state = np.zeros(config.reservoir_size, dtype=float)
        self._readout = np.zeros((ACTION_DIMENSION, self.feature_dimension), dtype=float)
        self._nonlinear_readout = None
        self._intervention_readout = np.zeros(self.feature_dimension, dtype=float)
        self._smoothed_yield_twist = np.zeros(6, dtype=float)
        self._previous_pose_error: np.ndarray | None = None
        self._previous_twist_error: np.ndarray | None = None
        self._previous_torque_feature_source: np.ndarray | None = None
        self.last_activation = 0.0
        self.last_intervention_probability = 0.0

    @property
    def feature_dimension(self) -> int:
        return 1 + self.input_dimension + self.config.reservoir_size

    @property
    def state(self) -> np.ndarray:
        return self._state.copy()

    @property
    def readout(self) -> np.ndarray:
        if self._nonlinear_readout is not None:
            raise ValueError("Nonlinear-head checkpoints do not expose a single linear readout")
        return self._readout.copy()

    def reset(self, state: np.ndarray | None = None) -> None:
        self._smoothed_yield_twist.fill(0.0)
        self._previous_pose_error = None
        self._previous_twist_error = None
        self._previous_torque_feature_source = None
        self.last_activation = 0.0
        self.last_intervention_probability = 0.0
        if state is None:
            self._state.fill(0.0)
            return
        state_array = _finite_vector(state, self.config.reservoir_size, "initial reservoir state")
        self._state = np.clip(state_array, -1.0, 1.0)

    def _advance_encoded(self, encoded_input: np.ndarray) -> np.ndarray:
        encoded = _finite_vector(encoded_input, self.input_dimension, "encoded student input")
        proposal = np.tanh(self._input @ encoded + self._recurrent @ self._state + self._bias)
        self._state = (1.0 - self._leak_vector) * self._state + self._leak_vector * proposal
        if not np.all(np.isfinite(self._state)):
            raise RuntimeError("Direct ESN reservoir state became non-finite")
        return np.concatenate(([1.0], encoded, self._state))

    def advance(self, observation: DirectESNObservation | ESNObservation, pose_error: np.ndarray | None = None, twist_error: np.ndarray | None = None) -> np.ndarray:
        """Advance using deployment-available state and WBC deviation."""

        if self.config.zero_twist_error or self.config.zero_joint_velocity:
            # Partial-observation ablations apply identically in training
            # features and deployment, so both see the same information set.
            from dataclasses import replace as _replace
            if isinstance(observation, DirectESNObservation):
                fields = {}
                if self.config.zero_twist_error:
                    fields["wbc_twist_error"] = np.zeros(6)
                if self.config.zero_joint_velocity:
                    fields["joint_velocity"] = np.zeros(7)
                observation = _replace(observation, **fields)
            if twist_error is not None and self.config.zero_twist_error:
                twist_error = np.zeros(6)
        if isinstance(observation, DirectESNObservation):
            if self.config.include_torque_estimate and self.config.torque_feature_mode == "delta":
                from dataclasses import replace as _replace
                motor_torque = observation.joint_torque_estimate.copy()
                feature_torque = (np.zeros(7, dtype=float)
                                  if self._previous_torque_feature_source is None
                                  else motor_torque - self._previous_torque_feature_source)
                self._previous_torque_feature_source = motor_torque
                observation = _replace(observation, joint_torque_estimate=feature_torque)
            encoded = encode_direct_esn_observation(observation, include_torque_estimate=self.config.include_torque_estimate)
        else:
            pose = np.zeros(6) if pose_error is None else _finite_vector(pose_error, 6, "wbc_pose_error")
            twist = np.zeros(6) if twist_error is None else _finite_vector(twist_error, 6, "wbc_twist_error")
            encoded = encode_direct_esn_observation(DirectESNObservation(
                observation.joint_position, observation.joint_velocity, observation.wbc_task_twist, pose, twist,
            ), include_torque_estimate=self.config.include_torque_estimate)
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

        if self._nonlinear_readout is not None:
            raise ValueError("Linear fit_readout cannot update a nonlinear head")
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

    def fit_intervention_gate(
        self, features: np.ndarray, intervention_labels: np.ndarray, *,
        l2: float = 1.0e-4, steps: int = 800, learning_rate: float = 0.08,
    ) -> dict[str, float]:
        """Fit a class-balanced logistic head on the fixed ESN features.

        This is not a contact classifier: labels are derived solely from the
        teacher action being nonzero.  At deployment the head reads exactly the
        same causal feature vector as the direct action readout.
        """

        design = _finite_matrix(features, self.feature_dimension, "intervention features")
        labels = np.asarray(intervention_labels, dtype=float).reshape(-1)
        if len(labels) != len(design) or not np.all(np.isfinite(labels)):
            raise ValueError("intervention labels must be finite and match features")
        labels = (labels > 0.5).astype(float)
        if not np.isfinite(l2) or l2 < 0.0 or steps < 1 or learning_rate <= 0.0:
            raise ValueError("invalid intervention-head optimizer parameters")
        positives = float(np.sum(labels))
        negatives = float(len(labels) - positives)
        if positives < 1.0 or negatives < 1.0:
            raise ValueError("intervention gate requires both positive and negative labels")
        sample_weight = np.where(labels > 0.5, negatives / positives, 1.0)
        weight_sum = float(np.sum(sample_weight))
        params = np.zeros(self.feature_dimension, dtype=float)
        for _ in range(int(steps)):
            logits = np.clip(design @ params, -40.0, 40.0)
            probability = 1.0 / (1.0 + np.exp(-logits))
            gradient = (design.T @ (sample_weight * (probability - labels))) / weight_sum + l2 * params
            params -= float(learning_rate) * gradient
        self._intervention_readout = params
        probability = self.intervention_probability(design)
        prediction = probability >= self.config.intervention_gate_threshold
        return {
            "positive_fraction": float(np.mean(labels)),
            "balanced_accuracy": float(0.5 * (
                np.mean(prediction[labels > 0.5]) + np.mean(~prediction[labels < 0.5])
            )),
        }

    def intervention_probability(self, feature: np.ndarray) -> np.ndarray | float:
        values = np.asarray(feature, dtype=float)
        if values.ndim == 1:
            vector = _finite_vector(values, self.feature_dimension, "intervention feature")
            score = float(np.clip(vector @ self._intervention_readout, -40.0, 40.0))
            return float(1.0 / (1.0 + np.exp(-score)))
        matrix = _finite_matrix(values, self.feature_dimension, "intervention features")
        score = np.clip(matrix @ self._intervention_readout, -40.0, 40.0)
        return 1.0 / (1.0 + np.exp(-score))

    def action_from_feature(
        self, feature: np.ndarray, activation: float = 1.0, pose_error: np.ndarray | None = None,
        residual_gain: float = 1.0, intervention_gain: float = 1.0,
    ) -> DirectESNAction:
        feature_array = _finite_vector(feature, self.feature_dimension, "feature")
        if self._nonlinear_readout is None:
            raw = self._readout @ feature_array
        else:
            head = self._nonlinear_readout
            normalized = (feature_array-head["nl_mean"])/head["nl_std"]
            hidden = np.tanh(head["nl_w1"] @ normalized + head["nl_b1"])
            raw = head["nl_w2"] @ hidden + head["nl_b2"]
        bounded = (np.tanh(raw) * float(np.clip(activation, 0.0, 1.0))
                   * float(np.clip(residual_gain, 0.0, 1.0))
                   * float(np.clip(intervention_gain, 0.0, 1.0)))
        if self.config.error_aligned_yield and pose_error is not None:
            error = _finite_vector(pose_error, 6, "pose_error")
            aligned_error = error[:3]
            if self.config.error_aligned_yield_axes == "xy":
                aligned_error = error[:2]
            linear_error_norm = float(np.linalg.norm(aligned_error))
            if linear_error_norm >= self.config.activation_error_start_m:
                # The ESN chooses *when* and *how strongly* to yield.  The
                # world-frame translation direction is the measurable WBC
                # deviation away from nominal, which removes arbitrary
                # cross-axis readout components without using contact truth.
                magnitude = min(1.0, float(np.linalg.norm(bounded[1:4])))
                if self.config.error_aligned_yield_axes == "xyz":
                    bounded[1:4] = -magnitude * error[:3] / linear_error_norm
                else:
                    lateral_magnitude = min(1.0, float(np.linalg.norm(bounded[1:3])))
                    bounded[1:3] = -lateral_magnitude * error[:2] / linear_error_norm
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

    def _activation(
        self, pose_error: np.ndarray | None, twist_error: np.ndarray | None,
    ) -> float:
        """Smoothly open on short-time measured-error transients only."""
        if self.config.activation_mode == "always_on":
            return 1.0
        if self.config.activation_mode == "absolute_position_error":
            if pose_error is None:
                return 0.0
            position_error = float(np.linalg.norm(
                _finite_vector(pose_error, 6, "pose_error")[:3]))
            phase = np.clip(
                (position_error - self.config.activation_error_start_m)
                / (self.config.activation_error_full_m - self.config.activation_error_start_m),
                0.0, 1.0,
            )
            return float(phase * phase * (3.0 - 2.0 * phase))
        pose_phase = 0.0
        twist_phase = 0.0
        if pose_error is not None:
            pose = _finite_vector(pose_error, 6, "pose_error")
            if self._previous_pose_error is not None:
                scales = np.asarray([0.012] * 3 + [0.20] * 3)
                delta_norm = float(np.linalg.norm((pose - self._previous_pose_error) / scales))
                pose_phase = np.clip(
                    (delta_norm - self.config.activation_pose_rate_start)
                    / (self.config.activation_pose_rate_full - self.config.activation_pose_rate_start),
                    0.0, 1.0,
                )
            self._previous_pose_error = pose.copy()
        if twist_error is not None:
            twist = _finite_vector(twist_error, 6, "twist_error")
            if self._previous_twist_error is not None:
                scales = np.asarray([0.40] * 3 + [1.20] * 3)
                delta_norm = float(np.linalg.norm((twist - self._previous_twist_error) / scales))
                twist_phase = np.clip(
                    (delta_norm - self.config.activation_twist_rate_start)
                    / (self.config.activation_twist_rate_full - self.config.activation_twist_rate_start),
                    0.0, 1.0,
                )
            self._previous_twist_error = twist.copy()
        phase = max(float(pose_phase), float(twist_phase))
        return float(phase * phase * (3.0 - 2.0 * phase))

    def activation_from_errors(self, pose_error: np.ndarray | None, twist_error: np.ndarray | None) -> float:
        """Return the current deployable transient gate for offline diagnostics."""
        return self._activation(pose_error, twist_error)

    def act(
        self,
        joint_position: np.ndarray,
        joint_velocity: np.ndarray,
        wbc_task_twist: np.ndarray,
        *,
        pose_error: np.ndarray | None = None,
        twist_error: np.ndarray | None = None,
        joint_torque_estimate: np.ndarray | None = None,
    ) -> DirectESNAction:
        """Return the direct compliance command.

        Pose and twist errors are measured WBC deviation signals. They are
        deployable (unlike contact force or obstacle truth) and are the key
        phase cue that lets the ESN stay neutral on nominal motion.
        """

        observation = DirectESNObservation(
            joint_position, joint_velocity, wbc_task_twist,
            np.zeros(6) if pose_error is None else pose_error,
            np.zeros(6) if twist_error is None else twist_error,
            joint_torque_estimate,
        )
        feature = self.advance(observation, pose_error, twist_error)
        activation = self._activation(pose_error, twist_error)
        self.last_activation = activation
        intervention_gain = 1.0
        if self.config.intervention_gate_enabled:
            probability = float(self.intervention_probability(feature))
            self.last_intervention_probability = probability
            intervention_gain = float(probability >= self.config.intervention_gate_threshold)
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
            intervention_gain=intervention_gain,
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
        if self._nonlinear_readout is not None:
            raise ValueError("Use set_nonlinear_readout for a nonlinear-head checkpoint")
        matrix = _finite_matrix(readout, self.feature_dimension, "readout")
        if matrix.shape != (ACTION_DIMENSION, self.feature_dimension):
            raise ValueError("readout has invalid shape")
        self._readout = matrix.copy()

    def readout_copy(self) -> np.ndarray:
        """Return a copy for conservative offline DAgger refits."""
        if self._nonlinear_readout is not None:
            raise ValueError("Nonlinear-head checkpoints do not have a single linear readout")
        return self._readout.copy()

    def contract(self) -> dict[str, Any]:
        return {
            "method": "direct_esn_compliant_controller",
            "readout_architecture": "linear" if self._nonlinear_readout is None else "normalized_hidden_tanh",
            "readout_hidden_units": 0 if self._nonlinear_readout is None else len(self._nonlinear_readout["nl_b1"]),
            "wbc_role": "fixed nominal trajectory, nominal end-effector twist, and measured tracking error",
            "esn_role": "primary collision-response controller: slowdown, yielding, and rejoin command",
            "ppo_used_in_proposed": False,
            "vmc_used_in_proposed": False,
            "student_input_fields": list(DEPLOYABLE_INPUT_FIELDS),
            "student_input_dimension": self.input_dimension,
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
            intervention_readout=self._intervention_readout,
            recurrent=self._recurrent,
            input_matrix=self._input,
            bias=self._bias,
            config_json=json.dumps(asdict(self.config)),
            contract_json=json.dumps(self.contract()),
            **({} if self._nonlinear_readout is None else self._nonlinear_readout),
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
            input_matrix = _finite_matrix(archive["input_matrix"], controller.input_dimension, "input_matrix")
            bias = _finite_vector(archive["bias"], config.reservoir_size, "bias")
            if recurrent.shape != (config.reservoir_size, config.reservoir_size) or input_matrix.shape != (config.reservoir_size, controller.input_dimension):
                raise ValueError("serialized reservoir matrix dimensions do not match config")
            controller._recurrent = recurrent.copy()
            controller._input = input_matrix.copy()
            controller._bias = bias.copy()
            controller.set_readout(archive["readout"])
            head_keys={"nl_mean","nl_std","nl_w1","nl_b1","nl_w2","nl_b2"}
            present=head_keys & set(archive.files)
            if present:
                if present != head_keys:
                    raise ValueError("Incomplete nonlinear readout checkpoint")
                controller.set_nonlinear_readout(**{k:archive[k] for k in head_keys})
            if "intervention_readout" in archive:
                controller._intervention_readout = _finite_vector(
                    archive["intervention_readout"], controller.feature_dimension, "intervention_readout")
            return controller

    def set_nonlinear_readout(self, *, nl_mean, nl_std, nl_w1, nl_b1, nl_w2, nl_b2):
        """Trainable tanh head on the same fixed causal reservoir features.

        This optional head has the same normalized one-hidden-layer form as
        the MLP baseline. It adds no observations, gates or phase supervision.
        """
        mean=_finite_vector(nl_mean,self.feature_dimension,"head mean")
        std=_finite_vector(nl_std,self.feature_dimension,"head std")
        first=_finite_matrix(nl_w1,self.feature_dimension,"head input weights")
        bias=_finite_vector(nl_b1,len(first),"head hidden bias")
        second=_finite_matrix(nl_w2,len(first),"head output weights")
        output_bias=_finite_vector(nl_b2,ACTION_DIMENSION,"head output bias")
        if np.any(std<=0) or second.shape[0]!=ACTION_DIMENSION:
            raise ValueError("Invalid nonlinear readout dimensions or normalization")
        self._nonlinear_readout={"nl_mean":mean.copy(),"nl_std":std.copy(),
             "nl_w1":first.copy(),"nl_b1":bias.copy(),"nl_w2":second.copy(),"nl_b2":output_bias.copy()}


class MultiHeadDirectESNController:
    """Independent ESN with phase-specialized direct compliance readouts.

    The recurrent state and the 32-D deployable observation are identical to
    :class:`DirectESNController`.  Only the linear readout is split into three
    heads.  A continuous gate is computed from the *nominal WBC vertical
    twist* already present in the student input: the descending/approach head,
    the rising/lift head, and a near-zero-twist rejoin head.  This is a
    reference-phase cue, not a contact label; no board pose, force, object
    state, or contact timing is available to this class.

    Keeping the gate outside the trained feature vector makes the information
    contract auditable while allowing one shared reservoir to learn different
    responses for the two mechanically distinct impacts.
    """

    family = "direct_esn_multhead"
    HEAD_NAMES = ("pre_contact", "post_contact", "rejoin")

    def __init__(self, config: DirectESNConfig = DirectESNConfig(), head_count: int = 3) -> None:
        if head_count != len(self.HEAD_NAMES):
            raise ValueError("the mult-head controller currently requires three heads")
        self.config = config
        self._base = DirectESNController(config)
        self._readout_heads = np.zeros((head_count, ACTION_DIMENSION, self.feature_dimension), dtype=float)

    @property
    def feature_dimension(self) -> int:
        return self._base.feature_dimension

    @property
    def reservoir_size(self) -> int:
        return self.config.reservoir_size

    @property
    def readout_heads(self) -> np.ndarray:
        return self._readout_heads.copy()

    @property
    def state(self) -> np.ndarray:
        return self._base.state

    def reset(self) -> None:
        self._base.reset()

    def _phase_gates(self, feature: np.ndarray) -> np.ndarray:
        """Return [approach, lift, rejoin] weights from nominal WBC twist.

        ``feature[16]`` is the normalized nominal z velocity (the first seven
        entries are q, the next seven qdot, then nominal twist).  The smooth
        tanh/exp construction avoids a hard phase switch and remains valid
        when the commanded vertical velocity is small or changes sign.
        """

        normalized_vertical_twist = float(np.clip(feature[16], -10.0, 10.0))
        phase = np.tanh(normalized_vertical_twist / 0.22)
        approach = 0.5 * (1.0 - phase)
        lift = 0.5 * (1.0 + phase)
        rejoin = float(np.exp(-abs(normalized_vertical_twist) / 0.16))
        weights = np.asarray([approach, lift, rejoin], dtype=float)
        total = float(np.sum(weights))
        return weights / total if total > 1.0e-12 else np.full(3, 1.0 / 3.0)

    def phase_gates(self, feature: np.ndarray) -> np.ndarray:
        """Public read-only gate helper for offline audits and unit tests."""

        return self._phase_gates(_finite_vector(feature, self.feature_dimension, "feature"))

    def set_readout_heads(self, readout_heads: np.ndarray) -> None:
        matrix = np.asarray(readout_heads, dtype=float)
        if matrix.shape != self._readout_heads.shape or not np.all(np.isfinite(matrix)):
            raise ValueError(f"readout_heads must have shape {self._readout_heads.shape}")
        self._readout_heads = matrix.copy()

    def _effective_readout(self, feature: np.ndarray) -> np.ndarray:
        return np.tensordot(self._phase_gates(feature), self._readout_heads, axes=(0, 0))

    def act(
        self,
        joint_position: np.ndarray,
        joint_velocity: np.ndarray,
        wbc_task_twist: np.ndarray,
        *,
        pose_error: np.ndarray | None = None,
        twist_error: np.ndarray | None = None,
    ) -> DirectESNAction:
        observation = DirectESNObservation(
            joint_position, joint_velocity, wbc_task_twist,
            np.zeros(6) if pose_error is None else pose_error,
            np.zeros(6) if twist_error is None else twist_error,
        )
        feature = self._base.advance(observation)
        effective = self._effective_readout(feature)
        previous = self._base._readout
        self._base._readout = effective
        try:
            activation = self._base._activation(pose_error, twist_error)
            self._base.last_activation = activation
            action = self._base.action_from_feature(
                feature, activation=activation, pose_error=pose_error,
            )
            # Before contact, tracking-error activation is normally zero.  A
            # bounded preview gate lets the learned readout make a small
            # tangential adjustment during nominal upward motion, using only
            # the deployable WBC phase cue.  Preserve the slowdown channel from
            # the measured-error path and preview only Cartesian yielding.
            if (self.config.lift_preview_activation > 0.0
                    and float(wbc_task_twist[2]) > 0.02
                    and self.config.lift_preview_activation > activation):
                preview = self._base.action_from_feature(
                    feature, activation=self.config.lift_preview_activation,
                    pose_error=pose_error,
                )
                bounded = action.bounded_filter_action.copy()
                bounded[1:] = preview.bounded_filter_action[1:]
                action = DirectESNAction(
                    action.raw_readout, bounded, action.wbc_scale,
                    preview.yielding_twist,
                )
        finally:
            self._base._readout = previous
        if self.config.mirror_gate_enabled and pose_error is not None:
            action = self._base._apply_mirror_gate(action, np.asarray(pose_error, dtype=float))
        if self.config.yield_smoothing_alpha < 1.0:
            alpha = float(self.config.yield_smoothing_alpha)
            smoothed = alpha * action.yielding_twist + (1.0 - alpha) * self._base._smoothed_yield_twist
            self._base._smoothed_yield_twist = smoothed.copy()
            bounded = action.bounded_filter_action.copy()
            scale = np.asarray([
                self.config.maximum_linear_yield_mps] * 3
                + [self.config.maximum_angular_yield_radps] * 3,
            )
            bounded[1:] = np.clip(smoothed / scale, -1.0, 1.0)
            action = DirectESNAction(action.raw_readout, bounded, action.wbc_scale, smoothed)
        return action

    def contract(self) -> dict[str, Any]:
        payload = self._base.contract()
        payload.update({
            "method": self.family,
            "readout_heads": list(self.HEAD_NAMES),
            "phase_gate": {
                "source": "normalized nominal WBC vertical twist feature[16]",
                "uses_contact_label": False,
                "uses_obstacle_or_object_state": False,
                "formula": "soft tanh approach/lift weights plus exp near-zero rejoin weight",
            },
        })
        return payload

    def save_npz(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            target, readout_heads=self._readout_heads,
            recurrent=self._base._recurrent, input_matrix=self._base._input,
            bias=self._base._bias, config_json=json.dumps(asdict(self.config)),
            contract_json=json.dumps(self.contract()),
        )

    @classmethod
    def from_npz(cls, path: str | Path) -> "MultiHeadDirectESNController":
        with np.load(path, allow_pickle=False) as archive:
            required = {"readout_heads", "recurrent", "input_matrix", "bias", "config_json"}
            missing = required - set(archive.files)
            if missing:
                raise ValueError(f"{path}: missing serialized fields {sorted(missing)}")
            config = DirectESNConfig(**json.loads(str(archive["config_json"])))
            controller = cls(config)
            recurrent = _finite_matrix(archive["recurrent"], config.reservoir_size, "recurrent")
            input_matrix = _finite_matrix(archive["input_matrix"], DEPLOYABLE_INPUT_DIMENSION, "input_matrix")
            bias = _finite_vector(archive["bias"], config.reservoir_size, "bias")
            if recurrent.shape != (config.reservoir_size, config.reservoir_size):
                raise ValueError("serialized recurrent matrix dimensions do not match config")
            controller._base._recurrent = recurrent.copy()
            controller._base._input = input_matrix.copy()
            controller._base._bias = bias.copy()
            controller.set_readout_heads(archive["readout_heads"])
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
