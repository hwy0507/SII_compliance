#!/usr/bin/env python3
"""Evaluate a frozen two-phase stiffness schedule on held-out static scenes."""

from __future__ import annotations

import argparse
import json
from argparse import Namespace
from pathlib import Path

import numpy as np

from train_phase_stiffness_cem import _evaluate, _load


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--static-results", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--split", choices=("train", "validation", "test"), default="validation")
    parser.add_argument("--scenes", type=int, default=4)
    parser.add_argument("--contact-kappa-vector", type=float, nargs=6, required=True)
    parser.add_argument("--recovery-kappa-vector", type=float, nargs=6, required=True)
    parser.add_argument("--damping-ratio", type=float, default=0.8)
    parser.add_argument("--carriage-drive-scale", type=float, default=8.0)
    parser.add_argument("--carriage-mass-kg", type=float, default=1.0)
    parser.add_argument("--recovery-ramp", type=float, default=0.08)
    args = parser.parse_args()
    if args.scenes < 1 or min(args.contact_kappa_vector + args.recovery_kappa_vector) <= 0.0:
        raise ValueError("positive six-channel stiffness vectors and a positive scene count are required")
    manifest = _load(args.manifest)
    by_id = {sample["sample_id"]: sample for sample in manifest["splits"][args.split]}
    static = _load(args.static_results)["records"]
    effective = [
        record for record in static
        if record["split"] == args.split and record["valid"] and record["peak_contact_force_n"] >= 15.0
    ]
    if len(effective) < args.scenes:
        raise RuntimeError("not enough effective held-out scenes")
    scenes = [by_id[record["sample_id"]] for record in sorted(
        effective, key=lambda record: record["peak_contact_force_n"], reverse=True
    )[:args.scenes]]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = _evaluate(
        f"frozen_{args.split}", np.asarray(args.contact_kappa_vector), np.asarray(args.recovery_kappa_vector), scenes,
        Namespace(**vars(args)),
    )
    report = {
        "split": args.split,
        "scene_selection": "top peak-force held-out scenes passing static effective-collision gate",
        "scenes": [{key: sample[key] for key in ("sample_id", "rod_stroke_m", "rod_height_m", "rod_start_time_s", "grasp_time_s")} for sample in scenes],
        "result": result,
    }
    (args.output_dir / "frozen_phase_schedule_evaluation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
