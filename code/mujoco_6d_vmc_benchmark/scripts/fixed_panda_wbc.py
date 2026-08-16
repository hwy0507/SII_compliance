"""Fixed-base Panda whole-body-command adapter for the MuJoCo benchmark.

This module intentionally does *not* import the Fetch/ManiSkill whole-body
stack: that system uses a different robot, state space, and simulator.  It
defines the contract required by the Panda benchmark instead.  A planned SE(3)
task target is converted at each control step to a bounded, redundant-arm
resolved-rate WBC command.  The downstream VMC/ESN layer may comply with that
command but never changes its target-generation policy.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import mujoco
import numpy as np

from run_benchmark import ARM_DOF, body_jacobian, so3_log


@dataclass(frozen=True)
class FixedBasePandaWBCConfig:
    """Gains and bounds for a deterministic fixed-base task-priority WBC."""

    position_feedback_gain: float = 3.0
    orientation_feedback_gain: float = 2.5
    pseudoinverse_damping: float = 0.035
    nullspace_posture_gain: float = 0.20
    max_linear_speed_mps: float = 0.35
    max_angular_speed_radps: float = 1.20
    max_joint_speed_radps: float = 1.25

    def __post_init__(self) -> None:
        values = np.asarray(list(asdict(self).values()), dtype=float)
        if not np.all(np.isfinite(values)) or np.any(values <= 0.0):
            raise ValueError("all fixed-base Panda WBC gains and limits must be finite and positive")


@dataclass(frozen=True)
class WBCCommand:
    """Immutable command crossing from fixed WBC into the compliance layer."""

    target_position_m: np.ndarray
    target_rotation: np.ndarray
    task_twist_world: np.ndarray
    joint_velocity_radps: np.ndarray
    position_error_m: np.ndarray
    orientation_error_rad: np.ndarray


def _clip_norm(vector: np.ndarray, maximum: float) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    return vector if norm <= maximum else vector * (maximum / norm)


class FixedBasePandaWBC:
    """Task-priority, fixed-target generator for Panda's redundant seven-DOF arm.

    At each tick it receives only the preplanned SE(3) target and Panda's
    proprioceptively available state.  It creates the nominal task twist using
    damped resolved-rate IK plus a bounded null-space posture term.  No rod,
    contact, force, obstacle, or future-release information is involved.
    """

    source_name = "fixed_base_panda_resolved_rate_wbc_v1"

    def __init__(
        self, model: mujoco.MjModel, hand_id: int, nominal_posture: np.ndarray,
        config: FixedBasePandaWBCConfig | None = None,
    ) -> None:
        self.model = model
        self.hand_id = int(hand_id)
        self.config = config or FixedBasePandaWBCConfig()
        posture = np.asarray(nominal_posture, dtype=float)
        if posture.shape != (ARM_DOF,) or not np.all(np.isfinite(posture)):
            raise ValueError("nominal_posture must be a finite Panda seven-joint vector")
        self.nominal_posture = posture.copy()

    def command(
        self,
        data: mujoco.MjData,
        target_position_m: np.ndarray,
        target_rotation: np.ndarray,
        feedforward_twist_world: np.ndarray,
        *,
        feedback_scale: float = 1.0,
    ) -> WBCCommand:
        target_position = np.asarray(target_position_m, dtype=float)
        target_rotation = np.asarray(target_rotation, dtype=float)
        feedforward = np.asarray(feedforward_twist_world, dtype=float)
        if target_position.shape != (3,) or target_rotation.shape != (3, 3) or feedforward.shape != (6,):
            raise ValueError("Panda WBC requires target position (3,), rotation (3,3), and twist (6,)")
        if not np.isfinite(feedback_scale) or not 0.0 < feedback_scale <= 1.0:
            raise ValueError("WBC feedback scale must be finite and in (0, 1]")

        current_position = data.xpos[self.hand_id].copy()
        current_rotation = data.xmat[self.hand_id].reshape(3, 3).copy()
        position_error = target_position - current_position
        orientation_error = so3_log(target_rotation @ current_rotation.T)
        desired_twist = feedforward.copy()
        desired_twist[:3] += feedback_scale * self.config.position_feedback_gain * position_error
        desired_twist[3:] += feedback_scale * self.config.orientation_feedback_gain * orientation_error
        desired_twist[:3] = _clip_norm(desired_twist[:3], self.config.max_linear_speed_mps)
        desired_twist[3:] = _clip_norm(desired_twist[3:], self.config.max_angular_speed_radps)

        jacobian = body_jacobian(self.model, data, self.hand_id)
        damping_sq = self.config.pseudoinverse_damping ** 2
        regularized_gram = jacobian @ jacobian.T + damping_sq * np.eye(6)
        damped_pinv = jacobian.T @ np.linalg.solve(regularized_gram, np.eye(6))
        qdot_task = damped_pinv @ desired_twist
        nullspace = np.eye(ARM_DOF) - damped_pinv @ jacobian
        qdot = qdot_task + nullspace @ (self.config.nullspace_posture_gain * (self.nominal_posture - data.qpos[:ARM_DOF]))
        qdot = np.clip(qdot, -self.config.max_joint_speed_radps, self.config.max_joint_speed_radps)
        # ``J qdot`` is what a downstream task-space compliance layer must
        # receive, not the unconstrained desired twist before WBC bounds.
        return WBCCommand(
            target_position_m=target_position.copy(), target_rotation=target_rotation.copy(),
            task_twist_world=jacobian @ qdot, joint_velocity_radps=qdot,
            position_error_m=position_error, orientation_error_rad=orientation_error,
        )
