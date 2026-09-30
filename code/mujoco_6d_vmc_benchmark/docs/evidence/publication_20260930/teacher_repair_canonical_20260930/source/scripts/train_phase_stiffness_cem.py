#!/usr/bin/env python3
"""Train a two-phase six-dimensional stiffness schedule with CEM.

This is the *dynamic warm-start* before online RL: it optimizes a 12-D,
interpretable schedule `[contact kappa(6), recovery kappa(6)]` across several
physical collision scenes. It is not presented as a state-feedback policy;
the resulting valid elite distribution initializes later PPO training.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

from run_rod_perturbation_benchmark import kappa_filename_tag


SCRIPT_DIR = Path(__file__).resolve().parent
RUNNER = SCRIPT_DIR / "run_rod_perturbation_benchmark.py"
BASE_KAPPA = np.full(6, 35.0)


def _run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _valid(summary: dict[str, Any]) -> tuple[bool, list[str]]:
    task, phase, torque, rod = summary["task_validity"], summary["phase_analysis"], summary["torque"], summary["rod_diagnostics"]
    failures: list[str] = []
    if not task["simulation_finite"]:
        failures.append("nonfinite")
    if not task["rod_hand_contact_observed"]:
        failures.append("missing_contact")
    if rod["peak_contact_force_n"] < 15.0 or rod["contact_impulse_ns"] < 0.45:
        failures.append("ineffective_collision")
    if phase["rejoin_time_s"] is None:
        failures.append("no_rejoin")
    if not task["target_lifted_after_recovery"] or not task["target_held_at_end"]:
        failures.append("task_failure")
    if torque["hard_limit_fraction"] != 0.0:
        failures.append("hard_torque_limit")
    return not failures, failures


def _score(summary: dict[str, Any], paired_offset_mm: float) -> float:
    """Temporary CEM objective; final claims use its Pareto archive."""
    latency = summary["phase_analysis"]["release_to_rejoin_latency_s"]
    if latency is None:
        return 100.0
    return float(
        0.40 * paired_offset_mm
        + 0.35 * summary["tracking"]["recovery_position_rmse_m"] * 1000.0
        + 4.0 * latency
        + 0.05 * summary["torque"]["applied_peak_nm"]
        + 0.0002 * summary["motion"]["jerk_peak_mps3"]
    )


def _evaluate(
    candidate_id: str,
    contact: np.ndarray,
    recovery: np.ndarray,
    samples: list[dict[str, Any]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    candidate_dir = args.output_dir / candidate_id
    records: list[dict[str, Any]] = []
    tag = kappa_filename_tag(contact)
    summary_name = f"rod_perturbation_{tag}_summary.json"
    trace_name = f"rod_perturbation_{tag}_trace.npz"
    for sample in samples:
        sample_dir = candidate_dir / sample["sample_id"]
        rod_dir, no_rod_dir = sample_dir / "rod", sample_dir / "no_rod"
        common = [
            "--menagerie", str(args.menagerie), "--output-dir", str(rod_dir), "--controller-mode", "vmc",
            "--kappa-vector", *(str(value) for value in contact),
            "--recovery-kappa-vector", *(str(value) for value in recovery),
            "--damping-ratio", str(args.damping_ratio), "--carriage-drive-scale", str(args.carriage_drive_scale),
            "--recovery-carriage-drive-scale", str(args.carriage_drive_scale), "--recovery-ramp", str(args.recovery_ramp),
            "--contact-time-constant", "0.015", "--rod-stroke", str(sample["rod_stroke_m"]),
            "--rod-height", str(sample["rod_height_m"]), "--rod-start-time", str(sample["rod_start_time_s"]),
            "--grasp-time", str(sample["grasp_time_s"]), "--explicit-translational-carriage", "--carriage-mass-kg", str(args.carriage_mass_kg),
        ]
        if not (rod_dir / summary_name).is_file():
            _run([sys.executable, str(RUNNER), *common])
        if not (no_rod_dir / summary_name).is_file():
            no_rod_command = common.copy()
            no_rod_command[no_rod_command.index("--output-dir") + 1] = str(no_rod_dir)
            _run([sys.executable, str(RUNNER), *no_rod_command, "--disable-rod"])
        rod, no_rod = _load(rod_dir / summary_name), _load(no_rod_dir / summary_name)
        with np.load(rod_dir / trace_name) as rod_trace, np.load(no_rod_dir / trace_name) as no_rod_trace:
            paired_offset = float(np.max(np.linalg.norm(rod_trace["ee_position"] - no_rod_trace["ee_position"], axis=1)) * 1000.0)
        valid, failures = _valid(rod)
        no_rod_valid, no_rod_failures = _valid(no_rod)
        # No-rod intentionally fails the contact requirement, so use task-only checks.
        no_rod_task = no_rod["task_validity"]
        if not (no_rod_task["simulation_finite"] and no_rod_task["target_lifted_after_recovery"] and no_rod_task["target_held_at_end"] and no_rod["torque"]["hard_limit_fraction"] == 0.0):
            valid = False
            failures.append("invalid_no_rod_task")
        records.append({
            "sample_id": sample["sample_id"], "valid": valid, "invalid_reasons": failures,
            "paired_offset_mm": paired_offset, "score": _score(rod, paired_offset) if valid else 100.0,
            "recovery_rmse_mm": rod["tracking"]["recovery_position_rmse_m"] * 1000.0,
            "rejoin_latency_s": rod["phase_analysis"]["release_to_rejoin_latency_s"],
            "peak_torque_nm": rod["torque"]["applied_peak_nm"],
            "peak_contact_force_n": rod["rod_diagnostics"]["peak_contact_force_n"],
        })
    valid_count = sum(record["valid"] for record in records)
    mean_score = float(np.mean([record["score"] for record in records]))
    return {
        "candidate_id": candidate_id, "contact_kappa_vector": contact.tolist(), "recovery_kappa_vector": recovery.tolist(),
        "valid_count": valid_count, "scene_count": len(records), "mean_score": mean_score, "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--static-results", type=Path, default=None,
        help="Completed static-manifest results used to select effective, non-grazing train scenes.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--scenes", type=int, default=4, help="Deterministically selected high-stroke training scenes per candidate.")
    parser.add_argument("--population", type=int, default=6)
    parser.add_argument("--generations", type=int, default=2)
    parser.add_argument("--elites", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260815)
    parser.add_argument("--initial-log-sigma", type=float, default=0.25)
    parser.add_argument("--damping-ratio", type=float, default=0.8)
    parser.add_argument("--carriage-drive-scale", type=float, default=8.0)
    parser.add_argument("--carriage-mass-kg", type=float, default=1.0)
    parser.add_argument("--recovery-ramp", type=float, default=0.08)
    parser.add_argument(
        "--recovery-only-tighten", action="store_true",
        help="Constrain every recovery stiffness channel to be at least its contact-stage value.",
    )
    args = parser.parse_args()
    if args.population < 2 or not 1 <= args.elites < args.population or args.generations < 1 or args.scenes < 1:
        raise ValueError("invalid CEM population settings")
    manifest = _load(args.manifest)
    train_by_id = {sample["sample_id"]: sample for sample in manifest["splits"]["train"]}
    scene_selection = "highest-stroke manifest samples (no static result file provided)"
    if args.static_results is not None:
        static_records = _load(args.static_results)["records"]
        effective = [
            record for record in static_records
            if record["split"] == "train" and record["valid"] and record["peak_contact_force_n"] >= 15.0
        ]
        if len(effective) < args.scenes:
            raise RuntimeError("not enough effective static training scenes for the requested CEM scene count")
        # Start with genuinely energetic collisions. A later robustness stage
        # deliberately adds medium-strength held-out scenes after warm-start.
        train_samples = [train_by_id[record["sample_id"]] for record in sorted(
            effective, key=lambda record: record["peak_contact_force_n"], reverse=True
        )]
        scenes = train_samples[:args.scenes]
        scene_selection = "top peak-force train scenes passing the static effective-collision gate"
    else:
        train_samples = sorted(train_by_id.values(), key=lambda sample: sample["rod_stroke_m"], reverse=True)
        scenes = train_samples[:args.scenes]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    mean = np.concatenate([np.zeros(6), np.log(np.full(6, 50.0 / 35.0))])
    sigma = np.full(12, args.initial_log_sigma)
    history: list[dict[str, Any]] = []
    for generation in range(args.generations):
        candidates: list[dict[str, Any]] = []
        for population_index in range(args.population):
            latent = mean + sigma * rng.standard_normal(12)
            contact = np.clip(BASE_KAPPA * np.exp(latent[:6]), 8.0, 70.0)
            recovery = np.clip(BASE_KAPPA * np.exp(latent[6:]), 8.0, 70.0)
            if args.recovery_only_tighten:
                recovery = np.maximum(recovery, contact)
            candidates.append(_evaluate(f"generation_{generation:02d}_candidate_{population_index:02d}", contact, recovery, scenes, args))
        candidates.sort(key=lambda candidate: (candidate["valid_count"] != candidate["scene_count"], candidate["mean_score"]))
        elite = candidates[:args.elites]
        elite_latent = np.array([
            np.log(np.asarray(candidate["contact_kappa_vector"] + candidate["recovery_kappa_vector"]) / np.concatenate([BASE_KAPPA, BASE_KAPPA]))
            for candidate in elite
        ])
        mean = np.mean(elite_latent, axis=0)
        sigma = np.maximum(0.05, np.std(elite_latent, axis=0) + 0.04)
        history.append({"generation": generation, "candidates": candidates, "elite_ids": [candidate["candidate_id"] for candidate in elite], "mean_log_ratio": mean.tolist(), "sigma": sigma.tolist()})
    winner = history[-1]["candidates"][0]
    report = {
        "method": "cross-entropy method over a two-phase 12-D stiffness schedule; warm-start only, not state-feedback RL",
        "recovery_only_tighten": args.recovery_only_tighten,
        "scene_selection": scene_selection,
        "scenes": [{key: sample[key] for key in ("sample_id", "rod_stroke_m", "rod_height_m", "rod_start_time_s", "grasp_time_s")} for sample in scenes],
        "effective_collision_gate": {"minimum_peak_contact_force_n": 15.0, "minimum_contact_impulse_ns": 0.45},
        "winner": winner, "history": history,
    }
    (args.output_dir / "phase_stiffness_cem_summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"winner": winner, "scene_count": len(scenes)}, indent=2))


if __name__ == "__main__":
    main()
