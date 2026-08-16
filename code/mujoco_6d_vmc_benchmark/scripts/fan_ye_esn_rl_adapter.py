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

``fan_ye_closed_loop_esn`` additionally gives the reservoir, but not the PPO
readout directly, the prior residual command after shared safety filtering.
This lets the fixed memory distinguish a disturbance departure from actuator
settling caused by its own bounded yield request.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from esn_compliance import ESNObservation, encode_student_observation
from fan_ye_esn_design import FanYeAlignedESN, FanYeESNConfig, FanYeInputNormalizer


CURRENT_WBC_FEATURE_DIMENSION = 32
FORECAST_OUTPUT_DIMENSION = 6
FORECAST_HORIZON_S = 0.120
APPLIED_RESIDUAL_CONTEXT_DIMENSION = 7
CLOSED_LOOP_ESN_INPUT_DIMENSION = CURRENT_WBC_FEATURE_DIMENSION + APPLIED_RESIDUAL_CONTEXT_DIMENSION
WBC_POSE_ERROR_SCALE = np.array([0.060, 0.060, 0.060, 0.20, 0.20, 0.20], dtype=float)
WBC_TWIST_ERROR_SCALE = np.array([0.60, 0.60, 0.60, 2.0, 2.0, 2.0], dtype=float)

# Frozen after a 32-D deployment-state-only Fan Ye CR/ESPI screen on the
# isolated post-V4 development train split.  Candidate #116 is the fast
# loading memory; #117 is the slower release/rejoin memory.
MULTISCALE_RESERVOIR_CONFIGS = (
    FanYeESNConfig(
        reservoir_size=64, spectral_radius=0.986655955886451,
        input_scale=0.7963986424712566, time_constant_s=0.04253725603074088,
        connection_probability=0.27912832622475403, bias_scale=0.6112709785768513,
        ridge_lambda=1.1544452061983395e-08, dt_s=0.04, seed=20260933,
        input_dimension=CURRENT_WBC_FEATURE_DIMENSION,
    ),
    FanYeESNConfig(
        reservoir_size=64, spectral_radius=1.8803965096021835,
        input_scale=0.7699460193264828, time_constant_s=0.14001593770536352,
        connection_probability=0.11951281209855406, bias_scale=0.6200204813876405,
        ridge_lambda=0.00013767884053248608, dt_s=0.04, seed=20260934,
        input_dimension=CURRENT_WBC_FEATURE_DIMENSION,
    ),
)

# Closed-loop candidates #107 (fast loading) and #24 (slow recovery) are
# frozen after a 160-candidate CR/ESPI screen on the new post-V4 development
# *train* probe traces.  No PPO return, validation reward, or final holdout is
# involved.  The 39-D robust scales below are part of that frozen design: using
# different online scaling would make the deployed reservoir differ from the
# screened one.
CLOSED_LOOP_RESERVOIR_CONFIGS = (
    FanYeESNConfig(
        reservoir_size=64, spectral_radius=1.724510757157626,
        input_scale=0.9569744552122891, time_constant_s=0.048321880926077046,
        connection_probability=0.1493301790242772, bias_scale=0.8567456405674412,
        ridge_lambda=1.77634882463859e-05, dt_s=0.04, seed=20261068,
        input_dimension=CLOSED_LOOP_ESN_INPUT_DIMENSION,
    ),
    FanYeESNConfig(
        reservoir_size=64, spectral_radius=0.6482510374809771,
        input_scale=1.5687862441893154, time_constant_s=0.12635851180063093,
        connection_probability=0.03133930952221364, bias_scale=0.29275318007721074,
        ridge_lambda=1.1436672886070185e-07, dt_s=0.04, seed=20260985,
        input_dimension=CLOSED_LOOP_ESN_INPUT_DIMENSION,
    ),
)
CLOSED_LOOP_INPUT_NORMALIZER = FanYeInputNormalizer(np.array([
    0.001, 0.0019346113549545407, 0.0010674077784642577, 0.5395164489746094,
    0.001, 0.5253284573554993, 0.26176950335502625, 0.0011447283904999495,
    0.0042251660488545895, 0.0012022806331515312, 0.015776079148054123, 0.001,
    0.0014003021642565727, 0.001, 0.028656626120209694, 0.02179226651787758,
    0.16923697292804718, 0.001580705866217613, 0.10238812118768692, 0.007849977351725101,
    0.04264411702752113, 0.04767336696386337, 0.27775225043296814, 0.00446879118680954,
    0.24344322085380554, 0.021393440663814545, 0.014425558969378471, 0.014958151616156101,
    0.1096409484744072, 0.001427232753485441, 0.059435877948999405, 0.004488341975957155,
    0.550000011920929, 0.010268226265907288, 0.01105387881398201, 0.06853578239679337,
    0.001, 0.021286968141794205, 0.0018348857993260026,
], dtype=float))


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


