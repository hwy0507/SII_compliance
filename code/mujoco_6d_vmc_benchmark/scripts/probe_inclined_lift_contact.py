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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--mode", choices=("nominal", "vmc", "esn"), default="vmc")
    parser.add_argument("--esn", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20262001)
    args = parser.parse_args()
    if args.mode == "esn" and args.esn is None:
        raise SystemExit("--mode esn needs --esn")
    controller, budget = (None, 0.05) if args.mode == "nominal" else (
        (make_vmc(), 0.02) if args.mode == "vmc" else (load_controller(args.esn), 0.05))
    fixture = VelocityResidualFixture(0.170, 0.541, 99.0, impactor_type="rod")
    env = PandaWBCVelocityResidualEnv(
        menagerie=args.menagerie, fan_ye_model_npz=None, fan_ye_train_summary_json=None,
        observation_mode="direct_esn", rod_enabled=False, robot="fr3", seed=args.seed,
        execution_mode="torque_residual", residual_torque_scale=budget,
        wbc_backend="paper_mpc", fixtures=(fixture,), lift_board_tilt_deg=40.0,
    )
    env.reset(seed=args.seed, options={"fixture_index": 0})
    if controller is not None and hasattr(controller, "reset"):
        controller.reset()
    board_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "lift_board")
    rows, done = [], False
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
        rows.append({
            "t": float(d["time_s"]), "board_force_n": force,
            "hand_position_m": d["ee_position"].tolist(),
            "hand_twist_mps": d["ee_twist"][:3].tolist(),
            "nominal_position_m": d["nominal_position"].tolist(),
            "pose_error_m": d["wbc_pose_error"][:3].tolist(),
            "action": np.asarray(action).tolist(),
        })
        _, _, done, _, info = env.step(action)
    env.close()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"mode": args.mode, "budget": budget, "rows": rows,
                                    "terminal": info}, indent=2) + "\n")
    active = [row for row in rows if row["board_force_n"] > 1.0]
    print(json.dumps({"rows": len(rows), "contact_rows": len(active),
        "first_contact_s": active[0]["t"] if active else None,
        "peak_force_n": max((row["board_force_n"] for row in rows), default=0.0),
        "terminal": info}, indent=2))


if __name__ == "__main__":
    main()
