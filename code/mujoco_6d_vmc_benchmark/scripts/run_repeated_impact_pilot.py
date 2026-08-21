#!/usr/bin/env python3
"""Non-confirmatory MuJoCo calibration for repeated physical rod impacts.

This script deliberately has *no* parameter sweep or winner selection.  It
checks that a two-pulse, force-limited rod trajectory produces a meaningful
hard contact before a fixed grasp deadline, using the frozen ESN-303 and VMC
configurations.  Its output is a development/pilot artifact only; a later
validation/test split must be created before making a comparative claim.

The physical rod is the repository's existing MuJoCo slide body: 0.30 kg,
joint damping 2.0, position-servo kp=5000 and force range [-300, 300] N.  The
second pulse arrives during the recovery from the first, leaving 0.08--0.14 s
before the 2.40 s grasp deadline.  Neither controller receives pulse count,
phase, force, obstacle pose, or release time.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_benchmark import TORQUE_LIMITS  # noqa: E402
from run_paper_mpc_benchmark import run_rollout  # noqa: E402
from vmc_compliance_baseline import SpringCarriageConfig, load_controller  # noqa: E402
from vmc_torque_baseline import VMCTorqueBaseline  # noqa: E402
from wbc_velocity_residual_env import VelocityResidualFixture  # noqa: E402


def parse_seeds(value: str) -> list[int]:
    seeds = list(dict.fromkeys(int(item.strip()) for item in value.split(",") if item.strip()))
    if not seeds:
        raise argparse.ArgumentTypeError("seed list cannot be empty")
    return seeds


def repeated_rod_fixtures() -> tuple[VelocityResidualFixture, ...]:
    """Four matched, physically feasible two-impact conditions.

    The standard rod waveform lasts 0.64 s.  A 0.70 s period leaves a 60 ms
    physical retraction gap between pulses; start times make the second pulse
    end before the normal 2.40 s gripper-close deadline.  Heights/strokes stay
    span 0.160--0.176 m, a deliberately mild extension of the validated
    0.160--0.175 m single-impact ladder.  This supplies a small severity
    ladder rather than a different contact mechanism.
    """

    return (
        VelocityResidualFixture(0.160, 0.539, 0.920, rod_cycles=2, cycle_period_s=0.700),
        VelocityResidualFixture(0.166, 0.540, 0.940, rod_cycles=2, cycle_period_s=0.700),
        VelocityResidualFixture(0.172, 0.541, 0.960, rod_cycles=2, cycle_period_s=0.700),
        VelocityResidualFixture(0.176, 0.542, 0.980, rod_cycles=2, cycle_period_s=0.700),
    )


def summarize(rows: list[dict]) -> dict:
    return {
        "count": len(rows),
        "success_count": int(sum(bool(row["task_success"]) for row in rows)),
        "success_rate": float(np.mean([bool(row["task_success"]) for row in rows])),
        "effective_collision_count": int(sum(float(row["obstacle_force_n"]) >= 1.0 for row in rows)),
        "mean_at_grasp_err_mm": float(np.mean([float(row["at_grasp_err_mm"]) for row in rows])),
        "mean_peak_force_n": float(np.mean([float(row["obstacle_force_n"]) for row in rows])),
        "hard_limit_count": int(sum(bool(row["hard_limit"]) for row in rows)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--esn", type=Path, required=True)
    parser.add_argument("--seeds", type=parse_seeds, default=[20260829])
    parser.add_argument("--budget", type=float, default=0.03)
    parser.add_argument("--vmc-k", type=float, default=1.5)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 0.0 < args.budget <= 1.0 or args.vmc_k <= 0.0:
        raise SystemExit("budget must be in (0, 1] and vmc-k must be positive")

    esn = load_controller(args.esn)
    base = SpringCarriageConfig(k_translation_base=2.2, k_rotation_base=0.18)
    vmc_config = replace(
        base,
        k_translation_base=float(args.vmc_k),
        k_rotation_base=float(base.k_rotation_base * args.vmc_k / base.k_translation_base),
    )

    rows: list[dict] = []
    for seed in args.seeds:
        for fixture_index, fixture in enumerate(repeated_rod_fixtures()):
            controllers = (
                ("none", None),
                ("esn303", esn),
                ("vmc", VMCTorqueBaseline(vmc_config, TORQUE_LIMITS * args.budget)),
            )
            for method, controller in controllers:
                row = run_rollout(
                    args.menagerie, fixture, impactor_kind="repeated_rod", controller=controller,
                    residual_scale=args.budget, seed=seed,
                    verbose_name=f"pilot/{method}/fx{fixture_index}",
                )
                row["method"] = method
                row["fixture_index"] = fixture_index
                rows.append(row)
                print(
                    f"s{seed} {method} fx{fixture_index}: success={row['task_success']} "
                    f"force={row['obstacle_force_n']:.2f}N grasp={row['at_grasp_err_mm']:.2f}mm",
                    flush=True,
                )

    output = {
        "schema_version": 1,
        "status": "non_confirmatory_physics_calibration_only",
        "physical_model": {
            "impactor": "existing MuJoCo rod slide body",
            "rod_mass_kg": 0.30,
            "slide_joint_damping": 2.0,
            "position_servo_kp": 5000.0,
            "position_servo_force_range_n": [-300.0, 300.0],
            "contact_time_constant_s": 0.015,
        },
        "observation_contract": "q, qdot, nominal_twist, pose_error, wbc_twist_error only; no contact truth or pulse schedule",
        "frozen_controllers": {
            "esn": str(args.esn),
            "vmc_k": float(args.vmc_k),
            "residual_budget": float(args.budget),
        },
        "seeds": args.seeds,
        "fixtures": [asdict(fixture) for fixture in repeated_rod_fixtures()],
        "summary": {
            method: summarize([row for row in rows if row["method"] == method])
            for method in ("none", "esn303", "vmc")
        },
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
