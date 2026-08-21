#!/usr/bin/env python3
"""Record a deterministic train-only randomized teacher-trace manifest.

The teacher remains the analytic torque VMC, while the Paper-MPC nominal
controller and the fixture randomization are kept identical to the benchmark.
The generated rod/ball traces are intended for Direct-ESN coverage BC; board
and no-rod traces are added explicitly so the student keeps the full task
contract. Test seeds must be disjoint from ``--seed`` in the manifest.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from record_paper_mpc_expert_traces import record  # noqa: E402
from wbc_velocity_residual_env import default_velocity_residual_fixtures  # noqa: E402


def _jitter_fixture(fixture, *, rng: np.random.Generator, stroke: float, height: float, start: float):
    return replace(
        fixture,
        rod_stroke_m=float(fixture.rod_stroke_m + rng.uniform(-stroke, stroke)),
        rod_height_m=float(fixture.rod_height_m + rng.uniform(-height, height)),
        rod_start_time_s=float(fixture.rod_start_time_s + rng.uniform(-start, start)),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--seed", type=int, default=5000)
    parser.add_argument("--stroke-jitter-m", type=float, default=0.002)
    parser.add_argument("--height-jitter-m", type=float, default=0.0015)
    parser.add_argument("--start-jitter-s", type=float, default=0.015)
    parser.add_argument("--budget", type=float, default=0.03)
    args = parser.parse_args()
    if args.count < 2:
        raise SystemExit("--count must be at least 2")
    for value, name in ((args.stroke_jitter_m, "stroke"), (args.height_jitter_m, "height"),
                        (args.start_jitter_s, "start"), (args.budget, "budget")):
        if not np.isfinite(value) or value < 0.0:
            raise SystemExit(f"{name} parameter must be finite and non-negative")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    fixtures = default_velocity_residual_fixtures()
    manifest = {
        "schema_version": 1,
        "seed": args.seed,
        "count": args.count,
        "stroke_jitter_m": args.stroke_jitter_m,
        "height_jitter_m": args.height_jitter_m,
        "start_jitter_s": args.start_jitter_s,
        "budget": args.budget,
        "traces": [],
    }

    for index in range(args.count):
        rng = np.random.default_rng(args.seed + index)
        kind = "rod" if index % 2 == 0 else "ball"
        fixture = _jitter_fixture(
            fixtures[index % 3], rng=rng, stroke=args.stroke_jitter_m,
            height=args.height_jitter_m, start=args.start_jitter_s,
        )
        fixture = replace(fixture, impactor_type=kind)
        teacher_k = 2.2 if kind == "rod" else 1.5
        path = args.out_dir / f"random_{index:02d}_{kind}.npz"
        summary = record(
            args.menagerie, fixture, path, k=teacher_k, budget=args.budget,
            seed=args.seed + index, side=None, lift_board=False,
        )
        row = {
            "index": index,
            "kind": kind,
            "teacher_k": teacher_k,
            "fixture": {
                "rod_stroke_m": fixture.rod_stroke_m,
                "rod_height_m": fixture.rod_height_m,
                "rod_start_time_s": fixture.rod_start_time_s,
                "impactor_type": fixture.impactor_type,
            },
            "trace": str(path),
            "summary": summary,
        }
        manifest["traces"].append(row)
        print(json.dumps(row), flush=True)

    # Keep the task's static board and neutral behavior in the training set.
    board_fixture = replace(fixtures[1], rod_start_time_s=99.0)
    board_path = args.out_dir / "board_fixed.npz"
    board_summary = record(
        args.menagerie, board_fixture, board_path, k=2.2, budget=args.budget,
        seed=args.seed + args.count + 1, side=None, lift_board=True,
    )
    manifest["traces"].append({"kind": "board", "trace": str(board_path), "summary": board_summary})

    neutral_path = args.out_dir / "no_rod.npz"
    neutral_summary = record(
        args.menagerie, board_fixture, neutral_path, k=2.2, budget=args.budget,
        seed=args.seed + args.count + 2, side=None, lift_board=False,
    )
    manifest["traces"].append({"kind": "no_rod", "trace": str(neutral_path), "summary": neutral_summary})

    manifest_path = args.out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"manifest": str(manifest_path), "success": all(t["summary"]["success"] for t in manifest["traces"])}, indent=2))


if __name__ == "__main__":
    main()
