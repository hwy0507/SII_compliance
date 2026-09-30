#!/usr/bin/env python3
"""Run one fixed-WBC grasp task against rod, ball, and hand-palm proxies.

The matrix keeps the nominal Panda task, impact timing, slide displacement,
approach direction, WBC command source, MuJoCo timestep, and controller
parameters fixed.  Each impactor gets a matched no-impact episode.  The
human-hand entry is explicitly a palm-sized compliant geometry proxy; it is
not a human biomechanics or safety simulation.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from run_benchmark import VMCConfig
from run_rod_perturbation_benchmark import (
    IMPACTOR_TYPES,
    run_episode,
)
from screen_benchmark_v4_manifest import WARM_START_KAPPA


CONTROLLERS = ("rigid", "impedance", "vmc_gated")
# Development calibration only: each geometry is driven to an overlapping
# effective-contact regime before controller comparison.  These values are not
# controller parameters and must remain fixed during the matrix evaluation.
CALIBRATED_STROKE_M = {"rod": 0.170, "ball": 0.145, "hand_proxy": 0.145}


def _controller_common(
    menagerie: Path,
    controller: str,
    impactor_type: str,
) -> dict:
    config = replace(
        VMCConfig(zeta=0.8),
        carriage_drive_k_translation=VMCConfig().carriage_drive_k_translation * 8.0,
        carriage_drive_k_rotation=VMCConfig().carriage_drive_k_rotation * 8.0,
    )
    return {
        "menagerie": menagerie,
        "kappa": np.asarray(WARM_START_KAPPA),
        "render_gif": False,
        "config": config,
        "rod_stroke_m": CALIBRATED_STROKE_M[impactor_type],
        "contact_time_constant_s": 0.015,
        "recovery_kappa": np.asarray(WARM_START_KAPPA),
        "recovery_ramp_s": 0.08,
        "recovery_drive_scale_factor": 14.0 / 8.0,
        "grasp_time_s": 2.40,
        "rod_start_time_s": 0.955,
        "explicit_translational_carriage": controller == "vmc_gated",
        "carriage_mass_kg": 1.0,
        "controller_mode": controller,
        "rod_approach_side": "negative_y",
        "rod_height_m": 0.540,
        "rod_center_x_m": 0.55,
        "rod_center_y_m": 0.0,
        "remove_rod_when_disabled": True,
        "recovery_gate_hold_s": 0.28,
        "recovery_gate_taper_s": 0.04,
        "reference_source": "fixed_panda_wbc",
        "impactor_type": impactor_type,
    }


def _paired_metrics(impact: dict, no_impact: dict, impact_dir: Path) -> dict:
    traces = sorted(impact_dir.glob("rod_perturbation_*_trace.npz"))
    no_impact_traces = sorted((impact_dir / "no_impact").glob("rod_perturbation_*_trace.npz"))
    if len(traces) != 1 or len(no_impact_traces) != 1:
        raise RuntimeError("expected exactly one impact/no-impact trace per matrix cell")
    impact_trace = np.load(traces[0])
    no_impact_trace = np.load(no_impact_traces[0])
    paired = np.linalg.norm(impact_trace["ee_position"] - no_impact_trace["ee_position"], axis=1)
    validity = impact["task_validity"]
    no_validity = no_impact["task_validity"]
    return {
        "valid": bool(
            validity["simulation_finite"]
            and validity["rod_hand_contact_observed"]
            and validity["target_lifted_after_recovery"]
            and validity["target_held_at_end"]
            and no_validity["simulation_finite"]
            and no_validity["target_lifted_after_recovery"]
            and no_validity["target_held_at_end"]
            and impact["torque"]["hard_limit_fraction"] == 0.0
        ),
        "peak_paired_offset_mm": float(np.max(paired) * 1000.0),
        "paired_offset_rmse_mm": float(np.sqrt(np.mean(paired**2)) * 1000.0),
        "recovery_rmse_mm": float(impact["tracking"]["recovery_position_rmse_m"] * 1000.0),
        "rejoin_latency_ms": None if impact["phase_analysis"]["release_to_rejoin_latency_s"] is None else float(impact["phase_analysis"]["release_to_rejoin_latency_s"] * 1000.0),
        "peak_recovery_jerk_mps3": float(impact["motion"]["jerk_peak_mps3"]),
        "post_contact_speed_p95_mps": float(impact["motion"]["post_contact_speed_p95_mps"]),
        "peak_torque_nm": float(impact["torque"]["applied_peak_nm"]),
        "peak_torque_rate_nmps": float(impact["torque"]["torque_rate_peak_nmps"]),
        "contact_impulse_ns": float(impact["rod_diagnostics"]["contact_impulse_ns"]),
        "peak_contact_force_n": float(impact["rod_diagnostics"]["peak_contact_force_n"]),
        "max_penetration_mm": float(impact["task_validity"]["max_rod_penetration_m"] * 1000.0),
        "secondary_contact_count": int(impact["phase_analysis"]["secondary_contact_count"]),
        "task_success": bool(validity["target_lifted_after_recovery"] and validity["target_held_at_end"]),
        "no_impact_task_success": bool(no_validity["target_lifted_after_recovery"] and no_validity["target_held_at_end"]),
    }


def run_matrix(menagerie: Path, output_dir: Path, impactors: tuple[str, ...], controllers: tuple[str, ...]) -> dict:
    rows = []
    for impactor in impactors:
        for controller in controllers:
            pair_dir = output_dir / impactor / controller
            pair_dir.mkdir(parents=True, exist_ok=True)
            common = _controller_common(menagerie, controller, impactor)
            impact = run_episode(rod_enabled=True, output_dir=pair_dir, **common)
            no_impact_dir = pair_dir / "no_impact"
            no_impact_dir.mkdir(parents=True, exist_ok=True)
            no_impact = run_episode(rod_enabled=False, output_dir=no_impact_dir, **common)
            metrics = _paired_metrics(impact, no_impact, pair_dir)
            rows.append({
                "impactor_type": impactor,
                "controller": controller,
                "reference_source": "fixed_panda_wbc",
                **metrics,
            })
    payload = {
        "stage": "same-task physical impactor matrix; development validation, not V4 final holdout",
        "protocol": {
            "task": "fixed Panda WBC descend -> impact while open -> rejoin -> close -> lift and hold",
            "impactors": list(impactors),
            "controllers": list(controllers),
            "same_wbc_task": True,
            "same_impact_timing_and_slide_direction": True,
            "calibrated_impactor_stroke_m": CALIBRATED_STROKE_M,
            "calibration_policy": "Each geometry uses a fixed preselected slide stroke that yielded real contact, task success, and no hard torque limit under the frozen WBC-aware VMC-gated controller. Controller parameters were not changed.",
            "same_no_impact_pair": True,
            "hand_proxy_warning": "soft palm-sized ellipsoid; not human biomechanics or a human safety certification",
        },
        "rows": rows,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "impactor_matrix_summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--impactors", nargs="+", choices=IMPACTOR_TYPES, default=list(IMPACTOR_TYPES))
    parser.add_argument("--controllers", nargs="+", choices=CONTROLLERS, default=list(CONTROLLERS))
    args = parser.parse_args()
    payload = run_matrix(args.menagerie, args.output_dir, tuple(args.impactors), tuple(args.controllers))
    print(json.dumps({"rows": len(payload["rows"]), "output_dir": str(args.output_dir)}, indent=2))


if __name__ == "__main__":
    main()
