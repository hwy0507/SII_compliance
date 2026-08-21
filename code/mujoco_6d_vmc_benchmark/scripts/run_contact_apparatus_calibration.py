#!/usr/bin/env python3
"""Calibrate physically parameterized repeated-contact conditions in MuJoCo.

This is development-only infrastructure calibration, not a model-selection or
comparative test.  It validates four explicit external-apparatus models using
the same finite-mass, damped-slide, force-limited position-servo rod that a
real contact rig can approximate.  All physical values are logged in each
fixture manifest and hidden from all controllers.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_paper_mpc_benchmark import run_rollout  # noqa: E402
from wbc_velocity_residual_env import VelocityResidualFixture  # noqa: E402


def physical_calibration_fixtures() -> tuple[tuple[str, VelocityResidualFixture], ...]:
    """Prespecified physical contact-apparatus profiles, all two-pulse.

    ``solref`` time constant is MuJoCo's normal-contact softness parameter.
    The values form a transparent bounded envelope around the historical rod:
    0.18--0.50 kg moving tool/end-effector, 0.6--4 N s/m slide damping,
    2.5--9 kN/m position-loop gain, ±150--300 N driver capability, and
    8--25 ms contact time constant.  They model variability in a compliant
    pusher/human-contact rig rather than unexplained reward noise.
    """

    common = dict(rod_cycles=2, cycle_period_s=0.700)
    return (
        ("nominal", VelocityResidualFixture(0.170, 0.541, 0.960, **common)),
        ("soft_light", VelocityResidualFixture(
            0.170, 0.541, 0.960, impactor_mass_kg=0.18,
            rod_slide_damping=4.0, rod_driver_kp=2500.0,
            rod_driver_force_limit_n=150.0, contact_time_constant_s=0.025,
            **common)),
        ("medium", VelocityResidualFixture(
            0.170, 0.541, 0.960, impactor_mass_kg=0.36,
            rod_slide_damping=1.2, rod_driver_kp=6500.0,
            rod_driver_force_limit_n=250.0, contact_time_constant_s=0.012,
            **common)),
        ("stiff_heavy", VelocityResidualFixture(
            0.170, 0.541, 0.960, impactor_mass_kg=0.50,
            rod_slide_damping=0.6, rod_driver_kp=9000.0,
            rod_driver_force_limit_n=300.0, contact_time_constant_s=0.008,
            **common)),
        # Development-only deadline compression.  The 20 ms inter-pulse gap
        # remains physically realizable (the 640 ms waveform lasts less than
        # the 660 ms cycle), but the second retract finishes only 40 ms before
        # the existing 2.40 s gripper-close deadline.
        ("stiff_heavy_deadline", VelocityResidualFixture(
            0.170, 0.541, 1.060, rod_cycles=2, cycle_period_s=0.660,
            impactor_mass_kg=0.50, rod_slide_damping=0.6, rod_driver_kp=9000.0,
            rod_driver_force_limit_n=300.0, contact_time_constant_s=0.008)),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260832)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for index, (profile, fixture) in enumerate(physical_calibration_fixtures()):
        row = run_rollout(
            args.menagerie, fixture, impactor_kind="repeated_rod", controller=None,
            residual_scale=0.03, seed=args.seed, verbose_name=f"calibration/{profile}",
        )
        row["profile"] = profile
        row["fixture_index"] = index
        rows.append(row)
        print(
            f"{profile}: bouts={row['contact_bout_count']} force={row['obstacle_force_n']:.2f}N "
            f"grasp={row['at_grasp_err_mm']:.2f}mm success={row['task_success']}",
            flush=True,
        )
    output = {
        "schema_version": 1,
        "status": "development_only_physical_apparatus_calibration",
        "controller": "PaperMPC only; no compliance policy comparison",
        "fixture_profiles": [
            {"name": name, "parameters": asdict(fixture)}
            for name, fixture in physical_calibration_fixtures()
        ],
        "acceptance_criterion": (
            "Each retained profile must yield at least two hand-contact bouts, "
            "finite state, no hard torque limit, and a nontrivial pre-grasp tracking challenge."
        ),
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    main()
