#!/usr/bin/env python3
"""Render a real thick-table corner: horizontal top + vertical apron."""
from __future__ import annotations
import argparse, json, os, sys, hashlib
from pathlib import Path
import imageio.v3 as iio
import mujoco, numpy as np
from PIL import Image, ImageDraw, ImageFont

# These are the audited edge-aligned dimensions from extraction_experiment.
os.environ.update({
    "EXTRACTION_TABLE": "1", "THICK_TABLE_SCENE": "1",
    "EXT_TABLE_X": "0.93", "EXT_TABLE_Y": "0.0", "EXT_TABLE_Z": "0.66",
    # The side is directly under the tabletop's left edge.  The apron face
    # toward the robot is the table's outer edge:
    # x_left(side) = 0.750 - 0.040 = 0.710
    #              = 0.930 - 0.220 = x_left(tabletop).
    # Its thickness extends inward (+x), never toward the robot, so the two
    # boards meet without a seam or a protruding strip on the robot side.
    "EXT_TABLE_SIDE_X": "0.750", "EXT_TABLE_SIDE_Y": "0.0",
    # The apron hangs below the tabletop: its top face meets the tabletop
    # underside (0.66 - 0.035 = 0.625), never the tabletop upper surface.
    "EXT_TABLE_SIDE_Z": "0.573", "EXT_TABLE_SIDE_HY": "0.24",
    "EXT_TABLE_SIDE_HZ": "0.06", "EXT_TABLE_SIDE_HX": "0.04",
    "EXT_TABLE_SIDE_TILT_DEG": "0.0",
})
_table_shift = float(os.environ.get('TABLE_X_SHIFT_M', '0.0'))
if _table_shift:
    os.environ['EXT_TABLE_X'] = f'{0.93 + _table_shift:.6f}'
    os.environ['EXT_TABLE_SIDE_X'] = f'{0.750 + _table_shift:.6f}'
sys.path.insert(0, str(Path(__file__).resolve().parent))
from direct_esn_compliance import (  # noqa: E402
    DirectESNController, MultiHeadDirectESNController,
    PrivilegedTeacherConfig, privileged_teacher_action,
)
from mlp_compliance_baseline import MLPComplianceController  # noqa: E402
from vmc_compliance_baseline import SpringCarriageConfig, SpringCarriageVMC, VMCComplianceAdapter  # noqa: E402
from wbc_velocity_residual_core import VelocityResidualSafetyConfig  # noqa: E402
from audited_velocity_env import PandaWBCVelocityResidualEnv, VelocityResidualFixture  # noqa: E402
from current_student_policy_20260921 import load_current  # noqa: E402
from run_benchmark import body_jacobian  # noqa: E402
from haptic_vmc_teacher_20260916 import equivalent_tool_wrench  # noqa: E402

class _CurrentPolicyAdapter:
    def __init__(self, policy, env): self.policy,self.env=policy,env
    def reset(self): self.policy.reset()
    def act(self, joint_position, joint_velocity, nominal_twist, **kw):
        d=self.env.diagnostics(); q=np.asarray(joint_position);dq=np.asarray(joint_velocity)
        pose=np.asarray(kw.get('pose_error',d['wbc_pose_error']));twerr=np.asarray(kw.get('twist_error',d['wbc_twist_error']))
        loads=np.asarray(d['joint_torque_estimate']); wrench=equivalent_tool_wrench(body_jacobian(self.env.model,self.env.data,self.env._hand_id),loads)[:3]
        path=np.asarray(nominal_twist[:3]); path=path/max(np.linalg.norm(path),1e-9)
        obs=np.r_[q,dq,np.asarray(nominal_twist),pose,twerr,loads,wrench,path]
        action=self.policy.act(obs)
        class Result: pass
        result=Result();result.bounded_filter_action=np.asarray(action,dtype=float);return result

def _sha256_file(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda: f.read(1 << 20), b''):
                h.update(block)
        return h.hexdigest()
    except OSError:
        return None

def ft(n):
    p=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(p,n) if p.is_file() else ImageFont.load_default()

