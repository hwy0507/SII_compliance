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

# Supplemental conditions for the second, expanded validation pass.  This
# table is fixed before running v2 and is never used for ESN updates.
SUPPLEMENTAL_CONDITIONS: tuple[RobustCondition, ...] = (
    RobustCondition("sup_soft_low", "supplemental_held_out", 20266501, 0.00075, -0.0005, 0.009, 0.003, 0),
    RobustCondition("sup_soft_high", "supplemental_held_out", 20266502, 0.00675, 0.0005, 0.011, 0.003, 0),
    RobustCondition("sup_stiff_low", "supplemental_held_out", 20266503, 0.00125, -0.0035, 0.026, 0.010, 1),
    RobustCondition("sup_stiff_high", "supplemental_held_out", 20266504, 0.00625, 0.0035, 0.028, 0.010, 1),
    RobustCondition("sup_mix_one", "supplemental_held_out", 20266505, 0.00750, -0.0015, 0.016, 0.011, 1),
    RobustCondition("sup_mix_two", "supplemental_held_out", 20266506, 0.00050, 0.0020, 0.021, 0.006, 0),
    RobustCondition("sup_mix_three", "supplemental_held_out", 20266507, 0.00575, -0.0040, 0.013, 0.007, 1),
    RobustCondition("sup_mix_four", "supplemental_held_out", 20266508, 0.00275, 0.0040, 0.025, 0.007, 0),
)

# Final confirmatory split for the lift-constrained v3 ESN.  These conditions
# were declared after closing v1/v2 development, but before any v3 method was
# evaluated.  They are never returned by the ESN trainer.
CONFIRMATORY_CONDITIONS: tuple[RobustCondition, ...] = (
    RobustCondition("conf_soft_edge_low", "confirmatory_held_out", 20266901, 0.00025, -0.0025, 0.008, 0.002, 0),
    RobustCondition("conf_soft_edge_high", "confirmatory_held_out", 20266902, 0.00775, 0.0025, 0.010, 0.002, 0),
    RobustCondition("conf_stiff_edge_low", "confirmatory_held_out", 20266903, 0.00075, -0.0045, 0.030, 0.012, 2),
    RobustCondition("conf_stiff_edge_high", "confirmatory_held_out", 20266904, 0.00725, 0.0045, 0.028, 0.012, 2),
    RobustCondition("conf_delay_soft_a", "confirmatory_held_out", 20266905, 0.00200, -0.0030, 0.012, 0.010, 2),
    RobustCondition("conf_delay_soft_b", "confirmatory_held_out", 20266906, 0.00650, 0.0030, 0.014, 0.010, 2),
    RobustCondition("conf_delay_stiff_a", "confirmatory_held_out", 20266907, 0.00150, -0.0010, 0.026, 0.008, 1),
    RobustCondition("conf_delay_stiff_b", "confirmatory_held_out", 20266908, 0.00600, 0.0010, 0.024, 0.008, 1),
    RobustCondition("conf_mid_a", "confirmatory_held_out", 20266909, 0.00325, -0.0040, 0.017, 0.006, 1),
    RobustCondition("conf_mid_b", "confirmatory_held_out", 20266910, 0.00475, 0.0040, 0.019, 0.006, 1),
    RobustCondition("conf_mid_c", "confirmatory_held_out", 20266911, 0.00250, -0.0005, 0.015, 0.004, 0),
    RobustCondition("conf_mid_d", "confirmatory_held_out", 20266912, 0.00500, 0.0005, 0.023, 0.004, 0),
)

V4_DEVELOPMENT_CONDITIONS: tuple[RobustCondition, ...] = (
    RobustCondition("v4dev_low_soft", "v4_development", 20267201, 0.00025, -0.0035, 0.009, 0.004, 0),
    RobustCondition("v4dev_low_stiff", "v4_development", 20267202, 0.00075, 0.0035, 0.028, 0.010, 2),
    RobustCondition("v4dev_high_soft", "v4_development", 20267203, 0.00775, -0.0025, 0.011, 0.004, 0),
    RobustCondition("v4dev_high_stiff", "v4_development", 20267204, 0.00725, 0.0025, 0.027, 0.010, 2),
    RobustCondition("v4dev_mid_delay_a", "v4_development", 20267205, 0.00200, -0.0040, 0.014, 0.008, 2),
    RobustCondition("v4dev_mid_delay_b", "v4_development", 20267206, 0.00600, 0.0040, 0.023, 0.008, 2),
    RobustCondition("v4dev_mid_a", "v4_development", 20267207, 0.00300, -0.0010, 0.017, 0.006, 1),
    RobustCondition("v4dev_mid_b", "v4_development", 20267208, 0.00500, 0.0010, 0.021, 0.006, 1),
)

