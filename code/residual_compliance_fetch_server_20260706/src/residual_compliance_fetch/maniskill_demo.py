from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from residual_compliance_fetch.bc_policy import BCResidualPolicy
from residual_compliance_fetch.controllers import (
    ContactComplianceConfig,
    ContactComplianceController,
    JointPathTracker,
    JointTrackerConfig,
    LinkState,
    SmootherConfig,
    VelocitySmoother,
)
from residual_compliance_fetch.metrics import RolloutMetrics
from residual_compliance_fetch.obstacles import CrossingSphereObstacle, CrossingSphereSpec
from residual_compliance_fetch.trajectory import default_path_from_current, load_arm_path
from residual_compliance_fetch.utils import ensure_dir, flatten_state, to_numpy, vector3
from residual_compliance_fetch.visualization import ThirdPersonCamera


FETCH_ARM_LINK_HINTS = (
    "shoulder_pan",
    "shoulder_lift",
    "upperarm",
    "elbow",
    "forearm",
    "wrist",
    "gripper_link",
)


@dataclass
class DemoConfig:
    env_id: str = "ReplicaCAD_SceneManipulation-v1"
    robot_uids: str = "fetch"
    obs_mode: str = "state"
    control_mode: str = "pd_joint_vel"
    render_mode: str | None = "human"
    render_backend: str = "gpu"
    collision_only_visuals: bool = False
    seed: int = 0
    dt: float = 1.0 / 30.0
    max_steps: int = 420
    goal_tolerance: float = 0.10
    record_gif: bool = False
    record_fps: float = 10.0
    record_width: int = 960
    record_height: int = 540
    record_stride: int = 3
    no_early_stop: bool = False
    lock_non_arm_joints: bool = True
    camera_view: str = "side"
    camera_target: tuple[float, float, float] = (-0.62, 0.04, 1.45)
    allowed_penetration: float = 0.025
    trajectory: str | None = None
    output_dir: str = "outputs/demo"


@dataclass
class CommandConfig:
    nominal_kp: float = 1.8
    nominal_max_qdot: float = 0.75
    waypoint_tolerance: float = 0.07
    command_max_qdot: float = 0.90
    command_max_accel: float = 3.20
    command_lowpass_alpha: float = 0.30


def parse_render_mode(value: str | None) -> str | None:
    if value is None:
        return None
    if str(value).lower() in {"none", "null", "false", "0"}:
        return None
    return value


def apply_collision_only_visual_patch() -> None:
    """Disable visual geometry loading for headless training while keeping collisions."""
    import mani_skill.render.utils as render_utils
    from sapien.wrapper.urdf_loader import URDFLoader

    render_utils.can_render = lambda device: False
    if getattr(URDFLoader, "_residual_collision_only_patch", False):
        return

    original_build_link = URDFLoader._build_link

    def _build_link_collision_only(self, link, link_builder):
        old_visuals = getattr(link, "visuals", None)
        replaced = False
        try:
            try:
                link.visuals = []
                replaced = True
            except Exception:
                if hasattr(old_visuals, "clear"):
                    old_copy = list(old_visuals)
                    old_visuals.clear()
                    try:
                        return original_build_link(self, link, link_builder)
                    finally:
                        old_visuals.extend(old_copy)
                return original_build_link(self, link, link_builder)
            return original_build_link(self, link, link_builder)
        finally:
            if replaced:
                try:
                    link.visuals = old_visuals
                except Exception:
                    pass

    URDFLoader._build_link = _build_link_collision_only
    URDFLoader._residual_collision_only_patch = True
    URDFLoader._residual_original_build_link = original_build_link


