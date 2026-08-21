"""Independent WBC-aware velocity-residual environment for MLP/ESN control.

The proposed actor is not connected to the VMC virtual springs.  A fixed Panda
WBC produces the nominal task command.  The learned actor may only slow that
command and add a bounded six-dimensional Cartesian yield velocity.  A shared
adapter enforces action, joint-velocity, joint-acceleration, torque, and torque
slew limits before applying commands to the physical MuJoCo Panda.
"""

from __future__ import annotations

import os as _os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import gymnasium as gym
import mujoco
import numpy as np

from esn_compliance import ESNObservation, encode_student_observation
from direct_esn_compliance import DirectESNObservation, encode_direct_esn_observation
from fan_ye_esn_rl_adapter import (
    CURRENT_WBC_FEATURE_DIMENSION,
    FanYeESNRLObservationAdapter,
    encode_applied_residual_context,
    encode_kinematic_pose_forecast,
    encode_wbc_current_feature,
    WBC_POSE_ERROR_SCALE,
    WBC_TWIST_ERROR_SCALE,
)
from fixed_panda_wbc import FixedBasePandaWBC, WBCCommand
from run_benchmark import ARM_DOF, CONTROL_DT, TORQUE_LIMITS, body_jacobian, body_twist, so3_log
from run_grasp_impact_benchmark import TABLE_TOP_Z, TARGET_START_Z, PickLiftCarryReference
from run_rod_perturbation_benchmark import make_rod_model, rod_contact_diagnostics, rod_motion
from stiffness_training_core import EFFECTIVE_COLLISION_GATE
from wbc_velocity_residual_core import (
    FilteredVelocityResidualAction,
    VelocityResidualActionFilter,
    VelocityResidualSafetyConfig,
    safe_joint_velocity_command,
    safe_velocity_tracking_torque,
    deployable_authority_gate,
    predictive_authority_multiplier,
    predictive_wbc_feedback_scale,
    phase_predictive_wbc_feedback_scale,
    project_yield_action_to_error_phase,
    apply_rejoin_velocity_envelope,
    ResidualEnergyTank,
    stable_phase_memory_floor,
)


RL_DT = 0.040
PHYSICS_STEPS_PER_ACTION = int(round(RL_DT / CONTROL_DT))
SIM_TIME_S = 6.20
ROD_PROFILE_DURATION_S = 0.64
CONTACT_TIME_CONSTANT_S = 0.015


@dataclass(frozen=True)
class VelocityResidualFixture:
    """Physical perturbation configuration hidden from the deployed actor."""

    rod_stroke_m: float
    rod_height_m: float
    rod_start_time_s: float
    grasp_time_s: float = 2.40
    rod_approach_side: str = "negative_y"
    rod_center_x_m: float = 0.55
    rod_center_y_m: float = 0.0
    impactor_type: str = "rod"
    # Multi-cycle impacts: the rod repeats its press--hold--retract profile
    # this many times, spaced by cycle_period_s (see rod_motion).
    rod_cycles: int = 1
    cycle_period_s: float = 0.80


def default_velocity_residual_fixtures() -> tuple[VelocityResidualFixture, ...]:
    return (
        VelocityResidualFixture(0.160, 0.539, 1.055),
        VelocityResidualFixture(0.165, 0.540, 1.070),
        VelocityResidualFixture(0.170, 0.541, 1.085),
        VelocityResidualFixture(0.175, 0.542, 1.100),
    )


@dataclass(frozen=True)
class VelocityResidualRewardConfig:
    """Training-only objective; none of these labels enter the observation."""

    position_error_weight: float = 0.040
    orientation_error_weight: float = 0.014
    twist_error_weight: float = 0.005
    torque_weight: float = 0.004
    slowdown_weight: float = 0.006
    yield_magnitude_weight: float = 0.004
    action_change_weight: float = 0.003
    raw_policy_action_weight: float = 0.010
    contact_impulse_weight: float = 0.050
    post_release_error_weight: float = 0.100
    recovery_progress_weight: float = 0.050
    recovery_jerk_weight: float = 0.002
    jerk_reference_mps3: float = 1200.0
    terminal_bonus: float = 12.0

    def __post_init__(self) -> None:
        values = np.asarray(list(asdict(self).values()), dtype=float)
        if not np.all(np.isfinite(values)) or np.any(values < 0.0):
            raise ValueError("velocity-residual reward weights must be finite and non-negative")
        if self.jerk_reference_mps3 <= 0.0 or self.terminal_bonus <= 0.0:
            raise ValueError("jerk reference and terminal bonus must be positive")


