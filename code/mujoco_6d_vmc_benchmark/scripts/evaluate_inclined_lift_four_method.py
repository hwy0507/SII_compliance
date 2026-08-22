#!/usr/bin/env python3
"""Held-out physical inclined-board comparison: PaperMPC, VMC, MLP, ESN.

All learned methods use the same 32-D proprioceptive/WBC observation.  Board
contact measurements are collected only as evaluation metadata to verify that
the arm really touches and slides along the MuJoCo plank.
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

from mlp_compliance_baseline import MLPComplianceController  # noqa: E402
from run_benchmark import TORQUE_LIMITS  # noqa: E402
from vmc_compliance_baseline import SpringCarriageConfig, load_controller  # noqa: E402
from vmc_torque_baseline import VMCTorqueBaseline  # noqa: E402
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv, VelocityResidualFixture  # noqa: E402


def fixture(seed: int) -> VelocityResidualFixture:
    rng = np.random.default_rng(seed)
    return VelocityResidualFixture(
        rod_stroke_m=float(rng.uniform(0.165, 0.175)),
        rod_height_m=float(rng.uniform(0.539, 0.542)),
        rod_start_time_s=99.0, grasp_time_s=2.4,
        rod_approach_side="negative_y", impactor_type="rod",
        rod_cycles=1, cycle_period_s=0.8, contact_time_constant_s=0.015,
    )


def make_vmc(budget: float) -> VMCTorqueBaseline:
    base = SpringCarriageConfig(k_translation_base=2.2, k_rotation_base=0.18)
    cfg = replace(base, k_translation_base=1.0,
                  k_rotation_base=base.k_rotation_base / base.k_translation_base)
    return VMCTorqueBaseline(cfg, TORQUE_LIMITS * budget)


def board_incidence(env: PandaWBCVelocityResidualEnv, board_id: int,
                    hand_twist: np.ndarray) -> tuple[float, float, float]:
    rot = np.asarray(env.data.geom_xmat[board_id], dtype=float).reshape(3, 3)
    normal = rot[:, 2]
    normal /= max(float(np.linalg.norm(normal)), 1e-12)
    velocity = np.asarray(hand_twist[:3], dtype=float)
    normal_speed = abs(float(np.dot(velocity, normal)))
    tangent_speed = float(np.linalg.norm(velocity - np.dot(velocity, normal) * normal))
    fraction = normal_speed / max(float(np.linalg.norm(velocity)), 1e-12)
    return normal_speed, tangent_speed, fraction


def run_one(menagerie: Path, label: str, controller, *, seed: int, tilt: float,
            budget: float, board_y_offset_m: float, board_yaw_deg: float,
            contact_mode: str) -> dict:
    fx = fixture(seed)
    env = PandaWBCVelocityResidualEnv(
        menagerie=menagerie, fan_ye_model_npz=None, fan_ye_train_summary_json=None,
        observation_mode="direct_esn", rod_enabled=False, robot="fr3", seed=seed,
        execution_mode="torque_residual", residual_torque_scale=budget,
        wbc_backend="paper_mpc", fixtures=(fx,), lift_board_tilt_deg=float(tilt),
        lift_board_y_offset_m=float(board_y_offset_m),
        lift_board_yaw_deg=float(board_yaw_deg),
        lift_board_contact_mode=contact_mode,
    )
    env.reset(seed=seed, options={"fixture_index": 0})
    if controller is not None and hasattr(controller, "reset"):
        controller.reset()
    rows = []
    board_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "lift_board")
    done, info = False, {}
    while not done:
        d = env.diagnostics()
        board_contact, board_force = env._lift_board_contact_diagnostics()
        hand = np.asarray(d["ee_position"])
        nominal = np.asarray(d["nominal_position"])
        normal_speed, tangent_speed, normal_fraction = board_incidence(
            env, board_id, np.asarray(d["ee_twist"])
        )
        rows.append({
            "t": float(d["time_s"]), "board_contact": bool(board_contact),
            "board_force_n": float(board_force),
            "hand_y_m": float(hand[1]), "nominal_y_m": float(nominal[1]),
            "y_dodge_m": float(hand[1] - nominal[1]),
            "pose_error_m": float(np.linalg.norm(d["wbc_pose_error"][:3])),
            "normal_speed_mps": normal_speed,
            "tangent_speed_mps": tangent_speed,
            "normal_speed_fraction": normal_fraction,
        })
        if controller is None:
            action = np.zeros(7)
        elif hasattr(controller, "baseline") and hasattr(controller, "residual_torque_limits"):
            action = controller.act(
                d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                hand_jacobian=d["hand_jacobian"], pose_error=d["wbc_pose_error"],
                twist_error=d["wbc_twist_error"]).bounded_filter_action
        else:
            action = controller.act(
                d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"]).bounded_filter_action
        _, _, done, _, info = env.step(action)
    active = [r for r in rows if r["board_contact"]]
    first_active = active[0] if active else None
    peak_post = max((r["pose_error_m"] for r in rows if active and r["t"] >= active[0]["t"]), default=0.0)
    result = {
        "method": label, "seed": int(seed), "tilt_deg": float(tilt),
        "board_y_offset_m": float(board_y_offset_m),
        "board_yaw_deg": float(board_yaw_deg),
        "contact_mode": contact_mode,
        "task_success": bool(info.get("task_success", False)),
        "hard_torque_limit": bool(info.get("hard_torque_limit", False)),
        "finite_state": bool(info.get("finite_state", False)),
        "peak_torque_nm": float(info.get("peak_torque_nm", np.nan)),
        "first_board_contact_s": info.get("lift_board_first_contact_s"),
        "board_contact_duration_s": float(info.get("lift_board_contact_duration_s", 0.0)),
        "board_contact_impulse_ns": float(info.get("lift_board_contact_impulse_ns", 0.0)),
        "board_peak_force_n": float(info.get("lift_board_peak_force_n", 0.0)),
        "board_contact_bout_count": int(info.get("lift_board_contact_bout_count", 0)),
        "first_contact_normal_speed_mps": (float(first_active["normal_speed_mps"])
                                            if first_active is not None else None),
        "first_contact_tangent_speed_mps": (float(first_active["tangent_speed_mps"])
                                             if first_active is not None else None),
        "first_contact_normal_speed_fraction": (float(first_active["normal_speed_fraction"])
                                                 if first_active is not None else None),
        "geometry_valid_postgrasp": bool(
            first_active is not None and float(first_active["t"]) >= fx.grasp_time_s
        ),
        "max_y_dodge_mm": float(max((r["y_dodge_m"] for r in rows), default=0.0) * 1000.0),
        "contact_y_dodge_mm": float(max((r["y_dodge_m"] for r in active), default=0.0) * 1000.0),
        "peak_postcontact_error_mm": float(peak_post * 1000.0),
        "rows": rows,
    }
    env.close()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--esn", type=Path, required=True)
    parser.add_argument("--mlp", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[20262201, 20262202, 20262203])
    parser.add_argument("--tilts", type=float, nargs="+", default=[35.0, 40.0])
    parser.add_argument("--yaws", type=float, nargs="+", default=[0.0],
                        help="board yaw angles about world z; 0 is the original side-contact orientation")
    parser.add_argument("--contact-mode", choices=("side_slide", "front_face", "front_longitudinal"), default="side_slide")
    parser.add_argument("--esn-budget", type=float, default=0.02)
    parser.add_argument("--mlp-budget", type=float, default=0.02)
    parser.add_argument("--vmc-budget", type=float, default=0.02)
    args = parser.parse_args()
    methods = [
        ("PaperMPC", None, args.vmc_budget),
        ("VMC", make_vmc(args.vmc_budget), args.vmc_budget),
        ("MLP_inclined", MLPComplianceController.from_npz(args.mlp), args.mlp_budget),
        ("ESN_inclined", load_controller(args.esn), args.esn_budget),
    ]
    rows = []
    for label, controller, budget in methods:
        for tilt in args.tilts:
            for yaw in args.yaws:
                for seed in args.seeds:
                    if controller is not None and hasattr(controller, "reset"):
                        controller.reset()
                    offset = float(np.random.default_rng(seed * 1009 + int(round(tilt * 10)) + int(round(yaw * 100))).uniform(-0.008, 0.008))
                    rows.append(run_one(args.menagerie, label, controller, seed=seed,
                                        tilt=tilt, budget=budget, board_y_offset_m=offset,
                                        board_yaw_deg=yaw, contact_mode=args.contact_mode))
                    print(json.dumps({k: rows[-1][k] for k in rows[-1] if k != "rows"}), flush=True)
    summary = {}
    for label, _, _ in methods:
        group = [r for r in rows if r["method"] == label]
        valid = [r for r in group if r["geometry_valid_postgrasp"]]
        summary[label] = {
            "count": len(group),
            "success_count": int(sum(r["task_success"] for r in group)),
            "success_rate": float(np.mean([r["task_success"] for r in group])),
            "board_contact_rate": float(np.mean([r["board_contact_bout_count"] > 0 for r in group])),
            "mean_board_peak_force_n": float(np.mean([r["board_peak_force_n"] for r in group])),
            "mean_board_impulse_ns": float(np.mean([r["board_contact_impulse_ns"] for r in group])),
            "mean_contact_y_dodge_mm": float(np.mean([r["contact_y_dodge_mm"] for r in group])),
            "mean_peak_postcontact_error_mm": float(np.mean([r["peak_postcontact_error_mm"] for r in group])),
            "mean_peak_torque_nm": float(np.mean([r["peak_torque_nm"] for r in group])),
            "geometry_valid_postgrasp_rate": float(np.mean([r["geometry_valid_postgrasp"] for r in group])),
            "valid_geometry_success_rate": (float(np.mean([r["task_success"] for r in valid]))
                                             if valid else float("nan")),
        }
    output = {
        "schema_version": 1,
        "protocol": "inclined_lift_physical_contact_heldout",
        "observation_contract": "learned methods: q, qdot, nominal_twist, pose_error, wbc_twist_error (32-D); no board/contact truth",
        "board_geometry": "MuJoCo lift_board physical box; side_slide uses 0.18 x 0.05 x 0.008 m, front_face uses 0.24 x 0.24 x 0.008 m half-extents configured in the environment",
        "contact_mode": args.contact_mode,
        "angle_audit": "first-contact normal-speed fraction is |v_hand dot n_board| / ||v_hand||; contact/board quantities are offline only",
        "budgets": {"ESN": args.esn_budget, "MLP": args.mlp_budget, "VMC": args.vmc_budget},
        "summary": summary, "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"summary": summary}, indent=2))


if __name__ == "__main__":
    main()