def build_maniskill_env(config: DemoConfig):
    if config.collision_only_visuals:
        lvp_icd = Path("/usr/share/vulkan/icd.d/lvp_icd.x86_64.json")
        if lvp_icd.exists():
            os.environ.setdefault("VK_ICD_FILENAMES", str(lvp_icd))
        apply_collision_only_visual_patch()

    import gymnasium as gym
    from mani_skill.utils.structs.types import GPUMemoryConfig, SceneConfig, SimConfig

    return gym.make(
        config.env_id,
        robot_uids=config.robot_uids,
        obs_mode=config.obs_mode,
        control_mode=config.control_mode,
        render_mode=parse_render_mode(config.render_mode),
        render_backend=config.render_backend,
        sim_config=SimConfig(
            gpu_memory_config=GPUMemoryConfig(
                found_lost_pairs_capacity=2**25,
                max_rigid_patch_count=2**18,
            ),
            scene_config=SceneConfig(contact_offset=0.001),
        ),
    )


def active_joint_indices(agent) -> dict[str, int]:
    joint_names = [j.name for j in agent.robot.active_joints]
    return {name: idx for idx, name in enumerate(joint_names)}


def get_arm_indices(agent) -> list[int]:
    name_to_idx = active_joint_indices(agent)
    return [name_to_idx[name] for name in agent.arm_joint_names]


def get_arm_qpos(robot, arm_indices: list[int]) -> np.ndarray:
    q_full = flatten_state(robot.get_qpos())
    return q_full[arm_indices].astype(np.float32)


def get_arm_qvel(robot, arm_indices: list[int]) -> np.ndarray:
    qvel = flatten_state(robot.get_qvel())
    return qvel[arm_indices].astype(np.float32)


def get_arm_qlimits(robot, arm_indices: list[int]) -> np.ndarray | None:
    try:
        limits = to_numpy(robot.get_qlimits()).astype(np.float32)
    except Exception:
        return None
    while limits.ndim > 2 and limits.shape[0] == 1:
        limits = limits[0]
    if limits.ndim == 2 and limits.shape[1] == 2:
        return limits[arm_indices]
    return None


def set_arm_start(robot, scene, arm_indices: list[int], q_arm: np.ndarray) -> None:
    q_full = flatten_state(robot.get_qpos())
    q_full[arm_indices] = np.asarray(q_arm, dtype=np.float32)
    robot.set_qpos(q_full)
    robot.set_qvel(np.zeros_like(q_full, dtype=np.float32))
    if hasattr(scene, "px") and hasattr(scene.px, "gpu_update_articulation_kinematics"):
        scene.px.gpu_update_articulation_kinematics()


def update_articulation_kinematics(scene) -> None:
    if hasattr(scene, "px") and hasattr(scene.px, "gpu_update_articulation_kinematics"):
        scene.px.gpu_update_articulation_kinematics()


def locked_joint_indices(agent, arm_indices: list[int]) -> list[int]:
    q_full = flatten_state(agent.robot.get_qpos())
    arm_set = set(int(i) for i in arm_indices)
    joint_names = [str(joint.name) for joint in agent.robot.active_joints]
    lock_indices: list[int] = []
    for idx in range(len(q_full)):
        name = joint_names[idx] if idx < len(joint_names) else ""
        if idx in arm_set:
            continue
        if "gripper" in name or "finger" in name:
            continue
        lock_indices.append(idx)
    return lock_indices


def enforce_locked_joints(
    robot,
    scene,
    lock_indices: list[int],
    locked_qpos: np.ndarray,
) -> tuple[float, float]:
    if not lock_indices:
        return 0.0, 0.0

    q_full = flatten_state(robot.get_qpos()).astype(np.float32)
    qvel_full = flatten_state(robot.get_qvel()).astype(np.float32)
    indices = np.asarray(lock_indices, dtype=np.int64)
    correction = float(np.linalg.norm(q_full[indices] - locked_qpos[indices]))
    locked_velocity_norm = float(np.linalg.norm(qvel_full[indices]))

    q_full[indices] = locked_qpos[indices]
    qvel_full[indices] = 0.0
    robot.set_qpos(q_full)
    robot.set_qvel(qvel_full)
    update_articulation_kinematics(scene)
    return correction, locked_velocity_norm


