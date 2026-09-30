"""Frozen evaluation of official SimbaV2 or canonical zero-action on Office.

Example (a JSON list is required):
  python evaluate.py --checkpoint /absolute/checkpoint --manifest cases.json \
      --output /absolute/new_output --physics-dt 0.00005
  python evaluate.py --zero-action --manifest smoke.json --duration 6.2 \
      --output /absolute/new_smoke

No training, reward shaping or normalization-statistics update occurs here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from office_env import OfficeEnv
from official_agent import OfficialOfficeAgent

DEFAULT_DT = .00005
ALLOWED = {"seed", "variant", "ball_speed", "person_stroke", "rod_stroke",
           "events", "physics_dt", "id", "label"}
CORE_METRICS = (
    "position_rmse_3d_m", "linear_speed_peak_mps",
    "generalized_actuator_torque_peak_nm",
    "generalized_actuator_torque_peak_by_joint_nm",
)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_manifest(path):
    entries = json.loads(Path(path).read_text())
    if not isinstance(entries, list) or not entries:
        raise ValueError("manifest must be a nonempty JSON list")
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or "seed" not in entry or "variant" not in entry:
            raise ValueError(f"case {index}: seed and variant required")
        if set(entry) - ALLOWED:
            raise ValueError(f"case {index}: unknown keys {set(entry)-ALLOWED}")
        if any(isinstance(entry[k], bool) or not isinstance(entry[k], int)
               for k in ("seed", "variant")):
            raise ValueError("seed and variant must be integers")
        if entry.get("events", "all") not in ("all", "ball", "person", "rod", "settle"):
            raise ValueError("unsupported event configuration")
        for key in ("ball_speed", "person_stroke", "rod_stroke", "physics_dt"):
            if key in entry and (not math.isfinite(entry[key]) or entry[key] <= 0):
                raise ValueError(f"{key} must be positive and finite")
    return entries


def load_frozen_agent(path):
    state = json.loads((Path(path) / "official_agent_state.json").read_text())
    config = state["config"]
    utd = int(state["utd"])
    decay = int(config["learning_rate_decay_step"])
    if decay % utd:
        raise ValueError("saved LR schedule cannot reconstruct training budget")
    agent = OfficialOfficeAgent(
        seed=int(config["seed"]), total_steps=decay // utd,
        utd=utd, gamma=float(config["gamma"]))
    agent.load(path)
    return agent


def extract_result(result_path):
    """Use audited substep summary and literal task gates, never stage labels."""
    raw = json.loads(Path(result_path).read_text())
    metrics = raw["metrics"]
    for key in CORE_METRICS:
        if key not in metrics:
            raise ValueError(f"missing audited metric: {key}")
    for key in ("physical_valid", "placement_complete", "task_success",
                "strict_success", "contact_coverage_valid", "passed"):
        if key not in raw or not isinstance(raw[key], bool):
            raise ValueError(f"missing/nonboolean result gate: {key}")
    return dict(
        position_rmse_3d_m=float(metrics["position_rmse_3d_m"]),
        peak_velocity_mps=float(metrics["linear_speed_peak_mps"]),
        peak_torque_nm=float(metrics["generalized_actuator_torque_peak_nm"]),
        peak_torque_by_joint_nm=metrics["generalized_actuator_torque_peak_by_joint_nm"],
        physical_valid=raw["physical_valid"],
        placement_complete=raw["placement_complete"],
        task_success=raw["task_success"],
        strict_success=raw["strict_success"],
        contact_coverage_valid=raw["contact_coverage_valid"],
        apparatus_passed=raw["passed"],
        full_task_horizon_completed=raw.get("full_task_horizon_completed"),
        execution_complete=raw.get("execution_complete"),
        final_stage_diagnostic_only=raw.get("final_task_stage"),
        abort_reason=raw.get("abort_reason"),
        max_external_penetration_m=raw["stats"]["max_external_penetration_m"],
        substep_samples=int(metrics["samples"]),
        metrics_reference="current commanded task-stage waypoint; all audited physical substeps",
        rmse_weighting=metrics["rmse_weighting"],
        event_contacts=raw["stats"]["events"],
        validator_source_sha256=raw.get("source_sha256", {}),
        model_sha256=raw.get("model_sha256"),
    )


def aggregate(rows):
    if not rows:
        return {}
    return dict(
        episodes=len(rows),
        physical_valid_count=sum(r["physical_valid"] for r in rows),
        placement_count=sum(r["placement_complete"] for r in rows),
        task_success_count=sum(r["task_success"] for r in rows),
        strict_success_count=sum(r["strict_success"] for r in rows),
        arithmetic_mean_across_episode_metrics={
            k:float(np.mean([r[k] for r in rows]))
            for k in ("position_rmse_3d_m", "peak_velocity_mps", "peak_torque_nm")},
        worst_peak_across_episodes={
            k:float(max(r[k] for r in rows))
            for k in ("peak_velocity_mps", "peak_torque_nm")},
        interpretation="means include physical/task failures; these are not success-conditioned rankings",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--checkpoint", type=Path)
    group.add_argument("--zero-action", action="store_true")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=55.)
    parser.add_argument("--physics-dt", type=float, default=None,
                        help="override all manifest physics_dt values (default fallback 5e-5)")
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    if args.duration < 6.2 or not math.isfinite(args.duration):
        parser.error("Office validator requires duration >= 6.2 seconds")
    if args.physics_dt is not None and (args.physics_dt <= 0 or not math.isfinite(args.physics_dt)):
        parser.error("physics-dt must be positive")
    entries = load_manifest(args.manifest)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    agent = load_frozen_agent(args.checkpoint.resolve()) if args.checkpoint else None
    before_stats = agent.diagnostics() if agent else None
    effective = []
    for entry in entries:
        case = dict(entry)
        case["physics_dt"] = (args.physics_dt if args.physics_dt is not None
                              else entry.get("physics_dt", DEFAULT_DT))
        case["duration_s"] = args.duration
        effective.append(case)
    protocol = dict(
        algorithm="official_simbav2" if agent else "canonical_zero_action",
        checkpoint=str(args.checkpoint.resolve()) if args.checkpoint else None,
        checkpoint_state_sha256=(sha256(args.checkpoint / "official_agent_state.json")
                                 if agent else None),
        manifest_source=str(args.manifest.resolve()),
        manifest_sha256=sha256(args.manifest),
        effective_manifest=effective,
        duration_s=args.duration,
        classification="smoke_only" if args.duration != 55. else "frozen_development_evaluation",
        deterministic_policy=True, normalizer_statistics_frozen=True,
        raw_substeps_saved=True,
        action_contract="canonical slowdown plus Cartesian residuals, normalized action7; common filter only",
        sample_reference="current task-stage waypoint; full episode physical-time RMSE",
        success_source="literal validator task_success/strict_success/placement_complete fields",
        source_sha256={name:sha256(Path(__file__).with_name(name))
                       for name in ("evaluate.py", "official_agent.py", "office_env.py")},
    )
    write_json(output / "PROTOCOL.json", protocol)
    rows = []
    for index, case in enumerate(effective):
        episode_root = output / f"case_{index:03d}"
        env = OfficeEnv(episode_root, rewarder=None, duration=args.duration,
                        physics_dt=case["physics_dt"], save_substeps=True)
        options = {k:case[k] for k in ("variant","ball_speed","person_stroke",
                                      "rod_stroke","events") if k in case}
        options["render"] = args.render
        try:
            obs, initial_info = env.reset(seed=case["seed"], options=options)
            actions = []
            while True:
                action = (agent.sample_action(obs, training=False) if agent
                          else np.zeros(7, dtype=np.float32))
                actions.append(np.asarray(action).copy())
                obs, done, info = env.step_raw(action)
                if done:
                    break
            raw_path = env.args.output.with_suffix(".json")
            substep_path = raw_path.parent / (raw_path.stem + "_metrics") / "substep_metrics.npz"
            if not substep_path.is_file():
                raise RuntimeError("validator did not save promised raw substep arrays")
            row = extract_result(raw_path)
            row.update(case_index=index, condition=case,
                       raw_result_json=str(raw_path),
                       raw_substep_npz=str(substep_path),
                       requested_actions_npz=str(episode_root / "requested_actions.npz"))
            np.savez_compressed(episode_root / "requested_actions.npz",
                                action=np.asarray(actions))
            write_json(episode_root / "EVALUATION.json", row)
            rows.append(row)
            if agent and before_stats != agent.diagnostics():
                raise AssertionError("evaluation modified normalization statistics or update counters")
            write_json(output / "SUMMARY.json",
                       dict(status="running", protocol=protocol, rows=rows,
                            aggregate=aggregate(rows)))
            print(json.dumps(dict(case=index, metrics={k:row[k] for k in
                      ("position_rmse_3d_m","peak_velocity_mps","peak_torque_nm","strict_success")})),
                  flush=True)
        except BaseException as error:
            write_json(output / "FAILURE.json",
                       dict(case=index,error=repr(error),completed=len(rows)))
            raise
        finally:
            env.close()
    write_json(output / "SUMMARY.json",
               dict(status="complete", protocol=protocol, rows=rows,
                    aggregate=aggregate(rows),normalizer_before=before_stats,
                    normalizer_after=agent.diagnostics() if agent else None))


if __name__ == "__main__":
    main()
