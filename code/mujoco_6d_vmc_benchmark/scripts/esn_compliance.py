"""Deployable Echo-State Network primitives for WBC-aware compliance.

The ESN is deliberately a small, bounded *student* that modulates the
six-dimensional VMC springs and its recovery drive.  It is not allowed to
command torque directly and it never receives contact/rod/obstacle truth.

Only :mod:`numpy` is required.  This makes the observation and safety contract
unit-testable away from the MuJoCo server, while the eventual rollout adapter
can use exactly the same projection functions in the torque-level simulator.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from stiffness_training_core import (
    DriveResidualActionConfig,
    PRIVILEGED_DIAGNOSTICS,
    StiffnessActionConfig,
    action_to_kappa,
    action_to_recovery_drive,
)


STUDENT_INPUT_FIELDS = ("joint_position_7", "joint_velocity_7", "wbc_task_twist_6")
STUDENT_INPUT_DIMENSION = 20
ACTION_DIMENSION = 7
TEACHER_ONLY_FIELDS = (
    "rod_contact", "rod_force", "rod_penetration", "rod_displacement",
    "rod_command_velocity", "obstacle_geometry_or_pose", "contact_normal",
    "future_collision_phase", "future_release_time", "fixture_id",
)


def _finite_vector(value: np.ndarray | list[float] | tuple[float, ...], size: int, label: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.shape != (size,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{label} must be a finite {size}-vector")
    return array


@dataclass(frozen=True)
class ESNObservation:
    """The complete online student observation at one controller update.

    Values are physical units.  :func:`encode_student_observation` applies
    the fixed scales before they reach the reservoir.
    """

    joint_position: np.ndarray
    joint_velocity: np.ndarray
    wbc_task_twist: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "joint_position", _finite_vector(self.joint_position, 7, "joint_position"))
        object.__setattr__(self, "joint_velocity", _finite_vector(self.joint_velocity, 7, "joint_velocity"))
        object.__setattr__(self, "wbc_task_twist", _finite_vector(self.wbc_task_twist, 6, "wbc_task_twist"))


def encode_student_observation(observation: ESNObservation) -> np.ndarray:
    """Return the normalized 20-D deployable ESN input.

    Joint positions/velocities and the translational/angular WBC twist are
    clipped only after deterministic physical-unit normalization.  No
    end-effector contact proxy, carriage state, target state or force channel
    is smuggled in here.
    """

    scales = np.concatenate((np.full(7, 3.0), np.full(7, 3.0), np.array([0.60] * 3 + [2.0] * 3)))
    encoded = np.concatenate((observation.joint_position, observation.joint_velocity, observation.wbc_task_twist)) / scales
    return np.clip(encoded, -10.0, 10.0)


@dataclass(frozen=True)
class ESNConfig:
    """Fixed reservoir hyperparameters; only the readout is trained."""

    reservoir_size: int = 160
    spectral_radius: float = 0.90
    sparsity: float = 0.12
    input_scale: float = 0.45
    feedback_scale: float = 0.10
    leak_rate: float = 0.35
    seed: int = 20260815
    ridge_lambda: float = 1.0e-4

    def __post_init__(self) -> None:
        if self.reservoir_size < 1 or not 0.0 < self.spectral_radius <= 1.5:
            raise ValueError("reservoir_size must be positive and spectral_radius must be in (0, 1.5]")
        if not 0.0 < self.sparsity <= 1.0 or not 0.0 < self.leak_rate <= 1.0:
            raise ValueError("sparsity and leak_rate must be in (0, 1]")
        if self.input_scale <= 0.0 or self.feedback_scale < 0.0 or self.ridge_lambda < 0.0:
            raise ValueError("ESN scales and ridge_lambda must be non-negative (input_scale positive)")


@dataclass(frozen=True)
class ProjectedComplianceAction:
    """Controller-safe command emitted after the student action projection."""

    raw_action: np.ndarray
    bounded_action: np.ndarray
    kappa: np.ndarray
    recovery_drive_scale: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "raw_action", _finite_vector(self.raw_action, ACTION_DIMENSION, "raw_action"))
        object.__setattr__(self, "bounded_action", _finite_vector(self.bounded_action, ACTION_DIMENSION, "bounded_action"))
        object.__setattr__(self, "kappa", _finite_vector(self.kappa, 6, "kappa"))
        if not np.isfinite(self.recovery_drive_scale) or self.recovery_drive_scale <= 0.0:
            raise ValueError("recovery_drive_scale must be finite and positive")


def project_compliance_action(
    raw_action: np.ndarray | list[float] | tuple[float, ...],
    previous_kappa: np.ndarray | list[float] | tuple[float, ...],
    previous_drive_scale: float,
    *,
    stiffness_config: StiffnessActionConfig = StiffnessActionConfig(),
    drive_config: DriveResidualActionConfig = DriveResidualActionConfig(),
) -> ProjectedComplianceAction:
    """Bound and slew-limit one ESN action before it reaches the VMC layer."""

    raw = _finite_vector(raw_action, ACTION_DIMENSION, "raw_action")
    bounded = np.clip(raw, -1.0, 1.0)
    return ProjectedComplianceAction(
        raw_action=raw,
        bounded_action=bounded,
        kappa=action_to_kappa(bounded[:6], previous_kappa, stiffness_config),
        recovery_drive_scale=action_to_recovery_drive(bounded[6], previous_drive_scale, drive_config),
    )


class ComplianceESN:
    """A resettable ESN student with a ridge-regression linear readout.

    ``step`` is online/deployment-safe: it accepts only :class:`ESNObservation`
    plus the previous bounded action feedback.  Teacher labels enter solely
    through :meth:`fit_readout` during offline training.
    """

    def __init__(self, config: ESNConfig = ESNConfig()) -> None:
        self.config = config
        rng = np.random.default_rng(config.seed)
        recurrent = rng.uniform(-1.0, 1.0, (config.reservoir_size, config.reservoir_size))
        recurrent *= rng.random(recurrent.shape) < config.sparsity
        eigenvalue_radius = float(np.max(np.abs(np.linalg.eigvals(recurrent))))
        # A small sparse random graph can be acyclic (or numerically almost
        # acyclic), giving an unusably tiny spectral radius.  Dividing by that
        # value turns otherwise bounded weights into an unstable amplification.
        # Use a deterministic unit-radius ring in that degenerate case.
        if not np.isfinite(eigenvalue_radius) or eigenvalue_radius < 1.0e-8:
            recurrent = np.roll(np.eye(config.reservoir_size), shift=1, axis=1)
            eigenvalue_radius = 1.0
        self._recurrent = recurrent * (config.spectral_radius / eigenvalue_radius)
        self._input = rng.uniform(-config.input_scale, config.input_scale, (config.reservoir_size, STUDENT_INPUT_DIMENSION))
        self._feedback = rng.uniform(-config.feedback_scale, config.feedback_scale, (config.reservoir_size, ACTION_DIMENSION))
        self._readout = np.zeros((ACTION_DIMENSION, 1 + STUDENT_INPUT_DIMENSION + config.reservoir_size), dtype=float)
        self._state = np.zeros(config.reservoir_size, dtype=float)
        self._previous_action = np.zeros(ACTION_DIMENSION, dtype=float)

    @property
    def readout_feature_dimension(self) -> int:
        return self._readout.shape[1]

    @property
    def state(self) -> np.ndarray:
        return self._state.copy()

    def reset(self) -> None:
        """Clear rollout state and action feedback at an episode boundary."""

        self._state.fill(0.0)
        self._previous_action.fill(0.0)

    def _update(self, encoded_input: np.ndarray, previous_action: np.ndarray) -> np.ndarray:
        proposal = np.tanh(self._input @ encoded_input + self._recurrent @ self._state + self._feedback @ previous_action)
        self._state = (1.0 - self.config.leak_rate) * self._state + self.config.leak_rate * proposal
        if not np.all(np.isfinite(self._state)):
            raise RuntimeError("ESN reservoir state became non-finite")
        return np.concatenate((np.array([1.0]), encoded_input, self._state))

    def step(self, observation: ESNObservation) -> np.ndarray:
        """Advance the reservoir and return seven unprojected readout values."""

        feature = self._update(encode_student_observation(observation), self._previous_action)
        action = self._readout @ feature
        if not np.all(np.isfinite(action)):
            raise RuntimeError("ESN readout produced non-finite action")
        self._previous_action = np.clip(action, -1.0, 1.0)
        return action

    def collect_features(self, observations: list[ESNObservation], *, washout_steps: int) -> np.ndarray:
        """Run one offline trajectory and return readout features after washout."""

        if not 0 <= washout_steps < len(observations):
            raise ValueError("washout_steps must be non-negative and smaller than sequence length")
        self.reset()
        features = []
        for index, observation in enumerate(observations):
            feature = self._update(encode_student_observation(observation), self._previous_action)
            # During teacher-forced collection the feedback remains the prior
            # bounded student action.  It never receives a privileged label.
            self._previous_action = np.clip(self._readout @ feature, -1.0, 1.0)
            if index >= washout_steps:
                features.append(feature)
        return np.asarray(features, dtype=float)

    def fit_readout(self, features: np.ndarray, teacher_actions: np.ndarray) -> None:
        """Fit the offline linear student readout by ridge regression.

        ``teacher_actions`` must be a finite ``N x 7`` bounded target.  It may
        have been generated with privileged simulation diagnostics, but those
        fields are deliberately absent from the deployed ESN interface.
        """

        design = np.asarray(features, dtype=float)
        targets = np.asarray(teacher_actions, dtype=float)
        if design.ndim != 2 or design.shape[1] != self.readout_feature_dimension or not np.all(np.isfinite(design)):
            raise ValueError("features have an invalid shape or non-finite value")
        if targets.shape != (design.shape[0], ACTION_DIMENSION) or not np.all(np.isfinite(targets)):
            raise ValueError("teacher_actions must be a finite N x 7 array")
        if not len(design):
            raise ValueError("at least one training feature is required")
        targets = np.clip(targets, -1.0, 1.0)
        gram = design.T @ design + self.config.ridge_lambda * np.eye(design.shape[1])
        readout = np.linalg.solve(gram, design.T @ targets).T
        if not np.all(np.isfinite(readout)):
            raise RuntimeError("ridge regression produced a non-finite ESN readout")
        self._readout = readout

    def contract(self) -> dict[str, Any]:
        """A serializable audit record stored with every ESN training run."""

        return {
            "student": {
                "input_dimension": STUDENT_INPUT_DIMENSION,
                "input_fields": list(STUDENT_INPUT_FIELDS),
                "input_normalization": {
                    "joint_position_rad": 3.0, "joint_velocity_radps": 3.0,
                    "wbc_task_twist": [0.60, 0.60, 0.60, 2.0, 2.0, 2.0],
                },
                "reservoir_feedback": "previous bounded seven-dimensional student action only",
                "forbidden_privileged_inputs": list(dict.fromkeys((*PRIVILEGED_DIAGNOSTICS, *TEACHER_ONLY_FIELDS))),
            },
            "teacher": {
                "allowed_information": list(TEACHER_ONLY_FIELDS),
                "role": "offline label generation and evaluation only; never an online student input",
            },
            "action": {
                "dimension": ACTION_DIMENSION,
                "channels": ["delta_log_kappa_x", "delta_log_kappa_y", "delta_log_kappa_z", "delta_log_kappa_roll", "delta_log_kappa_pitch", "delta_log_kappa_yaw", "delta_log_recovery_drive"],
                "raw_range_after_projection": [-1.0, 1.0],
                "safety": "positive bounded log-space spring and recovery-drive mapping, action-rate limiting, shared torque feasibility scaling and torque slew limiter; optional frozen energy shield remains downstream",
            },
            "reservoir": asdict(self.config),
        }
