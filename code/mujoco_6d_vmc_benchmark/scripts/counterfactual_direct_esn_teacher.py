"""Short-horizon privileged MuJoCo teacher for Direct-ESN DAgger.

This module is deliberately *training-only*.  It evaluates each candidate on
cloned MjData, then uses contact/impactor truth only to select an offline
label.  None of those quantities are part of the deployed Direct ESN input.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

import mujoco
import numpy as np

from run_benchmark import ARM_DOF, CONTROL_DT, TORQUE_LIMITS, body_jacobian, body_twist
from run_rod_perturbation_benchmark import rod_contact_diagnostics, rod_motion
from wbc_velocity_residual_core import (
    VelocityResidualActionFilter,
    safe_joint_velocity_command,
    safe_velocity_tracking_torque,
)
from wbc_velocity_residual_env import RL_DT

if TYPE_CHECKING:
    from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv


@dataclass(frozen=True)
class CounterfactualTeacherConfig:
    """Weights and candidate set for a one-action counterfactual rollout."""

    horizon_steps: int = 8
    contact_peak_weight: float = 0.80
    contact_impulse_weight: float = 0.60
    tracking_weight: float = 0.45
    torque_weight: float = 0.06
    action_weight: float = 0.004
    action_change_weight: float = 0.002
    secondary_contact_weight: float = 0.15
    tracking_reference_m: float = 0.012
    force_reference_n: float = 10.0
    impulse_reference_ns: float = 0.10
    activation_force_n: float = 0.20
    # Safety-side objectives (torque slew and uncommanded forward surge) so
    # the teacher's labels internalize all three headline metrics, not only
    # tracking accuracy and contact force.
    torque_rate_weight: float = 0.05
    torque_rate_reference_nmps: float = 300.0
    surge_weight: float = 0.10
    surge_reference_mps: float = 0.05

    def __post_init__(self) -> None:
        values = np.asarray(list(asdict(self).values()), dtype=float)
        if not np.all(np.isfinite(values)) or np.any(values <= 0.0):
            raise ValueError("counterfactual teacher parameters must be finite and positive")
        if self.horizon_steps < 2:
            raise ValueError("counterfactual teacher horizon must include at least two physics steps")


@dataclass(frozen=True)
class CounterfactualTeacherResult:
    """Offline label and diagnostics written to a DAgger archive."""

    action: np.ndarray
    cost: float
    candidate_costs: np.ndarray
    candidate_actions: np.ndarray
    predicted_peak_force_n: float
    predicted_impulse_ns: float
    predicted_terminal_error_m: float


def _normal_from_fixture_side(side: str) -> np.ndarray:
    if side == "negative_y":
        return np.array([0.0, -1.0, 0.0])
    if side == "positive_y":
        return np.array([0.0, 1.0, 0.0])
    raise ValueError(f"unsupported rod approach side {side!r}")


def candidate_actions(approach_normal: np.ndarray) -> np.ndarray:
    """Return neutral, slowdown, and outward-yield candidates.

    The normal is privileged fixture geometry and is intentionally only used
    here.  Keeping the candidates compact makes each DAgger sample affordable
    while preserving a meaningful action comparison under the real safety
    slew limits.
    """

    normal = np.asarray(approach_normal, dtype=float)
    if normal.shape != (3,) or not np.all(np.isfinite(normal)):
        raise ValueError("approach normal must be a finite three-vector")
    magnitude = float(np.linalg.norm(normal))
    if magnitude <= 1e-9:
        raise ValueError("approach normal must be nonzero")
    away = -normal / magnitude
    actions = [np.zeros(7, dtype=float), np.array([0.22, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])]
    for slowdown in (0.22, 0.45):
        for yield_strength in (0.20, 0.45, 0.75):
            actions.append(np.concatenate(([slowdown], yield_strength * away, np.zeros(3))))
    return np.asarray(actions, dtype=float)


def _filtered_action(env: "PandaWBCVelocityResidualEnv", action: np.ndarray):
    """Apply the same action envelope as deployment without mutating env."""

    action_filter = VelocityResidualActionFilter(env.safety_config)
    action_filter.wbc_scale = float(env.action_filter.wbc_scale)
    action_filter.cartesian_yield_twist = env.action_filter.cartesian_yield_twist.copy()
    return action_filter.filter(action, RL_DT)


def _command_for_clone(env: "PandaWBCVelocityResidualEnv", clone: mujoco.MjData, time_s: float):
    assert env.reference is not None and env.fixed_wbc is not None
    position, rotation, linear, angular = env.reference.sample(time_s)
    # Direct ESN always uses the fixed, unmodulated WBC feedback scale.
    return env.fixed_wbc.command(clone, position, rotation, np.concatenate((linear, angular)), feedback_scale=1.0)


def _rollout_candidate(
    env: "PandaWBCVelocityResidualEnv",
    action: np.ndarray,
    time_s: float,
    previous_action: np.ndarray,
    config: CounterfactualTeacherConfig,
) -> dict[str, float]:
    """Evaluate one constant 40-ms policy action from a copied state."""

    assert env.model is not None and env.data is not None and env.reference is not None
    model = env.model
    clone = mujoco.MjData(model)
    mujoco.mj_copyData(clone, model, env.data)
    applied_action = _filtered_action(env, action)
    previous_qdot = env.previous_joint_velocity_command.copy()
    previous_torque = env.previous_torque.copy()
    peak_force = 0.0
    impulse = 0.0
    peak_torque_ratio = 0.0
    peak_torque_rate = 0.0
    peak_surge = 0.0
    previous_twist = body_twist(model, clone, env._hand_id)
    secondary_contacts = 0
    for step in range(config.horizon_steps):
        current_time = time_s + step * CONTROL_DT
        command = _command_for_clone(env, clone, current_time)
        jacobian = body_jacobian(model, clone, env._hand_id)
        qdot_command, _ = safe_joint_velocity_command(
            command.joint_velocity_radps, jacobian, applied_action, previous_qdot, CONTROL_DT, env.safety_config,
        )
        torque, _ = safe_velocity_tracking_torque(
            clone.qfrc_bias[:ARM_DOF].copy(), clone.qvel[:ARM_DOF].copy(), qdot_command,
            previous_torque, CONTROL_DT, env.safety_config,
        )
        rod_displacement, _ = (
            rod_motion(current_time, env.fixture.rod_stroke_m, env.fixture.rod_start_time_s)
            if env.rod_enabled else (0.0, 0.0)
        )
        clone.mocap_pos[env._obstacle_mocap] = np.array([3.0, 3.0, 3.0])
        clone.mocap_quat[env._obstacle_mocap] = np.array([1.0, 0.0, 0.0, 0.0])
        clone.qfrc_applied[:] = 0.0
        clone.ctrl[:ARM_DOF] = torque
        clone.ctrl[ARM_DOF] = env.reference.gripper_target(current_time - (env.fixture.grasp_time_s - 2.10))
        clone.ctrl[env._rod_ctrl] = rod_displacement
        mujoco.mj_step(model, clone)
        _, force, _ = rod_contact_diagnostics(model, clone, env._rod_geom_id, env._hand_geom_id)
        peak_force = max(peak_force, force)
        impulse += force * CONTROL_DT
        peak_torque_ratio = max(peak_torque_ratio, float(np.max(np.abs(torque) / TORQUE_LIMITS)))
        peak_torque_rate = max(peak_torque_rate, float(np.max(np.abs(torque - previous_torque)) / CONTROL_DT))
        current_twist = body_twist(model, clone, env._hand_id)
        nominal_speed = float(np.linalg.norm(command.task_twist_world[:3]))
        if nominal_speed > 1.0e-9:
            direction = command.task_twist_world[:3] / nominal_speed
            surge = float(np.dot(current_twist[:3], direction)) - nominal_speed
            peak_surge = max(peak_surge, max(0.0, surge))
        previous_twist = current_twist
        # The rod itself is expected. Any other collision involving the Panda
        # indicates a candidate that exits the intended safe interaction.
        for index in range(clone.ncon):
            contact = clone.contact[index]
            geoms = {contact.geom1, contact.geom2}
            if env._hand_geom_id in geoms and env._rod_geom_id not in geoms:
                secondary_contacts += 1
        previous_qdot = qdot_command
        previous_torque = torque
    terminal_command = _command_for_clone(env, clone, time_s + config.horizon_steps * CONTROL_DT)
    terminal_error = float(np.linalg.norm(terminal_command.target_position_m - clone.xpos[env._hand_id]))
    action_delta = np.asarray(action, dtype=float) - np.asarray(previous_action, dtype=float)
    cost = (
        config.contact_peak_weight * (peak_force / config.force_reference_n) ** 2
        + config.contact_impulse_weight * (impulse / config.impulse_reference_ns) ** 2
        + config.tracking_weight * (terminal_error / config.tracking_reference_m) ** 2
        + config.torque_weight * peak_torque_ratio**2
        + config.action_weight * float(np.mean(np.asarray(action, dtype=float) ** 2))
        + config.action_change_weight * float(np.mean(action_delta**2))
        + config.secondary_contact_weight * secondary_contacts
        + config.torque_rate_weight * (peak_torque_rate / config.torque_rate_reference_nmps) ** 2
        + config.surge_weight * (peak_surge / config.surge_reference_mps) ** 2
    )
    return {
        "cost": float(cost),
        "peak_force_n": float(peak_force),
        "impulse_ns": float(impulse),
        "terminal_error_m": terminal_error,
        "peak_torque_rate_nmps": float(peak_torque_rate),
        "peak_surge_mps": float(peak_surge),
    }


def select_counterfactual_action(
    env: "PandaWBCVelocityResidualEnv",
    time_s: float,
    previous_action: np.ndarray,
    config: CounterfactualTeacherConfig | None = None,
) -> CounterfactualTeacherResult:
    """Select the minimum-cost privileged label without changing the live env."""

    teacher_config = config or CounterfactualTeacherConfig()
    zero_action = np.zeros(7, dtype=float)
    zero_result = _rollout_candidate(env, zero_action, time_s, previous_action, teacher_config)
    # Nominal neutrality is a hard teacher-side property.  The deployed ESN
    # never sees rod existence: this only prevents offline labels from turning
    # ordinary WBC tracking error into a residual-control target.  During or
    # immediately before a real collision, the zero-action rollout predicts a
    # nontrivial contact force and enables outward-yield alternatives.
    if not env.rod_enabled or zero_result["peak_force_n"] < teacher_config.activation_force_n:
        return CounterfactualTeacherResult(
            action=zero_action,
            cost=float(zero_result["cost"]),
            candidate_costs=np.asarray([zero_result["cost"]], dtype=float),
            candidate_actions=np.asarray([zero_action]),
            predicted_peak_force_n=float(zero_result["peak_force_n"]),
            predicted_impulse_ns=float(zero_result["impulse_ns"]),
            predicted_terminal_error_m=float(zero_result["terminal_error_m"]),
        )
    actions = candidate_actions(_normal_from_fixture_side(env.fixture.rod_approach_side))
    results = [zero_result, *[
        _rollout_candidate(env, action, time_s, previous_action, teacher_config) for action in actions[1:]
    ]]
    costs = np.asarray([item["cost"] for item in results], dtype=float)
    chosen = int(np.argmin(costs))
    return CounterfactualTeacherResult(
        action=actions[chosen].copy(),
        cost=float(costs[chosen]),
        candidate_costs=costs,
        candidate_actions=actions,
        predicted_peak_force_n=float(results[chosen]["peak_force_n"]),
        predicted_impulse_ns=float(results[chosen]["impulse_ns"]),
        predicted_terminal_error_m=float(results[chosen]["terminal_error_m"]),
    )
