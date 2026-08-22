#!/usr/bin/env python3
"""Pre-registered robust dual-board evaluation with no policy-side obstacle truth.

This protocol intentionally remains separate from the locked 2026-08-22
dual-phase result.  It tests a physically motivated sim-to-real envelope:
fixed-board placement tolerance, contact relaxation time, encoder-velocity
noise, and an identical residual-command latency for every learned/feedback
controller.  The nominal PaperMPC WBC stays at its normal low-level rate;
only the optional residual channel is delayed.

Run ``--methods PaperMPC --split all`` first.  That is a geometry/physics
gate only: every retained condition must make the two contacts in the intended
order without a reset overlap or object-board collision.  Once that manifest
is saved, do not edit the condition table after seeing any method score.
"""

from __future__ import annotations

import argparse
import json
from collections import deque
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np

from evaluate_dual_phase_four_method import aggregate, controller_action, fixture, make_vmc
from mlp_compliance_baseline import MLPComplianceController
from vmc_compliance_baseline import load_controller
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv


@dataclass(frozen=True)
class RobustCondition:
    """One fully specified, fixed-world MuJoCo condition.

    The policy receives none of these fields.  ``joint_velocity_noise_std``
    enters only the measured-qdot path used by *all* residual controllers.
    ``residual_action_delay_steps`` is applied to every nonzero residual
    command after the controller emits it, including VMC, MLP, and ESN.
    """

    name: str
    split: str
    seed: int
    board_y_offset_m: float
    board_z_offset_m: float
    contact_time_constant_s: float
    joint_velocity_noise_std: float
    residual_action_delay_steps: int


# This table is declared before running the robust screen.  The development
# and held-out tables use disjoint seeds and non-identical numeric levels.
# Values are deliberately moderate: they model placement tolerance, contact
# softness/stiffness, noisy differentiated encoders and 40-ms residual delay,
# while retaining an ordinary fixed wooden-board manipulation task.
CONDITIONS: tuple[RobustCondition, ...] = (
    RobustCondition("dev_soft_near", "development", 20266101, 0.0015, -0.0015, 0.010, 0.004, 0),
    RobustCondition("dev_stiff_near", "development", 20266102, 0.0030, 0.0015, 0.020, 0.004, 0),
    RobustCondition("dev_soft_delayed", "development", 20266103, 0.0045, -0.0025, 0.010, 0.008, 1),
    RobustCondition("dev_stiff_delayed", "development", 20266104, 0.0060, 0.0025, 0.022, 0.008, 1),
    RobustCondition("held_mid_near", "held_out", 20266201, 0.00225, -0.0010, 0.012, 0.005, 0),
    RobustCondition("held_mid_far", "held_out", 20266202, 0.00375, 0.0010, 0.018, 0.005, 0),
    RobustCondition("held_soft_delayed", "held_out", 20266203, 0.00525, -0.0030, 0.014, 0.009, 1),
    RobustCondition("held_stiff_delayed", "held_out", 20266204, 0.00475, 0.0030, 0.024, 0.009, 1),
)


def selected_conditions(split: str) -> tuple[RobustCondition, ...]:
    if split == "all":
        return CONDITIONS
    return tuple(item for item in CONDITIONS if item.split == split)


