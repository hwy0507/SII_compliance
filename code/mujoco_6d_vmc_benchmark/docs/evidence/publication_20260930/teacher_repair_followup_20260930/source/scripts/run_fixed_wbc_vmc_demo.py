#!/usr/bin/env python3
"""Render a paired Panda fixed-WBC + VMC yield--rejoin grasp demonstration.

The script makes the control boundary explicit: a fixed-base Panda WBC emits
its target pose/twist and a low-level VMC-gated layer executes it compliantly.
The paired no-rod view replays the same WBC task, while the physical-rod view
shows yield, safe rejoin, grasp, and lift.  This is a MuJoCo demo, not a
hardware or mobile-Fetch WBC claim.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

from run_benchmark import VMCConfig
from run_rod_perturbation_benchmark import kappa_filename_tag, run_episode


KAPPA_6D = np.asarray([27.579838, 52.550787, 48.699427, 35.859580, 40.719830, 34.766858])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--camera-view", choices=("overview", "hand-closeup"), default="hand-closeup")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    config = replace(
        VMCConfig(zeta=0.8),
        carriage_drive_k_translation=VMCConfig().carriage_drive_k_translation * 8.0,
        carriage_drive_k_rotation=VMCConfig().carriage_drive_k_rotation * 8.0,
    )
    common = dict(
        menagerie=args.menagerie, kappa=KAPPA_6D, render_gif=True, config=config,
        rod_stroke_m=0.170, contact_time_constant_s=0.015,
        recovery_kappa=KAPPA_6D, recovery_ramp_s=0.08,
        recovery_drive_scale_factor=14.0 / 8.0, grasp_time_s=2.40,
        rod_start_time_s=0.995, explicit_translational_carriage=True,
        carriage_mass_kg=1.0, controller_mode="vmc_gated",
        rod_approach_side="negative_y", rod_height_m=0.540,
        rod_center_x_m=0.55, rod_center_y_m=0.0,
        recovery_gate_hold_s=0.28, recovery_gate_taper_s=0.04,
        reference_source="fixed_panda_wbc", camera_view=args.camera_view,
        render_start_time_s=0.82, render_end_time_s=3.80, playback_speed=0.50,
    )
    rod_dir, no_rod_dir = args.output_dir / "physical_rod", args.output_dir / "no_rod_reference"
    rod_dir.mkdir(parents=True, exist_ok=True)
    no_rod_dir.mkdir(parents=True, exist_ok=True)
    rod = run_episode(output_dir=rod_dir, rod_enabled=True, **common)
    no_rod = run_episode(output_dir=no_rod_dir, rod_enabled=False, remove_rod_when_disabled=True, **common)

    tag = kappa_filename_tag(KAPPA_6D)
    paired_gif = args.output_dir / "fixed_wbc_vmc_yield_rejoin_demo.gif"
    subprocess.run([
        sys.executable, str(Path(__file__).with_name("render_rod_comparison.py")),
        "--perturbed-gif", str(rod_dir / f"rod_perturbation_{tag}.gif"),
        "--perturbed-trace", str(rod_dir / f"rod_perturbation_{tag}_trace.npz"),
        "--reference-gif", str(no_rod_dir / f"rod_perturbation_{tag}.gif"),
        "--reference-trace", str(no_rod_dir / f"rod_perturbation_{tag}_trace.npz"),
        "--time-start", "0.82", "--time-end", "3.80", "--playback-speed", "0.50",
        "--output", str(paired_gif),
    ], check=True)
    payload = {
        "stage": "fixed-base Panda WBC + VMC-gated physical rod yield--rejoin demonstration",
        "scope": "MuJoCo Panda fixed-base WBC adapter; not Fetch WBC, hardware validation, or ESN",
        "policy_contract": "fixed WBC target generation -> bounded WBC task command -> causal VMC-gated low-level torque execution",
        "rod_summary": rod, "no_rod_summary": no_rod,
        "paired_demo_gif": str(paired_gif),
    }
    (args.output_dir / "fixed_wbc_vmc_demo_summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({
        "paired_demo_gif": str(paired_gif),
        "rod_validity": rod["task_validity"],
        "phase": rod["phase_analysis"],
        "wbc_interface": rod["wbc_interface"],
    }, indent=2))


if __name__ == "__main__":
    main()
