"""Deployable Fan Ye state adapters for WBC-aware residual actors.

The original comparison exposes a matched 20-D proprioceptive feature to the
MLP and appends a fixed 64-D Fan Ye reservoir state for the ESN.  That input is
too indirect for a recovery controller: the action filter knows the measured
WBC tracking departure, while the actor previously had to infer both its size
and direction from joint motion.  The v2 adapter therefore adds only the
deployable WBC pose/twist tracking errors.  It deliberately still excludes
contact, force, rod state, obstacle geometry, future release, and fixture ID.

``fan_ye_esn`` retains the frozen v1 reservoir for a clean historical
comparison.  ``fan_ye_multiscale_esn`` replaces it with fixed fast/slow Fan
Ye-style reservoirs driven by the 32-D error-aware input, so loading and
release/rejoin can be represented at separate time constants.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from esn_compliance import ESNObservation, encode_student_observation
from fan_ye_esn_design import FanYeAlignedESN, FanYeESNConfig, FanYeInputNormalizer


CURRENT_WBC_FEATURE_DIMENSION = 32
WBC_POSE_ERROR_SCALE = np.array([0.060, 0.060, 0.060, 0.20, 0.20, 0.20], dtype=float)
WBC_TWIST_ERROR_SCALE = np.array([0.60, 0.60, 0.60, 2.0, 2.0, 2.0], dtype=float)


def encode_wbc_current_feature(
    observation: ESNObservation, pose_error: np.ndarray, twist_error: np.ndarray,
) -> np.ndarray:
    """Encode current state plus measured WBC tracking errors.

    The two error channels are available from the WBC target and robot state at
    the same control instant.  They are not collision proxies and do not use
    privileged simulation diagnostics.
    """

    pose = np.asarray(pose_error, dtype=float)
    twist = np.asarray(twist_error, dtype=float)
    if pose.shape != (6,) or twist.shape != (6,) or not np.all(np.isfinite(pose)) or not np.all(np.isfinite(twist)):
        raise ValueError("WBC pose and twist errors must be finite six-vectors")
    base = encode_student_observation(observation)
    encoded = np.concatenate((base, pose / WBC_POSE_ERROR_SCALE, twist / WBC_TWIST_ERROR_SCALE))
    return np.clip(encoded, -10.0, 10.0).astype(np.float32)


class FanYeESNRLObservationAdapter:
    """Stateful, resettable current-state and multi-timescale ESN map."""

    student_input_fields = ("joint_position_7", "joint_velocity_7", "wbc_task_twist_6", "wbc_pose_error_6", "wbc_twist_error_6")
    excluded_fields = ("rod_contact", "rod_force", "rod_penetration", "rod_state", "obstacle_pose_or_geometry", "future_release", "fixture_id", "recovery_gate")

    def __init__(self, model_npz: Path, training_summary_json: Path) -> None:
        summary = json.loads(training_summary_json.read_text())
        self.reservoir = FanYeAlignedESN(FanYeESNConfig(**summary["config"]))
        if self.reservoir.config.input_dimension != 20:
            raise ValueError("the frozen v1 Fan Ye reservoir must use the legacy 20-D input")
        with np.load(model_npz) as archive:
            self.normalizer = FanYeInputNormalizer(archive["input_normalizer_scales"])
        # Fixed, causally distinct reservoirs.  The fast reservoir resolves the
        # loading transient while the slow one preserves release/rejoin context.
        base = self.reservoir.config
        self.multiscale_reservoirs = (
            FanYeAlignedESN(FanYeESNConfig(
                reservoir_size=64, spectral_radius=base.spectral_radius,
                input_scale=base.input_scale * 0.70, time_constant_s=base.dt_s,
                connection_probability=base.connection_probability, bias_scale=base.bias_scale,
                ridge_lambda=base.ridge_lambda, dt_s=base.dt_s, seed=base.seed + 101,
                input_dimension=CURRENT_WBC_FEATURE_DIMENSION,
            )),
            FanYeAlignedESN(FanYeESNConfig(
                reservoir_size=64, spectral_radius=base.spectral_radius,
                input_scale=base.input_scale, time_constant_s=min(0.320, base.time_constant_s * 4.0),
                connection_probability=base.connection_probability, bias_scale=base.bias_scale,
                ridge_lambda=base.ridge_lambda, dt_s=base.dt_s, seed=base.seed + 202,
                input_dimension=CURRENT_WBC_FEATURE_DIMENSION,
            )),
        )
        self.feature_dimension = CURRENT_WBC_FEATURE_DIMENSION + self.reservoir.config.reservoir_size
        self.multiscale_feature_dimension = CURRENT_WBC_FEATURE_DIMENSION + sum(
            item.config.reservoir_size for item in self.multiscale_reservoirs
        )
        self.reset()

    def reset(self) -> None:
        self.reservoir.reset()
        for reservoir in self.multiscale_reservoirs:
            reservoir.reset()

    def observe(
        self, observation: ESNObservation, pose_error: np.ndarray, twist_error: np.ndarray,
    ) -> np.ndarray:
        """Return v1 reservoir memory plus the error-aware current feature."""

        normalized = self.normalized_input(observation)
        current = encode_wbc_current_feature(observation, pose_error, twist_error)
        self.reservoir.advance(normalized)
        feature = np.concatenate((current, self.reservoir.state))
        if feature.shape != (self.feature_dimension,) or not np.all(np.isfinite(feature)):
            raise RuntimeError("Fan Ye RL adapter produced an invalid feature")
        return feature.astype(np.float32)

    def observe_multiscale(
        self, observation: ESNObservation, pose_error: np.ndarray, twist_error: np.ndarray,
    ) -> np.ndarray:
        """Return v2 fast/slow Fan Ye memory on the deployable 32-D state."""

        current = encode_wbc_current_feature(observation, pose_error, twist_error)
        states = []
        for reservoir in self.multiscale_reservoirs:
            reservoir.advance(current)
            states.append(reservoir.state)
        feature = np.concatenate((current, *states))
        if feature.shape != (self.multiscale_feature_dimension,) or not np.all(np.isfinite(feature)):
            raise RuntimeError("Fan Ye multiscale adapter produced an invalid feature")
        return feature.astype(np.float32)

    def normalized_input(self, observation: ESNObservation) -> np.ndarray:
        """Return the matched 20-D current input without reservoir memory."""

        raw = encode_student_observation(observation)
        normalized = self.normalizer.transform(raw[None, :])[0]
        if normalized.shape != (20,) or not np.all(np.isfinite(normalized)):
            raise RuntimeError("Fan Ye normalized input adapter produced an invalid feature")
        return normalized.astype(np.float32)
