#!/usr/bin/env python3
"""Aggregate paired independent-ESN overnight validation artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


REPORT_NAME = "wbc_velocity_residual_paired_evaluation.json"
METRICS = (
    "recovery_rmse_mm", "contact_impulse_ns", "peak_jerk_mps3", "peak_torque_nm",
    "paired_offset_rmse_mm", "peak_paired_offset_mm", "mean_wbc_slowdown", "mean_yield_twist_norm",
)


def _summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())["summary"]


def _mean(summary: dict[str, Any], key: str) -> float:
    value = summary[key]
    return float(value["mean"] if isinstance(value, dict) else value)


def _rejoin_mean(summary: dict[str, Any]) -> float | None:
    value = summary["rejoin_latency_s"]
    return None if value is None else float(value["mean"])


def _gate(summary: dict[str, Any]) -> bool:
    n = int(summary["episode_count"])
    return bool(
        summary["task_success_count"] == n
        and summary["matched_no_rod_task_success_count"] == n
        and summary["effective_collision_count"] >= min(8, n)
        and summary["hard_torque_limit_count"] == 0
    )


def _distribution(values: list[float]) -> dict[str, float | int]:
    vector = np.asarray(values, dtype=float)
    return {
        "mean": float(np.mean(vector)),
        "std": float(np.std(vector, ddof=0)),
        "count": int(vector.size),
    }


def _optional_distribution(values: list[float]) -> dict[str, float | int | None]:
    return _distribution(values) if values else {"mean": None, "std": None, "count": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-markdown", type=Path, default=None)
    args = parser.parse_args()
    rows: list[dict[str, Any]] = []
    for run_root in sorted(path for path in args.output_root.iterdir() if path.is_dir()):
        mlp_path = run_root / "current_mlp" / "validation" / REPORT_NAME
        esn_path = run_root / "fan_ye_esn" / "validation" / REPORT_NAME
        if not mlp_path.exists() or not esn_path.exists():
            continue
        mlp, esn = _summary(mlp_path), _summary(esn_path)
        profile, _, seed_text = run_root.name.rpartition("_seed")
        row: dict[str, Any] = {
            "run_id": run_root.name,
            "profile": profile,
            "seed": int(seed_text),
            "mlp_gate": _gate(mlp),
            "esn_gate": _gate(esn),
            "mlp": {key: _mean(mlp, key) for key in METRICS},
            "esn": {key: _mean(esn, key) for key in METRICS},
        }
        row["mlp"]["rejoin_latency_s"] = _rejoin_mean(mlp)
        row["esn"]["rejoin_latency_s"] = _rejoin_mean(esn)
        row["difference_esn_minus_mlp"] = {key: row["esn"][key] - row["mlp"][key] for key in METRICS}
        row["difference_esn_minus_mlp"]["rejoin_latency_s"] = (
            None if row["esn"]["rejoin_latency_s"] is None or row["mlp"]["rejoin_latency_s"] is None
            else row["esn"]["rejoin_latency_s"] - row["mlp"]["rejoin_latency_s"]
        )
        rows.append(row)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["profile"], []).append(row)
    aggregates: dict[str, Any] = {}
    for profile, profile_rows in grouped.items():
        paired = [row for row in profile_rows if row["mlp_gate"] and row["esn_gate"]]
        aggregates[profile] = {
            "complete_pairs": len(profile_rows),
            "gate_passing_pairs": len(paired),
            "esn_minus_mlp": {
                key: _distribution([row["difference_esn_minus_mlp"][key] for row in paired])
                for key in METRICS
            } | {
                "rejoin_latency_s": _optional_distribution([
                    row["difference_esn_minus_mlp"]["rejoin_latency_s"]
                    for row in paired if row["difference_esn_minus_mlp"]["rejoin_latency_s"] is not None
                ])
            } if paired else {},
        }
    output = {
        "controller_family": "independent_wbc_velocity_residual",
        "uses_vmc": False,
        "rows": rows,
        "by_profile": aggregates,
    }
    output_json = args.output_json or args.output_root / "overnight_paired_summary.json"
    output_json.write_text(json.dumps(output, indent=2) + "\n")
    output_markdown = args.output_markdown or args.output_root / "overnight_paired_summary.md"
    lines = [
        "# Independent WBC residual overnight summary", "",
        "Only pairs passing task, no-rod, effective-collision, and torque gates are used for paired effect summaries.", "",
        "| profile | completed pairs | gated pairs | ESN−MLP recovery RMSE (mm) | ESN−MLP impulse (N s) | ESN−MLP rejoin metric |", "",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for profile, values in aggregates.items():
        differences = values["esn_minus_mlp"]
        recovery = "—" if not differences else f"{differences['recovery_rmse_mm']['mean']:.3f} ± {differences['recovery_rmse_mm']['std']:.3f}"
        impulse = "—" if not differences else f"{differences['contact_impulse_ns']['mean']:.3f} ± {differences['contact_impulse_ns']['std']:.3f}"
        rejoin = "—" if not differences or differences["rejoin_latency_s"]["count"] == 0 else f"{differences['rejoin_latency_s']['mean']:.3f} ± {differences['rejoin_latency_s']['std']:.3f}"
        lines.append(f"| {profile} | {values['complete_pairs']} | {values['gate_passing_pairs']} | {recovery} | {impulse} | {rejoin} |")
    output_markdown.write_text("\n".join(lines) + "\n")
    print(json.dumps({"output_json": str(output_json), "output_markdown": str(output_markdown), "profiles": aggregates}, indent=2))


if __name__ == "__main__":
    main()
