"""WBC adapter for executing a FLASK joint trajectory on fixed-base FR3.

The planner stays in flat joint space while this adapter exposes the same
``WBCCommand`` contract as ``FixedBasePandaWBC``.  It combines the planned
joint velocity with bounded joint feedback, then reports the corresponding
end-effector pose and spatial twist to the existing compliance layer.
"""

from __future__ import annotations

import numpy as np

from fixed_panda_wbc import WBCCommand
from run_benchmark import ARM_DOF, body_jacobian, so3_log


class FlaskTrajectoryWBC:
    """Track a :class:`FlaskTrajectory` through the existing WBC boundary."""

    source_name = "flask_joint_trajectory_wbc_v1"

    def __init__(self, model, hand_id: int, nominal_posture: np.ndarray, *, feedback_gain: float = 2.5, max_joint_speed_radps: float = 1.25):
        posture = np.asarray(nominal_posture, dtype=float)
        if posture.shape != (ARM_DOF,) or not np.all(np.isfinite(posture)):
            raise ValueError("nominal_posture must be a finite seven-joint vector")
        if not np.isfinite(feedback_gain) or feedback_gain <= 0.0 or not np.isfinite(max_joint_speed_radps) or max_joint_speed_radps <= 0.0:
            raise ValueError("feedback gain and joint-speed limit must be positive")
        self.model = model
        self.hand_id = int(hand_id)
        self.nominal_posture = posture.copy()
        self.feedback_gain = float(feedback_gain)
        self.max_joint_speed = float(max_joint_speed_radps)
        self._reference_data = None

    def command(self, data, trajectory, *, time_s: float | None = None, feedback_scale: float = 1.0) -> WBCCommand:
        if not np.isfinite(feedback_scale) or not 0.0 < feedback_scale <= 1.0:
            raise ValueError("feedback_scale must be finite and in (0, 1]")
        clock = float(data.time if time_s is None else time_s)
        q_ref, qdot_ref, _ = trajectory.sample(clock)
        q = np.asarray(data.qpos[:ARM_DOF], dtype=float)
        qdot = qdot_ref + feedback_scale * self.feedback_gain * (q_ref - q)
        qdot = np.clip(qdot, -self.max_joint_speed, self.max_joint_speed)

        # Evaluate FK at the reference configuration without disturbing the
        # live simulation state.  The target is supplied for telemetry and for
        # the existing Cartesian compliance layer; the commanded twist is the
        # physically consistent J(q) qdot.
        if self._reference_data is None:
            import mujoco
            self._reference_data = mujoco.MjData(self.model)
        self._reference_data.qpos[:] = data.qpos
        self._reference_data.qpos[:ARM_DOF] = q_ref
        self._reference_data.qvel[:] = 0.0
        import mujoco
        mujoco.mj_forward(self.model, self._reference_data)
        target_position = self._reference_data.xpos[self.hand_id].copy()
        target_rotation = self._reference_data.xmat[self.hand_id].reshape(3, 3).copy()
        jacobian = body_jacobian(self.model, data, self.hand_id)
        current_position = data.xpos[self.hand_id].copy()
        current_rotation = data.xmat[self.hand_id].reshape(3, 3).copy()
        return WBCCommand(
            target_position_m=target_position,
            target_rotation=target_rotation,
            task_twist_world=jacobian @ qdot,
            joint_velocity_radps=qdot,
            position_error_m=target_position - current_position,
            orientation_error_rad=so3_log(target_rotation @ current_rotation.T),
        )