def build_action_slices(agent) -> dict[str, slice]:
    action_slices: dict[str, slice] = {}
    current = 0
    for name in ["arm", "gripper", "body", "base"]:
        controller = agent.controller.controllers.get(name)
        if controller is None:
            continue
        dim = int(controller.action_space.shape[0])
        action_slices[name] = slice(current, current + dim)
        current += dim
    return action_slices


def compose_action(env, action_slices: dict[str, slice], qdot_arm: np.ndarray) -> np.ndarray:
    action = np.zeros(env.action_space.shape, dtype=np.float32)

    if "arm" in action_slices:
        sl = action_slices["arm"]
        arm_action = np.zeros(sl.stop - sl.start, dtype=np.float32)
        arm_action[: min(7, len(arm_action))] = np.asarray(qdot_arm, dtype=np.float32)[: min(7, len(arm_action))]
        action[sl] = arm_action

    if "gripper" in action_slices:
        sl = action_slices["gripper"]
        action[sl] = np.ones(sl.stop - sl.start, dtype=np.float32)

    if "body" in action_slices:
        sl = action_slices["body"]
        action[sl] = np.zeros(sl.stop - sl.start, dtype=np.float32)

    if "base" in action_slices:
        sl = action_slices["base"]
        action[sl] = np.zeros(sl.stop - sl.start, dtype=np.float32)

    return np.nan_to_num(action, nan=0.0).astype(np.float32)


def select_arm_links(robot) -> list[LinkState]:
    selected: list[LinkState] = []
    seen: set[str] = set()
    for idx, link in enumerate(robot.links):
        name = str(link.name)
        if name in seen:
            continue
        if any(hint in name for hint in FETCH_ARM_LINK_HINTS):
            selected.append(LinkState(name=name, index=idx, position=vector3(link.pose.p)))
            seen.add(name)

    if not selected:
        for idx, link in list(enumerate(robot.links))[-8:]:
            selected.append(LinkState(name=str(link.name), index=idx, position=vector3(link.pose.p)))
    return selected


def refresh_link_positions(link_states: list[LinkState], robot) -> list[LinkState]:
    out: list[LinkState] = []
    for item in link_states:
        link = robot.links[item.index]
        out.append(LinkState(name=item.name, index=item.index, position=vector3(link.pose.p)))
    return out


def min_link_clearance(
    link_states: list[LinkState],
    obstacle_position: np.ndarray,
    obstacle_radius: float,
    link_radius: float,
    active: bool,
) -> float:
    if not active:
        return float("inf")
    clearances = []
    for link in link_states:
        dist = float(np.linalg.norm(link.position - obstacle_position))
        clearances.append(dist - float(obstacle_radius) - float(link_radius))
    return float(min(clearances)) if clearances else float("inf")


def make_nominal_path(
    robot,
    arm_indices: list[int],
    trajectory: str | None,
    num_waypoints: int = 90,
) -> np.ndarray:
    if trajectory:
        return load_arm_path(trajectory)
    q_start = get_arm_qpos(robot, arm_indices)
    limits = get_arm_qlimits(robot, arm_indices)
    return default_path_from_current(q_start, q_limits=limits, num_waypoints=num_waypoints)