def encode_applied_residual_context(
    wbc_scale: float, cartesian_yield_twist: np.ndarray, *,
    minimum_wbc_scale: float = 0.20, maximum_linear_yield_mps: float = 0.16,
    maximum_angular_yield_radps: float = 0.60,
) -> np.ndarray:
    """Normalize the last actual safety-filtered residual command.

    These values are available causally at every decision point.  They exclude
    raw proposed actions, contacts, forces, rod state, obstacle geometry, and
    any release/phase label.
    """

    yield_twist = np.asarray(cartesian_yield_twist, dtype=float)
    if (
        not np.isfinite(wbc_scale) or yield_twist.shape != (6,)
        or not np.all(np.isfinite(yield_twist)) or not 0.0 < minimum_wbc_scale < 1.0
        or maximum_linear_yield_mps <= 0.0 or maximum_angular_yield_radps <= 0.0
    ):
        raise ValueError("applied residual context must be finite and safety-bounded")
    slowdown = (1.0 - float(wbc_scale)) / (1.0 - minimum_wbc_scale)
    scales = np.array([
        maximum_linear_yield_mps, maximum_linear_yield_mps, maximum_linear_yield_mps,
        maximum_angular_yield_radps, maximum_angular_yield_radps, maximum_angular_yield_radps,
    ])
    return np.clip(np.concatenate(([slowdown], yield_twist / scales)), -1.0, 1.0).astype(np.float32)


def encode_kinematic_pose_forecast(pose_error: np.ndarray, twist_error: np.ndarray) -> np.ndarray:
    """Causal 120-ms *change* in pose error for the MLP control.

    This is a deliberately simple matched baseline for the ESN forecast.  Both
    methods receive the same current WBC state and six additional forecast
    channels; only the method used to predict their future error differs.
    """

    pose = np.asarray(pose_error, dtype=float)
    twist = np.asarray(twist_error, dtype=float)
    if pose.shape != (6,) or twist.shape != (6,) or not np.all(np.isfinite(pose)) or not np.all(np.isfinite(twist)):
        raise ValueError("kinematic forecast requires finite six-dimensional WBC errors")
    # The current pose error is already present in the 32-D state.  Supplying
    # its future absolute value repeats that state and obscures whether the
    # error is expected to grow or recover.  The matched baseline therefore
    # receives only the constant-twist prediction of its change.
    del pose
    return np.clip(FORECAST_HORIZON_S * twist / WBC_POSE_ERROR_SCALE, -10.0, 10.0).astype(np.float32)


