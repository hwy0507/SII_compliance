#!/usr/bin/env python3
"""Benchmark six-spring compliant recovery after a physical rod perturbation.

Panda follows a nominal tabletop grasp approach.  While the gripper is still
open, a finite-mass cylindrical rod, position-driven through a physical slide
joint, presses across the hand. The end effector departs from its moving
nominal trajectory tube, the six virtual springs and virtual carriage generate
a bounded restoring wrench, the hand re-joins the nominal tube, and the
gripper then completes a physical grasp and lift.

The finite grasp trajectory is a moving attractor/trajectory tube, *not* a
mathematical limit cycle.  A strict limit-cycle study should instead supply a
periodic nominal pose with a phase variable; this benchmark exposes the same
six-dimensional departure-and-return mechanism for the user task.
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
from run_grasp_impact_benchmark import (
    GRASP_TIME_S,
    LIFT_COMPLETE_TIME_S,
    TABLE_TOP_Z,
    TARGET_START_Z,
    PickLiftCarryReference,
    smoothstep,
)


ROD_START_TIME_S = 1.08
ROD_PEAK_TIME_S = 1.28
ROD_RETRACT_TIME_S = 1.52
ROD_END_TIME_S = 1.72
DEFAULT_CONTACT_TIME_CONSTANT_S = 0.015
PATH_MARKER_COUNT = 13
ACTUAL_TRAIL_COUNT = 12
CAMERA_VIEWS = ("overview", "hand-closeup")


def rod_motion(
    time_s: float,
    stroke_m: float,
    start_time_s: float = ROD_START_TIME_S,
    cycles: int = 1,
    cycle_period_s: float = 0.80,
) -> tuple[float, float]:
    """One or more physical rod press--hold--retract pulses on a slide joint."""

    profile_duration = ROD_END_TIME_S - ROD_START_TIME_S
    if cycles < 1 or cycle_period_s < profile_duration:
        raise ValueError("rod cycles must be positive and spaced by one complete rod profile")
    elapsed = time_s - start_time_s
    cycle_index = int(np.floor(elapsed / cycle_period_s)) if elapsed >= 0.0 else -1
    if cycle_index < 0 or cycle_index >= cycles:
        return 0.0, 0.0
    local_time = ROD_START_TIME_S + elapsed - cycle_index * cycle_period_s
    if local_time <= ROD_START_TIME_S or local_time >= ROD_END_TIME_S:
        return 0.0, 0.0
    if local_time < ROD_PEAK_TIME_S:
        blend, derivative = smoothstep((local_time - ROD_START_TIME_S) / (ROD_PEAK_TIME_S - ROD_START_TIME_S))
        displacement = stroke_m * blend
        velocity = stroke_m * derivative / (ROD_PEAK_TIME_S - ROD_START_TIME_S)
        return float(displacement), float(velocity)
    if local_time <= ROD_RETRACT_TIME_S:
        return stroke_m, 0.0
    blend, derivative = smoothstep((local_time - ROD_RETRACT_TIME_S) / (ROD_END_TIME_S - ROD_RETRACT_TIME_S))
    displacement = stroke_m * (1.0 - blend)
    velocity = -stroke_m * derivative / (ROD_END_TIME_S - ROD_RETRACT_TIME_S)
    return float(displacement), float(velocity)


def stiffness_schedule(
    time_s: float,
    contact_kappa: float,
    recovery_kappa: float,
    recovery_ramp_s: float,
) -> float:
    """One scalar for all six springs: low while yielding, high after release."""

    if contact_kappa <= 0.0 or recovery_kappa <= 0.0 or recovery_ramp_s < 0.0:
        raise ValueError("stiffness schedule arguments must be positive")
    if time_s <= ROD_END_TIME_S:
        return float(contact_kappa)
    if recovery_ramp_s == 0.0 or time_s >= ROD_END_TIME_S + recovery_ramp_s:
        return float(recovery_kappa)
    blend, _ = smoothstep((time_s - ROD_END_TIME_S) / recovery_ramp_s)
    return float((1.0 - blend) * contact_kappa + blend * recovery_kappa)


def _rod_scene_xml(
    menagerie: Path,
    contact_time_constant_s: float,
    rod_height_m: float = 0.540,
    explicit_translational_carriage: bool = False,
    carriage_mass_kg: float = 0.35,
    explicit_rotational_carriage: bool = False,
    rotational_carriage_inertia_scale: float = 1.0,
) -> str:
    """Official Panda plus physical table/block and a dynamic slide-mounted rod."""

    text = _torque_actuated_xml(menagerie, contact_time_constant_s)
    anchor = "</actuator>\n\n  <keyframe>"
    gripper = (
        '<position name="gripper" tendon="split" kp="250" '
        'ctrllimited="true" ctrlrange="0 0.04" forcelimited="true" forcerange="-100 100"/>\n'
    )
    if anchor not in text:
        raise RuntimeError("could not add the physical gripper actuator")
    text = text.replace(anchor, gripper + anchor, 1)
    # The rod's cylinder axis is local z. Rotate it so its long axis is world
    # x, then slide it along world y into and back out of the hand. A position
    # actuator drives the support slide; the finite-mass rod/contact response
    # remains part of MuJoCo dynamics rather than a mocap teleport.
    explicit_carriage_xml = ""
    if explicit_translational_carriage:
        rotational_child_xml = ""
        if explicit_rotational_carriage:
            rotational_inertia = 0.08 * rotational_carriage_inertia_scale
            rotational_child_xml = f"""
        <!-- Ball joint supplies a physical, three-DoF rotational carriage state. -->
        <body name="explicit_rotation_carriage" pos="0 0 0" gravcomp="1">
          <joint name="explicit_carriage_ball" type="ball" damping="0.02"/>
          <inertial pos="0 0 0" mass="0.30" diaginertia="{rotational_inertia:.6g} {rotational_inertia:.6g} {rotational_inertia:.6g}"/>
          <geom type="sphere" size="0.013" contype="0" conaffinity="0" rgba="0.95 0.45 0.08 0.50"/>
        </body>
            """
        explicit_carriage_xml = f"""
      <!-- One physical 3D carriage: three orthogonal slide states share one mass. -->
      <body name="explicit_carriage" pos="0 0 0" gravcomp="1">
        <joint name="explicit_carriage_x_slide" type="slide" axis="1 0 0" damping="1.0"/>
        <joint name="explicit_carriage_y_slide" type="slide" axis="0 1 0" damping="1.0"/>
        <joint name="explicit_carriage_z_slide" type="slide" axis="0 0 1" damping="1.0"/>
        <inertial pos="0 0 0" mass="{carriage_mass_kg:.6g}" diaginertia="1e-6 1e-6 1e-6"/>
        <geom type="sphere" size="0.018" contype="0" conaffinity="0" rgba="0.05 0.85 0.95 0.45"/>
        {rotational_child_xml}
      </body>
      """
    injected = f"""
      <camera name="rod_track" pos="1.18 -1.42 0.86"
        xyaxes="0.79 0.61 0  -0.17 0.22 0.96"/>
      <geom name="table" type="box" pos="0.54 0 0.38" size="0.20 0.20 0.02"
        contype="2" conaffinity="2" rgba="0.31 0.22 0.13 1" friction="1.2 0.02 0.002"/>
      <body name="target_object" pos="0.54 0 {TARGET_START_Z:.3f}">
        <freejoint name="target_freejoint"/>
        <geom name="target_object_geom" type="box" size="0.025 0.025 0.025" mass="0.08"
          contype="6" conaffinity="7" rgba="0.96 0.65 0.10 1" friction="1.5 0.02 0.002"
          solref="{contact_time_constant_s:.5f} 1" solimp="0.85 0.95 0.002 0.5 2"/>
      </body>
      <body name="rod_support" pos="0.55 -0.20 {rod_height_m:.3f}">
        <joint name="rod_slide" type="slide" axis="0 1 0" range="0 0.20" damping="2.0"/>
        <geom name="rod_geom" type="cylinder" size="0.014 0.15" quat="0.7071068 0 0.7071068 0"
          mass="0.30" contype="8" conaffinity="4" rgba="0.18 0.70 0.25 1"
          friction="0.8 0.02 0.002" solref="{contact_time_constant_s:.5f} 1"
          solimp="0.85 0.95 0.002 0.5 2"/>
      </body>
      <body name="nominal_marker" mocap="true" pos="0 0 1">
        <geom type="sphere" size="0.025" contype="0" conaffinity="0" rgba="0.10 0.35 1.0 0.95"/>
      </body>
      <body name="actual_marker" mocap="true" pos="0 0 1">
        <geom type="sphere" size="0.024" contype="0" conaffinity="0" rgba="1.0 0.05 0.68 0.98"/>
      </body>
      {''.join(f'<body name="nominal_path_{index}" mocap="true" pos="0 0 1"><geom type="sphere" size="0.010" contype="0" conaffinity="0" rgba="0.22 0.52 1.0 0.62"/></body>' for index in range(PATH_MARKER_COUNT))}
      {''.join(f'<body name="actual_trail_{index}" mocap="true" pos="0 0 -2"><geom type="sphere" size="0.008" contype="0" conaffinity="0" rgba="1.0 0.10 0.62 {0.20 + 0.60 * (index + 1) / ACTUAL_TRAIL_COUNT:.3f}"/></body>' for index in range(ACTUAL_TRAIL_COUNT))}
      <geom name="rod_guide" type="box" pos="0.55 -0.10 0.435" size="0.18 0.13 0.008"
        contype="0" conaffinity="0" rgba="0.10 0.12 0.15 0.70"/>
      {explicit_carriage_xml}
    """
    text = text.replace("  </worldbody>", injected + "  </worldbody>", 1)
    rod_driver = (
        '<position name="rod_driver" joint="rod_slide" kp="5000" '
        'ctrllimited="true" ctrlrange="0 0.20" forcelimited="true" forcerange="-300 300"/>\n'
    )
    if anchor not in text:
        raise RuntimeError("could not add the physical rod driver actuator")
    text = text.replace(anchor, rod_driver + anchor, 1)
    return text


def make_rod_model(
    menagerie: Path,
    contact_time_constant_s: float,
    rod_height_m: float = 0.540,
    explicit_translational_carriage: bool = False,
    carriage_mass_kg: float = 0.35,
    explicit_rotational_carriage: bool = False,
    rotational_carriage_inertia_scale: float = 1.0,
) -> tuple[mujoco.MjModel, mujoco.MjData]:
    xml = _rod_scene_xml(
        menagerie, contact_time_constant_s, rod_height_m,
        explicit_translational_carriage, carriage_mass_kg,
        explicit_rotational_carriage, rotational_carriage_inertia_scale,
    )
    assets_dir = menagerie / "franka_emika_panda" / "assets"
    assets = {str(path.relative_to(assets_dir)): path.read_bytes() for path in assets_dir.rglob("*") if path.is_file()}
    model = mujoco.MjModel.from_xml_string(xml, assets=assets)
    model.opt.timestep = CONTROL_DT
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)
    return model, data


def rod_contact_diagnostics(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    rod_geom_id: int,
    hand_geom_id: int,
) -> tuple[bool, float, float]:
    touching_hand = False
    peak_force = 0.0
    peak_penetration = 0.0
    wrench = np.zeros(6)
    for index in range(data.ncon):
        contact = data.contact[index]
        if {contact.geom1, contact.geom2} != {rod_geom_id, hand_geom_id}:
            continue
        touching_hand = True
        mujoco.mj_contactForce(model, data, index, wrench)
        peak_force = max(peak_force, float(np.linalg.norm(wrench[:3])))
        peak_penetration = max(peak_penetration, max(0.0, -float(contact.dist)))
    return touching_hand, peak_force, peak_penetration


def _apply_body_force(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    body_id: int,
    force: np.ndarray,
) -> None:
    """Accumulate a world-frame point force at a body's origin into qfrc_applied."""
    generalized = np.zeros(model.nv, dtype=float)
    mujoco.mj_applyFT(
        model, data, np.asarray(force, dtype=float), np.zeros(3), data.xpos[body_id], body_id, generalized
    )
    data.qfrc_applied[:] += generalized


