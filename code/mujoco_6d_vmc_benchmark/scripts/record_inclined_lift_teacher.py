#!/usr/bin/env python3
"""Record train-only teacher traces for the physical inclined-board lift task.

The board is part of the MuJoCo scene and is placed from the lift reference;
it is never exposed to the student controller.  The teacher is a frozen VMC
torque-residual controller.  Its actions are the only labels saved for ESN
and MLP behavioural cloning, while contact quantities remain audit metadata.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from record_paper_mpc_expert_traces import record  # noqa: E402
from wbc_velocity_residual_env import VelocityResidualFixture  # noqa: E402


def make_fixture(seed: int) -> VelocityResidualFixture:
    rng = np.random.default_rng(seed)
    # The rod is parked.  This keeps the only perturbation the real inclined
    # board contact during lift, while retaining the standard FR3 fixture and
    # grasp timing used by the benchmark.
    return VelocityResidualFixture(
        rod_stroke_m=float(rng.uniform(0.165, 0.175)),
        rod_height_m=float(rng.uniform(0.539, 0.542)),
        rod_start_time_s=99.0,
        grasp_time_s=2.4,
        rod_approach_side="negative_y",
        impactor_type="rod",
        rod_cycles=1,
        cycle_period_s=0.8,
        impactor_mass_kg=None,
        rod_slide_damping=2.0,
        rod_driver_kp=5000.0,
        rod_driver_force_limit_n=300.0,
        contact_time_constant_s=0.015,
    )


def record_one(menagerie: Path, out: Path, *, seed: int, tilt: float,
               y_offset_m: float, k: float, budget: float) -> dict:
    # The shared recorder writes exactly the deployable 32-D observation
    # fields plus the bounded seven-dimensional teacher action.  ``lift_board``
    # activates the physical inclined board in the current Paper-MPC scene.
    summary = record(
        menagerie, make_fixture(seed), out, k=k, budget=budget, seed=seed,
        lift_board=True, lift_board_tilt_deg=tilt, lift_board_y_offset_m=y_offset_m,
    )
    summary.update({"seed": seed, "tilt_deg": tilt, "board_y_offset_m": y_offset_m, "teacher_k": k,
                    "teacher_budget": budget})
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20262101)
    parser.add_argument("--tilts", type=float, nargs="+", default=[30.0, 35.0, 40.0])
    parser.add_argument("--y-offsets", type=float, nargs="+", default=[-0.006, -0.002, 0.002, 0.006],
                        help="train-only board center y offsets, relative to the clearance placement")
    parser.add_argument("--per-tilt", type=int, default=2)
    parser.add_argument("--k", type=float, default=1.0)
    parser.add_argument("--budget", type=float, default=0.02)
    args = parser.parse_args()
    if args.per_tilt < 1 or not args.tilts:
        raise SystemExit("per-tilt and tilts must be non-empty positive values")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    index = 0
    for tilt in args.tilts:
        for local in range(args.per_tilt):
            seed = args.seed + index
            path = args.out_dir / f"inclined_tilt{tilt:g}_{local:02d}.npz"
            y_offset = float(args.y_offsets[local % len(args.y_offsets)])
            summary = record_one(args.menagerie, path, seed=seed, tilt=float(tilt), y_offset_m=y_offset,
                                 k=args.k, budget=args.budget)
            entries.append({"index": index, "trace": str(path), **summary})
            print(json.dumps(entries[-1]), flush=True)
            index += 1
    neutral_path = args.out_dir / "neutral_no_board.npz"
    neutral_summary = record(
        args.menagerie, make_fixture(args.seed + index), neutral_path,
        k=args.k, budget=args.budget, seed=args.seed + index, lift_board=False,
    )
    neutral = {"trace": str(neutral_path), **neutral_summary}
    print(json.dumps({"neutral": neutral}), flush=True)
    manifest = {
        "schema_version": 1,
        "split": "train_only",
        "observation_contract": "q, qdot, nominal_twist, pose_error, wbc_twist_error only",
        "teacher": {"family": "VMC", "k": args.k, "budget": args.budget},
        "board": {"tilts_deg": [float(v) for v in args.tilts],
                  "y_offsets_m": [float(v) for v in args.y_offsets],
                  "geometry_source": "MuJoCo lift_board in fr3_scene.py"},
        "entries": entries,
        "neutral": neutral,
    }
    manifest_path = args.out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"manifest": str(manifest_path),
                      "all_teacher_success": all(e["success"] for e in entries)}, indent=2))


if __name__ == "__main__":
    main()