def run_one(
    menagerie: Path, label: str, controller, condition: RobustCondition, *, budget: float,
) -> dict[str, object]:
    fx = replace(fixture(condition.seed), contact_time_constant_s=condition.contact_time_constant_s)
    env = PandaWBCVelocityResidualEnv(
        menagerie, None, None, "direct_esn", fixtures=(fx,), rod_enabled=False,
        robot="fr3", wbc_backend="paper_mpc", execution_mode="torque_residual",
        residual_torque_scale=budget, lift_board_tilt_deg=15.0,
        lift_board_contact_mode="dual_phase_longitudinal",
        lift_board_y_offset_m=condition.board_y_offset_m,
        lift_board_z_offset_m=condition.board_z_offset_m,
        joint_velocity_noise_std=condition.joint_velocity_noise_std,
        seed=condition.seed,
    )
    # Explicit controller-to-actuator FIFO: this is outside the ESN and
    # applies identically to VMC/MLP/ESN.  PaperMPC emits the same all-zero
    # residual at every time, so it is intentionally unaffected by the queue.
    command_fifo = deque(
        (np.zeros(7, dtype=float) for _ in range(condition.residual_action_delay_steps)),
        maxlen=condition.residual_action_delay_steps or None,
    )
    env.reset(seed=condition.seed, options={"fixture_index": 0})
    if controller is not None and hasattr(controller, "reset"):
        controller.reset()
    done = False
    info: dict[str, object] = {}
    while not done:
        proposed = controller_action(controller, env.diagnostics())
        if condition.residual_action_delay_steps:
            applied = command_fifo.popleft()
            command_fifo.append(proposed)
        else:
            applied = proposed
        _, _, terminated, truncated, info = env.step(applied)
        done = bool(terminated or truncated)
    boards = info["dual_board_metrics"]
    row: dict[str, object] = {
        "method": label,
        "condition": asdict(condition),
        "budget": budget,
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
    row["physical_audit_pass"] = physical_audit_pass(row)
    env.close()
    return row


def physical_audit_pass(row: dict[str, object]) -> bool:
    """The same hard physical checks are used for every method and split."""

    pre, post = row["pregrasp"], row["postgrasp"]
    assert isinstance(pre, dict) and isinstance(post, dict)
    relevant_partner = lambda board: bool(board["hand_body_contact"] or board["link7_body_contact"])
    return bool(
        row["task_success"] and row["dual_phase_geometry_valid"]
        and not row["initial_board_contact"] and row["finite_state"]
        and bool(pre["contact"]) and bool(post["contact"])
        and relevant_partner(pre) and relevant_partner(post)
        and not bool(pre["target_object_contact"]) and not bool(post["target_object_contact"])
        and float(pre["max_penetration_m"]) <= 0.002
        and float(post["max_penetration_m"]) <= 0.002
    )


def robust_aggregate(rows: list[dict[str, object]]) -> dict[str, float | int]:
    summary = aggregate(rows)
    summary["physical_audit_pass_count"] = int(sum(bool(row["physical_audit_pass"]) for row in rows))
    summary["physical_audit_pass_rate"] = float(np.mean([bool(row["physical_audit_pass"]) for row in rows]))
    summary["initial_contact_count"] = int(sum(bool(row["initial_board_contact"]) for row in rows))
    summary["object_board_contact_count"] = int(sum(
        bool(row["pregrasp"]["target_object_contact"]) or bool(row["postgrasp"]["target_object_contact"])
        for row in rows
    ))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--esn", type=Path)
    parser.add_argument("--mlp", type=Path)
    parser.add_argument("--budget", type=float, default=0.04)
    parser.add_argument("--vmc-stiffness", type=float, default=0.5)
    parser.add_argument("--split", choices=("development", "held_out", "all"), default="all")
    parser.add_argument("--methods", nargs="+", choices=("PaperMPC", "VMC", "MLP", "ESN"),
                        default=("PaperMPC", "VMC", "MLP", "ESN"))
    parser.add_argument("--manifest-only", action="store_true",
                        help="write the pre-registered protocol without starting MuJoCo")
    args = parser.parse_args()
    if not 0.0 < args.budget <= 1.0 or args.vmc_stiffness <= 0.0:
        raise ValueError("budget and VMC stiffness must be positive")
    if not args.manifest_only and "ESN" in args.methods and args.esn is None:
        raise ValueError("ESN was selected but --esn is missing")
    if not args.manifest_only and "MLP" in args.methods and args.mlp is None:
        raise ValueError("MLP was selected but --mlp is missing")
    conditions = selected_conditions(args.split)
    protocol = {
        "schema_version": 1,
        "protocol": "dual_phase_longitudinal_cross_physics_robustness_v1",
        "status": "pre_registered_before_method_scores",
        "observation_contract": "MLP/ESN: q(7), qdot(7), nominal_twist(6), WBC pose error(6), WBC twist error(6); no board/contact/object truth",
        "fairness": "same MuJoCo model/reference/condition per method; VMC, MLP and ESN share budget, safety clamps, qdot noise and residual FIFO latency",
        "physical_variations": "fixed board pose tolerance, MuJoCo contact relaxation time, measured joint-velocity noise, residual action delay",
        "conditions": [asdict(item) for item in conditions],
        "budget": args.budget,
        "vmc_stiffness": args.vmc_stiffness,
    }
    if args.manifest_only:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(protocol, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(protocol, indent=2))
        return
    controllers: dict[str, object | None] = {
        "PaperMPC": None,
        "VMC": make_vmc(args.budget, args.vmc_stiffness),
        "MLP": None if args.mlp is None else MLPComplianceController.from_npz(args.mlp),
        "ESN": None if args.esn is None else load_controller(args.esn),
    }
    rows: list[dict[str, object]] = []
    for label in args.methods:
        for condition in conditions:
            row = run_one(args.menagerie, label, controllers[label], condition, budget=args.budget)
            rows.append(row)
            print(json.dumps(row), flush=True)
    output = {
        **protocol,
        "methods": list(args.methods),
        "summary": {label: robust_aggregate([row for row in rows if row["method"] == label]) for label in args.methods},
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": output["summary"], "output": str(args.out)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
