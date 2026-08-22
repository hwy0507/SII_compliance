#!/usr/bin/env python3
"""Fair four-method evaluation on the physical dual-board manipulation task."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from mlp_compliance_baseline import MLPComplianceController
from run_benchmark import TORQUE_LIMITS
from vmc_compliance_baseline import SpringCarriageConfig, load_controller
from vmc_torque_baseline import VMCTorqueBaseline
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv, VelocityResidualFixture


def fixture(seed: int) -> VelocityResidualFixture:
    rng = np.random.default_rng(seed)
    return VelocityResidualFixture(
        rod_stroke_m=float(rng.uniform(0.165, 0.175)),
        rod_height_m=float(rng.uniform(0.539, 0.542)),
        rod_start_time_s=99.0, grasp_time_s=2.4,
        contact_time_constant_s=float(rng.uniform(0.0135, 0.0165)),
    )


def make_vmc(budget: float, stiffness: float = 1.0) -> VMCTorqueBaseline:
    base = SpringCarriageConfig(k_translation_base=2.2, k_rotation_base=0.18)
    config = replace(
        base, k_translation_base=float(stiffness),
        k_rotation_base=base.k_rotation_base * float(stiffness) / base.k_translation_base,
    )
    return VMCTorqueBaseline(config, TORQUE_LIMITS * float(budget))


def controller_action(controller, diagnostics: dict[str, np.ndarray]) -> np.ndarray:
    if controller is None:
        return np.zeros(7)
    kwargs = {
        "pose_error": diagnostics["wbc_pose_error"],
        "twist_error": diagnostics["wbc_twist_error"],
    }
    if hasattr(controller, "baseline") and hasattr(controller, "residual_torque_limits"):
        kwargs["hand_jacobian"] = diagnostics["hand_jacobian"]
    return np.asarray(controller.act(
        diagnostics["joint_position"], diagnostics["joint_velocity"],
        diagnostics["nominal_twist"], **kwargs,
    ).bounded_filter_action, dtype=float)


def run_one(
    menagerie: Path, label: str, controller, *, seed: int, budget: float,
    board_y_offset_m: float = 0.0, board_z_offset_m: float = 0.0,
) -> dict[str, object]:
    env = PandaWBCVelocityResidualEnv(
        menagerie, None, None, "direct_esn", fixtures=(fixture(seed),), rod_enabled=False,
        robot="fr3", wbc_backend="paper_mpc", execution_mode="torque_residual",
        residual_torque_scale=budget, lift_board_tilt_deg=15.0,
        lift_board_contact_mode="dual_phase_longitudinal",
        lift_board_y_offset_m=board_y_offset_m, lift_board_z_offset_m=board_z_offset_m,
        seed=seed,
    )
    env.reset(seed=seed, options={"fixture_index": 0})
    if controller is not None and hasattr(controller, "reset"):
        controller.reset()
    done = False
    info: dict[str, object] = {}
    while not done:
        action = controller_action(controller, env.diagnostics())
        _, _, terminated, truncated, info = env.step(action)
        done = bool(terminated or truncated)
    boards = info["dual_board_metrics"]
    row: dict[str, object] = {
        "method": label, "seed": seed, "budget": budget,
        "board_y_offset_m": board_y_offset_m, "board_z_offset_m": board_z_offset_m,
        "task_success": bool(info["task_success"]),
        "dual_phase_geometry_valid": bool(info["dual_phase_geometry_valid"]),
        "initial_board_contact": bool(info["dual_initial_board_contacts"]),
        "finite_state": bool(info["finite_state"]),
        "hard_torque_limit": bool(info["hard_torque_limit"]),
        "final_target_lift_m": float(info["final_target_lift_m"]),
        "final_hand_target_distance_m": float(info["final_hand_target_distance_m"]),
        "peak_torque_nm": float(info["peak_torque_nm"]),
        "peak_jerk_mps3": float(info["peak_jerk_mps3"]),
        "pregrasp": boards["pregrasp_board"],
        "postgrasp": boards["postgrasp_board"],
    }
    env.close()
    return row


def aggregate(rows: list[dict[str, object]]) -> dict[str, float | int]:
    def mean(path: tuple[str, str] | str) -> float:
        if isinstance(path, str):
            values = [float(row[path]) for row in rows]
        else:
            values = [float(row[path[0]][path[1]]) for row in rows]
        return float(np.mean(values))

    return {
        "count": len(rows),
        "success_count": int(sum(bool(row["task_success"]) for row in rows)),
        "success_rate": float(np.mean([bool(row["task_success"]) for row in rows])),
        "geometry_valid_rate": float(np.mean([bool(row["dual_phase_geometry_valid"]) for row in rows])),
        "mean_pre_peak_force_n": mean(("pregrasp", "peak_force_n")),
        "mean_pre_impulse_ns": mean(("pregrasp", "contact_impulse_ns")),
        "mean_pre_max_penetration_mm": 1000.0 * mean(("pregrasp", "max_penetration_m")),
        "mean_post_peak_force_n": mean(("postgrasp", "peak_force_n")),
        "mean_post_impulse_ns": mean(("postgrasp", "contact_impulse_ns")),
        "mean_post_max_penetration_mm": 1000.0 * mean(("postgrasp", "max_penetration_m")),
        "mean_total_board_impulse_ns": mean(("pregrasp", "contact_impulse_ns"))
        + mean(("postgrasp", "contact_impulse_ns")),
        "mean_final_target_lift_mm": 1000.0 * mean("final_target_lift_m"),
        "mean_final_hand_target_distance_mm": 1000.0 * mean("final_hand_target_distance_m"),
        "mean_peak_jerk_mps3": mean("peak_jerk_mps3"),
        "mean_peak_torque_nm": mean("peak_torque_nm"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--esn", type=Path)
    parser.add_argument("--mlp", type=Path)
    parser.add_argument("--seeds", type=int, nargs="+", default=[20265001, 20265002, 20265003])
    parser.add_argument("--y-offsets", type=float, nargs="+", default=[-0.003, 0.0, 0.003])
    parser.add_argument("--z-offsets", type=float, nargs="+", default=[0.0])
    parser.add_argument("--budget", type=float, default=0.02)
    parser.add_argument("--vmc-stiffness", type=float, default=1.0)
    args = parser.parse_args()
    methods = [("PaperMPC", None), ("VMC", make_vmc(args.budget, args.vmc_stiffness))]
    if args.mlp is not None:
        methods.append(("MLP", MLPComplianceController.from_npz(args.mlp)))
    if args.esn is not None:
        methods.append(("ESN", load_controller(args.esn)))
    rows: list[dict[str, object]] = []
    for label, controller in methods:
        for y_offset in args.y_offsets:
            for z_offset in args.z_offsets:
                for seed in args.seeds:
                    row = run_one(
                        args.menagerie, label, controller, seed=seed, budget=args.budget,
                        board_y_offset_m=y_offset, board_z_offset_m=z_offset,
                    )
                    rows.append(row)
                    print(json.dumps(row), flush=True)
    summary = {
        label: aggregate([row for row in rows if row["method"] == label])
        for label, _ in methods
    }
    output = {
        "schema_version": 1,
        "protocol": "dual_phase_longitudinal_physical_contact",
        "observation_contract": "MLP/ESN: q(7), qdot(7), nominal_twist(6), WBC pose error(6), WBC twist error(6); no obstacle/contact/object truth",
        "fairness": "same MuJoCo model, board geometry, reference, seed, residual torque fraction and safety clamps",
        "budget": args.budget, "vmc_stiffness": args.vmc_stiffness,
        "summary": summary, "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": summary}, indent=2), flush=True)


if __name__ == "__main__":
    main()
