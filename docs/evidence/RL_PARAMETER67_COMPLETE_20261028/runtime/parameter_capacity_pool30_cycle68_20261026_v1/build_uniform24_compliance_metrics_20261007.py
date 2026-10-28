#!/usr/bin/env python3
"""Summarize event-conditioned compliance metrics for the uniform /24 cohort.

The input is the frozen final_delivery comparison REPORT.json.  This tool only
post-processes recorded metrics; it does not run a simulator or infer missing
contact/recovery values as zero.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from build_uniform24_matrix_20261007 import FAMILIES


EVENTS = ("ball", "human", "rod")


def mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    rows = report["raw_rows"]
    families = []
    for family in FAMILIES:
        candidate = report["families"][family]["models"][0]
        selected = [row for row in rows if row["candidate"] == candidate]
        if len(selected) != 24:
            raise ValueError(f"{family}: expected 24 rows, got {len(selected)}")
        metrics = [row["metrics"] for row in selected]
        event_summary = {}
        for event in EVENTS:
            contacts = [m["contact"][event] for m in metrics]
            recovery = [m["recovery"][event]["settled_rejoin_time_s"] for m in metrics]
            def values(key: str) -> list[float]:
                return [float(c[key]) for c in contacts if c.get(key) is not None]
            observed_recovery = [float(v) for v in recovery if v is not None]
            event_summary[event] = {
                "n_contact_exposed": len(values("contact_p95_force_n")),
                "contact_p95_force_n_mean": mean(values("contact_p95_force_n")),
                "impulse_ns_mean": mean(values("impulse_ns")),
                "contact_duration_s_mean": mean(values("contact_duration_s")),
                "recovery_success": len(observed_recovery),
                "recovery_time_s_mean_if_observed": mean(observed_recovery),
            }
        penetration = [
            max(float(m["safety_audit"]["external_penetration_mm"]),
                float(m["safety_audit"]["edge_penetration_mm"]))
            for m in metrics
        ]
        tv_per_s = [
            sum(float(v) for v in m["torque_total_variation_nm_by_joint"])
            / float(m["duration_s"])
            for m in metrics
            if float(m["duration_s"]) > 0
        ]
        families.append({
            "family": family,
            "candidate": candidate,
            "task": sum(bool(m["task_success"]) for m in metrics),
            "strict": sum(bool(m["strict_success"]) for m in metrics),
            "short": sum(not bool(m["full_horizon"]) for m in metrics),
            "max_penetration_mm": max(penetration),
            "torque_total_variation_nm_per_s_mean": mean(tv_per_s),
            "mechanical_work_j_mean": mean([float(m["absolute_joint_mechanical_work_j"]) for m in metrics]),
            "events": event_summary,
        })
    print(json.dumps({
        "conditions": 24,
        "selection_rule": "first frozen model per family",
        "events": list(EVENTS),
        "families": families,
    }, indent=2))


if __name__ == "__main__":
    main()
