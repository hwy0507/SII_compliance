"""Load a Fan-Ye ESN ridge readout as a bounded Panda VMC policy callback."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from esn_compliance import ESNObservation, ProjectedComplianceAction, project_compliance_action
from fan_ye_esn_design import FanYeAlignedESN, FanYeESNConfig, FanYeInputNormalizer
from stiffness_training_core import DriveResidualActionConfig, StiffnessActionConfig


@dataclass(frozen=True)
class FanYeVMCPolicyConfig:
    """Frozen actuator envelope for the Fan-Ye ESN execution layer."""

    base_kappa: tuple[float, float, float, float, float, float] = (27.579838, 52.550787, 48.699427, 35.859580, 40.719830, 34.766858)
    minimum_kappa: tuple[float, float, float, float, float, float] = (12.0, 16.0, 16.0, 12.0, 12.0, 12.0)
    maximum_kappa: tuple[float, float, float, float, float, float] = (55.0, 70.0, 70.0, 70.0, 70.0, 70.0)
    contact_drive_scale: float = 8.0
    base_recovery_drive_scale: float = 14.0
    minimum_recovery_drive_scale: float = 8.0
    maximum_recovery_drive_scale: float = 20.0
    update_hz: float = 25.0

    def __post_init__(self) -> None:
        if self.contact_drive_scale <= 0.0 or self.update_hz <= 0.0:
            raise ValueError("policy execution scales must be positive")


class FanYeVMCPolicy:
    """A stateful callback accepted by ``run_episode(compliance_policy=...)``."""

    def __init__(self, model_npz: Path, training_summary_json: Path, config: FanYeVMCPolicyConfig = FanYeVMCPolicyConfig()) -> None:
        summary = json.loads(training_summary_json.read_text())
        self.reservoir = FanYeAlignedESN(FanYeESNConfig(**summary["config"]))
        with np.load(model_npz) as archive:
            self.reservoir.set_readout(archive["readout"])
            self.normalizer = FanYeInputNormalizer(archive["input_normalizer_scales"])
        self.config = config
        self.stiffness_config = StiffnessActionConfig(
            base_kappa=config.base_kappa, minimum_kappa=config.minimum_kappa, maximum_kappa=config.maximum_kappa,
            update_hz=config.update_hz,
        )
        self.drive_config = DriveResidualActionConfig(
            base_recovery_drive_scale=config.base_recovery_drive_scale,
            minimum_recovery_drive_scale=config.minimum_recovery_drive_scale,
            maximum_recovery_drive_scale=config.maximum_recovery_drive_scale,
            update_hz=config.update_hz,
        )
        self.reset()

    def reset(self) -> None:
        self.reservoir.reset()
        self._previous_kappa = np.asarray(self.config.base_kappa, dtype=float)
        self._previous_drive = self.config.base_recovery_drive_scale

    def __call__(self, observation: ESNObservation) -> ProjectedComplianceAction:
        encoded = self.normalizer.transform(np.asarray([
            np.concatenate((
                observation.joint_position / 3.0,
                observation.joint_velocity / 3.0,
                observation.wbc_task_twist / np.array([0.60] * 3 + [2.0] * 3),
            ))
        ]))[0]
        raw = self.reservoir.action(encoded)
        projected = project_compliance_action(
            raw, self._previous_kappa, self._previous_drive,
            stiffness_config=self.stiffness_config, drive_config=self.drive_config,
        )
        self._previous_kappa = projected.kappa
        self._previous_drive = projected.recovery_drive_scale
        return projected
