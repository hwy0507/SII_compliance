"""End-to-end source audit, matched training, and guarded-push evaluation."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False))
    temporary.replace(path)


def launch_training(job, dataset: Path, output: Path, epochs: int):
    model, seed = job
    folder = output / "models" / model / f"seed_{seed}"
    complete = folder / "TRAINING_COMPLETE.json"
    if complete.exists():
        return model, seed, json.loads(complete.read_text())
    command = [sys.executable, str(ROOT / "scripts" / "train_matched_action7_20260921.py"),
               "--dataset", str(dataset), "--output", str(folder), "--model", model,
               "--seed", str(seed), "--epochs", str(epochs), "--steps-per-epoch", "48",
               "--batch-size", "4096", "--evaluate-every", "5"]
    environment = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    folder.parent.mkdir(parents=True, exist_ok=True)
    with (folder.parent / f"seed_{seed}.log").open("w") as log:
        completed_process = subprocess.run(command, cwd=ROOT, env=environment,
                                           stdout=log, stderr=subprocess.STDOUT, timeout=7200)
    if completed_process.returncode or not complete.exists():
        raise RuntimeError(f"Training failed: {model} seed {seed}")
    return model, seed, json.loads(complete.read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "outputs" / "four_scene_pareto_teacher_v1_20260918")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--epochs", type=int, default=100)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    started = time.time()
    certificate = json.loads((args.dataset / "quality_certificate.json").read_text())
    ready = json.loads((args.dataset / "READY.json").read_text())
    if not certificate.get("ready") or not ready.get("ready") or not certificate.get("physics_groups_disjoint"):
        raise RuntimeError("A fixture-disjoint audited teacher bank is required")
    protocol = {"dataset": str(args.dataset), "dataset_certificate": certificate,
                "models": ["mlp", "esn_nonlinear", "esn_linear"],
                "seeds": [20260921, 20260922, 20260923],
                "selection": "lowest balanced source-validation scaled action MSE per model family",
                "complex_office_used_for_training_or_selection": False,
                "guarded_push_role": "development transfer diagnostic only"}
    dump(args.output / "protocol.json", protocol)
    jobs = [(model, seed) for model in protocol["models"] for seed in protocol["seeds"]]
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(launch_training, job, args.dataset, args.output, args.epochs) for job in jobs]
        for future in as_completed(futures):
            model, seed, result = future.result(); results.append({"model": model, "seed": seed, **result})
            dump(args.output / "training_results.json", results)
            dump(args.output / "status.json", {"phase": "training", "completed": len(results),
                                                "total": len(jobs), "elapsed_s": time.time() - started})
    selected = {}
    for model in protocol["models"]:
        candidates = [row for row in results if row["model"] == model]
        best = min(candidates, key=lambda row: row["validation"]["balanced_scaled_mse"])
        selected[model] = {"seed": best["seed"],
                           "checkpoint": str(args.output / "models" / model / f"seed_{best['seed']}" / "best.npz"),
                           "validation": best["validation"], "test": best["test"],
                           "trainable_parameters": best["trainable_parameters"]}
    selection = {"selected": selected, "selection_uses_office": False,
                 "selection_metric": "balanced source-validation scaled action MSE"}
    dump(args.output / "selection.json", selection)
    evaluation = args.output / "guarded_push_evaluation"
    command = [sys.executable, str(ROOT / "scripts" / "evaluate_matched_guarded_push_20260921.py"),
               "--selection", str(args.output / "selection.json"), "--output", str(evaluation),
               "--workers", "12"]
    with (args.output / "guarded_push_evaluation.log").open("w") as log:
        completed = subprocess.run(command, cwd=ROOT,
                                   env=dict(os.environ, MUJOCO_GL="egl", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1"),
                                   stdout=log, stderr=subprocess.STDOUT, timeout=7200)
    if completed.returncode:
        raise RuntimeError("Guarded-push evaluation failed")
    summary = json.loads((evaluation / "summary.json").read_text())
    final = {"phase": "complete", "elapsed_s": time.time() - started,
             "selection": selection, "guarded_push": summary,
             "scope": "audited source holdout plus guarded-push development transfer; final office test not run"}
    dump(args.output / "FINAL_RESULT.json", final)
    dump(args.output / "status.json", final)
    print(json.dumps(final, indent=2), flush=True)


if __name__ == "__main__":
    main()
