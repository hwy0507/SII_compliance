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
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

import imageio.v3 as iio
import mujoco
import numpy as np

from energy_safety import EnergyBudgetSafety, EnergySafetyConfig
from fixed_panda_wbc import FixedBasePandaWBC
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
REFERENCE_SOURCES = ("proxy", "fixed_panda_wbc")
CONTROLLER_MODES = ("rigid", "impedance", "vmc", "vmc_gated", "vmc_taper", "vmc_energy")
VMC_MODES = ("vmc", "vmc_gated", "vmc_taper", "vmc_energy")
ROD_APPROACH_SIDES = ("negative_x", "positive_x", "negative_y", "positive_y", "negative_z", "positive_z")
PHASE_LABELS = ("approach", "contact", "unloading", "rejoined", "task")
REJOIN_THRESHOLD_M = 0.005
REJOIN_HOLD_S = 0.080
CONTACT_WINDOW_MERGE_S = 0.020


@dataclass(frozen=True)
class RodApproachGeometry:
    """Physical support, slide, and cylinder orientation for one approach side."""

    approach_side: str
    support_position_m: tuple[float, float, float]
    slide_axis_world: tuple[float, float, float]
    rod_long_axis_world: tuple[float, float, float]
    cylinder_quaternion_wxyz: tuple[float, float, float, float]


def rod_approach_geometry(
    approach_side: str,
    rod_height_m: float,
    rod_center_x_m: float = 0.55,
    rod_center_y_m: float = 0.0,
) -> RodApproachGeometry:
    """Return a non-degenerate, axis-aligned physical rod geometry.

    The cylinder's long axis is always orthogonal to the commanded slide axis.
    ``rod_height_m`` remains the interaction-plane height for horizontal
    approaches.  For vertical approaches it is the central height around
    which mirrored supports start 0.14 m below/above the hand plane.
    """
    if approach_side not in ROD_APPROACH_SIDES:
        raise ValueError(f"unknown rod approach side: {approach_side}")
    if not np.all(np.isfinite((rod_height_m, rod_center_x_m, rod_center_y_m))):
        raise ValueError("rod approach geometry requires finite coordinates")
    if approach_side == "negative_y":
        return RodApproachGeometry(approach_side, (rod_center_x_m, -0.20, rod_height_m), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.7071068, 0.0, 0.7071068, 0.0))
    if approach_side == "positive_y":
        return RodApproachGeometry(approach_side, (rod_center_x_m, 0.20, rod_height_m), (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.7071068, 0.0, 0.7071068, 0.0))
    if approach_side == "negative_x":
        return RodApproachGeometry(approach_side, (rod_center_x_m - 0.20, rod_center_y_m, rod_height_m), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.7071068, -0.7071068, 0.0, 0.0))
    if approach_side == "positive_x":
        return RodApproachGeometry(approach_side, (rod_center_x_m + 0.20, rod_center_y_m, rod_height_m), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.7071068, -0.7071068, 0.0, 0.0))
    if approach_side == "negative_z":
        return RodApproachGeometry(approach_side, (rod_center_x_m, rod_center_y_m, rod_height_m - 0.14), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (0.7071068, -0.7071068, 0.0, 0.0))
    return RodApproachGeometry(approach_side, (rod_center_x_m, rod_center_y_m, rod_height_m + 0.14), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (0.7071068, -0.7071068, 0.0, 0.0))


def kappa_filename_tag(kappa: float | np.ndarray) -> str:
    """Stable file stem for legacy scalar and independent six-kappa runs."""
    values = np.asarray(kappa, dtype=float)
    if values.ndim == 0:
        return f"kappa_{float(values):.2f}"
    if values.shape != (6,):
        raise ValueError("kappa filename tag expects a scalar or six-vector")
    return "kvec_" + "_".join(f"{value:.3g}" for value in values)


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
    contact_kappa: float | np.ndarray,
    recovery_kappa: float | np.ndarray,
    recovery_ramp_s: float,
    release_time_s: float = ROD_END_TIME_S,
) -> float | np.ndarray:
    """Interpolate shared or six-dimensional stiffness schedules after release."""

    contact = np.asarray(contact_kappa, dtype=float)
    recovery = np.asarray(recovery_kappa, dtype=float)
    scalar_schedule = contact.ndim == 0 and recovery.ndim == 0
    if contact.ndim == 0:
        contact = np.full(6, float(contact))
    if recovery.ndim == 0:
        recovery = np.full(6, float(recovery))
    if contact.shape != (6,) or recovery.shape != (6,) or not np.all(np.isfinite(contact)) or not np.all(np.isfinite(recovery)) or np.any(contact <= 0.0) or np.any(recovery <= 0.0) or recovery_ramp_s < 0.0 or not np.isfinite(release_time_s):
        raise ValueError("stiffness schedule arguments must be positive")
    if time_s <= release_time_s:
        return float(contact[0]) if scalar_schedule else contact.copy()
    if recovery_ramp_s == 0.0 or time_s >= release_time_s + recovery_ramp_s:
        return float(recovery[0]) if scalar_schedule else recovery.copy()
    blend, _ = smoothstep((time_s - release_time_s) / recovery_ramp_s)
    result = (1.0 - blend) * contact + blend * recovery
    return float(result[0]) if scalar_schedule else result