V4_FINAL_CONDITIONS: tuple[RobustCondition, ...] = (
    RobustCondition("v4final_01", "v4_final_held_out", 20267301, 0.00035, -0.0020, 0.010, 0.003, 0),
    RobustCondition("v4final_02", "v4_final_held_out", 20267302, 0.00060, 0.0020, 0.029, 0.011, 2),
    RobustCondition("v4final_03", "v4_final_held_out", 20267303, 0.00110, -0.00425, 0.013, 0.009, 2),
    RobustCondition("v4final_04", "v4_final_held_out", 20267304, 0.00180, 0.00425, 0.026, 0.009, 1),
    RobustCondition("v4final_05", "v4_final_held_out", 20267305, 0.00240, -0.0030, 0.016, 0.005, 0),
    RobustCondition("v4final_06", "v4_final_held_out", 20267306, 0.00290, 0.0030, 0.024, 0.007, 2),
    RobustCondition("v4final_07", "v4_final_held_out", 20267307, 0.00340, -0.0005, 0.018, 0.004, 1),
    RobustCondition("v4final_08", "v4_final_held_out", 20267308, 0.00390, 0.0005, 0.022, 0.008, 1),
    RobustCondition("v4final_09", "v4_final_held_out", 20267309, 0.00430, -0.0015, 0.015, 0.006, 2),
    RobustCondition("v4final_10", "v4_final_held_out", 20267310, 0.00480, 0.0015, 0.025, 0.010, 0),
    RobustCondition("v4final_11", "v4_final_held_out", 20267311, 0.00530, -0.00375, 0.012, 0.007, 1),
    RobustCondition("v4final_12", "v4_final_held_out", 20267312, 0.00580, 0.00375, 0.027, 0.005, 2),
    RobustCondition("v4final_13", "v4_final_held_out", 20267313, 0.00630, -0.00275, 0.014, 0.011, 2),
    RobustCondition("v4final_14", "v4_final_held_out", 20267314, 0.00680, 0.00275, 0.023, 0.003, 0),
    RobustCondition("v4final_15", "v4_final_held_out", 20267315, 0.00720, -0.00125, 0.011, 0.008, 1),
    RobustCondition("v4final_16", "v4_final_held_out", 20267316, 0.00765, 0.00125, 0.028, 0.006, 2),
)

# Fresh confirmatory split for the carry-retention constrained ESN.  This
# table is deliberately disjoint from v4 development/final seeds and is
# declared before the corresponding method checkpoint is evaluated.  It
# varies the same physical factors (board placement, contact relaxation,
# measured qdot noise, and residual delay) without exposing any of them to a
# policy.
V5_CONFIRMATORY_CONDITIONS: tuple[RobustCondition, ...] = (
    RobustCondition("v5conf_01", "v5_confirmatory", 20267501, 0.00045, -0.00175, 0.0095, 0.0035, 0),
    RobustCondition("v5conf_02", "v5_confirmatory", 20267502, 0.00085, 0.00175, 0.0285, 0.0105, 2),
    RobustCondition("v5conf_03", "v5_confirmatory", 20267503, 0.00135, -0.00375, 0.0125, 0.0085, 2),
    RobustCondition("v5conf_04", "v5_confirmatory", 20267504, 0.00195, 0.00375, 0.0255, 0.0085, 1),
    RobustCondition("v5conf_05", "v5_confirmatory", 20267505, 0.00255, -0.00275, 0.0155, 0.0055, 0),
    RobustCondition("v5conf_06", "v5_confirmatory", 20267506, 0.00305, 0.00275, 0.0235, 0.0075, 2),
    RobustCondition("v5conf_07", "v5_confirmatory", 20267507, 0.00355, -0.00075, 0.0185, 0.0045, 1),
    RobustCondition("v5conf_08", "v5_confirmatory", 20267508, 0.00405, 0.00075, 0.0215, 0.0075, 1),
    RobustCondition("v5conf_09", "v5_confirmatory", 20267509, 0.00445, -0.00125, 0.0145, 0.0065, 2),
    RobustCondition("v5conf_10", "v5_confirmatory", 20267510, 0.00495, 0.00125, 0.0245, 0.0095, 0),
    RobustCondition("v5conf_11", "v5_confirmatory", 20267511, 0.00545, -0.00350, 0.0115, 0.0065, 1),
    RobustCondition("v5conf_12", "v5_confirmatory", 20267512, 0.00595, 0.00350, 0.0265, 0.0055, 2),
    RobustCondition("v5conf_13", "v5_confirmatory", 20267513, 0.00645, -0.00250, 0.0135, 0.0105, 2),
    RobustCondition("v5conf_14", "v5_confirmatory", 20267514, 0.00695, 0.00250, 0.0225, 0.0035, 0),
    RobustCondition("v5conf_15", "v5_confirmatory", 20267515, 0.00735, -0.00100, 0.0105, 0.0085, 1),
    RobustCondition("v5conf_16", "v5_confirmatory", 20267516, 0.00755, 0.00100, 0.0275, 0.0065, 2),
)


def selected_conditions(split: str) -> tuple[RobustCondition, ...]:
    if split == "all":
        return CONDITIONS
    if split == "expanded_held_out":
        return tuple(item for item in CONDITIONS if item.split == "held_out") + SUPPLEMENTAL_CONDITIONS
    if split == "supplemental_held_out":
        return SUPPLEMENTAL_CONDITIONS
    if split == "confirmatory_held_out":
        return CONFIRMATORY_CONDITIONS
    if split == "v4_development":
        return V4_DEVELOPMENT_CONDITIONS
    if split == "v4_final_held_out":
        return V4_FINAL_CONDITIONS
    if split == "v5_confirmatory":
        return V5_CONFIRMATORY_CONDITIONS
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
    parser.add_argument("--split", choices=("development", "held_out", "expanded_held_out", "supplemental_held_out", "confirmatory_held_out", "v4_development", "v4_final_held_out", "v5_confirmatory", "all"), default="all")
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