def _apply_body_torque(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    body_id: int,
    torque: np.ndarray,
) -> None:
    """Accumulate a world-frame pure torque at a body's origin."""
    generalized = np.zeros(model.nv, dtype=float)
    mujoco.mj_applyFT(
        model, data, np.zeros(3), np.asarray(torque, dtype=float), data.xpos[body_id], body_id, generalized
    )
    data.qfrc_applied[:] += generalized


def _saturated_translation_spring(
    stiffness: float,
    maximum_force: float,
    displacement: np.ndarray,
) -> np.ndarray:
    """Per-axis nonlinear force law matching the existing VMC saturation convention."""
    return maximum_force * np.tanh(stiffness * np.asarray(displacement, dtype=float) / maximum_force)


def _saturate_vector_norm(vector: np.ndarray, maximum_norm: float) -> np.ndarray:
    """Bound a vector norm while preserving direction."""
    vector = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(vector))
    if norm <= maximum_norm or norm <= EPS:
        return vector
    return vector * (maximum_norm / norm)


def _rotation_to_quaternion(rotation: np.ndarray) -> np.ndarray:
    """Convert a rotation matrix into MuJoCo's scalar-first quaternion."""
    quaternion = np.zeros(4, dtype=float)
    mujoco.mju_mat2Quat(quaternion, np.asarray(rotation, dtype=float).reshape(9))
    return quaternion


