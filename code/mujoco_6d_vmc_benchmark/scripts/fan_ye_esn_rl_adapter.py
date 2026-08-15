"""Deployable Fan Ye state adapter for a WBC-aware actor.

The adapter deliberately exposes no collision diagnostics.  It turns the same
20-D observation used by the frozen ESN policy into either a matched 20-D
current-state feature for the MLP baseline or that input concatenated with the
fixed 64-D Fan Ye reservoir state for the ESN actor.  The actor's downstream
action space is defined by its controller and is not coupled to this adapter.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from esn_compliance import ESNObservation, encode_student_observation
from fan_ye_esn_design import FanYeAlignedESN, FanYeESNConfig, FanYeInputNormalizer


class FanYeESNRLObservationAdapter:
    """Stateful, resettable 20-D WBC input to fixed-reservoir actor feature map."""

    student_input_fields = ("joint_position_7", "joint_velocity_7", "wbc_task_twist_6")
    excluded_fields = ("rod_contact", "rod_force", "rod_penetration", "rod_state", "obstacle_pose_or_geometry", "future_release", "fixture_id", "recovery_gate")

    def __init__(self, model_npz: Path, training_summary_json: Path) -> None:
        summary = json.loads(training_summary_json.read_text())
        self.reservoir = FanYeAlignedESN(FanYeESNConfig(**summary["config"]))
        with np.load(model_npz) as archive:
            self.normalizer = FanYeInputNormalizer(archive["input_normalizer_scales"])
        self.feature_dimension = 20 + self.reservoir.config.reservoir_size
        self.reset()

    def reset(self) -> None:
        self.reservoir.reset()

    def observe(self, observation: ESNObservation) -> np.ndarray:
        normalized = self.normalized_input(observation)
        self.reservoir.advance(normalized)
        feature = np.concatenate((normalized, self.reservoir.state))
        if feature.shape != (self.feature_dimension,) or not np.all(np.isfinite(feature)):
            raise RuntimeError("Fan Ye RL adapter produced an invalid feature")
        return feature.astype(np.float32)

    def normalized_input(self, observation: ESNObservation) -> np.ndarray:
        """Return the matched 20-D current input without reservoir memory."""

        raw = encode_student_observation(observation)
        normalized = self.normalizer.transform(raw[None, :])[0]
        if normalized.shape != (20,) or not np.all(np.isfinite(normalized)):
            raise RuntimeError("Fan Ye normalized input adapter produced an invalid feature")
        return normalized.astype(np.float32)