def run_rollout(
    *,
    mode: str,
    demo_config: DemoConfig,
    command_config: CommandConfig,
    compliance_config: ContactComplianceConfig,
    obstacle_spec: CrossingSphereSpec,
    output_dir: Path,
    include_records: bool = False,
    bc_checkpoint: str | None = None,
) -> dict[str, Any]:
    env = build_maniskill_env(demo_config)
    recorder = None
    metrics = RolloutMetrics(
        mode=mode,
        goal_tolerance=float(demo_config.goal_tolerance),
        allowed_penetration=float(demo_config.allowed_penetration),
    )

    try:
        env.reset(seed=int(demo_config.seed))
        agent = env.unwrapped.agent
        robot = agent.robot
        scene = env.unwrapped.scene
        action_slices = build_action_slices(agent)
        arm_indices = get_arm_indices(agent)

        nominal_path = make_nominal_path(robot, arm_indices, demo_config.trajectory)
        set_arm_start(robot, scene, arm_indices, nominal_path[0])
        locked_qpos = flatten_state(robot.get_qpos()).astype(np.float32)
        lock_indices = (
            locked_joint_indices(agent, arm_indices)
            if bool(demo_config.lock_non_arm_joints)
            else []
        )
        lock_joint_names = [
            str(agent.robot.active_joints[idx].name)
            for idx in lock_indices
            if idx < len(agent.robot.active_joints)
        ]

        tracker = JointPathTracker(
            nominal_path,
            JointTrackerConfig(
                kp=float(command_config.nominal_kp),
                waypoint_tolerance=float(command_config.waypoint_tolerance),
                max_qdot=float(command_config.nominal_max_qdot),
            ),
        )
        smoother = VelocitySmoother(
            dim=7,
            config=SmootherConfig(
                dt=float(demo_config.dt),
                lowpass_alpha=float(command_config.command_lowpass_alpha),
                max_velocity=float(command_config.command_max_qdot),
                max_accel=float(command_config.command_max_accel),
            ),
        )
        compliance_controller = ContactComplianceController(compliance_config)
        bc_policy = BCResidualPolicy(bc_checkpoint) if mode == "bc_policy" and bc_checkpoint else None
        obstacle = CrossingSphereObstacle.build_in_scene(scene, obstacle_spec)
        pin_model = robot.create_pinocchio_model()
        link_states = select_arm_links(robot)

        if demo_config.record_gif:
            recorder = ThirdPersonCamera(
                scene,
                target_pos=np.asarray(demo_config.camera_target, dtype=np.float32),
                width=int(demo_config.record_width),
                height=int(demo_config.record_height),
                view=str(demo_config.camera_view),
            )

        final_q = nominal_path[0]
        start_wall = time.time()
        force_feedback_depth = 0.0
        force_feedback_level = 0.0
        qvel_tracking_error = 0.0
        prev_residual = np.zeros(7, dtype=np.float32)

        for step in range(int(demo_config.max_steps)):
            t = step * float(demo_config.dt)
            true_obstacle_state = obstacle.update(t)

            q_full = flatten_state(robot.get_qpos())
            q_arm = q_full[arm_indices].astype(np.float32)
            final_q = q_arm
            qdot_nom, q_target, tracker_done = tracker.command(q_arm)

            link_states = refresh_link_positions(link_states, robot)
            qdot_residual = np.zeros(7, dtype=np.float32)
            compliance_info = {
                "contact_level": 0.0,
                "contact_depth": 0.0,
                "min_clearance": min_link_clearance(
                    link_states,
                    true_obstacle_state.position,
                    true_obstacle_state.radius,
                    compliance_config.link_radius,
                    true_obstacle_state.active,
                ),
                "active_link": None,
                "nominal_scale": 1.0,
                "source": "nominal",
            }

            if mode in {"contact_compliance", "bc_policy"}:
                analytic_residual, compliance_info = compliance_controller.compute(
                    q_full=q_full,
                    arm_indices=arm_indices,
                    link_states=link_states,
                    obstacle=true_obstacle_state,
                    qdot_nominal=qdot_nom,
                    pinocchio_model=pin_model,
                    external_contact_depth=force_feedback_depth,
                    external_force_level=force_feedback_level,
                )
                if mode == "contact_compliance":
                    qdot_residual = analytic_residual
                elif bc_policy is not None:
                    active_contact = (
                        float(compliance_info.get("contact_depth", 0.0)) > 0.0
                        or float(compliance_info.get("force_level", 0.0)) > 0.0
                        or float(compliance_info.get("contact_level", 0.0)) > 0.0
                    )
                    residual_memory = float(np.linalg.norm(prev_residual)) > 1e-4
                    if active_contact:
                        qdot_residual = bc_policy.predict(
                            q_arm=q_arm,
                            q_target=q_target,
                            qdot_nominal=qdot_nom,
                            prev_residual=prev_residual,
                            compliance_info=compliance_info,
                            qvel_tracking_error=qvel_tracking_error,
                        )
                        qdot_residual = np.clip(
                            qdot_residual,
                            -float(compliance_config.max_residual_qdot),
                            float(compliance_config.max_residual_qdot),
                        )
                        compliance_info["source"] = (
                            f"bc_policy:{compliance_info.get('active_link')}"
                            if float(compliance_info.get("contact_level", 0.0)) > 0.0
                            else "bc_policy_recovery"
                        )
                    elif residual_memory:
                        qdot_residual = (
                            float(compliance_config.recovery_decay) * prev_residual
                        ).astype(np.float32)
                        compliance_info["source"] = "bc_policy_recovery"
                        compliance_info["nominal_scale"] = 1.0
                    else:
                        qdot_residual = np.zeros(7, dtype=np.float32)
                        compliance_info["source"] = "nominal"
                        compliance_info["nominal_scale"] = 1.0

            qdot_nom_for_command = qdot_nom
            if mode in {"contact_compliance", "bc_policy"}:
                qdot_nom_for_command = float(compliance_info["nominal_scale"]) * qdot_nom

            qdot_cmd = smoother.filter(qdot_nom_for_command + qdot_residual)
            prev_residual = qdot_residual.astype(np.float32)
            action = compose_action(env, action_slices, qdot_cmd)
            env.step(action)
            locked_joint_correction, locked_joint_velocity_norm = enforce_locked_joints(
                robot,
                scene,
                lock_indices,
                locked_qpos,
            )
            post_qvel_arm = get_arm_qvel(robot, arm_indices)
            qvel_tracking_error = float(np.linalg.norm(qdot_cmd - post_qvel_arm))

            if parse_render_mode(demo_config.render_mode) == "human":
                env.render()

            if recorder is not None and step % int(max(demo_config.record_stride, 1)) == 0:
                recorder.capture()

            post_links = refresh_link_positions(link_states, robot)
            actual_clearance = min_link_clearance(
                post_links,
                true_obstacle_state.position,
                true_obstacle_state.radius,
                compliance_config.link_radius,
                true_obstacle_state.active,
            )
            measured_contact_depth = max(0.0, -float(actual_clearance))
            measured_force_level = float(
                np.clip(
                    (
                        qvel_tracking_error
                        - float(compliance_config.force_proxy_threshold)
                    )
                    / max(float(compliance_config.force_proxy_scale), 1e-6),
                    0.0,
                    1.0,
                )
            )
            contact_feedback_available = (
                measured_contact_depth > 0.0 or force_feedback_depth > 0.0
            )
            if not contact_feedback_available:
                measured_force_level = 0.0
            elif (
                measured_contact_depth <= 0.0
                and actual_clearance > float(compliance_config.force_proxy_max_clearance)
            ):
                measured_force_level = 0.0
            if measured_contact_depth > 0.0 or measured_force_level > 0.0:
                force_feedback_depth = max(
                    measured_contact_depth,
                    measured_force_level * float(compliance_config.force_proxy_depth_scale),
                )
                force_feedback_level = max(
                    measured_force_level,
                    min(
                        1.0,
                        measured_contact_depth
                        / max(float(compliance_config.penetration_scale), 1e-6),
                    ),
                )
            else:
                force_feedback_depth *= float(compliance_config.force_memory_decay)
                force_feedback_level *= float(compliance_config.force_memory_decay)
                if force_feedback_depth < 1e-4:
                    force_feedback_depth = 0.0
                if force_feedback_level < 1e-3:
                    force_feedback_level = 0.0
            min_clearance_value = min(float(compliance_info["min_clearance"]), actual_clearance)
            active_link = compliance_info["active_link"]

            metrics.add(
                t=t,
                q_arm=q_arm,
                q_target=q_target,
                qdot_nom=qdot_nom,
                qdot_residual=qdot_residual,
                qdot_cmd=qdot_cmd,
                min_clearance=min_clearance_value,
                risk=float(compliance_info["contact_level"]),
                active_link=active_link,
                feedback_confidence=1.0,
                feedback_source=str(compliance_info.get("source", "unknown")),
                contact_depth=float(compliance_info.get("contact_depth", 0.0)),
                force_proxy_level=float(compliance_info.get("force_level", 0.0)),
                qvel_tracking_error=qvel_tracking_error,
                locked_joint_correction=locked_joint_correction,
                locked_joint_velocity_norm=locked_joint_velocity_norm,
            )

            final_error = float(np.linalg.norm(tracker.final_target - q_arm))
            if (
                not bool(demo_config.no_early_stop)
                and tracker_done
                and final_error <= float(demo_config.goal_tolerance)
            ):
                break

        summary = metrics.finalize(final_q=final_q, goal_q=tracker.final_target)
        summary["wall_time"] = float(time.time() - start_wall)
        summary["trajectory_source"] = demo_config.trajectory or "default_interpolated"
        summary["lock_non_arm_joints"] = bool(demo_config.lock_non_arm_joints)
        summary["locked_joint_names"] = lock_joint_names

        if recorder is not None:
            gif_path = output_dir / f"{mode}.gif"
            recorder.save_gif(gif_path, fps=float(demo_config.record_fps))
            summary["gif"] = str(gif_path)

        records_path = output_dir / f"{mode}_records.json"
        with records_path.open("w", encoding="utf-8") as f:
            json.dump(metrics.to_json_dict(include_records=include_records), f, indent=2)
        summary["records"] = str(records_path)

        return summary

    finally:
        env.close()


