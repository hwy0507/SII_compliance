#!/usr/bin/env python3
"""Freeze the selected static VMC baseline on predeclared held-out fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


BASE_KAPPA = [27.579838, 52.550787, 48.699427, 35.859580, 40.719830, 34.766858]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--split", choices=("validation", "test"), default="test")
    args = parser.parse_args()
    source = json.loads(args.source_manifest.read_text())
    samples = []
    for sample in source["splits"][args.split]:
        samples.append({
            "sample_id": f"fixed_vmc_{sample['sample_id']}",
            "split": "held_out",
            "rod_stroke_m": sample["rod_stroke_m"],
            "rod_height_m": sample["rod_height_m"],
            "rod_start_time_s": sample["rod_start_time_s"],
            "grasp_time_s": sample["grasp_time_s"],
            "initial_kappa_vector": BASE_KAPPA,
        })
    manifest = {
        "schema_version": 1,
        "stage": "held-out static baseline validation before RL",
        "source_manifest": str(args.source_manifest),
        "source_split": args.split,
        "frozen_controller": {
            "kappa_vector": BASE_KAPPA,
            "contact_carriage_drive_scale": 8.0,
            "recovery_carriage_drive_scale": 14.0,
            "recovery_ramp_s": 0.08,
            "damping_ratio": 0.8,
            "explicit_translational_carriage_mass_kg": 1.0,
        },
        "effective_collision_gate": {"minimum_peak_contact_force_n": 15.0, "minimum_contact_impulse_ns": 0.45},
        "validity_gate": "finite + physical rod contact + stable rejoin + lift + hold + no hard torque limit + valid matched no-rod task",
        "training_contract": source["training_contract"],
        "splits": {"train": [], "validation": [], "test": samples},
    }
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(args.output_path)


if __name__ == "__main__":
    main()
