#!/usr/bin/env python3
"""Run a resumable, paired MLP-vs-ESN overnight campaign on one server.

Each unit starts exactly two CPU-affined jobs concurrently: the current-state
MLP baseline and a selected Fan Ye ESN controller.  Their environment,
reward, seed, PPO budget, safety adapter, and physical fixtures are identical.
The only difference is the fixed 64-state reservoir appended to the ESN input.
No VMC script, stiffness action, virtual spring, or virtual-carriage state is
used by this launcher.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def _parse_csv(value: str) -> tuple[str, ...]:
    values = tuple(item.strip() for item in value.split(",") if item.strip())
    if not values:
        raise ValueError("comma-separated argument must contain at least one item")
    return values


def _train_command(
    python: str,
    repo: Path,
    *,
    output_dir: Path,
    menagerie: Path,
    manifest: Path,
    model_npz: Path,
    summary_json: Path,
    observation_mode: str,
    reward_profile: str,
    seed: int,
    total_timesteps: int,
    n_envs: int,
    checkpoint_interval: int,
    residual_window_end_at_grasp: bool,
    directional_phase_projection: bool,
) -> list[str]:
    command = [
        python, str(repo / "scripts" / "train_wbc_velocity_residual.py"),
        "--menagerie", str(menagerie),
        "--output-dir", str(output_dir),
        "--fixture-manifest", str(manifest),
        "--fixture-split", "train",
        "--fan-ye-model-npz", str(model_npz),
        "--fan-ye-train-summary-json", str(summary_json),
        "--observation-mode", observation_mode,
        "--reward-profile", reward_profile,
        "--total-timesteps", str(total_timesteps),
        "--n-envs", str(n_envs),
        "--seed", str(seed),
        "--checkpoint-interval", str(checkpoint_interval),
        "--device", "cpu",
    ]
    if residual_window_end_at_grasp:
        command.append("--residual-window-end-at-grasp")
    if directional_phase_projection:
        command.append("--directional-phase-projection")
    return command


def _evaluation_command(
    python: str,
    repo: Path,
    *,
    output_dir: Path,
    run_dir: Path,
    menagerie: Path,
    manifest: Path,
    model_npz: Path,
    summary_json: Path,
    observation_mode: str,
    reward_profile: str,
    residual_window_end_at_grasp: bool,
    directional_phase_projection: bool,
) -> list[str]:
    command = [
        python, str(repo / "scripts" / "evaluate_wbc_velocity_residual.py"),
        "--menagerie", str(menagerie),
        "--output-dir", str(output_dir),
        "--fixture-manifest", str(manifest),
        "--fixture-split", "validation",
        "--fan-ye-model-npz", str(model_npz),
        "--fan-ye-train-summary-json", str(summary_json),
        "--observation-mode", observation_mode,
        "--reward-profile", reward_profile,
        "--model", str(run_dir / "ppo_wbc_residual_final.zip"),
        "--vecnormalize", str(run_dir / "vecnormalize.pkl"),
    ]
    if residual_window_end_at_grasp:
        command.append("--residual-window-end-at-grasp")
    if directional_phase_projection:
        command.append("--directional-phase-projection")
    return command


def _validation_gate(report_path: Path) -> dict[str, Any]:
    if not report_path.exists():
        return {"passed": False, "reason": "evaluation report missing"}
    report = json.loads(report_path.read_text())
    summary = report["summary"]
    expected = int(summary["episode_count"])
    checks = {
        "task_success": int(summary["task_success_count"]) == expected,
        "matched_no_rod_success": int(summary["matched_no_rod_task_success_count"]) == expected,
        # The frozen neutral-WBC validation currently has one fixture just below
        # the 15-N effective-contact threshold, so this is a predeclared
        # validity floor rather than an action-dependent nine-of-nine target.
        "effective_collision_at_least_eight": int(summary["effective_collision_count"]) >= min(8, expected),
        "no_hard_torque_limit": int(summary["hard_torque_limit_count"]) == 0,
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "summary": summary,
    }


def _launch_pair(
    *,
    repo: Path,
    environment: dict[str, str],
    mlp_command: list[str],
    esn_command: list[str],
    mlp_dir: Path,
    esn_dir: Path,
    dry_run: bool,
) -> dict[str, Any]:
    if dry_run:
        return {"mlp_command": ["taskset", "-c", "0-9", *mlp_command], "esn_command": ["taskset", "-c", "10-19", *esn_command], "mlp_exit": None, "esn_exit": None}
    mlp_dir.mkdir(parents=True, exist_ok=True)
    esn_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    with (mlp_dir / "train.log").open("a") as mlp_log, (esn_dir / "train.log").open("a") as esn_log:
        mlp = subprocess.Popen(
            ["taskset", "-c", "0-9", *mlp_command], cwd=repo, env=environment,
            stdout=mlp_log, stderr=subprocess.STDOUT,
        )
        esn = subprocess.Popen(
            ["taskset", "-c", "10-19", *esn_command], cwd=repo, env=environment,
            stdout=esn_log, stderr=subprocess.STDOUT,
        )
        mlp_exit = mlp.wait()
        esn_exit = esn.wait()
    return {
        "mlp_command": ["taskset", "-c", "0-9", *mlp_command],
        "esn_command": ["taskset", "-c", "10-19", *esn_command],
        "mlp_exit": mlp_exit,
        "esn_exit": esn_exit,
        "elapsed_s": time.time() - started,
    }


def _evaluate_pair(
    *,
    repo: Path,
    environment: dict[str, str],
    mlp_command: list[str],
    esn_command: list[str],
    mlp_dir: Path,
    esn_dir: Path,
) -> dict[str, Any]:
    started = time.time()
    with (mlp_dir / "evaluation.log").open("w") as mlp_log, (esn_dir / "evaluation.log").open("w") as esn_log:
        mlp = subprocess.Popen(
            ["taskset", "-c", "0-9", *mlp_command], cwd=repo, env=environment,
            stdout=mlp_log, stderr=subprocess.STDOUT,
        )
        esn = subprocess.Popen(
            ["taskset", "-c", "10-19", *esn_command], cwd=repo, env=environment,
            stdout=esn_log, stderr=subprocess.STDOUT,
        )
        mlp_exit = mlp.wait()
        esn_exit = esn.wait()
    mlp_report = mlp_dir / "validation" / "wbc_velocity_residual_paired_evaluation.json"
    esn_report = esn_dir / "validation" / "wbc_velocity_residual_paired_evaluation.json"
    return {
        "mlp_exit": mlp_exit,
        "esn_exit": esn_exit,
        "elapsed_s": time.time() - started,
        "mlp_gate": _validation_gate(mlp_report),
        "esn_gate": _validation_gate(esn_report),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--fixture-manifest", type=Path, required=True)
    parser.add_argument("--fan-ye-model-npz", type=Path, required=True)
    parser.add_argument("--fan-ye-train-summary-json", type=Path, required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--seeds", default="20260840,20260841,20260842,20260843,20260844,20260845")
    parser.add_argument("--profiles", default="balanced,contact_safe,recovery_priority")
    parser.add_argument("--total-timesteps", type=int, default=2_000_000)
    parser.add_argument("--n-envs", type=int, default=8)
    parser.add_argument("--checkpoint-interval", type=int, default=100_000)
    parser.add_argument("--esn-observation-mode", choices=("fan_ye_esn", "fan_ye_multiscale_esn"), default="fan_ye_esn", help="Frozen v1 reservoir or the v2 fast/slow error-aware reservoir.")
    parser.add_argument("--directional-phase-projection", action="store_true", help="Use the same deployable WBC-error yield/rejoin projection in both lanes.")
    parser.add_argument("--residual-window-end-at-grasp", action="store_true", help="Return residual authority to fixed WBC at gripper-close; retain learned yielding only for approach/recovery.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.total_timesteps < 1 or args.n_envs != 8 or args.checkpoint_interval < 1:
        raise ValueError("this validated overnight launcher requires n-envs=8 and positive step/checkpoint counts")
    repo = args.repo.resolve()
    required = [
        repo / "scripts" / "train_wbc_velocity_residual.py",
        repo / "scripts" / "evaluate_wbc_velocity_residual.py",
        args.menagerie, args.fixture_manifest, args.fan_ye_model_npz, args.fan_ye_train_summary_json,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing required campaign paths: " + ", ".join(missing))
    if "post_v4_development" not in args.fixture_manifest.as_posix():
        raise ValueError("overnight campaign must use the isolated post-V4 development manifest")
    seeds = tuple(int(value) for value in _parse_csv(args.seeds))
    profiles = _parse_csv(args.profiles)
    allowed_profiles = {"balanced", "contact_safe", "recovery_priority", "impulse_constrained"}
    if not set(profiles) <= allowed_profiles:
        raise ValueError(f"profiles must be a subset of {sorted(allowed_profiles)}")
    args.output_root.mkdir(parents=True, exist_ok=True)
    status_path = args.output_root / "campaign_status.json"
    manifest_path = args.output_root / "campaign_manifest.json"
    manifest = {
        "controller_family": "independent_wbc_velocity_residual",
        "uses_vmc": False,
        "campaign_type": "paired_current_mlp_vs_fan_ye_esn",
        "esn_observation_mode": args.esn_observation_mode,
        "seeds": list(seeds),
        "profiles": list(profiles),
        "total_timesteps": args.total_timesteps,
        "n_envs_per_lane": args.n_envs,
        "cpu_affinity": {"current_mlp": "0-9", "fan_ye_esn": "10-19"},
        "fixture_manifest": str(args.fixture_manifest),
        "artifact_hashes": {str(path): _sha256(path) for path in required if path.is_file()},
        "fairness_contract": "matched seeds/profiles/steps/fixtures/PPO/safety/action; reservoir memory is the only MLP-vs-ESN difference",
        "v4_final_policy": "frozen and excluded",
        "residual_window_end_at_grasp": args.residual_window_end_at_grasp,
        "directional_phase_projection": args.directional_phase_projection,
    }
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
        raise RuntimeError("existing campaign manifest differs; choose a new output root rather than silently mixing runs")
    _write_json(manifest_path, manifest)
    environment = os.environ.copy()
    environment.update({"MUJOCO_GL": "egl", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    status: dict[str, Any] = json.loads(status_path.read_text()) if status_path.exists() else {"manifest": str(manifest_path), "runs": {}}
    for profile in profiles:
        for seed in seeds:
            run_id = f"{profile}_seed{seed}"
            mlp_dir = args.output_root / run_id / "current_mlp"
            esn_dir = args.output_root / run_id / "fan_ye_esn"
            complete = (
                (mlp_dir / "validation" / "wbc_velocity_residual_paired_evaluation.json").exists()
                and (esn_dir / "validation" / "wbc_velocity_residual_paired_evaluation.json").exists()
            )
            if complete:
                status["runs"].setdefault(run_id, {})["skipped_existing"] = True
                _write_json(status_path, status)
                continue
            entry: dict[str, Any] = {"profile": profile, "seed": seed, "started_unix_s": time.time(), "status": "training"}
            status["runs"][run_id] = entry
            _write_json(status_path, status)
            mlp_train = _train_command(
                args.python, repo, output_dir=mlp_dir, menagerie=args.menagerie, manifest=args.fixture_manifest,
                model_npz=args.fan_ye_model_npz, summary_json=args.fan_ye_train_summary_json,
                observation_mode="current_mlp", reward_profile=profile, seed=seed,
                total_timesteps=args.total_timesteps, n_envs=args.n_envs, checkpoint_interval=args.checkpoint_interval,
                residual_window_end_at_grasp=args.residual_window_end_at_grasp,
                directional_phase_projection=args.directional_phase_projection,
            )
            esn_train = _train_command(
                args.python, repo, output_dir=esn_dir, menagerie=args.menagerie, manifest=args.fixture_manifest,
                model_npz=args.fan_ye_model_npz, summary_json=args.fan_ye_train_summary_json,
                observation_mode=args.esn_observation_mode, reward_profile=profile, seed=seed,
                total_timesteps=args.total_timesteps, n_envs=args.n_envs, checkpoint_interval=args.checkpoint_interval,
                residual_window_end_at_grasp=args.residual_window_end_at_grasp,
                directional_phase_projection=args.directional_phase_projection,
            )
            entry["training"] = _launch_pair(
                repo=repo, environment=environment, mlp_command=mlp_train, esn_command=esn_train,
                mlp_dir=mlp_dir, esn_dir=esn_dir, dry_run=args.dry_run,
            )
            if args.dry_run:
                entry["status"] = "dry_run"
                _write_json(status_path, status)
                continue
            if entry["training"]["mlp_exit"] != 0 or entry["training"]["esn_exit"] != 0:
                entry["status"] = "training_failed"
                entry["finished_unix_s"] = time.time()
                _write_json(status_path, status)
                continue
            entry["status"] = "evaluating"
            _write_json(status_path, status)
            mlp_eval = _evaluation_command(
                args.python, repo, output_dir=mlp_dir / "validation", run_dir=mlp_dir, menagerie=args.menagerie,
                manifest=args.fixture_manifest, model_npz=args.fan_ye_model_npz,
                summary_json=args.fan_ye_train_summary_json, observation_mode="current_mlp", reward_profile=profile,
                residual_window_end_at_grasp=args.residual_window_end_at_grasp,
                directional_phase_projection=args.directional_phase_projection,
            )
            esn_eval = _evaluation_command(
                args.python, repo, output_dir=esn_dir / "validation", run_dir=esn_dir, menagerie=args.menagerie,
                manifest=args.fixture_manifest, model_npz=args.fan_ye_model_npz,
                summary_json=args.fan_ye_train_summary_json, observation_mode=args.esn_observation_mode, reward_profile=profile,
                residual_window_end_at_grasp=args.residual_window_end_at_grasp,
                directional_phase_projection=args.directional_phase_projection,
            )
            entry["evaluation"] = _evaluate_pair(
                repo=repo, environment=environment, mlp_command=mlp_eval, esn_command=esn_eval,
                mlp_dir=mlp_dir, esn_dir=esn_dir,
            )
            entry["status"] = "passed_validation_gate" if (
                entry["evaluation"]["mlp_gate"]["passed"] and entry["evaluation"]["esn_gate"]["passed"]
            ) else "completed_with_gate_failure"
            entry["finished_unix_s"] = time.time()
            _write_json(status_path, status)


if __name__ == "__main__":
    main()
