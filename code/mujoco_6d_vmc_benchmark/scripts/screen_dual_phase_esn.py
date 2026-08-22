#!/usr/bin/env python3
"""Development-only ESN dynamics screen for the dual-board task."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from bootstrap_direct_esn_multifixture import _load_episode
from direct_esn_compliance import DirectESNConfig, DirectESNController
from evaluate_dual_phase_four_method import aggregate, make_vmc, run_one


def specs() -> list[dict[str, object]]:
    # Fixed before seeing the development results: single- and multi-timescale
    # reservoirs, three memory regimes, and modest readout smoothing variants.
    return [
        {"size": 160, "rho": .85, "input": .35, "tc": .04, "ridge": 1e-4, "alpha": 1.0, "seed": 20265501},
        {"size": 160, "rho": .92, "input": .45, "tc": .08, "ridge": 1e-4, "alpha": .85, "seed": 20265502},
        {"size": 160, "rho": .98, "input": .60, "tc": .16, "ridge": 3e-4, "alpha": .70, "seed": 20265503},
        {"size": 320, "rho": .85, "input": .45, "tc": .04, "ridge": 3e-5, "alpha": .85, "seed": 20265504},
        {"size": 320, "rho": .92, "input": .35, "tc": .08, "ridge": 1e-4, "alpha": .70, "seed": 20265505},
        {"size": 320, "rho": .98, "input": .60, "tc": .16, "ridge": 3e-4, "alpha": .50, "seed": 20265506},
        {"size": 480, "rho": .88, "input": .25, "tc": .08, "ridge": 1e-4, "alpha": .85, "seed": 20265507},
        {"size": 480, "rho": .94, "input": .45, "tc": .12, "ridge": 3e-4, "alpha": .70, "seed": 20265508},
        {"size": 320, "rho": .90, "input": .35, "multi": (.04, .12), "ridge": 1e-4, "alpha": .85, "seed": 20265509},
        {"size": 320, "rho": .94, "input": .45, "multi": (.04, .16), "ridge": 3e-4, "alpha": .70, "seed": 20265510},
        {"size": 480, "rho": .90, "input": .35, "multi": (.06, .16), "ridge": 1e-4, "alpha": .70, "seed": 20265511},
        {"size": 480, "rho": .98, "input": .60, "multi": (.08, .16), "ridge": 1e-3, "alpha": .50, "seed": 20265512},
    ]


def fit(spec: dict[str, object], traces: list[Path], output: Path) -> tuple[DirectESNController, float]:
    multi = spec.get("multi")
    config = DirectESNConfig(
        reservoir_size=int(spec["size"]), spectral_radius=float(spec["rho"]),
        input_scale=float(spec["input"]), time_constant_s=float(spec.get("tc", .12)),
        multiscale_time_constants_s=None if multi is None else tuple(multi),
        ridge_lambda=float(spec["ridge"]), seed=int(spec["seed"]),
        yield_smoothing_alpha=float(spec["alpha"]),
    )
    model = DirectESNController(config)
    features, labels = [], []
    for path in traces:
        observations, actions, budget = _load_episode(path, 1, "bounded_action")
        if budget is None or not np.isclose(budget, .04):
            raise ValueError(f"{path}: expected 4% teacher budget")
        features.append(model.features(observations, washout_steps=3))
        labels.append(actions[3:])
    mse = model.fit_readout(np.concatenate(features), np.concatenate(labels))
    model.save_npz(output)
    return model, float(mse)


def evaluate(menagerie: Path, label: str, controller) -> tuple[dict, list[dict]]:
    rows = []
    for seed in (20265401, 20265402):
        for y in (0.0, 0.0015, 0.0030):
            for z in (-0.002, 0.0, 0.002):
                rows.append(run_one(
                    menagerie, label, controller, seed=seed, budget=.04,
                    board_y_offset_m=y, board_z_offset_m=z,
                ))
    return aggregate(rows), rows


def physical_loss(summary: dict, vmc: dict) -> float:
    keys = (
        "mean_pre_peak_force_n", "mean_pre_impulse_ns",
        "mean_post_peak_force_n", "mean_post_impulse_ns", "mean_peak_jerk_mps3",
    )
    return float(np.mean([
        float(summary[key]) / max(float(vmc[key]), 0.05) for key in keys
    ]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--teacher-manifest", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.teacher_manifest.read_text())
    traces = [Path(path) for path in manifest["accepted_traces"]]
    if len(traces) != 18:
        raise ValueError("expected the predeclared 18 accepted training traces")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    vmc_summary, vmc_rows = evaluate(args.menagerie, "VMC_dev", make_vmc(.04, .5))
    records = []
    all_rows = list(vmc_rows)
    for index, spec in enumerate(specs()):
        model_path = args.out_dir / f"esn_{index:02d}.npz"
        controller, mse = fit(spec, traces, model_path)
        summary, rows = evaluate(args.menagerie, f"ESN_{index:02d}", controller)
        loss = physical_loss(summary, vmc_summary)
        record = {
            "index": index, "model": str(model_path), "spec": spec,
            "reservoir": asdict(controller.config), "training_mse": mse,
            "summary": summary, "physical_loss_vs_vmc": loss,
        }
        records.append(record)
        all_rows.extend(rows)
        print(json.dumps(record), flush=True)
    selected = max(records, key=lambda item: (
        item["summary"]["success_rate"], item["summary"]["geometry_valid_rate"],
        -item["physical_loss_vs_vmc"], item["summary"]["mean_final_target_lift_mm"],
    ))
    output = {
        "schema_version": 1, "status": "development_only_not_confirmatory",
        "selection_rule": "success, geometry validity, then equal mean of pre/post force, impulse and jerk ratios to VMC",
        "observation_contract": manifest["observation_contract"],
        "teacher_manifest": str(args.teacher_manifest), "vmc": vmc_summary,
        "candidates": records, "selected": selected, "rows": all_rows,
    }
    path = args.out_dir / "screen.json"
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"selected": selected, "output": str(path)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
