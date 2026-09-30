#!/usr/bin/env python3
"""Generate a deterministic static-search and RL-training preparation manifest.

The manifest contains only predeclared, physically plausible fixture
randomizations and low-rate six-dimensional stiffness actions.  It does not
run MuJoCo; ``run_training_manifest.py`` will be the later evaluator after the
static-search gate is accepted.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from stiffness_training_core import StiffnessActionConfig, latin_hypercube, scenario_from_unit, training_contract


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--train-samples", type=int, default=32)
    parser.add_argument("--validation-samples", type=int, default=8)
    parser.add_argument("--test-samples", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260814)
    args = parser.parse_args()
    counts = {"train": args.train_samples, "validation": args.validation_samples, "test": args.test_samples}
    if any(value < 1 for value in counts.values()):
        raise ValueError("each split must contain at least one sample")

    config = StiffnessActionConfig()
    splits = {}
    for index, (name, count) in enumerate(counts.items()):
        design = latin_hypercube(count, 10, args.seed + index)
        splits[name] = [
            {"sample_id": f"{name}_{sample_index:03d}", "split": name, **scenario_from_unit(unit, config)}
            for sample_index, unit in enumerate(design)
        ]
    manifest = {
        "schema_version": 1,
        "seed": args.seed,
        "stage": "training-preparation; static LHS evaluation precedes RL",
        "training_contract": training_contract(config),
        "randomization": {
            "method": "Latin hypercube, deterministic by seed",
            "ranges": {
                "rod_stroke_m": [0.155, 0.180],
                "rod_height_m": [0.538, 0.542],
                "rod_start_time_s": [1.040, 1.120],
                "grasp_time_s": 2.40,
            },
            "held_constant_for_first_stage": ["rod direction (+Y)", "rod mass", "contact solver parameters", "reference trajectory", "torque limits"],
        },
        "splits": splits,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / "stiffness_training_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(path)


if __name__ == "__main__":
    main()
