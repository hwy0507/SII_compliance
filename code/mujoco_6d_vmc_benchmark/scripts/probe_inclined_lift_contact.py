#!/usr/bin/env python3
"""Inspect one frozen controller during a physical inclined-board lift.

This diagnostic deliberately records obstacle/force information only to audit
the MuJoCo scene and to design *offline teacher labels*.  None of these fields
are supplied to a deployed learned controller.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import mujoco
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_benchmark import TORQUE_LIMITS  # noqa: E402
from vmc_compliance_baseline import SpringCarriageConfig, load_controller  # noqa: E402
from vmc_torque_baseline import VMCTorqueBaseline  # noqa: E402
from mlp_compliance_baseline import MLPComplianceController  # noqa: E402
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv, VelocityResidualFixture  # noqa: E402


def make_vmc() -> VMCTorqueBaseline:
    base = SpringCarriageConfig(k_translation_base=2.2, k_rotation_base=0.18)
    cfg = replace(base, k_translation_base=1.0,
                  k_rotation_base=base.k_rotation_base / base.k_translation_base)
    return VMCTorqueBaseline(cfg, TORQUE_LIMITS * 0.02)


def board_contact_force(env, board_id: int) -> float:
    total = 0.0
    wrench = np.zeros(6)
    for index in range(env.data.ncon):
        contact = env.data.contact[index]
        if board_id not in (int(contact.geom1), int(contact.geom2)):
            continue
        mujoco.mj_contactForce(env.model, env.data, index, wrench)
        total += float(np.linalg.norm(wrench[:3]))
    return total


def board_incidence(env, board_id: int, hand_twist: np.ndarray) -> tuple[float, float, float, list[float]]:
    """Return normal speed, tangential speed, normal fraction and board normal.

    This is an offline geometry audit.  The sign of the normal is chosen only
    for a stable magnitude report; no contact/board quantity enters a policy.
    """
    rot = np.asarray(env.data.geom_xmat[board_id], dtype=float).reshape(3, 3)
    normal = rot[:, 2]
    normal /= max(float(np.linalg.norm(normal)), 1e-12)
    velocity = np.asarray(hand_twist[:3], dtype=float)
    normal_speed = abs(float(np.dot(velocity, normal)))
    tangent_speed = float(np.linalg.norm(velocity - np.dot(velocity, normal) * normal))
    total_speed = float(np.linalg.norm(velocity))
    fraction = normal_speed / max(total_speed, 1e-12)
    return normal_speed, tangent_speed, fraction, normal.tolist()


def board_contact_records(env, board_id: int) -> list[dict]:
    """Return contact-point geometry for offline anti-tunnelling auditing."""
    board_rotation = np.asarray(env.data.geom_xmat[board_id], dtype=float).reshape(3, 3)
    board_center = np.asarray(env.data.geom_xpos[board_id], dtype=float)
    board_normal = board_rotation[:, 2]
    records: list[dict] = []
    for index in range(env.data.ncon):
        contact = env.data.contact[index]
        if board_id not in (int(contact.geom1), int(contact.geom2)):
            continue
        other_id = int(contact.geom2) if int(contact.geom1) == board_id else int(contact.geom1)
        point = np.asarray(contact.pos, dtype=float)
        local = board_rotation.T @ (point - board_center)
        normal = np.asarray(contact.frame[:3], dtype=float)
        records.append({
            "contact_index": int(index),
            "other_geom": mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_GEOM, other_id),
            "position_m": point.tolist(),
            "board_local_m": local.tolist(),
            "distance_m": float(contact.dist),
            "normal_alignment": abs(float(np.dot(normal, board_normal))),
        })
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--mode", choices=("nominal", "vmc", "mlp", "esn"), default="vmc")
    parser.add_argument("--esn", type=Path)
    parser.add_argument("--mlp", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20262001)
    parser.add_argument("--tilt", type=float, default=40.0)
    parser.add_argument("--yaw", type=float, default=0.0,
                        help="board yaw about world z; geometry/audit parameter only")
    parser.add_argument("--contact-mode", choices=("side_slide", "front_face", "front_longitudinal"), default="side_slide")
    parser.add_argument("--board-y-offset", type=float, default=0.0,
                        help="scene-only board center-y jitter in metres")
    parser.add_argument("--board-z-offset", type=float, default=0.0,
                        help="front-face board-center height offset in metres")
    args = parser.parse_args()
    if args.mode == "esn" and args.esn is None:
        raise SystemExit("--mode esn needs --esn")
    if args.mode == "mlp" and args.mlp is None:
        raise SystemExit("--mode mlp needs --mlp")
    controller, budget = (None, 0.05) if args.mode == "nominal" else (
        (make_vmc(), 0.02) if args.mode == "vmc" else
        (MLPComplianceController.from_npz(args.mlp), 0.02) if args.mode == "mlp" else
        (load_controller(args.esn), 0.02))
    fixture = VelocityResidualFixture(0.170, 0.541, 99.0, impactor_type="rod")
    env = PandaWBCVelocityResidualEnv(
        menagerie=args.menagerie, fan_ye_model_npz=None, fan_ye_train_summary_json=None,
        observation_mode="direct_esn", rod_enabled=False, robot="fr3", seed=args.seed,
        execution_mode="torque_residual", residual_torque_scale=budget,
        wbc_backend="paper_mpc", fixtures=(fixture,), lift_board_tilt_deg=float(args.tilt),
        lift_board_yaw_deg=float(args.yaw),
        lift_board_y_offset_m=float(args.board_y_offset),
        lift_board_z_offset_m=float(args.board_z_offset),
        lift_board_contact_mode=args.contact_mode,
    )
    env.reset(seed=args.seed, options={"fixture_index": 0})
    if controller is not None and hasattr(controller, "reset"):
        controller.reset()
    board_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "lift_board")
    board_center = env.model.geom_pos[board_id].copy().tolist()
    board_half_extents = env.model.geom_size[board_id].copy()
    rows, done, all_contacts = [], False, []
    while not done:
        d = env.diagnostics()
        if controller is None:
            action = np.zeros(7)
        elif hasattr(controller, "baseline") and hasattr(controller, "residual_torque_limits"):
            action = controller.act(d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                hand_jacobian=d["hand_jacobian"], pose_error=d["wbc_pose_error"],
                twist_error=d["wbc_twist_error"]).bounded_filter_action
        else:
            action = controller.act(d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"]).bounded_filter_action
        force = board_contact_force(env, board_id)
        contacts = board_contact_records(env, board_id)
        all_contacts.extend({"t": float(d["time_s"]), **record} for record in contacts)
        normal_speed, tangent_speed, normal_fraction, board_normal = board_incidence(
            env, board_id, d["ee_twist"]
        )
        rows.append({
            "t": float(d["time_s"]), "board_force_n": force,
            "board_normal_world": board_normal,
            "normal_speed_mps": normal_speed,
            "tangent_speed_mps": tangent_speed,
            "normal_speed_fraction": normal_fraction,
            "hand_position_m": d["ee_position"].tolist(),
            "hand_collision_position_m": env.data.geom_xpos[env._hand_geom_id].copy().tolist(),
            "link7_collision_position_m": env.data.geom_xpos[mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "fr3_link7_collision")].copy().tolist(),
            "hand_collision_axes_world": np.asarray(env.data.geom_xmat[env._hand_geom_id], dtype=float).reshape(3, 3).tolist(),
            "hand_collision_half_extents_m": env.model.geom_size[env._hand_geom_id].copy().tolist(),
            "hand_twist_mps": d["ee_twist"][:3].tolist(),
            "nominal_position_m": d["nominal_position"].tolist(),
            "pose_error_m": d["wbc_pose_error"][:3].tolist(),
            "action": np.asarray(action).tolist(),
        })
        _, _, done, _, info = env.step(action)
    env.close()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"mode": args.mode, "budget": budget,
                                    "tilt_deg": float(args.tilt), "yaw_deg": float(args.yaw),
                                    "contact_mode": args.contact_mode,
                                    "board_y_offset_m": float(args.board_y_offset), "board_z_offset_m": float(args.board_z_offset),
                                    "board_center_m": board_center, "board_half_extents_m": board_half_extents.tolist(),
                                    "rows": rows, "board_contacts": all_contacts,
                                    "terminal": info}, indent=2) + "\n")
    active = [row for row in rows if row["board_force_n"] > 1.0]
    half_extents = np.asarray(board_half_extents, dtype=float)
    face_contacts = [record for record in all_contacts if abs(record["board_local_m"][0]) < 0.80 * half_extents[0]
                     and abs(record["board_local_m"][1]) < 0.70 * half_extents[1]
                     and record["normal_alignment"] > 0.70]
    max_penetration = max((-record["distance_m"] for record in all_contacts), default=0.0)
    print(json.dumps({"rows": len(rows), "contact_rows": len(active),
        "first_contact_s": active[0]["t"] if active else None,
        "first_contact_normal_speed_mps": active[0]["normal_speed_mps"] if active else None,
        "first_contact_tangent_speed_mps": active[0]["tangent_speed_mps"] if active else None,
        "first_contact_normal_speed_fraction": active[0]["normal_speed_fraction"] if active else None,
        "peak_force_n": max((row["board_force_n"] for row in rows), default=0.0),
        "contact_points": len(all_contacts), "broad_face_contact_points": len(face_contacts),
        "max_contact_penetration_m": max_penetration,
        "initial_board_contact": bool(all_contacts and all_contacts[0]["t"] < 2.40),
        "terminal": info}, indent=2))


if __name__ == "__main__":
    main()