def _json_safe(value):
    """Convert non-finite audit values to JSON null for browser clients."""
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _privileged_corner_teacher_action(env, side_id: int, *, contact_duration_s: float,
                                     contact_seen: bool) -> tuple[np.ndarray, float, bool, float, float]:
    """Evaluate the analytic privileged teacher on the current table-side contact.

    This helper is intentionally only for visualization/training diagnostics:
    it reads MuJoCo contact force, normal/distance and duration, which are not
    part of the deployed ESN observation contract.
    """
    force = 0.0
    signed_distance = 1.0e-3
    normal = np.zeros(3, dtype=float)
    touching = False
    for index in range(env.data.ncon):
        contact = env.data.contact[index]
        pair = {int(contact.geom1), int(contact.geom2)}
        if side_id not in pair:
            continue
        other = int(contact.geom2) if int(contact.geom1) == side_id else int(contact.geom1)
        if other not in getattr(env, "_end_effector_geom_ids", set()):
            continue
        touching = True
        wrench = np.zeros(6, dtype=float)
        mujoco.mj_contactForce(env.model, env.data, index, wrench)
        candidate_force = float(np.linalg.norm(wrench[:3]))
        if candidate_force >= force:
            force = candidate_force
            signed_distance = float(contact.dist)
            hand = np.asarray(env.data.xpos[env._hand_id], dtype=float)
            board = np.asarray(env.data.geom_xpos[side_id], dtype=float)
            direction_to_board = board - hand
            norm = float(np.linalg.norm(direction_to_board))
            if norm > 1.0e-9:
                # privileged_teacher_action negates the normal, so this
                # orientation makes the yield point away from the apron.
                normal = direction_to_board / norm
    if touching:
        contact_seen = True
        contact_duration_s += 0.04
    cfg = PrivilegedTeacherConfig()
    action = privileged_teacher_action(
        force, normal, contact_duration_s, signed_distance,
        np.concatenate((
            env._wbc_command(env.step_count * 0.04).target_position_m
            - env.data.xpos[env._hand_id],
            np.zeros(3),
        )),
        config=cfg,
    ) if touching or contact_seen else np.zeros(7, dtype=float)
    return action, contact_duration_s, contact_seen, force, max(0.0, -signed_distance)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--menagerie",type=Path,required=True)
    ap.add_argument("--esn",type=Path,required=True); ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--seed",type=int,default=20264031); ap.add_argument("--fps",type=int,default=20)
    ap.add_argument("--simulation-time",type=float,default=8.0)
    ap.add_argument("--scenario",choices=("combined","ball","push","corner"),default="combined")
    ap.add_argument("--controller",choices=("paper_mpc","vmc","mlp","esn","teacher"),default="esn")
    ap.add_argument("--mlp",type=Path,default=None,help="MLP checkpoint for --controller mlp")
    ap.add_argument("--vmc-stiffness",type=float,default=1.0)
    ap.add_argument("--vmc-k-translation",type=float,default=None)
    ap.add_argument("--vmc-k-rotation",type=float,default=None)
    ap.add_argument("--vmc-zeta",type=float,default=None)
    ap.add_argument("--vmc-mass",type=float,default=None)
    ap.add_argument("--vmc-inertia",type=float,default=None)
    ap.add_argument("--vmc-drive-k",type=float,default=None)
    ap.add_argument("--vmc-drive-k-rotation",type=float,default=None)
    ap.add_argument("--vmc-drive-zeta",type=float,default=None)
    ap.add_argument("--vmc-max-speed",type=float,default=None)
    ap.add_argument("--vmc-max-angular-speed",type=float,default=None)
    ap.add_argument("--vmc-yield-speed",type=float,default=None)
    ap.add_argument("--vmc-yield-angular-speed",type=float,default=None)
    ap.add_argument("--vmc-max-force",type=float,default=None)
    ap.add_argument("--vmc-max-moment",type=float,default=None)
    ap.add_argument("--vmc-slowdown-offset-start",type=float,default=None)
    ap.add_argument("--vmc-slowdown-offset-full",type=float,default=None)
    ap.add_argument("--vmc-slowdown-rate-start",type=float,default=None)
    ap.add_argument("--vmc-slowdown-rate-full",type=float,default=None)
    ap.add_argument("--vmc-slowdown-max-action",type=float,default=None)
    ap.add_argument("--no-render",action="store_true",help="collect metrics without writing GIF frames")
    ap.add_argument("--trace-output",type=Path,default=None,
                    help="optional npz archive of deployable observations and executed actions")
    ap.add_argument("--record-privileged-labels",action="store_true",
                    help="training-only: save analytic teacher actions evaluated on student rollout states")
    a=ap.parse_args(); scenario=a.scenario
    # Keep the tabletop+finger collision channel local to the thick-corner
    # protocol.  The renderer historically enabled THICK_TABLE_SCENE at
    # module import for all scenarios, which accidentally changed ball/push
    # target collision semantics during teacher collection.
    os.environ["TARGET_TABLE_AFFINITY"] = "14" if scenario in ("corner", "combined") else "2"
    # A demo is complete only after the manipulation consequence is visible:
    # the two isolated disturbance tests must recover, close on the block and
    # lift it; the table-corner test must reach the tabletop, open the gripper
    # and leave enough settling time to show a genuine physical placement.
    minimum_duration_s = {"ball": 8.4, "push": 13.0, "corner": 10.4}
    if scenario in minimum_duration_s:
        a.simulation_time = max(float(a.simulation_time), minimum_duration_s[scenario])
    os.environ["PUSH_ROD_SCENE"] = "1" if scenario in ("combined", "push") else "0"
    # The rod test must finish before the upward apron approach starts.  The
    # previous 2.70--3.80 s window overlapped the first table contact at about
    # 3.76 s, making the two disturbances impossible to separate in analysis.
    # Finish the rod perturbation well before the first apron contact.  The
    # previous window ended at 3.10 s and left only about 260 ms of free
    # recovery; this shorter window gives a visually and quantitatively clean
    # rod-release interval before the table-corner phase.
    if scenario == "push":
        # The isolated push is a sustained finite-mass press, not an impulse:
        # approach for 0.90 s, remain loaded for 1.00 s, then retract over
        # 0.55 s. This leaves a clean recovery interval before grasping.
        # Let the nominal WBC finish its descent and settle at the grasp
        # waypoint before the finite-mass rod arrives.  The previous start at
        # 0.80 s contacted the hand while it was still moving down, so the
        # post-release "recovery" was incorrectly measured against a moving
        # pre-contact baseline and the block was never enclosed by the fingers.
        push_start_s = float(os.environ.get("PUSH_ROD_START_S", "1.80"))
        push_press_s = float(os.environ.get("PUSH_ROD_PRESS_S", "0.90"))
        push_hold_s = float(os.environ.get("PUSH_ROD_HOLD_S", "4.50"))
        push_retract_s = float(os.environ.get("PUSH_ROD_RETRACT_S", "0.70"))
    else:
        push_start_s, push_press_s, push_hold_s, push_retract_s = 2.45, 0.22, 0.10, 0.18
    push_end_s = push_start_s + push_press_s + push_hold_s + push_retract_s
    # A human-like response to a sustained lateral push is not to freeze and
    # wait for release.  The hand should accumulate a bounded tangential
    # offset while the rod is still loaded, then rejoin the nominal path after
    # withdrawal.  The bypass is expressed in the x direction, orthogonal to
    # the rod's -y approach axis.  The default is +z because the detail
    # camera looks along x; this makes the ongoing bypass visually observable
    # instead of hiding it in camera depth.
    push_bypass_axis = os.environ.get("PUSH_BYPASS_AXIS", "z").strip().lower()
    if push_bypass_axis not in {"x", "z"}:
        raise ValueError("PUSH_BYPASS_AXIS must be 'x' or 'z'")
    push_bypass_offset_m = float(os.environ.get("PUSH_BYPASS_OFFSET_M", "0.055"))
    push_bypass_speed_mps = float(os.environ.get("PUSH_BYPASS_SPEED_MPS", "0.045"))
    push_bypass_kp_s_inv = float(os.environ.get("PUSH_BYPASS_KP_S_INV", "1.00"))
    # Require a clearly observable physical departure before beginning the
    # in-contact rejoin.  This keeps the push benchmark's >=30-mm yield
    # event intact while still allowing rejoin before rod withdrawal.
    push_rejoin_clearance_m = float(os.environ.get("PUSH_REJOIN_CLEARANCE_M", "0.030"))
    # Once the z-side bypass has cleared the rod, explicitly pass on the
    # robot's +x side while the rod is still held extended.  The previous
    # 35-mm offset was too small to be visible and was mostly absorbed by
    # the WBC posture feedback, so the hand appeared to wait for release.
    push_rejoin_pass_offset_m = float(os.environ.get("PUSH_REJOIN_PASS_OFFSET_M", "0.100"))
    push_rejoin_pass_speed_mps = float(os.environ.get("PUSH_REJOIN_PASS_SPEED_MPS", "0.120"))
    push_rejoin_pass_kp_s_inv = float(os.environ.get("PUSH_REJOIN_PASS_KP_S_INV", "1.50"))
    push_rejoin_track_speed_mps = float(os.environ.get("PUSH_REJOIN_TRACK_SPEED_MPS", "0.100"))
    push_rejoin_track_kp_s_inv = float(os.environ.get("PUSH_REJOIN_TRACK_KP_S_INV", "2.00"))
    os.environ["PUSH_ROD_START_S"] = str(push_start_s)
    os.environ["PUSH_ROD_PRESS_S"] = str(push_press_s)
    os.environ["PUSH_ROD_HOLD_S"] = str(push_hold_s)
    os.environ["PUSH_ROD_RETRACT_S"] = str(push_retract_s)
    # The push test uses the corrected pre-grasp height (joint-4=-1.80), so
    # place the rod at the palm height and align its finite-radius cylinder
    # with the hand's x position.  Keeping these as scene-only environment
    # parameters leaves the ball and table-corner protocols unchanged.
    if scenario == "push":
        os.environ.setdefault("PUSH_ROD_CENTER_X", "0.550")
        os.environ.setdefault("PUSH_ROD_CENTER_Z", "0.530")
    else:
        os.environ.pop("PUSH_ROD_CENTER_X", None)
        os.environ.pop("PUSH_ROD_CENTER_Z", None)
    # Validated push configuration: the finite-mass rod produces a visible
    # >=30 mm departure while preserving grasp success and sub-mm contact
    # penetration.  Keep the values overridable for future ablations.
    os.environ.setdefault("PUSH_ROD_STROKE_M", "0.085" if scenario == "push" else "0.090")
    # Ball parameters are exposed as environment variables so candidate
    # contact geometries can be screened on the server without editing the
    # protocol itself. Defaults are the last validated finite-mass impact.
    # A modest finite-mass increase makes the strike visibly stronger without
    # turning the impactor into an artificial kinematic obstacle.  The value
    # remains exposed for parameter sweeps and is audited in terminal_info.
    ball_mass = float(os.environ.get("BALL_MASS_KG", "0.30"))
    ball_stroke = float(os.environ.get("BALL_STROKE_M", "0.220" if scenario == "ball" else "0.160"))
    ball_press = float(os.environ.get("BALL_PRESS_S", "0.030"))
    ball_retract = float(os.environ.get("BALL_RETRACT_S", "0.16"))
    ball_proxy_y = float(os.environ.get("BALL_PROXY_Y_M", "0.022"))
    ball_proxy_z = float(os.environ.get("BALL_PROXY_Z_M", "0.040"))
    ball_proxy_sy = float(os.environ.get("BALL_PROXY_SY_M", "0.026"))
    # The validated eccentric strike line is still on the palm proxy and
    # remains clear of the upstream FR3 link; the old 0.55 m line was too
    # central to make the physical departure obvious in the overview camera.
    ball_center_x = float(os.environ.get("BALL_CENTER_X_M", "0.60"))
    ball_height = float(os.environ.get("BALL_HEIGHT_M", "0.480" if scenario == "ball" else "0.541"))
    wbc_gain_scale = float(os.environ.get("WBC_GAIN_SCALE", "1.0"))
    ball_phase_gain_scale = float(os.environ.get("BALL_PHASE_GAIN_SCALE", "0.20" if scenario == "ball" else "0.45"))
    ball_start_s = 2.55 if scenario == "ball" else 1.055
    default_gain_start = ball_start_s - 0.15
    default_gain_end = ball_start_s + ball_press + ball_retract + 0.35
    ball_phase_gain_start = float(os.environ.get("BALL_PHASE_GAIN_START_S", str(default_gain_start)))
    ball_phase_gain_end = float(os.environ.get("BALL_PHASE_GAIN_END_S", str(default_gain_end)))
    # Keep the impact itself compliant, then explicitly restore stronger WBC
    # authority once the finite-mass ball has finished its press/retract.
    # This is a protocol-time schedule (no obstacle state is read), and makes
    # the post-impact rejoin visible without increasing the instantaneous
    # collision torque.
    ball_recovery_start_s = float(os.environ.get(
        "BALL_RECOVERY_START_S", str(ball_start_s + ball_press + ball_retract)))
    ball_recovery_end_s = float(os.environ.get("BALL_RECOVERY_END_S", "4.80"))
    ball_recovery_gain_scale = float(os.environ.get(
        "BALL_RECOVERY_WBC_GAIN_SCALE", "2.20"))
    # Let each learned controller respond during the ball impact through the
    # approach-axis residual only.  The previous ``off`` default silently
    # disabled all learned residuals before grasping, making ball results
    # identical across methods.  Keeping only vy avoids steering an upstream
    # link into the finite-mass impactor while preserving a fair low-level
    # comparison.
    pregrasp_yield_mode = os.environ.get(
        "PREGRASP_YIELD_MODE", "y_only" if scenario in ("ball", "push") else "off")
    board_y_offset = float(os.environ.get("LIFT_BOARD_Y_OFFSET_M", "0.0"))
    board_z_offset = float(os.environ.get("LIFT_BOARD_Z_OFFSET_M", "0.0"))
    # In the isolated impact tests the external object is fully withdrawn
    # before the close command.  These times preserve a clean free-recovery
    # interval while keeping the final GIF concise enough for presentation.
    # Keep the nominal protocol unchanged by default, but expose the push
    # grasp time for controlled recovery-time sweeps.  This is useful because
    # the sustained rod test needs a clean free-recovery interval after
    # withdrawal before the fingers close around the object.
    grasp_time_s = {"ball": 5.40, "push": 10.50}.get(scenario, 2.40)
    if scenario == "push":
        grasp_time_s = float(os.environ.get("PUSH_GRASP_TIME_S", str(grasp_time_s)))
    ball_contact_tau = float(os.environ.get("BALL_CONTACT_TIME_CONSTANT_S", "0.001"))
    ball_driver_kp = float(os.environ.get("BALL_DRIVER_KP", "1000.0"))
    ball_driver_force_limit = float(os.environ.get("BALL_DRIVER_FORCE_LIMIT_N", "100.0"))
    fx=VelocityResidualFixture(rod_stroke_m=ball_stroke,rod_height_m=ball_height,rod_start_time_s=ball_start_s,
        grasp_time_s=grasp_time_s,rod_approach_side="negative_y",impactor_type="ball",impactor_mass_kg=ball_mass,
        ball_radius_m=.03,rod_slide_damping=20.,rod_driver_kp=ball_driver_kp,
        rod_driver_force_limit_n=ball_driver_force_limit,
        contact_time_constant_s=ball_contact_tau,rod_center_x_m=ball_center_x,ball_impulse_mode=True,
        ball_impulse_press_duration_s=ball_press,ball_impulse_retract_duration_s=ball_retract)
    base_velocity_gains = wbc_gain_scale*np.array([42,42,36,32,9,8,6.])
    env=PandaWBCVelocityResidualEnv(menagerie=a.menagerie,fan_ye_model_npz=None,fan_ye_train_summary_json=None,
        observation_mode="direct_esn",fixtures=(fx,),rod_enabled=scenario in ("combined", "ball"),seed=a.seed,robot="fr3",
        execution_mode="twist",wbc_backend="paper_mpc",
        safety_config=VelocityResidualSafetyConfig(velocity_gain_nm_per_radps=base_velocity_gains.copy()),
        table_board_underside_z=.625,simulation_time_s=a.simulation_time,grasp_retention_mode="off",
        lift_board_y_offset_m=board_y_offset, lift_board_z_offset_m=board_z_offset,
        joint_velocity_noise_std=float(os.environ.get("JOINT_VELOCITY_NOISE_STD", "0.0")),
        joint_torque_noise_std=float(os.environ.get("JOINT_TORQUE_NOISE_STD", "0.0")))
    env.reset(seed=a.seed,options={"fixture_index":0})
    # Matched deployment perturbation: all controllers receive the same
    # reproducible initial encoder offset for a given seed.  The MuJoCo
    # contact state remains physical; only the initial robot configuration is
    # perturbed before the first control step.
    init_joint_std = float(os.environ.get("INIT_JOINT_PERTURB_STD_RAD", "0.0"))
    if init_joint_std > 0.0:
        env.data.qpos[:7] += init_joint_std * env.np_random.standard_normal(7)
        env.data.qvel[:7] = 0.0
        mujoco.mj_forward(env.model, env.data)
    # Use the audited straight-up -> clear-apron -> place reference.  The
    # nominal path approaches the table from below, then opens the gripper
    # only after the payload has reached the tabletop.
    ref = env.reference
    placement_gate = {'stable_s': 0.0, 'max_stable_s': 0.0,
                      'released': False, 'release_time_s': None,
                      'hover_stable_s': 0.0, 'max_hover_stable_s': 0.0,
                      'settle_relaxation_active': False,
                      'last_supported': False, 'last_target_speed_mps': None,
                      'last_target_bottom_m': None, 'last_table_surface_m': None,
                      'last_margin_xy_m': None, 'last_support_gap_m': None}
    home, pre, hold, lift, carry = [q.copy() for q in ref.q_knots]
    hold_debug = {}
    # The stock reference only changed joint-4, leaving the hand roughly
    # 0.19 m away from the block in the thick-table scene.  Solve a reachable
    # pre-grasp pose from the actual object position so the physical fingers,
    # rather than a hidden retention force, perform the grasp.
    if scenario in ("corner", "push", "ball", "combined"):
        from scipy.optimize import least_squares
        target_body = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_BODY, "target_object")
        target_xyz = env.data.xpos[target_body].copy()
        # The free block settles under gravity before the 2.4 s grasp event.
        # Solve grasp IK against its supported tabletop height, not the XML
        # spawn height, otherwise the fingers approach ~30 mm too high.
        top_for_grasp = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "thick_table_top")
        target_geom_for_grasp = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "target_object_geom")
        if top_for_grasp >= 0 and target_geom_for_grasp >= 0:
            target_xyz[2] = float(env.data.geom_xpos[top_for_grasp, 2] + env.model.geom_size[top_for_grasp, 2]
                                   - env.model.geom_size[target_geom_for_grasp, 2])
        scratch_hold = mujoco.MjData(env.model)
        scratch_hold.qpos[:] = env.data.qpos
        scratch_hold.qpos[:7] = hold
        mujoco.mj_forward(env.model, scratch_hold)
        # The Panda hand frame is above/behind the block at the grasp pose;
        # target the hand center and preserve the validated orientation.
        goal_p = target_xyz + np.array([0.016, 0.0, -0.160])
        goal_r = scratch_hold.xmat[env._hand_id].reshape(3, 3).copy()
        grasp_yaw = float(os.environ.get('GRASP_YAW_DEG', '0.0'))
        if abs(grasp_yaw) > 1e-12:
            a_yaw = np.deg2rad(grasp_yaw)
            Ry = np.array([[np.cos(a_yaw), 0., np.sin(a_yaw)],
                           [0., 1., 0.],
                           [-np.sin(a_yaw), 0., np.cos(a_yaw)]])
            goal_r = Ry @ goal_r
        def hold_residual(q):
            scratch_hold.qpos[:7] = q
            mujoco.mj_forward(env.model, scratch_hold)
            return np.r_[scratch_hold.xpos[env._hand_id] - goal_p,
                         0.05 * (scratch_hold.xmat[env._hand_id].reshape(3, 3) - goal_r).ravel(),
                         0.001 * (q - hold)]
        sol = least_squares(hold_residual, hold, max_nfev=600,
                            bounds=(env.model.jnt_range[:7, 0], env.model.jnt_range[:7, 1]))
        if np.linalg.norm(hold_residual(sol.x)[:3]) > 0.003:
            raise RuntimeError(f"pre-grasp hold IK failed: residual={hold_residual(sol.x)[:3].tolist()}")
        hold = sol.x
        hold_debug = {"goal_hand_position_m": goal_p.tolist(),
                      "solved_joint_position": hold.tolist(),
                      "residual_m": hold_residual(hold)[:3].tolist()}
        pre = hold.copy()
        # Generate a Cartesian vertical lift from the solved grasp pose.  A
        # raw joint-4 increment causes a large lateral sweep in this FR3
        # kinematic chain and drags the object out of the finger pads.
        scratch_lift = mujoco.MjData(env.model)
        scratch_lift.qpos[:] = env.data.qpos
        scratch_lift.qpos[:7] = hold
        mujoco.mj_forward(env.model, scratch_lift)
        # The thick-table route deliberately starts with a small 50-mm lift,
        # then gains height through its contact/escape waypoints. The
        # isolated ball and sustained-push tasks have no such later route;
        # use a taller Cartesian lift there so a successful physical pinch
        # satisfies the common 100-mm lift gate.
        isolated_lift_m = float(os.environ.get("ISOLATED_LIFT_M", "0.160"))
        lift_height_m = isolated_lift_m if scenario in ("ball", "push") else .050
        if lift_height_m <= 0.0:
            raise ValueError("lift height must be positive")
        lift_goal_p = scratch_lift.xpos[env._hand_id].copy() + np.array([0., 0., lift_height_m])
        lift_goal_r = scratch_lift.xmat[env._hand_id].reshape(3, 3).copy()
        def lift_residual(q):
            scratch_lift.qpos[:7] = q
            mujoco.mj_forward(env.model, scratch_lift)
            return np.r_[scratch_lift.xpos[env._hand_id] - lift_goal_p,
                         0.05 * (scratch_lift.xmat[env._hand_id].reshape(3, 3) - lift_goal_r).ravel(),
                         0.001 * (q - hold)]
        lift_sol = least_squares(lift_residual, hold, max_nfev=600,
                                 bounds=(env.model.jnt_range[:7, 0], env.model.jnt_range[:7, 1]))
        lift = lift_sol.x if np.linalg.norm(lift_residual(lift_sol.x)[:3]) < .004 else hold.copy()
        carry = lift.copy()
    # The nominal lift deliberately enters the apron with the end-effector
    # only: q2/q4=(0.40,-1.00) places the palm at approximately
    # (x,z)=(0.67,0.65), i.e. just across the apron left face while the
    # upstream links remain outside the hand-only collision channel.  The
    # following escape waypoint backs away before the final tabletop approach.
    contact = lift.copy(); contact[1] = 0.35; contact[3] = -1.20
    escape = lift.copy(); escape[1] = 0.16; escape[3] = -0.82
    # Place pose is at the near edge of the tabletop; the gripper opens only
    # after the payload has settled on the upper surface.
    place = np.array([0.0, 0.793, 0.0, -0.474, 0.0, 2.373, -0.785])
    lower = float(os.environ.get('PLACE_LOWER_M', '0.0'))
    place_x_offset = float(os.environ.get('PLACE_X_OFFSET_M', '0.0'))
    upright_place = os.environ.get('UPRIGHT_PLACE', '0') == '1'
    if lower or place_x_offset or upright_place:
        from scipy.optimize import least_squares
        scratch_place = mujoco.MjData(env.model)
        scratch_place.qpos[:] = env.data.qpos
        scratch_place.qpos[:7] = place
        mujoco.mj_forward(env.model,scratch_place)
        goal_p = scratch_place.xpos[env._hand_id].copy() + np.array([place_x_offset,0.,-lower])
        goal_r = scratch_place.xmat[env._hand_id].copy()
        place_pitch_deg = float(os.environ.get('PLACE_PITCH_DEG', '0.0'))
        if place_pitch_deg:
            pitch = np.deg2rad(place_pitch_deg)
            world_y_rotation = np.array([
                [np.cos(pitch), 0.0, np.sin(pitch)],
                [0.0, 1.0, 0.0],
                [-np.sin(pitch), 0.0, np.cos(pitch)],
            ])
            goal_r = (world_y_rotation @ goal_r.reshape(3, 3)).reshape(-1)
        if upright_place:
            # Match the original grasp orientation: payload below the hand,
            # rather than rotating it in front of the palm at the table edge.
            scratch_place.qpos[:7] = hold
            mujoco.mj_forward(env.model, scratch_place)
            goal_r = scratch_place.xmat[env._hand_id].copy()
            goal_p = np.array([float(os.environ.get('UPRIGHT_PLACE_X', '.74')),0.,
                               float(os.environ.get('UPRIGHT_PLACE_Z', '.82'))])
        def place_residual(q):
            scratch_place.qpos[:7]=q
            mujoco.mj_forward(env.model,scratch_place)
            orientation_weight = float(os.environ.get('PLACE_ORIENTATION_WEIGHT','0.1'))
            return np.r_[scratch_place.xpos[env._hand_id]-goal_p,
                         orientation_weight*(scratch_place.xmat[env._hand_id]-goal_r),
                         .001*(q-place)]
        solutions = [least_squares(place_residual,guess,max_nfev=400,
                     bounds=(env.model.jnt_range[:7,0],env.model.jnt_range[:7,1]))
                     for guess in ((hold,place,escape) if upright_place else (place,))]
        solution = min(solutions,key=lambda s:np.linalg.norm(place_residual(s.x)))
        if np.linalg.norm(place_residual(solution.x)[:3])>.001:
            raise RuntimeError(f'placement offset IK failed: residual={place_residual(solution.x).tolist()}')
        place=solution.x
    # Optional second, purely tangential placement waypoint.  The first
    # place pose establishes real payload/table support near the edge; this
    # waypoint then keeps the gripper closed and slides the supported payload
    # farther onto the tabletop before the state-based release gate may open.
    # Unlike the removed vertical settle waypoint, it does not drive the palm
    # into the rigid tabletop.  It is a nominal manipulation waypoint shared
    # by all controllers, not an obstacle-state input to MLP/ESN.
    place_settle = place.copy()
    place_settle_x = float(os.environ.get('PLACE_SETTLE_X_M', '0.0'))
    place_final_descent = float(os.environ.get('PLACE_FINAL_DESCENT_M', '0.0'))
    place_final_pitch_delta_deg = float(os.environ.get(
        'PLACE_FINAL_PITCH_DELTA_DEG', '0.0'))
    if not 0.0 <= place_final_descent <= 0.015:
        raise ValueError('PLACE_FINAL_DESCENT_M must be within [0, 0.015]')
    if not -20.0 <= place_final_pitch_delta_deg <= 20.0:
        raise ValueError('PLACE_FINAL_PITCH_DELTA_DEG must be within [-20, 20]')
    if place_settle_x or place_final_descent or place_final_pitch_delta_deg:
        from scipy.optimize import least_squares
        scratch_settle = mujoco.MjData(env.model)
        scratch_settle.qpos[:] = env.data.qpos
        scratch_settle.qpos[:7] = place
        mujoco.mj_forward(env.model, scratch_settle)
        settle_goal_p = (
            scratch_settle.xpos[env._hand_id].copy()
            + np.array([place_settle_x, 0.0, -place_final_descent])
        )
        settle_goal_r = scratch_settle.xmat[env._hand_id].copy()
        if place_final_pitch_delta_deg:
            delta = np.deg2rad(place_final_pitch_delta_deg)
            settle_pitch = np.array([
                [np.cos(delta), 0.0, np.sin(delta)],
                [0.0, 1.0, 0.0],
                [-np.sin(delta), 0.0, np.cos(delta)],
            ])
            settle_goal_r = (
                settle_pitch @ settle_goal_r.reshape(3, 3)
            ).reshape(-1)
        def settle_residual(q):
            scratch_settle.qpos[:7] = q
            mujoco.mj_forward(env.model, scratch_settle)
            return np.r_[
                scratch_settle.xpos[env._hand_id] - settle_goal_p,
                .1 * (scratch_settle.xmat[env._hand_id] - settle_goal_r),
                .001 * (q - place),
            ]
        settle_solution = least_squares(
            settle_residual, place, max_nfev=400,
            bounds=(env.model.jnt_range[:7, 0], env.model.jnt_range[:7, 1]),
        )
        if np.linalg.norm(settle_residual(settle_solution.x)[:3]) > .001:
            raise RuntimeError(
                'placement tangential settle IK failed: '
                f'residual={settle_residual(settle_solution.x).tolist()}'
            )
        place_settle = settle_solution.x
    if scenario == "ball":
        # Impact the open hand, recover at the unchanged pre-grasp waypoint,
        # then physically close and lift the block.  The environment shifts
        # the stock smooth gripper profile so closure starts at grasp_time_s.
        ref.times = np.array([0.0, 1.70, grasp_time_s + 0.55, 7.50, a.simulation_time])
        ref.q_knots = np.stack([home, pre, hold, lift, lift])
    elif scenario == "push":
        # The rod completes press--hold--withdraw while the hand is open.
        # After an uncontaminated recovery interval, close and lift normally.
        # After the rod withdraws, hold the recovered pre-grasp pose through
        # the physical gripper-close interval.  Only then begin lifting; this
        # prevents a pushed-away hand from starting the lift before it has
        # actually enclosed the block.
        ref.times = np.array([0.0, 1.70, grasp_time_s, grasp_time_s + 0.80, a.simulation_time])
        ref.q_knots = np.stack([home, pre, hold, hold, lift])
        clearance = float(os.environ.get('PREGRASP_CLEARANCE_M', '0.0'))
        if clearance > 0:
            from scipy.optimize import least_squares
            # Offline FK/IK on scratch data: never teleport the simulation.
            scratch = mujoco.MjData(env.model)
            scratch.qpos[:] = env.data.qpos
            scratch.qpos[:7] = hold
            mujoco.mj_forward(env.model, scratch)
            target_p = scratch.xpos[env._hand_id].copy() + np.array([0.,0.,clearance])
            target_r = scratch.xmat[env._hand_id].copy()
            def residual(q):
                scratch.qpos[:7] = q
                mujoco.mj_forward(env.model, scratch)
                return np.r_[scratch.xpos[env._hand_id]-target_p,
                             .1*(scratch.xmat[env._hand_id]-target_r),.001*(q-hold)]
            solution = least_squares(residual, hold, max_nfev=100,
                bounds=(env.model.jnt_range[:7,0],env.model.jnt_range[:7,1]))
            if np.linalg.norm(residual(solution.x)[:3]) > .001:
                raise RuntimeError('pregrasp clearance IK failed')
            ref.times = np.array([0.,1.7,grasp_time_s-1.0,grasp_time_s,
                                  grasp_time_s+.8,a.simulation_time])
            ref.q_knots = np.stack([home,solution.x,solution.x,hold,hold,lift])
    else:
        place_duration = float(os.environ.get('PLACE_APPROACH_DURATION_S', '1.4'))
        if place_duration <= 0:
            raise ValueError('PLACE_APPROACH_DURATION_S must be positive')
        place_end = 6.8 + place_duration
        settle_duration = float(os.environ.get('PLACE_SETTLE_DURATION_S', '0.8'))
        if settle_duration <= 0:
            raise ValueError('PLACE_SETTLE_DURATION_S must be positive')
        has_final_settle = bool(
            place_settle_x or place_final_descent or place_final_pitch_delta_deg)
        settle_end = place_end + settle_duration if has_final_settle else place_end
        a.simulation_time = max(a.simulation_time, settle_end+2.8)
        # Extend only the common placement segment, not the disturbance event.
        env.simulation_time_s = a.simulation_time
        # Hold the solved grasp pose through the complete physical closure
        # interval before moving the arm.  This prevents the object from
        # being merely brushed by the pads while the hand is already lifting.
        if has_final_settle:
            ref.times = np.array([0.0, 1.70, 2.40, 3.60, 4.10, 5.20, 6.80,
                                  place_end, settle_end, settle_end+.8])
            ref.q_knots = np.stack([home, pre, hold, hold, lift, contact, escape,
                                    place, place_settle, place_settle])
        else:
            ref.times = np.array([0.0, 1.70, 2.40, 3.60, 4.10, 5.20, 6.80,
                                  place_end, place_end+.8])
            ref.q_knots = np.stack([home, pre, hold, hold, lift, contact, escape,
                                    place, place])
        # Shared task supervisor, NOT a student observation. No timed release.
        def supported_gripper_target(t):
            if t < 2.4:
                # Match the validated Panda grasp benchmark: the tendon
                # position target 0.0 is the closed state; the larger target
                # opens the coupled fingers.
                return float(os.environ.get('GRIPPER_OPEN_COMMAND', '0.060'))
            if not placement_gate['released']:
                # A payload can remain a few millimetres above the table
                # because the closed fingers support it before the rigid top
                # does.  Once a state-based gate confirms a slow, safely
                # inset near-surface hover, slightly relax the fingers so
                # gravity can establish real table support.  This is not the
                # release command: full opening remains impossible until the
                # payload/table support gate has held for 0.24 s.
                if placement_gate['settle_relaxation_active']:
                    return float(os.environ.get(
                        'PLACEMENT_SETTLE_GRIPPER_COMMAND', '0.0'))
                return 0.0
            phase = np.clip((t-placement_gate['release_time_s'])/.55,0.,1.)
            opened = float(os.environ.get('GRIPPER_OPEN_COMMAND', '0.060'))
            return float(opened*phase*phase*(3.-2.*phase))
        ref.gripper_target = supported_gripper_target
    # Shared, bounded gripper aperture ablation; no object-state feedback.
    aperture = float(os.environ.get('GRIPPER_OPEN_APERTURE_M', '0.060'))
    if not .060 <= aperture <= .080:
        raise ValueError('GRIPPER_OPEN_APERTURE_M must be within [0.060, 0.080]')
    original_gripper_target = ref.gripper_target
    ref.gripper_target = lambda t: min(.080, max(0., original_gripper_target(t) * aperture / .060))
    if hasattr(env.fixed_wbc, "waypoint_period_s"):
        period = float(env.fixed_wbc.waypoint_period_s)
        # Paper-MPC's queue is normally built for its default 8 s horizon.
        # The isolated push protocol is deliberately longer (it contains a
        # multi-second press, release/recovery interval, then grasp and lift),
        # so retaining the old queue silently saturated the WBC at t=8 s and
        # made the object appear ungraspable.  Rebuild the queue through the
        # complete requested simulation duration after every custom timeline.
        count = int(np.ceil(a.simulation_time / period)) + 1
        env.fixed_wbc.waypoints = np.stack([ref._joint_sample(i * period)[0] for i in range(count)])
    current_policy=None
    if a.controller in ("paper_mpc", "teacher"):
        ctl = None
    elif a.controller == "mlp":
        if a.mlp is None:
            raise ValueError("--mlp is required for --controller mlp")
        try:
            current_policy=load_current(a.mlp);ctl=_CurrentPolicyAdapter(current_policy,env)
        except ValueError:
            ctl = MLPComplianceController.from_npz(a.mlp)
    elif a.controller == "vmc":
        if not np.isfinite(a.vmc_stiffness) or a.vmc_stiffness <= 0.0:
            raise ValueError("--vmc-stiffness must be positive")
        base = SpringCarriageConfig()
        def pick(value, default):
            return default if value is None else float(value)
        k_scale = float(a.vmc_stiffness)
        cfg = SpringCarriageConfig(
            kappa_6d=base.kappa_6d,
            k_translation_base=pick(a.vmc_k_translation, base.k_translation_base * k_scale),
            k_rotation_base=pick(a.vmc_k_rotation, base.k_rotation_base * k_scale),
            zeta=pick(a.vmc_zeta, base.zeta),
            virtual_mass=pick(a.vmc_mass, base.virtual_mass),
            virtual_inertia=pick(a.vmc_inertia, base.virtual_inertia),
            carriage_drive_k_translation=pick(a.vmc_drive_k, base.carriage_drive_k_translation),
            carriage_drive_k_rotation=pick(a.vmc_drive_k_rotation, base.carriage_drive_k_rotation),
            carriage_drive_zeta=pick(a.vmc_drive_zeta, base.carriage_drive_zeta),
            max_force=pick(a.vmc_max_force, base.max_force),
            max_moment=pick(a.vmc_max_moment, base.max_moment),
            max_carriage_speed=pick(a.vmc_max_speed, base.max_carriage_speed),
            max_carriage_angular_speed=pick(a.vmc_max_angular_speed, base.max_carriage_angular_speed),
            slowdown_offset_start_m=pick(
                a.vmc_slowdown_offset_start, base.slowdown_offset_start_m),
            slowdown_offset_full_m=pick(
                a.vmc_slowdown_offset_full, base.slowdown_offset_full_m),
            slowdown_rate_start_mps=pick(
                a.vmc_slowdown_rate_start, base.slowdown_rate_start_mps),
            slowdown_rate_full_mps=pick(
                a.vmc_slowdown_rate_full, base.slowdown_rate_full_mps),
            slowdown_max_action=pick(
                a.vmc_slowdown_max_action, base.slowdown_max_action),
            drive_source="proprioceptive", carriage_drive="spring",
        )
        ctl = VMCComplianceAdapter(SpringCarriageVMC(cfg))
        ctl.set_yield_limits(
            pick(a.vmc_yield_speed, ctl.linear_yield_limit_mps),
            pick(a.vmc_yield_angular_speed, ctl.angular_yield_limit_radps),
        )
    else:
        try:
            current_policy=load_current(a.esn);ctl=_CurrentPolicyAdapter(current_policy,env)
        except ValueError:
            current_policy=None
            try: ctl=MultiHeadDirectESNController.from_npz(a.esn)
            except ValueError as e:
                if "readout_heads" not in str(e): raise
                ctl=DirectESNController.from_npz(a.esn)
    if ctl is not None and hasattr(ctl, "reset"):
        ctl.reset()
    vmc_nominal_drive_stiffness = None
    vmc_nominal_drive_damping = None
    if a.controller == 'vmc' and hasattr(ctl, 'baseline'):
        vmc_nominal_drive_stiffness = ctl.baseline.drive_stiffness.copy()
        vmc_nominal_drive_damping = ctl.baseline.drive_damping.copy()
    top=mujoco.mj_name2id(env.model,mujoco.mjtObj.mjOBJ_GEOM,"thick_table_top")
    side=mujoco.mj_name2id(env.model,mujoco.mjtObj.mjOBJ_GEOM,"table_side")
    table_height_offset = float(os.environ.get('TABLE_HEIGHT_OFFSET_M','0.0'))
    if table_height_offset:
        for gid in (top,side):
            if gid < 0:
                raise RuntimeError('table pair missing')
            env.model.geom_pos[gid,2] += table_height_offset
        mujoco.mj_forward(env.model,env.data)
    # Use the normal high-resolution contact audit.  The table phase uses the
    # hand STL collision mesh, so no visual mesh offset or oversized sphere is
    # needed.
    # Tight contact integration is especially important for the finite-mass
    # sustained push: the actuator remains force-limited after contact, and
    # the rod must not tunnel through the hand collision mesh.
    # Fast-ball impacts require a substantially tighter solver grid than the
    # quasi-static table and sustained-rod phases.  Without this, the small
    # palm proxy can show millimetre-scale numerical overlap even though the
    # visual frame appears plausible.
    ball_dt = float(os.environ.get("BALL_TIMESTEP_S", "0.00002"))
    ball_iters = int(os.environ.get("BALL_SOLVER_ITERATIONS", "2000"))
    # Use MuJoCo's Newton contact solve for the high-speed finite-mass strike.
    # The older default solver occasionally left a ~0.6 mm transient overlap
    # in the hand proxy even with a very small timestep.  Newton is the same
    # solver used by the audited successful teacher rollouts and keeps the
    # physical contact gate reproducible.
    env.model.opt.solver = mujoco.mjtSolver.mjSOL_NEWTON
    env.model.opt.timestep = min(float(env.model.opt.timestep),
                                 ball_dt if scenario == "ball" else
                                 (float(os.environ.get("PUSH_AUDIT_TIMESTEP_S", "0.0001")) if scenario == "push" else
                                  float(os.environ.get('CORNER_AUDIT_TIMESTEP_S', '.00025'))))
    env.model.opt.iterations = max(int(env.model.opt.iterations),
                                   ball_iters if scenario == "ball" else
                                   (600 if scenario == "push" else 400))
    if scenario == "push":
        from push_numerics_20260916 import configure_push_numerics
        configure_push_numerics(env.model)
    if scenario == "ball":
        # The ball is a fast finite-mass impactor.  A very small contact
        # time-step plus strict solver tolerances prevents transient
        # sub-millimetre overlap from being hidden between controller samples.
        env.model.opt.tolerance = min(float(env.model.opt.tolerance), 1.0e-10)
        env.model.opt.ls_iterations = max(int(env.model.opt.ls_iterations), 100)
    if side >= 0:
        env.model.geom_solref[side] = np.array([0.00001, 1.0])
        env.model.geom_solimp[side] = np.array([0.99999, 0.999999, 0.0000001, 0.5, 2.0])
    if top >= 0 and os.environ.get('RIGID_TABLE_CONTACT', '0') == '1':
        table_solref = float(os.environ.get('RIGID_TABLE_SOLREF_TIME', '0.00001'))
        env.model.geom_solref[top] = np.array([table_solref, 1.0])
        env.model.geom_solimp[top] = np.array([0.99999, 0.999999, 0.0000001, 0.5, 2.0])
        if os.environ.get('RIGID_TABLE_PRIORITY', '0') == '1':
            env.model.geom_priority[top] = int(np.max(env.model.geom_priority)) + 1
    hand_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
    ball_proxy = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "hand_ball_proxy")
    push_rod = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "push_rod_geom")
    # Each isolated protocol contains only the disturbance under test.  The
    # unused geometry is both non-colliding and invisible, preventing a later
    # event from contaminating recovery metrics or the visual interpretation.
    if scenario in ("ball", "push"):
        for geom_id in (top, side):
            if geom_id >= 0:
                env.model.geom_contype[geom_id] = 0
                env.model.geom_conaffinity[geom_id] = 0
                env.model.geom_rgba[geom_id, 3] = 0.0
    if scenario in ("push", "corner"):
        ball_geom = int(env._rod_geom_id)
        env.model.geom_contype[ball_geom] = 0
        env.model.geom_conaffinity[ball_geom] = 0
        env.model.geom_rgba[ball_geom, 3] = 0.0
    if hand_id >= 0:
        print(f"Hand collision type: {mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_GEOM, hand_id)}")
    if ball_proxy >= 0 and scenario == "push":
        # The ball-only auxiliary shape is not part of the palm exterior.
        env.model.geom_contype[ball_proxy] = 0
        env.model.geom_conaffinity[ball_proxy] = 0
    if ball_proxy >= 0:
        # A small lateral offset makes the finite-mass impact genuinely eccentric,
        # producing visible hand yaw/roll while preserving the same impulse budget.
        env.model.geom_pos[ball_proxy] = np.array([0.0, ball_proxy_y, ball_proxy_z])
        env.model.geom_size[ball_proxy][1] = ball_proxy_sy
        ball_proxy_solref = float(os.environ.get("BALL_PROXY_SOLREF_TIME_S", "0.000001"))
        if ball_proxy_solref <= 0.0:
            raise ValueError("BALL_PROXY_SOLREF_TIME_S must be positive")
        env.model.geom_solref[ball_proxy] = np.array([ball_proxy_solref, 1.0])
        # Keep the previous near-rigid impedance as the reproducibility
        # default, while allowing a physically softer finite-duration impact
        # during force calibration.
        proxy_imp_min = float(os.environ.get("BALL_PROXY_SOLIMP_MIN", "0.999999"))
        proxy_imp_max = float(os.environ.get("BALL_PROXY_SOLIMP_MAX", "0.9999999"))
        proxy_imp_width = float(os.environ.get("BALL_PROXY_SOLIMP_WIDTH", "0.00000001"))
        env.model.geom_solimp[ball_proxy] = np.array(
            [proxy_imp_min, proxy_imp_max, proxy_imp_width, 0.5, 2.0])
        print(f"Ball-phase hand proxy: {env.model.geom_size[ball_proxy].tolist()} pos={env.model.geom_pos[ball_proxy].tolist()}")
    ball=int(env._rod_geom_id); renderer=None if a.no_render else mujoco.Renderer(env.model,480,640)
    # Keep both views below the tabletop.  The first view establishes the
    # complete pick/lift/place context; the second is a front-on, low camera
    # looking through the open space under the tabletop at the hand/apron
    # interface.  A negative elevation means the optical axis points slightly
    # upward, so the tabletop cannot occlude the contact.
    cam=mujoco.MjvCamera(); cam.type=mujoco.mjtCamera.mjCAMERA_FREE
    if scenario == "push":
        # Oblique overview: x-bypass is visible as a lateral route while the
        # rod remains visibly in front of the hand rather than edge-on.
        cam.lookat[:]=[.58,-.01,.54]; cam.distance=1.22; cam.azimuth=32; cam.elevation=-12
    else:
        cam.lookat[:]=[.71,-.02,.49]; cam.distance=1.50; cam.azimuth=45; cam.elevation=-18
    # Exact side elevation: the tabletop/apron common edge is projected onto
    # one line, making any real gap immediately visible instead of hiding it
    # behind a perspective corner.
    under_cam=mujoco.MjvCamera(); under_cam.type=mujoco.mjtCamera.mjCAMERA_FREE
    if scenario == "push":
        # Side-on detail view looks along x, so the y-aligned rod is shown as
        # a long bar and its contact with the palm is unambiguous.
        under_cam.lookat[:]=[.55,.02,.54]; under_cam.distance=.52; under_cam.azimuth=0; under_cam.elevation=0
    else:
        under_cam.lookat[:]=[.64,-.03,.70]; under_cam.distance=.62; under_cam.azimuth=90; under_cam.elevation=0
    hand_body = int(env.model.geom_bodyid[mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")])
    hand_tree = set()
    for bid in range(env.model.nbody):
        cur = bid
        while cur > 0 and cur != hand_body:
            cur = int(env.model.body_parentid[cur])
        if cur == hand_body:
            hand_tree.add(bid)
    allowed_compliance_bodies = {"hand", "left_finger", "right_finger", "fr3_link5", "fr3_link6", "fr3_link7"}
    target_geom = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "target_object_geom")
    runtime_collision_debug = {
        "target_geom_id": int(target_geom),
        "target_contype": int(env.model.geom_contype[target_geom]) if target_geom >= 0 else None,
        "target_conaffinity": int(env.model.geom_conaffinity[target_geom]) if target_geom >= 0 else None,
        "finger_geoms": [],
    }
    for gid in getattr(env, "_end_effector_geom_ids", []):
        body_name = mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_BODY,
                                      int(env.model.geom_bodyid[gid])) or ""
        if "finger" in body_name:
            runtime_collision_debug["finger_geoms"].append({
                "id": int(gid), "body": body_name,
                "contype": int(env.model.geom_contype[gid]),
                "conaffinity": int(env.model.geom_conaffinity[gid]),
                "margin": float(env.model.geom_margin[gid]),
            })
    initial_target_z = float(env.data.xpos[env._target_body_id][2])
    max_target_lift = 0.0
    target_top_contact = False
    target_top_first_contact_s = None
    frames=[]; first_side=None; ball_hit=None; push_hit=None; side_names=set(); side_bodies=set(); ball_names=set(); push_names=set(); max_side_pen=0.; max_upstream_pen=0.; max_push_pen=0.; peak_ball_force=0.; ball_contact_duration=0.; max_ball_ee_deviation=0.; peak_push_force=0.; push_contact_duration=0.; max_push_ee_deviation=0.; max_recovery_ee_error=0.; error_trace=[]; hand_trace=[]; speed_trace=[]; torque_trace=[]; trace_q=[]; trace_qdot=[]; trace_twist=[]; trace_pose_error=[]; trace_twist_error=[]; trace_joint_torque=[]; trace_command_actions=[]; trace_actions=[]; trace_privileged_labels=[]; trace_ee_position=[]; trace_nominal_position=[]; trace_ee_error=[]; grasp_contact_trace=[]; finger_qpos_trace=[]; finger_gap_trace=[]; grasp_target_pos_trace=[]; finger_pad_pos_trace=[]; teacher_contact_duration=0.0; teacher_contact_seen=False; label_contact_duration=0.0; label_contact_seen=False; push_contact_seen_local=False; push_contact_loss_steps=0; push_rejoin_started=False; push_rejoin_start_s=None; push_rejoin_track_started=False; push_rejoin_track_start_s=None; push_max_task_departure_m=0.0; push_in_hold_rejoin_complete_s=None; step=0; done=False; info={}
    while not done:
        t=step*.04
        if t >= grasp_time_s and 'POSTGRASP_SPEED_LIMIT_RADPS' in os.environ:
            from dataclasses import replace
            limit = float(os.environ['POSTGRASP_SPEED_LIMIT_RADPS'])
            if env.safety_config.maximum_joint_speed_radps != limit:
                env.safety_config = replace(env.safety_config, maximum_joint_speed_radps=limit)
        d=env.diagnostics(); kw={"pose_error":d["wbc_pose_error"],"twist_error":d["wbc_twist_error"]}
        if a.trace_output is not None:
            trace_q.append(np.asarray(d["joint_position"], dtype=np.float32).copy())
            trace_qdot.append(np.asarray(d["joint_velocity"], dtype=np.float32).copy())
            trace_twist.append(np.asarray(d["nominal_twist"], dtype=np.float32).copy())
            trace_pose_error.append(np.asarray(d["wbc_pose_error"], dtype=np.float32).copy())
            trace_twist_error.append(np.asarray(d["wbc_twist_error"], dtype=np.float32).copy())
            trace_joint_torque.append(np.asarray(d["joint_torque_estimate"], dtype=np.float32).copy())
        push_contact_now = False
        if scenario == "push" and push_rod >= 0:
            for contact_index in range(env.data.ncon):
                contact = env.data.contact[contact_index]
                pair = {int(contact.geom1), int(contact.geom2)}
                if push_rod not in pair:
                    continue
                other = int(contact.geom2) if int(contact.geom1) == push_rod else int(contact.geom1)
                if other in getattr(env, "_end_effector_geom_ids", set()):
                    push_contact_now = True
                    break
        if scenario == "push":
            task_departure_y = abs(
                float(d["ee_position"][1]) - float(d["nominal_position"][1])
            )
            push_max_task_departure_m = max(push_max_task_departure_m, task_departure_y)
            if push_contact_now:
                push_contact_seen_local = True
                push_contact_loss_steps = 0
            elif push_contact_seen_local:
                push_contact_loss_steps += 1
                # Once the hand has cleared the rod, rejoin immediately while
                # the rod is still held at its extended position.  This is
                # deliberately independent of the later withdrawal time.
                if push_contact_loss_steps >= 2 and not push_rejoin_started and t < push_end_s:
                    push_rejoin_started = True
                    push_rejoin_start_s = t
            # Do not wait for contact loss: once the measured tangential
            # departure has cleared the rod radius, begin rejoining the task
            # trajectory while the rod is still held in place.
            if push_contact_seen_local and not push_rejoin_started:
                bypass_index = 0 if push_bypass_axis == "x" else 2
                tangential_departure = abs(
                    float(d["ee_position"][bypass_index])
                    - float(d["nominal_position"][bypass_index])
                )
                rejoin_delay_s = float(os.environ.get("PUSH_REJOIN_DELAY_S", "0.55"))
                timed_rejoin = t >= push_start_s + push_press_s + rejoin_delay_s
                if (tangential_departure >= push_rejoin_clearance_m or timed_rejoin) and t < push_end_s:
                    push_rejoin_started = True
                    push_rejoin_start_s = t
            # Once contact has been sustained for a short, protocol-defined
            # interval, start the pass/rejoin maneuver even if the rod is
            # still pressing.  The old 30-mm displacement gate delayed this
            # until the end of the hold, which visually looked like waiting
            # for the rod to retract.  This gate uses only elapsed protocol
            # time plus the locally measured end-effector departure/contact;
            # it does not read rod pose, force, or any privileged state.
            if push_rejoin_started and not push_rejoin_track_started:
                # Phase 2 is state-triggered: do not pull back along y until
                # the measured hand has both yielded to the push and moved
                # far enough in x to pass the finite-radius rod.  These are
                # proprioceptive geometric errors, not obstacle state.
                x_departure = abs(
                    float(d["ee_position"][0]) - float(d["nominal_position"][0])
                )
                min_task_departure = float(os.environ.get(
                    "PUSH_REJOIN_MIN_TASK_DEPARTURE_M", "0.028"))
                track_clearance = float(os.environ.get(
                    "PUSH_REJOIN_TRACK_CLEARANCE_M", "0.035"))
                if (task_departure_y >= min_task_departure
                        and x_departure >= track_clearance):
                    push_rejoin_track_started = True
                    push_rejoin_track_start_s = t
            push_hold_end_s = push_start_s + push_press_s + push_hold_s
            if (push_rejoin_track_started
                    and push_in_hold_rejoin_complete_s is None
                    and push_max_task_departure_m >= 0.030
                    and task_departure_y <= 0.010
                    and t < push_hold_end_s):
                push_in_hold_rejoin_complete_s = t
        # A short, pre-grasp phase gain schedule gives the finite-mass ball
        # enough compliance to produce a visible physical departure, then
        # restores the validated gains before the rod/table phases.  It is a
        # task-phase parameter, not a contact/obstacle measurement.
        # Disturbance-time gain schedules are allowed only while generating
        # the tuned VMC teacher.  A learned student must not be helped by a
        # hidden clock that already knows when the ball or rod is active;
        # MLP/ESN (and the fixed Paper-MPC control) retain the same nominal
        # WBC gains throughout the disturbance and must express compliance
        # solely through their seven-dimensional action.
        # Legacy teacher traces used a disturbance-time low-level gain
        # schedule.  Keep that behaviour reproducible only when explicitly
        # enabled; new direct-action distillation campaigns set this flag to
        # zero so every successful teacher behaviour is representable by the
        # recorded seven-dimensional action alone.
        teacher_gain_schedule = (
            a.controller in ("teacher", "vmc")
            and os.environ.get("ALLOW_TEACHER_DISTURBANCE_GAIN_SCHEDULE", "1") == "1"
        )
        if (teacher_gain_schedule and scenario in ("combined", "ball")
                and ball_phase_gain_start <= t < ball_phase_gain_end):
            env.safety_config.velocity_gain_nm_per_radps[:] = base_velocity_gains * ball_phase_gain_scale
        elif (teacher_gain_schedule and scenario == "ball"
              and ball_recovery_start_s <= t < ball_recovery_end_s):
            env.safety_config.velocity_gain_nm_per_radps[:] = base_velocity_gains * ball_recovery_gain_scale
        elif (teacher_gain_schedule and scenario == "push"
              and push_start_s <= t < push_end_s):
            # The end-effector's world-y direction is dominated by FR3 joints
            # 1, 3 and 5 (indices 0, 2 and 4).  Lower only those feedback
            # gains during the push, retaining the z-lift gains so the later
            # grasp/lift phase remains unchanged.
            push_gains = base_velocity_gains.copy()
            # After the tangential clearance is reached, restore part of the
            # lateral feedback authority so the hand can actively recover its
            # pushed -y coordinate while the rod is still extended.  Keeping
            # this below the nominal gain preserves compliance; the x-side
            # pass command remains the mechanism that prevents re-contact.
            if a.controller in ("teacher", "vmc") and push_rejoin_started and push_rejoin_track_started:
                push_gains[[0, 2, 4]] *= float(os.environ.get("PUSH_REJOIN_WBC_GAIN_SCALE", "0.50"))
            else:
                push_gains[[0, 2, 4]] *= float(os.environ.get("PUSH_LATERAL_GAIN_SCALE", "0.15"))
            env.safety_config.velocity_gain_nm_per_radps[:] = push_gains
        elif (teacher_gain_schedule and scenario == "push"
              and push_end_s <= t < grasp_time_s):
            # After withdrawal the hand is no longer being intentionally
            # displaced.  Restore the normal residual authority, but allow a
            # modestly stronger low-level support gain to reject gravity-
            # induced sag during the long hold before grasping.
            recovery_wbc_scale = float(os.environ.get("PUSH_RECOVERY_WBC_GAIN_SCALE", "2.50"))
            env.safety_config.velocity_gain_nm_per_radps[:] = base_velocity_gains * recovery_wbc_scale
        else:
            env.safety_config.velocity_gain_nm_per_radps[:] = base_velocity_gains
        if t >= grasp_time_s + .8 and 'TRANSPORT_SERVO_SCALE' in os.environ:
            env.safety_config.velocity_gain_nm_per_radps[:] = base_velocity_gains * float(os.environ['TRANSPORT_SERVO_SCALE'])
        if scenario == 'corner':
            start = float(os.environ.get('TABLE_APPROACH_START_S','7.75'))
            end = float(os.environ.get('TABLE_APPROACH_END_S','8.45'))
            if start <= t < end:
                env.safety_config.velocity_gain_nm_per_radps[:] = base_velocity_gains * float(os.environ.get('TABLE_APPROACH_SERVO_SCALE','1.0'))
        if bool(getattr(getattr(ctl,"config",None),"include_torque_estimate",False)): kw["joint_torque_estimate"]=d.get("joint_torque_estimate")
        if (a.controller == 'vmc' and scenario == 'corner'
                and vmc_nominal_drive_stiffness is not None):
            recovery_start = float(os.environ.get(
                'CORNER_VMC_RECOVERY_START_S', 'inf'))
            recovery_end = float(os.environ.get(
                'CORNER_VMC_RECOVERY_END_S', 'inf'))
            recovery_scale = float(os.environ.get(
                'CORNER_VMC_RECOVERY_DRIVE_SCALE', '1.0'))
            if recovery_scale <= 0.0 or not np.isfinite(recovery_scale):
                raise ValueError('CORNER_VMC_RECOVERY_DRIVE_SCALE must be finite and positive')
            if recovery_end <= recovery_start:
                raise ValueError('CORNER_VMC_RECOVERY_END_S must be greater than recovery start')
            active_scale = (
                recovery_scale
                if recovery_start <= t < recovery_end
                else 1.0
            )
            ctl.baseline.drive_stiffness = (
                vmc_nominal_drive_stiffness * active_scale)
            # Preserve damping ratio while changing the virtual drive
            # stiffness: c scales with sqrt(k).
            ctl.baseline.drive_damping = (
                vmc_nominal_drive_damping * np.sqrt(active_scale))
        if a.controller == "teacher":
            act, teacher_contact_duration, teacher_contact_seen, _, _ = _privileged_corner_teacher_action(
                env, side, contact_duration_s=teacher_contact_duration,
                contact_seen=teacher_contact_seen,
            )
        elif ctl is None:
            act = np.zeros(7, dtype=float)
        else:
            act=ctl.act(d["joint_position"],d["joint_velocity"],d["nominal_twist"],**kw).bounded_filter_action.copy()
        privileged_label = None
        if a.record_privileged_labels:
            if scenario != "corner":
                raise ValueError("--record-privileged-labels currently supports the corner teacher only")
            privileged_label, label_contact_duration, label_contact_seen, _, _ = _privileged_corner_teacher_action(
                env, side, contact_duration_s=label_contact_duration,
                contact_seen=label_contact_seen,
            )
        # Optional frozen deployment-authority sweep for ESN ablations.  This
        # is a controller-level scalar, independent of contact/obstacle state;
        # it preserves the same proprioceptive observation and seven-channel
        # residual interface while allowing a fair post-training authority
        # study.  The default is exactly the checkpoint behaviour.
        if a.controller == "esn":
            authority_key = f"ESN_RESIDUAL_AUTHORITY_{scenario.upper()}"
            esn_authority = float(os.environ.get(
                authority_key, os.environ.get("ESN_RESIDUAL_AUTHORITY", "1.0")))
            if not np.isfinite(esn_authority) or esn_authority < 0.0:
                raise ValueError("ESN_RESIDUAL_AUTHORITY must be finite and non-negative")
            act[1:] = np.clip(act[1:] * esn_authority, -1.0, 1.0)
        # Once the finite-mass rod has fully withdrawn, let the learned
        # controller recover toward the nominal pre-grasp pose without
        # allowing a stale lateral residual to keep translating the hand.
        # This gate is time/protocol based (not vision or contact based) and
        # is exposed for an ablation sweep; the default remains conservative.
        push_rejoin_active = bool(
            a.controller in ("teacher", "vmc")
            and scenario == "push"
            and (push_rejoin_started or push_end_s <= t < grasp_time_s)
        )
        if push_rejoin_active:
            recovery_scale = float(os.environ.get("PUSH_RECOVERY_RESIDUAL_SCALE", "0.0"))
            act[1:] *= recovery_scale
            # Express both phases through the recorded slowdown action.  The
            # pass phase must remain compliant long enough for the rod to
            # produce a visible task-direction displacement.  Once the
            # proprioceptive departure/clearance gate starts track rejoin, a
            # separate scale restores WBC authority so the hand can return
            # while the rod is still held.  The legacy single-scale variable
            # remains the fallback for exact reproduction of older runs.
            legacy_slowdown_scale = float(os.environ.get(
                "PUSH_REJOIN_SLOWDOWN_SCALE", "0.0"))
            if push_rejoin_track_started:
                rejoin_slowdown_scale = float(os.environ.get(
                    "PUSH_REJOIN_TRACK_SLOWDOWN_SCALE",
                    str(legacy_slowdown_scale)))
            else:
                rejoin_slowdown_scale = float(os.environ.get(
                    "PUSH_REJOIN_PASS_SLOWDOWN_SCALE",
                    str(legacy_slowdown_scale)))
            act[0] *= float(np.clip(rejoin_slowdown_scale, 0.0, 1.0))
        # Before grasp, keep the learned lateral/orientation yield channels
        # available for a side impact, while suppressing only vertical yield
        # that could pull the hand away from the object.  ``off`` reproduces
        # the legacy all-channel clamp for a strict ablation.
        # This clamp is strictly pre-grasp.  The previous condition looked
        # only at the sign of nominal vz, so it also zeroed every VMC/MLP/ESN
        # residual during the post-grasp downward table-placement phase.
        # That silently converted the corner experiment back to bare WBC at
        # exactly the contact transition we intended to evaluate.
        if (t < grasp_time_s and float(d["nominal_twist"][2]) <= 0
                and not push_rejoin_active
                and not (scenario == "push" and a.controller in ("mlp", "esn"))):
            if pregrasp_yield_mode == "off":
                act[1:] *= 0.0
            elif pregrasp_yield_mode == "lateral":
                act[3] = 0.0
            elif pregrasp_yield_mode == "y_only":
                # The ball approaches along world -y.  Keep only the
                # matching translational yield channel; x/z/orientation yield
                # can steer the upstream link into the impactor.  The action
                # layout is [wbc_scale, vx, vy, vz, wx, wy, wz], so preserve
                # index 2 (vy) and clear the other five residual channels.
                act[1] = 0.0
                act[3:] = 0.0
            else:
                raise ValueError(f"unknown PREGRASP_YIELD_MODE={pregrasp_yield_mode!r}")
        # During the isolated sustained-rod test, the post-withdrawal phase
        # must visibly rejoin the nominal pre-grasp pose.  Build a bounded
        # proportional rejoin command from proprioceptive WBC pose/twist
        # error only; no rod pose, contact force, or release sensor is used.
        # The residual is blended after the optional stale-policy attenuation
        # so the teacher cannot keep pushing in the old lateral direction.
        if push_rejoin_active:
            recovery_kp = float(os.environ.get("PUSH_REJOIN_KP_S_INV", "0.65"))
            recovery_kd = float(os.environ.get("PUSH_REJOIN_KD", "0.10"))
            linear_limit = float(env.safety_config.maximum_linear_yield_mps)
            angular_limit = float(env.safety_config.maximum_angular_yield_radps)
            rejoin_pose_error = np.asarray(d["wbc_pose_error"][:3], dtype=float).copy()
            # While the rod is still extended, pass on the opposite side in
            # x before returning the visible z coordinate to its nominal
            # value. Once the rod withdraws, the ordinary nominal error is
            # used again, so this offset is temporary and bounded.
            if t < push_end_s:
                rejoin_pose_error[0] += push_rejoin_pass_offset_m
            desired_linear = recovery_kp * rejoin_pose_error \
                - recovery_kd * np.asarray(d["wbc_twist_error"][:3])
            if t < push_end_s and not push_rejoin_track_started:
                # Keep the pushed y coordinate compliant until the required
                # physical departure has actually occurred.
                desired_linear[1] = 0.0
            desired_angular = recovery_kp * np.asarray(d["wbc_pose_error"][3:]) \
                - recovery_kd * np.asarray(d["wbc_twist_error"][3:])
            rejoin_action = np.concatenate((
                desired_linear / max(linear_limit, 1.0e-9),
                desired_angular / max(angular_limit, 1.0e-9),
            ))
            rejoin_action = np.clip(rejoin_action, -1.0, 1.0)
            blend = float(os.environ.get("PUSH_REJOIN_BLEND", "0.85"))
            blend = float(np.clip(blend, 0.0, 1.0))
            act[1:] = np.clip((1.0 - blend) * act[1:] + blend * rejoin_action, -1.0, 1.0)
            # Do not leave the pass manoeuvre to a small residual position
            # error.  During the extended-hold interval command a bounded,
            # smooth +x velocity directly so the end effector visibly moves
            # around the rod before the rod retracts.  This is still a
            # proprioceptive teacher action: it uses only the WBC nominal
            # position and measured hand position, never rod pose/force.
            if t < push_end_s:
                pass_error_x = (
                    float(d["nominal_position"][0]) + push_rejoin_pass_offset_m
                    - float(d["ee_position"][0])
                )
                desired_pass_vx = float(np.clip(
                    push_rejoin_pass_kp_s_inv * pass_error_x,
                    -push_rejoin_pass_speed_mps,
                    push_rejoin_pass_speed_mps,
                ))
                act[1] = float(np.clip(
                    desired_pass_vx / max(linear_limit, 1.0e-9), -1.0, 1.0
                ))
                # At the same time, recover the pushed -y displacement back
                # toward the nominal path.  The x-side clearance is retained
                # so this does not drive the hand back into the still-
                # extended rod.  This makes the intended behavior explicit:
                # bypass laterally, then rejoin the task direction while the
                # external push is still active.
                track_error_y = (
                    float(d["nominal_position"][1])
                    - float(d["ee_position"][1])
                )
                if push_rejoin_track_started:
                    desired_track_vy = float(np.clip(
                        push_rejoin_track_kp_s_inv * track_error_y,
                        -push_rejoin_track_speed_mps,
                        push_rejoin_track_speed_mps,
                    ))
                    act[2] = float(np.clip(
                        desired_track_vy / max(linear_limit, 1.0e-9), -1.0, 1.0
                    ))
            # The final approach to the block is announced by the nominal
            # planner's downward task twist, which is part of the shared
            # student observation.  Stop the bypass/rejoin residual at that
            # observable phase transition so the open fingers do not sweep
            # the block sideways just before closing.  This deliberately
            # avoids rod pose, contact state, or a fixed withdrawal timer;
            # the zero action is saved in the teacher trace and must be
            # learned from the same nominal-twist cue by MLP and ESN.
            pregrasp_descent_threshold = float(os.environ.get(
                "PUSH_PREGRASP_DESCENT_THRESHOLD_MPS", "-0.002"))
            # The task planner schedules the final one-second descent; use
            # that shared phase boundary only to disambiguate it from the
            # earlier downward approach, which can have the same sign of
            # nominal vz while the rod interaction is still underway.
            pregrasp_descent_window_s = float(os.environ.get(
                "PUSH_PREGRASP_DESCENT_WINDOW_S", "1.10"))
            if (t >= grasp_time_s - pregrasp_descent_window_s
                    and float(d["nominal_twist"][2]) < pregrasp_descent_threshold):
                act[:] = 0.0
        # While the rod is still pressing, add a smooth tangential bypass
        # command instead of waiting for the external force to disappear.
        # The target is defined relative to the instantaneous nominal WBC
        # position, so this remains a bounded task-space action and does not
        # read rod pose, contact force, or any privileged obstacle state.
        if (a.controller in ("teacher", "vmc") and scenario == "push" and not push_rejoin_active
                and (push_contact_now or push_hit is not None) and t < push_end_s):
            bypass_index = 0 if push_bypass_axis == "x" else 2
            tangential_error = (
                float(d["nominal_position"][bypass_index]) + push_bypass_offset_m
                - float(d["ee_position"][bypass_index])
            )
            desired_bypass_v = float(np.clip(
                push_bypass_kp_s_inv * tangential_error,
                -push_bypass_speed_mps,
                push_bypass_speed_mps,
            ))
            bypass_action = desired_bypass_v / max(
                float(env.safety_config.maximum_linear_yield_mps), 1.0e-9
            )
            # Keep the y-yield generated by the physical push, while adding
            # only the orthogonal bypass needed to route around the rod.
            act[1 + bypass_index] = float(np.clip(bypass_action, -1.0, 1.0))
        # The auxiliary convex proxy is enabled only for the pre-grasp ball
        # impact.  After grasp, the exact hand STL remains active for the
        # thick-table contact while the ball proxy is removed from collision.
        if ball_proxy >= 0 and t >= fx.grasp_time_s and scenario == "combined":
            env.model.geom_contype[ball_proxy] = 0
            env.model.geom_conaffinity[ball_proxy] = 0
        # Approach the apron quasi-statically; a visual contact frame must
        # show the hand stopping at the face, not crossing it between control
        # updates.
        if scenario in ("combined", "corner") and 4.4 <= t <= 6.1: act *= .20
        if a.trace_output is not None:
            trace_command_actions.append(np.asarray(act, dtype=np.float32).copy())
        _,_,done,_,info=env.step(act); t=step*.04
        if a.trace_output is not None:
            # Grasp audit: record coupled finger joint positions, fingertip
            # separation, and contact forces against the free object.
            fids = [mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_JOINT, n)
                    for n in ("finger_joint1", "finger_joint2")]
            fq = [float(env.data.qpos[env.model.jnt_qposadr[j]]) if j >= 0 else float('nan') for j in fids]
            finger_geom_ids = [g for g in getattr(env, '_end_effector_geom_ids', [])
                               if (mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_BODY,
                                   int(env.model.geom_bodyid[g])) or '').endswith('finger')]
            finger_pos = [env.data.geom_xpos[g].copy() for g in finger_geom_ids]
            gap = float(np.linalg.norm(finger_pos[0] - finger_pos[-1])) if len(finger_pos) >= 2 else float('nan')
            contact_force = 0.0; contact_count = 0
            for ci in range(env.data.ncon):
                c = env.data.contact[ci]; pair = {int(c.geom1), int(c.geom2)}
                if target_geom in pair and any(g in pair for g in finger_geom_ids):
                    w = np.zeros(6); mujoco.mj_contactForce(env.model, env.data, ci, w)
                    contact_force += float(np.linalg.norm(w[:3])); contact_count += 1
            finger_qpos_trace.append(fq); finger_gap_trace.append(gap)
            grasp_contact_trace.append([contact_count, contact_force])
            grasp_target_pos_trace.append(env.data.geom_xpos[target_geom].copy())
            finger_pad_pos_trace.append([env.data.geom_xpos[g].copy() for g in finger_geom_ids])
        if a.trace_output is not None:
            # Record the action actually applied by the shared deployment
            # filter, not merely the pre-filter command.  This makes the
            # archive faithful for direct-action distillation and preserves
            # the raw command separately for auditability.
            applied = env.applied_action
            # The policy contract uses channel 0 as normalized slowdown
            # request (0=no slowdown, 1=max slowdown), while the filtered
            # action object stores the resulting WBC scale.  Convert back to
            # the policy coordinate system before writing the teacher target.
            min_scale = float(env.safety_config.minimum_wbc_scale)
            # In direct-ESN twist mode the physics consumes the filtered WBC
            # scale through ``_last_policy_wbc_scale`` and then restores the
            # public applied-action scale to 1.0 to avoid double-counting it
            # in the composed twist.  Use that effective scale here; reading
            # ``applied.wbc_scale`` would silently erase every slowdown label.
            effective_scale = float(getattr(
                env, "_last_policy_wbc_scale", applied.wbc_scale))
            slowdown = (1.0 - effective_scale) / max(1.0 - min_scale, 1e-9)
            applied_vec = np.concatenate((
                [float(np.clip(slowdown, 0.0, 1.0))],
                applied.cartesian_yield_twist[:3] /
                max(float(env.safety_config.maximum_linear_yield_mps), 1e-9),
                applied.cartesian_yield_twist[3:] /
                max(float(env.safety_config.maximum_angular_yield_radps), 1e-9),
            )).astype(np.float32)
            trace_actions.append(applied_vec)
            if privileged_label is not None:
                trace_privileged_labels.append(np.asarray(privileged_label, dtype=np.float32))
        actual_hand = env.data.xpos[env._hand_id].copy()
        target_position = env.data.xpos[env._target_body_id].copy()
        if scenario in ('corner', 'combined') and not placement_gate['released']:
            supported = any({int(c.geom1), int(c.geom2)} == {target_geom, top}
                            for c in env.data.contact[:env.data.ncon])
            target_speed = float(np.linalg.norm(env.data.cvel[env._target_body_id, 3:6]))
            target_extent_z = float(np.abs(env.data.geom_xmat[target_geom].reshape(3, 3)[2])
                                    @ env.model.geom_size[target_geom])
            target_extent_xy = np.abs(env.data.geom_xmat[target_geom].reshape(3, 3)[:2]) \
                @ env.model.geom_size[target_geom]
            target_bottom = float(env.data.geom_xpos[target_geom, 2] - target_extent_z)
            table_surface = float(env.data.geom_xpos[top, 2] + env.model.geom_size[top, 2])
            placement_margin_xy = env.model.geom_size[top, :2] \
                - np.abs(env.data.geom_xpos[target_geom, :2] - env.data.geom_xpos[top, :2]) \
                - target_extent_xy
            required_margin = float(os.environ.get('MIN_PLACEMENT_MARGIN_M', '0.0'))
            support_gap = float(target_bottom - table_surface)
            max_hover_gap = float(os.environ.get(
                'PLACEMENT_SETTLE_MAX_GAP_M', '0.008'))
            hover_required_s = float(os.environ.get(
                'PLACEMENT_HOVER_STABLE_S', '0.12'))
            safe_hover = (
                not supported
                and t > grasp_time_s
                and target_speed <= .025
                and 0.0 <= support_gap <= max_hover_gap
                and float(np.min(placement_margin_xy)) >= required_margin
            )
            placement_gate['hover_stable_s'] = (
                placement_gate['hover_stable_s'] + .04 if safe_hover else 0.0
            )
            placement_gate['max_hover_stable_s'] = max(
                placement_gate['max_hover_stable_s'],
                placement_gate['hover_stable_s'],
            )
            settle_gripper_command = float(os.environ.get(
                'PLACEMENT_SETTLE_GRIPPER_COMMAND', '0.0'))
            if (settle_gripper_command > 0.0
                    and placement_gate['hover_stable_s'] >= hover_required_s):
                placement_gate['settle_relaxation_active'] = True
            # Reject touching the tabletop underside/side as support.
            stable = (supported and target_speed <= .025 and t > grasp_time_s
                      and target_bottom >= table_surface - .0005
                      and float(np.min(placement_margin_xy)) >= required_margin)
            placement_gate['stable_s'] = placement_gate['stable_s'] + .04 if stable else 0.
            placement_gate['max_stable_s'] = max(
                placement_gate['max_stable_s'], placement_gate['stable_s'])
            placement_gate['last_supported'] = bool(supported)
            placement_gate['last_target_speed_mps'] = target_speed
            placement_gate['last_target_bottom_m'] = target_bottom
            placement_gate['last_table_surface_m'] = table_surface
            placement_gate['last_margin_xy_m'] = placement_margin_xy.tolist()
            placement_gate['last_support_gap_m'] = support_gap
            if placement_gate['stable_s'] >= .24:
                placement_gate['released'] = True
                placement_gate['release_time_s'] = float(env.data.time)
        if os.environ.get("DEBUG_GRASP", "0") == "1" and 7.3 <= t <= 9.2 and step % 5 == 0:
            partners=[]
            for ci in range(env.data.ncon):
                cc=env.data.contact[ci]; ids={int(cc.geom1),int(cc.geom2)}
                if target_geom in ids:
                    other=next(iter(ids-{target_geom}))
                    partners.append(mujoco.mj_id2name(env.model,mujoco.mjtObj.mjOBJ_GEOM,other) or str(other))
            print(f"grasp_trace t={t:.2f} hand={actual_hand.tolist()} target={target_position.tolist()} ctrl={float(env.data.ctrl[7]):.4f} contacts={partners}", flush=True)
        max_target_lift = max(max_target_lift, float(target_position[2] - initial_target_z))
        # Reuse the already evaluated task-space command rather than sampling
        # the reference a second time.  Both are Cartesian positions; using
        # the diagnostics value makes their time index explicit for trace
        # auditing and avoids accidental divergence if a stateful reference
        # is introduced later.
        nominal_hand = np.asarray(d["nominal_position"], dtype=float)
        ee_error = float(np.linalg.norm(actual_hand - nominal_hand))
        error_trace.append((t, ee_error))
        hand_trace.append((t, actual_hand.copy()))
        if a.trace_output is not None:
            trace_ee_position.append(actual_hand.astype(np.float32, copy=True))
            trace_nominal_position.append(nominal_hand.astype(np.float32, copy=True))
            trace_ee_error.append(ee_error)
        if len(hand_trace) >= 2:
            speed_trace.append(float(np.linalg.norm((hand_trace[-1][1] - hand_trace[-2][1]) / 0.04)))
        if getattr(env, "physics_torque_history", None):
            torque_trace.append(np.asarray(env.physics_torque_history[-1], dtype=float).copy())
        if os.environ.get("DEBUG_PUSH_TRACE", "0") == "1" and step % 25 == 0:
            rod_joint = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_JOINT, "push_rod_slide")
            rod_q = float(env.data.qpos[env.model.jnt_qposadr[rod_joint]]) if rod_joint >= 0 else float("nan")
            rod_x = env.data.geom_xpos[push_rod].copy() if push_rod >= 0 else np.full(3, np.nan)
            applied_yield = np.asarray(d.get("cartesian_yield_twist", np.zeros(6)), dtype=float)
            print(f"trace t={t:.2f} hand={actual_hand.tolist()} nominal={d['nominal_position'].tolist()} "
                  f"yield={applied_yield[:3].tolist()} contact={push_contact_now} "
                  f"rejoin={push_rejoin_started} rod={rod_x.tolist()} rod_q={rod_q:.5f}", flush=True)
        if (ball_start_s - 0.10) <= t <= (ball_start_s + ball_press + ball_retract + 0.80):
            max_ball_ee_deviation = max(max_ball_ee_deviation, ee_error)
        if push_start_s <= t <= push_end_s:
            max_push_ee_deviation = max(max_push_ee_deviation, ee_error)
        elif push_end_s < t <= (first_side if first_side is not None else push_end_s + 0.80):
            max_recovery_ee_error = max(max_recovery_ee_error, ee_error)
        for i in range(env.data.ncon):
            c=env.data.contact[i]; pair={int(c.geom1),int(c.geom2)}
            force=np.zeros(6); mujoco.mj_contactForce(env.model, env.data, i, force)
            if ball in pair:
                other=int(c.geom2) if int(c.geom1)==ball else int(c.geom1); n=mujoco.mj_id2name(env.model,mujoco.mjtObj.mjOBJ_GEOM,other)
                if n: ball_names.add(n); ball_hit=t if ball_hit is None else ball_hit
                force_norm=float(np.linalg.norm(force[:3])); peak_ball_force=max(peak_ball_force,force_norm); ball_contact_duration += 0.0005
            if side in pair:
                other=int(c.geom2) if int(c.geom1)==side else int(c.geom1); n=mujoco.mj_id2name(env.model,mujoco.mjtObj.mjOBJ_GEOM,other)
                if n: side_names.add(n)
                other_body=int(env.model.geom_bodyid[other]); body_name=mujoco.mj_id2name(env.model,mujoco.mjtObj.mjOBJ_BODY,other_body)
                if body_name: side_bodies.add(body_name)
                first_side=t if first_side is None else first_side
                pen=max(0.,-float(c.dist)); max_side_pen=max(max_side_pen,pen)
                if (mujoco.mj_id2name(env.model,mujoco.mjtObj.mjOBJ_BODY,other_body) or "") not in allowed_compliance_bodies:
                    max_upstream_pen=max(max_upstream_pen,pen)
            if top >= 0 and target_geom >= 0 and pair == {top, target_geom}:
                target_top_contact = True
                if target_top_first_contact_s is None:
                    target_top_first_contact_s = t
            if push_rod >= 0 and push_rod in pair:
                other=int(c.geom2) if int(c.geom1)==push_rod else int(c.geom1); n=mujoco.mj_id2name(env.model,mujoco.mjtObj.mjOBJ_GEOM,other)
                if n: push_names.add(n)
                if other in getattr(env, "_end_effector_geom_ids", []):
                    push_hit=t if push_hit is None else push_hit
                    peak_push_force=max(peak_push_force,float(np.linalg.norm(force[:3])))
                    push_contact_duration += 0.04
                    max_push_pen=max(max_push_pen,max(0.,-float(c.dist)))
        if renderer is not None and step%max(1,round(1./(a.fps*.04)))==0:
            renderer.update_scene(env.data,camera=cam); overview=Image.fromarray(renderer.render()).convert("RGB")
            renderer.update_scene(env.data,camera=under_cam); detail=Image.fromarray(renderer.render()).convert("RGB")
            im=Image.new("RGB",(overview.width+detail.width,overview.height)); im.paste(overview,(0,0)); im.paste(detail,(overview.width,0)); dr=ImageDraw.Draw(im)
            method_title={"paper_mpc":"paper-MPC/WBC","vmc":"VMC","mlp":"MLP","esn":"ESN","teacher":"privileged analytic teacher"}[a.controller]
            titles={"combined":f"{method_title} combined compliance demo","ball":f"{method_title} isolated ball impact","push":f"{method_title} isolated rod push","corner":f"{method_title} isolated table-corner contact"}
            subtitles={"combined":"ball impact + rod push + thick table corner","ball":"finite-mass impact, release and free recovery","push":"press, hold, full withdrawal and free recovery","corner":"pick below table, compliant apron contact and placement"}
            dr.rectangle((0,0,im.width,78),fill=(12,17,27)); dr.text((12,7),titles[scenario],fill="white",font=ft(22))
            dr.text((12,35),f"{subtitles[scenario]}   t={t:.2f} s",fill=(205,220,238),font=ft(14))
            push_active = push_start_s <= t < push_end_s
            object_lifted_now = float(target_position[2] - initial_target_z) >= 0.08
            if scenario == "ball":
                st = "OBJECT LIFTED" if object_lifted_now else ("GRASPING / LIFT" if t >= grasp_time_s else ("BALL IMPACT / RECOVERY" if ball_hit is not None else "APPROACH"))
            elif scenario == "push":
                teacher_rejoin = a.controller in ("teacher", "vmc") and push_rejoin_started
                st = "OBJECT LIFTED" if object_lifted_now else ("GRASPING / LIFT" if t >= grasp_time_s else ("COMPLIANT REJOIN" if teacher_rejoin or t >= push_end_s else ("ROD PUSH + TANGENTIAL BYPASS" if push_active and push_hit is not None else ("ROD PRESS" if push_active else "APPROACH"))))
            elif scenario == "corner":
                st = "OBJECT PLACED / SETTLING" if target_top_contact and t >= 8.3 else ("APRON CONTACT" if first_side is not None and t>=first_side else "APPROACH / GRASP")
            else: st="APRON CONTACT" if first_side is not None and t>=first_side else ("ROD PUSH" if push_active else ("BALL IMPACT" if ball_hit is not None else "APPROACH / GRASP"))
            dr.text((12,57),f"{st}   top={top>=0} side={side>=0}",fill=(255,205,90) if first_side is not None else (180,215,190),font=ft(14)); frames.append(np.asarray(im))
        step+=1
    final_target_position = env.data.xpos[env._target_body_id].copy()
    final_hand_position = env.data.xpos[env._hand_id].copy()
    final_target_speed = float(np.linalg.norm(env.data.cvel[env._target_body_id, 3:6]))
    final_gripper_command = float(env.data.ctrl[7])
    top_surface_z = None
    final_target_bottom_z = None
    final_target_on_top_xy = False
    final_placement_margin_xy = None
    final_placement_min_margin = None
    final_target_rotation = None
    final_target_extent_xyz = None
    final_hand_rotation = None
    final_hand_to_target_world = None
    if top >= 0 and target_geom >= 0:
        top_position = env.data.geom_xpos[top].copy()
        top_surface_z = float(top_position[2] + env.model.geom_size[top][2])
        target_rotation = env.data.geom_xmat[target_geom].reshape(3, 3)
        final_target_rotation = target_rotation.copy()
        final_target_extent_xyz = np.abs(target_rotation) @ env.model.geom_size[target_geom]
        # The target may be pitched during placement.  Use the projected
        # world-z half extent, exactly as the online release gate does,
        # rather than the unrotated local z half-size.
        final_target_bottom_z = float(
            env.data.geom_xpos[target_geom][2] - final_target_extent_xyz[2]
        )
        target_extent_xy = np.abs(target_rotation[:2]) @ env.model.geom_size[target_geom]
        final_placement_margin_xy = (
            env.model.geom_size[top, :2]
            - np.abs(env.data.geom_xpos[target_geom, :2] - top_position[:2])
            - target_extent_xy
        )
        final_placement_min_margin = float(np.min(final_placement_margin_xy))
        final_target_on_top_xy = bool(
            final_placement_min_margin >= 0.0
        )
        final_hand_rotation = env.data.xmat[env._hand_id].reshape(3, 3).copy()
        final_hand_to_target_world = (
            env.data.geom_xpos[target_geom] - env.data.xpos[env._hand_id]
        ).copy()
    object_grasped_and_lifted = bool(
        max_target_lift >= 0.10
        and float(np.linalg.norm(final_target_position - final_hand_position)) < 0.16
    )
    object_placed_on_table = bool(
        scenario == "corner"
        and target_top_contact
        and final_target_on_top_xy
        and top_surface_z is not None
        and final_target_bottom_z is not None
        and abs(final_target_bottom_z - top_surface_z) <= 0.020
        and final_target_speed <= 0.08
        and final_gripper_command >= 0.050
        and final_placement_min_margin is not None
        and final_placement_min_margin >= float(os.environ.get('MIN_PLACEMENT_MARGIN_M', '0.0'))
    )
    if renderer is not None:
        renderer.close()
    from push_numerics_20260916 import snapshot_numerics
    numerics_snapshot = snapshot_numerics(env.model)
    env.close(); a.output.parent.mkdir(parents=True,exist_ok=True)
    if a.trace_output is not None:
        a.trace_output.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            a.trace_output,
            joint_position=np.asarray(trace_q, dtype=np.float32),
            joint_velocity=np.asarray(trace_qdot, dtype=np.float32),
            wbc_task_twist=np.asarray(trace_twist, dtype=np.float32),
            pose_error=np.asarray(trace_pose_error, dtype=np.float32),
            wbc_twist_error=np.asarray(trace_twist_error, dtype=np.float32),
            teacher_action=np.asarray(trace_actions, dtype=np.float32),
            commanded_teacher_action=np.asarray(trace_command_actions, dtype=np.float32),
            ee_position=np.asarray(trace_ee_position, dtype=np.float32),
            nominal_position=np.asarray(trace_nominal_position, dtype=np.float32),
            ee_tracking_error_m=np.asarray(trace_ee_error, dtype=np.float32),
            **({"privileged_teacher_action": np.asarray(trace_privileged_labels, dtype=np.float32)}
               if a.record_privileged_labels else {}),
            trace_schema_version=np.asarray(3,dtype=np.int32),
            action_semantics=np.asarray('normalized_action_after_shared_filter'),
            command_time_s=np.arange(len(trace_actions),dtype=np.float64)*.04,
            joint_torque_estimate=np.asarray(trace_joint_torque, dtype=np.float32),
            finger_joint_qpos=np.asarray(finger_qpos_trace, dtype=np.float32),
            finger_gap_m=np.asarray(finger_gap_trace, dtype=np.float32),
            grasp_contact_count_force=np.asarray(grasp_contact_trace, dtype=np.float32),
            grasp_target_position=np.asarray(grasp_target_pos_trace, dtype=np.float32),
            grasp_finger_pad_positions=np.asarray(finger_pad_pos_trace, dtype=np.float32),
        )
    if not a.no_render:
        iio.imwrite(a.output,np.stack(frames),duration=1000./a.fps,loop=0)
    # Prefer the environment's physics-substep audit over the renderer-rate
    # fallback above.  This is the authoritative evidence for sustained
    # contact and non-penetration.
    push_hit = info.get("push_rod_first_contact_s", push_hit)
    peak_push_force = float(info.get("push_rod_peak_force_n", peak_push_force))
    peak_push_point_force = peak_push_force
    push_force_metric = os.environ.get("PUSH_FORCE_METRIC", "legacy_point")
    if push_force_metric == "ee_resultant":
        peak_push_force = float(info.get("push_rod_peak_resultant_force_n", 0.))
    elif push_force_metric == "robot_resultant":
        peak_push_force = float(info.get("push_rod_peak_all_robot_resultant_force_n", 0.))
    elif push_force_metric != "legacy_point":
        raise ValueError("Unknown PUSH_FORCE_METRIC")
    push_contact_duration = float(info.get("push_rod_contact_duration_s", push_contact_duration))
    push_contact_bout_count = int(info.get("push_rod_contact_bout_count", 0))
    push_contact_span = info.get("push_rod_contact_span_s")
    push_contact_duty_cycle = float(info.get("push_rod_contact_duty_cycle", 0.0))
    max_push_pen = float(info.get("peak_push_rod_penetration_m", max_push_pen))
    push_last_contact_s = info.get("push_rod_last_contact_s")
    push_baseline = None
    push_signed_displacement = 0.0
    push_max_actual_displacement = 0.0
    push_recovery_to_baseline = None
    push_measured_precontact_baseline = None
    if push_hit is not None and push_last_contact_s is not None:
        baseline_samples = [
            p for t,p in hand_trace if push_hit - 0.30 <= t <= push_hit - 0.08
        ]
        contact_samples = [
            p for t,p in hand_trace if push_hit <= t <= push_last_contact_s
        ]
        recovery_samples = [
            p for t,p in hand_trace if push_end_s + 0.30 <= t < grasp_time_s
        ]
        if baseline_samples and contact_samples:
            # Use the nominal hold waypoint as the recovery reference.  The
            # measured pre-contact hand is still logged separately, but it
            # is descending at the instant of impact and therefore would
            # incorrectly count normal settling as a recovery failure.
            push_measured_precontact_baseline = np.mean(np.stack(baseline_samples), axis=0)
            push_baseline = np.asarray(env.reference.sample(push_end_s)[0], dtype=float)
            push_axis = np.array([0.0, -1.0, 0.0])
            deltas = np.stack(contact_samples) - push_baseline
            push_signed_displacement = float(np.max(deltas @ push_axis))
            push_max_actual_displacement = float(np.max(np.linalg.norm(deltas, axis=1)))
            if recovery_samples:
                push_recovery_to_baseline = float(np.mean([
                    np.linalg.norm(p - push_baseline) for p in recovery_samples[-5:]
                ]))
    apron_gap_after_push = None if first_side is None else float(first_side - push_end_s)
    release_s = fx.rod_start_time_s + ball_press + ball_retract if scenario == "ball" else push_end_s
    # In the raised-clearance push protocol the final one-second segment
    # before gripper closure is an intentional downward grasp approach.  Its
    # vertical tracking lag belongs to whole-task tracking metrics, not to
    # recovery from the earlier lateral rod disturbance.  End the dedicated
    # push recovery window before that planned descent begins.
    push_recovery_window_end_s = grasp_time_s
    if (scenario == "push"
            and float(os.environ.get("PREGRASP_CLEARANCE_M", "0.0")) > 0.0):
        push_recovery_window_end_s = grasp_time_s - 1.0
    recovery = [
        (t,e) for t,e in error_trace
        if t >= release_s
        and (scenario != "push" or t < push_recovery_window_end_s)
    ]
    final_recovery_error = float(np.mean([e for _,e in recovery[-5:]])) if recovery else None
    recovery_time = None
    stable_samples=max(1,int(round(0.20/0.04)))
    for i in range(max(0,len(recovery)-stable_samples+1)):
        if all(e <= 0.010 for _,e in recovery[i:i+stable_samples]):
            recovery_time=float(recovery[i][0]-release_s); break
    # With a raised pre-grasp waypoint the nominal trajectory intentionally
    # descends after rod withdrawal.  Comparing the final hand to the old
    # fixed elevated point falsely labels correct trajectory re-entry as a
    # recovery failure.  In that protocol use the time-varying nominal WBC
    # tracking error; otherwise retain the historical fixed-point metric.
    push_recovery_metric = (
        final_recovery_error
        if scenario == 'push' and float(os.environ.get('PREGRASP_CLEARANCE_M', '0.0')) > 0.0
        else push_recovery_to_baseline
    )
    peak_impactor_pen = float(info.get("peak_impactor_penetration_m", 0.0))
    # The ball impact lasts only a few controller frames.  The renderer-rate
    # contact loop can legitimately miss it, so use the authoritative
    # physics-substep audit for event time, force, impulse and duration.
    if scenario == "ball":
        detail = info.get("peak_impactor_contact_detail") or {}
        if detail.get("geom1") or detail.get("geom2"):
            for name in (detail.get("geom1"), detail.get("geom2")):
                if name and name != "rod_geom":
                    ball_names.add(name)
        ball_hit = info.get("impactor_first_contact_s", ball_hit)
        peak_ball_force = float(info.get("peak_contact_force_n", peak_ball_force))
        ball_contact_duration = float(
            info.get("impactor_contact_duration_s", ball_contact_duration))
    if scenario == "ball":
        scenario_success=bool(ball_hit is not None and max_ball_ee_deviation >= 0.020
                               and object_grasped_and_lifted and info.get("geometry_valid",False)
                               and peak_impactor_pen <= 5e-4)
    elif scenario == "push":
        scenario_success=bool(push_hit is not None and push_contact_duration >= 1.20 and push_contact_span is not None and push_contact_span >= 1.50 and push_contact_duty_cycle >= 0.70 and push_signed_displacement >= 0.030 and push_recovery_metric is not None and push_recovery_metric <= 0.012 and object_grasped_and_lifted and max_push_pen <= 5e-4 and max_upstream_pen <= 1e-8)
    elif scenario == "corner":
        scenario_success=bool(object_placed_on_table and first_side is not None and max_side_pen <= 5e-4 and max_upstream_pen <= 1e-8)
    else:
        scenario_success=bool(info.get("task_success",False))
    failure_reasons=[]
    if scenario == "push" and not info.get("push_geometry_valid", False):
        scenario_success = False
        failure_reasons.append("push_full_robot_geometry_invalid")
    if not scenario_success:
        if scenario == "ball":
            if ball_hit is None: failure_reasons.append("no_hand_contact")
            if peak_impactor_pen > 5e-4: failure_reasons.append("penetration_over_0.5mm")
            if max_ball_ee_deviation < 0.020: failure_reasons.append("insufficient_yield")
            if not object_grasped_and_lifted: failure_reasons.append("grasp_or_lift_failure")
        elif scenario == "push":
            if push_hit is None: failure_reasons.append("no_push_contact")
            if push_contact_duration < 1.20: failure_reasons.append("short_contact")
            if push_contact_span is None or push_contact_span < 1.50: failure_reasons.append("short_contact_span")
            if push_contact_duty_cycle < 0.70: failure_reasons.append("low_contact_duty_cycle")
            if push_signed_displacement < 0.030: failure_reasons.append("insufficient_displacement")
            if push_recovery_metric is None or push_recovery_metric > 0.012: failure_reasons.append("recovery_over_12mm")
            if not object_grasped_and_lifted: failure_reasons.append("grasp_or_lift_failure")
            if max_push_pen > 5e-4: failure_reasons.append("penetration_over_0.5mm")
        elif scenario == "corner":
            if not object_grasped_and_lifted: failure_reasons.append("grasp_or_lift_failure")
            if first_side is None: failure_reasons.append("no_apron_contact")
            if not object_placed_on_table: failure_reasons.append("placement_failure")
            if (final_placement_min_margin is None or
                    final_placement_min_margin < float(os.environ.get('MIN_PLACEMENT_MARGIN_M', '0.0'))):
                failure_reasons.append("insufficient_placement_margin")
            if max_side_pen > 5e-4: failure_reasons.append("penetration_over_0.5mm")
            if max_upstream_pen > 1e-8: failure_reasons.append("upstream_contact")
    valid_contact = bool(
        (scenario != "ball" or (ball_hit is not None and peak_impactor_pen <= 5e-4)) and
        (scenario != "push" or (push_hit is not None and max_push_pen <= 5e-4)) and
        (scenario != "corner" or (first_side is not None and max_side_pen <= 5e-4 and max_upstream_pen <= 1e-8))
    )
    err_values = np.asarray([e for _, e in error_trace], dtype=float)
    speed_values = np.asarray(speed_trace, dtype=float)
    torque_values = np.stack(torque_trace) if torque_trace else np.zeros((0, 7), dtype=float)
    torque_norm_values = np.max(np.abs(torque_values), axis=1) if torque_values.size else np.zeros(0)
    out={"protocol":f"isolated_{scenario}_compliance" if scenario != "combined" else "thick_table_corner_with_push_rod","scenario":scenario,"controller":a.controller,"seed":a.seed,"scenario_success":scenario_success,"valid_contact":valid_contact,"failure_reasons":failure_reasons,"task_success":bool(info.get("task_success",False)),"record_duration_s":float(a.simulation_time),"grasp_time_s":float(grasp_time_s),"object_grasped_and_lifted":object_grasped_and_lifted,"max_target_lift_m":max_target_lift,"object_placed_on_table":object_placed_on_table,"target_top_contact":target_top_contact,"target_top_first_contact_s":target_top_first_contact_s,"top_surface_z_m":top_surface_z,"final_target_bottom_z_m":final_target_bottom_z,"final_target_speed_mps":final_target_speed,"final_gripper_command_m":final_gripper_command,"ball_contact_geoms":sorted(ball_names),"ball_first_contact_s":ball_hit,"peak_ball_force_n":peak_ball_force,"ball_contact_duration_s":ball_contact_duration,"ball_window_max_ee_deviation_m":max_ball_ee_deviation,"peak_impactor_penetration_m":peak_impactor_pen,"ball_recovery_start_s":ball_recovery_start_s,"ball_recovery_end_s":ball_recovery_end_s,"ball_recovery_wbc_gain_scale":ball_recovery_gain_scale,"push_rod_stroke_m":float(os.environ.get("PUSH_ROD_STROKE_M","0.085")),"push_lateral_gain_scale":float(os.environ.get("PUSH_LATERAL_GAIN_SCALE","0.15")),"push_recovery_wbc_gain_scale":float(os.environ.get("PUSH_RECOVERY_WBC_GAIN_SCALE","2.50")),"push_recovery_residual_scale":float(os.environ.get("PUSH_RECOVERY_RESIDUAL_SCALE","0.0")),"push_rejoin_clearance_m":float(os.environ.get("PUSH_REJOIN_CLEARANCE_M","0.030")),"push_rejoin_start_s":push_rejoin_start_s,"push_rejoin_track_start_s":push_rejoin_track_start_s,"push_rejoin_pass_offset_m":float(os.environ.get("PUSH_REJOIN_PASS_OFFSET_M","0.100")),"push_rejoin_track_kp_s_inv":float(os.environ.get("PUSH_REJOIN_TRACK_KP_S_INV","2.00")),"push_rejoin_blend":float(os.environ.get("PUSH_REJOIN_BLEND","0.85")),"push_contact_geoms":sorted(push_names),"push_first_contact_s":push_hit,"push_window_end_s":push_end_s,"apron_gap_after_push_s":apron_gap_after_push,"push_table_phase_separated":bool(apron_gap_after_push is not None and apron_gap_after_push >= 0.20),"peak_push_force_n":peak_push_force,"push_contact_duration_s":push_contact_duration,"push_contact_span_s":push_contact_span,"push_contact_duty_cycle":push_contact_duty_cycle,"push_contact_bout_count":push_contact_bout_count,"push_signed_actual_displacement_m":push_signed_displacement,"push_max_actual_displacement_m":push_max_actual_displacement,"push_recovery_to_precontact_baseline_m":push_recovery_to_baseline,"push_precontact_measured_baseline_position_m":None if push_measured_precontact_baseline is None else push_measured_precontact_baseline.tolist(),"push_precontact_baseline_position_m":None if push_baseline is None else push_baseline.tolist(),"max_push_penetration_m":max_push_pen,"push_window_max_ee_deviation_m":max_push_ee_deviation,"post_push_recovery_window_max_ee_error_m":max_recovery_ee_error,"release_time_s":release_s,"final_recovery_error_m":final_recovery_error,"recovery_time_to_10mm_s":recovery_time,"trace_output":None if a.trace_output is None else str(a.trace_output),"apron_contact_geoms":sorted(side_names),"apron_contact_bodies":sorted(side_bodies),"first_apron_contact_s":first_side,"max_apron_penetration_m":max_side_pen,"max_upstream_penetration_m":max_upstream_pen,"end_effector_only_contact":bool(max_upstream_pen <= 1e-8),"geometry_valid":bool(info.get("geometry_valid",False) and (scenario != "push" or max_push_pen <= 5e-4)),"track_error_rmse_m":float(np.sqrt(np.mean(err_values**2))) if err_values.size else None,"track_error_p95_m":float(np.percentile(err_values,95)) if err_values.size else None,"track_error_peak_m":float(np.max(err_values)) if err_values.size else None,"ee_speed_peak_mps":float(np.max(speed_values)) if speed_values.size else None,"ee_speed_p95_mps":float(np.percentile(speed_values,95)) if speed_values.size else None,"torque_rms_nm":float(np.sqrt(np.mean(torque_values**2))) if torque_values.size else None,"torque_p95_nm":float(np.percentile(torque_norm_values,95)) if torque_norm_values.size else None,"terminal_info":info,"gif":str(a.output)}
    # ``release_s`` denotes withdrawal of the disturbance fixture and is the
    # recovery anchor for the ball/push protocols.  In the corner protocol it
    # is not the gripper release time; reporting it under the generic
    # ``release_time_s`` key previously produced the misleading value 2.95 s
    # even though the state-based placement gate released at about 10.28 s.
    # Keep both events explicit and make the legacy key mean the task-relevant
    # release for each protocol.
    placement_release_time_s = placement_gate.get('release_time_s')
    out['disturbance_release_time_s'] = float(release_s)
    out['placement_release_time_s'] = placement_release_time_s
    out['release_time_s'] = (
        placement_release_time_s
        if scenario in ('corner', 'combined')
        else float(release_s)
    )
    out['final_placement_margin_xy_m'] = (
        None if final_placement_margin_xy is None else final_placement_margin_xy.tolist()
    )
    out['final_placement_min_margin_m'] = final_placement_min_margin
    out['final_target_rotation_world'] = (
        None if final_target_rotation is None else final_target_rotation.tolist()
    )
    out['final_target_projected_half_extent_xyz_m'] = (
        None if final_target_extent_xyz is None else final_target_extent_xyz.tolist()
    )
    out['final_hand_rotation_world'] = (
        None if final_hand_rotation is None else final_hand_rotation.tolist()
    )
    out['final_hand_to_target_world_m'] = (
        None if final_hand_to_target_world is None else final_hand_to_target_world.tolist()
    )
    out['required_placement_margin_m'] = float(
        os.environ.get('MIN_PLACEMENT_MARGIN_M', '0.0')
    )
    out['push_max_task_departure_m'] = push_max_task_departure_m
    out['push_in_hold_rejoin_complete_s'] = push_in_hold_rejoin_complete_s
    out['push_hold_end_s'] = push_start_s + push_press_s + push_hold_s
    out['push_recovery_window_end_s'] = push_recovery_window_end_s
    out['push_rejoin_delay_s'] = float(os.environ.get('PUSH_REJOIN_DELAY_S', '0.55'))
    out['push_recovery_metric_m'] = push_recovery_metric
    out['physics_audit'] = getattr(env, 'physics_audit', {})
    out['placement_release_gate'] = placement_gate
    out['release_supervisor_uses_simulator_state'] = scenario in ('corner', 'combined')
    out['peak_command_torque_nm'] = info.get('peak_torque_nm')
    out['hold_debug'] = hold_debug
    out['runtime_collision_debug'] = runtime_collision_debug
    out['simulation_numerics'] = numerics_snapshot
    out['push_force_metric'] = push_force_metric
    out['peak_push_contact_point_force_n'] = peak_push_point_force
    out['peak_push_ee_resultant_force_n'] = float(info.get('push_rod_peak_resultant_force_n', 0.))
    out['peak_push_all_robot_resultant_force_n'] = float(info.get('push_rod_peak_all_robot_resultant_force_n', 0.))
    out['reproducibility_manifest'] = {
        'argv': list(sys.argv),
        'environment': {k: os.environ[k] for k in sorted(os.environ)
                        if k.startswith(('TABLE_', 'PLACE_', 'PLACEMENT_',
                                         'MIN_PLACEMENT_', 'CORNER_VMC_',
                                         'RIGID_', 'BALL_', 'PUSH_', 'INIT_',
                                         'PREGRASP_', 'POSTGRASP_', 'ISOLATED_',
                                         'GRIPPER_', 'ESN_', 'MUJOCO_',
                                         'EXT_TABLE_', 'THICK_TABLE'))},
        'renderer_path': str(Path(__file__).resolve()),
        'renderer_sha256': _sha256_file(Path(__file__).resolve()),
        'env_path': str(Path(__file__).with_name('audited_velocity_env.py').resolve()),
        'env_sha256': _sha256_file(Path(__file__).with_name('audited_velocity_env.py').resolve()),
        'model_path': None if a.esn is None else str(a.esn.resolve()),
        'model_sha256': None if a.esn is None else _sha256_file(a.esn.resolve()),
        'trace_schema_version': 3,
    }
    audit = out['physics_audit']
    out['legacy_scenario_success'] = out['scenario_success']
    if scenario == 'corner':
        penetration = audit.get('max_robot_table_penetration_m')
        out['max_apron_penetration_m'] = penetration
        out['peak_table_contact_pair_force_n'] = audit.get('peak_robot_table_pair_force_n')
        physics_valid = penetration is not None and penetration <= 5e-4
        out['geometry_valid'] = bool(out['geometry_valid'] and physics_valid)
        out['valid_contact'] = bool(out['valid_contact'] and physics_valid)
        out['scenario_success'] = bool(out['scenario_success'] and physics_valid)
        if not physics_valid:
            out['failure_reasons'].append('physics_step_table_penetration_or_missing_audit')
    safe_out = _json_safe(out)
    a.output.with_suffix(".json").write_text(json.dumps(safe_out,indent=2,allow_nan=False)+"\n")
    print(json.dumps(safe_out),flush=True)
if __name__=="__main__": main()