class FixedErrorForecaster:
    """Fixed multiscale Fan Ye memory with a ridge future-error readout.

    The reservoirs stay frozen.  Only ``readout`` is fitted from development
    train trajectories, using current/historical deployable WBC state to
    predict the *change* in pose tracking error 120 ms ahead.  No control reward or
    privileged collision quantity is a predictor input.
    """

    def __init__(self, readout: np.ndarray | None = None) -> None:
        self.reservoirs = tuple(FanYeAlignedESN(config) for config in MULTISCALE_RESERVOIR_CONFIGS)
        self.design_dimension = 1 + CURRENT_WBC_FEATURE_DIMENSION + sum(
            reservoir.config.reservoir_size for reservoir in self.reservoirs
        )
        self.readout = np.zeros((FORECAST_OUTPUT_DIMENSION, self.design_dimension), dtype=float)
        if readout is not None:
            matrix = np.asarray(readout, dtype=float)
            if matrix.shape != self.readout.shape or not np.all(np.isfinite(matrix)):
                raise ValueError("forecast readout has invalid shape or non-finite values")
            self.readout = matrix.copy()
        self.reset()

    @classmethod
    def from_npz(cls, path: Path) -> "FixedErrorForecaster":
        with np.load(path) as archive:
            horizon = float(archive["forecast_horizon_s"])
            if not np.isclose(horizon, FORECAST_HORIZON_S):
                raise ValueError("forecast model horizon does not match the controller contract")
            return cls(archive["forecast_readout"])

    def reset(self) -> None:
        for reservoir in self.reservoirs:
            reservoir.reset()

    def advance(self, current_feature: np.ndarray) -> np.ndarray:
        current = np.asarray(current_feature, dtype=float)
        if current.shape != (CURRENT_WBC_FEATURE_DIMENSION,) or not np.all(np.isfinite(current)):
            raise ValueError("forecaster needs a finite current 32-D WBC feature")
        states = []
        for reservoir in self.reservoirs:
            reservoir.advance(current)
            states.append(reservoir.state)
        return np.concatenate((np.array([1.0]), current, *states))

    def forecast(self, current_feature: np.ndarray) -> np.ndarray:
        prediction = self.readout @ self.advance(current_feature)
        if not np.all(np.isfinite(prediction)):
            raise RuntimeError("future-error forecast became non-finite")
        return np.clip(prediction, -10.0, 10.0).astype(np.float32)