def run_comparison(
    demo_config: DemoConfig,
    command_config: CommandConfig | None = None,
    compliance_config: ContactComplianceConfig | None = None,
    obstacle_spec: CrossingSphereSpec | None = None,
    include_records: bool = False,
    bc_checkpoint: str | None = None,
) -> dict[str, Any]:
    command_config = command_config or CommandConfig()
    compliance_config = compliance_config or ContactComplianceConfig()
    obstacle_spec = obstacle_spec or CrossingSphereSpec()
    output_dir = ensure_dir(demo_config.output_dir)

    results: dict[str, Any] = {
        "config": {
            "env_id": demo_config.env_id,
            "seed": demo_config.seed,
            "trajectory": demo_config.trajectory,
            "camera_view": demo_config.camera_view,
            "camera_target": list(demo_config.camera_target),
            "allowed_penetration": demo_config.allowed_penetration,
            "obstacle": obstacle_spec.__dict__,
            "controller": "contact_only_compliance",
            "rl_finetuning": "PPO",
            "bc_checkpoint": bc_checkpoint,
            "lock_non_arm_joints": bool(demo_config.lock_non_arm_joints),
        },
        "rollouts": {},
    }

    modes = ["baseline", "contact_compliance"]
    if bc_checkpoint:
        modes.append("bc_policy")

    for mode in modes:
        results["rollouts"][mode] = run_rollout(
            mode=mode,
            demo_config=demo_config,
            command_config=command_config,
            compliance_config=compliance_config,
            obstacle_spec=obstacle_spec,
            output_dir=output_dir,
            include_records=include_records,
            bc_checkpoint=bc_checkpoint,
        )

    metrics_path = output_dir / "metrics.json"
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    results["metrics_path"] = str(metrics_path)
    return results
