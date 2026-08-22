#!/usr/bin/env python3
"""Record fair 32-D VMC teacher traces for the physical dual-board task."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluate_dual_phase_four_method import fixture
from record_paper_mpc_expert_traces import record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20265301)
    parser.add_argument("--budget", type=float, default=0.04)
    parser.add_argument("--teacher-stiffness", type=float, default=0.5)
    parser.add_argument("--repeats", type=int, default=2)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    # Positive y jitter keeps both physical boards in the swept volume; z
    # jitter changes contact timing without creating reset overlap.  These are
    # training-scene parameters only and never enter the saved observation.
    conditions = [
        (y, z) for y in (0.0, 0.0015, 0.0030) for z in (-0.002, 0.0, 0.002)
    ]
    entries = []
    index = 0
    for y_offset, z_offset in conditions:
        for repeat in range(args.repeats):
            seed = args.seed + index
            path = args.out_dir / f"dual_y{y_offset:+.4f}_z{z_offset:+.4f}_{repeat:02d}.npz"
            summary = record(
                args.menagerie, fixture(seed), path,
                k=args.teacher_stiffness, budget=args.budget, seed=seed,
                lift_board=True, lift_board_tilt_deg=15.0,
                lift_board_y_offset_m=y_offset, lift_board_z_offset_m=z_offset,
                lift_board_contact_mode="dual_phase_longitudinal",
            )
            entry = {
                "index": index, "seed": seed, "trace": str(path),
                "board_y_offset_m": y_offset, "board_z_offset_m": z_offset,
                **summary,
            }
            entries.append(entry)
            print(json.dumps(entry), flush=True)
            index += 1
    accepted = [
        entry for entry in entries
        if entry["success"] and entry["dual_phase_geometry_valid"]
    ]
    manifest = {
        "schema_version": 1, "split": "development_train_only",
        "observation_contract": "q(7),qdot(7),nominal_twist(6),pose_error(6),twist_error(6); no board/contact/object truth",
        "teacher": {"family": "VMC torque residual", "stiffness": args.teacher_stiffness,
                    "residual_budget_fraction": args.budget},
        "conditions": conditions, "entries": entries,
        "accepted_traces": [entry["trace"] for entry in accepted],
        "all_accepted": len(accepted) == len(entries),
    }
    manifest_path = args.out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(manifest_path), "accepted": len(accepted),
                      "total": len(entries)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