def make_render_camera(view: str, nominal_position: np.ndarray) -> str | mujoco.MjvCamera:
    """Return either the contextual scene camera or a hand-centred close-up.

    The close-up is a rendering-only free camera, locked to the nominal pose
    rather than the actual hand.  This preserves an externally induced hand
    departure in image space: an actual-hand-following camera would incorrectly
    hide exactly the 20--30 mm motion the benchmark intends to demonstrate.
    It never affects model state, contacts, controller inputs, or metrics.
    """

    if view == "overview":
        return "rod_track"
    if view != "hand-closeup":
        raise ValueError(f"unknown camera view: {view}")
    camera = mujoco.MjvCamera()
    mujoco.mjv_defaultCamera(camera)
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = nominal_position
    camera.distance = 0.44
    camera.azimuth = 142.0
    camera.elevation = -20.0
    return camera


def run_episode(
    menagerie: Path,
    kappa: float,
    output_dir: Path,
    render_gif: bool,
    config: VMCConfig,
    rod_stroke_m: float,
    contact_time_constant_s: float,
    rod_enabled: bool = True,
    playback_speed: float = 1.0,
    camera_view: str = "overview",
    render_start_time_s: float = 0.0,
    render_end_time_s: float = SIM_TIME_S,
    recovery_kappa: float | None = None,
    recovery_ramp_s: float = 0.16,
    recovery_drive_scale_factor: float = 1.0,
    grasp_time_s: float = GRASP_TIME_S,
    rod_start_time_s: float = ROD_START_TIME_S,
    rod_cycles: int = 1,
    rod_cycle_period_s: float = 0.80,
    response_only: bool = False,
    explicit_translational_carriage: bool = False,
    carriage_mass_kg: float = 0.35,
    rod_height_m: float = 0.540,
    explicit_rotational_carriage: bool = False,
    rotational_carriage_inertia_scale: float = 1.0,
    rotational_damping_ratio: float | None = None,
) -> dict[str, Any]:
    if explicit_rotational_carriage and not explicit_translational_carriage:
        raise ValueError("an explicit rotational carriage requires the explicit translational carriage parent")
    if rotational_carriage_inertia_scale <= 0.0 or (rotational_damping_ratio is not None and rotational_damping_ratio <= 0.0):
        raise ValueError("rotational carriage inertia scale must be positive")
    if not 0.0 <= render_start_time_s < render_end_time_s <= SIM_TIME_S:
        raise ValueError("render window must satisfy 0 <= start < end <= simulation time")
    recovery_kappa = kappa if recovery_kappa is None else recovery_kappa
    if recovery_kappa <= 0.0 or recovery_ramp_s < 0.0 or recovery_drive_scale_factor <= 0.0 or not ROD_END_TIME_S < grasp_time_s < LIFT_COMPLETE_TIME_S or rod_cycles < 1 or rod_cycle_period_s < ROD_END_TIME_S - ROD_START_TIME_S:
        raise ValueError("recovery stiffness and ramp must be non-negative / positive")
    # The default height intersects the descending hand.  In the repeated
    # response fixture the arm stays at the lower pre-grasp pose, so align the
    # same physical rod to that fixed interaction plane instead.
    model, data = make_rod_model(
        menagerie, contact_time_constant_s, 0.520 if response_only else rod_height_m,
        explicit_translational_carriage, carriage_mass_kg,
        explicit_rotational_carriage, rotational_carriage_inertia_scale,
    )
    objects = {
        "hand": (mujoco.mjtObj.mjOBJ_BODY, "hand"),
        "hand_geom": (mujoco.mjtObj.mjOBJ_GEOM, "hand_collision"),
        "target_body": (mujoco.mjtObj.mjOBJ_BODY, "target_object"),
        "target_freejoint": (mujoco.mjtObj.mjOBJ_JOINT, "target_freejoint"),
        "rod_geom": (mujoco.mjtObj.mjOBJ_GEOM, "rod_geom"),
        "rod_joint": (mujoco.mjtObj.mjOBJ_JOINT, "rod_slide"),
        "moving_obstacle": (mujoco.mjtObj.mjOBJ_BODY, "moving_obstacle"),
        "virtual_carriage": (mujoco.mjtObj.mjOBJ_BODY, "virtual_carriage"),
        "nominal_marker": (mujoco.mjtObj.mjOBJ_BODY, "nominal_marker"),
        "actual_marker": (mujoco.mjtObj.mjOBJ_BODY, "actual_marker"),
    }
    if explicit_translational_carriage:
        objects["explicit_carriage"] = (mujoco.mjtObj.mjOBJ_BODY, "explicit_carriage")
    if explicit_rotational_carriage:
        objects["explicit_rotation_carriage"] = (mujoco.mjtObj.mjOBJ_BODY, "explicit_rotation_carriage")
    ids = {label: mujoco.mj_name2id(model, obj, name) for label, (obj, name) in objects.items()}
    if min(ids.values()) < 0:
        raise RuntimeError("rod perturbation scene IDs were not resolved")
    target_qpos = model.jnt_qposadr[ids["target_freejoint"]]
    target_dof = model.jnt_dofadr[ids["target_freejoint"]]
    obstacle_mocap = model.body_mocapid[ids["moving_obstacle"]]
    carriage_mocap = model.body_mocapid[ids["virtual_carriage"]]
    nominal_marker_mocap = model.body_mocapid[ids["nominal_marker"]]
    actual_marker_mocap = model.body_mocapid[ids["actual_marker"]]
    explicit_carriage_body_id = ids["explicit_carriage"] if explicit_translational_carriage else -1
    explicit_rotation_carriage_body_id = ids["explicit_rotation_carriage"] if explicit_rotational_carriage else -1
    explicit_carriage_qpos_indices = np.array([
        model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"explicit_carriage_{axis}_slide")]
        for axis in "xyz"
    ], dtype=int) if explicit_translational_carriage else np.zeros(0, dtype=int)
    explicit_carriage_dof_indices = np.array([
        model.jnt_dofadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"explicit_carriage_{axis}_slide")]
        for axis in "xyz"
    ], dtype=int) if explicit_translational_carriage else np.zeros(0, dtype=int)
    explicit_rotation_qpos_indices = np.arange(
        model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "explicit_carriage_ball")],
        model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "explicit_carriage_ball")] + 4,
    ) if explicit_rotational_carriage else np.zeros(0, dtype=int)
    explicit_rotation_dof_indices = np.arange(
        model.jnt_dofadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "explicit_carriage_ball")],
        model.jnt_dofadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "explicit_carriage_ball")] + 3,
    ) if explicit_rotational_carriage else np.zeros(0, dtype=int)
    path_marker_mocaps = np.array([
        model.body_mocapid[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, f"nominal_path_{index}")]
        for index in range(PATH_MARKER_COUNT)
    ])
    actual_trail_mocaps = np.array([
        model.body_mocapid[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, f"actual_trail_{index}")]
        for index in range(ACTUAL_TRAIL_COUNT)
    ])
    if np.any(path_marker_mocaps < 0):
        raise RuntimeError("nominal trajectory marker mocap IDs were not resolved")
    if np.any(actual_trail_mocaps < 0):
        raise RuntimeError("actual end-effector trail mocap IDs were not resolved")
    rod_ctrl_index = ARM_DOF + 1
    if model.nu != rod_ctrl_index + 1:
        raise RuntimeError("expected seven torque motors, gripper, and rod driver")
    data.qpos[target_qpos:target_qpos + 7] = [0.54, 0.0, TARGET_START_Z, 1.0, 0.0, 0.0, 0.0]
    data.qvel[target_dof:target_dof + 6] = 0.0
    mujoco.mj_forward(model, data)

    reference = PickLiftCarryReference(model, data, ids["hand"])
    # The dotted blue curve makes the target moving trajectory visible in the
    # GIF; it is a visual aid only and never contributes collision/contact.
    for index, marker_mocap in enumerate(path_marker_mocaps):
        path_time = index * min(SIM_TIME_S, 6.20) / (PATH_MARKER_COUNT - 1)
        path_position, _, _, _ = reference.sample(path_time)
        data.mocap_pos[marker_mocap] = path_position
        data.mocap_quat[marker_mocap] = np.array([1.0, 0.0, 0.0, 0.0])
    controller = SixDVirtualCarriage(
        config, kappa, data.xpos[ids["hand"]].copy(), data.xmat[ids["hand"]].reshape(3, 3).copy()
    )
    renderer: mujoco.Renderer | None = mujoco.Renderer(model, height=480, width=640) if render_gif else None
    render_camera: str | mujoco.MjvCamera | None = None
    frames: list[np.ndarray] = []
    render_stride = max(1, round(1.0 / (RENDER_FPS * CONTROL_DT)))
    log: dict[str, list[Any]] = {key: [] for key in (
        "time", "track_position", "track_orientation", "ee_speed", "surge", "acceleration", "jerk",
        "torque_applied", "torque_ratio", "rod_contact", "rod_force", "rod_penetration",
        "carriage_displacement", "vmc_wrench", "ee_position", "nominal_position", "carriage_position",
        "object_position", "object_hand_distance", "rod_displacement", "rod_command_velocity", "active_kappa", "active_drive_scale",
        "explicit_carriage_position", "explicit_carriage_velocity", "explicit_carriage_force",
        "explicit_carriage_rotation", "explicit_carriage_angular_velocity", "explicit_carriage_moment",
        "simulation_finite",
    )}
    previous_twist = np.zeros(6)
    previous_acceleration = np.zeros(6)
    previous_torque = data.qfrc_bias[:ARM_DOF].copy()
    actual_position_history: list[np.ndarray] = []
    rod_hand_observed = False
    steps = int(SIM_TIME_S / CONTROL_DT)

    for step in range(steps):
        time_s = step * CONTROL_DT
        reference_time_s = 1.70 if response_only else time_s
        nominal_position, nominal_rotation, nominal_linear, nominal_angular = reference.sample(reference_time_s)
        nominal_twist = np.concatenate([nominal_linear, nominal_angular])
        if explicit_translational_carriage and step == 0:
            data.qpos[explicit_carriage_qpos_indices] = nominal_position
            data.qvel[explicit_carriage_dof_indices] = nominal_twist[:3]
            if explicit_rotational_carriage:
                data.qpos[explicit_rotation_qpos_indices] = _rotation_to_quaternion(nominal_rotation)
                data.qvel[explicit_rotation_dof_indices] = nominal_twist[3:]
            mujoco.mj_forward(model, data)
        active_kappa = stiffness_schedule(time_s, kappa, recovery_kappa, recovery_ramp_s)
        active_drive_scale = stiffness_schedule(time_s, 1.0, recovery_drive_scale_factor, recovery_ramp_s)
        controller.set_kappa(active_kappa)
        controller.set_carriage_drive_scale(active_drive_scale)
        rod_displacement, rod_velocity = rod_motion(
            time_s, rod_stroke_m, rod_start_time_s, rod_cycles, rod_cycle_period_s
        ) if rod_enabled else (0.0, 0.0)
        # The rod receives a position command, not a qpos teleport.
        data.mocap_pos[obstacle_mocap] = np.array([3.0, 3.0, 3.0])
        data.mocap_quat[obstacle_mocap] = np.array([1.0, 0.0, 0.0, 0.0])
        explicit_position = (
            data.qpos[explicit_carriage_qpos_indices].copy()
            if explicit_translational_carriage else controller.position[:3].copy()
        )
        explicit_velocity = (
            data.qvel[explicit_carriage_dof_indices].copy()
            if explicit_translational_carriage else controller.linear_velocity.copy()
        )
        data.mocap_pos[carriage_mocap] = (
            explicit_position if explicit_translational_carriage else controller.position
        )
        data.mocap_quat[carriage_mocap] = np.array([1.0, 0.0, 0.0, 0.0])
        data.mocap_pos[nominal_marker_mocap] = nominal_position
        data.mocap_quat[nominal_marker_mocap] = np.array([1.0, 0.0, 0.0, 0.0])

        ee_position = data.xpos[ids["hand"]].copy()
        ee_rotation = data.xmat[ids["hand"]].reshape(3, 3).copy()
        ee_twist = body_twist(model, data, ids["hand"])
        data.mocap_pos[actual_marker_mocap] = ee_position
        data.mocap_quat[actual_marker_mocap] = np.array([1.0, 0.0, 0.0, 0.0])
        actual_position_history.append(ee_position.copy())
        trail_stride = max(1, round(0.04 / CONTROL_DT))
        for index, marker_mocap in enumerate(actual_trail_mocaps):
            history_index = len(actual_position_history) - 1 - (ACTUAL_TRAIL_COUNT - index) * trail_stride
            data.mocap_pos[marker_mocap] = (
                actual_position_history[history_index] if history_index >= 0 else np.array([0.0, 0.0, -2.0])
            )
            data.mocap_quat[marker_mocap] = np.array([1.0, 0.0, 0.0, 0.0])
        wrench, carriage_displacement = controller.wrench(ee_position, ee_rotation, ee_twist)
        explicit_force = np.zeros(3, dtype=float)
        explicit_moment = np.zeros(3, dtype=float)
        explicit_rotation = controller.rotation.copy()
        explicit_angular_velocity = controller.angular_velocity.copy()
        if explicit_translational_carriage:
            # The physical carriage replaces only the translational Python
            # carriage channels; SO(3) channels remain in the existing VMC.
            carriage_displacement[:3] = explicit_position - ee_position
            spring_k = active_kappa * config.k_translation_base
            spring_d = 2.0 * config.zeta * np.sqrt(carriage_mass_kg * spring_k)
            explicit_force = _saturated_translation_spring(
                spring_k, config.max_force, explicit_position - ee_position
            ) + spring_d * (explicit_velocity - ee_twist[:3])
            drive_k = config.carriage_drive_k_translation * active_drive_scale
            drive_d = 2.0 * config.carriage_drive_zeta * np.sqrt(carriage_mass_kg * drive_k)
            drive_force = drive_k * (nominal_position - explicit_position) + drive_d * (nominal_twist[:3] - explicit_velocity)
            # Explicit virtual masses need a bounded total coupling force.  The
            # cutting reference uses per-channel max-force saturation; this
            # norm cap prevents low-mass/high-drive combinations from injecting
            # an unresolved impulse into the 4 ms Panda simulation.
            explicit_force = _saturate_vector_norm(explicit_force, 1.5 * config.max_force)
            drive_force = _saturate_vector_norm(drive_force, 1.5 * config.max_force)
            data.qfrc_applied[:] = 0.0
            _apply_body_force(model, data, explicit_carriage_body_id, drive_force - explicit_force)
            _apply_body_force(model, data, ids["hand"], explicit_force)
            wrench[:3] = 0.0
            if explicit_rotational_carriage:
                explicit_rotation = data.xmat[explicit_rotation_carriage_body_id].reshape(3, 3).copy()
                explicit_angular_velocity = body_twist(model, data, explicit_rotation_carriage_body_id)[3:]
                carriage_displacement[3:] = so3_log(explicit_rotation @ ee_rotation.T)
                spring_k_rotation = active_kappa * config.k_rotation_base
                virtual_inertia = config.virtual_inertia * rotational_carriage_inertia_scale
                rotational_zeta = config.zeta if rotational_damping_ratio is None else rotational_damping_ratio
                spring_d_rotation = 2.0 * rotational_zeta * np.sqrt(virtual_inertia * spring_k_rotation)
                explicit_moment = (
                    config.max_moment * np.tanh(spring_k_rotation * carriage_displacement[3:] / config.max_moment)
                    + spring_d_rotation * (explicit_angular_velocity - ee_twist[3:])
                )
                drive_k_rotation = config.carriage_drive_k_rotation * active_drive_scale
                drive_d_rotation = 2.0 * config.carriage_drive_zeta * np.sqrt(virtual_inertia * drive_k_rotation)
                drive_moment = (
                    drive_k_rotation * so3_log(nominal_rotation @ explicit_rotation.T)
                    + drive_d_rotation * (nominal_twist[3:] - explicit_angular_velocity)
                )
                explicit_moment = _saturate_vector_norm(explicit_moment, 1.5 * config.max_moment)
                drive_moment = _saturate_vector_norm(drive_moment, 1.5 * config.max_moment)
                _apply_body_torque(model, data, explicit_rotation_carriage_body_id, drive_moment - explicit_moment)
                _apply_body_torque(model, data, ids["hand"], explicit_moment)
                wrench[3:] = 0.0
        wrench_torque = body_jacobian(model, data, ids["hand"]).T @ wrench
        bias = data.qfrc_bias[:ARM_DOF].copy()
        scale = torque_feasible_scale(bias, wrench_torque)
        desired = bias + scale * wrench_torque
        applied = np.clip(rate_limit_torque(previous_torque, desired, CONTROL_DT, config), -TORQUE_LIMITS, TORQUE_LIMITS)
        data.ctrl[:ARM_DOF] = applied
        # The reference holds the reachable pre-grasp pose until 2.70 s.  A
        # short optional delay therefore gives the released spring system time
        # to rejoin before closure, without changing the arm path itself.
        data.ctrl[ARM_DOF] = 0.040 if response_only else reference.gripper_target(time_s - (grasp_time_s - GRASP_TIME_S))
        data.ctrl[rod_ctrl_index] = rod_displacement
        controller.advance(CONTROL_DT, nominal_position, nominal_rotation, nominal_twist, wrench)
        mujoco.mj_step(model, data)

        rod_contact, rod_force, rod_penetration = rod_contact_diagnostics(model, data, ids["rod_geom"], ids["hand_geom"])
        rod_hand_observed = rod_hand_observed or rod_contact
        acceleration = (ee_twist - previous_twist) / CONTROL_DT
        jerk = (acceleration - previous_acceleration) / CONTROL_DT
        direction = nominal_linear / (np.linalg.norm(nominal_linear) + EPS)
        surge = max(0.0, float(np.dot(ee_twist[:3], direction) - np.linalg.norm(nominal_linear)))
        target_position = data.xpos[ids["target_body"]].copy()
        values = {
            "time": time_s,
            "track_position": float(np.linalg.norm(ee_position - nominal_position)),
            "track_orientation": float(np.linalg.norm(so3_log(nominal_rotation @ ee_rotation.T))),
            "ee_speed": float(np.linalg.norm(ee_twist[:3])),
            "surge": surge,
            "acceleration": float(np.linalg.norm(acceleration[:3])),
            "jerk": float(np.linalg.norm(jerk[:3])),
            "torque_applied": applied.tolist(),
            "torque_ratio": float(np.max(np.abs(applied) / TORQUE_LIMITS)),
            "rod_contact": rod_contact,
            "rod_force": rod_force,
            "rod_penetration": rod_penetration,
            "carriage_displacement": carriage_displacement.tolist(),
            "vmc_wrench": wrench.tolist(),
            "ee_position": ee_position.tolist(),
            "nominal_position": nominal_position.tolist(),
            "carriage_position": controller.position.tolist(),
            "object_position": target_position.tolist(),
            "object_hand_distance": float(np.linalg.norm(target_position - ee_position)),
            "rod_displacement": rod_displacement,
            "rod_command_velocity": rod_velocity,
            "active_kappa": active_kappa,
            "active_drive_scale": active_drive_scale,
            "explicit_carriage_position": explicit_position.tolist(),
            "explicit_carriage_velocity": explicit_velocity.tolist(),
            "explicit_carriage_force": explicit_force.tolist(),
            "explicit_carriage_rotation": explicit_rotation.tolist(),
            "explicit_carriage_angular_velocity": explicit_angular_velocity.tolist(),
            "explicit_carriage_moment": explicit_moment.tolist(),
            "simulation_finite": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        }
        for key, value in values.items():
            log[key].append(value)
        previous_twist = ee_twist
        previous_acceleration = acceleration
        previous_torque = applied
        if renderer is not None and step % render_stride == 0 and render_start_time_s <= time_s <= render_end_time_s:
            # The close-up follows the nominal trajectory, not the actual
            # hand, so a physical departure remains visually observable.
            if camera_view == "hand-closeup":
                render_camera = make_render_camera(camera_view, nominal_position)
            elif render_camera is None:
                render_camera = make_render_camera(camera_view, nominal_position)
            renderer.update_scene(data, camera=render_camera)
            frames.append(renderer.render().copy())

    if renderer is not None:
        renderer.close()
        gif_path = output_dir / f"rod_perturbation_kappa_{kappa:.2f}.gif"
        iio.imwrite(gif_path, np.stack(frames), duration=1.0 / (RENDER_FPS * playback_speed), loop=0)
    else:
        gif_path = None
    arrays = {key: np.asarray(values) for key, values in log.items()}
    perturbation_mask = (arrays["time"] >= ROD_START_TIME_S) & (arrays["time"] <= ROD_END_TIME_S)
    recovery_mask = (arrays["time"] > ROD_END_TIME_S) & (arrays["time"] < grasp_time_s)
    object_position = arrays["object_position"]
    target_lifted = bool(np.max(object_position[:, 2]) > TABLE_TOP_Z + 0.12)
    target_held = bool(object_position[-1, 2] > TABLE_TOP_Z + 0.08 and arrays["object_hand_distance"][-1] < 0.16)
    rod_contact_mask = arrays["rod_contact"].astype(bool)
    peak_displacement = np.max(np.abs(arrays["carriage_displacement"]), axis=0)
    peak_wrench = np.max(np.abs(arrays["vmc_wrench"]), axis=0)
    explicit_force_norm = np.linalg.norm(arrays["explicit_carriage_force"], axis=1)
    explicit_moment_norm = np.linalg.norm(arrays["explicit_carriage_moment"], axis=1)
    peak_trajectory_deviation = _safe_scalar(np.max(arrays["track_position"][perturbation_mask]))
    pregrasp_error = _safe_scalar(arrays["track_position"][np.flatnonzero(arrays["time"] < grasp_time_s)[-1]])
    release_index = int(np.flatnonzero(arrays["time"] >= ROD_END_TIME_S)[0])
    release_error = _safe_scalar(arrays["track_position"][release_index])
    recovery_drop = _safe_scalar(release_error - pregrasp_error)
    contact_times = arrays["time"][rod_contact_mask]
    summary = {
        "kappa": kappa,
        "config": asdict(config),
        "scenario": "physical rod perturbation during open-gripper grasp approach; compliant return to moving nominal trajectory tube",
        "reference": "finite grasp trajectory (moving attractor, not a mathematical limit cycle); replace with fixed WBC pose/twist for WBC+VMC",
        "virtual_mechanism": {
            "explicit_translational_carriage": explicit_translational_carriage,
            "explicit_translational_carriage_mass_kg": carriage_mass_kg if explicit_translational_carriage else None,
            "explicit_rotational_carriage": explicit_rotational_carriage,
            "explicit_rotational_carriage_inertia_scale": rotational_carriage_inertia_scale if explicit_rotational_carriage else None,
            "explicit_rotational_damping_ratio": rotational_damping_ratio if explicit_rotational_carriage else None,
            "rotation_channels": "MuJoCo ball-joint physical virtual carriage" if explicit_rotational_carriage else "existing controller-integrated SO(3) virtual carriage",
            "explicit_force_norm_cap_n": 1.5 * config.max_force if explicit_translational_carriage else None,
        },
        "rod_motion": {
            "enabled": rod_enabled,
            "start_time_s": rod_start_time_s,
            "profile_duration_s": ROD_END_TIME_S - ROD_START_TIME_S,
            "cycles": rod_cycles,
            "cycle_period_s": rod_cycle_period_s,
            "final_end_time_s": rod_start_time_s + (rod_cycles - 1) * rod_cycle_period_s + (ROD_END_TIME_S - ROD_START_TIME_S),
            "stroke_m": rod_stroke_m,
            "height_m": rod_height_m,
        },
        "stiffness_schedule": {
            "shared_six_channel_contact_kappa": kappa,
            "shared_six_channel_recovery_kappa": recovery_kappa,
            "recovery_ramp_start_s": ROD_END_TIME_S,
            "recovery_ramp_duration_s": recovery_ramp_s,
            "recovery_carriage_drive_scale_factor": recovery_drive_scale_factor,
        },
        "visualization": {
            "nominal_marker": "bright blue sphere",
            "actual_marker": "magenta sphere",
            "actual_trail": "magenta 0.48 s end-effector history (exact, no visual scaling)",
            "virtual_carriage_marker": "cyan sphere",
            "nominal_path": "faint blue dotted curve",
            "playback_speed": playback_speed,
            "camera_view": camera_view,
            "render_window_s": [render_start_time_s, render_end_time_s],
        },
        "grasp_time_s": grasp_time_s,
        "contact_time_constant_s": contact_time_constant_s,
        "task_validity": {
            "simulation_finite": bool(np.all(arrays["simulation_finite"])),
            "physical_gripper_actuated": True,
            "rod_hand_contact_observed": rod_hand_observed,
            "target_lifted_after_recovery": target_lifted,
            "target_held_at_end": target_held,
            "max_rod_penetration_m": _safe_scalar(np.max(arrays["rod_penetration"])),
        },
        "six_spring_response": {
            "peak_carriage_displacement": peak_displacement.tolist(),
            "peak_translational_displacement_m": _safe_scalar(np.linalg.norm(peak_displacement[:3])),
            "peak_rotational_displacement_rad": _safe_scalar(np.linalg.norm(peak_displacement[3:])),
            "peak_virtual_wrench": peak_wrench.tolist(),
            "peak_virtual_force_n": _safe_scalar(np.linalg.norm(peak_wrench[:3])),
            # In explicit mode the translational spring is applied directly
            # through MuJoCo and is intentionally absent from vmc_wrench.
            # Keep a separate metric so summaries cannot report a misleading
            # zero translational force for the physical carriage.
            "peak_explicit_translational_spring_force_n": _safe_scalar(np.max(explicit_force_norm)),
            "peak_explicit_rotational_spring_moment_nm": _safe_scalar(np.max(explicit_moment_norm)),
            "peak_virtual_moment_nm": _safe_scalar(np.linalg.norm(peak_wrench[3:])),
            "peak_end_effector_nominal_deviation_m": peak_trajectory_deviation,
            "pregrasp_rejoin_error_m": pregrasp_error,
            "rejoin_fraction": pregrasp_error / max(peak_trajectory_deviation, EPS),
            "error_at_rod_release_m": release_error,
            "release_to_pregrasp_error_drop_m": recovery_drop,
            "release_to_pregrasp_error_drop_fraction": recovery_drop / max(release_error, EPS),
        },
        "tracking": {
            "perturbation_position_rmse_m": _safe_scalar(np.sqrt(np.mean(arrays["track_position"][perturbation_mask] ** 2))),
            "recovery_position_rmse_m": _safe_scalar(np.sqrt(np.mean(arrays["track_position"][recovery_mask] ** 2))),
            "pregrasp_position_error_m": pregrasp_error,
            "final_position_error_m": _safe_scalar(arrays["track_position"][-1]),
        },
        "motion": {
            "recovery_speed_p95_mps": _safe_scalar(np.quantile(arrays["ee_speed"][recovery_mask], 0.95)),
            "forward_surge_max_mps": _safe_scalar(np.max(arrays["surge"][perturbation_mask | recovery_mask])),
            "acceleration_peak_mps2": _safe_scalar(np.max(arrays["acceleration"][perturbation_mask | recovery_mask])),
            "jerk_peak_mps3": _safe_scalar(np.max(arrays["jerk"][perturbation_mask | recovery_mask])),
        },
        "torque": {
            "applied_peak_nm": _safe_scalar(np.max(np.abs(arrays["torque_applied"]))),
            "applied_peak_ratio": _safe_scalar(np.max(arrays["torque_ratio"])),
            "hard_limit_fraction": _safe_scalar(np.mean(np.isclose(np.abs(arrays["torque_applied"]), TORQUE_LIMITS[None, :], atol=1e-5))),
        },
        "rod_diagnostics": {
            "contact_start_time_s": _safe_scalar(contact_times[0]) if len(contact_times) else None,
            "contact_end_time_s": _safe_scalar(contact_times[-1]) if len(contact_times) else None,
            "contact_duration_s": _safe_scalar(np.sum(rod_contact_mask) * CONTROL_DT),
            "peak_contact_force_n": _safe_scalar(np.max(arrays["rod_force"])),
            "contact_impulse_ns": _safe_scalar(np.sum(arrays["rod_force"]) * CONTROL_DT),
            "max_penetration_m": _safe_scalar(np.max(arrays["rod_penetration"])),
        },
        "gif": str(gif_path) if gif_path else None,
    }
    np.savez_compressed(output_dir / f"rod_perturbation_kappa_{kappa:.2f}_trace.npz", **arrays)
    (output_dir / f"rod_perturbation_kappa_{kappa:.2f}_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
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
    parser.add_argument("--rod-stroke", type=float, default=0.16)
    parser.add_argument(
        "--rod-height", type=float, default=0.540,
        help="World z height of the rod axis; use this to test impact geometry while keeping the same rod profile.",
    )
    parser.add_argument(
        "--recovery-kappa", type=float, default=None,
        help="Shared six-channel stiffness after rod retraction; default keeps constant stiffness.",
    )
    parser.add_argument("--recovery-ramp", type=float, default=0.16, help="Seconds to smoothly ramp from contact to recovery stiffness.")
    parser.add_argument(
        "--recovery-carriage-drive-scale", type=float, default=None,
        help="Absolute carriage-drive scale after release; default keeps the contact-stage scale.",
    )
    parser.add_argument("--grasp-time", type=float, default=GRASP_TIME_S, help="Delay gripper closure until recovery has started.")
    parser.add_argument("--rod-start-time", type=float, default=ROD_START_TIME_S)
    parser.add_argument("--rod-cycles", type=int, default=1, help="Repeated physical press--hold--retract profiles.")
    parser.add_argument("--rod-cycle-period", type=float, default=0.80, help="Seconds from one rod pulse start to the next.")
    parser.add_argument("--response-only", action="store_true", help="Hold the nominal pre-grasp pose and leave the gripper open for repeated-excitation plots.")
    parser.add_argument("--explicit-translational-carriage", action="store_true", help="Use one explicit MuJoCo three-axis translation carriage mass.")
    parser.add_argument("--carriage-mass-kg", type=float, default=0.35, help="Mass per physical translation carriage axis.")
    parser.add_argument(
        "--explicit-rotational-carriage", action="store_true",
        help="Add a MuJoCo ball-joint rotational virtual carriage below the explicit translation carriage.",
    )
    parser.add_argument(
        "--rotational-carriage-inertia-scale", type=float, default=1.0,
        help="Multiplier on the rotational virtual inertia (base 0.08 kg m^2 per axis).",
    )
    parser.add_argument(
        "--rotational-damping-ratio", type=float, default=None,
        help="Optional damping ratio for the explicit rotational spring; default shares the six-channel zeta.",
    )
    parser.add_argument("--disable-rod", action="store_true", help="Paired no-perturbation grasp reference run.")
    parser.add_argument("--playback-speed", type=float, default=1.0, help="GIF-only playback multiplier; simulation dynamics are unchanged.")
    parser.add_argument(
        "--camera-view", choices=CAMERA_VIEWS, default="overview",
        help="GIF-only view: full task context or hand-centred close-up.",
    )
    parser.add_argument("--render-start-time", type=float, default=0.0, help="GIF-only simulation-time start, in seconds.")
    parser.add_argument("--render-end-time", type=float, default=SIM_TIME_S, help="GIF-only simulation-time end, in seconds.")
    parser.add_argument("--render-gif", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    positive_scales = [args.damping_ratio, args.carriage_drive_scale, args.carriage_drive_damping_ratio, args.contact_time_constant, args.playback_speed, args.rod_cycle_period, args.carriage_mass_kg, args.rod_height, args.rotational_carriage_inertia_scale]
    if args.rotational_damping_ratio is not None:
        positive_scales.append(args.rotational_damping_ratio)
    if min(positive_scales) <= 0 or args.rod_stroke < 0 or args.recovery_ramp < 0 or args.rod_cycles < 1 or args.rod_cycle_period < ROD_END_TIME_S - ROD_START_TIME_S or not ROD_END_TIME_S < args.grasp_time < LIFT_COMPLETE_TIME_S or (args.recovery_kappa is not None and args.recovery_kappa <= 0) or (args.recovery_carriage_drive_scale is not None and args.recovery_carriage_drive_scale <= 0) or (args.explicit_rotational_carriage and not args.explicit_translational_carriage):
        raise ValueError("all physical and controller scales must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    config = replace(
        VMCConfig(),
        zeta=args.damping_ratio,
        carriage_drive_k_translation=VMCConfig().carriage_drive_k_translation * args.carriage_drive_scale,
        carriage_drive_k_rotation=VMCConfig().carriage_drive_k_rotation * args.carriage_drive_scale,
        carriage_drive_zeta=args.carriage_drive_damping_ratio,
    )
    recovery_drive_scale_factor = (
        1.0 if args.recovery_carriage_drive_scale is None
        else args.recovery_carriage_drive_scale / args.carriage_drive_scale
    )
    runs = [
        run_episode(
            args.menagerie, kappa, args.output_dir, args.render_gif, config,
            args.rod_stroke, args.contact_time_constant, rod_enabled=not args.disable_rod,
            playback_speed=args.playback_speed, camera_view=args.camera_view,
            render_start_time_s=args.render_start_time, render_end_time_s=args.render_end_time,
            recovery_kappa=args.recovery_kappa, recovery_ramp_s=args.recovery_ramp,
            recovery_drive_scale_factor=recovery_drive_scale_factor,
            grasp_time_s=args.grasp_time,
            rod_start_time_s=args.rod_start_time, rod_cycles=args.rod_cycles,
            rod_cycle_period_s=args.rod_cycle_period, response_only=args.response_only,
            explicit_translational_carriage=args.explicit_translational_carriage,
            carriage_mass_kg=args.carriage_mass_kg,
            rod_height_m=args.rod_height,
            explicit_rotational_carriage=args.explicit_rotational_carriage,
            rotational_carriage_inertia_scale=args.rotational_carriage_inertia_scale,
            rotational_damping_ratio=args.rotational_damping_ratio,
        )
        for kappa in args.kappas
    ]
    matrix = {"protocol": {key: value for key, value in vars(args).items() if key not in {"menagerie", "output_dir"}}, "runs": runs}
    (args.output_dir / "evaluation_matrix.json").write_text(json.dumps(matrix, indent=2) + "\n")
    print(json.dumps(matrix, indent=2))


if __name__ == "__main__":
    os.environ.setdefault("MUJOCO_GL", "egl")
    main()
