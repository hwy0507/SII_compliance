#!/usr/bin/env python3
"""Build a validation-only Pareto archive for WBC residual PPO checkpoints.

The archive never opens the frozen V4 final holdout.  Every candidate is
evaluated through the same matched rod/no-rod MuJoCo protocol before it can
enter the Pareto set.  The representative checkpoint is selected by a
predeclared equal-rank rule over the five co-primary objectives, rather than a
post-hoc weighted scalar score.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


OBJECTIVES = (
    "recovery_rmse_mm",
    "rejoin_latency_s",
    "peak_recovery_jerk_mps3",
    "contact_impulse_ns",
    "peak_torque_nm",
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def _checkpoint_step(path: Path) -> int:
    match = re.fullmatch(r"ppo_wbc_residual_(\d+)_steps\.zip", path.name)
    if match is None:
        raise ValueError(f"unrecognized checkpoint name: {path.name}")
    return int(match.group(1))


def discover_candidates(run_dir: Path, include_final: bool = True) -> list[dict[str, Any]]:
    """Return only checkpoints with their matching normalization state."""
    candidates: list[dict[str, Any]] = []
    checkpoint_dir = run_dir / "checkpoints"
    if checkpoint_dir.is_dir():
        for model in sorted(checkpoint_dir.glob("ppo_wbc_residual_*_steps.zip"), key=_checkpoint_step):
            normalizer = checkpoint_dir / f"{model.stem}_vecnormalize.pkl"
            if normalizer.is_file():
                candidates.append({
                    "candidate_id": f"step_{_checkpoint_step(model)}",
                    "step": _checkpoint_step(model),
                    "model": str(model),
                    "vecnormalize": str(normalizer),
                })
    if include_final:
        model = run_dir / "ppo_wbc_residual_final.zip"
        normalizer = run_dir / "vecnormalize.pkl"
        if model.is_file() and normalizer.is_file():
            candidates.append({
                "candidate_id": "final",
                "step": None,
                "model": str(model),
                "vecnormalize": str(normalizer),
            })
    if not candidates:
        raise FileNotFoundError(f"no paired PPO/VecNormalize candidates found in {run_dir}")
    return candidates


def validation_gate(summary: dict[str, Any]) -> dict[str, Any]:
    expected = int(summary["episode_count"])
    checks = {
        "task_success": int(summary["task_success_count"]) == expected,
        "matched_no_rod_success": int(summary["matched_no_rod_task_success_count"]) == expected,
        "effective_collision_at_least_eight": int(summary["effective_collision_count"]) >= min(8, expected),
        "no_hard_torque_limit": int(summary["hard_torque_limit_count"]) == 0,
    }
    return {"passed": all(checks.values()), "checks": checks, "summary": summary}


def objective_vector(candidate: dict[str, Any]) -> tuple[float, ...]:
    summary = candidate["gate"]["summary"]
    values: list[float] = []
    for key in OBJECTIVES:
        distribution = summary.get(key)
        if distribution is None:
            # A task may still pass the grasp gate without settling below the
            # rejoin threshold.  Preserve that factual result, but make the
            # incomplete recovery strictly noncompetitive in the archive.
            values.append(float("inf"))
            continue
        values.append(float(distribution["mean"]))
    return tuple(values)


def dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """All archive objectives are minimized; equality alone is not dominance."""
    lhs = objective_vector(left)
    rhs = objective_vector(right)
    return all(a <= b for a, b in zip(lhs, rhs)) and any(a < b for a, b in zip(lhs, rhs))


def pareto_frontier(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    valid = [candidate for candidate in candidates if candidate["gate"]["passed"]]
    return [
        candidate for candidate in valid
        if not any(other is not candidate and dominates(other, candidate) for other in valid)
    ]


def select_representative(frontier: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Use equal ordinal ranks across objectives as the predeclared tie-break."""
    if not frontier:
        return None
    ranks: dict[str, list[int]] = {candidate["candidate_id"]: [] for candidate in frontier}
    for index in range(len(OBJECTIVES)):
        ordered = sorted(frontier, key=lambda item: (objective_vector(item)[index], item["candidate_id"]))
        for rank, candidate in enumerate(ordered, start=1):
            ranks[candidate["candidate_id"]].append(rank)
    return min(
        frontier,
        key=lambda item: (
            sum(ranks[item["candidate_id"]]),
            max(ranks[item["candidate_id"]]),
            objective_vector(item),
            item["candidate_id"],
        ),
    )


