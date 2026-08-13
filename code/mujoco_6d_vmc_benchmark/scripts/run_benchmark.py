#!/usr/bin/env python3
"""Run a fixed-reference 6D end-effector VMC stiffness sweep in MuJoCo.

The script purposefully keeps the reference source separate from the virtual
model controller.  It is therefore usable first with the deterministic
reaching proxy below and later with a cached or live fixed-WBC reference.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import imageio.v3 as iio
import mujoco
import numpy as np


ARM_DOF = 7
CONTROL_DT = 0.004
SIM_TIME_S = 7.0
INTERVENTION_TIME_S = 2.2
RENDER_FPS = 25
EPS = 1e-9

# Conservative arm torque limits used by the torque controller.  The first
# four values follow the standard Panda joint capability; distal values are
# intentionally conservative for this first stability benchmark.
TORQUE_LIMITS = np.array([87.0, 87.0, 87.0, 87.0, 12.0, 12.0, 12.0])


def _skew(vector: np.ndarray) -> np.ndarray:
    x, y, z = vector
    return np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])


def so3_log(rotation: np.ndarray) -> np.ndarray:
    """Return the principal rotation vector for a 3x3 rotation matrix."""

    cosine = float(np.clip((np.trace(rotation) - 1.0) * 0.5, -1.0, 1.0))
    angle = math.acos(cosine)
    if angle < 1e-7:
        return np.array(
            [rotation[2, 1] - rotation[1, 2], rotation[0, 2] - rotation[2, 0], rotation[1, 0] - rotation[0, 1]]
        ) * 0.5
    axis = np.array(
        [rotation[2, 1] - rotation[1, 2], rotation[0, 2] - rotation[2, 0], rotation[1, 0] - rotation[0, 1]]
    ) / (2.0 * math.sin(angle))
    return angle * axis


def integrate_orientation(rotation: np.ndarray, angular_velocity: np.ndarray, dt: float) -> np.ndarray:
    """First-order SO(3) integration, adequate at this small fixed dt."""

    theta = float(np.linalg.norm(angular_velocity) * dt)
    if theta < 1e-10:
        return rotation
    axis = angular_velocity / (np.linalg.norm(angular_velocity) + EPS)
    update = np.eye(3) + math.sin(theta) * _skew(axis) + (1.0 - math.cos(theta)) * (_skew(axis) @ _skew(axis))
    return update @ rotation


def saturated_spring(stiffness: np.ndarray, saturation: np.ndarray, error: np.ndarray) -> np.ndarray:
    return saturation * np.tanh(stiffness * error / saturation)


@dataclass(frozen=True)
class VMCConfig:
    """Physical baseline values before the single ``kappa`` multiplier."""

    k_translation_base: float = 220.0  # N/m
    k_rotation_base: float = 18.0  # Nm/rad
    zeta: float = 1.05
    virtual_mass: float = 1.25  # kg per translation direction
    virtual_inertia: float = 0.08  # kg m^2 per rotational direction
    carriage_drive_k_translation: float = 75.0
    carriage_drive_k_rotation: float = 7.0
    carriage_drive_zeta: float = 1.15
    max_force: float = 32.0  # N per Cartesian channel
    max_moment: float = 5.0  # Nm per rotational channel
    max_carriage_speed: float = 0.55
    max_carriage_angular_speed: float = 1.25


class NominalReference:
    """Repeatable fixed-reference proxy to be replaced by fixed WBC output."""

    def __init__(self, start_position: np.ndarray, start_rotation: np.ndarray) -> None:
        self.start_position = start_position.copy()
        self.start_rotation = start_rotation.copy()
        self.goal_offset = np.array([0.22, -0.16, 0.11])
        self.rise_time = 1.4

    def sample(self, time_s: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        phase = float(np.clip(time_s / self.rise_time, 0.0, 1.0))
        blend = 3.0 * phase**2 - 2.0 * phase**3
        blend_dot = 0.0 if time_s >= self.rise_time else (6.0 * phase - 6.0 * phase**2) / self.rise_time
        position = self.start_position + blend * self.goal_offset
        velocity = blend_dot * self.goal_offset
        return position, self.start_rotation, velocity, np.zeros(3)


class SixDVirtualCarriage:
    """Six nonlinear virtual springs coupled through the physical arm."""

    def __init__(self, config: VMCConfig, kappa: float, position: np.ndarray, rotation: np.ndarray) -> None:
        if kappa <= 0.0:
            raise ValueError("kappa must be positive")
        self.config = config
        self.kappa = float(kappa)
        self.position = position.copy()
        self.rotation = rotation.copy()
        self.linear_velocity = np.zeros(3)
        self.angular_velocity = np.zeros(3)

        self.mass = np.array([config.virtual_mass] * 3 + [config.virtual_inertia] * 3)
        self.stiffness = self.kappa * np.array([config.k_translation_base] * 3 + [config.k_rotation_base] * 3)
        self.damping = 2.0 * config.zeta * np.sqrt(self.mass * self.stiffness)
        self.saturation = np.array([config.max_force] * 3 + [config.max_moment] * 3)

        self.drive_stiffness = np.array([config.carriage_drive_k_translation] * 3 + [config.carriage_drive_k_rotation] * 3)
        self.drive_damping = 2.0 * config.carriage_drive_zeta * np.sqrt(self.mass * self.drive_stiffness)

    def wrench(self, ee_position: np.ndarray, ee_rotation: np.ndarray, ee_twist: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        rotation_error = so3_log(ee_rotation.T @ self.rotation)
        displacement = np.concatenate([self.position - ee_position, rotation_error])
        velocity_error = np.concatenate([self.linear_velocity, self.angular_velocity]) - ee_twist
        return saturated_spring(self.stiffness, self.saturation, displacement) + self.damping * velocity_error, displacement

    def advance(
        self,
        dt: float,
        nominal_position: np.ndarray,
        nominal_rotation: np.ndarray,
        nominal_twist: np.ndarray,
        wrench_on_robot: np.ndarray,
    ) -> None:
        rotation_error = so3_log(self.rotation.T @ nominal_rotation)
        displacement = np.concatenate([nominal_position - self.position, rotation_error])
        velocity_error = nominal_twist - np.concatenate([self.linear_velocity, self.angular_velocity])
        drive = self.drive_stiffness * displacement + self.drive_damping * velocity_error
        acceleration = (drive - wrench_on_robot) / self.mass
        self.linear_velocity += dt * acceleration[:3]
        self.angular_velocity += dt * acceleration[3:]
        self.linear_velocity = np.clip(self.linear_velocity, -self.config.max_carriage_speed, self.config.max_carriage_speed)
        self.angular_velocity = np.clip(self.angular_velocity, -self.config.max_carriage_angular_speed, self.config.max_carriage_angular_speed)
        self.position += dt * self.linear_velocity
        self.rotation = integrate_orientation(self.rotation, self.angular_velocity, dt)


def _torque_actuated_xml(menagerie: Path) -> str:
    """Reuse the official Panda geometry while replacing only arm actuation."""

    panda_path = menagerie / "franka_emika_panda" / "panda.xml"
    text = panda_path.read_text()
    torque_actuators = "\n".join(
        f'<motor name="torque_{index}" joint="joint{index}" ctrllimited="true" ctrlrange="{-limit:g} {limit:g}" forcelimited="true" forcerange="{-limit:g} {limit:g}"/>'
        for index, limit in enumerate(TORQUE_LIMITS, start=1)
    )
    replacement = f"<actuator>\n{torque_actuators}\n</actuator>\n\n  <keyframe>"
    text, count = re.subn(r"<actuator>.*?</actuator>\s*<keyframe>", replacement, text, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError("could not replace the official Panda actuator block")
    # The official home keyframe includes eight position-actuator controls.
    # Arm-only torque actuation has seven controls, so retain the initial qpos
    # but remove the now invalid actuator-control vector.
    text = re.sub(r'(<key\b[^>]*?)\sctrl="[^"]*"', r"\1", text)
    # The include needs to live alongside official meshes so retain its relative
    # asset resolution.  Add a mocap obstacle and carriage visual to worldbody.
    injected = """
      <body name="moving_obstacle" mocap="true" pos="0 0 1">
        <geom name="moving_obstacle_geom" type="sphere" size="0.070" mass="0" rgba="0.85 0.12 0.12 0.92" friction="0.9 0.05 0.02"/>
      </body>
      <body name="virtual_carriage" mocap="true" pos="0 0 1">
        <geom name="virtual_carriage_geom" type="sphere" size="0.028" mass="0" contype="0" conaffinity="0" rgba="0.10 0.85 0.95 0.65"/>
      </body>
    """
    text = text.replace("  </worldbody>", injected + "  </worldbody>", 1)
    text = text.replace('<option integrator="implicitfast"/>', '<option integrator="implicitfast" timestep="0.004" gravity="0 0 -9.81"/>')
    return text


def make_model(menagerie: Path) -> tuple[mujoco.MjModel, mujoco.MjData]:
    xml = _torque_actuated_xml(menagerie)
    panda_dir = menagerie / "franka_emika_panda"
    assets_dir = panda_dir / "assets"
    assets = {
        str(path.relative_to(assets_dir)): path.read_bytes()
        for path in assets_dir.rglob("*")
        if path.is_file()
    }
    model = mujoco.MjModel.from_xml_string(xml, assets=assets)
    model.opt.timestep = CONTROL_DT
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)
    return model, data


def body_twist(model: mujoco.MjModel, data: mujoco.MjData, body_id: int) -> np.ndarray:
    jac_position = np.zeros((3, model.nv))
    jac_rotation = np.zeros((3, model.nv))
    mujoco.mj_jacBody(model, data, jac_position, jac_rotation, body_id)
    return np.concatenate([jac_position[:, :ARM_DOF] @ data.qvel[:ARM_DOF], jac_rotation[:, :ARM_DOF] @ data.qvel[:ARM_DOF]])


def body_jacobian(model: mujoco.MjModel, data: mujoco.MjData, body_id: int) -> np.ndarray:
    jac_position = np.zeros((3, model.nv))
    jac_rotation = np.zeros((3, model.nv))
    mujoco.mj_jacBody(model, data, jac_position, jac_rotation, body_id)
    return np.vstack([jac_position[:, :ARM_DOF], jac_rotation[:, :ARM_DOF]])


def contact_diagnostics(model: mujoco.MjModel, data: mujoco.MjData, obstacle_geom_id: int) -> tuple[bool, float, float]:
    touching = False
    force_norm = 0.0
    max_penetration = 0.0
    contact_force = np.zeros(6)
    for index in range(data.ncon):
        contact = data.contact[index]
        if contact.geom1 != obstacle_geom_id and contact.geom2 != obstacle_geom_id:
            continue
        touching = True
        mujoco.mj_contactForce(model, data, index, contact_force)
        force_norm = max(force_norm, float(np.linalg.norm(contact_force[:3])))
        max_penetration = max(max_penetration, max(0.0, -float(contact.dist)))
    return touching, force_norm, max_penetration


def obstacle_position(time_s: float, nominal_position: np.ndarray) -> np.ndarray:
    """A deterministic lateral crossing through the nominal end-effector path."""

    # It begins above the nominal path, crosses at intervention time, then
    # leaves.  This makes every kappa evaluation a paired experiment.
    center = nominal_position + np.array([0.0, 0.30 - 0.22 * (time_s - INTERVENTION_TIME_S), 0.015])
    if time_s < 1.35 or time_s > 4.10:
        center[1] = 2.0
    return center


def _safe_scalar(value: np.ndarray | float) -> float:
    return float(np.asarray(value))


def run_episode(menagerie: Path, kappa: float, render_gif: bool, output_dir: Path) -> dict[str, Any]:
    model, data = make_model(menagerie)
    hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "hand")
    obstacle_geom_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "moving_obstacle_geom")
    obstacle_mocap_id = model.body_mocapid[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "moving_obstacle")]
    carriage_mocap_id = model.body_mocapid[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "virtual_carriage")]
    if min(hand_id, obstacle_geom_id, obstacle_mocap_id, carriage_mocap_id) < 0:
        raise RuntimeError("required Panda body/visual IDs were not found")

    ee_position0 = data.xpos[hand_id].copy()
    ee_rotation0 = data.xmat[hand_id].reshape(3, 3).copy()
    nominal = NominalReference(ee_position0, ee_rotation0)
    controller = SixDVirtualCarriage(VMCConfig(), kappa, ee_position0, ee_rotation0)

    renderer: mujoco.Renderer | None = None
    frames: list[np.ndarray] = []
    if render_gif:
        renderer = mujoco.Renderer(model, height=480, width=640)
    render_stride = max(1, round(1.0 / (RENDER_FPS * CONTROL_DT)))

    log: dict[str, list[Any]] = {key: [] for key in (
        "time", "track_position", "track_orientation", "ee_speed", "nominal_speed", "surge", "acceleration", "jerk",
        "torque_command", "torque_applied", "torque_ratio", "contact", "contact_force", "penetration", "carriage_error",
    )}
    previous_twist = np.zeros(6)
    previous_acceleration = np.zeros(6)
    had_contact = False
    steps = int(SIM_TIME_S / CONTROL_DT)

    for step in range(steps):
        time_s = step * CONTROL_DT
        nominal_position, nominal_rotation, nominal_linear, nominal_angular = nominal.sample(time_s)
        nominal_twist = np.concatenate([nominal_linear, nominal_angular])
        data.mocap_pos[obstacle_mocap_id] = obstacle_position(time_s, nominal_position)
        data.mocap_quat[obstacle_mocap_id] = np.array([1.0, 0.0, 0.0, 0.0])
        data.mocap_pos[carriage_mocap_id] = controller.position
        data.mocap_quat[carriage_mocap_id] = np.array([1.0, 0.0, 0.0, 0.0])

        ee_position = data.xpos[hand_id].copy()
        ee_rotation = data.xmat[hand_id].reshape(3, 3).copy()
        ee_twist = body_twist(model, data, hand_id)
        wrench, carriage_error = controller.wrench(ee_position, ee_rotation, ee_twist)
        jacobian = body_jacobian(model, data, hand_id)
        requested_torque = data.qfrc_bias[:ARM_DOF].copy() + jacobian.T @ wrench
        applied_torque = np.clip(requested_torque, -TORQUE_LIMITS, TORQUE_LIMITS)
        data.ctrl[:ARM_DOF] = applied_torque
        controller.advance(CONTROL_DT, nominal_position, nominal_rotation, nominal_twist, wrench)
        mujoco.mj_step(model, data)

        contact, contact_force, penetration = contact_diagnostics(model, data, obstacle_geom_id)
        had_contact = had_contact or contact
        acceleration = (ee_twist - previous_twist) / CONTROL_DT
        jerk = (acceleration - previous_acceleration) / CONTROL_DT
        direction = nominal_linear / (np.linalg.norm(nominal_linear) + EPS)
        surge = max(0.0, float(np.dot(ee_twist[:3], direction) - np.linalg.norm(nominal_linear)))
        tracking_rotation = so3_log(nominal_rotation.T @ ee_rotation)

        log["time"].append(time_s)
        log["track_position"].append(float(np.linalg.norm(ee_position - nominal_position)))
        log["track_orientation"].append(float(np.linalg.norm(tracking_rotation)))
        log["ee_speed"].append(float(np.linalg.norm(ee_twist[:3])))
        log["nominal_speed"].append(float(np.linalg.norm(nominal_linear)))
        log["surge"].append(surge)
        log["acceleration"].append(float(np.linalg.norm(acceleration[:3])))
        log["jerk"].append(float(np.linalg.norm(jerk[:3])))
        log["torque_command"].append(requested_torque.tolist())
        log["torque_applied"].append(applied_torque.tolist())
        log["torque_ratio"].append(float(np.max(np.abs(applied_torque) / TORQUE_LIMITS)))
        log["contact"].append(contact)
        log["contact_force"].append(contact_force)
        log["penetration"].append(penetration)
        log["carriage_error"].append(carriage_error.tolist())
        previous_twist = ee_twist
        previous_acceleration = acceleration

        if renderer is not None and step % render_stride == 0:
            renderer.update_scene(data, camera="track")
            frames.append(renderer.render().copy())

    if renderer is not None:
        renderer.close()
        gif_path = output_dir / f"vmc_kappa_{kappa:.2f}.gif"
        iio.imwrite(gif_path, np.stack(frames), duration=1.0 / RENDER_FPS, loop=0)
    else:
        gif_path = None

    array_log = {name: np.asarray(values) for name, values in log.items()}
    post_mask = array_log["time"] >= INTERVENTION_TIME_S
    torque_command = array_log["torque_command"]
    torque_applied = array_log["torque_applied"]
    contact_mask = array_log["contact"].astype(bool)
    summary: dict[str, Any] = {
        "kappa": kappa,
        "config": asdict(VMCConfig()),
        "model": "official mujoco_menagerie/franka_emika_panda with torque actuators",
        "reference": "deterministic fixed end-effector reaching proxy; replaceable by fixed WBC reference",
        "intervention_time_s": INTERVENTION_TIME_S,
        "contact_observed": bool(had_contact),
        "tracking": {
            "post_intervention_position_rmse_m": _safe_scalar(np.sqrt(np.mean(array_log["track_position"][post_mask] ** 2))),
            "post_intervention_position_max_m": _safe_scalar(np.max(array_log["track_position"][post_mask])),
            "post_intervention_orientation_rmse_rad": _safe_scalar(np.sqrt(np.mean(array_log["track_orientation"][post_mask] ** 2))),
            "final_position_error_m": _safe_scalar(array_log["track_position"][-1]),
        },
        "motion": {
            "post_intervention_speed_p50_mps": _safe_scalar(np.quantile(array_log["ee_speed"][post_mask], 0.50)),
            "post_intervention_speed_p95_mps": _safe_scalar(np.quantile(array_log["ee_speed"][post_mask], 0.95)),
            "post_intervention_speed_max_mps": _safe_scalar(np.max(array_log["ee_speed"][post_mask])),
            "forward_surge_max_mps": _safe_scalar(np.max(array_log["surge"][post_mask])),
            "acceleration_peak_mps2": _safe_scalar(np.max(array_log["acceleration"][post_mask])),
            "jerk_peak_mps3": _safe_scalar(np.max(array_log["jerk"][post_mask])),
        },
        "torque": {
            "commanded_peak_nm": _safe_scalar(np.max(np.abs(torque_command))),
            "applied_peak_nm": _safe_scalar(np.max(np.abs(torque_applied))),
            "applied_peak_ratio": _safe_scalar(np.max(array_log["torque_ratio"])),
            "saturation_fraction": _safe_scalar(np.mean(np.isclose(np.abs(torque_command), TORQUE_LIMITS[None, :], rtol=0.0, atol=1e-5) | (np.abs(torque_command) > TORQUE_LIMITS[None, :]))),
        },
        "contact_diagnostics": {
            "duration_s": _safe_scalar(np.sum(contact_mask) * CONTROL_DT),
            "peak_force_n": _safe_scalar(np.max(array_log["contact_force"])),
            "impulse_ns": _safe_scalar(np.sum(array_log["contact_force"]) * CONTROL_DT),
            "max_penetration_m": _safe_scalar(np.max(array_log["penetration"])),
        },
        "gif": str(gif_path) if gif_path else None,
    }
    np.savez_compressed(output_dir / f"vmc_kappa_{kappa:.2f}_trace.npz", **array_log)
    (output_dir / f"vmc_kappa_{kappa:.2f}_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", required=True, type=Path, help="Path to mujoco_menagerie checkout")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--kappas", nargs="+", type=float, default=[0.3, 0.5, 0.75, 1.0, 1.5, 2.0])
    parser.add_argument("--render-gif", action="store_true", help="Render one GIF for every evaluated kappa")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not (args.menagerie / "franka_emika_panda" / "panda.xml").is_file():
        raise FileNotFoundError("--menagerie must contain franka_emika_panda/panda.xml")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summaries = [run_episode(args.menagerie, kappa, args.render_gif, args.output_dir) for kappa in args.kappas]
    matrix = {"protocol": {"control_dt_s": CONTROL_DT, "simulation_time_s": SIM_TIME_S}, "runs": summaries}
    (args.output_dir / "evaluation_matrix.json").write_text(json.dumps(matrix, indent=2) + "\n")
    print(json.dumps(matrix, indent=2))


if __name__ == "__main__":
    # EGL is supplied by the server run command; do not override a caller's
    # preferred backend (for example glfw during local debugging).
    os.environ.setdefault("MUJOCO_GL", "egl")
    main()
