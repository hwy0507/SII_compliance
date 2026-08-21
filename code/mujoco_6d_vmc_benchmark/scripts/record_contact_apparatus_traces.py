#!/usr/bin/env python3
"""Generate train-only VMC demonstrations under randomized contact apparatuses.

The learned policy remains restricted to proprioception plus the nominal WBC
signals.  Mass, slide damping, actuator servo gain/force capability, contact
softness, pulse timing, and the VMC teacher's internal calculation are used
only to construct/label training rollouts; none are emitted in the Direct-ESN
input.  Evaluation seeds must be disjoint from ``--seed`` and are never read
by this generator.
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


def train_fixture(rng: np.random.Generator) -> VelocityResidualFixture:
    """One bounded physical two-pulse apparatus realization.

    Bounds are exactly the documented calibration envelope.  The second pulse
    ends before 2.40 s, so the grasp deadline has not been changed to favor a
    controller.  The fixed random generator seed makes every physical sample
    manifest-reproducible.
    """

    start = float(rng.uniform(0.90, 1.03))
    period = float(rng.uniform(0.66, 0.72))
    return VelocityResidualFixture(
        rod_stroke_m=float(rng.uniform(0.160, 0.176)),
        rod_height_m=float(rng.uniform(0.539, 0.542)),
        rod_start_time_s=start,
        rod_cycles=2,
        cycle_period_s=period,
        impactor_mass_kg=float(rng.uniform(0.18, 0.50)),
        rod_slide_damping=float(rng.uniform(0.6, 4.0)),
        rod_driver_kp=float(rng.uniform(2500.0, 9000.0)),
        rod_driver_force_limit_n=float(rng.uniform(150.0, 300.0)),
        contact_time_constant_s=float(rng.uniform(0.008, 0.025)),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--count", type=int, default=16)
    parser.add_argument("--seed", type=int, default=20260901)
    parser.add_argument("--teacher-k", type=float, default=1.5)
    parser.add_argument("--budget", type=float, default=0.03)
    args = parser.parse_args()
    if args.count < 1 or args.teacher_k <= 0.0 or not 0.0 < args.budget <= 1.0:
        raise SystemExit("count must be positive, teacher-k positive, and budget in (0,1]")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "split": "train_only",
        "generator_seed": args.seed,
        "count": args.count,
        "teacher": {"family": "VMCTorqueBaseline", "k": args.teacher_k, "budget": args.budget},
        "physical_ranges": {
            "impactor_mass_kg": [0.18, 0.50], "rod_slide_damping": [0.6, 4.0],
            "rod_driver_kp": [2500.0, 9000.0], "rod_driver_force_limit_n": [150.0, 300.0],
            "contact_time_constant_s": [0.008, 0.025], "rod_stroke_m": [0.160, 0.176],
            "rod_height_m": [0.539, 0.542], "rod_start_time_s": [0.90, 1.03],
            "cycle_period_s": [0.66, 0.72], "rod_cycles": 2,
        },
        "observation_contract": "q, qdot, nominal_twist, pose_error, wbc_twist_error only",
        "traces": [],
    }
    for index in range(args.count):
        fixture = train_fixture(np.random.default_rng(args.seed + index))
        path = args.out_dir / f"apparatus_train_{index:02d}.npz"
        summary = record(
            args.menagerie, fixture, path, k=args.teacher_k, budget=args.budget,
            seed=args.seed + index, side=None, lift_board=False,
        )
        row = {"index": index, "fixture": asdict(fixture), "trace": str(path), "summary": summary}
        manifest["traces"].append(row)
        print(json.dumps(row), flush=True)

    # A neutral trajectory ensures a repeat-trained readout has an explicit
    # zero-residual target away from contact.
    neutral = replace(VelocityResidualFixture(0.170, 0.541, 0.960), rod_start_time_s=99.0)
    neutral_path = args.out_dir / "no_rod.npz"
    neutral_summary = record(
        args.menagerie, neutral, neutral_path, k=args.teacher_k, budget=args.budget,
        seed=args.seed + args.count, side=None, lift_board=False,
    )
    manifest["traces"].append({
        "kind": "no_rod", "fixture": asdict(neutral), "trace": str(neutral_path), "summary": neutral_summary,
    })
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({
        "manifest": str(args.out_dir / "manifest.json"),
        "all_teacher_success": all(item["summary"]["success"] for item in manifest["traces"]),
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
