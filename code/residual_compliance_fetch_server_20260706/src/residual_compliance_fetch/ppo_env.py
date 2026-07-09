from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from residual_compliance_fetch.controllers import (
    ContactComplianceConfig,
    ContactComplianceController,
    JointPathTracker,
    JointTrackerConfig,
    SmootherConfig,
    VelocitySmoother,
)
from residual_compliance_fetch.maniskill_demo import (
    CommandConfig,
    DemoConfig,
    build_action_slices,
    build_maniskill_env,
    compose_action,
    enforce_locked_joints,
    get_arm_indices,
    get_arm_qpos,
    get_arm_qvel,
    locked_joint_indices,
    make_nominal_path,
    min_link_clearance,
    refresh_link_positions,
    select_arm_links,
    set_arm_start,
)
from residual_compliance_fetch.metrics import RolloutMetrics
from residual_compliance_fetch.obstacles import (
    CrossingSphereObstacle,
    CrossingSphereSpec,
    randomized_contact_heavy_crossing_sphere,
    randomized_crossing_sphere,
)
from residual_compliance_fetch.utils import ensure_dir, flatten_state
from residual_compliance_fetch.visualization import ThirdPersonCamera


ARM_DOF = 7
DEFAULT_LINK_VOCAB = (
    "none",
    "shoulder_pan",
    "shoulder_lift",
    "upperarm",
    "elbow",
    "forearm",
    "wrist",
    "gripper_link",
)


@dataclass
class PPORewardConfig:
    alive_penalty: float = 0.01
    progress_scale: float = 8.0
    success_bonus: float = 45.0
    collision_penalty: float = 55.0
    penetration_scale: float = 900.0
    contact_step_penalty: float = 0.04
    residual_penalty: float = 0.025
    jerk_penalty: float = 0.020
    final_error_penalty: float = 1.5
    ignored_action_penalty: float = 0.004


@dataclass
class PPOEnvConfig:
    demo: DemoConfig = field(default_factory=DemoConfig)
    command: CommandConfig = field(default_factory=CommandConfig)
    compliance: ContactComplianceConfig = field(default_factory=ContactComplianceConfig)
    reward: PPORewardConfig = field(default_factory=PPORewardConfig)
    obstacle_sampler: str = "contact_heavy"
    action_scale: float | None = None
    use_nominal_softening: bool = True


def load_bc_metadata(checkpoint_path: str | Path | None) -> dict[str, Any]:
    if checkpoint_path is None:
        return {}
    import torch

    path = Path(checkpoint_path)
    if not path.exists():
        raise FileNotFoundError(f"BC checkpoint not found: {path}")
    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    return {
        "obs_mean": np.asarray(ckpt.get("obs_mean"), dtype=np.float32),
        "obs_std": np.asarray(ckpt.get("obs_std"), dtype=np.float32),
        "link_vocab": [str(x) for x in ckpt.get("link_vocab", DEFAULT_LINK_VOCAB)],
        "hidden_sizes": tuple(int(x) for x in ckpt.get("hidden_sizes", (256, 256))),
        "obs_dim": int(ckpt.get("obs_dim", 0)),
        "action_dim": int(ckpt.get("action_dim", ARM_DOF)),
    }