def _direct_cartesian_wrench(
    nominal_position: np.ndarray,
    nominal_rotation: np.ndarray,
    nominal_twist: np.ndarray,
    ee_position: np.ndarray,
    ee_rotation: np.ndarray,
    ee_twist: np.ndarray,
    translation_stiffness: float,
    rotation_stiffness: float,
    damping_ratio: float,
    maximum_force: float,
    maximum_moment: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Bounded direct Cartesian PD wrench for rigid/impedance baselines."""
    position_error = nominal_position - ee_position
    rotation_error = so3_log(nominal_rotation @ ee_rotation.T)
    velocity_error = nominal_twist - ee_twist
    translation_damping = 2.0 * damping_ratio * np.sqrt(VMCConfig().virtual_mass * translation_stiffness)
    rotation_damping = 2.0 * damping_ratio * np.sqrt(VMCConfig().virtual_inertia * rotation_stiffness)
    force = _saturated_translation_spring(translation_stiffness, maximum_force, position_error)
    force += translation_damping * velocity_error[:3]
    moment = maximum_moment * np.tanh(rotation_stiffness * rotation_error / maximum_moment)
    moment += rotation_damping * velocity_error[3:]
    return np.concatenate([
        _saturate_vector_norm(force, maximum_force),
        _saturate_vector_norm(moment, maximum_moment),
    ]), np.concatenate([position_error, rotation_error])


def _contact_windows(time: np.ndarray, contact: np.ndarray) -> list[tuple[int, int]]:
    """Return inclusive physical contact windows, merging solver-scale gaps."""
    mask = np.asarray(contact, dtype=bool)
    edges = np.diff(np.concatenate([[False], mask, [False]]).astype(int))
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1) - 1
    raw = list(zip(starts.tolist(), ends.tolist()))
    if not raw:
        return []
    merged = [raw[0]]
    for start, end in raw[1:]:
        previous_start, previous_end = merged[-1]
        if float(time[start] - time[previous_end]) <= CONTACT_WINDOW_MERGE_S:
            merged[-1] = (previous_start, end)
        else:
            merged.append((start, end))
    return merged


def _phase_analysis(
    time: np.ndarray,
    contact: np.ndarray,
    position_error: np.ndarray,
    grasp_time_s: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Label approach/contact/unloading/rejoin phases from measured signals."""
    phase = np.full(len(time), 4, dtype=np.int8)
    windows = _contact_windows(time, contact)
    if not windows:
        phase[time < grasp_time_s] = 0
        return phase, {
            "labels": list(PHASE_LABELS),
            "contact_windows_s": [],
            "primary_contact_start_s": None,
            "primary_contact_release_s": None,
            "rejoin_time_s": None,
            "release_to_rejoin_latency_s": None,
            "secondary_contact_count": 0,
            "secondary_contact_windows_s": [],
            "phase_durations_s": {"approach": float(min(grasp_time_s, time[-1])), "contact": 0.0, "unloading": 0.0, "rejoined": 0.0, "task": float(max(0.0, time[-1] - grasp_time_s))},
        }

    primary_start, primary_end = windows[0]
    phase[time < time[primary_start]] = 0
    phase[np.asarray(contact, dtype=bool)] = 1
    release_time = float(time[primary_end])
    rejoin_index: int | None = None
    hold_steps = max(1, int(np.ceil(REJOIN_HOLD_S / max(time[1] - time[0], EPS))))
    eligible = np.flatnonzero(time >= release_time)
    within = position_error <= REJOIN_THRESHOLD_M
    for index in eligible:
        stop = index + hold_steps
        if stop <= len(time) and bool(np.all(within[index:stop])):
            rejoin_index = int(index)
            break
    non_contact_pregrasp = (~np.asarray(contact, dtype=bool)) & (time >= release_time) & (time < grasp_time_s)
    phase[non_contact_pregrasp] = 2
    if rejoin_index is not None:
        phase[(time >= time[rejoin_index]) & (time < grasp_time_s) & (~np.asarray(contact, dtype=bool))] = 3
    phase[time >= grasp_time_s] = 4
    durations = {label: float(np.sum(phase == index) * (time[1] - time[0])) for index, label in enumerate(PHASE_LABELS)}
    contact_windows_s = [[float(time[start]), float(time[end])] for start, end in windows]
    return phase, {
        "labels": list(PHASE_LABELS),
        "contact_windows_s": contact_windows_s,
        "primary_contact_start_s": float(time[primary_start]),
        "primary_contact_release_s": release_time,
        "rejoin_time_s": None if rejoin_index is None else float(time[rejoin_index]),
        "release_to_rejoin_latency_s": None if rejoin_index is None else float(time[rejoin_index] - release_time),
        "secondary_contact_count": max(0, len(windows) - 1),
        "secondary_contact_windows_s": contact_windows_s[1:],
        "phase_durations_s": durations,
    }


def _rod_scene_xml(
    menagerie: Path,
    contact_time_constant_s: float,
    rod_height_m: float = 0.540,
    rod_center_x_m: float = 0.55,
    rod_center_y_m: float = 0.0,
    explicit_translational_carriage: bool = False,
    carriage_mass_kg: float = 0.35,
    explicit_rotational_carriage: bool = False,
    rotational_carriage_inertia_scale: float = 1.0,
    rod_approach_side: str = "negative_y",
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
    # The rod is a finite-mass, position-driven body on a physical MuJoCo
    # slide.  Its support location, slide axis, and long-axis orientation are
    # constructed from the requested approach side instead of relabelling a
    # single y-axis collision after the fact.
    approach = rod_approach_geometry(rod_approach_side, rod_height_m, rod_center_x_m, rod_center_y_m)
    rod_guide_xml = ""
    if rod_approach_side.endswith("_y"):
        rod_guide_xml = (
            f'<geom name="rod_guide" type="box" pos="{rod_center_x_m:.3f} '
            f'{0.5 * approach.support_position_m[1]:.3f} 0.435" size="0.18 0.13 0.008" '
            'contype="0" conaffinity="0" rgba="0.10 0.12 0.15 0.70"/>'
        )
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
      <body name="rod_support" pos="{approach.support_position_m[0]:.3f} {approach.support_position_m[1]:.3f} {approach.support_position_m[2]:.3f}">
        <joint name="rod_slide" type="slide" axis="{approach.slide_axis_world[0]:.1f} {approach.slide_axis_world[1]:.1f} {approach.slide_axis_world[2]:.1f}" range="0 0.20" damping="2.0"/>
        <geom name="rod_geom" type="cylinder" size="0.014 0.15" quat="{approach.cylinder_quaternion_wxyz[0]:.7f} {approach.cylinder_quaternion_wxyz[1]:.7f} {approach.cylinder_quaternion_wxyz[2]:.7f} {approach.cylinder_quaternion_wxyz[3]:.7f}"
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
      {rod_guide_xml}
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
    rod_approach_side: str = "negative_y",
    rod_center_x_m: float = 0.55,
    rod_center_y_m: float = 0.0,
) -> tuple[mujoco.MjModel, mujoco.MjData]:
    xml = _rod_scene_xml(
        menagerie=menagerie, contact_time_constant_s=contact_time_constant_s, rod_height_m=rod_height_m,
        rod_center_x_m=rod_center_x_m, rod_center_y_m=rod_center_y_m,
        explicit_translational_carriage=explicit_translational_carriage, carriage_mass_kg=carriage_mass_kg,
        explicit_rotational_carriage=explicit_rotational_carriage,
        rotational_carriage_inertia_scale=rotational_carriage_inertia_scale, rod_approach_side=rod_approach_side,
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
    stiffness: float | np.ndarray,
    maximum_force: float,
    displacement: np.ndarray,
) -> np.ndarray:
    """Per-axis nonlinear force law matching the existing VMC saturation convention."""
    stiffness_array = np.asarray(stiffness, dtype=float)
    if stiffness_array.ndim == 0:
        stiffness_array = np.full(np.asarray(displacement).shape, float(stiffness_array))
    return maximum_force * np.tanh(stiffness_array * np.asarray(displacement, dtype=float) / maximum_force)


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
    kappa: float | np.ndarray,
    output_dir: Path,
    render_gif: bool,
    config: VMCConfig,
    rod_stroke_m: float,
    contact_time_constant_s: float,
    rod_enabled: bool = True,
    remove_rod_when_disabled: bool = False,
    playback_speed: float = 1.0,
    camera_view: str = "overview",
    render_start_time_s: float = 0.0,
    render_end_time_s: float = SIM_TIME_S,
    recovery_kappa: float | np.ndarray | None = None,
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
    rod_center_x_m: float = 0.55,
    rod_center_y_m: float = 0.0,
    explicit_rotational_carriage: bool = False,
    rotational_carriage_inertia_scale: float = 1.0,
    rotational_damping_ratio: float | None = None,
    controller_mode: str = "vmc",
    rod_approach_side: str = "negative_y",
    recovery_gate_hold_s: float = 0.28,
    recovery_gate_taper_s: float = 0.04,
    energy_safety_config: EnergySafetyConfig | None = None,
    reference_source: str = "proxy",
) -> dict[str, Any]:
    if controller_mode not in CONTROLLER_MODES:
        raise ValueError(f"unknown controller mode: {controller_mode}")
    if reference_source not in REFERENCE_SOURCES:
        raise ValueError(f"unknown reference source: {reference_source}")
    if controller_mode not in VMC_MODES and (explicit_translational_carriage or explicit_rotational_carriage):
        raise ValueError("explicit virtual carriages are available only for VMC controller modes")
    if explicit_rotational_carriage and not explicit_translational_carriage:
        raise ValueError("an explicit rotational carriage requires the explicit translational carriage parent")
    if rod_approach_side not in ROD_APPROACH_SIDES or not np.all(np.isfinite((rod_height_m, rod_center_x_m, rod_center_y_m))) or recovery_gate_hold_s < 0.0 or recovery_gate_taper_s < 0.0 or rotational_carriage_inertia_scale <= 0.0 or (rotational_damping_ratio is not None and rotational_damping_ratio <= 0.0):
        raise ValueError("rotational carriage inertia scale must be positive")
    if not 0.0 <= render_start_time_s < render_end_time_s <= SIM_TIME_S:
        raise ValueError("render window must satisfy 0 <= start < end <= simulation time")
    kappa_vector = np.asarray(kappa, dtype=float)
    if kappa_vector.ndim == 0:
        kappa_vector = np.full(6, float(kappa_vector))
    recovery_kappa = kappa if recovery_kappa is None else recovery_kappa
    recovery_kappa_vector = np.asarray(recovery_kappa, dtype=float)
    if recovery_kappa_vector.ndim == 0:
        recovery_kappa_vector = np.full(6, float(recovery_kappa_vector))
    rod_final_release_s = rod_start_time_s + (rod_cycles - 1) * rod_cycle_period_s + (ROD_END_TIME_S - ROD_START_TIME_S)
    if kappa_vector.shape != (6,) or recovery_kappa_vector.shape != (6,) or not np.all(np.isfinite(kappa_vector)) or not np.all(np.isfinite(recovery_kappa_vector)) or np.any(kappa_vector <= 0.0) or np.any(recovery_kappa_vector <= 0.0) or recovery_ramp_s < 0.0 or recovery_drive_scale_factor <= 0.0 or not rod_final_release_s < grasp_time_s < LIFT_COMPLETE_TIME_S or rod_cycles < 1 or rod_cycle_period_s < ROD_END_TIME_S - ROD_START_TIME_S:
        raise ValueError("recovery stiffness and ramp must be non-negative / positive")
    # The default height intersects the descending hand.  In the repeated
    # response fixture the arm stays at the lower pre-grasp pose, so align the
    # same physical rod to that fixed interaction plane instead.
    model, data = make_rod_model(
        menagerie, contact_time_constant_s, 0.520 if response_only else rod_height_m,
        explicit_translational_carriage, carriage_mass_kg,
        explicit_rotational_carriage, rotational_carriage_inertia_scale, rod_approach_side,
        rod_center_x_m, rod_center_y_m,
    )
    approach_geometry = rod_approach_geometry(
        rod_approach_side, 0.520 if response_only else rod_height_m, rod_center_x_m, rod_center_y_m,
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
    if not rod_enabled and remove_rod_when_disabled:
        # A vertical or fore-aft support can otherwise remain in the workspace
        # at zero slide displacement and corrupt the matched no-rod reference.
        # This explicitly removes only collision participation of the physical
        # rod for the reference episode; V2/V3 retain their legacy default.
        model.geom_contype[ids["rod_geom"]] = 0
        model.geom_conaffinity[ids["rod_geom"]] = 0
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
    fixed_wbc = (
        FixedBasePandaWBC(model, ids["hand"], data.qpos[:ARM_DOF])
        if reference_source == "fixed_panda_wbc" else None
    )
    # The dotted blue curve makes the target moving trajectory visible in the
    # GIF; it is a visual aid only and never contributes collision/contact.
    for index, marker_mocap in enumerate(path_marker_mocaps):
        path_time = index * min(SIM_TIME_S, 6.20) / (PATH_MARKER_COUNT - 1)
        path_position, _, _, _ = reference.sample(path_time)
        data.mocap_pos[marker_mocap] = path_position
        data.mocap_quat[marker_mocap] = np.array([1.0, 0.0, 0.0, 0.0])
    controller = SixDVirtualCarriage(
        config, kappa_vector, data.xpos[ids["hand"]].copy(), data.xmat[ids["hand"]].reshape(3, 3).copy()
    )
    renderer: mujoco.Renderer | None = mujoco.Renderer(model, height=480, width=640) if render_gif else None
    render_camera: str | mujoco.MjvCamera | None = None
    frames: list[np.ndarray] = []
    render_stride = max(1, round(1.0 / (RENDER_FPS * CONTROL_DT)))
    log: dict[str, list[Any]] = {key: [] for key in (
        "time", "track_position", "track_orientation", "ee_speed", "surge", "acceleration", "jerk",
        "torque_applied", "torque_ratio", "rod_contact", "rod_force", "rod_penetration",
        "carriage_displacement", "vmc_wrench", "ee_position", "nominal_position", "carriage_position",
        # These proprioceptive signals are sufficient to reconstruct a
        # deployable stiffness-policy observation offline.  Contact flags,
        # rod state, and contact force remain diagnostics only and must not be
        # consumed by the eventual deployed policy.
        "ee_rotation", "nominal_rotation", "ee_twist", "nominal_twist", "joint_position", "joint_velocity",
        "wbc_task_twist", "wbc_joint_velocity", "wbc_position_error", "wbc_orientation_error",
        "object_position", "object_hand_distance", "rod_displacement", "rod_command_velocity", "active_kappa", "active_drive_scale", "recovery_gate",
        "energy_tank_j", "energy_direction_scale", "energy_scale", "energy_requested_boost_n", "energy_applied_boost_n",
        "explicit_carriage_position", "explicit_carriage_velocity", "explicit_carriage_force",
        "explicit_carriage_rotation", "explicit_carriage_angular_velocity", "explicit_carriage_moment",
        "simulation_finite",
    )}
    previous_twist = np.zeros(6)
    previous_acceleration = np.zeros(6)
    previous_torque = data.qfrc_bias[:ARM_DOF].copy()
    actual_position_history: list[np.ndarray] = []
    rod_hand_observed = False
    recovery_gate_remaining_s = 0.0
    energy_safety = EnergyBudgetSafety(energy_safety_config) if controller_mode == "vmc_energy" else None
    steps = int(SIM_TIME_S / CONTROL_DT)

    for step in range(steps):
        time_s = step * CONTROL_DT
        # For repeated-excitation visualizations, first follow the nominal
        # approach until the pre-grasp pose is reached, then hold that pose.
        # Starting at the held reference from t=0 would create an artificial
        # tracking jump that could be mistaken for a collision response.
        reference_time_s = min(time_s, 1.70) if response_only else time_s
        planned_position, planned_rotation, planned_linear, planned_angular = reference.sample(reference_time_s)
        planned_twist = np.concatenate([planned_linear, planned_angular])
        ee_position = data.xpos[ids["hand"]].copy()
        ee_rotation = data.xmat[ids["hand"]].reshape(3, 3).copy()
        ee_twist = body_twist(model, data, ids["hand"])
        if fixed_wbc is None:
            nominal_position, nominal_rotation, nominal_twist = planned_position, planned_rotation, planned_twist
            wbc_task_twist = nominal_twist.copy()
            wbc_joint_velocity = np.zeros(ARM_DOF)
            wbc_position_error = np.zeros(3)
            wbc_orientation_error = np.zeros(3)
        else:
            wbc_command = fixed_wbc.command(data, planned_position, planned_rotation, planned_twist)
            nominal_position, nominal_rotation = wbc_command.target_position_m, wbc_command.target_rotation
            nominal_twist = wbc_command.task_twist_world
            wbc_task_twist = wbc_command.task_twist_world
            wbc_joint_velocity = wbc_command.joint_velocity_radps
            wbc_position_error = wbc_command.position_error_m
            wbc_orientation_error = wbc_command.orientation_error_rad
        if explicit_translational_carriage and step == 0:
            data.qpos[explicit_carriage_qpos_indices] = nominal_position
            data.qvel[explicit_carriage_dof_indices] = nominal_twist[:3]
            if explicit_rotational_carriage:
                data.qpos[explicit_rotation_qpos_indices] = _rotation_to_quaternion(nominal_rotation)
                data.qvel[explicit_rotation_dof_indices] = nominal_twist[3:]
            mujoco.mj_forward(model, data)
        active_kappa = stiffness_schedule(time_s, kappa_vector, recovery_kappa_vector, recovery_ramp_s, rod_final_release_s)
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

        if controller_mode in ("vmc_gated", "vmc_taper", "vmc_energy"):
            position_error = float(np.linalg.norm(nominal_position - ee_position))
            instant_phase = np.clip((position_error - 0.003) / 0.009, 0.0, 1.0)
            instant_gate = float(instant_phase * instant_phase * (3.0 - 2.0 * instant_phase))
            if instant_gate >= 0.05:
                recovery_gate_remaining_s = recovery_gate_hold_s
            else:
                recovery_gate_remaining_s = max(0.0, recovery_gate_remaining_s - CONTROL_DT)
            if controller_mode in ("vmc_taper", "vmc_energy") and recovery_gate_taper_s > 0.0:
                taper_phase = np.clip(recovery_gate_remaining_s / recovery_gate_taper_s, 0.0, 1.0)
                held_gate = float(taper_phase * taper_phase * (3.0 - 2.0 * taper_phase))
            else:
                held_gate = float(recovery_gate_remaining_s > 0.0)
            recovery_gate = max(instant_gate, held_gate)
            active_drive_scale = 1.0 + recovery_gate * (recovery_drive_scale_factor - 1.0)
        else:
            recovery_gate = 0.0
            active_drive_scale = stiffness_schedule(time_s, 1.0, recovery_drive_scale_factor, recovery_ramp_s, rod_final_release_s)
        controller.set_kappa(active_kappa)
        controller.set_carriage_drive_scale(active_drive_scale)
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
        if controller_mode in VMC_MODES:
            wrench, carriage_displacement = controller.wrench(ee_position, ee_rotation, ee_twist)
        elif controller_mode == "impedance":
            wrench, carriage_displacement = _direct_cartesian_wrench(
                nominal_position, nominal_rotation, nominal_twist,
                ee_position, ee_rotation, ee_twist,
                translation_stiffness=900.0,
                rotation_stiffness=45.0,
                damping_ratio=1.2,
                maximum_force=config.max_force,
                maximum_moment=config.max_moment,
            )
        else:
            wrench, carriage_displacement = _direct_cartesian_wrench(
                nominal_position, nominal_rotation, nominal_twist,
                ee_position, ee_rotation, ee_twist,
                translation_stiffness=8_000.0,
                rotation_stiffness=360.0,
                damping_ratio=1.5,
                maximum_force=90.0,
                maximum_moment=12.0,
            )
        explicit_force = np.zeros(3, dtype=float)
        explicit_moment = np.zeros(3, dtype=float)
        energy_tank_j = energy_safety.energy_j if energy_safety is not None else 0.0
        energy_direction_scale = energy_scale = 1.0
        energy_requested_boost_n = energy_applied_boost_n = 0.0
        explicit_rotation = controller.rotation.copy()
        explicit_angular_velocity = controller.angular_velocity.copy()
        if explicit_translational_carriage:
            # The physical carriage replaces only the translational Python
            # carriage channels; SO(3) channels remain in the existing VMC.
            carriage_displacement[:3] = explicit_position - ee_position
            spring_k = active_kappa[:3] * config.k_translation_base
            spring_d = 2.0 * config.zeta * np.sqrt(carriage_mass_kg * spring_k)
            explicit_force = _saturated_translation_spring(
                spring_k, config.max_force, explicit_position - ee_position
            ) + spring_d * (explicit_velocity - ee_twist[:3])
            drive_k = config.carriage_drive_k_translation * active_drive_scale
            drive_d = 2.0 * config.carriage_drive_zeta * np.sqrt(carriage_mass_kg * drive_k)
            drive_position_error = nominal_position - explicit_position
            drive_velocity_error = nominal_twist[:3] - explicit_velocity
            drive_force = drive_k * drive_position_error + drive_d * drive_velocity_error
            if energy_safety is not None:
                base_k = config.carriage_drive_k_translation
                base_d = 2.0 * config.carriage_drive_zeta * np.sqrt(carriage_mass_kg * base_k)
                base_drive_force = base_k * drive_position_error + base_d * drive_velocity_error
                drive_force, energy = energy_safety.filter_increment(
                    base_drive_force, drive_force, drive_position_error, drive_velocity_error,
                    explicit_velocity, drive_d, CONTROL_DT,
                )
                energy_tank_j = energy.tank_energy_j
                energy_direction_scale = energy.direction_scale
                energy_scale = energy.energy_scale
                energy_requested_boost_n = energy.requested_boost_norm_n
                energy_applied_boost_n = energy.applied_boost_norm_n
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
                spring_k_rotation = active_kappa[3:] * config.k_rotation_base
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
        if controller_mode in VMC_MODES:
            controller.advance(CONTROL_DT, nominal_position, nominal_rotation, nominal_twist, wrench)
        mujoco.mj_step(model, data)

        rod_contact, rod_force, rod_penetration = rod_contact_diagnostics(model, data, ids["rod_geom"], ids["hand_geom"])
        rod_hand_observed = rod_hand_observed or rod_contact
        acceleration = (ee_twist - previous_twist) / CONTROL_DT
        jerk = (acceleration - previous_acceleration) / CONTROL_DT
        nominal_linear = nominal_twist[:3]
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
            "ee_rotation": ee_rotation.tolist(),
            "nominal_rotation": nominal_rotation.tolist(),
            "ee_twist": ee_twist.tolist(),
            "nominal_twist": nominal_twist.tolist(),
            "joint_position": data.qpos[:ARM_DOF].copy().tolist(),
            "joint_velocity": data.qvel[:ARM_DOF].copy().tolist(),
            "wbc_task_twist": wbc_task_twist.tolist(),
            "wbc_joint_velocity": wbc_joint_velocity.tolist(),
            "wbc_position_error": wbc_position_error.tolist(),
            "wbc_orientation_error": wbc_orientation_error.tolist(),
            "object_position": target_position.tolist(),
            "object_hand_distance": float(np.linalg.norm(target_position - ee_position)),
            "rod_displacement": rod_displacement,
            "rod_command_velocity": rod_velocity,
            "active_kappa": active_kappa,
            "active_drive_scale": active_drive_scale,
            "recovery_gate": recovery_gate,
            "energy_tank_j": energy_tank_j,
            "energy_direction_scale": energy_direction_scale,
            "energy_scale": energy_scale,
            "energy_requested_boost_n": energy_requested_boost_n,
            "energy_applied_boost_n": energy_applied_boost_n,
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
        render_file_tag = kappa_filename_tag(kappa if np.asarray(kappa).ndim == 0 else kappa_vector)
        gif_path = output_dir / f"rod_perturbation_{render_file_tag}.gif"
        iio.imwrite(gif_path, np.stack(frames), duration=1.0 / (RENDER_FPS * playback_speed), loop=0)
    else:
        gif_path = None
    arrays = {key: np.asarray(values) for key, values in log.items()}
    phase, phase_summary = _phase_analysis(arrays["time"], arrays["rod_contact"], arrays["track_position"], grasp_time_s)
    arrays["phase"] = phase
    perturbation_mask = (arrays["time"] >= rod_start_time_s) & (arrays["time"] <= rod_final_release_s)
    recovery_mask = (arrays["time"] > rod_final_release_s) & (arrays["time"] < grasp_time_s)
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
    release_index = int(np.flatnonzero(arrays["time"] >= rod_final_release_s)[0])
    release_error = _safe_scalar(arrays["track_position"][release_index])
    recovery_drop = _safe_scalar(release_error - pregrasp_error)
    contact_times = arrays["time"][rod_contact_mask]
    contact_start_s = phase_summary["primary_contact_start_s"]
    contact_release_s = phase_summary["primary_contact_release_s"]
    rejoin_s = phase_summary["rejoin_time_s"]
    post_contact_end_s = grasp_time_s if rejoin_s is None else min(float(rejoin_s), grasp_time_s)
    post_contact_mask = (
        np.zeros_like(arrays["time"], dtype=bool)
        if contact_start_s is None
        else (arrays["time"] >= float(contact_start_s)) & (arrays["time"] <= post_contact_end_s)
    )
    if not np.any(post_contact_mask):
        post_contact_mask = perturbation_mask | recovery_mask
    recovery_iae = _safe_scalar(np.trapezoid(arrays["track_position"][recovery_mask], arrays["time"][recovery_mask]))
    post_release_peak_error = _safe_scalar(np.max(arrays["track_position"][recovery_mask]))
    torque_abs = np.abs(arrays["torque_applied"])
    torque_rate = np.diff(arrays["torque_applied"], axis=0) / CONTROL_DT
    summary = {
        "kappa": float(kappa_vector[0]) if np.allclose(kappa_vector, kappa_vector[0]) else None,
        "kappa_vector": kappa_vector.tolist(),
        "config": asdict(config),
        "scenario": "physical rod perturbation during open-gripper grasp approach; compliant return to moving nominal trajectory tube",
        "reference": "fixed-base Panda WBC output is supplied to the low-level compliance layer" if fixed_wbc is not None else "finite grasp trajectory proxy (moving attractor, not a mathematical limit cycle); replace with fixed WBC pose/twist for WBC+VMC",
        "wbc_interface": {
            "source": "fixed_base_panda_resolved_rate_wbc_v1" if fixed_wbc is not None else "trajectory_proxy",
            "fixed_wbc": fixed_wbc is not None,
            "contract": "per-tick planned SE(3) target -> bounded WBC pose target/task twist/joint velocity -> low-level compliance torque layer",
            "wbc_may_not_read": "rod state, contact flag, contact force, obstacle state, or future release time",
            "compliance_may_not_modify": "WBC target generation or high-level task plan",
        },
        "controller": {
            "mode": controller_mode,
            "description": {
                "rigid": "direct high-stiffness bounded Cartesian tracking of the nominal reference",
                "impedance": "fixed bounded Cartesian spring-damper tracking of the nominal reference",
                "vmc": "virtual-mechanism compliant controller; optional explicit MuJoCo virtual carriage",
                "vmc_gated": "six-spring VMC with a causal measured-error held return-drive gate",
                "vmc_taper": "six-spring VMC with a causal measured-error gate and smooth terminal taper",
                "vmc_energy": "six-spring VMC with causal error gate, direction smoothing, and an energy-budget safety filter on recovery-drive increment",
            }[controller_mode],
        },
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
            "collision_removed_when_disabled": bool(not rod_enabled and remove_rod_when_disabled),
            "start_time_s": rod_start_time_s,
            "profile_duration_s": ROD_END_TIME_S - ROD_START_TIME_S,
            "cycles": rod_cycles,
            "cycle_period_s": rod_cycle_period_s,
            "final_end_time_s": rod_final_release_s,
            "stroke_m": rod_stroke_m,
            "height_m": rod_height_m,
            "center_x_m": rod_center_x_m,
            "center_y_m": rod_center_y_m,
            "approach_side": rod_approach_side,
            "support_position_m": list(approach_geometry.support_position_m),
            "slide_axis_world": list(approach_geometry.slide_axis_world),
            "rod_long_axis_world": list(approach_geometry.rod_long_axis_world),
            "cylinder_quaternion_wxyz": list(approach_geometry.cylinder_quaternion_wxyz),
            "physical_geometry": "finite-mass cylinder on a position-actuated MuJoCo slide; no mocap teleport",
        },
        "stiffness_schedule": {
            "contact_kappa_vector": kappa_vector.tolist(),
            "recovery_kappa_vector": recovery_kappa_vector.tolist(),
            "shared_six_channel_contact_kappa": float(kappa_vector[0]) if np.allclose(kappa_vector, kappa_vector[0]) else None,
            "shared_six_channel_recovery_kappa": float(recovery_kappa_vector[0]) if np.allclose(recovery_kappa_vector, recovery_kappa_vector[0]) else None,
            "recovery_ramp_start_s": rod_final_release_s,
            "recovery_ramp_duration_s": recovery_ramp_s,
            "recovery_carriage_drive_scale_factor": recovery_drive_scale_factor,
            "causal_recovery_gate": {
                "enabled": controller_mode in ("vmc_gated", "vmc_taper", "vmc_energy"),
                "hold_s": recovery_gate_hold_s if controller_mode in ("vmc_gated", "vmc_taper", "vmc_energy") else None,
                "taper_s": recovery_gate_taper_s if controller_mode in ("vmc_taper", "vmc_energy") else None,
                "mean_gate": _safe_scalar(np.mean(arrays["recovery_gate"])),
                "uses_contact_or_future_release": False,
            },
            "energy_budget_safety": {
                "enabled": energy_safety is not None,
                "configuration": None if energy_safety is None else asdict(energy_safety.config),
                "mean_tank_energy_j": _safe_scalar(np.mean(arrays["energy_tank_j"])) if energy_safety is not None else None,
                "minimum_tank_energy_j": _safe_scalar(np.min(arrays["energy_tank_j"])) if energy_safety is not None else None,
                "mean_direction_scale": _safe_scalar(np.mean(arrays["energy_direction_scale"])) if energy_safety is not None else None,
                "mean_energy_scale": _safe_scalar(np.mean(arrays["energy_scale"])) if energy_safety is not None else None,
                "uses_contact_or_future_release": False,
                "claim": "energy-budget / passivity-inspired constraint on the incremental return drive; not a global passivity proof for the moving-reference robot",
            },
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
            "recovery_iae_m_s": recovery_iae,
            "post_release_peak_error_m": post_release_peak_error,
            "post_release_rebound_ratio": post_release_peak_error / max(release_error, EPS),
            "pregrasp_position_error_m": pregrasp_error,
            "final_position_error_m": _safe_scalar(arrays["track_position"][-1]),
        },
        "motion": {
            "recovery_speed_p95_mps": _safe_scalar(np.quantile(arrays["ee_speed"][recovery_mask], 0.95)),
            "post_contact_speed_peak_mps": _safe_scalar(np.max(arrays["ee_speed"][post_contact_mask])),
            "post_contact_speed_p95_mps": _safe_scalar(np.quantile(arrays["ee_speed"][post_contact_mask], 0.95)),
            "forward_surge_max_mps": _safe_scalar(np.max(arrays["surge"][perturbation_mask | recovery_mask])),
            "acceleration_peak_mps2": _safe_scalar(np.max(arrays["acceleration"][perturbation_mask | recovery_mask])),
            "jerk_peak_mps3": _safe_scalar(np.max(arrays["jerk"][perturbation_mask | recovery_mask])),
            "post_contact_jerk_p95_mps3": _safe_scalar(np.quantile(arrays["jerk"][post_contact_mask], 0.95)),
        },
        "torque": {
            "applied_peak_nm": _safe_scalar(np.max(np.abs(arrays["torque_applied"]))),
            "applied_peak_ratio": _safe_scalar(np.max(arrays["torque_ratio"])),
            "applied_rms_nm": _safe_scalar(np.sqrt(np.mean(torque_abs**2))),
            "applied_p95_nm": _safe_scalar(np.quantile(torque_abs, 0.95)),
            "torque_rate_peak_nmps": _safe_scalar(np.max(np.abs(torque_rate))),
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
        "phase_analysis": phase_summary,
        "gif": str(gif_path) if gif_path else None,
    }
    # Preserve the legacy scalar filename so baseline_ladder and existing
    # figures remain reproducible; vector runs receive an explicit kvec stem.
    file_tag = kappa_filename_tag(kappa if np.asarray(kappa).ndim == 0 else kappa_vector)
    np.savez_compressed(output_dir / f"rod_perturbation_{file_tag}_trace.npz", **arrays)
    (output_dir / f"rod_perturbation_{file_tag}_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--reference-source", choices=REFERENCE_SOURCES, default="proxy",
        help="Reference provider: legacy trajectory proxy or the fixed-base Panda WBC command adapter.",
    )
    parser.add_argument(
        "--controller-mode", choices=CONTROLLER_MODES, default="vmc",
        help="Low-level baseline: direct rigid tracking, fixed Cartesian impedance, or virtual-mechanism VMC.",
    )
    parser.add_argument("--kappas", type=float, nargs="+", default=[1.0])
    parser.add_argument(
        "--kappa-vector", type=float, nargs=6, default=None, metavar=("KX", "KY", "KZ", "KROLL", "KPITCH", "KYAW"),
        help="Independent contact-stage stiffness multipliers [x y z roll pitch yaw]. Overrides --kappas.",
    )
    parser.add_argument("--damping-ratio", type=float, default=1.8)
    parser.add_argument("--carriage-drive-scale", type=float, default=0.75)
    parser.add_argument("--carriage-drive-damping-ratio", type=float, default=2.0)
    parser.add_argument("--contact-time-constant", type=float, default=DEFAULT_CONTACT_TIME_CONSTANT_S)
    parser.add_argument("--rod-stroke", type=float, default=0.16)
    parser.add_argument(
        "--rod-height", type=float, default=0.540,
        help="World z height of the rod axis; use this to test impact geometry while keeping the same rod profile.",
    )
    parser.add_argument("--rod-center-x", type=float, default=0.55, help="World x coordinate of the rod interaction plane for y/z approaches.")
    parser.add_argument("--rod-center-y", type=float, default=0.0, help="World y coordinate of the rod interaction plane for x/z approaches.")
    parser.add_argument(
        "--rod-approach-side", choices=ROD_APPROACH_SIDES, default="negative_y",
        help="Physical side from which the finite-mass rod slides into the hand.",
    )
    parser.add_argument(
        "--recovery-kappa", type=float, default=None,
        help="Shared six-channel stiffness after rod retraction; default keeps constant stiffness.",
    )
    parser.add_argument(
        "--recovery-kappa-vector", type=float, nargs=6, default=None, metavar=("KX", "KY", "KZ", "KROLL", "KPITCH", "KYAW"),
        help="Independent recovery-stage stiffness multipliers; default keeps the contact vector.",
    )
    parser.add_argument("--recovery-ramp", type=float, default=0.16, help="Seconds to smoothly ramp from contact to recovery stiffness.")
    parser.add_argument("--recovery-gate-hold-s", type=float, default=0.28, help="Causal measured-error hold duration for vmc_gated/vmc_taper.")
    parser.add_argument("--recovery-gate-taper-s", type=float, default=0.04, help="Smooth terminal held-gate taper for vmc_taper.")
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
    parser.add_argument("--remove-rod-when-disabled", action="store_true", help="When --disable-rod, remove rod collision geometry for a clean no-rod reference.")
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
    if min(positive_scales) <= 0 or not np.all(np.isfinite((args.rod_center_x, args.rod_center_y))) or args.rod_stroke < 0 or args.recovery_ramp < 0 or args.recovery_gate_hold_s < 0 or args.recovery_gate_taper_s < 0 or args.rod_cycles < 1 or args.rod_cycle_period < ROD_END_TIME_S - ROD_START_TIME_S or not ROD_END_TIME_S < args.grasp_time < LIFT_COMPLETE_TIME_S or (args.recovery_kappa is not None and args.recovery_kappa <= 0) or (args.kappa_vector is not None and (not np.all(np.isfinite(args.kappa_vector)) or min(args.kappa_vector) <= 0)) or (args.recovery_kappa_vector is not None and (not np.all(np.isfinite(args.recovery_kappa_vector)) or min(args.recovery_kappa_vector) <= 0)) or (args.recovery_carriage_drive_scale is not None and args.recovery_carriage_drive_scale <= 0) or (args.explicit_rotational_carriage and not args.explicit_translational_carriage):
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
    contact_runs = [np.asarray(args.kappa_vector, dtype=float)] if args.kappa_vector is not None else args.kappas
    recovery_kappa = np.asarray(args.recovery_kappa_vector, dtype=float) if args.recovery_kappa_vector is not None else args.recovery_kappa
    runs = [
        run_episode(
            args.menagerie, kappa, args.output_dir, args.render_gif, config,
            args.rod_stroke, args.contact_time_constant, rod_enabled=not args.disable_rod,
            remove_rod_when_disabled=args.remove_rod_when_disabled,
            playback_speed=args.playback_speed, camera_view=args.camera_view,
            render_start_time_s=args.render_start_time, render_end_time_s=args.render_end_time,
            recovery_kappa=recovery_kappa, recovery_ramp_s=args.recovery_ramp,
            recovery_drive_scale_factor=recovery_drive_scale_factor,
            grasp_time_s=args.grasp_time,
            rod_start_time_s=args.rod_start_time, rod_cycles=args.rod_cycles,
            rod_cycle_period_s=args.rod_cycle_period, response_only=args.response_only,
            explicit_translational_carriage=args.explicit_translational_carriage,
            carriage_mass_kg=args.carriage_mass_kg,
            rod_height_m=args.rod_height,
            rod_center_x_m=args.rod_center_x,
            rod_center_y_m=args.rod_center_y,
            explicit_rotational_carriage=args.explicit_rotational_carriage,
            rotational_carriage_inertia_scale=args.rotational_carriage_inertia_scale,
            rotational_damping_ratio=args.rotational_damping_ratio,
            controller_mode=args.controller_mode,
            rod_approach_side=args.rod_approach_side,
            recovery_gate_hold_s=args.recovery_gate_hold_s,
            recovery_gate_taper_s=args.recovery_gate_taper_s,
            reference_source=args.reference_source,
        )
        for kappa in contact_runs
    ]
    matrix = {"protocol": {key: value for key, value in vars(args).items() if key not in {"menagerie", "output_dir"}}, "runs": runs}
    (args.output_dir / "evaluation_matrix.json").write_text(json.dumps(matrix, indent=2) + "\n")
    print(json.dumps(matrix, indent=2))


if __name__ == "__main__":
    os.environ.setdefault("MUJOCO_GL", "egl")
    main()
