#!/usr/bin/env python3
"""Run a physical approach-impact-recovery-grasp VMC benchmark.

This is intentionally a manipulation scene rather than the earlier free-space
reaching fixture: Panda descends toward a block on a table, a finite-mass ball
strikes its *open hand during the approach*, VMC yields and re-joins the
nominal approach, then Panda physically closes its parallel gripper and lifts
the block.  The impactor is a dynamic constrained body with an initial launch
velocity; it is never teleported through the robot.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import imageio.v3 as iio
import mujoco
import numpy as np

from run_benchmark import (
    ARM_DOF,
    CONTROL_DT,
    EPS,
    RENDER_FPS,
    SIM_TIME_S,
    TORQUE_LIMITS,
    SixDVirtualCarriage,
    VMCConfig,
    _safe_scalar,
    _torque_actuated_xml,
    body_jacobian,
    body_twist,
    rate_limit_torque,
    so3_log,
    torque_feasible_scale,
)


GRASP_TIME_S = 2.10
LIFT_COMPLETE_TIME_S = 4.10
# This is deliberately before GRASP_TIME_S: the manipulation task is recovery
# from a perturbation while reaching, followed by successful physical grasp.
IMPACT_TIME_S = 1.35
TABLE_TOP_Z = 0.400
TARGET_START_Z = 0.445
DEFAULT_CONTACT_TIME_CONSTANT_S = 0.025


def smoothstep(phase: float) -> tuple[float, float]:
    """Cubic blend and derivative with respect to normalized phase."""

    clipped = float(np.clip(phase, 0.0, 1.0))
    return 3.0 * clipped**2 - 2.0 * clipped**3, 6.0 * clipped - 6.0 * clipped**2


class PickLiftCarryReference:
    """Reachable pick--lift--carry arm reference, evaluated by forward kinematics."""

    def __init__(self, model: mujoco.MjModel, data: mujoco.MjData, hand_id: int) -> None:
        self.model = model
        self.hand_id = hand_id
        self.times = np.array([0.0, 1.70, 2.70, LIFT_COMPLETE_TIME_S, 6.20])
        home = data.qpos[:ARM_DOF].copy()
        pregrasp = home.copy()
        pregrasp[3] = -1.80  # fingertips straddle the tabletop block
        lifted = home.copy()
        lifted[3] = -1.42
        carry = lifted.copy()
        carry[0] = 0.18
        carry[1] = -0.10
        self.q_knots = np.stack([home, pregrasp, pregrasp, lifted, carry])
        self._work = mujoco.MjData(model)
        self._work.qpos[:] = data.qpos
        self._work.qvel[:] = 0.0

    def _joint_sample(self, time_s: float) -> tuple[np.ndarray, np.ndarray]:
        segment = int(np.searchsorted(self.times, time_s, side="right") - 1)
        segment = int(np.clip(segment, 0, len(self.times) - 2))
        t0, t1 = self.times[segment], self.times[segment + 1]
        phase = (time_s - t0) / (t1 - t0)
        blend, derivative = smoothstep(phase)
        delta = self.q_knots[segment + 1] - self.q_knots[segment]
        q = self.q_knots[segment] + blend * delta
        qdot = derivative * delta / (t1 - t0) if t0 <= time_s < t1 else np.zeros(ARM_DOF)
        return q, qdot

    def sample(self, time_s: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        q, qdot = self._joint_sample(time_s)
        self._work.qpos[:ARM_DOF] = q
        self._work.qvel[:ARM_DOF] = qdot
        mujoco.mj_forward(self.model, self._work)
        pose = self._work.xpos[self.hand_id].copy()
        rotation = self._work.xmat[self.hand_id].reshape(3, 3).copy()
        twist = body_twist(self.model, self._work, self.hand_id)
        return pose, rotation, twist[:3], twist[3:]

    @staticmethod
    def gripper_target(time_s: float) -> float:
        """Open during approach, close smoothly around the physical block."""

        if time_s <= GRASP_TIME_S:
            return 0.040
        close_phase, _ = smoothstep((time_s - GRASP_TIME_S) / 0.55)
        return float(0.040 * (1.0 - close_phase))


def _grasp_scene_xml(menagerie: Path, contact_time_constant_s: float) -> str:
    """Extend the official Panda model with table, free block and rail impactor."""

    text = _torque_actuated_xml(menagerie, contact_time_constant_s)
    # Keep the seven torque motors and add a physical tendon-position actuator
    # for Panda's existing coupled parallel gripper.  A zero target closes it;
    # the block remains a free body supported by contact/friction, not a weld.
    original = "</actuator>\n\n  <keyframe>"
    gripper = (
        '<position name="gripper" tendon="split" kp="250" '
        'ctrllimited="true" ctrlrange="0 0.04" forcelimited="true" forcerange="-100 100"/>\n'
    )
    if original not in text:
        raise RuntimeError("could not add the physical gripper actuator")
    text = text.replace(original, gripper + original, 1)
    # The old free-space mocap obstacle is retained by the shared transformer
    # but placed offstage in the episode.  The new impactor has a slide joint:
    # it receives a launch velocity once and then evolves by contact dynamics.
    injected = f"""
      <camera name="grasp_track" pos="1.20 -1.55 0.95"
        xyaxes="0.79 0.61 0  -0.17 0.22 0.96"/>
      <geom name="table" type="box" pos="0.54 0 0.38" size="0.20 0.20 0.02"
        contype="2" conaffinity="2" rgba="0.31 0.22 0.13 1" friction="1.2 0.02 0.002"/>
      <body name="target_object" pos="0.54 0 {TARGET_START_Z:.3f}">
        <freejoint name="target_freejoint"/>
        <geom name="target_object_geom" type="box" size="0.025 0.025 0.025" mass="0.08"
          contype="6" conaffinity="7" rgba="0.96 0.65 0.10 1" friction="1.5 0.02 0.002"
          solref="{contact_time_constant_s:.5f} 1" solimp="0.85 0.95 0.002 0.5 2"/>
      </body>
      <body name="rail_impactor" pos="0.55 -0.34 0.540">
        <inertial pos="0 0 0" mass="0.16" diaginertia="0.00012 0.00012 0.00012"/>
        <joint name="impactor_slide" type="slide" axis="0 1 0" range="0 0.72" damping="0.05" frictionloss="0.01"/>
        <geom name="impactor_geom" type="sphere" size="0.035" mass="0" contype="8" conaffinity="6"
          rgba="0.86 0.10 0.10 1" friction="0.9 0.02 0.002"
          solref="{contact_time_constant_s:.5f} 1" solimp="0.85 0.95 0.002 0.5 2"/>
      </body>
      <geom name="rail_visual" type="box" pos="0.54 0.02 0.405" size="0.055 0.38 0.008"
        contype="0" conaffinity="0" rgba="0.15 0.16 0.18 0.72"/>
    """
    text = text.replace("  </worldbody>", injected + "  </worldbody>", 1)
    return text


def make_grasp_model(menagerie: Path, contact_time_constant_s: float) -> tuple[mujoco.MjModel, mujoco.MjData]:
    xml = _grasp_scene_xml(menagerie, contact_time_constant_s)
    assets_dir = menagerie / "franka_emika_panda" / "assets"
    assets = {str(path.relative_to(assets_dir)): path.read_bytes() for path in assets_dir.rglob("*") if path.is_file()}
    model = mujoco.MjModel.from_xml_string(xml, assets=assets)
    model.opt.timestep = CONTROL_DT
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)
    return model, data


def contact_summary(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    impactor_geom_id: int,
    hand_geom_id: int,
    target_geom_id: int,
) -> tuple[bool, bool, bool, float, float]:
    """Return impact, impact-to-hand, impact-to-target, force and penetration."""

    impact_contact = False
    impact_hand_contact = False
    impact_target_contact = False
    peak_force = 0.0
    peak_penetration = 0.0
    wrench = np.zeros(6)
    for index in range(data.ncon):
        contact = data.contact[index]
        ids = {contact.geom1, contact.geom2}
        if impactor_geom_id not in ids:
            continue
        impact_contact = True
        impact_hand_contact = impact_hand_contact or hand_geom_id in ids
        impact_target_contact = impact_target_contact or target_geom_id in ids
        mujoco.mj_contactForce(model, data, index, wrench)
        peak_force = max(peak_force, float(np.linalg.norm(wrench[:3])))
        peak_penetration = max(peak_penetration, max(0.0, -float(contact.dist)))
    return impact_contact, impact_hand_contact, impact_target_contact, peak_force, peak_penetration


def run_episode(
    menagerie: Path,
    kappa: float,
    output_dir: Path,
    render_gif: bool,
    config: VMCConfig,
    impact_enabled: bool,
    impact_speed_mps: float,
    contact_time_constant_s: float,
) -> dict[str, Any]:
    model, data = make_grasp_model(menagerie, contact_time_constant_s)
    object_ids = {
        "hand": (mujoco.mjtObj.mjOBJ_BODY, "hand"),
        "hand_geom": (mujoco.mjtObj.mjOBJ_GEOM, "hand_collision"),
        "target_body": (mujoco.mjtObj.mjOBJ_BODY, "target_object"),
        "target_geom": (mujoco.mjtObj.mjOBJ_GEOM, "target_object_geom"),
        "impactor_geom": (mujoco.mjtObj.mjOBJ_GEOM, "impactor_geom"),
        "impactor_joint": (mujoco.mjtObj.mjOBJ_JOINT, "impactor_slide"),
        "target_freejoint": (mujoco.mjtObj.mjOBJ_JOINT, "target_freejoint"),
        "moving_obstacle": (mujoco.mjtObj.mjOBJ_BODY, "moving_obstacle"),
        "virtual_carriage": (mujoco.mjtObj.mjOBJ_BODY, "virtual_carriage"),
    }
    ids = {label: mujoco.mj_name2id(model, obj, name) for label, (obj, name) in object_ids.items()}
    if min(ids.values()) < 0:
        raise RuntimeError("grasp scene IDs were not resolved")
    impactor_dof = model.jnt_dofadr[ids["impactor_joint"]]
    target_qpos = model.jnt_qposadr[ids["target_freejoint"]]
    obstacle_mocap = model.body_mocapid[ids["moving_obstacle"]]
    carriage_mocap = model.body_mocapid[ids["virtual_carriage"]]
    # Free joints are reset to their qpos state rather than their XML body
    # offset.  Seed the target explicitly on the table before the first
    # forward pass, otherwise it starts at the world origin and falls through
    # the scene before the gripper arrives.
    data.qpos[target_qpos:target_qpos + 7] = [0.54, 0.0, TARGET_START_Z, 1.0, 0.0, 0.0, 0.0]
    data.qvel[model.jnt_dofadr[ids["target_freejoint"]]:model.jnt_dofadr[ids["target_freejoint"]] + 6] = 0.0
    mujoco.mj_forward(model, data)

    hand_position = data.xpos[ids["hand"]].copy()
    hand_rotation = data.xmat[ids["hand"]].reshape(3, 3).copy()
    reference = PickLiftCarryReference(model, data, ids["hand"])
    controller = SixDVirtualCarriage(config, kappa, hand_position, hand_rotation)

    renderer: mujoco.Renderer | None = mujoco.Renderer(model, height=480, width=640) if render_gif else None
    frames: list[np.ndarray] = []
    render_stride = max(1, round(1.0 / (RENDER_FPS * CONTROL_DT)))
    log: dict[str, list[Any]] = {key: [] for key in (
        "time", "track_position", "track_orientation", "ee_speed", "surge", "acceleration", "jerk",
        "torque_applied", "torque_ratio", "impact_contact", "impact_hand_contact", "impact_target_contact", "impact_force",
        "impact_penetration", "object_position", "object_hand_distance", "gripper_target",
    )}
    previous_twist = np.zeros(6)
    previous_acceleration = np.zeros(6)
    previous_torque = data.qfrc_bias[:ARM_DOF].copy()
    launched = False
    impact_observed = False
    impact_hand_observed = False
    impact_target_observed = False
    steps = int(SIM_TIME_S / CONTROL_DT)

    for step in range(steps):
        time_s = step * CONTROL_DT
        nominal_position, nominal_rotation, nominal_linear, nominal_angular = reference.sample(time_s)
        nominal_twist = np.concatenate([nominal_linear, nominal_angular])
        # Prevent the legacy mocap diagnostic ball from entering this scene.
        data.mocap_pos[obstacle_mocap] = np.array([3.0, 3.0, 3.0])
        data.mocap_pos[carriage_mocap] = controller.position
        data.mocap_quat[obstacle_mocap] = np.array([1.0, 0.0, 0.0, 0.0])
        data.mocap_quat[carriage_mocap] = np.array([1.0, 0.0, 0.0, 0.0])
        if impact_enabled and not launched and time_s >= IMPACT_TIME_S:
            data.qvel[impactor_dof] = impact_speed_mps
            launched = True

        ee_position = data.xpos[ids["hand"]].copy()
        ee_rotation = data.xmat[ids["hand"]].reshape(3, 3).copy()
        ee_twist = body_twist(model, data, ids["hand"])
        wrench, _ = controller.wrench(ee_position, ee_rotation, ee_twist)
        wrench_torque = body_jacobian(model, data, ids["hand"]).T @ wrench
        bias = data.qfrc_bias[:ARM_DOF].copy()
        scale = torque_feasible_scale(bias, wrench_torque)
        desired_torque = bias + scale * wrench_torque
        applied_torque = np.clip(
            rate_limit_torque(previous_torque, desired_torque, CONTROL_DT, config),
            -TORQUE_LIMITS,
            TORQUE_LIMITS,
        )
        data.ctrl[:ARM_DOF] = applied_torque
        data.ctrl[ARM_DOF] = reference.gripper_target(time_s)
        controller.advance(CONTROL_DT, nominal_position, nominal_rotation, nominal_twist, wrench)
        mujoco.mj_step(model, data)

        impact_contact, impact_hand, impact_target, force, penetration = contact_summary(
            model, data, ids["impactor_geom"], ids["hand_geom"], ids["target_geom"]
        )
        impact_observed = impact_observed or impact_contact
        impact_hand_observed = impact_hand_observed or impact_hand
        impact_target_observed = impact_target_observed or impact_target
        acceleration = (ee_twist - previous_twist) / CONTROL_DT
        jerk = (acceleration - previous_acceleration) / CONTROL_DT
        direction = nominal_linear / (np.linalg.norm(nominal_linear) + EPS)
        surge = max(0.0, float(np.dot(ee_twist[:3], direction) - np.linalg.norm(nominal_linear)))
        target_position = data.xpos[ids["target_body"]].copy()

        for key, value in {
            "time": time_s,
            "track_position": float(np.linalg.norm(ee_position - nominal_position)),
            "track_orientation": float(np.linalg.norm(so3_log(nominal_rotation @ ee_rotation.T))),
            "ee_speed": float(np.linalg.norm(ee_twist[:3])),
            "surge": surge,
            "acceleration": float(np.linalg.norm(acceleration[:3])),
            "jerk": float(np.linalg.norm(jerk[:3])),
            "torque_applied": applied_torque.tolist(),
            "torque_ratio": float(np.max(np.abs(applied_torque) / TORQUE_LIMITS)),
            "impact_contact": impact_contact,
            "impact_hand_contact": impact_hand,
            "impact_target_contact": impact_target,
            "impact_force": force,
            "impact_penetration": penetration,
            "object_position": target_position.tolist(),
            "object_hand_distance": float(np.linalg.norm(target_position - ee_position)),
            "gripper_target": reference.gripper_target(time_s),
        }.items():
            log[key].append(value)
        previous_twist = ee_twist
        previous_acceleration = acceleration
        previous_torque = applied_torque
        if renderer is not None and step % render_stride == 0:
            renderer.update_scene(data, camera="grasp_track")
            frames.append(renderer.render().copy())

    if renderer is not None:
        renderer.close()
        gif_path = output_dir / f"grasp_impact_kappa_{kappa:.2f}.gif"
        iio.imwrite(gif_path, np.stack(frames), duration=1.0 / RENDER_FPS, loop=0)
    else:
        gif_path = None
    arrays = {key: np.asarray(values) for key, values in log.items()}
    approach_recovery_mask = (arrays["time"] >= IMPACT_TIME_S) & (arrays["time"] < GRASP_TIME_S)
    object_position = arrays["object_position"]
    target_lifted = bool(np.max(object_position[:, 2]) > TABLE_TOP_Z + 0.12)
    final_object_held = bool(
        object_position[-1, 2] > TABLE_TOP_Z + 0.08 and arrays["object_hand_distance"][-1] < 0.16
    )
    impact_mask = arrays["impact_contact"].astype(bool)
    summary = {
        "kappa": kappa,
        "config": asdict(config),
        "scenario": "physical tabletop approach-impact-recovery-grasp; rail-launched finite-mass impactor",
        "reference": "deterministic fixed end-effector proxy; replace with fixed WBC pose/twist for WBC+VMC evaluation",
        "grasp_time_s": GRASP_TIME_S,
        "impact_time_s": IMPACT_TIME_S if impact_enabled else None,
        "impact_enabled": impact_enabled,
        "impact_speed_mps": impact_speed_mps if impact_enabled else 0.0,
        "contact_time_constant_s": contact_time_constant_s,
        "task_validity": {
            "physical_gripper_actuated": True,
            "target_lifted": target_lifted,
            "target_held_at_end": final_object_held,
            "impactor_contact_observed": impact_observed,
            "impactor_hand_contact_observed": impact_hand_observed,
            "impactor_target_contact_observed": impact_target_observed,
            "max_impactor_penetration_m": _safe_scalar(np.max(arrays["impact_penetration"])),
        },
        "tracking": {
            "approach_recovery_position_rmse_m": _safe_scalar(np.sqrt(np.mean(arrays["track_position"][approach_recovery_mask] ** 2))),
            "pregrasp_position_error_m": _safe_scalar(arrays["track_position"][np.flatnonzero(arrays["time"] < GRASP_TIME_S)[-1]]),
            "final_position_error_m": _safe_scalar(arrays["track_position"][-1]),
            "approach_recovery_orientation_rmse_rad": _safe_scalar(np.sqrt(np.mean(arrays["track_orientation"][approach_recovery_mask] ** 2))),
        },
        "motion": {
            "approach_recovery_speed_p95_mps": _safe_scalar(np.quantile(arrays["ee_speed"][approach_recovery_mask], 0.95)),
            "forward_surge_max_mps": _safe_scalar(np.max(arrays["surge"][approach_recovery_mask])),
            "acceleration_peak_mps2": _safe_scalar(np.max(arrays["acceleration"][approach_recovery_mask])),
            "jerk_peak_mps3": _safe_scalar(np.max(arrays["jerk"][approach_recovery_mask])),
        },
        "torque": {
            "applied_peak_nm": _safe_scalar(np.max(np.abs(arrays["torque_applied"]))),
            "applied_peak_ratio": _safe_scalar(np.max(arrays["torque_ratio"])),
            "hard_limit_fraction": _safe_scalar(np.mean(np.isclose(np.abs(arrays["torque_applied"]), TORQUE_LIMITS[None, :], atol=1e-5))),
        },
        "impact_diagnostics": {
            "duration_s": _safe_scalar(np.sum(impact_mask) * CONTROL_DT),
            "peak_force_n": _safe_scalar(np.max(arrays["impact_force"])),
            "impulse_ns": _safe_scalar(np.sum(arrays["impact_force"]) * CONTROL_DT),
            "max_penetration_m": _safe_scalar(np.max(arrays["impact_penetration"])),
        },
        "gif": str(gif_path) if gif_path else None,
    }
    np.savez_compressed(output_dir / f"grasp_impact_kappa_{kappa:.2f}_trace.npz", **arrays)
    (output_dir / f"grasp_impact_kappa_{kappa:.2f}_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--kappas", type=float, nargs="+", default=[1.0])
    parser.add_argument("--damping-ratio", type=float, default=1.8)
    parser.add_argument("--carriage-drive-scale", type=float, default=0.75)
    parser.add_argument("--carriage-drive-damping-ratio", type=float, default=2.0)
    parser.add_argument("--contact-time-constant", type=float, default=DEFAULT_CONTACT_TIME_CONSTANT_S)
    parser.add_argument("--impact-speed", type=float, default=1.10)
    parser.add_argument("--disable-impact", action="store_true")
    parser.add_argument("--render-gif", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if min(args.damping_ratio, args.carriage_drive_scale, args.carriage_drive_damping_ratio, args.contact_time_constant, args.impact_speed) <= 0:
        raise ValueError("positive scales, contact time constant and impact speed are required")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    config = replace(
        VMCConfig(),
        zeta=args.damping_ratio,
        carriage_drive_k_translation=VMCConfig().carriage_drive_k_translation * args.carriage_drive_scale,
        carriage_drive_k_rotation=VMCConfig().carriage_drive_k_rotation * args.carriage_drive_scale,
        carriage_drive_zeta=args.carriage_drive_damping_ratio,
    )
    runs = [
        run_episode(
            args.menagerie, kappa, args.output_dir, args.render_gif, config,
            impact_enabled=not args.disable_impact, impact_speed_mps=args.impact_speed,
            contact_time_constant_s=args.contact_time_constant,
        )
        for kappa in args.kappas
    ]
    matrix = {"protocol": vars(args) | {"menagerie": str(args.menagerie), "output_dir": str(args.output_dir)}, "runs": runs}
    matrix["protocol"].pop("menagerie")
    matrix["protocol"].pop("output_dir")
    (args.output_dir / "evaluation_matrix.json").write_text(json.dumps(matrix, indent=2) + "\n")
    print(json.dumps(matrix, indent=2))


if __name__ == "__main__":
    os.environ.setdefault("MUJOCO_GL", "egl")
    main()
