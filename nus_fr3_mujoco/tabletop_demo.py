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
from .scene_belief import RGBDObstacleTracker, WristSceneBeliefEstimator
from .wrist_camera import WristRGBDCamera, VelocityAwareViewScheduler, depth_preview


HOME = np.array([0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785], dtype=np.float64)
GRASP_CLOSURE_M = 0.017


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


def panda_side_grasp_quaternion() -> np.ndarray:
    """Orient the Panda jaws for a stable horizontal side grasp.

    The finger slides close along world X and the pads advance along world
    -Y.  This is the collision-tested orientation for the FR3 hand mesh; the
    wrist stays level with the desk and the two pads remain on opposite sides
    of the cylinder throughout closure.
    """

    local_x = np.array([0.0, 0.0, -1.0], dtype=np.float64)
    local_y = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    local_z = np.array([0.0, -1.0, 0.0], dtype=np.float64)
    rotation = np.column_stack((local_x, local_y, local_z))
    quaternion = np.zeros(4, dtype=np.float64)
    mujoco.mju_mat2Quat(quaternion, rotation.reshape(-1))
    return quaternion


def stabilize_target_on_desk(env: FR3MuJoCoEnv, target_body_id: int) -> np.ndarray:
    """Place the free target at the static desk contact height before planning."""

    target_joint_id = int(env.model.body_jntadr[target_body_id])
    target_qposadr = int(env.model.jnt_qposadr[target_joint_id])
    target_geom_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "target_object_geom")
    desk_geom_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "desk_top")
    if target_geom_id < 0 or desk_geom_id < 0:
        raise RuntimeError("scene must contain target_object_geom and desk_top")
    desk_top_z = float(env.model.geom_pos[desk_geom_id][2] + env.model.geom_size[desk_geom_id][2])
    target_half_height = float(env.model.geom_size[target_geom_id][1])
    qpos = env.data.qpos[target_qposadr : target_qposadr + 7]
    qpos[2] = desk_top_z + target_half_height
    qpos[3:7] = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
    env.data.qvel[int(env.model.jnt_dofadr[target_joint_id]) : int(env.model.jnt_dofadr[target_joint_id]) + 6] = 0.0
    mujoco.mj_forward(env.model, env.data)
    return env.data.xpos[target_body_id].copy()


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


def pose_ik_residual(
    env: FR3MuJoCoEnv,
    body_id: int,
    target_position: np.ndarray,
    target_quaternion: np.ndarray,
) -> tuple[float, float]:
    """Return position and rotation residuals for the current model state."""

    position_error = float(np.linalg.norm(np.asarray(target_position) - env.data.xpos[body_id]))
    target_flat = np.zeros(9, dtype=np.float64)
    mujoco.mju_quat2Mat(target_flat, target_quaternion)
    target_rotation = target_flat.reshape(3, 3)
    current_rotation = env.data.xmat[body_id].reshape(3, 3)
    relative = target_rotation @ current_rotation.T
    rotation_error = 0.5 * np.array(
        [
            relative[2, 1] - relative[1, 2],
            relative[0, 2] - relative[2, 0],
            relative[1, 0] - relative[0, 1],
        ],
        dtype=np.float64,
    )
    return position_error, float(np.linalg.norm(rotation_error))


