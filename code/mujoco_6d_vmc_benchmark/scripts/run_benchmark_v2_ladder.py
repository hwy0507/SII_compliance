#!/usr/bin/env python3
"""Evaluate the frozen V2 manifest with a fair rigid/impedance/VMC ladder."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from energy_safety import EnergySafetyConfig
from run_benchmark import VMCConfig
from run_rod_perturbation_benchmark import run_episode


KAPPA_6D = [27.579838, 52.550787, 48.699427, 35.859580, 40.719830, 34.766858]
CONTROLLERS = ("rigid", "impedance", "vmc_isotropic", "vmc_6d", "vmc_gated", "vmc_taper", "vmc_energy")
METRICS = (
    "peak_paired_offset_mm", "paired_offset_rmse_mm", "recovery_rmse_mm",
    "recovery_iae_mm_s", "rejoin_latency_s", "yield_peak_error_mm",
    "rebound_ratio", "post_contact_speed_p95_mps", "post_contact_jerk_p95_mps3",
    "peak_jerk_mps3", "peak_torque_nm", "torque_p95_nm", "torque_rms_nm",
    "torque_rate_peak_nmps", "peak_contact_force_n", "contact_impulse_ns",
)


def _trace(path: Path) -> dict[str, np.ndarray]:
    with np.load(next(path.glob("rod_perturbation_*_trace.npz"))) as archive:
        return {key: np.asarray(archive[key]) for key in archive.files}


def _valid(summary: dict[str, Any], no_rod: bool) -> tuple[bool, list[str]]:
    task, torque = summary["task_validity"], summary["torque"]
    failures: list[str] = []
    if not task["simulation_finite"]:
        failures.append("nonfinite")
    if not no_rod and (not task["rod_hand_contact_observed"] or summary["rod_diagnostics"]["peak_contact_force_n"] < 15.0 or summary["rod_diagnostics"]["contact_impulse_ns"] < 0.45):
        failures.append("ineffective_collision")
    if not no_rod and summary["phase_analysis"]["rejoin_time_s"] is None:
        failures.append("no_stable_rejoin")
    if not task["target_lifted_after_recovery"]:
        failures.append("target_not_lifted")
    if not task["target_held_at_end"]:
        failures.append("target_not_held")
    if torque["hard_limit_fraction"] != 0.0:
        failures.append("hard_torque_limit")
    return not failures, failures


def _spec(name: str) -> tuple[str, float | np.ndarray]:
    if name == "rigid":
        return "rigid", 35.0
    if name == "impedance":
        return "impedance", 35.0
    if name == "vmc_isotropic":
        return "vmc", 35.0
    if name == "vmc_6d":
        return "vmc", np.asarray(KAPPA_6D)
    if name == "vmc_gated":
        return "vmc_gated", np.asarray(KAPPA_6D)
    if name == "vmc_taper":
        return "vmc_taper", np.asarray(KAPPA_6D)
    if name == "vmc_energy":
        return "vmc_energy", np.asarray(KAPPA_6D)
    raise ValueError(name)


def _load_energy_safety_config(path: Path | None) -> EnergySafetyConfig | None:
    """Load an explicitly frozen safety configuration for a holdout run.

    The runner accepts only fields belonging to :class:`EnergySafetyConfig`.
    Selection metadata such as ``label`` can live in the same JSON artifact,
    but it cannot silently change the controller parameters.
    """
    if path is None:
        return None
    payload = json.loads(path.read_text())
    fields = set(EnergySafetyConfig.__dataclass_fields__)
    missing = sorted(fields - set(payload))
    if missing:
        raise ValueError(f"energy safety configuration is missing fields: {missing}")
    return EnergySafetyConfig(**{field: payload[field] for field in fields})


def _run_fixture(
    menagerie: Path, root: Path, fixture: dict[str, Any], controller: str,
    energy_safety_config: EnergySafetyConfig | None = None,
) -> dict[str, Any]:
    mode, kappa = _spec(controller)
    uses_virtual_carriage = mode.startswith("vmc")
    config = replace(
        VMCConfig(zeta=0.8),
        carriage_drive_k_translation=VMCConfig().carriage_drive_k_translation * 8.0,
        carriage_drive_k_rotation=VMCConfig().carriage_drive_k_rotation * 8.0,
    )
    common = dict(
        menagerie=menagerie, kappa=kappa, render_gif=False, config=config,
        rod_stroke_m=fixture["rod_stroke_m"], contact_time_constant_s=0.015,
        recovery_kappa=kappa, recovery_ramp_s=0.08, recovery_drive_scale_factor=14.0 / 8.0,
        grasp_time_s=fixture["grasp_time_s"], rod_start_time_s=fixture["rod_start_time_s"],
        explicit_translational_carriage=uses_virtual_carriage, carriage_mass_kg=1.0,
        rod_height_m=fixture["rod_height_m"], controller_mode=mode,
        rod_approach_side=fixture["rod_approach_side"], recovery_gate_hold_s=0.28,
        recovery_gate_taper_s=0.04,
        # The configuration is only meaningful for this controller.  Keeping
        # it absent for all baselines guards against accidental cross-method
        # leakage in a mixed ladder.
        energy_safety_config=energy_safety_config if controller == "vmc_energy" else None,
    )
    run_dir = root / controller / fixture["fixture_id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    rod = run_episode(output_dir=run_dir, rod_enabled=True, **common)
    no_rod_dir = run_dir / "no_rod"
    no_rod_dir.mkdir(parents=True, exist_ok=True)
    no_rod = run_episode(output_dir=no_rod_dir, rod_enabled=False, **common)
    rod_trace, no_rod_trace = _trace(run_dir), _trace(no_rod_dir)
    paired = np.linalg.norm(rod_trace["ee_position"] - no_rod_trace["ee_position"], axis=1)
    rod_valid, rod_failures = _valid(rod, no_rod=False)
    no_rod_valid, no_rod_failures = _valid(no_rod, no_rod=True)
    motion, torque, tracking, phase, rod_info = rod["motion"], rod["torque"], rod["tracking"], rod["phase_analysis"], rod["rod_diagnostics"]
    return {
        "controller": controller, "fixture_id": fixture["fixture_id"],
        "approach_side": fixture["rod_approach_side"], "timing_bin": fixture["timing_bin"], "impulse_bin": fixture["realized_impulse_bin"],
        "valid": rod_valid and no_rod_valid, "invalid_reasons": rod_failures + [f"no_rod:{item}" for item in no_rod_failures],
        "peak_paired_offset_mm": float(np.max(paired) * 1000.0), "paired_offset_rmse_mm": float(np.sqrt(np.mean(paired**2)) * 1000.0),
        "recovery_rmse_mm": tracking["recovery_position_rmse_m"] * 1000.0, "recovery_iae_mm_s": tracking["recovery_iae_m_s"] * 1000.0,
        "rejoin_latency_s": phase["release_to_rejoin_latency_s"], "yield_peak_error_mm": rod["six_spring_response"]["peak_end_effector_nominal_deviation_m"] * 1000.0,
        "rebound_ratio": tracking["post_release_rebound_ratio"], "post_contact_speed_p95_mps": motion["post_contact_speed_p95_mps"],
        "post_contact_jerk_p95_mps3": motion["post_contact_jerk_p95_mps3"], "peak_jerk_mps3": motion["jerk_peak_mps3"],
        "peak_torque_nm": torque["applied_peak_nm"], "torque_p95_nm": torque["applied_p95_nm"], "torque_rms_nm": torque["applied_rms_nm"],
        "torque_rate_peak_nmps": torque["torque_rate_peak_nmps"], "peak_contact_force_n": rod_info["peak_contact_force_n"],
        "contact_impulse_ns": rod_info["contact_impulse_ns"], "task_success": rod["task_validity"]["target_lifted_after_recovery"] and rod["task_validity"]["target_held_at_end"],
        "no_rod_task_success": no_rod["task_validity"]["target_lifted_after_recovery"] and no_rod["task_validity"]["target_held_at_end"],
    }


def _aggregate(
    rows: list[dict[str, Any]], controllers: tuple[str, ...], fixture_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Aggregate only valid rows, optionally on an explicitly paired fixture set."""
    result = []
    for controller in controllers:
        subset = [row for row in rows if row["controller"] == controller and (fixture_ids is None or row["fixture_id"] in fixture_ids)]
        valid = [row for row in subset if row["valid"]]
        summary: dict[str, Any] = {
            "controller": controller,
            "fixture_count": len(subset),
            "valid_count": len(valid),
            "task_success_count": sum(row["task_success"] for row in subset),
            "no_rod_task_success_count": sum(row["no_rod_task_success"] for row in subset),
        }
        for metric in METRICS:
            values = [row[metric] for row in valid if row[metric] is not None]
            summary[metric] = None if not values else {"mean": float(np.mean(values)), "std": float(np.std(values)), "count": len(values)}
        result.append(summary)
    return result