class ResidualComplianceFetchPPOEnv(gym.Env):
    """Gymnasium env for contact-only residual compliance PPO.

    The nominal tracker, dynamic obstacle, locked Fetch body joints, contact feedback, metrics,
    and optional GIF camera are the same components used by the analytic/BC demo. The policy only
    controls a 7D residual arm joint velocity, gated to zero before contact-like feedback exists.
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        env_config: PPOEnvConfig | None = None,
        *,
        seed: int = 0,
        link_vocab: list[str] | tuple[str, ...] | None = None,
        obs_mean: np.ndarray | None = None,
        obs_std: np.ndarray | None = None,
        record_gif: bool = False,
        output_dir: str | Path | None = None,
    ) -> None:
        super().__init__()
        self.cfg = env_config or PPOEnvConfig()
        self.seed_value = int(seed)
        self.rng = np.random.default_rng(self.seed_value)
        self.link_vocab = list(link_vocab or DEFAULT_LINK_VOCAB)
        if "none" not in self.link_vocab:
            self.link_vocab = ["none"] + self.link_vocab
        self.link_to_index = {name: idx for idx, name in enumerate(self.link_vocab)}
        self.obs_mean = None if obs_mean is None else np.asarray(obs_mean, dtype=np.float32)
        self.obs_std = None if obs_std is None else np.maximum(np.asarray(obs_std, dtype=np.float32), 1e-6)
        self.record_gif = bool(record_gif)
        self.output_dir = None if output_dir is None else Path(output_dir)

        obs_dim = ARM_DOF * 5 + 5 + len(self.link_vocab)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
        )
        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(ARM_DOF,), dtype=np.float32
        )

        self.env = None
        self.agent = None
        self.robot = None
        self.scene = None
        self.action_slices: dict[str, slice] = {}
        self.arm_indices: list[int] = []
        self.lock_indices: list[int] = []
        self.locked_qpos: np.ndarray | None = None
        self.lock_joint_names: list[str] = []
        self.nominal_path: np.ndarray | None = None
        self.tracker: JointPathTracker | None = None
        self.smoother: VelocitySmoother | None = None
        self.compliance_controller: ContactComplianceController | None = None
        self.obstacle: CrossingSphereObstacle | None = None
        self.obstacle_spec: CrossingSphereSpec | None = None
        self.pin_model = None
        self.link_states = []
        self.metrics: RolloutMetrics | None = None
        self.recorder: ThirdPersonCamera | None = None
        self.step_count = 0
        self.force_feedback_depth = 0.0
        self.force_feedback_level = 0.0
        self.qvel_tracking_error = 0.0
        self.prev_residual = np.zeros(ARM_DOF, dtype=np.float32)
        self.prev_policy_action = np.zeros(ARM_DOF, dtype=np.float32)
        self.cached_state: dict[str, Any] | None = None
        self.cached_obs: np.ndarray | None = None
        self.episode_summary: dict[str, Any] | None = None

    def _sample_obstacle(self) -> CrossingSphereSpec:
        if self.cfg.obstacle_sampler == "broad":
            return randomized_crossing_sphere(self.rng)
        if self.cfg.obstacle_sampler == "contact_heavy":
            return randomized_contact_heavy_crossing_sphere(self.rng)
        raise ValueError(f"Unknown obstacle sampler: {self.cfg.obstacle_sampler}")

    def _setup_episode(self) -> None:
        self.env = build_maniskill_env(self.cfg.demo)
        self.env.reset(seed=int(self.seed_value + self.rng.integers(0, 1_000_000)))
        self.agent = self.env.unwrapped.agent
        self.robot = self.agent.robot
        self.scene = self.env.unwrapped.scene
        self.action_slices = build_action_slices(self.agent)
        self.arm_indices = get_arm_indices(self.agent)

        self.nominal_path = make_nominal_path(
            self.robot, self.arm_indices, self.cfg.demo.trajectory
        )
        set_arm_start(self.robot, self.scene, self.arm_indices, self.nominal_path[0])
        self.locked_qpos = flatten_state(self.robot.get_qpos()).astype(np.float32)
        self.lock_indices = (
            locked_joint_indices(self.agent, self.arm_indices)
            if bool(self.cfg.demo.lock_non_arm_joints)
            else []
        )
        self.lock_joint_names = [
            str(self.agent.robot.active_joints[idx].name)
            for idx in self.lock_indices
            if idx < len(self.agent.robot.active_joints)
        ]

        self.tracker = JointPathTracker(
            self.nominal_path,
            JointTrackerConfig(
                kp=float(self.cfg.command.nominal_kp),
                waypoint_tolerance=float(self.cfg.command.waypoint_tolerance),
                max_qdot=float(self.cfg.command.nominal_max_qdot),
            ),
        )
        self.smoother = VelocitySmoother(
            dim=ARM_DOF,
            config=SmootherConfig(
                dt=float(self.cfg.demo.dt),
                lowpass_alpha=float(self.cfg.command.command_lowpass_alpha),
                max_velocity=float(self.cfg.command.command_max_qdot),
                max_accel=float(self.cfg.command.command_max_accel),
            ),
        )
        self.compliance_controller = ContactComplianceController(self.cfg.compliance)
        self.obstacle_spec = self._sample_obstacle()
        self.obstacle = CrossingSphereObstacle.build_in_scene(
            self.scene,
            self.obstacle_spec,
            add_visual=not bool(self.cfg.demo.collision_only_visuals),
        )
        self.pin_model = self.robot.create_pinocchio_model()
        self.link_states = select_arm_links(self.robot)

        self.metrics = RolloutMetrics(
            mode="ppo_policy",
            goal_tolerance=float(self.cfg.demo.goal_tolerance),
            allowed_penetration=float(self.cfg.demo.allowed_penetration),
        )
        self.recorder = None
        if self.record_gif:
            self.recorder = ThirdPersonCamera(
                self.scene,
                target_pos=np.asarray(self.cfg.demo.camera_target, dtype=np.float32),
                width=int(self.cfg.demo.record_width),
                height=int(self.cfg.demo.record_height),
                view=str(self.cfg.demo.camera_view),
            )

        self.step_count = 0
        self.force_feedback_depth = 0.0
        self.force_feedback_level = 0.0
        self.qvel_tracking_error = 0.0
        self.prev_residual[:] = 0.0
        self.prev_policy_action[:] = 0.0
        self.episode_summary = None
        self.cached_obs = self._compute_observation()

    def _link_one_hot(self, active_link: str | None) -> np.ndarray:
        link_name = "none" if active_link is None else str(active_link)
        idx = self.link_to_index.get(link_name)
        if idx is None:
            for key, value in self.link_to_index.items():
                if key != "none" and (key in link_name or link_name in key):
                    idx = value
                    break
        if idx is None:
            idx = self.link_to_index["none"]
        one_hot = np.zeros(len(self.link_vocab), dtype=np.float32)
        one_hot[int(idx)] = 1.0
        return one_hot

    def _normalize_obs(self, obs: np.ndarray) -> np.ndarray:
        obs = np.asarray(obs, dtype=np.float32)
        if self.obs_mean is None or self.obs_std is None:
            return obs
        if self.obs_mean.shape != obs.shape:
            raise ValueError(f"obs_mean shape {self.obs_mean.shape} != obs shape {obs.shape}")
        return ((obs - self.obs_mean) / self.obs_std).astype(np.float32)

    def _compute_observation(self) -> np.ndarray:
        assert self.robot is not None
        assert self.tracker is not None
        assert self.obstacle is not None
        assert self.compliance_controller is not None

        t = self.step_count * float(self.cfg.demo.dt)
        true_obstacle_state = self.obstacle.update(t)
        q_full = flatten_state(self.robot.get_qpos())
        q_arm = q_full[self.arm_indices].astype(np.float32)
        qdot_nom, q_target, tracker_done = self.tracker.command(q_arm)
        self.link_states = refresh_link_positions(self.link_states, self.robot)

        compliance_info = {
            "contact_level": 0.0,
            "contact_depth": 0.0,
            "force_level": 0.0,
            "min_clearance": min_link_clearance(
                self.link_states,
                true_obstacle_state.position,
                true_obstacle_state.radius,
                self.cfg.compliance.link_radius,
                true_obstacle_state.active,
            ),
            "active_link": None,
            "nominal_scale": 1.0,
            "source": "nominal",
        }
        _, compliance_info = self.compliance_controller.compute(
            q_full=q_full,
            arm_indices=self.arm_indices,
            link_states=self.link_states,
            obstacle=true_obstacle_state,
            qdot_nominal=qdot_nom,
            pinocchio_model=self.pin_model,
            external_contact_depth=self.force_feedback_depth,
            external_force_level=self.force_feedback_level,
        )
        contact_depth = float(compliance_info.get("contact_depth", 0.0))
        force_level = float(compliance_info.get("force_level", 0.0))
        contact_level = float(compliance_info.get("contact_level", 0.0))
        contact_flag = float(
            contact_depth > 1e-8 or force_level > 1e-8 or contact_level > 1e-8
        )
        raw_obs = np.concatenate(
            [
                q_arm,
                q_target,
                q_target - q_arm,
                qdot_nom,
                self.prev_residual.astype(np.float32),
                np.asarray(
                    [
                        contact_depth,
                        force_level,
                        float(self.qvel_tracking_error),
                        contact_level,
                        contact_flag,
                    ],
                    dtype=np.float32,
                ),
                self._link_one_hot(compliance_info.get("active_link")),
            ]
        ).astype(np.float32)
        self.cached_state = {
            "t": t,
            "q_full": q_full,
            "q_arm": q_arm,
            "qdot_nom": qdot_nom,
            "q_target": q_target,
            "tracker_done": bool(tracker_done),
            "obstacle_state": true_obstacle_state,
            "compliance_info": compliance_info,
            "final_error_before": float(np.linalg.norm(self.tracker.final_target - q_arm)),
        }
        return self._normalize_obs(raw_obs)

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        if seed is not None:
            self.seed_value = int(seed)
            self.rng = np.random.default_rng(self.seed_value)
        self.close()
        self._setup_episode()
        return self.cached_obs.copy(), {"obstacle": self.obstacle_spec.__dict__}

    def _update_contact_feedback(self, actual_clearance: float, qdot_cmd: np.ndarray) -> None:
        assert self.robot is not None
        post_qvel_arm = get_arm_qvel(self.robot, self.arm_indices)
        self.qvel_tracking_error = float(np.linalg.norm(qdot_cmd - post_qvel_arm))
        measured_contact_depth = max(0.0, -float(actual_clearance))
        measured_force_level = float(
            np.clip(
                (
                    self.qvel_tracking_error
                    - float(self.cfg.compliance.force_proxy_threshold)
                )
                / max(float(self.cfg.compliance.force_proxy_scale), 1e-6),
                0.0,
                1.0,
            )
        )
        contact_feedback_available = (
            measured_contact_depth > 0.0 or self.force_feedback_depth > 0.0
        )
        if not contact_feedback_available:
            measured_force_level = 0.0
        elif (
            measured_contact_depth <= 0.0
            and actual_clearance > float(self.cfg.compliance.force_proxy_max_clearance)
        ):
            measured_force_level = 0.0

        if measured_contact_depth > 0.0 or measured_force_level > 0.0:
            self.force_feedback_depth = max(
                measured_contact_depth,
                measured_force_level * float(self.cfg.compliance.force_proxy_depth_scale),
            )
            self.force_feedback_level = max(
                measured_force_level,
                min(
                    1.0,
                    measured_contact_depth
                    / max(float(self.cfg.compliance.penetration_scale), 1e-6),
                ),
            )
        else:
            self.force_feedback_depth *= float(self.cfg.compliance.force_memory_decay)
            self.force_feedback_level *= float(self.cfg.compliance.force_memory_decay)
            if self.force_feedback_depth < 1e-4:
                self.force_feedback_depth = 0.0
            if self.force_feedback_level < 1e-3:
                self.force_feedback_level = 0.0

    def _reward(
        self,
        *,
        progress: float,
        final_error: float,
        max_penetration: float,
        active_contact: bool,
        severe_collision: bool,
        success: bool,
        policy_action: np.ndarray,
        residual: np.ndarray,
    ) -> float:
        rcfg = self.cfg.reward
        action_delta = np.asarray(policy_action, dtype=np.float32) - self.prev_policy_action
        reward = -float(rcfg.alive_penalty)
        reward += float(rcfg.progress_scale) * float(progress)
        reward -= float(rcfg.penetration_scale) * float(max_penetration) ** 2
        reward -= float(rcfg.final_error_penalty) * float(final_error) / max(int(self.cfg.demo.max_steps), 1)
        if active_contact:
            reward -= float(rcfg.contact_step_penalty)
        else:
            reward -= float(rcfg.ignored_action_penalty) * float(np.linalg.norm(policy_action))
        reward -= float(rcfg.residual_penalty) * float(np.linalg.norm(residual))
        reward -= float(rcfg.jerk_penalty) * float(np.linalg.norm(action_delta))
        if severe_collision:
            reward -= float(rcfg.collision_penalty)
        if success:
            reward += float(rcfg.success_bonus)
        return float(reward)

    def step(self, action: np.ndarray):
        assert self.env is not None
        assert self.robot is not None
        assert self.scene is not None
        assert self.smoother is not None
        assert self.metrics is not None
        assert self.cached_state is not None

        state = self.cached_state
        policy_action = np.clip(np.asarray(action, dtype=np.float32), -1.0, 1.0)
        compliance_info = dict(state["compliance_info"])
        active_contact = (
            float(compliance_info.get("contact_depth", 0.0)) > 0.0
            or float(compliance_info.get("force_level", 0.0)) > 0.0
            or float(compliance_info.get("contact_level", 0.0)) > 0.0
        )
        action_scale = (
            float(self.cfg.action_scale)
            if self.cfg.action_scale is not None
            else float(self.cfg.compliance.max_residual_qdot)
        )
        if active_contact:
            qdot_residual = np.clip(
                policy_action * action_scale,
                -float(self.cfg.compliance.max_residual_qdot),
                float(self.cfg.compliance.max_residual_qdot),
            ).astype(np.float32)
            compliance_info["source"] = f"ppo_policy:{compliance_info.get('active_link')}"
        elif float(np.linalg.norm(self.prev_residual)) > 1e-4:
            qdot_residual = (
                float(self.cfg.compliance.recovery_decay) * self.prev_residual
            ).astype(np.float32)
            compliance_info["source"] = "ppo_policy_recovery"
            compliance_info["nominal_scale"] = 1.0
        else:
            qdot_residual = np.zeros(ARM_DOF, dtype=np.float32)
            compliance_info["source"] = "nominal"
            compliance_info["nominal_scale"] = 1.0

        qdot_nom = np.asarray(state["qdot_nom"], dtype=np.float32)
        qdot_nom_for_command = qdot_nom
        if bool(self.cfg.use_nominal_softening):
            qdot_nom_for_command = float(compliance_info.get("nominal_scale", 1.0)) * qdot_nom
        qdot_cmd = self.smoother.filter(qdot_nom_for_command + qdot_residual)
        self.prev_residual = qdot_residual.astype(np.float32)

        self.env.step(compose_action(self.env, self.action_slices, qdot_cmd))
        locked_joint_correction, locked_joint_velocity_norm = enforce_locked_joints(
            self.robot,
            self.scene,
            self.lock_indices,
            self.locked_qpos,
        )

        if self.recorder is not None and self.step_count % int(max(self.cfg.demo.record_stride, 1)) == 0:
            self.recorder.capture()

        post_links = refresh_link_positions(self.link_states, self.robot)
        obstacle_state = state["obstacle_state"]
        actual_clearance = min_link_clearance(
            post_links,
            obstacle_state.position,
            obstacle_state.radius,
            self.cfg.compliance.link_radius,
            obstacle_state.active,
        )
        self._update_contact_feedback(actual_clearance, qdot_cmd)
        min_clearance_value = min(float(compliance_info.get("min_clearance", actual_clearance)), actual_clearance)
        max_penetration = max(0.0, -float(min_clearance_value))
        severe_collision = max_penetration > float(self.cfg.demo.allowed_penetration)

        self.step_count += 1
        final_q = get_arm_qpos(self.robot, self.arm_indices)
        final_error = float(np.linalg.norm(self.tracker.final_target - final_q))
        goal_reached = (
            bool(state["tracker_done"])
            and final_error <= float(self.cfg.demo.goal_tolerance)
        )
        terminated = bool(goal_reached or severe_collision)
        truncated = bool(self.step_count >= int(self.cfg.demo.max_steps))
        success = bool(goal_reached and not severe_collision)
        progress = float(state["final_error_before"]) - final_error

        self.metrics.add(
            t=float(state["t"]),
            q_arm=np.asarray(state["q_arm"], dtype=np.float32),
            q_target=np.asarray(state["q_target"], dtype=np.float32),
            qdot_nom=qdot_nom,
            qdot_residual=qdot_residual,
            qdot_cmd=qdot_cmd,
            min_clearance=min_clearance_value,
            risk=float(compliance_info.get("contact_level", 0.0)),
            active_link=compliance_info.get("active_link"),
            feedback_confidence=1.0,
            feedback_source=str(compliance_info.get("source", "unknown")),
            contact_depth=float(compliance_info.get("contact_depth", 0.0)),
            force_proxy_level=float(compliance_info.get("force_level", 0.0)),
            qvel_tracking_error=float(self.qvel_tracking_error),
            locked_joint_correction=locked_joint_correction,
            locked_joint_velocity_norm=locked_joint_velocity_norm,
        )

        reward = self._reward(
            progress=progress,
            final_error=final_error,
            max_penetration=max_penetration,
            active_contact=active_contact,
            severe_collision=severe_collision,
            success=success,
            policy_action=policy_action,
            residual=qdot_residual,
        )
        self.prev_policy_action = policy_action.astype(np.float32)

        info = {
            "success": success,
            "collision": severe_collision,
            "max_penetration": max_penetration,
            "final_error": final_error,
            "contact": bool(active_contact or max_penetration > 0.0),
            "obstacle": self.obstacle_spec.__dict__ if self.obstacle_spec is not None else {},
        }
        if terminated or truncated:
            self.episode_summary = self.metrics.finalize(
                final_q=final_q, goal_q=self.tracker.final_target
            )
            self.episode_summary.update(
                {
                    "terminated": bool(terminated),
                    "truncated": bool(truncated),
                    "obstacle": info["obstacle"],
                    "locked_joint_names": self.lock_joint_names,
                }
            )
            obs = self.cached_obs.copy()
            info["episode_summary"] = self.episode_summary
        else:
            obs = self._compute_observation()
            self.cached_obs = obs
        return obs.astype(np.float32), float(reward), terminated, truncated, info

    def write_episode_artifacts(
        self,
        output_dir: str | Path | None = None,
        *,
        include_records: bool = True,
        gif_name: str = "ppo_policy.gif",
    ) -> dict[str, Any]:
        out = ensure_dir(output_dir or self.output_dir or "outputs/ppo_episode")
        summary = dict(self.episode_summary or {})
        if self.recorder is not None:
            gif_path = out / gif_name
            self.recorder.save_gif(gif_path, fps=float(self.cfg.demo.record_fps))
            summary["gif"] = str(gif_path)
        if self.metrics is not None:
            records_path = out / "ppo_policy_records.json"
            with records_path.open("w", encoding="utf-8") as f:
                json.dump(self.metrics.to_json_dict(include_records=include_records), f, indent=2)
            summary["records"] = str(records_path)
        summary_path = out / "ppo_policy_summary.json"
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        summary["summary_path"] = str(summary_path)
        return summary

    def close(self) -> None:
        if self.env is not None:
            self.env.close()
        self.env = None
        self.agent = None
        self.robot = None
        self.scene = None
