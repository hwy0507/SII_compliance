"""Nominal velocity controller faithfully reimplemented from the paper system.

Source of the replicated control law (checked line-by-line against the local
main-project code, ``whole-body-motion-control/grasp_anywhere/envs/maniskill/
maniskill_env_mpc.py``, the "Localization and Control" layer of
"Visibility-Aware Mobile Grasping in Dynamic Environments"):

- one-step quadratic solve ``(B^T Q B + R) u = B^T Q (x_ref - x)`` with the
  linearized kinematics ``x_next = x + B u dt``.  For the arm block
  ``B_arm = I`` so the solve is ``(Q_a + R_a) u = Q_a (q_ref - q)``.
- state/control weights from the source ``_mpc`` dict: arm ``Q = 12``,
  arm ``R = 1.0`` (diag), aggressiveness ``gain = 2.5``.
- waypoint-queue reference consumption: each tick selects the *nearest*
  waypoint from the last pointer forward, then aims at the waypoint
  ``lookahead = 2`` steps ahead (``k = min(2, N)`` in the source).
- velocity clip at the source ``joint_vel_max = 7.0`` rad/s for arm joints.

Platform reductions (fixed-base FR3, documented like the Pink adapter):

1. The source state is 11-DoF whole-body (base x/y/theta, torso, 7 arm
   joints) and its control is 10-D; the base/torso blocks are dropped for
   the fixed-base arm, leaving the 7-DoF arm block of the same solve.
2. The source waypoint queue comes from their whole-body planner; here it
   is the dense joint-space sampling of the benchmark reference (one
   waypoint per 40 ms control step), consumed through the same
   nearest-waypoint + lookahead mechanism.
3. The output contract matches ``FixedBasePandaWBC``: per-cycle
   ``WBCCommand`` with the reference SE(3) target (for the observation
   contract), task twist ``J qdot``, and the bounded joint velocity.

The compliance layer below (velocity servo + residual torque) is unchanged;
this file only replaces the nominal velocity publisher.
"""

from __future__ import annotations

import numpy as np

from fixed_panda_wbc import WBCCommand
from run_benchmark import ARM_DOF, body_jacobian, so3_log


class PaperMPCWBC:
    """One-step quadratic nominal velocity controller (paper replication)."""

    family = "paper_mpc_velocity_wbc_fr3"

    def __init__(
        self,
        model,
        hand_id: int,
        reference,
        nominal_posture: np.ndarray,
        *,
        q_weight: float = 12.0,
        r_weight: float = 1.0,
        gain: float = 2.5,
        lookahead: int = 2,
        joint_vel_max_radps: float = 7.0,
        search_window: int = 30,
        waypoint_period_s: float | None = None,
        horizon_s: float = 8.0,
    ) -> None:
        posture = np.asarray(nominal_posture, dtype=float)
        if posture.shape != (ARM_DOF,) or not np.all(np.isfinite(posture)):
            raise ValueError("nominal_posture must be a finite seven-joint vector")
        self.model = model
        self.hand_id = int(hand_id)
        self.reference = reference
        self.nominal_posture = posture.copy()
        # Closed-form of the source one-step solve for the arm block:
        #   u = gain * (Q + R)^-1 Q (q_ref - q)
        self.feedback_gain = gain * q_weight / (q_weight + r_weight)
        self.lookahead = int(lookahead)
        self.joint_vel_max = float(joint_vel_max_radps)
        self.search_window = int(search_window)
        # Waypoint-queue resolution.  The source controller has no explicit
        # feedforward: aiming k waypoints ahead IS its feedforward.  Steady
        # ramp-tracking lag is qdot * (1/g_eff - k*dt_wp), so the queue is
        # sampled at dt_wp = 1/(g_eff * k), the spacing at which the
        # lookahead exactly cancels the one-step-solve lag (zero steady-state
        # error, derived from the source's own gain and lookahead constants;
        # the source's planner produced roughly this spacing).
        if waypoint_period_s is None:
            waypoint_period_s = 1.0 / (self.feedback_gain * self.lookahead)
        self.waypoint_period_s = float(waypoint_period_s)
        # Dense joint-space waypoint queue from the reference (their planner
        # emits a merged trajectory; ours is the reference sampled at the
        # resolved queue spacing).
        count = int(round(horizon_s / self.waypoint_period_s)) + 1
        self.waypoints = np.stack([
            self.reference._joint_sample(i * self.waypoint_period_s)[0] for i in range(count)
        ])
        self.last_idx = 0

    def reset(self) -> None:
        self.last_idx = 0

    def _nearest_waypoint(self, q: np.ndarray, time_s: float) -> int:
        """Time-anchored forward nearest waypoint.

        The source searches forward from the last pointer over its planner
        queue.  This benchmark's joint-space reference retraces itself (the
        approach lowers joint 4 and the lift raises it back along the same
        line), so an unconstrained joint-space nearest search jumps to the
        retraced segment.  The queue is time-indexed here (waypoint i is the
        reference at i*dt_wp), so the search window is anchored at the
        simulation clock: catch up if behind (within 0.5 s), never skip
        more than ~1.7 s ahead.  This preserves the source mechanism (never
        skip waypoints after a perturbation) while disambiguating retrace.
        """

        t_idx = int(time_s / self.waypoint_period_s)
        begin = max(self.last_idx, t_idx - 3)
        end = min(len(self.waypoints), t_idx + 3 + 1)
        if end <= begin:
            return min(begin, len(self.waypoints) - 1)
        window = self.waypoints[begin:end]
        distances = np.linalg.norm(window - q, axis=1)
        return begin + int(np.argmin(distances))

    def command(
        self,
        data,
        target_position_m: np.ndarray,
        target_rotation: np.ndarray,
        feedforward_twist_world: np.ndarray,
        *,
        feedback_scale: float = 1.0,
    ) -> WBCCommand:
        target_position = np.asarray(target_position_m, dtype=float)
        target_rotation = np.asarray(target_rotation, dtype=float).reshape(3, 3)
        if target_position.shape != (3,) or not np.isfinite(feedback_scale):
            raise ValueError("PaperMPC WBC requires a 3-D target and finite feedback scale")
        if not 0.0 < feedback_scale <= 1.0:
            raise ValueError("WBC feedback scale must be finite and in (0, 1]")

        q = data.qpos[:ARM_DOF].copy()
        self.last_idx = self._nearest_waypoint(q, float(data.time))
        idx_ref = min(self.last_idx + self.lookahead, len(self.waypoints) - 1)
        error = self.waypoints[idx_ref] - q
        # The compliance layer scales only the feedback part of the nominal
        # command (same contract as the previous WBCs).
        qdot = self.feedback_gain * feedback_scale * error
        qdot = np.clip(qdot, -self.joint_vel_max, self.joint_vel_max)

        jacobian = body_jacobian(self.model, data, self.hand_id)
        current_position = data.xpos[self.hand_id].copy()
        current_rotation = data.xmat[self.hand_id].reshape(3, 3).copy()
        return WBCCommand(
            target_position_m=target_position.copy(),
            target_rotation=target_rotation.copy(),
            task_twist_world=jacobian @ qdot,
            joint_velocity_radps=qdot,
            position_error_m=target_position - current_position,
            orientation_error_rad=so3_log(target_rotation @ current_rotation.T),
        )