class PandaWBCVelocityResidualEnv(gym.Env[np.ndarray, np.ndarray]):
    """Panda pick task controlled by WBC plus an independent learned residual."""

    metadata = {"render_modes": []}
    observation_modes = ("direct_esn", "current_mlp", "kinematic_forecast_mlp", "fan_ye_esn", "fan_ye_multiscale_esn", "fan_ye_phase_esn", "fan_ye_stable_phase_esn", "fan_ye_closed_loop_esn", "fan_ye_forecast_esn", "fan_ye_forecast_authority_esn", "fan_ye_forecast_wbc_esn", "fan_ye_phase_predictive_wbc_esn")

    def __init__(
        self,
        menagerie: str | Path,
        fan_ye_model_npz: str | Path | None,
        fan_ye_train_summary_json: str | Path | None,
        observation_mode: str,
        fixtures: tuple[VelocityResidualFixture, ...] | None = None,
        rod_enabled: bool = True,
        safety_config: VelocityResidualSafetyConfig | None = None,
        torque_limit_scale: float = 1.0,
        robot: str = "panda",
        wbc_backend: str = "fixed",
        wbc_urdf_path: str | Path | None = None,
        rod_hold_extension_s: float = 0.0,
        table_board_underside_z: float | None = None,
        lift_board_tilt_deg: float | None = None,
        joint_velocity_noise_std: float = 0.0,
        execution_mode: str = "twist",
        residual_torque_scale: float = 0.25,
        reward_config: VelocityResidualRewardConfig | None = None,
        residual_window_end_at_grasp: bool = False,
        residual_energy_tank: bool = False,
        forecast_model_npz: str | Path | None = None,
        predictive_wbc_min_feedback_scale: float = 0.60,
        predictive_wbc_growth_deadband: float = 0.05,
        seed: int | None = None,
    ) -> None:
        super().__init__()
        if observation_mode not in self.observation_modes:
            raise ValueError(f"observation_mode must be one of {self.observation_modes}")
        self.menagerie = Path(menagerie)
        self.fixtures = fixtures or default_velocity_residual_fixtures()
        if not self.fixtures:
            raise ValueError("at least one velocity-residual fixture is required")
        self.observation_mode = observation_mode
        self.rod_enabled = bool(rod_enabled)
        self.safety_config = safety_config or VelocityResidualSafetyConfig()
        self.robot = robot
        if wbc_backend not in ("fixed", "pink", "paper_mpc"):
            raise ValueError("wbc_backend must be 'fixed', 'pink', or 'paper_mpc'")
        if wbc_backend == "pink" and robot != "fr3":
            raise ValueError("the vendored Pink-IK WBC backend is wired for robot='fr3'")
        self.wbc_backend = wbc_backend
        self.wbc_urdf_path = wbc_urdf_path
        if table_board_underside_z is not None and robot != "fr3":
            raise ValueError("the extraction-board scene is wired for robot='fr3'")
        self.table_board_underside_z = table_board_underside_z
        if lift_board_tilt_deg is not None and robot != "fr3":
            raise ValueError("the inclined lift-board scene is wired for robot='fr3'")
        self.lift_board_tilt_deg = lift_board_tilt_deg
        self._board_reference_factory = None
        if execution_mode not in ("twist", "torque_residual", "torque_takeover", "torque_takeover_gc"):
            raise ValueError(
                "execution_mode must be 'twist', 'torque_residual', 'torque_takeover', or 'torque_takeover_gc'")
        if not 0.0 < residual_torque_scale <= 1.0:
            raise ValueError("residual torque scale must lie in (0, 1]")
        self.execution_mode = execution_mode
        self._pending_residual_scale = float(residual_torque_scale)
        if rod_hold_extension_s < 0.0 or joint_velocity_noise_std < 0.0:
            raise ValueError("rod hold extension and velocity noise must be non-negative")
        self.rod_hold_extension_s = float(rod_hold_extension_s)
        self.rod_profile_duration_s = ROD_PROFILE_DURATION_S + self.rod_hold_extension_s
        self.joint_velocity_noise_std = float(joint_velocity_noise_std)
        if not np.isfinite(torque_limit_scale) or torque_limit_scale <= 0.0:
            raise ValueError("torque_limit_scale must be finite and positive")
        # Diagnostic relief of the shared torque envelope.  1.0 keeps the
        # frozen benchmark protocol; larger values expose each controller's
        # raw torque demand that the shared limiter would otherwise clip.
        self.torque_limits = TORQUE_LIMITS * float(torque_limit_scale)
        # Per-joint budget for learned/hand residual torques (fraction of the
        # hardware limits), applied before the shared final clamp.
        self.residual_torque_limits = self.torque_limits * self._pending_residual_scale
        self.physics_torque_history: list[np.ndarray] = []
        self._residual_torque_command = np.zeros(ARM_DOF)
        self._takeover_torque_command = np.zeros(ARM_DOF)
        # Per-step torque decomposition of the LAST physics substep, exposed in
        # diagnostics for architecture-comparison experiments.
        self._last_torque_components: dict[str, np.ndarray] | None = None
        # Shadow (non-applied) expert channel for DAgger on full-authority
        # students: externally set each step; consumed in takeover modes.
        self.expert_residual_torque: np.ndarray | None = None
        # Optional substep-rate (250 Hz) residual policy hook for high-rate
        # compliance experiments: called inside every physics substep with the
        # live MuJoCo data before torque application.
        self.substep_policy_hook = None
        self._shadow_torque_components: dict[str, np.ndarray] | None = None
        self._shadow_previous_torque = np.zeros(ARM_DOF)
        self.reward_config = reward_config or VelocityResidualRewardConfig()
        self.residual_window_end_at_grasp = bool(residual_window_end_at_grasp)
        self.residual_energy_tank_enabled = bool(residual_energy_tank)
        self.energy_tank = ResidualEnergyTank(enabled=self.residual_energy_tank_enabled)
        self.predictive_wbc_min_feedback_scale = float(predictive_wbc_min_feedback_scale)
        self.predictive_wbc_growth_deadband = float(predictive_wbc_growth_deadband)
        if not 0.0 < self.predictive_wbc_min_feedback_scale <= 1.0 or not 0.0 <= self.predictive_wbc_growth_deadband < 1.0:
            raise ValueError("predictive WBC feedback bounds are invalid")
        if observation_mode == "direct_esn" and (fan_ye_model_npz is None or fan_ye_train_summary_json is None):
            self.feature_adapter = None
        else:
            if fan_ye_model_npz is None or fan_ye_train_summary_json is None:
                raise ValueError("fan-ye model and summary are required for non-direct observation modes")
            self.feature_adapter = FanYeESNRLObservationAdapter(
                Path(fan_ye_model_npz), Path(fan_ye_train_summary_json),
                None if forecast_model_npz is None else Path(forecast_model_npz),
            )
        observation_dimension = {
            "direct_esn": 32,
            "current_mlp": CURRENT_WBC_FEATURE_DIMENSION,
            "kinematic_forecast_mlp": CURRENT_WBC_FEATURE_DIMENSION + 6,
            "fan_ye_esn": self.feature_adapter.feature_dimension if self.feature_adapter is not None else 20,
            "fan_ye_multiscale_esn": self.feature_adapter.multiscale_feature_dimension if self.feature_adapter is not None else 20,
            "fan_ye_phase_esn": self.feature_adapter.multiscale_feature_dimension if self.feature_adapter is not None else 20,
            "fan_ye_stable_phase_esn": self.feature_adapter.multiscale_feature_dimension if self.feature_adapter is not None else 20,
            "fan_ye_closed_loop_esn": self.feature_adapter.closed_loop_feature_dimension if self.feature_adapter is not None else 20,
            "fan_ye_forecast_esn": CURRENT_WBC_FEATURE_DIMENSION + 6,
            "fan_ye_forecast_authority_esn": CURRENT_WBC_FEATURE_DIMENSION,
            "fan_ye_forecast_wbc_esn": CURRENT_WBC_FEATURE_DIMENSION,
            "fan_ye_phase_predictive_wbc_esn": self.feature_adapter.multiscale_feature_dimension if self.feature_adapter is not None else 20,
        }[observation_mode]
        self.action_space = gym.spaces.Box(-1.0, 1.0, shape=(7,), dtype=np.float32)
        self.observation_space = gym.spaces.Box(-10.0, 10.0, shape=(observation_dimension,), dtype=np.float32)
        self.action_filter = VelocityResidualActionFilter(self.safety_config)
        self.model: mujoco.MjModel | None = None
        self.data: mujoco.MjData | None = None
        self.reference: PickLiftCarryReference | None = None
        self.fixed_wbc: FixedBasePandaWBC | None = None
        self.fixture = self.fixtures[0]
        self._hand_id = -1
        self._hand_geom_id = -1
        self._rod_geom_id = -1
        self._target_body_id = -1
        self._target_qpos = -1
        self._target_dof = -1
        self._rod_ctrl = -1
        self._obstacle_mocap = -1
        self.step_count = 0
        self.previous_policy_action = np.zeros(7, dtype=float)
        self.previous_joint_velocity_command = np.zeros(ARM_DOF, dtype=float)
        self.previous_torque = np.zeros(ARM_DOF, dtype=float)
        self.previous_twist = np.zeros(6, dtype=float)
        self.previous_acceleration = np.zeros(6, dtype=float)
        self.previous_position_error = 0.0
        self.applied_action = FilteredVelocityResidualAction(1.0, np.zeros(6), np.zeros(7), False, False)
        self.raw_joint_velocity_command = np.zeros(ARM_DOF, dtype=float)
        self.peak_force = 0.0
        self.contact_impulse = 0.0
        # Privileged training diagnostics. These are never exposed through
        # the direct-ESN observation, but allow an offline DAgger teacher to
        # label the exact states the student visited.
        self.physics_torque_history = []
        self.last_action_contact_force = 0.0
        self.last_action_contact_penetration = 0.0
        self.last_action_contact_wrench_world = np.zeros(6)
        self.last_action_contact_seen = False
        self.dagger_contact_duration_s = 0.0
        self.peak_torque = 0.0
        self.peak_jerk = 0.0
        self.peak_recovery_jerk = 0.0
        self.minimum_torque_feasible_scale = 1.0
        self.hard_limit_seen = False
        self.rod_hand_observed = False
        self.slew_limited_actions = 0
        self.saturated_policy_actions = 0
        self.cumulative_wbc_slowdown = 0.0
        self.cumulative_yield_norm = 0.0
        self.current_authority_gate = 0.0
        self.cumulative_authority_gate = 0.0
        self.current_predictive_authority_multiplier = 1.0
        self.cumulative_predictive_authority_multiplier = 0.0
        self.predicted_delta_pose_error = np.zeros(6, dtype=float)
        self.current_predictive_wbc_feedback_scale = 1.0
        self.cumulative_predictive_wbc_feedback_scale = 0.0
        self.phase_memory_score = 0.0
        self.phase_memory_gate = 0.0
        self.cumulative_phase_memory_score = 0.0
        self.cumulative_phase_memory_gate = 0.0
        self.stable_phase_memory_floor = 0.0
        self.cumulative_stable_phase_memory_floor = 0.0
        self.current_energy_tank_multiplier = 1.0
        self.current_energy_tank_value = self.energy_tank.energy
        self.cumulative_energy_tank_multiplier = 0.0
        self.minimum_energy_tank_value = self.energy_tank.energy
        self.reset(seed=seed)

    def _build_scene(self) -> None:
        if self.robot == "fr3":
            from fr3_scene import make_fr3_hand_model

            scene_kwargs = dict(
                rod_height_m=self.fixture.rod_height_m,
                rod_approach_side=self.fixture.rod_approach_side,
                rod_center_x_m=self.fixture.rod_center_x_m,
                rod_center_y_m=self.fixture.rod_center_y_m,
                impactor_type=self.fixture.impactor_type,
                board_underside_z=self.table_board_underside_z,
            )
            if self.lift_board_tilt_deg is not None:
                # Two-pass placement: a throwaway board-free build provides
                # the lift-path FK, then the real scene is rebuilt with the
                # inclined static board centered on the mid-lift waypoint so
                # the rising arm strikes its tilted face.  The board scenario
                # uses a lateral lift arc (joint 2 offset) so the descent
                # path and the board are geometrically separated — the arm
                # strikes the board only while moving bottom-up.
                import os as _os
                lateral_arc = float(_os.environ.get("LIFT_BOARD_ARC", "0.40"))

                def board_reference(model_, data_, hand_id_):
                    ref = PickLiftCarryReference(model_, data_, hand_id_)
                    knots = ref.q_knots.copy()
                    # Lateral arc on joint 1 (base yaw, z-axis): at this
                    # configuration joint 2's axis is horizontal and moves the
                    # EE in x-z, NOT laterally -- the first attempt used joint
                    # 2 and the hand never left y=0 (the board was never
                    # touched).  Joint 1 swings the EE along +y as required.
                    knots[3][0] += lateral_arc   # lifted: lateral arc on joint 1
                    knots[4][0] += lateral_arc   # carry: keep the offset
                    ref.q_knots = knots
                    return ref

                probe_model, probe_data = make_fr3_hand_model(
                    self.menagerie, CONTACT_TIME_CONSTANT_S, **scene_kwargs)
                probe_hand = mujoco.mj_name2id(
                    probe_model, mujoco.mjtObj.mjOBJ_BODY, "hand")
                probe_ref = board_reference(probe_model, probe_data, probe_hand)
                p_start = probe_ref.sample(2.70)[0]
                p_end = probe_ref.sample(4.10)[0]
                center = 0.75 * p_start + 0.25 * p_end
                center[0] += float(_os.environ.get("LIFT_BOARD_X_OFF", "0.0"))  # keep the slab clear of the home-pose forearm arch
                center[1] += float(_os.environ.get("LIFT_BOARD_Y_OFF", "0.09"))  # clear of the y=0 descent incl. open-finger edges (grasp stays clean)
                center[2] += float(_os.environ.get("LIFT_BOARD_Z_OFF", "0.0"))  # raise the low -y edge clear of the carried block's swing
                scene_kwargs["lift_board_center_m"] = tuple(float(v) for v in center)
                scene_kwargs["lift_board_tilt_deg"] = float(self.lift_board_tilt_deg)
                self._board_reference_factory = board_reference
            else:
                self._board_reference_factory = None
            self.model, self.data = make_fr3_hand_model(
                self.menagerie, CONTACT_TIME_CONSTANT_S, **scene_kwargs)
        elif self.robot == "panda":
            self.model, self.data = make_rod_model(
                self.menagerie,
                CONTACT_TIME_CONSTANT_S,
                self.fixture.rod_height_m,
                explicit_translational_carriage=False,
                explicit_rotational_carriage=False,
                rod_approach_side=self.fixture.rod_approach_side,
                rod_center_x_m=self.fixture.rod_center_x_m,
                rod_center_y_m=self.fixture.rod_center_y_m,
                impactor_type=self.fixture.impactor_type,
            )
        else:
            raise ValueError(f"unknown robot {robot!r}")
        model, data = self.model, self.data
        named = {
            "hand": (mujoco.mjtObj.mjOBJ_BODY, "hand"),
            "hand_geom": (mujoco.mjtObj.mjOBJ_GEOM, "hand_collision"),
            "target_body": (mujoco.mjtObj.mjOBJ_BODY, "target_object"),
            "target_freejoint": (mujoco.mjtObj.mjOBJ_JOINT, "target_freejoint"),
            "rod_geom": (mujoco.mjtObj.mjOBJ_GEOM, "rod_geom"),
            "moving_obstacle": (mujoco.mjtObj.mjOBJ_BODY, "moving_obstacle"),
        }
        ids = {key: mujoco.mj_name2id(model, kind, name) for key, (kind, name) in named.items()}
        if min(ids.values()) < 0:
            raise RuntimeError("direct WBC residual scene IDs were not resolved")
        self._hand_id = ids["hand"]
        self._hand_geom_id = ids["hand_geom"]
        self._target_body_id = ids["target_body"]
        self._rod_geom_id = ids["rod_geom"]
        self._target_qpos = int(model.jnt_qposadr[ids["target_freejoint"]])
        self._target_dof = int(model.jnt_dofadr[ids["target_freejoint"]])
        self._obstacle_mocap = int(model.body_mocapid[ids["moving_obstacle"]])
        self._rod_ctrl = ARM_DOF + 1
        if model.nu != ARM_DOF + 2 or self._obstacle_mocap < 0:
            raise RuntimeError("expected Panda torques, gripper, rod driver, and diagnostic mocap")
        data.qpos[self._target_qpos:self._target_qpos + 7] = [
            0.54, 0.0, TARGET_START_Z, 1.0, 0.0, 0.0, 0.0,
        ]
        data.qvel[self._target_dof:self._target_dof + 6] = 0.0
        mujoco.mj_forward(model, data)
        if self._board_reference_factory is not None:
            self.reference = self._board_reference_factory(model, data, self._hand_id)
        else:
            self.reference = PickLiftCarryReference(model, data, self._hand_id)
        if self.wbc_backend == "pink":
            from pink_wbc_adapter import PinkWBCAdapter

            if self.wbc_urdf_path is None:
                raise ValueError("wbc_backend='pink' requires wbc_urdf_path (FR3 URDF)")
            self.fixed_wbc = PinkWBCAdapter(
                model, self._hand_id, data.qpos[:ARM_DOF], self.wbc_urdf_path)
        elif self.wbc_backend == "paper_mpc":
            from paper_mpc_wbc import PaperMPCWBC

            self.fixed_wbc = PaperMPCWBC(
                model, self._hand_id, self.reference, data.qpos[:ARM_DOF])
        else:
            self.fixed_wbc = FixedBasePandaWBC(model, self._hand_id, data.qpos[:ARM_DOF])

    def _extended_hold_profile_time(self, time_s: float) -> float:
        """Freeze the rod inside the hold window to extend it physically.

        The stock profile presses, holds briefly, and retracts with fixed
        constants.  Mapping time through this function stretches the hold
        segment by ``rod_hold_extension_s`` without touching shared code.
        """

        if self.rod_hold_extension_s <= 0.0:
            return time_s
        start = self.fixture.rod_start_time_s
        elapsed = time_s - start
        # Stock profile segments (s): press [0, 0.24], hold [0.24, 0.40],
        # retract [0.40, 0.64]; mirroring run_rod_perturbation_benchmark.
        press_end, hold_end = 0.24, 0.40
        extension = self.rod_hold_extension_s
        crawl_rate = press_end / hold_end
        if elapsed < press_end:
            return time_s
        if elapsed < hold_end + extension:
            # Slow crawl through the hold window: the rod keeps advancing at
            # a fraction of the press speed, following the yielding hand and
            # maintaining the squeeze instead of stopping at full stroke.
            return start + press_end + crawl_rate * (elapsed - press_end)
        # After the extended hold, land on the retract phase consistently.
        return start + press_end + crawl_rate * (hold_end + extension - press_end) + (elapsed - hold_end - extension)

    def _wbc_command(self, time_s: float) -> WBCCommand:
        assert self.data is not None and self.reference is not None and self.fixed_wbc is not None
        position, rotation, linear, angular = self.reference.sample(time_s)
        if self.observation_mode == "fan_ye_forecast_wbc_esn":
            pose_error = np.concatenate((
                position - self.data.xpos[self._hand_id],
                so3_log(rotation @ self.data.xmat[self._hand_id].reshape(3, 3).T),
            ))
            self.current_predictive_wbc_feedback_scale = predictive_wbc_feedback_scale(
                pose_error / WBC_POSE_ERROR_SCALE, self.predicted_delta_pose_error,
                minimum_feedback_scale=self.predictive_wbc_min_feedback_scale,
                growth_deadband=self.predictive_wbc_growth_deadband,
            )
        elif self.observation_mode == "fan_ye_phase_predictive_wbc_esn":
            pose_error = np.concatenate((
                position - self.data.xpos[self._hand_id],
                so3_log(rotation @ self.data.xmat[self._hand_id].reshape(3, 3).T),
            ))
            self.current_predictive_wbc_feedback_scale = phase_predictive_wbc_feedback_scale(
                pose_error / WBC_POSE_ERROR_SCALE, self.predicted_delta_pose_error,
                self.phase_memory_score, self.current_predictive_wbc_feedback_scale, CONTROL_DT,
                minimum_feedback_scale=self.predictive_wbc_min_feedback_scale,
                growth_deadband=self.predictive_wbc_growth_deadband,
            )
        else:
            self.current_predictive_wbc_feedback_scale = 1.0
        return self.fixed_wbc.command(
            self.data, position, rotation, np.concatenate((linear, angular)),
            feedback_scale=self.current_predictive_wbc_feedback_scale,
        )

    def _observation(self, time_s: float) -> np.ndarray:
        assert self.data is not None
        command = self._wbc_command(time_s)
        position_error = command.target_position_m - self.data.xpos[self._hand_id]
        rotation_error = so3_log(command.target_rotation @ self.data.xmat[self._hand_id].reshape(3, 3).T)
        pose_error = np.concatenate((position_error, rotation_error))
        twist_error = command.task_twist_world - body_twist(self.model, self.data, self._hand_id)
        student = ESNObservation(
            self.data.qpos[:ARM_DOF].copy(),
            self.data.qvel[:ARM_DOF].copy(),
            command.task_twist_world.copy(),
        )
        if self.observation_mode == "direct_esn":
            return encode_direct_esn_observation(DirectESNObservation(
                student.joint_position, student.joint_velocity, student.wbc_task_twist,
                pose_error, twist_error,
            )).astype(np.float32)
        if self.observation_mode == "current_mlp":
            return encode_wbc_current_feature(student, pose_error, twist_error)
        if self.observation_mode == "kinematic_forecast_mlp":
            return np.concatenate((
                encode_wbc_current_feature(student, pose_error, twist_error),
                encode_kinematic_pose_forecast(pose_error, twist_error),
            )).astype(np.float32)
        if self.observation_mode == "fan_ye_esn":
            return self.feature_adapter.observe(student, pose_error, twist_error)
        if self.observation_mode == "fan_ye_multiscale_esn":
            return self.feature_adapter.observe_multiscale(student, pose_error, twist_error)
        if self.observation_mode in ("fan_ye_phase_esn", "fan_ye_stable_phase_esn", "fan_ye_phase_predictive_wbc_esn"):
            feature = self.feature_adapter.observe_phase_memory(student, pose_error, twist_error)
            self.phase_memory_score = self.feature_adapter.phase_memory_score()
            if self.observation_mode == "fan_ye_phase_predictive_wbc_esn":
                forecast_feature = self.feature_adapter.observe_forecast(student, pose_error, twist_error)
                self.predicted_delta_pose_error = np.asarray(forecast_feature[-6:], dtype=float)
            return feature
        if self.observation_mode == "fan_ye_forecast_esn":
            return self.feature_adapter.observe_forecast(student, pose_error, twist_error)
        if self.observation_mode in ("fan_ye_forecast_authority_esn", "fan_ye_forecast_wbc_esn"):
            forecast_feature = self.feature_adapter.observe_forecast(student, pose_error, twist_error)
            self.predicted_delta_pose_error = np.asarray(forecast_feature[-6:], dtype=float)
            return forecast_feature[:CURRENT_WBC_FEATURE_DIMENSION].astype(np.float32)
        context = encode_applied_residual_context(
            self.applied_action.wbc_scale, self.applied_action.cartesian_yield_twist,
            minimum_wbc_scale=self.safety_config.minimum_wbc_scale,
            maximum_linear_yield_mps=self.safety_config.maximum_linear_yield_mps,
            maximum_angular_yield_radps=self.safety_config.maximum_angular_yield_radps,
        )
        return self.feature_adapter.observe_closed_loop(student, pose_error, twist_error, context)

    def reset(
        self, *, seed: int | None = None, options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        requested = None if options is None else options.get("fixture_index")
        index = int(self.np_random.integers(len(self.fixtures))) if requested is None else int(requested)
        self.fixture = self.fixtures[index % len(self.fixtures)]
        self._build_scene()
        assert self.data is not None
        self.step_count = 0
        self.previous_policy_action[:] = 0.0
        self.previous_joint_velocity_command[:] = 0.0
        self.previous_torque = self.data.qfrc_bias[:ARM_DOF].copy()
        self._shadow_previous_torque = self.data.qfrc_bias[:ARM_DOF].copy()
        self.expert_residual_torque = None
        self._last_torque_components = None
        self._shadow_torque_components = None
        self.previous_twist[:] = 0.0
        self.previous_acceleration[:] = 0.0
        self.previous_position_error = 0.0
        self.raw_joint_velocity_command[:] = 0.0
        self.peak_force = self.contact_impulse = self.peak_torque = self.peak_jerk = self.peak_recovery_jerk = 0.0
        self.physics_torque_history = []
        self.last_action_contact_force = 0.0
        self.last_action_contact_penetration = 0.0
        self.last_action_contact_wrench_world = np.zeros(6)
        self.last_action_contact_seen = False
        self.dagger_contact_duration_s = 0.0
        self.minimum_torque_feasible_scale = 1.0
        self.hard_limit_seen = self.rod_hand_observed = False
        self.slew_limited_actions = self.saturated_policy_actions = 0
        self.cumulative_wbc_slowdown = self.cumulative_yield_norm = 0.0
        self.current_authority_gate = self.cumulative_authority_gate = 0.0
        self.current_predictive_authority_multiplier = 1.0
        self.cumulative_predictive_authority_multiplier = 0.0
        self.predicted_delta_pose_error[:] = 0.0
        self.current_predictive_wbc_feedback_scale = 1.0
        self.cumulative_predictive_wbc_feedback_scale = 0.0
        self.phase_memory_score = 0.0
        self.phase_memory_gate = 0.0
        self.cumulative_phase_memory_score = 0.0
        self.cumulative_phase_memory_gate = 0.0
        self.stable_phase_memory_floor = 0.0
        self.cumulative_stable_phase_memory_floor = 0.0
        self.energy_tank.reset()
        self.current_energy_tank_multiplier = 1.0
        self.current_energy_tank_value = self.energy_tank.energy
        self.cumulative_energy_tank_multiplier = 0.0
        self.minimum_energy_tank_value = self.energy_tank.energy
        self.action_filter.reset()
        self.applied_action = FilteredVelocityResidualAction(1.0, np.zeros(6), np.zeros(7), False, False)
        if self.feature_adapter is not None:
            self.feature_adapter.reset()
        observation = self._observation(0.0)
        return observation, {
            "fixture_index": index % len(self.fixtures),
            "controller_family": "direct_esn" if self.observation_mode == "direct_esn" else "wbc_velocity_residual",
            "uses_vmc": False,
        }

    def _physics_step(self, time_s: float) -> tuple[float, float, float, float, float]:
        assert self.model is not None and self.data is not None and self.reference is not None
        model, data = self.model, self.data
        command = self._wbc_command(time_s)
        plank_launch = _os.environ.get("LIFT_PLANK_MODE", "servo") == "launch"
        if self.rod_enabled and plank_launch:
            # Momentum-limited flying plank: velocity-kick the slide during a
            # short launch window, then zero drive -- damping + frictionloss
            # coast it through the arm's column and stop it.  The fixture's
            # rod_stroke_m is REUSED as the launch speed (m/s) and
            # rod_start_time_s as the launch time.
            window = float(_os.environ.get("LIFT_PLANK_WINDOW", "0.25"))
            elapsed = time_s - self.fixture.rod_start_time_s
            rod_displacement = self.fixture.rod_stroke_m if 0.0 <= elapsed <= window else 0.0
        elif self.rod_enabled:
            profile_time = self._extended_hold_profile_time(time_s)
            rod_displacement, _ = rod_motion(
                profile_time, self.fixture.rod_stroke_m, self.fixture.rod_start_time_s,
                cycles=self.fixture.rod_cycles, cycle_period_s=self.fixture.cycle_period_s,
            )
        else:
            rod_displacement = 0.0
        data.mocap_pos[self._obstacle_mocap] = np.array([3.0, 3.0, 3.0])
        data.mocap_quat[self._obstacle_mocap] = np.array([1.0, 0.0, 0.0, 0.0])
        data.qfrc_applied[:] = 0.0
        # Delayed cue (LIFT_CUE): a brief observable wrist nudge at t~1.0-1.3
        # that PREDICTS the strike at ~3.0.  The WBC erases its instantaneous
        # trace within ~0.5 s -- by strike time only a controller that
        # INTEGRATED the cue (reservoir memory) can still know to pre-yield.
        if _os.environ.get("LIFT_CUE", "0") == "1" and 1.0 <= time_s <= 1.3:
            data.qfrc_applied[4] = 8.0
        jacobian = body_jacobian(model, data, self._hand_id)
        qdot_command, raw_qdot = safe_joint_velocity_command(
            command.joint_velocity_radps,
            jacobian,
            self.applied_action,
            self.previous_joint_velocity_command,
            CONTROL_DT,
            self.safety_config,
        )
        if self.substep_policy_hook is not None and self.execution_mode == "torque_residual":
            self._residual_torque_command = np.asarray(
                self.substep_policy_hook(self.data, command), dtype=float)
        if self.execution_mode == "torque_takeover" or self.execution_mode == "torque_takeover_gc":
            # Full-authority learned controller: the policy action is the
            # TOTAL joint torque in units of the hardware limits ([-1, 1] per
            # joint).  No velocity servo runs.  The *_gc variant keeps a pure
            # gravity-compensation feedthrough so the policy only has to learn
            # the dynamic part; the plain variant must learn gravity as well.
            bias_feedthrough = data.qfrc_bias[:ARM_DOF].copy() \
                if self.execution_mode == "torque_takeover_gc" else np.zeros(ARM_DOF)
            takeover = np.clip(
                np.asarray(self._takeover_torque_command, dtype=float),
                -self.torque_limits, self.torque_limits)
            applied_torque = np.clip(
                bias_feedthrough + takeover, -self.torque_limits, self.torque_limits)
            feasible_scale = 1.0
            self._last_torque_components = {
                "total": applied_torque.copy(),
                "bias": bias_feedthrough.copy(),
                "servo": np.zeros(ARM_DOF),
                "policy": takeover.copy(),
            }
            if self.expert_residual_torque is not None:
                # Shadow expert (never applied): what the nominal architecture
                # (WBC velocity servo + bounded residual) WOULD have commanded
                # from this same state.  Provides exact DAgger labels for the
                # full-authority student's visited states.
                shadow_servo, _ = safe_velocity_tracking_torque(
                    data.qfrc_bias[:ARM_DOF].copy(),
                    data.qvel[:ARM_DOF].copy(),
                    qdot_command,
                    self._shadow_previous_torque,
                    CONTROL_DT,
                    self.safety_config,
                    torque_limits=self.torque_limits,
                )
                shadow_residual = np.clip(
                    np.asarray(self.expert_residual_torque, dtype=float),
                    -self.residual_torque_limits, self.residual_torque_limits)
                shadow_total = np.clip(
                    shadow_servo + shadow_residual, -self.torque_limits, self.torque_limits)
                self._shadow_torque_components = {
                    "total": shadow_total.copy(),
                    "bias": data.qfrc_bias[:ARM_DOF].copy(),
                    "servo": shadow_servo.copy(),
                    "policy": shadow_residual.copy(),
                }
                self._shadow_previous_torque = shadow_total.copy()
        else:
            applied_torque, feasible_scale = safe_velocity_tracking_torque(
                data.qfrc_bias[:ARM_DOF].copy(),
                data.qvel[:ARM_DOF].copy(),
                qdot_command,
                self.previous_torque,
                CONTROL_DT,
                self.safety_config,
                torque_limits=self.torque_limits,
            )
            self._shadow_previous_torque = applied_torque.copy()
            if self.execution_mode == "torque_residual":
                # Impedance-style compliance channel: the policy action is a raw
                # joint-torque residual (clipped to its own budget and slewed by
                # the shared clamp) added on top of the WBC velocity servo, so a
                # collision is softened in the force domain instead of by moving
                # the reference away from the nominal path.
                residual = np.clip(
                    np.asarray(self._residual_torque_command, dtype=float),
                    -self.residual_torque_limits, self.residual_torque_limits)
                applied_torque = np.clip(
                    applied_torque + residual, -self.torque_limits, self.torque_limits)
                self._last_torque_components = {
                    "total": applied_torque.copy(),
                    "bias": data.qfrc_bias[:ARM_DOF].copy(),
                    "servo": (applied_torque - residual).copy(),
                    "policy": residual.copy(),
                }
            else:
                self._last_torque_components = {
                    "total": applied_torque.copy(),
                    "bias": data.qfrc_bias[:ARM_DOF].copy(),
                    "servo": applied_torque.copy(),
                    "policy": np.zeros(ARM_DOF),
                }
        data.ctrl[:ARM_DOF] = applied_torque
        data.ctrl[ARM_DOF] = self.reference.gripper_target(
            time_s - (self.fixture.grasp_time_s - 2.10)
        )
        data.ctrl[self._rod_ctrl] = rod_displacement
        ee_position = data.xpos[self._hand_id].copy()
        ee_rotation = data.xmat[self._hand_id].reshape(3, 3).copy()
        ee_twist = body_twist(model, data, self._hand_id)
        mujoco.mj_step(model, data)
        rod_contact, rod_force, rod_penetration = rod_contact_diagnostics(
            model, data, self._rod_geom_id, self._hand_geom_id
        )
        step_wrench = self._rod_hand_wrench_world()
        if np.linalg.norm(step_wrench) >= np.linalg.norm(self.last_action_contact_wrench_world):
            self.last_action_contact_wrench_world = step_wrench
        self.rod_hand_observed = self.rod_hand_observed or rod_contact
        self.peak_force = max(self.peak_force, rod_force)
        self.contact_impulse += rod_force * CONTROL_DT
        self.last_action_contact_seen = self.last_action_contact_seen or rod_contact
        self.last_action_contact_force = max(self.last_action_contact_force, rod_force)
        self.last_action_contact_penetration = max(self.last_action_contact_penetration, rod_penetration)
        acceleration = (ee_twist - self.previous_twist) / CONTROL_DT
        jerk = (acceleration - self.previous_acceleration) / CONTROL_DT
        jerk_norm = float(np.linalg.norm(jerk[:3]))
        self.peak_jerk = max(self.peak_jerk, jerk_norm)
        release_time_s = (
            self.fixture.rod_start_time_s
            + (self.fixture.rod_cycles - 1) * self.fixture.cycle_period_s
            + self.rod_profile_duration_s
        )
        if self.rod_enabled and release_time_s < time_s < self.fixture.grasp_time_s:
            self.peak_recovery_jerk = max(self.peak_recovery_jerk, jerk_norm)
        self.peak_torque = max(self.peak_torque, float(np.max(np.abs(applied_torque))))
        self.minimum_torque_feasible_scale = min(self.minimum_torque_feasible_scale, feasible_scale)
        self.physics_torque_history.append(applied_torque.copy())
        self.hard_limit_seen = self.hard_limit_seen or bool(
            np.any(np.isclose(np.abs(applied_torque), self.torque_limits, atol=1e-5))
        )
        position_error = float(np.linalg.norm(command.target_position_m - ee_position))
        orientation_error = float(np.linalg.norm(so3_log(command.target_rotation @ ee_rotation.T)))
        twist_error = float(np.linalg.norm(command.task_twist_world - ee_twist))
        torque_ratio = float(np.max(np.abs(applied_torque) / TORQUE_LIMITS))
        self.previous_joint_velocity_command = qdot_command
        self.raw_joint_velocity_command = raw_qdot
        self.previous_torque = applied_torque
        self.previous_twist = ee_twist
        self.previous_acceleration = acceleration
        return position_error, orientation_error, twist_error, torque_ratio, jerk_norm

    def _terminal_info(self) -> dict[str, Any]:
        assert self.data is not None
        target_position = self.data.xpos[self._target_body_id].copy()
        hand_position = self.data.xpos[self._hand_id].copy()
        lifted = bool(target_position[2] > TABLE_TOP_Z + 0.12)
        held = bool(
            target_position[2] > TABLE_TOP_Z + 0.08
            and np.linalg.norm(target_position - hand_position) < 0.16
        )
        effective = bool(
            self.rod_enabled
            and self.rod_hand_observed
            and self.peak_force >= EFFECTIVE_COLLISION_GATE["minimum_peak_contact_force_n"]
            and self.contact_impulse >= EFFECTIVE_COLLISION_GATE["minimum_contact_impulse_ns"]
        )
        finite = bool(np.isfinite(self.data.qpos).all() and np.isfinite(self.data.qvel).all())
        success = bool(finite and lifted and held and not self.hard_limit_seen)
        count = max(1, self.step_count)
        return {
            "task_success": success,
            "effective_collision": effective,
            "rod_hand_contact": self.rod_hand_observed,
            "peak_contact_force_n": self.peak_force,
            "contact_impulse_ns": self.contact_impulse,
            "peak_torque_nm": self.peak_torque,
            "peak_jerk_mps3": self.peak_jerk,
            "peak_recovery_jerk_mps3": self.peak_recovery_jerk,
            "hard_torque_limit": self.hard_limit_seen,
            "finite_state": finite,
            "minimum_torque_feasible_scale": self.minimum_torque_feasible_scale,
            "mean_wbc_slowdown": self.cumulative_wbc_slowdown / count,
            "mean_yield_twist_norm": self.cumulative_yield_norm / count,
            "mean_authority_gate": self.cumulative_authority_gate / count,
            "mean_predictive_authority_multiplier": self.cumulative_predictive_authority_multiplier / count,
            "mean_predictive_wbc_feedback_scale": self.cumulative_predictive_wbc_feedback_scale / count,
            "mean_phase_memory_score": self.cumulative_phase_memory_score / count,
            "mean_phase_memory_gate": self.cumulative_phase_memory_gate / count,
            "mean_stable_phase_memory_floor": self.cumulative_stable_phase_memory_floor / count,
            "mean_energy_tank_multiplier": self.cumulative_energy_tank_multiplier / count,
            "minimum_energy_tank_value": self.minimum_energy_tank_value,
            "action_slew_limited_fraction": self.slew_limited_actions / count,
            "policy_action_saturation_fraction": self.saturated_policy_actions / count,
            "fixture": asdict(self.fixture),
            "controller_family": "direct_esn" if self.observation_mode == "direct_esn" else "wbc_velocity_residual",
            "observation_mode": self.observation_mode,
            "uses_vmc": False,
            "residual_window_end_at_grasp": self.residual_window_end_at_grasp,
        }

    def _rod_hand_wrench_world(self) -> np.ndarray:
        """Net rod-on-hand wrench in the world frame over the last physics step.

        Label/sensor-side diagnostic only: the Direct ESN observation never
        reads it.  The force-feedback VMC baseline consumes it explicitly.
        """

        assert self.data is not None and self.model is not None
        wrench_world = np.zeros(6)
        hand_position = self.data.xpos[self._hand_id]
        local = np.zeros(6)
        for index in range(self.data.ncon):
            contact = self.data.contact[index]
            if {contact.geom1, contact.geom2} != {self._rod_geom_id, self._hand_geom_id}:
                continue
            mujoco.mj_contactForce(self.model, self.data, index, local)
            rotation = np.asarray(contact.frame, dtype=float).reshape(3, 3).T
            # mj_contactForce wrench acts on geom1 pushing it away from geom2.
            if contact.geom1 == self._hand_geom_id:
                force = rotation @ local[:3]
                torque = rotation @ local[3:]
            else:
                force = -(rotation @ local[:3])
                torque = -(rotation @ local[3:])
            arm = np.asarray(contact.pos, dtype=float) - hand_position
            wrench_world[:3] += force
            wrench_world[3:] += torque + np.cross(arm, force)
        # Empirically calibrated against the fixture-2 collision: the raw
        # mj_contactForce summation above yields the wrench pushing the *rod*
        # away, so negate to report the rod-on-hand wrench (rod approaches
        # from -y and pushes the hand toward +y there).
        return -wrench_world

    def _noisy_joint_velocity(self) -> np.ndarray:
        """Sensor-model joint velocity: optional additive Gaussian noise.

        The noise models a low-cost encoder / velocity-estimate channel and
        applies identically to every controller reading the diagnostic
        observation (ESN, MLP, and any baseline consuming the same signal).
        """

        measured = self.data.qvel[:ARM_DOF].copy()
        if self.joint_velocity_noise_std > 0.0:
            measured = measured + self.joint_velocity_noise_std * self.np_random.standard_normal(ARM_DOF)
        return measured

    def diagnostics(self) -> dict[str, Any]:
        """Offline state for matched evaluation; never part of actor input."""

        assert self.data is not None
        time_s = min(self.step_count * RL_DT, SIM_TIME_S)
        command = self._wbc_command(time_s)
        return {
            "time_s": time_s,
            "ee_position": self.data.xpos[self._hand_id].copy(),
            "hand_jacobian": body_jacobian(self.model, self.data, self._hand_id).copy(),
            "ee_rotation": self.data.xmat[self._hand_id].reshape(3, 3).copy(),
            "ee_twist": body_twist(self.model, self.data, self._hand_id),
            "nominal_position": command.target_position_m.copy(),
            "nominal_rotation": command.target_rotation.copy(),
            "nominal_twist": command.task_twist_world.copy(),
            "wbc_pose_error": np.concatenate((
                command.target_position_m - self.data.xpos[self._hand_id],
                so3_log(command.target_rotation @ self.data.xmat[self._hand_id].reshape(3, 3).T),
            )),
            "wbc_twist_error": command.task_twist_world - body_twist(self.model, self.data, self._hand_id),
            "wbc_scale": self.applied_action.wbc_scale,
            "authority_gate": self.current_authority_gate,
            "predictive_authority_multiplier": self.current_predictive_authority_multiplier,
            "predicted_delta_pose_error": self.predicted_delta_pose_error.copy(),
            "predictive_wbc_feedback_scale": self.current_predictive_wbc_feedback_scale,
            "phase_memory_score": self.phase_memory_score,
            "phase_memory_gate": self.phase_memory_gate,
            "stable_phase_memory_floor": self.stable_phase_memory_floor,
            "energy_tank_multiplier": self.current_energy_tank_multiplier,
            "energy_tank_value": self.current_energy_tank_value,
            "cartesian_yield_twist": self.applied_action.cartesian_yield_twist.copy(),
            "joint_velocity_command": self.previous_joint_velocity_command.copy(),
            "raw_joint_velocity_command": self.raw_joint_velocity_command.copy(),
            "applied_torque": self.previous_torque.copy(),
            "torque_components": self._last_torque_components,
            "shadow_torque_components": self._shadow_torque_components,
            "joint_position": self.data.qpos[:ARM_DOF].copy(),
            "joint_velocity": self._noisy_joint_velocity(),
        }

    def step(self, action: np.ndarray) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        action = np.asarray(action, dtype=float)
        if action.shape != (7,) or not np.all(np.isfinite(action)):
            raise ValueError("direct WBC residual action must be a finite seven-vector")
        raw_policy_action = np.clip(action, -1.0, 1.0)
        if self.execution_mode == "torque_residual":
            # Action contract in this mode: 7-D per-joint residual torque in
            # units of the per-joint residual budget ([-1, 1] each).
            self._residual_torque_command = raw_policy_action * self.residual_torque_limits
        elif self.execution_mode in ("torque_takeover", "torque_takeover_gc"):
            # Action contract in these modes: 7-D total joint torque in units
            # of the per-joint HARDWARE torque limits ([-1, 1] each).
            self._takeover_torque_command = raw_policy_action * TORQUE_LIMITS
        self.last_action_contact_force = 0.0
        self.last_action_contact_penetration = 0.0
        self.last_action_contact_seen = False
        # Twist-mode compliance channel: the action's wbc_scale slot doubles
        # as WBC feedback-authority scheduling (feedforward stays full-rate).
        if self.execution_mode == "twist" and self.observation_mode == "direct_esn":
            self.current_predictive_wbc_feedback_scale = float(
                getattr(self, "_last_policy_wbc_scale", 1.0))
        command = self._wbc_command(self.step_count * RL_DT)
        assert self.data is not None
        pose_error = np.concatenate((
            command.target_position_m - self.data.xpos[self._hand_id],
            so3_log(command.target_rotation @ self.data.xmat[self._hand_id].reshape(3, 3).T),
        ))
        twist_error = command.task_twist_world - body_twist(self.model, self.data, self._hand_id)
        tracking_error = float(np.linalg.norm(pose_error[:3]))
        self.current_authority_gate = deployable_authority_gate(tracking_error, self.safety_config)
        direct_esn_mode = self.observation_mode == "direct_esn"
        if direct_esn_mode:
            # Direct ESN is the primary collision-response policy in this
            # mode. Do not apply the legacy PPO authority gate, phase
            # projection, predictive WBC gain modulation, or energy tank.
            self.current_authority_gate = 1.0
        self.phase_memory_gate = 0.0
        if self.observation_mode in ("fan_ye_phase_esn", "fan_ye_stable_phase_esn", "fan_ye_phase_predictive_wbc_esn"):
            scaled_error = pose_error / WBC_POSE_ERROR_SCALE
            scaled_twist = twist_error / WBC_TWIST_ERROR_SCALE
            error_norm = float(np.linalg.norm(scaled_error))
            twist_norm = float(np.linalg.norm(scaled_twist))
            rejoin_confidence = 0.0 if error_norm <= 1.0e-6 or twist_norm <= 1.0e-6 else float(np.clip(
                -np.dot(scaled_error, scaled_twist) / (error_norm * twist_norm), 0.0, 1.0,
            ))
            if self.observation_mode in ("fan_ye_stable_phase_esn", "fan_ye_phase_predictive_wbc_esn"):
                self.stable_phase_memory_floor = stable_phase_memory_floor(
                    self.phase_memory_score, rejoin_confidence, tracking_error,
                    self.stable_phase_memory_floor, RL_DT, self.safety_config,
                )
                self.phase_memory_gate = self.stable_phase_memory_floor
            else:
                self.phase_memory_gate = float(np.clip(
                    0.55 * self.phase_memory_score * rejoin_confidence, 0.0, 0.55,
                ))
            self.current_authority_gate = max(self.current_authority_gate, self.phase_memory_gate)
        if self.observation_mode == "fan_ye_forecast_authority_esn":
            kinematic_delta = encode_kinematic_pose_forecast(pose_error, twist_error)
            self.current_predictive_authority_multiplier = predictive_authority_multiplier(
                pose_error / WBC_POSE_ERROR_SCALE, self.predicted_delta_pose_error, self.safety_config,
                kinematic_delta_pose_error=kinematic_delta,
                measured_pose_error_rate=twist_error / WBC_POSE_ERROR_SCALE,
            )
        else:
            self.current_predictive_authority_multiplier = 1.0
        # The benchmark's perturbation is defined during the fixed WBC approach
        # and rejoin window.  Once the preplanned gripper-close phase begins,
        # residual authority smoothly exits through the same action filter and
        # the fixed WBC owns lift/carry.  This uses only the WBC task phase, not
        # a contact, force, rod, obstacle, or future-release signal.
        if self.residual_window_end_at_grasp and self.step_count * RL_DT >= self.fixture.grasp_time_s:
            self.current_authority_gate = 0.0
        self.current_authority_gate *= self.current_predictive_authority_multiplier
        if direct_esn_mode:
            phase_projected_action = raw_policy_action.copy()
            gated_action = phase_projected_action.copy()
            self.current_energy_tank_multiplier = 1.0
            self.current_energy_tank_value = self.energy_tank.energy
        else:
            phase_projected_action = project_yield_action_to_error_phase(
                raw_policy_action, pose_error, twist_error, self.safety_config,
            )
            phase_projected_action = apply_rejoin_velocity_envelope(
                phase_projected_action, pose_error, twist_error, self.safety_config,
            )
            phase_projected_action, self.current_energy_tank_multiplier, self.current_energy_tank_value = self.energy_tank.apply(
                phase_projected_action, pose_error, twist_error, RL_DT, self.phase_memory_score,
            )
            gated_action = phase_projected_action.copy()
            gated_action[0] *= self.current_authority_gate
            gated_action[1:] *= self.current_authority_gate
        self.applied_action = self.action_filter.filter(gated_action, RL_DT)
        if self.execution_mode == "twist" and self.observation_mode == "direct_esn":
            # The wbc_scale channel is consumed as WBC feedback-authority
            # scheduling (wired above); applying it multiplicatively on the
            # composed command as well would double-count the slowdown.
            from dataclasses import replace as _dc_replace
            self._last_policy_wbc_scale = float(self.applied_action.wbc_scale)
            if self.applied_action.wbc_scale != 1.0:
                self.applied_action = _dc_replace(self.applied_action, wbc_scale=1.0)
        self.slew_limited_actions += int(self.applied_action.slew_limited)
        self.saturated_policy_actions += int(np.any(np.abs(raw_policy_action) >= 0.98))
        self.cumulative_wbc_slowdown += 1.0 - self.applied_action.wbc_scale
        self.cumulative_yield_norm += float(np.linalg.norm(self.applied_action.cartesian_yield_twist))
        self.cumulative_authority_gate += self.current_authority_gate
        self.cumulative_predictive_authority_multiplier += self.current_predictive_authority_multiplier
        self.cumulative_predictive_wbc_feedback_scale += self.current_predictive_wbc_feedback_scale
        self.cumulative_phase_memory_score += self.phase_memory_score
        self.cumulative_phase_memory_gate += self.phase_memory_gate
        self.cumulative_stable_phase_memory_floor += self.stable_phase_memory_floor
        self.cumulative_energy_tank_multiplier += self.current_energy_tank_multiplier
        self.minimum_energy_tank_value = min(self.minimum_energy_tank_value, self.current_energy_tank_value)
        impulse_before = self.contact_impulse
        action_start_error = self.previous_position_error
        final_position_error = 0.0
        peak_step_jerk = 0.0
        reward = 0.0
        release_time_s = (
            self.fixture.rod_start_time_s
            + (self.fixture.rod_cycles - 1) * self.fixture.cycle_period_s
            + self.rod_profile_duration_s
        )
        for substep in range(PHYSICS_STEPS_PER_ACTION):
            time_s = self.step_count * RL_DT + substep * CONTROL_DT
            position_error, orientation_error, twist_error, torque_ratio, jerk_norm = self._physics_step(time_s)
            final_position_error = position_error
            peak_step_jerk = max(peak_step_jerk, jerk_norm)
            reward -= (
                self.reward_config.position_error_weight * min(position_error / 0.06, 3.0)
                + self.reward_config.orientation_error_weight * min(orientation_error / 0.20, 3.0)
                + self.reward_config.twist_error_weight * min(twist_error / 2.2, 3.0)
                + self.reward_config.torque_weight * torque_ratio**2
            ) / PHYSICS_STEPS_PER_ACTION
            if self.rod_enabled and release_time_s < time_s < self.fixture.grasp_time_s:
                reward -= self.reward_config.post_release_error_weight * min(
                    (position_error / 0.012) ** 2, 4.0
                ) / PHYSICS_STEPS_PER_ACTION
        if self.last_action_contact_seen:
            self.dagger_contact_duration_s += RL_DT
        else:
            self.dagger_contact_duration_s = 0.0
        slowdown = 1.0 - self.applied_action.wbc_scale
        normalized_yield = np.concatenate((
            self.applied_action.cartesian_yield_twist[:3] / self.safety_config.maximum_linear_yield_mps,
            self.applied_action.cartesian_yield_twist[3:] / self.safety_config.maximum_angular_yield_radps,
        ))
        action_change = float(np.mean((raw_policy_action - self.previous_policy_action) ** 2))
        reward -= self.reward_config.slowdown_weight * slowdown**2
        reward -= self.reward_config.yield_magnitude_weight * float(np.mean(normalized_yield**2))
        reward -= self.reward_config.action_change_weight * action_change
        reward -= self.reward_config.raw_policy_action_weight * float(np.mean(raw_policy_action**2))
        reward -= self.reward_config.contact_impulse_weight * max(0.0, self.contact_impulse - impulse_before)
        if self.rod_enabled and release_time_s < self.step_count * RL_DT < self.fixture.grasp_time_s:
            progress = float(np.clip((action_start_error - final_position_error) / 0.004, -1.0, 1.0))
            reward += self.reward_config.recovery_progress_weight * progress
            normalized_jerk = min((peak_step_jerk / self.reward_config.jerk_reference_mps3) ** 2, 4.0)
            reward -= self.reward_config.recovery_jerk_weight * normalized_jerk
        self.previous_position_error = final_position_error
        self.previous_policy_action = phase_projected_action.copy()
        self.step_count += 1
        terminated = self.step_count >= int(round(SIM_TIME_S / RL_DT))
        info: dict[str, Any] = {}
        if terminated:
            info = self._terminal_info()
            valid_success = info["task_success"] and (
                info["effective_collision"] if self.rod_enabled else True
            )
            reward += self.reward_config.terminal_bonus if valid_success else -self.reward_config.terminal_bonus
        observation = self._observation(min(self.step_count * RL_DT, SIM_TIME_S))
        return observation, float(reward), terminated, False, info

    def close(self) -> None:
        self.model = None
        self.data = None