def _evaluation_command(args: argparse.Namespace, candidate: dict[str, Any], output_dir: Path) -> list[str]:
    command = [
        args.python, str(args.evaluator),
        "--menagerie", str(args.menagerie),
        "--output-dir", str(output_dir),
        "--fixture-manifest", str(args.fixture_manifest),
        "--fixture-split", "validation",
        "--fan-ye-model-npz", str(args.fan_ye_model_npz),
        "--fan-ye-train-summary-json", str(args.fan_ye_train_summary_json),
        "--observation-mode", args.observation_mode,
        "--reward-profile", args.reward_profile,
        "--model", candidate["model"],
        "--vecnormalize", candidate["vecnormalize"],
    ]
    if args.residual_window_end_at_grasp:
        command.append("--residual-window-end-at-grasp")
    if args.directional_phase_projection:
        command.append("--directional-phase-projection")
    return command


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--fixture-manifest", type=Path, required=True)
    parser.add_argument("--fan-ye-model-npz", type=Path, required=True)
    parser.add_argument("--fan-ye-train-summary-json", type=Path, required=True)
    parser.add_argument("--observation-mode", required=True)
    parser.add_argument("--reward-profile", required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--evaluator", type=Path, default=Path(__file__).with_name("evaluate_wbc_velocity_residual.py"))
    parser.add_argument("--residual-window-end-at-grasp", action="store_true")
    parser.add_argument("--directional-phase-projection", action="store_true")
    parser.add_argument("--exclude-final", action="store_true")
    args = parser.parse_args()
    if "post_v4_development" not in args.fixture_manifest.as_posix():
        raise ValueError("checkpoint archive must use the isolated post-V4 development manifest")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    candidates = discover_candidates(args.run_dir, include_final=not args.exclude_final)
    for candidate in candidates:
        candidate_dir = args.output_dir / candidate["candidate_id"]
        candidate_dir.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(_evaluation_command(args, candidate, candidate_dir), check=False, text=True, capture_output=True)
        (candidate_dir / "evaluation.stdout.log").write_text(result.stdout)
        (candidate_dir / "evaluation.stderr.log").write_text(result.stderr)
        report_path = candidate_dir / "wbc_velocity_residual_paired_evaluation.json"
        if result.returncode != 0 or not report_path.is_file():
            candidate["gate"] = {"passed": False, "reason": f"evaluator exit {result.returncode}"}
            candidate["evaluation_exit_code"] = result.returncode
            continue
        report = json.loads(report_path.read_text())
        candidate["gate"] = validation_gate(report["summary"])
        candidate["evaluation_report"] = str(report_path)
        candidate["evaluation_exit_code"] = result.returncode
    frontier = pareto_frontier(candidates)
    representative = select_representative(frontier)
    archive = {
        "protocol": "validation-only checkpoint archive; frozen V4 final holdout excluded",
        "selection_rule": "gate first; nondominated Pareto frontier over recovery RMSE, rejoin latency, recovery jerk, contact impulse, and peak torque; equal ordinal-rank representative tie-break",
        "fixture_manifest": str(args.fixture_manifest),
        "objectives_minimize": list(OBJECTIVES),
        "candidates": candidates,
        "pareto_frontier_candidate_ids": [candidate["candidate_id"] for candidate in frontier],
        "representative_candidate_id": None if representative is None else representative["candidate_id"],
        "representative": representative,
    }
    _write_json(args.output_dir / "wbc_velocity_residual_checkpoint_archive.json", archive)
    print(json.dumps({
        "candidate_count": len(candidates),
        "gate_pass_count": sum(bool(item["gate"].get("passed")) for item in candidates),
        "pareto_frontier": archive["pareto_frontier_candidate_ids"],
        "representative": archive["representative_candidate_id"],
    }, indent=2))


if __name__ == "__main__":
    main()
