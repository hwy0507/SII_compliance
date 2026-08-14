"""Step-wise MuJoCo environment for deployable six-dimensional stiffness PPO.

The policy sees only the 51-D proprioceptive contract in
``stiffness_training_core``.  Rod contact, rod force, rod motion, and obstacle
geometry are deliberately *not* part of the observation.  They are retained
only for physical simulation and terminal benchmark validity diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gymnasium as gym
import mujoco
import numpy as np

from run_benchmark import (
    ARM_DOF,
    CONTROL_DT,
    EPS,
    TORQUE_LIMITS,
    SixDVirtualCarriage,
    VMCConfig,
    body_jacobian,
    body_twist,
    rate_limit_torque,
    so3_log,
    torque_feasible_scale,
)
from run_grasp_impact_benchmark import (
    LIFT_COMPLETE_TIME_S,
    TABLE_TOP_Z,
    TARGET_START_Z,
    PickLiftCarryReference,
)
from run_rod_perturbation_benchmark import (
    _apply_body_force,
    _saturated_translation_spring,
    _saturate_vector_norm,
    make_rod_model,
    rod_contact_diagnostics,
    rod_motion,
)
from stiffness_training_core import (
    DriveResidualActionConfig,
    EFFECTIVE_COLLISION_GATE,
    StiffnessActionConfig,
    action_to_recovery_drive,
    action_to_kappa,
    deployment_observation,
    deployment_observation_with_drive_residual,
)


RL_DT = 0.040  # Policy update rate: 25 Hz, ten 4-ms MuJoCo steps.
PHYSICS_STEPS_PER_ACTION = int(round(RL_DT / CONTROL_DT))
SIM_TIME_S = 6.20
GRASP_TIME_S = 2.40
CONTACT_TIME_CONSTANT_S = 0.015
CARRIAGE_MASS_KG = 1.0
ROD_PROFILE_DURATION_S = 0.64

# CEM is used only to choose a conservative initial operating point.  PPO
# still learns state feedback; no collision phase or timed recovery schedule
# is exposed to the policy.
WARM_START_KAPPA = (27.579838, 52.550787, 48.699427, 35.859580, 40.719830, 34.766858)
CONTACT_CARRIAGE_DRIVE_SCALE = 8.0
RECOVERY_CARRIAGE_DRIVE_SCALE = 14.0


@dataclass(frozen=True)
class Fixture:
    """Physical rod fixture sampled independently of the policy."""

    rod_stroke_m: float
    rod_height_m: float
    rod_start_time_s: float
    grasp_time_s: float = GRASP_TIME_S


def default_fixtures() -> tuple[Fixture, ...]:
    """Calibrated collision range used by the manifest's train split.

    The policy cannot alter a fixture.  Terminal success is counted only when
    the measured force and impulse pass the predeclared effective-collision
    gate, so grazing contact cannot improve the learning objective.
    """

    # A frozen-policy physical screening run accepted indices 1--4 below:
    # each has a matched no-rod success, task success under the rod, and meets
    # both the 15 N / 0.45 Ns effective-contact thresholds.  The softer 0.155
    # m case was rejected for ineffective contact; the 0.180 m case was
    # rejected because the same task gate failed.  Keeping either would make
    # a terminal penalty depend on an exogenous fixture rather than the action.
    return (
        Fixture(0.160, 0.539, 1.055), Fixture(0.165, 0.540, 1.070),
        Fixture(0.170, 0.541, 1.085), Fixture(0.175, 0.542, 1.100),
    )


class PandaSixDStiffnessEnv(gym.Env[np.ndarray, np.ndarray]):
    """Panda grasp-under-rod-contact task with 6-D stiffness actions.

    Translation uses the MuJoCo explicit three-axis virtual carriage already
    validated by the benchmark.  Rotations use the stable controller-integrated
    SO(3) carriage, yielding six independently adjustable nonlinear spring
    channels without reintroducing the unvalidated ball-joint chatter mode.
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        menagerie: str | Path,
        fixtures: tuple[Fixture, ...] | None = None,
        rod_enabled: bool = True,
        enable_drive_residual: bool = False,
        seed: int | None = None,
    ) -> None:
        super().__init__()
        self.menagerie = Path(menagerie)
        self.fixtures = fixtures or default_fixtures()
        self.rod_enabled = bool(rod_enabled)
        self.enable_drive_residual = bool(enable_drive_residual)
        if not self.fixtures:
            raise ValueError("at least one physical fixture is required")
        self.action_config = StiffnessActionConfig(base_kappa=WARM_START_KAPPA)
        self.drive_action_config = DriveResidualActionConfig(base_recovery_drive_scale=RECOVERY_CARRIAGE_DRIVE_SCALE)
        self.config = VMCConfig(zeta=0.8, carriage_drive_k_translation=75.0 * CONTACT_CARRIAGE_DRIVE_SCALE)
        action_dimension = 7 if self.enable_drive_residual else 6
        observation_dimension = 52 if self.enable_drive_residual else 51
        self.action_space = gym.spaces.Box(-1.0, 1.0, shape=(action_dimension,), dtype=np.float32)
        self.observation_space = gym.spaces.Box(-10.0, 10.0, shape=(observation_dimension,), dtype=np.float32)
        self.model: mujoco.MjModel | None = None
        self.data: mujoco.MjData | None = None
        self.ids: dict[str, int] = {}
        self.controller: SixDVirtualCarriage | None = None
        self.reference: PickLiftCarryReference | None = None
        self.fixture = self.fixtures[0]
        self.step_count = 0
        self.previous_action = np.zeros(6, dtype=float)
        self.previous_drive_action = 0.0
        self.current_kappa = np.asarray(WARM_START_KAPPA, dtype=float)
        self.current_recovery_drive_scale = RECOVERY_CARRIAGE_DRIVE_SCALE
        self.previous_torque = np.zeros(ARM_DOF, dtype=float)
        self.previous_twist = np.zeros(6, dtype=float)
        self.previous_acceleration = np.zeros(6, dtype=float)
        self.peak_force = 0.0
        self.contact_impulse = 0.0
        self.peak_torque = 0.0
        self.peak_jerk = 0.0
        self.hard_limit_seen = False
        self.rod_hand_observed = False
        self.previous_position_error = 0.0
        self.cumulative_log_kappa_deviation = 0.0
        self.post_release_step_count = 0
        self.cumulative_residual_gate = 0.0
        self.cumulative_log_drive_deviation = 0.0
        self._explicit_qpos = np.zeros(3, dtype=int)
        self._explicit_dof = np.zeros(3, dtype=int)
        self._target_qpos = 0
        self._target_dof = 0
        self._rod_ctrl = 0
        self._obstacle_mocap = -1
        self._carriage_mocap = -1
        self._hand_id = -1
        self._hand_geom_id = -1
        self._rod_geom_id = -1
        self._target_body_id = -1
        self.reset(seed=seed)

    def _build_scene(self) -> None:
        self.model, self.data = make_rod_model(
            self.menagerie,
            CONTACT_TIME_CONSTANT_S,
            self.fixture.rod_height_m,
            explicit_translational_carriage=True,
            carriage_mass_kg=CARRIAGE_MASS_KG,
        )
        model, data = self.model, self.data
        object_ids = {
            "hand": (mujoco.mjtObj.mjOBJ_BODY, "hand"),
            "hand_geom": (mujoco.mjtObj.mjOBJ_GEOM, "hand_collision"),
            "target_body": (mujoco.mjtObj.mjOBJ_BODY, "target_object"),
            "target_freejoint": (mujoco.mjtObj.mjOBJ_JOINT, "target_freejoint"),
            "rod_geom": (mujoco.mjtObj.mjOBJ_GEOM, "rod_geom"),
            "moving_obstacle": (mujoco.mjtObj.mjOBJ_BODY, "moving_obstacle"),
            "virtual_carriage": (mujoco.mjtObj.mjOBJ_BODY, "virtual_carriage"),
            "explicit_carriage": (mujoco.mjtObj.mjOBJ_BODY, "explicit_carriage"),
        }
        self.ids = {name: mujoco.mj_name2id(model, kind, label) for name, (kind, label) in object_ids.items()}
        if min(self.ids.values()) < 0:
            raise RuntimeError("RL rod scene IDs were not resolved")
        self._hand_id = self.ids["hand"]
        self._hand_geom_id = self.ids["hand_geom"]
        self._rod_geom_id = self.ids["rod_geom"]
        self._target_body_id = self.ids["target_body"]
        self._target_qpos = model.jnt_qposadr[self.ids["target_freejoint"]]
        self._target_dof = model.jnt_dofadr[self.ids["target_freejoint"]]
        self._explicit_qpos = np.array([
            model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"explicit_carriage_{axis}_slide")]
            for axis in "xyz"
        ], dtype=int)
        self._explicit_dof = np.array([
            model.jnt_dofadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"explicit_carriage_{axis}_slide")]
            for axis in "xyz"
        ], dtype=int)
        self._rod_ctrl = ARM_DOF + 1
        if model.nu != self._rod_ctrl + 1:
            raise RuntimeError("expected seven arm torques, a gripper, and a rod driver")
        self._obstacle_mocap = model.body_mocapid[self.ids["moving_obstacle"]]
        self._carriage_mocap = model.body_mocapid[self.ids["virtual_carriage"]]
        if self._obstacle_mocap < 0 or self._carriage_mocap < 0:
            raise RuntimeError("RL diagnostic mocap IDs were not resolved")
        data.qpos[self._target_qpos:self._target_qpos + 7] = [0.54, 0.0, TARGET_START_Z, 1.0, 0.0, 0.0, 0.0]
        data.qvel[self._target_dof:self._target_dof + 6] = 0.0
        mujoco.mj_forward(model, data)
        self.reference = PickLiftCarryReference(model, data, self._hand_id)
        nominal_position, nominal_rotation, nominal_linear, _ = self.reference.sample(0.0)
        data.qpos[self._explicit_qpos] = nominal_position
        data.qvel[self._explicit_dof] = nominal_linear
        mujoco.mj_forward(model, data)
        self.controller = SixDVirtualCarriage(
            self.config, self.current_kappa, data.xpos[self._hand_id].copy(), data.xmat[self._hand_id].reshape(3, 3).copy()
        )

    def _observation(self, time_s: float) -> np.ndarray:
        assert self.data is not None and self.reference is not None
        nominal_position, nominal_rotation, nominal_linear, nominal_angular = self.reference.sample(time_s)
        ee_position = self.data.xpos[self._hand_id].copy()
        ee_rotation = self.data.xmat[self._hand_id].reshape(3, 3).copy()
        ee_twist = body_twist(self.model, self.data, self._hand_id)
        carriage_position = self.data.qpos[self._explicit_qpos].copy()
        carriage_velocity = self.data.qvel[self._explicit_dof].copy()
        angular_displacement = so3_log(self.controller.rotation @ ee_rotation.T) if self.controller is not None else np.zeros(3)
        angular_velocity = self.controller.angular_velocity.copy() if self.controller is not None else np.zeros(3)
        fields = {
            "position_error_world": nominal_position - ee_position,
            "orientation_error_world": so3_log(nominal_rotation @ ee_rotation.T),
            "twist_error_world": np.concatenate([nominal_linear, nominal_angular]) - ee_twist,
            "joint_position": self.data.qpos[:ARM_DOF].copy(),
            "joint_velocity": self.data.qvel[:ARM_DOF].copy(),
            "carriage_displacement": np.concatenate([carriage_position - ee_position, angular_displacement]),
            "carriage_velocity": np.concatenate([carriage_velocity, angular_velocity]),
            "applied_torque_ratio": np.abs(self.previous_torque) / TORQUE_LIMITS,
        }
        observation = (
            deployment_observation_with_drive_residual(
                **fields, previous_stiffness_action=self.previous_action, previous_drive_action=self.previous_drive_action,
            )
            if self.enable_drive_residual
            else deployment_observation(**fields, previous_action=self.previous_action)
        )
        return observation.astype(np.float32)

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        requested = None if options is None else options.get("fixture_index")
        index = int(self.np_random.integers(len(self.fixtures))) if requested is None else int(requested)
        self.fixture = self.fixtures[index % len(self.fixtures)]
        self.current_kappa = np.asarray(WARM_START_KAPPA, dtype=float)
        self.previous_action[:] = 0.0
        self.previous_drive_action = 0.0
        self.current_recovery_drive_scale = RECOVERY_CARRIAGE_DRIVE_SCALE
        self.step_count = 0
        self.peak_force = self.contact_impulse = self.peak_torque = self.peak_jerk = 0.0
        self.hard_limit_seen = self.rod_hand_observed = False
        self.previous_position_error = 0.0
        self.cumulative_log_kappa_deviation = 0.0
        self.post_release_step_count = 0
        self.cumulative_residual_gate = 0.0
        self.cumulative_log_drive_deviation = 0.0
        self._build_scene()
        assert self.data is not None
        self.previous_torque = self.data.qfrc_bias[:ARM_DOF].copy()
        self.previous_twist[:] = 0.0
        self.previous_acceleration[:] = 0.0
        return self._observation(0.0), {"fixture_index": index % len(self.fixtures)}

    def _physics_step(self, time_s: float) -> tuple[float, float, float, float]:
        assert self.model is not None and self.data is not None and self.controller is not None and self.reference is not None
        model, data = self.model, self.data
        nominal_position, nominal_rotation, nominal_linear, nominal_angular = self.reference.sample(time_s)
        nominal_twist = np.concatenate([nominal_linear, nominal_angular])
        rod_displacement, _ = (
            rod_motion(time_s, self.fixture.rod_stroke_m, self.fixture.rod_start_time_s)
            if self.rod_enabled else (0.0, 0.0)
        )
        data.mocap_pos[self._obstacle_mocap] = np.array([3.0, 3.0, 3.0])
        data.mocap_quat[self._obstacle_mocap] = np.array([1.0, 0.0, 0.0, 0.0])
        carriage_position = data.qpos[self._explicit_qpos].copy()
        carriage_velocity = data.qvel[self._explicit_dof].copy()
        data.mocap_pos[self._carriage_mocap] = carriage_position
        data.mocap_quat[self._carriage_mocap] = np.array([1.0, 0.0, 0.0, 0.0])
        ee_position = data.xpos[self._hand_id].copy()
        ee_rotation = data.xmat[self._hand_id].reshape(3, 3).copy()
        ee_twist = body_twist(model, data, self._hand_id)
        self.controller.set_kappas(self.current_kappa)
        wrench, _ = self.controller.wrench(ee_position, ee_rotation, ee_twist)
        spring_k = self.current_kappa[:3] * self.config.k_translation_base
        spring_d = 2.0 * self.config.zeta * np.sqrt(CARRIAGE_MASS_KG * spring_k)
        spring_force = _saturated_translation_spring(spring_k, self.config.max_force, carriage_position - ee_position)
        spring_force += spring_d * (carriage_velocity - ee_twist[:3])
        # The return-drive boost is based solely on the measured tracking
        # departure, not rod contact, rod force, obstacle pose, or a timed
        # collision phase.  The scalar residual selects the boosted target;
        # it is not a seventh virtual spring.
        drive_gate = self._deployable_residual_gate(time_s) if self.enable_drive_residual else 0.0
        active_drive_scale = CONTACT_CARRIAGE_DRIVE_SCALE + drive_gate * (self.current_recovery_drive_scale - CONTACT_CARRIAGE_DRIVE_SCALE)
        drive_k = 75.0 * active_drive_scale
        drive_d = 2.0 * self.config.carriage_drive_zeta * np.sqrt(CARRIAGE_MASS_KG * drive_k)
        drive_force = drive_k * (nominal_position - carriage_position) + drive_d * (nominal_twist[:3] - carriage_velocity)
        spring_force = _saturate_vector_norm(spring_force, 1.5 * self.config.max_force)
        drive_force = _saturate_vector_norm(drive_force, 1.5 * self.config.max_force)
        # Applied external forces are reconstructed every 4 ms; this preserves
        # equal-and-opposite spring coupling rather than accumulating a force.
        data.qfrc_applied[:] = 0.0
        _apply_body_force(model, data, self.ids["explicit_carriage"], drive_force - spring_force)
        _apply_body_force(model, data, self._hand_id, spring_force)
        wrench[:3] = 0.0
        wrench_torque = body_jacobian(model, data, self._hand_id).T @ wrench
        bias = data.qfrc_bias[:ARM_DOF].copy()
        desired = bias + torque_feasible_scale(bias, wrench_torque) * wrench_torque
        applied = np.clip(rate_limit_torque(self.previous_torque, desired, CONTROL_DT, self.config), -TORQUE_LIMITS, TORQUE_LIMITS)
        data.ctrl[:ARM_DOF] = applied
        data.ctrl[ARM_DOF] = self.reference.gripper_target(time_s - (self.fixture.grasp_time_s - 2.10))
        data.ctrl[self._rod_ctrl] = rod_displacement
        self.controller.advance(CONTROL_DT, nominal_position, nominal_rotation, nominal_twist, wrench)
        mujoco.mj_step(model, data)
        rod_contact, rod_force, _ = rod_contact_diagnostics(model, data, self._rod_geom_id, self._hand_geom_id)
        self.rod_hand_observed = self.rod_hand_observed or rod_contact
        self.peak_force = max(self.peak_force, rod_force)
        self.contact_impulse += rod_force * CONTROL_DT
        acceleration = (ee_twist - self.previous_twist) / CONTROL_DT
        jerk = (acceleration - self.previous_acceleration) / CONTROL_DT
        jerk_norm = float(np.linalg.norm(jerk[:3]))
        self.peak_jerk = max(self.peak_jerk, jerk_norm)
        self.peak_torque = max(self.peak_torque, float(np.max(np.abs(applied))))
        torque_ratio = float(np.max(np.abs(applied) / TORQUE_LIMITS))
        self.hard_limit_seen = self.hard_limit_seen or bool(np.any(np.isclose(np.abs(applied), TORQUE_LIMITS, atol=1e-5)))
        position_error = float(np.linalg.norm(nominal_position - ee_position))
        orientation_error = float(np.linalg.norm(so3_log(nominal_rotation @ ee_rotation.T)))
        twist_error = float(np.linalg.norm(nominal_twist - ee_twist))
        self.previous_twist = ee_twist
        self.previous_acceleration = acceleration
        self.previous_torque = applied
        return position_error, orientation_error, twist_error, torque_ratio

    def _terminal_info(self) -> dict[str, Any]:
        assert self.data is not None
        target_position = self.data.xpos[self._target_body_id].copy()
        hand_position = self.data.xpos[self._hand_id].copy()
        lifted = bool(target_position[2] > TABLE_TOP_Z + 0.12)
        held = bool(target_position[2] > TABLE_TOP_Z + 0.08 and np.linalg.norm(target_position - hand_position) < 0.16)
        effective = bool(
            self.rod_enabled
            and self.rod_hand_observed
            and self.peak_force >= EFFECTIVE_COLLISION_GATE["minimum_peak_contact_force_n"]
            and self.contact_impulse >= EFFECTIVE_COLLISION_GATE["minimum_contact_impulse_ns"]
        )
        success = bool(np.isfinite(self.data.qpos).all() and np.isfinite(self.data.qvel).all() and lifted and held and not self.hard_limit_seen)
        return {
            "task_success": success,
            "effective_collision": effective,
            "rod_hand_contact": self.rod_hand_observed,
            "peak_contact_force_n": self.peak_force,
            "contact_impulse_ns": self.contact_impulse,
            "peak_torque_nm": self.peak_torque,
            "peak_jerk_mps3": self.peak_jerk,
            "hard_torque_limit": self.hard_limit_seen,
            "mean_log_kappa_deviation": self.cumulative_log_kappa_deviation / max(1, self.step_count),
            "mean_log_drive_deviation": self.cumulative_log_drive_deviation / max(1, self.step_count),
            "mean_residual_gate": self.cumulative_residual_gate / max(1, self.step_count),
            "fixture": self.fixture.__dict__.copy(),
        }

    def diagnostics(self) -> dict[str, Any]:
        """Current state for frozen-policy offline evaluation only.

        This method is intentionally outside the policy observation path.  It
        permits a benchmark harness to form matched rod/no-rod trajectories
        and safety metrics after training without giving those diagnostics to
        the deployed actor.
        """

        assert self.data is not None and self.reference is not None
        time_s = min(self.step_count * RL_DT, SIM_TIME_S)
        nominal_position, nominal_rotation, nominal_linear, nominal_angular = self.reference.sample(time_s)
        ee_position = self.data.xpos[self._hand_id].copy()
        ee_rotation = self.data.xmat[self._hand_id].reshape(3, 3).copy()
        ee_twist = body_twist(self.model, self.data, self._hand_id)
        return {
            "time_s": time_s,
            "ee_position": ee_position,
            "ee_rotation": ee_rotation,
            "ee_twist": ee_twist,
            "nominal_position": nominal_position,
            "nominal_rotation": nominal_rotation,
            "nominal_twist": np.concatenate([nominal_linear, nominal_angular]),
            "kappa": self.current_kappa.copy(),
            "applied_torque": self.previous_torque.copy(),
            "recovery_drive_scale": self.current_recovery_drive_scale,
        }

    def _deployable_residual_gate(self, time_s: float) -> float:
        """Smoothly enable stiffness residuals only when observable error grows.

        This is a deployment-time proprioceptive shield, not a collision
        detector: it uses only nominal-vs-measured end-effector position,
        exactly as the 51-D actor observation does.  The gate prevents the
        learned residual from drifting the nominal task before an impact while
        preserving state-feedback adaptation during a visible departure.
        """

        assert self.data is not None and self.reference is not None
        nominal_position, _, _, _ = self.reference.sample(time_s)
        position_error = float(np.linalg.norm(nominal_position - self.data.xpos[self._hand_id]))
        phase = np.clip((position_error - 0.003) / 0.009, 0.0, 1.0)
        return float(phase * phase * (3.0 - 2.0 * phase))

    def step(self, action: np.ndarray) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        action = np.asarray(action, dtype=float)
        expected_action_shape = (7,) if self.enable_drive_residual else (6,)
        if action.shape != expected_action_shape or not np.all(np.isfinite(action)):
            raise ValueError(f"action must be a finite {expected_action_shape[0]}-vector")
        action = np.clip(action, -1.0, 1.0)
        residual_gate = self._deployable_residual_gate(self.step_count * RL_DT)
        stiffness_action = action[:6]
        applied_action = residual_gate * stiffness_action
        self.current_kappa = action_to_kappa(applied_action, self.current_kappa, self.action_config)
        drive_action = 0.0 if not self.enable_drive_residual else float(action[6])
        applied_drive_action = residual_gate * drive_action
        if self.enable_drive_residual:
            self.current_recovery_drive_scale = action_to_recovery_drive(
                applied_drive_action, self.current_recovery_drive_scale, self.drive_action_config,
            )
        self.cumulative_residual_gate += residual_gate
        accumulated_reward = 0.0
        release_time_s = self.fixture.rod_start_time_s + ROD_PROFILE_DURATION_S
        action_start_error = self.previous_position_error
        final_position_error = 0.0
        for _ in range(PHYSICS_STEPS_PER_ACTION):
            time_s = self.step_count * RL_DT + _ * CONTROL_DT
            position_error, orientation_error, twist_error, torque_ratio = self._physics_step(time_s)
            final_position_error = position_error
            # The actor receives no contact/phase variable.  This internal
            # reward schedule uses the predeclared physical rod release only
            # to distinguish "yield safely" from "rejoin quickly"; it cannot
            # be used as a policy observation or deployment-time clock.
            is_recovery = self.rod_enabled and release_time_s < time_s < self.fixture.grasp_time_s
            is_loading = self.rod_enabled and self.fixture.rod_start_time_s <= time_s <= release_time_s
            position_weight = 0.018 if is_loading else 0.035
            accumulated_reward += (
                -position_weight * min(position_error / 0.06, 3.0)
                -0.014 * min(orientation_error / 0.20, 3.0)
                -0.004 * min(twist_error / 2.2, 3.0)
                -0.004 * torque_ratio**2
            ) / PHYSICS_STEPS_PER_ACTION
            if is_recovery:
                # Make the scientific objective explicit: after the external
                # rod releases, shrink the departure tube without a force or
                # phase observation entering the actor.
                accumulated_reward -= 0.075 * min((position_error / 0.012) ** 2, 4.0) / PHYSICS_STEPS_PER_ACTION
                self.post_release_step_count += 1
        action_delta = float(np.mean((applied_action - self.previous_action) ** 2) + (applied_drive_action - self.previous_drive_action) ** 2)
        accumulated_reward -= 0.003 * action_delta
        if self.rod_enabled and self.step_count * RL_DT > release_time_s:
            recovery_progress = np.clip((action_start_error - final_position_error) / 0.004, -1.0, 1.0)
            accumulated_reward += 0.040 * float(recovery_progress)
        self.previous_position_error = final_position_error
        self.cumulative_log_kappa_deviation += float(np.mean(np.abs(np.log(self.current_kappa / np.asarray(WARM_START_KAPPA)))))
        self.cumulative_log_drive_deviation += abs(float(np.log(self.current_recovery_drive_scale / RECOVERY_CARRIAGE_DRIVE_SCALE)))
        self.previous_action = applied_action.copy()
        self.previous_drive_action = applied_drive_action
        self.step_count += 1
        terminated = self.step_count >= int(round(SIM_TIME_S / RL_DT))
        info: dict[str, Any] = {}
        if terminated:
            info = self._terminal_info()
            # Success has value only under a substantial, predeclared physical
            # collision.  The policy has no means to choose its force/impulse.
            if info["task_success"] and info["effective_collision"]:
                accumulated_reward += 12.0
            else:
                accumulated_reward -= 12.0
        observation = self._observation(min(self.step_count * RL_DT, SIM_TIME_S))
        truncated = False
        return observation, float(accumulated_reward), terminated, truncated, info

    def close(self) -> None:
        self.model = None
        self.data = None
