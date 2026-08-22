"""Independent WBC-aware velocity-residual environment for MLP/ESN control.

The proposed actor is not connected to the VMC virtual springs.  A fixed Panda
WBC produces the nominal task command.  The learned actor may only slow that
command and add a bounded six-dimensional Cartesian yield velocity.  A shared
adapter enforces action, joint-velocity, joint-acceleration, torque, and torque
slew limits before applying commands to the physical MuJoCo Panda.
"""

from __future__ import annotations

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
from run_grasp_impact_benchmark import LIFT_COMPLETE_TIME_S, TABLE_TOP_Z, TARGET_START_Z, PickLiftCarryReference
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
    # Physical external-apparatus/contact parameters.  They are injected only
    # into MuJoCo scene construction and never into the policy observation.
    # Defaults reproduce the historical FR3 benchmark exactly.
    impactor_mass_kg: float | None = None
    rod_slide_damping: float = 2.0
    rod_driver_kp: float = 5000.0
    rod_driver_force_limit_n: float = 300.0
    contact_time_constant_s: float = CONTACT_TIME_CONSTANT_S


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
        lift_board_y_offset_m: float = 0.0,
        lift_board_z_offset_m: float = 0.0,
        lift_board_yaw_deg: float = 0.0,
        lift_board_contact_mode: str = "side_slide",
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
        if lift_board_contact_mode not in (
            "side_slide", "front_face", "front_longitudinal", "dual_phase_longitudinal",
        ):
            raise ValueError(
                "lift_board_contact_mode must be 'side_slide', 'front_face', "
                "'front_longitudinal', or 'dual_phase_longitudinal'"
            )
        self.lift_board_contact_mode = lift_board_contact_mode
        self._front_face_initial_qpos: np.ndarray | None = None
        if not np.isfinite(lift_board_y_offset_m):
            raise ValueError("lift_board_y_offset_m must be finite")
        self.lift_board_y_offset_m = float(lift_board_y_offset_m)
        if not np.isfinite(lift_board_z_offset_m):
            raise ValueError("lift_board_z_offset_m must be finite")
        self.lift_board_z_offset_m = float(lift_board_z_offset_m)
        if not np.isfinite(lift_board_yaw_deg):
            raise ValueError("lift_board_yaw_deg must be finite")
        self.lift_board_yaw_deg = float(lift_board_yaw_deg)
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
        self._lift_board_geom_id = -1
        # Dual-phase boards are separate fixed MuJoCo geoms.  Their state is
        # retained only for post-episode auditing; it is never used by the
        # 32-D direct-ESN observation or the controller action path.
        self._dual_board_geom_ids: dict[str, int] = {}
        self.dual_board_metrics: dict[str, dict[str, Any]] = {}
        # Reset-time board contacts invalidate an episode: a board must be
        # encountered by the moving robot, never start intersecting it.
        self.dual_initial_board_contacts: dict[str, list[str]] = {}
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
        self.lift_board_peak_force = 0.0
        self.lift_board_contact_impulse = 0.0
        self.lift_board_contact_duration_s = 0.0
        self.lift_board_contact_bout_count = 0
        self.lift_board_first_contact_s = None
        self._previous_lift_board_contact = False
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
                impactor_mass_kg=self.fixture.impactor_mass_kg,
                rod_slide_damping=self.fixture.rod_slide_damping,
                rod_driver_kp=self.fixture.rod_driver_kp,
                rod_driver_force_limit_n=self.fixture.rod_driver_force_limit_n,
            )
            if self.lift_board_tilt_deg is not None:
                # Two-pass placement: a throwaway board-free build provides
                # the lift-path FK, then the real scene is rebuilt with the
                # inclined static board centered on the mid-lift waypoint so
                # the rising arm strikes its tilted face.  The board scenario
                # uses a lateral lift arc (joint 2 offset) so the descent
                # path and the board are geometrically separated — the arm
                # strikes the board only while moving bottom-up.
                def side_slide_reference(model_, data_, hand_id_):
                    ref = PickLiftCarryReference(model_, data_, hand_id_)
                    knots = ref.q_knots.copy()
                    # Lateral arc on joint 1 (base yaw, z-axis): at this
                    # configuration joint 2's axis is horizontal and moves the
                    # EE in x-z, NOT laterally -- the first attempt used joint
                    # 2 and the hand never left y=0 (the board was never
                    # touched).  Joint 1 swings the EE along +y as required.
                    knots[3][0] += 0.40   # lifted: lateral arc on joint 1
                    knots[4][0] += 0.40   # carry: keep the offset
                    ref.q_knots = knots
                    return ref

                def front_face_reference(model_, data_, hand_id_):
                    """Move below the overhang, then raise into its face.

                    The arm follows a normal centre-line pick-down motion,
                    sweeps sideways only after reaching the low pregrasp
                    height, and performs the vertical lift beneath the fixed
                    board.  Thus it never crosses the board while descending
                    from home, and all later contact is standard MuJoCo
                    contact rather than a pose correction or teleportation.
                    """
                    ref = PickLiftCarryReference(model_, data_, hand_id_)
                    home = ref.q_knots[0].copy()
                    pregrasp = ref.q_knots[1].copy()
                    lifted = ref.q_knots[3].copy()
                    carry = ref.q_knots[4].copy()
                    # The stock FR3 pregrasp wrist frame leaves the distal
                    # hand mesh about 110 mm above the tabletop object.  Move
                    # the grasp posture down by 0.18 rad at joint 4 so the
                    # actual collision mesh, not its wrist origin, encloses
                    # the free target before the lift begins.
                    pregrasp[3] -= 0.18
                    lifted[3] -= 0.18
                    under_board_pregrasp = pregrasp.copy()
                    under_board_lifted = lifted.copy()
                    under_board_carry = carry.copy()
                    under_board_pregrasp[0] += 0.80
                    under_board_lifted[0] += 0.80
                    under_board_carry[0] += 0.80
                    ref.times = np.array([0.0, 1.70, 2.70, LIFT_COMPLETE_TIME_S, 6.20])
                    ref.q_knots = np.stack((
                        home, pregrasp, under_board_pregrasp, under_board_lifted, under_board_carry,
                    ))
                    return ref

                probe_model, probe_data = make_fr3_hand_model(
                    self.menagerie, self.fixture.contact_time_constant_s, **scene_kwargs)
                probe_hand = mujoco.mj_name2id(
                    probe_model, mujoco.mjtObj.mjOBJ_BODY, "hand")
                if self.lift_board_contact_mode == "side_slide":
                    probe_ref = side_slide_reference(probe_model, probe_data, probe_hand)
                    p_start = probe_ref.sample(2.70)[0]
                    p_end = probe_ref.sample(4.10)[0]
                    center = 0.75 * p_start + 0.25 * p_end
                    # Rotating the board around world z changes its projected
                    # lateral span.  Place its near edge above the entire
                    # descent/grasp envelope before adding it to the rising arc;
                    # otherwise yaw=45/90 deg would physically intersect the
                    # hand at t=0 and masquerade as a frontal lift collision.
                    yaw = np.deg2rad(self.lift_board_yaw_deg)
                    projected_half_y = abs(np.sin(yaw)) * 0.18 + abs(np.cos(yaw)) * 0.05
                    negative_jitter_guard = max(0.0, -self.lift_board_y_offset_m)
                    min_center_y = projected_half_y + 0.07 + negative_jitter_guard
                    center[1] = max(center[1] + 0.09, min_center_y) + self.lift_board_y_offset_m
                    scene_kwargs["lift_board_size_m"] = (0.18, 0.05, 0.008)
                    self._board_reference_factory = side_slide_reference
                elif self.lift_board_contact_mode == "front_face":
                    # Front-face mode is deliberately a different physical
                    # setup, not a yaw variation of the edge-slide scene.
                    # The nominal reference is left unmodified (y=0), and a
                    # 36 x 28 cm board is centered over the lift corridor.
                    # Its underside is 60 mm above the t=3.20 EE reference,
                    # so the arm begins collision-free and then approaches
                    # the broad lower face from below.  The board stays
                    # mildly inclined, retaining the intended compliant-slide
                    # behavior after a genuine frontal impact.
                    probe_ref = front_face_reference(probe_model, probe_data, probe_hand)
                    self._front_face_initial_qpos = None
                    # Place the fixed board over the distal link-7 trajectory
                    # at the planned impact instant.  The reference is
                    # evaluated in a board-free probe model, so this is a
                    # deterministic geometry calculation, not feedback.
                    probe_ref.sample(3.80)
                    link7_collision = mujoco.mj_name2id(
                        probe_model, mujoco.mjtObj.mjOBJ_GEOM, "fr3_link7_collision")
                    center = probe_ref._work.geom_xpos[link7_collision].copy()
                    # Align the board in the *MuJoCo collision-geometry*
                    # frame, not the wrist-body frame.  This is an offline
                    # scene-construction calculation only; no board pose or
                    # contact signal is exposed to any controller.
                    # Leave 35 mm of initial vertical clearance above the
                    # link-7 collision envelope, then let the rising hand
                    # make the first contact with the board's underside.
                    center[2] += 0.035 + self.lift_board_z_offset_m
                    center[1] += self.lift_board_y_offset_m
                    scene_kwargs["lift_board_size_m"] = (0.120, 0.120, 0.008)
                    self._board_reference_factory = front_face_reference
                elif self.lift_board_contact_mode == "front_longitudinal":
                    # The corrected demo: a near-vertical board faces the
                    # long axis of the distal hand/link-7 collision geometry.
                    # The arm rises underneath and the longitudinal side of
                    # the end-effector sweeps into the board face.
                    probe_ref = front_face_reference(probe_model, probe_data, probe_hand)
                    probe_ref.sample(3.80)
                    hand_collision = mujoco.mj_name2id(
                        probe_model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
                    link7_collision = mujoco.mj_name2id(
                        probe_model, mujoco.mjtObj.mjOBJ_GEOM, "fr3_link7_collision")
                    hand_axes = probe_ref._work.geom_xmat[hand_collision].reshape(3, 3)
                    long_axis = hand_axes[:, 2].copy()
                    long_axis[2] = 0.0
                    long_axis /= max(float(np.linalg.norm(long_axis)), 1e-12)
                    # For Rx(90°) followed by Rz(yaw), board +z is
                    # [sin(yaw), -cos(yaw), 0].
                    longitudinal_yaw = float(np.rad2deg(np.arctan2(long_axis[0], -long_axis[1])))
                    center = probe_ref._work.geom_xpos[hand_collision].copy()
                    center += long_axis * 0.085
                    # The paper-MPC/WBC tracking of the large base-yaw
                    # under-board arc settles about 180 mm inward in x/y and
                    # 120 mm lower in z than the pure FK waypoint.  Apply
                    # this fixed, board-free calibration so the vertical
                    # plank meets the longitudinal hand section rather than
                    # upstream link 5.  It is scene geometry, not an online
                    # observation supplied to a controller.
                    center += np.array([0.18, -0.18, -0.12])
                    board_x = np.array([np.cos(np.deg2rad(longitudinal_yaw)),
                                        np.sin(np.deg2rad(longitudinal_yaw)), 0.0])
                    # The first longitudinal contact was at the +local-x
                    # edge. Shift the finite board along its own long axis so
                    # the link-6/link-7 contact patch is on the broad face.
                    center -= board_x * 0.160
                    center[2] += self.lift_board_z_offset_m
                    center[1] += self.lift_board_y_offset_m
                    # Local y becomes world vertical after the 90° tilt.  A
                    # 120 mm vertical face is sufficient for the longitudinal
                    # hand section but excludes the upstream link-5 envelope.
                    scene_kwargs["lift_board_size_m"] = (0.20, 0.04, 0.008)
                    scene_kwargs["lift_board_tilt_deg"] = 90.0
                    scene_kwargs["lift_board_yaw_deg"] = longitudinal_yaw
                    self._board_reference_factory = front_face_reference
                else:
                    # Unified physical task: two *different*, static wooden
                    # boards.  Both are constructed from a board-free FK
                    # probe but remain fixed world geoms throughout rollout.
                    #
                    # All methods share this obstacle-agnostic reference.  It
                    # preserves the previously audited block-centred pregrasp
                    # and adds only a modest common lateral lift component
                    # after the close command, so the object is mechanically
                    # pinched before it encounters the second board.
                    def dual_phase_reference(model_, data_, hand_id_):
                        ref = PickLiftCarryReference(model_, data_, hand_id_)
                        home = ref.q_knots[0].copy()
                        pregrasp = ref.q_knots[1].copy()
                        grasp = ref.q_knots[2].copy()
                        lifted = ref.q_knots[3].copy()
                        carry = ref.q_knots[4].copy()
                        lifted[0] -= 0.26
                        carry[0] -= 0.26
                        ref.times = np.array([0.0, 1.70, 2.70, 4.20, 6.20])
                        ref.q_knots = np.stack((home, pregrasp, grasp, lifted, carry))
                        return ref

                    probe_ref = dual_phase_reference(probe_model, probe_data, probe_hand)
                    hand_collision = mujoco.mj_name2id(
                        probe_model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
                    collision_radius = float(probe_model.geom_rbound[hand_collision])

                    def dual_board_center(time_s: float, normal: np.ndarray) -> np.ndarray:
                        probe_ref.sample(time_s)
                        point = probe_ref._work.geom_xpos[hand_collision].copy()
                        # Put the physical face just ahead of the collision
                        # mesh along its planned travel direction.  The small
                        # clearance prevents an artificial initial overlap.
                        # `geom_rbound` is a conservative enclosing sphere
                        # for the hand mesh.  A 5-mm clearance avoids a reset
                        # overlap without placing the finite board so far away
                        # that the real collision mesh never reaches it.
                        point += normal * (collision_radius + 0.005)
                        point[1] += self.lift_board_y_offset_m
                        point[2] += self.lift_board_z_offset_m
                        return point

                    # The pre-grasp board is a finite horizontal plank with a
                    # free edge at y=30 mm.  During descent, the longitudinal
                    # hand/link-7 collision meshes meet its broad top face and
                    # can slide over that edge; the fingers and block are not
                    # enclosed by an infinite shelf.  Its pose was selected by
                    # a board-free geometry scan with a zero-contact reset gate.
                    pre = np.array([
                        0.550,
                        0.050 + self.lift_board_y_offset_m,
                        0.540 + self.lift_board_z_offset_m,
                    ])
                    # Rz(0) Rx(90) maps board +z to -y for the second,
                    # vertical plank.  The already-grasped hand rises into its
                    # broad face and has a finite lateral edge to slide around.
                    post = dual_board_center(3.35, np.array([0.0, -1.0, 0.0]))
                    scene_kwargs["dual_board_specs"] = (
                        ("pregrasp_board", tuple(float(v) for v in pre), 0.0, 0.0,
                         (0.120, 0.020, 0.008)),
                        ("postgrasp_board", tuple(float(v) for v in post), 90.0, 0.0,
                         (0.105, 0.075, 0.008)),
                    )
                    self._board_reference_factory = dual_phase_reference
                if self.lift_board_contact_mode != "dual_phase_longitudinal":
                    scene_kwargs["lift_board_center_m"] = tuple(float(v) for v in center)
                    if self.lift_board_contact_mode != "front_longitudinal":
                        scene_kwargs["lift_board_tilt_deg"] = float(self.lift_board_tilt_deg)
                        scene_kwargs["lift_board_yaw_deg"] = float(self.lift_board_yaw_deg)
            else:
                self._board_reference_factory = None
            self.model, self.data = make_fr3_hand_model(
                self.menagerie, self.fixture.contact_time_constant_s, **scene_kwargs)
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
        self._lift_board_geom_id = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_GEOM, "lift_board")
        self._dual_board_geom_ids = {
            name: mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, name)
            for name in ("pregrasp_board", "postgrasp_board")
        }
        if self.lift_board_contact_mode == "dual_phase_longitudinal" and min(
            self._dual_board_geom_ids.values()
        ) < 0:
            raise RuntimeError("dual-phase board scene IDs were not resolved")
        self._target_qpos = int(model.jnt_qposadr[ids["target_freejoint"]])
        self._target_dof = int(model.jnt_dofadr[ids["target_freejoint"]])
        self._obstacle_mocap = int(model.body_mocapid[ids["moving_obstacle"]])
        self._rod_ctrl = ARM_DOF + 1
        if model.nu != ARM_DOF + 2 or self._obstacle_mocap < 0:
            raise RuntimeError("expected Panda torques, gripper, rod driver, and diagnostic mocap")
        if not self.rod_enabled:
            # The rail apparatus is intentionally absent from board-only
            # episodes.  Leaving its inactive collision geom enabled would
            # let a hidden rod touch a board at reset, which is neither a
            # robot--board interaction nor a valid task initialization.
            model.geom_contype[self._rod_geom_id] = 0
            model.geom_conaffinity[self._rod_geom_id] = 0
            model.geom_rgba[self._rod_geom_id, 3] = 0.0
        data.qpos[self._target_qpos:self._target_qpos + 7] = [
            0.54, 0.0, TARGET_START_Z, 1.0, 0.0, 0.0, 0.0,
        ]
        data.qvel[self._target_dof:self._target_dof + 6] = 0.0
        if self._front_face_initial_qpos is not None:
            data.qpos[:ARM_DOF] = self._front_face_initial_qpos
            data.qvel[:ARM_DOF] = 0.0
        mujoco.mj_forward(model, data)
        self.dual_initial_board_contacts = {}
        if self.lift_board_contact_mode == "dual_phase_longitudinal":
            for name, board_id in self._dual_board_geom_ids.items():
                contact, _, _, _, _, partners = self._board_contact_diagnostics(board_id)
                if contact:
                    self.dual_initial_board_contacts[name] = partners
            if self.dual_initial_board_contacts:
                raise RuntimeError(
                    "dual-phase scene has invalid t=0 board contact: "
                    f"{self.dual_initial_board_contacts}"
                )
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
        self.lift_board_peak_force = 0.0
        self.lift_board_contact_impulse = 0.0
        self.lift_board_contact_duration_s = 0.0
        self.lift_board_contact_bout_count = 0
        self.lift_board_first_contact_s = None
        self._previous_lift_board_contact = False
        self.dual_board_metrics = {
            name: {
                "contact": False, "first_contact_s": None, "peak_force_n": 0.0,
                "contact_impulse_ns": 0.0, "contact_duration_s": 0.0,
                "contact_bout_count": 0, "max_penetration_m": 0.0,
                "hand_collision_contact": False, "link7_collision_contact": False,
                "hand_body_contact": False, "link7_body_contact": False,
                "target_object_contact": False,
                "target_lift_at_first_contact_m": None,
                "contact_geom_names": [],
                "previous_contact": False,
            }
            for name, geom_id in self._dual_board_geom_ids.items() if geom_id >= 0
        }
        self.physics_torque_history = []
        self.last_action_contact_force = 0.0
        self.last_action_contact_penetration = 0.0
        self.last_action_contact_wrench_world = np.zeros(6)
        self.last_action_contact_seen = False
        self.dagger_contact_duration_s = 0.0
        self.minimum_torque_feasible_scale = 1.0
        self.hard_limit_seen = self.rod_hand_observed = False
        self.contact_bout_count = 0
        self._previous_rod_hand_contact = False
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
        if self.rod_enabled:
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
        gripper_time = time_s if self.lift_board_contact_mode == "front_longitudinal" else (
            time_s - (self.fixture.grasp_time_s - 2.10))
        data.ctrl[ARM_DOF] = self.reference.gripper_target(gripper_time)
        data.ctrl[self._rod_ctrl] = rod_displacement
        ee_position = data.xpos[self._hand_id].copy()
        ee_rotation = data.xmat[self._hand_id].reshape(3, 3).copy()
        ee_twist = body_twist(model, data, self._hand_id)
        mujoco.mj_step(model, data)
        board_contact, board_force = self._lift_board_contact_diagnostics()
        if board_contact:
            self.lift_board_contact_duration_s += CONTROL_DT
            self.lift_board_contact_impulse += board_force * CONTROL_DT
            if self.lift_board_first_contact_s is None:
                self.lift_board_first_contact_s = float(time_s + CONTROL_DT)
            if not self._previous_lift_board_contact:
                self.lift_board_contact_bout_count += 1
        self._previous_lift_board_contact = bool(board_contact)
        self.lift_board_peak_force = max(self.lift_board_peak_force, board_force)
        # Audit the two task phases separately.  These values intentionally
        # remain after `mj_step` and outside `_observation`: a policy can only
        # infer contact through its permitted proprioceptive/WBC-error history.
        for name, board_id in self._dual_board_geom_ids.items():
            if board_id < 0 or name not in self.dual_board_metrics:
                continue
            contact, force, penetration, hand_hit, link7_hit, partners = self._board_contact_diagnostics(board_id)
            metrics = self.dual_board_metrics[name]
            if contact:
                metrics["contact"] = True
                metrics["contact_duration_s"] = float(metrics["contact_duration_s"]) + CONTROL_DT
                metrics["contact_impulse_ns"] = float(metrics["contact_impulse_ns"]) + force * CONTROL_DT
                if metrics["first_contact_s"] is None:
                    metrics["first_contact_s"] = float(time_s + CONTROL_DT)
                    metrics["target_lift_at_first_contact_m"] = float(
                        self.data.xpos[self._target_body_id][2] - TABLE_TOP_Z
                    )
                if not bool(metrics["previous_contact"]):
                    metrics["contact_bout_count"] = int(metrics["contact_bout_count"]) + 1
            metrics["previous_contact"] = bool(contact)
            metrics["peak_force_n"] = max(float(metrics["peak_force_n"]), force)
            metrics["max_penetration_m"] = max(float(metrics["max_penetration_m"]), penetration)
            metrics["hand_collision_contact"] = bool(metrics["hand_collision_contact"]) or hand_hit
            metrics["link7_collision_contact"] = bool(metrics["link7_collision_contact"]) or link7_hit
            metrics["hand_body_contact"] = bool(metrics["hand_body_contact"]) or any(
                partner == "hand_collision" or partner.startswith("hand/") for partner in partners)
            metrics["link7_body_contact"] = bool(metrics["link7_body_contact"]) or any(
                partner == "fr3_link7_collision" or partner.startswith("fr3_link7/")
                for partner in partners
            )
            metrics["target_object_contact"] = bool(metrics["target_object_contact"]) or (
                "target_object_geom" in partners
            )
            known_partners = set(metrics["contact_geom_names"])
            known_partners.update(partners)
            metrics["contact_geom_names"] = sorted(known_partners)
        rod_contact, rod_force, rod_penetration = rod_contact_diagnostics(
            model, data, self._rod_geom_id, self._hand_geom_id
        )
        step_wrench = self._rod_hand_wrench_world()
        if np.linalg.norm(step_wrench) >= np.linalg.norm(self.last_action_contact_wrench_world):
            self.last_action_contact_wrench_world = step_wrench
        self.rod_hand_observed = self.rod_hand_observed or rod_contact
        if rod_contact and not self._previous_rod_hand_contact:
            self.contact_bout_count += 1
        self._previous_rod_hand_contact = bool(rod_contact)
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
        base_success = bool(finite and lifted and held and not self.hard_limit_seen)
        count = max(1, self.step_count)
        dual_metrics = {
            name: {key: value for key, value in metrics.items() if key != "previous_contact"}
            for name, metrics in self.dual_board_metrics.items()
        }
        pre = dual_metrics.get("pregrasp_board", {})
        post = dual_metrics.get("postgrasp_board", {})
        dual_phase_valid = bool(
            pre.get("contact")
            and post.get("contact")
            and pre.get("first_contact_s") is not None
            and post.get("first_contact_s") is not None
            and float(pre["first_contact_s"]) < self.fixture.grasp_time_s
            and float(post["first_contact_s"]) > self.fixture.grasp_time_s
            and float(pre["first_contact_s"]) < float(post["first_contact_s"])
            and bool(pre.get("hand_body_contact") or pre.get("link7_body_contact"))
            and bool(post.get("hand_body_contact") or post.get("link7_body_contact"))
            and not bool(pre.get("target_object_contact"))
            and not bool(post.get("target_object_contact"))
            and float(pre.get("target_lift_at_first_contact_m") or 0.0) < 0.04
            and float(post.get("target_lift_at_first_contact_m") or 0.0) > 0.08
            and float(pre.get("max_penetration_m") or 0.0) < 0.002
            and float(post.get("max_penetration_m") or 0.0) < 0.002
        )
        success = bool(base_success and (
            self.lift_board_contact_mode != "dual_phase_longitudinal" or dual_phase_valid
        ))
        return {
            "task_success": success,
            "final_target_position_m": target_position.tolist(),
            "final_hand_position_m": hand_position.tolist(),
            "final_hand_target_distance_m": float(np.linalg.norm(target_position - hand_position)),
            "final_target_lift_m": float(target_position[2] - TABLE_TOP_Z),
            "effective_collision": effective,
            "rod_hand_contact": self.rod_hand_observed,
            "contact_bout_count": self.contact_bout_count,
            "peak_contact_force_n": self.peak_force,
            "contact_impulse_ns": self.contact_impulse,
            "lift_board_contact": bool(self.lift_board_contact_bout_count > 0),
            "lift_board_first_contact_s": self.lift_board_first_contact_s,
            "lift_board_peak_force_n": self.lift_board_peak_force,
            "lift_board_contact_impulse_ns": self.lift_board_contact_impulse,
            "lift_board_contact_duration_s": self.lift_board_contact_duration_s,
            "lift_board_contact_bout_count": self.lift_board_contact_bout_count,
            "dual_board_metrics": dual_metrics,
            "dual_initial_board_contacts": self.dual_initial_board_contacts,
            "dual_phase_geometry_valid": dual_phase_valid,
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

    def _board_contact_diagnostics(
        self, board_id: int,
    ) -> tuple[bool, float, float, bool, bool, list[str]]:
        """Return contact metadata for one fixed board geom.

        The exact collision partners and non-positive MuJoCo contact distance
        are retained so a reported recovery can be audited for real body--board
        contact and bounded numerical penetration.
        """
        if board_id < 0:
            return False, 0.0, 0.0, False, False, []
        assert self.data is not None and self.model is not None
        total = 0.0
        peak_penetration = 0.0
        seen = hand_hit = link7_hit = False
        partners: set[str] = set()
        link7_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "fr3_link7_collision")
        local = np.zeros(6)
        for index in range(self.data.ncon):
            contact = self.data.contact[index]
            if board_id not in (int(contact.geom1), int(contact.geom2)):
                continue
            seen = True
            other_id = int(contact.geom2) if int(contact.geom1) == board_id else int(contact.geom1)
            other_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, other_id)
            # Several fingertip collision geoms are intentionally unnamed in
            # the menagerie XML.  Preserve their numeric identity rather than
            # silently losing them or failing on a mixed None/string sort.
            if other_name is None:
                body_id = int(self.model.geom_bodyid[other_id])
                body_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_BODY, body_id)
                partners.add(f"{body_name or 'unnamed_body'}/geom_{other_id}")
            else:
                partners.add(other_name)
            hand_hit = hand_hit or other_id == self._hand_geom_id
            link7_hit = link7_hit or other_id == link7_id
            peak_penetration = max(peak_penetration, max(0.0, -float(contact.dist)))
            mujoco.mj_contactForce(self.model, self.data, index, local)
            total += float(np.linalg.norm(local[:3]))
        return seen, total, peak_penetration, hand_hit, link7_hit, sorted(partners)

    def _lift_board_contact_diagnostics(self) -> tuple[bool, float]:
        """Contact state and force magnitude for the physical inclined board.

        These values are scene-audit / teacher-label metadata and intentionally
        do not enter the 32-D deployed ESN or MLP input.
        """
        seen, total, _, _, _, _ = self._board_contact_diagnostics(self._lift_board_geom_id)
        return seen, total

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
