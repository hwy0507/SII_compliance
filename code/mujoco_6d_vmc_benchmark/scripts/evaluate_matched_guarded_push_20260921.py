"""Paired guarded-push closed-loop evaluation for frozen matched students."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False))
    temporary.replace(path)


def run(job, output: Path, reference: dict, base_panel: dict, vmc_config: dict):
    method, model, fixture = job
    seed = fixture["seed"]; angle = fixture["push_angle"]
    stem = output / method / fixture["id"] / "rollout"
    stem.parent.mkdir(parents=True, exist_ok=True)
    arguments = {key: value for key, value in reference.items()
                 if value is not None and key not in ("output", "render", "settle_only", "model")}
    arguments.update(seed=seed, event_stage="loaded_lift", push_angle=angle,
                     push_height=fixture["push_height"], payload_mass=fixture["payload_mass"],
                     duration=24.)
    command = [sys.executable, str(ROOT / "scripts" / "run_panel_push_20260920.py"),
               "--output", str(stem)]
    for key, value in arguments.items():
        command += ["--" + key.replace("_", "-"), str(value)]
    if model is not None:
        command += ["--model", str(model)]
    panel = dict(base_panel, rod_height_m=fixture["push_height"])
    environment = dict(os.environ, CORE_VMC_CONFIG=json.dumps(vmc_config),
                       PANEL_CONFIG=json.dumps(panel), PANELS_ENABLED="1", MUJOCO_GL="egl",
                       OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    dump(stem.with_suffix(".command.json"), {"argv": command, "method": method,
                                             "model": None if model is None else str(model),
                                             "panel": panel, "vmc_config": vmc_config})
    with stem.with_suffix(".log").open("w") as log:
        completed = subprocess.run(command, cwd=ROOT, env=environment, stdout=log,
                                   stderr=subprocess.STDOUT, timeout=1200)
    if completed.returncode or not stem.with_suffix(".json").exists():
        return {"method": method, "fixture": fixture, "strict_success": False,
                "execution_error": f"returncode={completed.returncode}"}
    result = json.loads(stem.with_suffix(".json").read_text())
    contact = result["contact"]
    with np.load(stem.with_suffix(".npz"), allow_pickle=False) as trace:
        time_values = trace["time"]
        position = trace["position"]
        target = trace["target"]
        velocity = trace["twist"][:, :3]
        torque = trace["torque"]
    first_contact = contact.get("first_s")
    window = time_values >= first_contact if first_contact is not None else np.ones(len(time_values), dtype=bool)
    tracking_rmse = float(np.sqrt(np.mean(np.sum((position[window] - target[window]) ** 2, axis=1))))
    speed = np.linalg.norm(velocity, axis=1)
    acceleration = np.linalg.norm(np.diff(velocity, axis=0) / .04, axis=1)
    jerk = np.linalg.norm(np.diff(velocity, n=2, axis=0) / (.04 ** 2), axis=1)
    penetration = float(contact.get("all_external_max_penetration_m", 1.))
    strict = bool(result.get("success") and result.get("grasp_lift_success") and
                  not result.get("invalid_physics") and penetration < .0002)
    return {
        "method": method, "fixture": fixture, "strict_success": strict,
        "task_success": bool(result.get("success")), "grasp_lift_success": bool(result.get("grasp_lift_success")),
        "tracking_rmse_after_contact_m": tracking_rmse,
        "speed_p95_mps": float(np.percentile(speed, 95)), "speed_peak_mps": float(speed.max()),
        "acceleration_p95_mps2": float(np.percentile(acceleration, 95)),
        "jerk_p95_mps3": float(np.percentile(jerk, 95)),
        "peak_contact_force_n": float(contact.get("all_external_peak_force_n", 0.)),
        "peak_motor_torque_nm": float(np.max(np.abs(torque))),
        "max_penetration_m": penetration, "endpoint_error_m": float(result.get("endpoint_error_m", 1.)),
        "lift_m": float(result.get("lift_m", 0.)), "contact_bodies": contact.get("robot_bodies", []),
        "result": str(stem.with_suffix(".json")), "trace": str(stem.with_suffix(".npz")),
    }


def aggregate(rows: list[dict]) -> dict:
    output = {}
    for method in sorted({row["method"] for row in rows}):
        part = [row for row in rows if row["method"] == method]
        valid = [row for row in part if "execution_error" not in row]
        output[method] = {
            "n": len(part), "completed": len(valid),
            "strict_successes": sum(row.get("strict_success", False) for row in valid),
            "task_successes": sum(row.get("task_success", False) for row in valid),
        }
        for key in ("tracking_rmse_after_contact_m", "speed_p95_mps", "speed_peak_mps",
                    "acceleration_p95_mps2", "jerk_p95_mps3", "peak_contact_force_n",
                    "peak_motor_torque_nm", "max_penetration_m", "endpoint_error_m"):
            values = [row[key] for row in valid if key in row]
            if values:
                output[method][key + "_median"] = float(np.median(values))
                output[method][key + "_worst"] = float(np.max(values))
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    if (args.output / "protocol.json").exists():
        raise RuntimeError("Evaluation output already contains a protocol; refusing to overwrite")
    args.output.mkdir(parents=True, exist_ok=True)
    selection = json.loads(args.selection.read_text())
    models = {name: Path(value["checkpoint"]) for name, value in selection["selected"].items()}
    reference = json.loads((ROOT / "web_demo" / "assets" / "loaded_push_release_20260918" / "rollout.json").read_text())["arguments"]
    panel = {"layout": "raised_hand_rim", "pad_bottom_z": .55, "pad_top_z": .71,
             "pad_lower_y": -.15, "pad_upper_y": -.085, "front_inner_x": .595,
             "back_inner_x": .500, "pad_thickness": .015, "end_effector_only": False,
             "rod_height_m": .58, "workstation": True}
    vmc_config = {"stiffness_6d": [520, 360, 1400, 12, 10, 14],
                  "damping_6d": [32, 27, 62, 3, 2.7, 3.3],
                  "mass_6d": [.5, .5, .8, .06, .06, .08],
                  "wrench_limit_6d": [35, 35, 50, 3, 3, 3],
                  "deadband_6d": [.2, .2, .2, .03, .03, .03],
                  "velocity_limit_6d": [.12, .12, .16, .55, .55, .65],
                  "offset_limit_6d": [.18, .18, .18, .35, .35, .35],
                  "action_limit_6d": [.16, .16, .2, .6, .6, .6],
                  "offset_tracking_gain_6d": 1.4, "filter_tau": .04,
                  "axis_rotation_rpy": [.35, 0, -.25]}
    profiles = ((.575, .085), (.580, .100), (.585, .115))
    conditions = []
    for angle_index, angle in enumerate((-.15, -.05, .10)):
        for profile_index, (height, payload) in enumerate(profiles):
            conditions.append({"id": f"angle_{angle:+.2f}_h_{height:.3f}_m_{payload:.3f}",
                               "seed": 9200 + angle_index * 10 + profile_index,
                               "push_angle": angle, "push_height": height,
                               "payload_mass": payload})
    jobs = [("vmc", None, fixture) for fixture in conditions]
    for method, checkpoint in models.items():
        jobs.extend((method, checkpoint, fixture) for fixture in conditions)
    protocol = {"role": "source-development guarded-push transfer; not final office test",
                "methods": ["vmc", *models], "conditions": conditions,
                "fixture_axes": ["push_angle", "push_height", "payload_mass"],
                "metrics": ["tracking_rmse_after_contact", "speed/acceleration/jerk",
                            "peak_contact_force", "peak_motor_torque", "penetration"],
                "models_frozen": True, "office_used_for_selection": False}
    dump(args.output / "protocol.json", protocol)
    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run, job, args.output, reference, panel, vmc_config) for job in jobs]
        for future in as_completed(futures):
            rows.append(future.result()); dump(args.output / "results.json", rows)
            dump(args.output / "status.json", {"phase": "evaluating", "completed": len(rows),
                                                "total": len(jobs), "summary": aggregate(rows)})
            print(json.dumps(rows[-1]), flush=True)
    summary = aggregate(rows)
    dump(args.output / "summary.json", summary)
    dump(args.output / "status.json", {"phase": "complete", "completed": len(rows),
                                        "total": len(jobs), "summary": summary})
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
