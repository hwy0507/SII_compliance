"""Render the first fixed-base FR3 tabletop nominal-control demo."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import imageio.v3 as iio
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .contracts import FR3Waypoint
from .mujoco_env import FR3MuJoCoEnv
from .nominal_controller import FR3NominalVelocityServo
from .grasp_latch import MuJoCoGraspLatch
from .collision_checker import FR3SweptVolumeChecker
from .receding_horizon import RecedingHorizonSupervisor
from .scene_belief import WristSceneBeliefEstimator
from .wrist_camera import WristRGBDCamera, VelocityAwareViewScheduler, depth_preview


HOME = np.array([0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785], dtype=np.float64)


@dataclass(frozen=True)
class DemoSegment:
    duration_s: float
    q: np.ndarray
    gripper_m: float
    phase: str


@dataclass(frozen=True)
class CandidatePlan:
    name: str
    segments: tuple[DemoSegment, ...]
    target: np.ndarray
    waypoint_diagnostics: tuple[dict[str, object], ...]
    coarse_report: object
    path_length_rad: float


def look_at_quaternion(position: np.ndarray, look_at: np.ndarray) -> np.ndarray:
    """Return a hand orientation whose local +Z axis points at ``look_at``."""

    forward = np.asarray(look_at, dtype=np.float64) - np.asarray(position, dtype=np.float64)
    if np.linalg.norm(forward) < 1.0e-9:
        forward = np.array([0.0, 0.0, -1.0], dtype=np.float64)
    forward /= np.linalg.norm(forward)
    up = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    if abs(float(np.dot(up, forward))) > 0.95:
        up = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    y_axis = up - np.dot(up, forward) * forward
    y_axis /= max(np.linalg.norm(y_axis), 1.0e-9)
    x_axis = np.cross(y_axis, forward)
    x_axis /= max(np.linalg.norm(x_axis), 1.0e-9)
    rotation = np.column_stack((x_axis, y_axis, forward))
    quaternion = np.zeros(4, dtype=np.float64)
    mujoco.mju_mat2Quat(quaternion, rotation.reshape(-1))
    return quaternion


def solve_pose_ik(
    env: FR3MuJoCoEnv,
    body_id: int,
    target_position: np.ndarray,
    target_quaternion: np.ndarray,
    seed: np.ndarray,
    orientation_weight: float = 0.75,
) -> np.ndarray:
    """Damped least-squares 6D IK for a hand pose and wrist-camera view."""

    q = np.asarray(seed, dtype=np.float64).copy()
    lower = env.model.jnt_range[env.joint_ids, 0]
    upper = env.model.jnt_range[env.joint_ids, 1]
    for _ in range(160):
        env.data.qpos[env.qpos_adrs] = q
        mujoco.mj_forward(env.model, env.data)
        position_error = np.asarray(target_position, dtype=np.float64) - env.data.xpos[body_id]
        current_rotation = env.data.xmat[body_id].reshape(3, 3)
        target_rotation = np.zeros(9, dtype=np.float64)
        mujoco.mju_quat2Mat(target_rotation, target_quaternion)
        target_rotation = target_rotation.reshape(3, 3)
        rotation_error_matrix = target_rotation @ current_rotation.T
        rotation_error = 0.5 * np.array(
            [
                rotation_error_matrix[2, 1] - rotation_error_matrix[1, 2],
                rotation_error_matrix[0, 2] - rotation_error_matrix[2, 0],
                rotation_error_matrix[1, 0] - rotation_error_matrix[0, 1],
            ],
            dtype=np.float64,
        )
        orientation_weight = float(np.clip(orientation_weight, 0.0, 1.0))
        error = np.concatenate((position_error, orientation_weight * rotation_error))
        if np.linalg.norm(position_error) < 0.004 and (orientation_weight == 0.0 or np.linalg.norm(rotation_error) < 0.025):
            return q
        jacp = np.zeros((3, env.model.nv), dtype=np.float64)
        jacr = np.zeros((3, env.model.nv), dtype=np.float64)
        mujoco.mj_jacBody(env.model, env.data, jacp, jacr, body_id)
        jacobian = np.vstack((jacp[:, env.dof_adrs], orientation_weight * jacr[:, env.dof_adrs]))
        damping = 0.045
        dq = jacobian.T @ np.linalg.solve(jacobian @ jacobian.T + damping * np.eye(6), error)
        dq_norm = np.linalg.norm(dq)
        if dq_norm > 0.18:
            dq *= 0.18 / dq_norm
        q = np.clip(q + 0.65 * dq, lower, upper)
    return q


def solve_position_nullspace_view_ik(
    env: FR3MuJoCoEnv,
    body_id: int,
    target_position: np.ndarray,
    target_quaternion: np.ndarray,
    seed: np.ndarray,
    view_gain: float = 0.55,
) -> np.ndarray:
    """Solve hand position while steering wrist orientation in its null space.

    The position task remains the primary constraint. The view term is
    projected through ``I - Jp# Jp`` so the wrist can face a target or a
    predicted swept-volume point without replacing the grasp waypoint.
    """

    q = np.asarray(seed, dtype=np.float64).copy()
    lower = env.model.jnt_range[env.joint_ids, 0]
    upper = env.model.jnt_range[env.joint_ids, 1]
    target_rotation_flat = np.zeros(9, dtype=np.float64)
    mujoco.mju_quat2Mat(target_rotation_flat, target_quaternion)
    target_rotation = target_rotation_flat.reshape(3, 3)
    identity = np.eye(7, dtype=np.float64)
    for _ in range(220):
        env.data.qpos[env.qpos_adrs] = q
        mujoco.mj_forward(env.model, env.data)
        position_error = np.asarray(target_position, dtype=np.float64) - env.data.xpos[body_id]
        current_rotation = env.data.xmat[body_id].reshape(3, 3)
        rotation_error_matrix = target_rotation @ current_rotation.T
        rotation_error = 0.5 * np.array(
            [
                rotation_error_matrix[2, 1] - rotation_error_matrix[1, 2],
                rotation_error_matrix[0, 2] - rotation_error_matrix[2, 0],
                rotation_error_matrix[1, 0] - rotation_error_matrix[0, 1],
            ],
            dtype=np.float64,
        )
        jacp = np.zeros((3, env.model.nv), dtype=np.float64)
        jacr = np.zeros((3, env.model.nv), dtype=np.float64)
        mujoco.mj_jacBody(env.model, env.data, jacp, jacr, body_id)
        jacp = jacp[:, env.dof_adrs]
        jacr = jacr[:, env.dof_adrs]
        # Use the exact local position null space. A heavily regularized
        # projector can leak orientation motion back into the position task.
        position_pinv = np.linalg.pinv(jacp, rcond=1.0e-4)
        position_step = position_pinv @ position_error
        nullspace = identity - position_pinv @ jacp
        view_step = nullspace @ (0.22 * jacr.T @ rotation_error)
        # Delay most of the view steering until the hand is close to the
        # waypoint, which keeps the camera objective from bending the reach.
        view_activation = float(np.clip(1.0 - np.linalg.norm(position_error) / 0.12, 0.0, 1.0))
        dq = position_step + float(np.clip(view_gain, 0.0, 1.0)) * view_activation * view_step
        dq_norm = np.linalg.norm(dq)
        if dq_norm > 0.16:
            dq *= 0.16 / dq_norm
        q = np.clip(q + 0.72 * dq, lower, upper)
        # Position convergence is not enough: when the hand is already at the
        # waypoint, continue steering the wrist orientation in the position
        # null space until the camera view has also converged.
        if np.linalg.norm(position_error) < 0.003 and np.linalg.norm(rotation_error) < 0.035:
            return q
    return q


def interpolate_segment(left: np.ndarray, right: np.ndarray, ratio: float) -> np.ndarray:
    ratio = float(np.clip(ratio, 0.0, 1.0))
    smooth = ratio * ratio * (3.0 - 2.0 * ratio)
    return (1.0 - smooth) * left + smooth * right


def _solve_waypoint_specs(
    env: FR3MuJoCoEnv,
    hand_id: int,
    target: np.ndarray,
    waypoint_specs: list[tuple[str, np.ndarray, np.ndarray, float, float]],
) -> tuple[list[np.ndarray], list[dict[str, object]]]:
    """Solve one candidate waypoint chain and record position residuals."""

    view_scheduler = VelocityAwareViewScheduler()
    waypoint_positions = np.asarray([spec[1] for spec in waypoint_specs], dtype=np.float64)
    waypoint_speeds = np.zeros(len(waypoint_specs), dtype=np.float64)
    for index in range(len(waypoint_specs) - 1):
        waypoint_speeds[index] = np.linalg.norm(waypoint_positions[index + 1] - waypoint_positions[index]) / waypoint_specs[index][3]
    waypoint_speeds[-1] = 0.10

    solved_waypoints: list[np.ndarray] = []
    waypoint_diagnostics: list[dict[str, object]] = []
    seed = HOME.copy()
    for index, (phase_name, position, semantic_target, _, view_gain) in enumerate(waypoint_specs):
        decision = view_scheduler.choose_focus(
            phase_name,
            position,
            semantic_target,
            waypoint_positions[index + 1 :],
            waypoint_speeds[index + 1 :],
        )
        print(
            f"planned_view_focus candidate_phase={phase_name} focus={decision.focus_name} "
            f"score={decision.score:.3f} risk={decision.risk_weight:.3f}"
        )
        solved = solve_position_nullspace_view_ik(
            env,
            hand_id,
            position,
            look_at_quaternion(position, decision.focus_point),
            seed,
            view_gain=view_gain,
        )
        solved_waypoints.append(solved)
        env.data.qpos[env.qpos_adrs] = solved
        mujoco.mj_forward(env.model, env.data)
        waypoint_diagnostics.append(
            {
                "phase": phase_name,
                "target_position": np.asarray(position, dtype=np.float64).tolist(),
                "solved_hand_position": env.data.xpos[hand_id].copy().tolist(),
                "position_error_m": float(np.linalg.norm(position - env.data.xpos[hand_id])),
                "focus_name": decision.focus_name,
                "focus_point": decision.focus_point.tolist(),
            }
        )
        seed = solved
    return solved_waypoints, waypoint_diagnostics


def _refine_place_and_build_segments(
    env: FR3MuJoCoEnv,
    hand_id: int,
    target: np.ndarray,
    solved_waypoints: list[np.ndarray],
    waypoint_diagnostics: list[dict[str, object]],
    desired_object_place: np.ndarray,
) -> list[DemoSegment]:
    """Refine carry/release and add a collision-safe post-release retract."""

    q_approach, q_pregrasp, q_grasp, q_lift, q_place_hover = solved_waypoints
    env.data.qpos[env.qpos_adrs] = q_grasp
    mujoco.mj_forward(env.model, env.data)
    grasp_hand_position = env.data.xpos[hand_id].copy()
    grasp_hand_rotation = env.data.xmat[hand_id].reshape(3, 3).copy()
    grasp_relative_position = grasp_hand_rotation.T @ (target - grasp_hand_position)
    view_scheduler = VelocityAwareViewScheduler()
    place_hand_position = np.asarray(desired_object_place, dtype=np.float64).copy() + np.array([0.0, 0.0, 0.075])
    q_place = q_place_hover.copy()
    for _ in range(4):
        # The target cylinder sits on the tabletop at z=0.72.  Keeping the
        # hand at roughly target_z + 0.075 lets the captured grasp transform
        # place the object on the table instead of hovering above it.
        place_hand_position[2] = max(place_hand_position[2], float(desired_object_place[2]) + 0.075)
        place_decision = view_scheduler.choose_focus(
            "CARRY AROUND CLUTTER",
            place_hand_position,
            desired_object_place,
            np.empty((0, 3)),
            np.empty((0,)),
        )
        q_place = solve_position_nullspace_view_ik(
            env,
            hand_id,
            place_hand_position,
            look_at_quaternion(place_hand_position, place_decision.focus_point),
            q_place,
            view_gain=0.65,
        )
        env.data.qpos[env.qpos_adrs] = q_place
        mujoco.mj_forward(env.model, env.data)
        predicted_object_place = env.data.xpos[hand_id] + env.data.xmat[hand_id].reshape(3, 3) @ grasp_relative_position
        place_hand_position += desired_object_place - predicted_object_place
    solved_waypoints[-1] = q_place
    env.data.qpos[env.qpos_adrs] = q_place
    mujoco.mj_forward(env.model, env.data)
    predicted_object_place = env.data.xpos[hand_id] + env.data.xmat[hand_id].reshape(3, 3) @ grasp_relative_position
    waypoint_diagnostics[-1]["object_place_target"] = desired_object_place.tolist()
    waypoint_diagnostics[-1]["predicted_object_place"] = predicted_object_place.tolist()
    waypoint_diagnostics[-1]["object_place_error_m"] = float(np.linalg.norm(desired_object_place - predicted_object_place))
    retract_hand_position = place_hand_position + np.array([0.0, 0.0, 0.16], dtype=np.float64)
    q_retract = solve_position_nullspace_view_ik(
        env,
        hand_id,
        retract_hand_position,
        look_at_quaternion(retract_hand_position, desired_object_place),
        q_place,
        view_gain=0.25,
    )
    return [
        DemoSegment(2.0, q_approach, 0.04, "APPROACH ABOVE CLUTTER"),
        DemoSegment(1.5, q_pregrasp, 0.04, "PRE-GRASP"),
        DemoSegment(1.2, q_grasp, 0.04, "DESCEND"),
        DemoSegment(1.0, q_grasp, 0.0, "CLOSE GRIPPER"),
        DemoSegment(1.8, q_lift, 0.0, "LIFT"),
        DemoSegment(2.3, q_place_hover, 0.0, "CARRY AROUND CLUTTER"),
        # Give the joint servo enough time to settle before the latch is
        # released; otherwise the object is evaluated while the hand is still
        # catching up to the refined placement pose.
        DemoSegment(1.8, q_place, 0.0, "PLACE DESCEND"),
        DemoSegment(1.0, q_place, 0.04, "RELEASE"),
        DemoSegment(0.8, q_retract, 0.04, "RETRACT AFTER RELEASE"),
        DemoSegment(1.8, HOME, 0.04, "RETURN HOME"),
    ]


def _joint_path_length(segments: list[DemoSegment], q_start: np.ndarray) -> float:
    previous = np.asarray(q_start, dtype=np.float64)
    length = 0.0
    for segment in segments:
        current = np.asarray(segment.q, dtype=np.float64)
        length += float(np.linalg.norm(current - previous))
        previous = current
    return length


def build_segments(
    env: FR3MuJoCoEnv,
) -> tuple[list[DemoSegment], np.ndarray, list[dict[str, object]], object, list[dict[str, object]]]:
    target_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_BODY, "target_object")
    hand_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_BODY, "fr3_hand")
    if target_id < 0 or hand_id < 0:
        raise RuntimeError("tabletop scene must contain target_object and fr3_hand")

    env.data.qpos[env.qpos_adrs] = HOME
    mujoco.mj_forward(env.model, env.data)
    target = env.data.xpos[target_id].copy()

    # Candidate Cartesian waypoints are deliberately small perturbations around
    # the deterministic nominal route. The checker selects among them using
    # geometry, not obstacle names or hand-tuned collision labels.
    approach_candidates = {
        "approach_left": np.array([0.06, -0.40, 1.05], dtype=np.float64),
        "approach_center": np.array([0.10, -0.40, 1.05], dtype=np.float64),
        "approach_right": np.array([0.14, -0.40, 1.05], dtype=np.float64),
    }
    pregrasp = target + np.array([0.0, 0.0, 0.16])
    grasp = target + np.array([0.0, 0.0, 0.075])
    lift = target + np.array([0.0, 0.0, 0.30])
    place_candidates = {
        "place_left": np.array([0.32, -0.12, 0.78], dtype=np.float64),
        "place_center": np.array([0.40, -0.10, 0.78], dtype=np.float64),
        "place_right": np.array([0.48, -0.10, 0.78], dtype=np.float64),
    }
    checker = FR3SweptVolumeChecker(env, safety_margin_m=0.015)
    candidates: list[CandidatePlan] = []
    for approach_name, approach in approach_candidates.items():
        for place_name, desired_object_place in place_candidates.items():
            env.reset(HOME)
            waypoint_specs = [
                ("APPROACH ABOVE CLUTTER", approach, target, 2.0, 0.45),
                ("PRE-GRASP", pregrasp, target, 1.5, 0.70),
                ("DESCEND", grasp, target, 1.2, 0.80),
                ("LIFT", lift, target, 1.8, 0.55),
                ("CARRY AROUND CLUTTER", desired_object_place + np.array([0.0, 0.0, 0.18]), desired_object_place, 2.3, 0.65),
            ]
            solved, diagnostics = _solve_waypoint_specs(env, hand_id, target, waypoint_specs)
            segments = _refine_place_and_build_segments(env, hand_id, target, solved, diagnostics, desired_object_place)
            q_sweep, t_sweep = checker.interpolate_segments(segments, HOME, sample_dt_s=0.06)
            report = checker.check_trajectory(q_sweep, t_sweep, max_events=32)
            candidates.append(
                CandidatePlan(
                    name=f"{approach_name}+{place_name}",
                    segments=tuple(segments),
                    target=target.copy(),
                    waypoint_diagnostics=tuple(diagnostics),
                    coarse_report=report,
                    path_length_rad=_joint_path_length(segments, HOME),
                )
            )
            print(
                f"candidate={candidates[-1].name} collision={report.collision_count} "
                f"near={report.near_collision_count} min_clearance={report.min_clearance_m:.4f} "
                f"path={candidates[-1].path_length_rad:.3f}"
            )
    selected = min(
        candidates,
        key=lambda candidate: (
            not candidate.coarse_report.collision_free,
            candidate.coarse_report.near_collision_count,
            -candidate.coarse_report.min_clearance_m,
            candidate.path_length_rad,
        ),
    )
    print(f"selected_candidate={selected.name}")
    candidate_records = [
        {
            "name": candidate.name,
            "collision_count": candidate.coarse_report.collision_count,
            "near_collision_count": candidate.coarse_report.near_collision_count,
            "min_clearance_m": candidate.coarse_report.min_clearance_m,
            "path_length_rad": candidate.path_length_rad,
            "selected": candidate.name == selected.name,
        }
        for candidate in candidates
    ]
    return (
        list(selected.segments),
        selected.target,
        list(selected.waypoint_diagnostics),
        selected.coarse_report,
        candidate_records,
        candidates,
    )


def phase_sample(segments: list[DemoSegment], t: float, q_start: np.ndarray) -> tuple[np.ndarray, float, str]:
    elapsed = 0.0
    previous = q_start
    for segment in segments:
        if t <= elapsed + segment.duration_s:
            ratio = (t - elapsed) / segment.duration_s
            return interpolate_segment(previous, segment.q, ratio), segment.gripper_m, segment.phase
        elapsed += segment.duration_s
        previous = segment.q
    final = segments[-1]
    return final.q.copy(), final.gripper_m, final.phase


def render_demo(
    model_path: Path,
    output_path: Path,
    fps: int = 20,
    metrics_path: Path | None = None,
    dynamic_obstacle: bool = False,
) -> None:
    env = FR3MuJoCoEnv(model_path, physics_dt_s=0.002, policy_dt_s=0.040, ee_body_name="fr3_link7")
    env.reset(HOME)
    obstacle = None
    if dynamic_obstacle:
        from .dynamic_obstacle import PredictableCrossingObstacle

        obstacle = PredictableCrossingObstacle(env.model)
        obstacle.apply(env, 0.0)
    servo = FR3NominalVelocityServo(env, kp=(22.0,) * 7, kv=(10.0,) * 7)
    segments, target, waypoint_diagnostics, _, candidate_records, candidates = build_segments(env)
    sweep_checker = FR3SweptVolumeChecker(env, safety_margin_m=0.015)
    q_sweep, t_sweep = sweep_checker.interpolate_segments(segments, HOME, sample_dt_s=0.02)
    sweep_report = sweep_checker.check_trajectory(q_sweep, t_sweep)
    print(
        f"swept_volume samples={sweep_report.sampled_steps} pairs={sweep_report.pair_checks} "
        f"min_clearance={sweep_report.min_clearance_m:.4f}m "
        f"collision_count={sweep_report.collision_count} "
        f"near_collision_count={sweep_report.near_collision_count}"
    )
    # Planning temporarily changes qpos while solving IK. Execution starts
    # from the actual HOME state after the offline checks are complete.
    state = env.reset(HOME)
    execution_checker = sweep_checker
    if dynamic_obstacle:
        execution_checker = FR3SweptVolumeChecker(
            env,
            safety_margin_m=0.015,
            obstacle_state_fn=obstacle.apply,
        )
        obstacle.apply(env, 0.0)
    supervisor = RecedingHorizonSupervisor(
        candidates,
        execution_checker,
        initial_plan=next(record["name"] for record in candidate_records if record["selected"]),
        initial_q=HOME,
        horizon_s=0.6,
        check_period_s=0.2,
        sample_dt_s=0.06,
    )
    total_time = sum(segment.duration_s for segment in segments)
    total_steps = int(np.ceil(total_time / env.policy_dt_s))
    renderer = mujoco.Renderer(env.model, height=480, width=640)
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = [0.0, -0.05, 0.78]
    camera.distance = 3.25
    camera.azimuth = 136.0
    camera.elevation = -18.0
    wrist_camera = WristRGBDCamera(env.model, "wrist_rgbd", width=320, height=240)
    scene_estimator = WristSceneBeliefEstimator(env.model, "wrist_rgbd")
    view_scheduler = VelocityAwareViewScheduler()
    grasp_latch = MuJoCoGraspLatch(env)
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    font = ImageFont.truetype(str(font_path), 20) if font_path.exists() else ImageFont.load_default()

    frames: list[np.ndarray] = []
    phase_records: list[dict[str, object]] = []
    observation_records: list[dict[str, object]] = []
    last_phase: str | None = None
    max_grasp_tracking_error = 0.0
    min_target_visibility = 1.0
    finite_state = True
    max_dynamic_obstacle_force = 0.0
    dynamic_obstacle_contact_steps = 0
    release_target_position = None
    last_horizon_clearance_m = sweep_report.min_clearance_m
    last_horizon_collision_count = sweep_report.collision_count
    replanning_records: list[dict[str, object]] = []
    q_start = HOME.copy()
    for step in range(total_steps + 1):
        t = min(step * env.policy_dt_s, total_time)
        if obstacle is not None:
            obstacle.apply(env, t)
        wrist = wrist_camera.render(env.data)
        belief = scene_estimator.estimate(
            wrist,
            target_position_world=env.data.xpos[grasp_latch.object_id].copy(),
            stride=8,
        )
        horizon_decision = supervisor.update(env.q, t)
        if horizon_decision is not None:
            replanning_records.append(
                {
                    "time_s": horizon_decision.time_s,
                    "phase": horizon_decision.phase,
                    "active_plan": horizon_decision.active_plan,
                    "selected_plan": horizon_decision.selected_plan,
                    "switched": horizon_decision.switched,
                    "trigger_reason": horizon_decision.trigger_reason,
                    "horizon_min_clearance_m": horizon_decision.report.min_clearance_m,
                    "horizon_collision_count": horizon_decision.report.collision_count,
                    "horizon_near_collision_count": horizon_decision.report.near_collision_count,
                }
            )
            last_horizon_clearance_m = horizon_decision.report.min_clearance_m
            last_horizon_collision_count = horizon_decision.report.collision_count
        q_ref, gripper, phase = supervisor.reference(env.q, t)
        if obstacle is not None:
            obstacle.apply(env, t)
        state = env.state()
        finite_state = finite_state and bool(np.all(np.isfinite(state.q)) and np.all(np.isfinite(state.qdot)))
        target_position_now = env.data.xpos[grasp_latch.object_id].copy()
        hand_position_now = env.data.xpos[grasp_latch.hand_id].copy()
        if grasp_latch.engaged:
            max_grasp_tracking_error = max(
                max_grasp_tracking_error,
                grasp_latch.tracking_error_m(),
            )
        command = servo.compute(state, FR3Waypoint(t, tuple(q_ref), phase))
        if env.model.nu > 7:
            env.data.ctrl[7] = gripper
        if phase == "LIFT" and not grasp_latch.engaged:
            grasp_latch.engage(reference_position=target)
        if phase == "RELEASE" and grasp_latch.engaged:
            release_target_position = env.data.xpos[grasp_latch.object_id].copy()
            grasp_latch.release()
        state = env.step(command.torque, q_cmd=command.q_cmd, qdot_cmd=command.qdot_cmd)
        if obstacle is not None:
            obstacle_state = obstacle.contact_summary(env)
            max_dynamic_obstacle_force = max(
                max_dynamic_obstacle_force,
                float(obstacle_state["max_contact_force_n"]),
            )
            dynamic_obstacle_contact_steps += int(obstacle_state["contact_count"] > 0)
        grasp_latch.update()
        state = env.state()
        target_position_now = env.data.xpos[grasp_latch.object_id].copy()
        hand_position_now = env.data.xpos[grasp_latch.hand_id].copy()
        if grasp_latch.engaged:
            max_grasp_tracking_error = max(
                max_grasp_tracking_error,
                grasp_latch.tracking_error_m(),
            )
        if phase != last_phase:
            phase_records.append(
                {
                    "time_s": float(t),
                    "phase": phase,
                    "grasp_engaged": bool(grasp_latch.engaged),
                    "hand_position": hand_position_now.tolist(),
                    "target_position": target_position_now.tolist(),
                    "hand_target_distance_m": float(np.linalg.norm(target_position_now - hand_position_now)),
                    "grasp_tracking_error_m": float(grasp_latch.tracking_error_m()),
                }
            )
            last_phase = phase
        jacp, _ = env.jacobian()
        ee_speed = float(np.linalg.norm(jacp @ state.qdot))
        view_mode, speed_score = view_scheduler.select(
            phase,
            state.qdot,
            ee_speed_m_s=ee_speed,
        )
        renderer.update_scene(env.data, camera=camera)
        overview = Image.fromarray(renderer.render()).convert("RGB")
        min_target_visibility = min(min_target_visibility, belief.target_visibility)
        if phase_records and phase_records[-1]["phase"] == phase and not observation_records:
            observation_records.append(
                {
                    "time_s": float(t),
                    "phase": phase,
                    "target_visibility": float(belief.target_visibility),
                    "target_pixel_uv": belief.target_pixel_uv.tolist(),
                    "obstacle_point_count": int(len(belief.obstacle_points_world)),
                    "valid_depth_ratio": float(belief.valid_depth_ratio),
                }
            )
        elif phase_records and (not observation_records or observation_records[-1]["phase"] != phase):
            observation_records.append(
                {
                    "time_s": float(t),
                    "phase": phase,
                    "target_visibility": float(belief.target_visibility),
                    "target_pixel_uv": belief.target_pixel_uv.tolist(),
                    "obstacle_point_count": int(len(belief.obstacle_points_world)),
                    "valid_depth_ratio": float(belief.valid_depth_ratio),
                }
            )
        wrist_rgb = Image.fromarray(wrist.rgb).convert("RGB")
        wrist_depth = Image.fromarray(depth_preview(wrist.depth_m)).convert("RGB")
        frame = Image.new("RGB", (960, 480), (16, 20, 26))
        frame.paste(overview, (0, 0))
        frame.paste(wrist_rgb, (640, 0))
        frame.paste(wrist_depth, (640, 240))
        draw = ImageDraw.Draw(frame)
        draw.rectangle((0, 0, frame.width, 74), fill=(10, 16, 24))
        draw.rectangle((640, 0, 960, 28), fill=(10, 16, 24))
        draw.rectangle((640, 240, 960, 268), fill=(10, 16, 24))
        draw.text((14, 10), "FR3 + wrist RGB-D | velocity-aware active view", fill=(235, 242, 250), font=font)
        grasp_state = "GRASPED" if grasp_latch.engaged else "OPEN"
        draw.text((14, 40), f"t={t:5.2f}s  {phase}  view={view_mode}  grasp={grasp_state}", fill=(185, 220, 255), font=font)
        draw.text((14, 64), f"rgbd points={len(belief.obstacle_points_world):4d}  target visibility={belief.target_visibility:.2f}", fill=(175, 195, 205), font=font)
        clearance_label = "horizon" if obstacle is not None else "planned"
        draw.text((650, 220), f"{clearance_label} clearance={last_horizon_clearance_m:.3f} m", fill=(175, 195, 205), font=font)
        draw.text((650, 5), "WRIST RGB", fill=(235, 242, 250), font=font)
        draw.text((650, 245), "WRIST DEPTH", fill=(235, 242, 250), font=font)
        frames.append(np.asarray(frame))
    renderer.close()
    wrist_camera.close()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(output_path, np.stack(frames), duration=1.0 / fps, loop=0)
    print(f"saved {output_path} ({len(frames)} frames, {total_time:.2f}s)")
    print(f"target_initial_xyz={target.tolist()}")
    final_target = env.data.xpos[grasp_latch.object_id].copy()
    selected_candidate = supervisor.active_plan
    selected_plan = next(candidate for candidate in candidates if candidate.name == selected_candidate)
    desired_place = selected_plan.waypoint_diagnostics[-1].get("object_place_target")
    desired_place_array = None if desired_place is None else np.asarray(desired_place, dtype=np.float64)
    placement_reference = final_target if release_target_position is None else release_target_position
    placement_error = None if desired_place_array is None else float(np.linalg.norm(placement_reference - desired_place_array))
    placement_success = bool(
        desired_place_array is not None
        and np.linalg.norm(placement_reference[:2] - desired_place_array[:2]) <= 0.06
        and abs(float(placement_reference[2] - desired_place_array[2])) <= 0.06
    )
    metrics = {
        "total_time_s": float(total_time),
        "initial_target_position": target.tolist(),
        "final_target_position": final_target.tolist(),
        "phase_records": phase_records,
        "max_grasp_tracking_error_m": float(max_grasp_tracking_error),
        "finite_state": bool(finite_state),
        "final_grasp_engaged": bool(grasp_latch.engaged),
        "waypoint_diagnostics": waypoint_diagnostics,
        "candidate_records": candidate_records,
        "replanning_records": replanning_records,
        "replanning_count": int(supervisor.check_count),
        "plan_switch_count": int(supervisor.switch_count),
        "dynamic_obstacle_enabled": bool(obstacle is not None),
        "dynamic_obstacle_contact_steps": int(dynamic_obstacle_contact_steps),
        "max_dynamic_obstacle_force_n": float(max_dynamic_obstacle_force),
        "placement_reference_position": placement_reference.tolist(),
        "placement_error_m": placement_error,
        "placement_success": placement_success,
        "grasp_success": bool(any(record["grasp_engaged"] for record in phase_records)),
        "observation_records": observation_records,
        "min_target_visibility": float(min_target_visibility),
        "swept_volume_report": {
            "sampled_steps": sweep_report.sampled_steps,
            "pair_checks": sweep_report.pair_checks,
            "min_clearance_m": sweep_report.min_clearance_m,
            "min_clearance_time_s": sweep_report.min_clearance_time_s,
            "min_clearance_robot_geom": sweep_report.min_clearance_robot_geom,
            "min_clearance_obstacle_geom": sweep_report.min_clearance_obstacle_geom,
            "collision_count": sweep_report.collision_count,
            "near_collision_count": sweep_report.near_collision_count,
            "events": [event.__dict__ for event in sweep_report.events],
        },
    }
    if metrics_path is not None:
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"saved {metrics_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fps", type=int, default=20)
    parser.add_argument("--metrics", type=Path, default=None)
    parser.add_argument("--dynamic-obstacle", action="store_true")
    args = parser.parse_args()
    render_demo(args.model, args.output, args.fps, args.metrics, args.dynamic_obstacle)


if __name__ == "__main__":
    main()