def _common_valid_fixture_ids(rows: list[dict[str, Any]], controllers: tuple[str, ...]) -> list[str]:
    """Return the intersection of fixtures that pass every controller's gates.

    The fixed manifest defines what must be attempted; this intersection defines
    the only sample set on which direct numeric controller comparisons are fair.
    Individual validity rates are retained separately and are not hidden.
    """
    by_controller = {
        controller: {row["fixture_id"] for row in rows if row["controller"] == controller and row["valid"]}
        for controller in controllers
    }
    if not by_controller:
        return []
    return sorted(set.intersection(*by_controller.values()))


def _stratified_aggregate(
    rows: list[dict[str, Any]], controllers: tuple[str, ...], fixture_ids: set[str], field: str,
) -> dict[str, list[dict[str, Any]]]:
    values = sorted({row[field] for row in rows if row["fixture_id"] in fixture_ids})
    return {
        value: _aggregate(
            [row for row in rows if row[field] == value], controllers, fixture_ids,
        )
        for value in values
    }


def _plot(
    all_aggregate: list[dict[str, Any]], common_aggregate: list[dict[str, Any]],
    common_fixture_count: int, output: Path,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), constrained_layout=True)
    all_by_name = {row["controller"]: row for row in all_aggregate}
    display_name = {
        "rigid": "Rigid", "impedance": "Impedance", "vmc_isotropic": "VMC-iso",
        "vmc_6d": "VMC-6D", "vmc_gated": "VMC-gated", "vmc_taper": "VMC-taper", "vmc_energy": "VMC-energy",
    }
    label_offsets = {
        "rigid": (4, 4), "impedance": (4, 4), "vmc_isotropic": (-96, 12),
        "vmc_6d": (-82, -13), "vmc_gated": (5, 8), "vmc_taper": (-84, -12), "vmc_energy": (5, -14),
    }
    for row in common_aggregate:
        if row["valid_count"] == 0 or row["recovery_rmse_mm"] is None:
            continue
        x = row["recovery_rmse_mm"]["mean"]
        axes[0].scatter(x, row["peak_torque_nm"]["mean"], s=70, label=row["controller"])
        axes[1].scatter(x, row["post_contact_jerk_p95_mps3"]["mean"], s=70, label=row["controller"])
        for axis, y in ((axes[0], row["peak_torque_nm"]["mean"]), (axes[1], row["post_contact_jerk_p95_mps3"]["mean"])):
            valid_count = all_by_name[row["controller"]]["valid_count"]
            fixture_count = all_by_name[row["controller"]]["fixture_count"]
            axis.annotate(
                f"{display_name[row['controller']]} ({valid_count}/{fixture_count})", (x, y),
                xytext=label_offsets[row["controller"]], textcoords="offset points", fontsize=8,
            )
    title_suffix = f"common-valid subset n={common_fixture_count}"
    axes[0].set(xlabel="Recovery RMSE (mm)", ylabel="Peak torque (Nm)", title=f"Accuracy–torque Pareto ({title_suffix})")
    axes[1].set(xlabel="Recovery RMSE (mm)", ylabel="Post-contact jerk P95 (m/s³)", title=f"Accuracy–smoothness Pareto ({title_suffix})")
    for axis in axes:
        axis.grid(alpha=0.25)
        axis.spines[["top", "right"]].set_visible(False)
    fig.savefig(output, dpi=220)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--controllers", choices=CONTROLLERS, nargs="+", default=list(CONTROLLERS))
    parser.add_argument(
        "--energy-safety-config-json", type=Path,
        help="Frozen JSON configuration injected only into vmc_energy; use for no-tuning holdout evaluation.",
    )
    parser.add_argument(
        "--existing-results", type=Path,
        help="Re-render the Pareto figure from a completed ladder JSON without rerunning MuJoCo episodes.",
    )
    args = parser.parse_args()
    if args.existing_results is not None:
        payload = json.loads(args.existing_results.read_text())
        _plot(
            payload["aggregate"], payload["aggregate_common_valid_all_controllers"],
            len(payload["common_valid_fixture_ids_all_controllers"]),
            args.output_dir / "benchmark_v2_pareto.png",
        )
        print(f"Re-rendered {args.output_dir / 'benchmark_v2_pareto.png'} from {args.existing_results}")
        return
    manifest = json.loads(args.manifest.read_text())
    fixtures = manifest["splits"]["test"]
    if not fixtures:
        raise RuntimeError("V2 manifest has no physically valid test fixtures")
    controllers = tuple(args.controllers)
    energy_safety_config = _load_energy_safety_config(args.energy_safety_config_json)
    if energy_safety_config is not None and "vmc_energy" not in controllers:
        raise ValueError("--energy-safety-config-json requires vmc_energy in --controllers")
    rows = [
        _run_fixture(args.menagerie, args.output_dir / "episodes", fixture, controller, energy_safety_config)
        for fixture in fixtures for controller in controllers
    ]
    aggregate = _aggregate(rows, controllers)
    common_ids = _common_valid_fixture_ids(rows, controllers)
    common_aggregate = _aggregate(rows, controllers, set(common_ids))
    common_set = set(common_ids)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "protocol": {
            "manifest": str(args.manifest), "controllers": list(controllers),
            "energy_safety_config_json": None if args.energy_safety_config_json is None else str(args.energy_safety_config_json),
            "energy_safety_config": None if energy_safety_config is None else {
                field: getattr(energy_safety_config, field) for field in EnergySafetyConfig.__dataclass_fields__
            },
            "validity": "finite + effective physical collision + stable rejoin + lift + hold + no hard torque limit + valid matched no-rod",
            "comparison_rule": "numeric cross-controller comparisons use only the common-valid fixture intersection; per-controller validity is reported separately",
        },
        "rows": rows,
        "aggregate": aggregate,
        "common_valid_fixture_ids_all_controllers": common_ids,
        "aggregate_common_valid_all_controllers": common_aggregate,
        "aggregate_common_valid_by_approach_side": _stratified_aggregate(rows, controllers, common_set, "approach_side"),
        "aggregate_common_valid_by_timing_bin": _stratified_aggregate(rows, controllers, common_set, "timing_bin"),
        "aggregate_common_valid_by_impulse_bin": _stratified_aggregate(rows, controllers, common_set, "impulse_bin"),
    }
    (args.output_dir / "benchmark_v2_ladder.json").write_text(json.dumps(payload, indent=2) + "\n")
    with (args.output_dir / "benchmark_v2_ladder.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    _plot(aggregate, common_aggregate, len(common_ids), args.output_dir / "benchmark_v2_pareto.png")
    print(json.dumps({"per_controller": aggregate, "common_valid_fixture_count": len(common_ids), "common_valid": common_aggregate}, indent=2))


if __name__ == "__main__":
    main()