class FanYeESNRLObservationAdapter:
    """Stateful, resettable current-state and multi-timescale ESN map."""

    student_input_fields = ("joint_position_7", "joint_velocity_7", "wbc_task_twist_6", "wbc_pose_error_6", "wbc_twist_error_6")
    excluded_fields = ("rod_contact", "rod_force", "rod_penetration", "rod_state", "obstacle_pose_or_geometry", "future_release", "fixture_id", "recovery_gate")

    def __init__(self, model_npz: Path, training_summary_json: Path, forecast_model_npz: Path | None = None) -> None:
        summary = json.loads(training_summary_json.read_text())
        self.reservoir = FanYeAlignedESN(FanYeESNConfig(**summary["config"]))
        if self.reservoir.config.input_dimension != 20:
            raise ValueError("the frozen v1 Fan Ye reservoir must use the legacy 20-D input")
        with np.load(model_npz) as archive:
            self.normalizer = FanYeInputNormalizer(archive["input_normalizer_scales"])
        # Fixed, causally distinct reservoirs.  The fast reservoir resolves the
        # loading transient while the slow one preserves release/rejoin context.
        self.multiscale_reservoirs = tuple(FanYeAlignedESN(config) for config in MULTISCALE_RESERVOIR_CONFIGS)
        self.closed_loop_reservoirs = tuple(FanYeAlignedESN(config) for config in CLOSED_LOOP_RESERVOIR_CONFIGS)
        self.error_forecaster = None if forecast_model_npz is None else FixedErrorForecaster.from_npz(forecast_model_npz)
        self.phase_memory_hold = 0.0
        self.feature_dimension = CURRENT_WBC_FEATURE_DIMENSION + self.reservoir.config.reservoir_size
        self.multiscale_feature_dimension = CURRENT_WBC_FEATURE_DIMENSION + sum(
            item.config.reservoir_size for item in self.multiscale_reservoirs
        )
        self.closed_loop_feature_dimension = CURRENT_WBC_FEATURE_DIMENSION + sum(
            item.config.reservoir_size for item in self.closed_loop_reservoirs
        )
        self.reset()

    def reset(self) -> None:
        self.reservoir.reset()
        for reservoir in self.multiscale_reservoirs:
            reservoir.reset()
        for reservoir in self.closed_loop_reservoirs:
            reservoir.reset()
        if self.error_forecaster is not None:
            self.error_forecaster.reset()
        self.phase_memory_hold = 0.0

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

    def observe_phase_memory(
        self, observation: ESNObservation, pose_error: np.ndarray, twist_error: np.ndarray,
    ) -> np.ndarray:
        """Update a causal fast/slow disagreement memory and return the state."""

        feature = self.observe_multiscale(observation, pose_error, twist_error)
        fast, slow = self.multiscale_reservoirs
        fast_state = np.asarray(fast.state, dtype=float)
        slow_state = np.asarray(slow.state, dtype=float)
        fast_norm = float(np.linalg.norm(fast_state))
        slow_norm = float(np.linalg.norm(slow_state))
        if fast_norm <= 1.0e-9 or slow_norm <= 1.0e-9:
            disagreement = 0.0
        else:
            cosine = float(np.dot(fast_state, slow_state) / (fast_norm * slow_norm))
            disagreement = float(np.clip(0.5 * (1.0 - cosine), 0.0, 1.0))
        self.phase_memory_hold = max(disagreement, 0.92 * self.phase_memory_hold)
        return feature

    def phase_memory_score(self) -> float:
        """Return the bounded causal fast/slow disagreement memory."""

        return float(np.clip(self.phase_memory_hold, 0.0, 1.0))

    def observe_closed_loop(
        self, observation: ESNObservation, pose_error: np.ndarray, twist_error: np.ndarray,
        applied_residual_context: np.ndarray,
    ) -> np.ndarray:
        """Return action-aware fast/slow memory plus current deployable state.

        The 7-D context is prior *physical* residual output from the common
        safety filter and only affects the reservoir recurrence.
        """

        current = encode_wbc_current_feature(observation, pose_error, twist_error)
        context = np.asarray(applied_residual_context, dtype=float)
        if context.shape != (APPLIED_RESIDUAL_CONTEXT_DIMENSION,) or not np.all(np.isfinite(context)):
            raise ValueError("closed-loop ESN context must be a finite normalized seven-vector")
        reservoir_input = np.concatenate((current, np.clip(context, -1.0, 1.0)))
        normalized_input = CLOSED_LOOP_INPUT_NORMALIZER.transform(reservoir_input[None, :])[0]
        states = []
        for reservoir in self.closed_loop_reservoirs:
            reservoir.advance(normalized_input)
            states.append(reservoir.state)
        feature = np.concatenate((current, *states))
        if feature.shape != (self.closed_loop_feature_dimension,) or not np.all(np.isfinite(feature)):
            raise RuntimeError("Fan Ye closed-loop adapter produced an invalid feature")
        return feature.astype(np.float32)

    def observe_forecast(
        self, observation: ESNObservation, pose_error: np.ndarray, twist_error: np.ndarray,
    ) -> np.ndarray:
        """Return current 32-D state and a causal ESN 120-ms error forecast.

        Unlike the rejected action-context ablation, the predicted value is a
        dynamic state estimate, not a residual-action history.
        """

        if self.error_forecaster is None:
            raise RuntimeError("fan_ye_forecast_esn requires a fitted forecast model")
        current = encode_wbc_current_feature(observation, pose_error, twist_error)
        forecast = self.error_forecaster.forecast(current)
        feature = np.concatenate((current, forecast))
        if feature.shape != (CURRENT_WBC_FEATURE_DIMENSION + FORECAST_OUTPUT_DIMENSION,) or not np.all(np.isfinite(feature)):
            raise RuntimeError("Fan Ye forecast adapter produced an invalid feature")
        return feature.astype(np.float32)

    def normalized_input(self, observation: ESNObservation) -> np.ndarray:
        """Return the matched 20-D current input without reservoir memory."""

        raw = encode_student_observation(observation)
        normalized = self.normalizer.transform(raw[None, :])[0]
        if normalized.shape != (20,) or not np.all(np.isfinite(normalized)):
            raise RuntimeError("Fan Ye normalized input adapter produced an invalid feature")
        return normalized.astype(np.float32)
