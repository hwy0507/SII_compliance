#!/usr/bin/env python3
"""Record disjoint train-only demonstrations spanning contact directions/forms.

The ESN never receives the domain label.  Direction, probe shape and apparatus
parameters only construct MuJoCo scenes; VMC actions become offline labels.
Each trace records its own torque budget so the bootstrap can convert actions
to one common ESN deployment budget without a silent scale mismatch.
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


def fixture(rng: np.random.Generator, *, side: str, kind: str) -> VelocityResidualFixture:
    return VelocityResidualFixture(
        rod_stroke_m=float(rng.uniform(0.160, 0.176)), rod_height_m=float(rng.uniform(0.539, 0.542)),
        rod_start_time_s=float(rng.uniform(0.90, 1.03)), rod_approach_side=side, impactor_type=kind,
        rod_cycles=2, cycle_period_s=float(rng.uniform(0.66, 0.72)),
        impactor_mass_kg=float(rng.uniform(0.18, 0.50)), rod_slide_damping=float(rng.uniform(0.6, 4.0)),
        rod_driver_kp=float(rng.uniform(2500.0, 9000.0)),
        rod_driver_force_limit_n=float(rng.uniform(150.0, 300.0)),
        contact_time_constant_s=float(rng.uniform(0.008, 0.025)),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261301)
    parser.add_argument("--per-domain", type=int, default=10)
    args = parser.parse_args()
    if args.per_domain < 1:
        raise SystemExit("per-domain must be positive")
    # These are train-only teacher choices, selected from prior independent
    # protocols: stiff/high-authority VMC for -y rod, soft/low-authority VMC
    # for +y palm.  The student later converts both physical actions to 5%.
    domains = (("negative_y_rod", "negative_y", "rod", 2.2, 0.05),
               ("positive_y_hand", "positive_y", "hand_proxy", 1.0, 0.02))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"schema_version": 1, "split": "train_only", "generator_seed": args.seed,
                "domains": [], "observation_contract": "q, qdot, nominal_twist, pose_error, wbc_twist_error only"}
    index = 0
    for name, side, kind, k, budget in domains:
        entries = []
        for local in range(args.per_domain):
            fx = fixture(np.random.default_rng(args.seed + index), side=side, kind=kind)
            path = args.out_dir / f"{name}_{local:02d}.npz"
            summary = record(args.menagerie, fx, path, k=k, budget=budget, seed=args.seed + index)
            entry = {"index": index, "fixture": asdict(fx), "trace": str(path), "teacher": {"k": k, "budget": budget}, "summary": summary}
            entries.append(entry); print(json.dumps(entry), flush=True); index += 1
        manifest["domains"].append({"name": name, "entries": entries})
    neutral = replace(VelocityResidualFixture(0.170, 0.541, 0.960), rod_start_time_s=99.0)
    path = args.out_dir / "neutral_no_rod.npz"
    summary = record(args.menagerie, neutral, path, k=1.0, budget=0.02, seed=args.seed + index)
    manifest["neutral"] = {"fixture": asdict(neutral), "trace": str(path), "teacher": {"k": 1.0, "budget": 0.02}, "summary": summary}
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"manifest": str(args.out_dir / "manifest.json"), "all_teacher_success": all(e['summary']['success'] for d in manifest['domains'] for e in d['entries']) and summary['success']}, indent=2))


if __name__ == "__main__":
    main()