def solve_fixed_pose_with_restarts(
    env: FR3MuJoCoEnv,
    body_id: int,
    target_position: np.ndarray,
    target_quaternion: np.ndarray,
    preferred_seed: np.ndarray,
) -> np.ndarray:
    """Solve a fixed hand pose while rejecting non-converged IK branches."""

    seeds = [
        np.asarray(preferred_seed, dtype=np.float64).copy(),
        HOME.copy(),
        HOME + np.array([0.35, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        HOME + np.array([-0.35, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    ]
    candidates: list[tuple[float, float, float, np.ndarray]] = []
    for seed in seeds:
        q = solve_pose_ik(
            env,
            body_id,
            target_position,
            target_quaternion,
            seed,
            orientation_weight=1.0,
        )
        env.data.qpos[env.qpos_adrs] = q
        mujoco.mj_forward(env.model, env.data)
        position_error, rotation_error = pose_ik_residual(
            env,
            body_id,
            target_position,
            target_quaternion,
        )
        feasible = float(position_error <= 0.008 and rotation_error <= 0.05)
        # Feasible solutions dominate. Among them, preserve the continuous
        # elbow/wrist branch by staying close to the previous waypoint.
        score = (-feasible, position_error + rotation_error, float(np.linalg.norm(q - preferred_seed)))
        candidates.append((score[0], score[1], score[2], q.copy()))
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    return candidates[0][3]


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
    waypoint_specs: list[tuple[str, np.ndarray, np.ndarray, float, float, np.ndarray | None]],
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
    for index, (phase_name, position, semantic_target, _, view_gain, orientation) in enumerate(waypoint_specs):
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
        if orientation is None:
            solved = solve_position_nullspace_view_ik(
                env,
                hand_id,
                position,
                look_at_quaternion(position, decision.focus_point),
                seed,
                view_gain=view_gain,
            )
        else:
            # Task-space grasp waypoints use full pose IK. The previous
            # position-priority null-space solver could leave the wrist in a
            # visually awkward orientation even when the hand position was
            # close to the target.
            solved = solve_fixed_pose_with_restarts(
                env,
                hand_id,
                position,
                orientation,
                seed,
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
                "hand_quaternion_wxyz": env.data.xquat[hand_id].copy().tolist(),
                "orientation_error_rad": (
                    pose_ik_residual(env, hand_id, position, orientation)[1]
                    if orientation is not None
                    else None
                ),
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
    grasp_quaternion: np.ndarray,
) -> list[DemoSegment]:
    """Refine carry/release and add a collision-safe post-release retract."""

    q_approach, q_pregrasp, q_grasp, q_lift, q_place_hover = solved_waypoints
    env.data.qpos[env.qpos_adrs] = q_grasp
    mujoco.mj_forward(env.model, env.data)
    grasp_hand_position = env.data.xpos[hand_id].copy()
    grasp_hand_rotation = env.data.xmat[hand_id].reshape(3, 3).copy()
    grasp_relative_position = grasp_hand_rotation.T @ (target - grasp_hand_position)
    # The grasp transform is measured from the hand body to the object center.
    # Therefore the hand must be placed by the inverse of that measured
    # offset.  Adding a fixed height here lifted the object 7.5 cm above the
    # desk during release, which made the placement look and behave wrong.
    place_hand_position = np.asarray(desired_object_place, dtype=np.float64).copy() - grasp_hand_rotation @ grasp_relative_position
    q_place = q_place_hover.copy()
    for _ in range(4):
        q_place = solve_position_nullspace_view_ik(
            env,
            hand_id,
            place_hand_position,
            grasp_quaternion,
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
        grasp_quaternion,
        q_place,
        view_gain=0.25,
    )
    return [
        DemoSegment(3.2, q_approach, 0.04, "APPROACH ABOVE CLUTTER"),
        DemoSegment(1.8, q_pregrasp, 0.04, "PRE-GRASP"),
        DemoSegment(1.3, q_grasp, 0.04, "DESCEND"),
        DemoSegment(1.0, q_grasp, 0.04, "SETTLE AT GRASP"),
        DemoSegment(1.4, q_grasp, 0.0, "CLOSE GRIPPER"),
        DemoSegment(2.0, q_lift, 0.0, "LIFT"),
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
    target = stabilize_target_on_desk(env, target_id)

    # Candidate routes are evaluated in joint space.  The grasp is approached
    # from the open left side of the desk: the wrist stays to the left of the
    # keyboard while descending, then advances along the gripper approach
    # axis.  Keep three small lateral variants around the same side-grasp
    # geometry so the online supervisor still has alternatives.
    # The center-only debugging variant is not robust in the dynamic scene:
    # it can place the fingers outside the cylinder at closure.  The online
    # supervisor also needs more than one approach corridor while the robot is
    # still in APPROACH ABOVE CLUTTER.
    approach_candidates = {
        "approach_left": target + np.array([-0.06, 0.18, 0.30], dtype=np.float64),
        "approach_center": target + np.array([0.00, 0.18, 0.30], dtype=np.float64),
        "approach_right": target + np.array([0.06, 0.18, 0.30], dtype=np.float64),
    }
    grasp_quaternion = panda_side_grasp_quaternion()
    pregrasp = target + np.array([0.0, 0.14, 0.04])
    grasp = target + np.array([0.0, 0.105, 0.0])
    lift = grasp + np.array([0.0, 0.0, 0.30])
    place_candidates = {
        "place_left": np.array([0.20, -0.30, 0.78], dtype=np.float64),
        "place_center": np.array([0.30, -0.30, 0.78], dtype=np.float64),
        "place_right": np.array([0.40, -0.30, 0.78], dtype=np.float64),
    }
    checker = FR3SweptVolumeChecker(
        env,
        safety_margin_m=0.015,
        excluded_obstacle_bodies=("target_object", "dynamic_obstacle", "obstacle_prediction_proxy"),
    )
    candidates: list[CandidatePlan] = []
    for approach_name, approach in approach_candidates.items():
        for place_name, desired_object_place in place_candidates.items():
            env.reset(HOME)
            target = stabilize_target_on_desk(env, target_id)
            waypoint_specs = [
                ("APPROACH ABOVE CLUTTER", approach, target, 3.2, 0.00, grasp_quaternion),
                ("PRE-GRASP", pregrasp, target, 1.8, 0.20, grasp_quaternion),
                ("DESCEND", grasp, target, 1.3, 0.10, grasp_quaternion),
                ("LIFT", lift, target, 2.0, 0.10, grasp_quaternion),
                ("CARRY AROUND CLUTTER", desired_object_place + np.array([0.0, 0.0, 0.18]), desired_object_place, 2.3, 0.10, grasp_quaternion),
            ]
            solved, diagnostics = _solve_waypoint_specs(env, hand_id, target, waypoint_specs)
            segments = _refine_place_and_build_segments(env, hand_id, target, solved, diagnostics, desired_object_place, grasp_quaternion)
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
    active_view_enabled: bool = True,
    grasp_closure_m: float = GRASP_CLOSURE_M,
    gripper_kp: float = 800.0,
) -> None:
    env = FR3MuJoCoEnv(model_path, physics_dt_s=0.002, policy_dt_s=0.040, ee_body_name="fr3_link7")
    if env.model.nu > 7:
        env.model.actuator_gainprm[7, 0] = float(gripper_kp)
    env.reset(HOME)
    obstacle = None
    perception_tracker = RGBDObstacleTracker()
    perception_predictor = None
    if dynamic_obstacle:
        from .dynamic_obstacle import PredictableCrossingObstacle, RGBDObstaclePredictor

        obstacle = PredictableCrossingObstacle(env.model)
        obstacle.apply(env, 0.0)
        perception_predictor = RGBDObstaclePredictor(env.model, perception_tracker)
    servo = FR3NominalVelocityServo(env, kp=(22.0,) * 7, kv=(10.0,) * 7)
    segments, target, waypoint_diagnostics, _, candidate_records, candidates = build_segments(env)
    sweep_checker = FR3SweptVolumeChecker(
        env,
        safety_margin_m=0.015,
        excluded_obstacle_bodies=("target_object", "dynamic_obstacle", "obstacle_prediction_proxy"),
    )
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
            obstacle_state_fn=perception_predictor.apply,
            excluded_obstacle_bodies=("target_object", "dynamic_obstacle"),
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
        switch_cooldown_s=0.4,
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
    stabilize_target_on_desk(env, grasp_latch.object_id)
    target_joint_id = int(env.model.body_jntadr[grasp_latch.object_id])
    target_qposadr = int(env.model.jnt_qposadr[target_joint_id])
    target_qveladr = int(env.model.jnt_dofadr[target_joint_id])
    target_rest_qpos = env.data.qpos[target_qposadr : target_qposadr + 7].copy()
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    font = ImageFont.truetype(str(font_path), 20) if font_path.exists() else ImageFont.load_default()

    frames: list[np.ndarray] = []
    phase_records: list[dict[str, object]] = []
    observation_records: list[dict[str, object]] = []
    active_view_records: list[dict[str, object]] = []
    last_phase: str | None = None
    max_grasp_tracking_error = 0.0
    min_target_visibility = 1.0
    finite_state = True
    max_dynamic_obstacle_force = 0.0
    dynamic_obstacle_contact_steps = 0
    dynamic_obstacle_contact_pairs: list[dict[str, object]] = []
    release_target_position = None
    last_horizon_clearance_m = sweep_report.min_clearance_m
    last_horizon_collision_count = sweep_report.collision_count
    replanning_records: list[dict[str, object]] = []
    q_start = HOME.copy()
    hand_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_BODY, "fr3_hand")
    q_grasp_ref = next(segment.q.copy() for segment in segments if segment.phase == "DESCEND")
    q_pregrasp_ref = next(segment.q.copy() for segment in segments if segment.phase == "PRE-GRASP")
    last_active_view_time = -np.inf
    active_view_accept_count = 0
    active_view_reject_count = 0
    grasp_attempted = False
    grasp_validation_records: list[dict[str, object]] = []
    illegal_target_contact_steps = 0
    target_contact_records: list[dict[str, object]] = []
    grasp_contact_enabled_records: list[dict[str, object]] = []
    grasp_failed = False
    grasp_failure_time_s: float | None = None
    grasp_ever_engaged = False
    close_phase_start_time = -np.inf
    for step in range(total_steps + 1):
        t = min(step * env.policy_dt_s, total_time)
        # The target is a desk item, not a free projectile.  Hold its initial
        # resting pose until the closure phase so small solver/contact impulses
        # during the approach cannot make it slide away before either fingertip
        # has a chance to engage.  Once closure starts, normal MuJoCo contact
        # dynamics are restored and the latch validates the physical grasp.
        if not grasp_attempted and t < 7.30:
            env.data.qpos[target_qposadr : target_qposadr + 7] = target_rest_qpos
            env.data.qvel[target_qveladr : target_qveladr + 6] = 0.0
            mujoco.mj_forward(env.model, env.data)
        if obstacle is not None:
            obstacle.apply(env, t)
        # The nominal stack sees only the wrist RGB-D frame. The benchmark
        # obstacle is moved independently to generate the hidden environment.
        wrist = wrist_camera.render(env.data)
        belief = scene_estimator.estimate(
            wrist,
            target_position_world=env.data.xpos[grasp_latch.object_id].copy(),
            stride=8,
        )
        perceived_state = perception_tracker.update(
            wrist,
            time_s=t,
            target_position_world=env.data.xpos[grasp_latch.object_id].copy(),
        )
        if perception_predictor is not None:
            perception_predictor.update(perceived_state)
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
        if phase == "CLOSE GRIPPER" and last_phase != phase:
            close_phase_start_time = t
        if grasp_failed:
            recovery_elapsed = float(t - (grasp_failure_time_s or t))
            if recovery_elapsed < 0.8:
                q_ref = q_grasp_ref
                phase = "GRASP FAILED / OPEN"
            elif recovery_elapsed < 1.8:
                q_ref = q_pregrasp_ref
                phase = "GRASP FAILED / RETREAT"
            else:
                q_ref = HOME
                phase = "GRASP FAILED / HOME"
            gripper = 0.04
        hand_position = env.data.xpos[hand_id].copy()
        q_before_view_ik = env.q.copy()
        future_hand_positions = []
        elapsed_plan = 0.0
        for future_segment in supervisor.plan_segments():
            elapsed_plan += float(future_segment.duration_s)
            if elapsed_plan <= t + 0.18:
                continue
            env.data.qpos[env.qpos_adrs] = future_segment.q
            mujoco.mj_forward(env.model, env.data)
            future_hand_positions.append(env.data.xpos[hand_id].copy())
        env.data.qpos[env.qpos_adrs] = q_before_view_ik
        mujoco.mj_forward(env.model, env.data)
        active_view = view_scheduler.choose_active_focus(
            phase,
            hand_position,
            env.data.xpos[grasp_latch.object_id].copy(),
            perceived_state,
            future_positions=np.asarray(future_hand_positions, dtype=np.float64),
        )
        if (
            active_view_enabled
            and active_view.action_required
            and phase in {"CARRY AROUND CLUTTER", "RETURN HOME"}
            and t - last_active_view_time >= 0.32
        ):
            q_view = solve_position_nullspace_view_ik(
                env,
                hand_id,
                hand_position,
                look_at_quaternion(hand_position, active_view.focus_point),
                env.q,
                view_gain=0.45,
            )
            # Active perception must not submit a wrist reorientation that is
            # already unsafe under the currently observed RGB-D hypothesis.
            # The checker sees the RGB-D-driven proxy, never the hidden body.
            view_gate_q, view_gate_t = execution_checker.interpolate_segments(
                [DemoSegment(0.32, q_view, 0.0, phase)],
                env.q,
                sample_dt_s=0.04,
            )
            view_gate_report = execution_checker.check_trajectory(
                view_gate_q,
                view_gate_t + float(t),
                near_collision_margin_m=0.010,
                max_events=8,
            )
            view_accepted = bool(
                view_gate_report.collision_count == 0
                and view_gate_report.min_clearance_m >= 0.0
            )
            # IK is used to construct a camera-view action. Restore the real
            # measured configuration before the torque servo advances it.
            env.data.qpos[env.qpos_adrs] = q_before_view_ik
            mujoco.mj_forward(env.model, env.data)
            if view_accepted:
                q_ref = 0.65 * q_ref + 0.35 * q_view
                view_action = "ACTIVE_OBSTACLE_VIEW"
                active_view_accept_count += 1
                last_active_view_time = t
            else:
                view_action = "ACTIVE_VIEW_REJECTED"
                active_view_reject_count += 1
        else:
            view_action = "TASK_VIEW"
        active_view_records.append(
            {
                "time_s": float(t),
                "phase": phase,
                "focus_name": active_view.focus_name,
                "focus_point": active_view.focus_point.tolist(),
                "action": view_action,
                "action_required": bool(active_view.action_required),
                "obstacle_visible": bool(perceived_state.visible),
                "obstacle_position_world": perceived_state.position_world.tolist(),
                "obstacle_velocity_world": perceived_state.velocity_world.tolist(),
                "obstacle_speed_m_s": float(np.linalg.norm(perceived_state.velocity_world)),
                "prediction_uncertainty_m": float(np.sqrt(perceived_state.covariance_m2)),
                "tracking_confidence": float(perceived_state.confidence),
                "safety_gate": view_action != "ACTIVE_VIEW_REJECTED",
            }
        )
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
        if phase == "CLOSE GRIPPER":
            gripper = float(grasp_closure_m)
        elif phase in {"LIFT", "CARRY AROUND CLUTTER", "PLACE DESCEND"}:
            gripper = float(grasp_closure_m) if grasp_latch.engaged else 0.04
        if env.model.nu > 7:
            env.data.ctrl[7] = gripper
        # Keep the target physically available to the desk throughout the
        # reach, but prevent an open finger from grazing it before the grasp
        # pose has settled. The fingertip-target channel is enabled only for
        # the closure window and remains enabled after a validated grasp.
        # Keep the target collision channel disabled while the fingers are
        # still converging.  Enabling it only for the final part of closure
        # prevents a slightly high pad from tipping the free cylinder while
        # the wrist settles, yet still gives the latch a physical contact
        # window before validation in LIFT.
        grasp_contact_enabled = bool(
            (phase == "CLOSE GRIPPER" and t - close_phase_start_time >= 0.9)
            or grasp_latch.engaged
        )
        env.model.geom_conaffinity[grasp_latch.target_geom_id] = 8 if grasp_contact_enabled else 0
        grasp_contact_enabled_records.append(
            {"time_s": float(t), "phase": phase, "enabled": grasp_contact_enabled}
        )
        if phase == "LIFT" and not grasp_latch.engaged and not grasp_attempted:
            validation = grasp_latch.validate_grasp()
            grasp_validation_records.append({"time_s": float(t), **validation})
            grasp_latch.engage()
            grasp_attempted = True
            if not grasp_latch.engaged:
                grasp_failed = True
                grasp_failure_time_s = float(t)
                env.model.geom_conaffinity[grasp_latch.target_geom_id] = 0
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
            if obstacle_state["contact_count"]:
                dynamic_obstacle_contact_pairs.append(
                    {"time_s": float(t), "phase": phase, "pairs": obstacle_state.get("contact_pairs", [])}
                )
        target_contact = grasp_latch.target_contact_summary()
        illegal_target_contact_steps += int(target_contact["illegal_target_contact_count"] > 0)
        if target_contact["target_robot_contact_count"]:
            target_contact_records.append({"time_s": float(t), "phase": phase, **target_contact})
        # Decide during closure, while the fingers are still in contact. The
        # previous implementation waited until the first LIFT sample, which
        # allowed a valid transient grasp to destabilize before validation.
        if phase == "CLOSE GRIPPER" and not grasp_latch.engaged and not grasp_attempted:
            closure_validation = grasp_latch.validate_grasp()
            if closure_validation["left_finger_contact"] or closure_validation["right_finger_contact"]:
                grasp_validation_records.append({"time_s": float(t), **closure_validation})
            if bool(closure_validation["valid"]):
                grasp_latch.engage()
                grasp_attempted = True
                grasp_ever_engaged = True
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
        draw.text((14, 40), f"t={t:5.2f}s  {phase}  view={view_action}  grasp={grasp_state}", fill=(185, 220, 255), font=font)
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
        "dynamic_obstacle_contact_pairs": dynamic_obstacle_contact_pairs,
        "max_dynamic_obstacle_force_n": float(max_dynamic_obstacle_force),
        "placement_reference_position": placement_reference.tolist(),
        "placement_error_m": placement_error,
        "placement_success": placement_success,
        "grasp_success": bool(grasp_ever_engaged),
        "grasp_ever_engaged": bool(grasp_ever_engaged),
        "grasp_attempted": bool(grasp_attempted),
        "grasp_failed": bool(grasp_failed),
        "grasp_failure_time_s": grasp_failure_time_s,
        "grasp_validation_records": grasp_validation_records,
        "target_contact_records": target_contact_records,
        "illegal_target_contact_steps": int(illegal_target_contact_steps),
        "grasp_contact_enabled_records": grasp_contact_enabled_records,
        "observation_records": observation_records,
        "active_view_records": active_view_records,
        "active_view_accept_count": int(active_view_accept_count),
        "active_view_reject_count": int(active_view_reject_count),
        "perception_contract": {
            "obstacle_pose_available_to_nominal": False,
            "obstacle_velocity_available_to_nominal": False,
            "obstacle_contact_available_to_nominal": False,
            "obstacle_source": "wrist_rgbd_only",
        },
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
    parser.add_argument("--disable-active-view", action="store_true")
    parser.add_argument("--grasp-closure", type=float, default=GRASP_CLOSURE_M)
    parser.add_argument("--gripper-kp", type=float, default=800.0)
    args = parser.parse_args()
    render_demo(
        args.model,
        args.output,
        args.fps,
        args.metrics,
        args.dynamic_obstacle,
        not args.disable_active_view,
        args.grasp_closure,
        args.gripper_kp,
    )


if __name__ == "__main__":
    main()
