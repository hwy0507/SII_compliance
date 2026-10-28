#!/usr/bin/env python3
"""Re-aggregate the frozen research72 report to one fixed model per family.

This does not run MuJoCo.  It is deliberately a post-processing tool: every
family is restricted to the first candidate listed in REPORT.json, which is
the pre-registered seed 2026100301 for stochastic families and the sole
candidate for deterministic families.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


FAMILIES = (
    "esn",
    "matched_rnn",
    "matched_mlp",
    "ordinary_rnn",
    "ordinary_mlp",
    "memoryless",
    "classical_vmc",
    "classical_admittance",
    "classical_impedance",
    "parameter_vmc",
    "parameter_admittance",
    "parameter_impedance",
    "direct_metric",
    "direct_office_task",
    "enhanced_teacher",
    "nominal_zero",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path, help="frozen final_delivery comparison/REPORT.json")
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    rows = report["raw_rows"]
    output = []
    for family in FAMILIES:
        candidate = report["families"][family]["models"][0]
        selected = [row for row in rows if row["candidate"] == candidate]
        if len(selected) != 24:
            raise ValueError(f"{family}: {candidate} has {len(selected)} rows, expected 24")
        metrics = [row["metrics"] for row in selected]
        mean = lambda key: statistics.fmean(item[key] for item in metrics)
        output.append(
            {
                "family": family,
                "candidate": candidate,
                "task": sum(item["task_success"] for item in metrics),
                "strict": sum(item["strict_success"] for item in metrics),
                "rmse_mm": mean("rmse_mm"),
                "peak_torque_nm": mean("peak_torque_nm"),
                "peak_speed_mps": mean("peak_speed_mps"),
                "work_j": mean("absolute_joint_mechanical_work_j"),
                "short": sum(not item["full_horizon"] for item in metrics),
            }
        )
    print(json.dumps({"conditions": 24, "selection_rule": "first frozen model per family", "rows": output}, indent=2))


if __name__ == "__main__":
    main()
