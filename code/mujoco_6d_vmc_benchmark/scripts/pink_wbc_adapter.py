"""FR3 platform adapter for the vendored Autolife Pink differential-IK WBC.

The vendored ``vendor_autolife/autolife_planning`` package (upstream:
AdaCompNUS/Autolife-Planning, wheel 0.3.4 — the WBC/IK stack behind
AdaCompNUS/Prepose-Sampler) is used **unmodified**.  Every FR3-specific
adaptation lives in this file:

Platform adaptations (documented per the vendor NOTICE):

1. ``ChainConfig`` points at the official Franka FR3 URDF (arm-only,
   ``fr3_link0`` -> ``fr3_link8``).  Autolife-specific URDF/frames are not
   used.
2. Frame offset: the benchmark scene grafts the Panda Hand on ``fr3_link8``
   with a constant Rz(-45 deg) rotation, so hand-frame targets from the
   benchmark reference are converted to ``fr3_link8`` targets by a constant
   rotation before IK (positions coincide: the hand origin == link8 origin).
3. WBC semantics: Autolife uses the solver as a batched IK; here it runs
   online, once per 40 ms control step, seeded at the measured q, which makes
   the differential-IK solution a velocity-level WBC command
   (``qdot_WBC = (q_ik - q) / dt``).  Autolife-only tasks (head-camera
   stabilization, CoM stability for the legged robot, coupled knee-ankle
   joints) are disabled: fixed-base arm.
4. Feedforward: Pink's FrameTask has no twist feedforward, so the adapter
   embeds it by targeting a short lookahead pose (reference + twist*dt_ff),
   matching the feedforward+feedback structure of the previous
   ``FixedBasePandaWBC`` contract.
5. Output contract identical to ``FixedBasePandaWBC``: per-cycle
   ``WBCCommand`` with hand-frame target pose, task twist (J qdot), and
   bounded joint velocity.  Joint-speed cap and the MuJoCo hand Jacobian are
   taken from the benchmark model, exactly as the previous WBC did.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from fixed_panda_wbc import WBCCommand
from run_benchmark import ARM_DOF, body_jacobian, so3_log

_VENDOR = Path(__file__).resolve().parent / "vendor_autolife"
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

from autolife_planning.kinematics.pink_ik_solver import PinkIKSolver  # noqa: E402
from autolife_planning.types.geometry import SE3Pose  # noqa: E402
from autolife_planning.types.ik import PinkIKConfig  # noqa: E402
from autolife_planning.types.robot import ChainConfig  # noqa: E402

# Constant hand->flange rotation: the Panda Hand is grafted on fr3_link8 with
# quat = Rz(-45 deg); a hand-frame orientation R_h corresponds to the flange
# orientation R_f = R_h @ Rz(+45 deg).
_R_HAND_TO_FLANGE = Rotation.from_euler("z", np.pi / 4.0).as_matrix()


class PinkWBCAdapter:
    """Velocity-level whole-body command from the vendored Pink IK solver."""

    family = "autolife_pink_ik_wbc_fr3"

    def __init__(
        self,
        model,
        hand_id: int,
        nominal_posture: np.ndarray,
        urdf_path: str | Path,
        *,
        max_iterations: int = 1,
        integration_dt: float = 0.04,
        lookahead_s: float = 0.08,
        max_joint_speed_radps: float = 1.25,
        position_cost: float = 1.0,
        orientation_cost: float = 1.0,
        posture_cost: float = 1.0e-2,
        lm_damping: float = 1.0e-3,
        solver: str = "osqp",
    ) -> None:
        posture = np.asarray(nominal_posture, dtype=float)
        if posture.shape != (ARM_DOF,) or not np.all(np.isfinite(posture)):
            raise ValueError("nominal_posture must be a finite seven-joint vector")
        self.model = model
        self.hand_id = int(hand_id)
        self.nominal_posture = posture.copy()
        self.lookahead_s = float(lookahead_s)
        self.max_joint_speed = float(max_joint_speed_radps)
        chain = ChainConfig(
            base_link="fr3_link0",
            ee_link="fr3_link8",
            num_joints=ARM_DOF,
            urdf_path=str(urdf_path),
        )
        self.config = PinkIKConfig(
            dt=integration_dt,
            max_iterations=int(max_iterations),
            convergence_thresh=1.0e-4,
            orientation_thresh=1.0e-3,
            position_cost=position_cost,
            orientation_cost=orientation_cost,
            posture_cost=posture_cost,
            lm_damping=lm_damping,
            com_cost=0.0,          # fixed-base arm: no tipping task
            camera_frame=None,     # Autolife head-camera task: N/A on FR3
            camera_cost=0.0,
            self_collision=False,  # no collision context wired on FR3
            solver=solver,
        )
        self.solver = PinkIKSolver(chain, config=self.config)

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
        hand_rotation = np.asarray(target_rotation, dtype=float).reshape(3, 3)
        feedforward = np.asarray(feedforward_twist_world, dtype=float)
        if target_position.shape != (3,) or feedforward.shape != (6,):
            raise ValueError("Pink WBC adapter requires (3,) target and (6,) twist")

        # Lookahead target embeds the feedforward twist (adaptation 4).
        v_ff, w_ff = feedforward[:3], feedforward[3:]
        position_la = target_position + v_ff * self.lookahead_s
        rotation_la = Rotation.from_rotvec(w_ff * self.lookahead_s).as_matrix() @ hand_rotation
        # Hand-frame target -> flange (fr3_link8) target (adaptation 2).
        flange_rotation = rotation_la @ _R_HAND_TO_FLANGE

        q_seed = data.qpos[:ARM_DOF].copy()
        result = self.solver.solve_constrained(
            SE3Pose(position=position_la, rotation=flange_rotation),
            seed=q_seed,
            config=self.config,
        )
        q_next = np.asarray(result.joint_positions, dtype=float)
        dt_effective = self.config.dt * max(1, self.config.max_iterations)
        qdot = np.clip((q_next - q_seed) / dt_effective, -self.max_joint_speed, self.max_joint_speed)

        jacobian = body_jacobian(self.model, data, self.hand_id)
        current_position = data.xpos[self.hand_id].copy()
        current_rotation = data.xmat[self.hand_id].reshape(3, 3).copy()
        position_error = target_position - current_position
        orientation_error = so3_log(hand_rotation @ current_rotation.T)
        return WBCCommand(
            target_position_m=target_position.copy(),
            target_rotation=hand_rotation.copy(),
            task_twist_world=jacobian @ qdot,
            joint_velocity_radps=qdot,
            position_error_m=position_error,
            orientation_error_rad=orientation_error,
        )
