#!/usr/bin/env python3
"""Long-running, resumable ESN search for inclined-board MuJoCo contacts.

This is an overnight development search, not a license to change the
observation contract.  Every candidate is trained from the same successful
teacher archives and is evaluated against a VMC constructed with the same
residual budget.  Contact/board fields are only used by the evaluator after a
rollout has completed.  The script writes a manifest after every candidate so
that a killed job can be resumed safely.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bootstrap_direct_esn_multifixture import _load_episode  # noqa: E402
from direct_esn_compliance import DirectESNConfig, DirectESNController  # noqa: E402
from evaluate_inclined_lift_four_method import fixture, make_vmc, run_one  # noqa: E402
from vmc_compliance_baseline import load_controller  # noqa: E402


TRACE_PATHS = (
    "/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_angle_train_20260821/inclined_tilt35_yaw0_00.npz",
    "/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_angle_train_20260821/inclined_tilt35_yaw0_01.npz",
    "/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_angle_train_20260821/inclined_tilt35_yaw30_00.npz",
    "/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_angle_train_20260821/inclined_tilt35_yaw30_01.npz",
    "/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_angle_train_20260821/inclined_tilt40_yaw0_00.npz",
    "/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_angle_train_20260821/inclined_tilt40_yaw0_01.npz",
    "/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_angle_train_20260821/inclined_tilt40_yaw60_01.npz",
    "/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_angle_train_yaw60_pos_20260821/inclined_tilt40_yaw60_00.npz",
    "/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_angle_train_yaw60_pos_20260821/inclined_tilt40_yaw60_01.npz",
)
NEUTRAL_PATH = "/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_angle_train_20260821/neutral_no_board.npz"


def jsonable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)


def config_id(config: dict) -> str:
    raw = json.dumps(config, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def scalar_summary(rows: list[dict]) -> dict:
    if not rows:
        return {"count": 0}
    return {
        "count": len(rows),
        "success_count": int(sum(bool(row["task_success"]) for row in rows)),
        "success_rate": float(np.mean([bool(row["task_success"]) for row in rows])),
        "mean_peak_force_n": float(np.mean([row["board_peak_force_n"] for row in rows])),
        "mean_impulse_ns": float(np.mean([row["board_contact_impulse_ns"] for row in rows])),
        "mean_postcontact_error_mm": float(np.mean([row["peak_postcontact_error_mm"] for row in rows])),
        "mean_peak_torque_nm": float(np.mean([row["peak_torque_nm"] for row in rows])),
        "geometry_valid_rate": float(np.mean([row["geometry_valid_postgrasp"] for row in rows])),
    }


def relative_loss(summary: dict, vmc: dict) -> float:
    keys = ("mean_peak_force_n", "mean_impulse_ns", "mean_postcontact_error_mm")
    return float(np.mean([summary[key] / max(vmc[key], 1.0e-9) for key in keys]))


def score(summary: dict, vmc: dict) -> tuple[float, float, float]:
    # Success is primary.  Physical loss is the first tie-break; peak torque
    # is a final tie-break so a low-force but non-retaining policy cannot win.
    return (
        float(summary.get("success_rate", 0.0)),
        -relative_loss(summary, vmc),
        -float(summary.get("mean_peak_torque_nm", math.inf)),
    )


def load_training_data(target_budget: float, *, rod_repeat: int = 2,
                       neutral_repeat: int = 2):
    data = []
    for path_string in (*TRACE_PATHS, NEUTRAL_PATH):
        path = Path(path_string)
        observations, actions, trace_budget = _load_episode(path, 1, "bounded_action")
        if trace_budget is None:
            raise ValueError(f"{path}: missing residual budget provenance")
        actions = np.clip(actions * trace_budget / target_budget, -1.0, 1.0)
        repeat = neutral_repeat if path == Path(NEUTRAL_PATH) else rod_repeat
        data.append((path, observations, actions, repeat))
    return data


def fit_candidate(spec: dict, out_path: Path, train_data: list) -> tuple[DirectESNController, dict]:
    scales = spec.get("multiscale_time_constants_s")
    config = DirectESNConfig(
        reservoir_size=int(spec["reservoir_size"]),
        spectral_radius=float(spec["spectral_radius"]),
        input_scale=float(spec["input_scale"]),
        time_constant_s=float(spec.get("time_constant_s", 0.12)),
        multiscale_time_constants_s=None if scales is None else tuple(scales),
        fast_fraction=float(spec.get("fast_fraction", 0.50)),
        ridge_lambda=float(spec["ridge_lambda"]),
        seed=int(spec["seed"]),
        error_aligned_yield=bool(spec.get("error_aligned_yield", False)),
        rejoin_fade_enabled=bool(spec.get("rejoin_fade_enabled", False)),
        yield_smoothing_alpha=float(spec.get("yield_smoothing_alpha", 1.0)),
        mirror_gate_enabled=bool(spec.get("mirror_gate_enabled", False)),
        mirror_gate_channels="y",
    )
    model = DirectESNController(config)
    features_all, targets_all, smooth_all, smooth_targets_all = [], [], [], []
    lead = int(spec.get("target_lead_steps", 0))
    smooth_weight = float(spec.get("smoothness_weight", 0.0))
    derivative_match = bool(spec.get("derivative_match", False))
    derivative_alpha = float(spec.get("derivative_lowpass", 1.0))
    for path, observations, actions, repeat in train_data:
        features = model.features(observations, washout_steps=3)
        labels = actions[3:]
        if lead:
            if lead >= len(labels):
                raise ValueError(f"{path}: target lead exceeds episode")
            features, labels = features[:-lead], labels[lead:]
        features_all.extend([features] * repeat)
        targets_all.extend([labels] * repeat)
        if smooth_weight > 0.0:
            smooth_all.extend([np.diff(features, axis=0)] * repeat)
            diff = np.diff(labels, axis=0) if derivative_match else np.zeros_like(np.diff(labels, axis=0))
            if derivative_match and derivative_alpha < 1.0:
                filtered = np.empty_like(diff)
                state = np.zeros(diff.shape[1])
                for index, value in enumerate(diff):
                    state = derivative_alpha * value + (1.0 - derivative_alpha) * state
                    filtered[index] = state
                diff = filtered
            smooth_targets_all.extend([diff] * repeat)
    design = np.concatenate(features_all, axis=0)
    targets = np.concatenate(targets_all, axis=0)
    smooth = np.concatenate(smooth_all, axis=0) if smooth_all else None
    smooth_targets = np.concatenate(smooth_targets_all, axis=0) if smooth_targets_all else None
    channel_scales = None
    if bool(spec.get("relieve_direction_channels", False)):
        channel_scales = np.array([1.0, 1.0, 0.1, 1.0, 1.0, 1.0, 0.1])
    mse = model.fit_readout(
        design, targets, smoothness_features=smooth,
        smoothness_weight=smooth_weight, smoothness_targets=smooth_targets,
        smoothness_channel_scales=channel_scales,
    )
    model.save_npz(out_path)
    return model, {"readout_training_mse": mse, "training_samples": len(design), "reservoir": asdict(config)}


class Ensemble:
    def __init__(self, members):
        self.members = list(members)

    def reset(self):
        for member in self.members:
            member.reset()

    def act(self, *args, **kwargs):
        actions = [np.asarray(member.act(*args, **kwargs).bounded_filter_action, dtype=float)
                   for member in self.members]
        return SimpleNamespace(bounded_filter_action=np.mean(actions, axis=0))


def evaluate_controller(menagerie: Path, controller, label: str, budget: float,
                        tilts: list[float], yaws: list[float], seeds: list[int],
                        *, keep_rows: bool = False) -> tuple[dict, list[dict]]:
    rows = []
    for tilt in tilts:
        for yaw in yaws:
            for seed in seeds:
                controller.reset()
                offset = float(np.random.default_rng(
                    seed * 1009 + int(round(tilt * 10)) + int(round(yaw * 100))
                ).uniform(-0.008, 0.008))
                row = run_one(
                    menagerie, label, controller, seed=seed, tilt=tilt,
                    budget=budget, board_y_offset_m=offset, board_yaw_deg=yaw,
                )
                if not keep_rows:
                    row.pop("rows", None)
                rows.append(row)
    return scalar_summary(rows), rows


def random_specs(count: int, seed: int) -> list[dict]:
    rng = np.random.default_rng(seed)
    sizes = [160, 240, 320, 480]
    single_tc = [0.04, 0.08, 0.12, 0.16]
    multiscale = [(0.04, 0.12), (0.04, 0.16), (0.06, 0.16), (0.08, 0.16)]
    budgets = [0.015, 0.020, 0.025, 0.030]
    specs = []
    for index in range(count):
        use_multi = bool(rng.random() < 0.58)
        scales = list(multiscale[int(rng.integers(len(multiscale)))]) if use_multi else None
        spec = {
            "reservoir_size": int(rng.choice(sizes)),
            "spectral_radius": float(rng.choice([0.82, 0.88, 0.90, 0.94, 0.98])),
            "input_scale": float(rng.choice([0.25, 0.35, 0.45, 0.60, 0.80])),
            "ridge_lambda": float(rng.choice([1e-5, 3e-5, 1e-4, 3e-4, 1e-3])),
            "seed": int(rng.choice([20263050, 20263051, 20263052, 20263053, 20263054, 20263055])),
            "target_budget": float(rng.choice(budgets)),
            "yield_smoothing_alpha": float(rng.choice([1.0, 0.85, 0.70, 0.50])),
            "rejoin_fade_enabled": bool(rng.random() < 0.18),
            "mirror_gate_enabled": bool(rng.random() < 0.15),
            "error_aligned_yield": bool(rng.random() < 0.08),
            "target_lead_steps": int(rng.choice([0, 0, 0, 1, 2])),
            "smoothness_weight": float(rng.choice([0.0, 0.0, 0.003, 0.01, 0.02])),
            "derivative_match": bool(rng.random() < 0.38),
            "derivative_lowpass": float(rng.choice([0.5, 0.75, 1.0])),
            "relieve_direction_channels": bool(rng.random() < 0.45),
        }
        if scales is None:
            spec["time_constant_s"] = float(rng.choice(single_tc))
            spec["multiscale_time_constants_s"] = None
        else:
            spec["time_constant_s"] = 0.12
            spec["multiscale_time_constants_s"] = scales
        # Direction-relief is meaningful only when a smoothness penalty exists.
        if spec["smoothness_weight"] == 0.0:
            spec["derivative_match"] = False
            spec["relieve_direction_channels"] = False
        specs.append(spec)
    return specs


def dedupe_specs(specs: list[dict]) -> list[dict]:
    result, seen = [], set()
    for spec in specs:
        ident = config_id(spec)
        if ident not in seen:
            seen.add(ident)
            spec = dict(spec)
            spec["id"] = ident
            result.append(spec)
    return result


def dump_state(path: Path, state: dict):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(state, indent=2, default=jsonable) + "\n")
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--hours", type=float, default=14.2)
    parser.add_argument("--stage1-count", type=int, default=500)
    parser.add_argument("--stage2-count", type=int, default=128)
    parser.add_argument("--stage3-count", type=int, default=32)
    parser.add_argument("--final-count", type=int, default=16)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--seed", type=int, default=20260821)
    args = parser.parse_args()
    if args.hours <= 0 or min(args.stage1_count, args.stage2_count, args.stage3_count, args.final_count) < 1:
        raise SystemExit("hours and stage counts must be positive")
    args.out.mkdir(parents=True, exist_ok=True)
    state_path = args.out / "overnight_manifest.json"
    deadline = time.time() + args.hours * 3600.0

    if args.resume and state_path.exists():
        state = json.loads(state_path.read_text())
        # Allow a later invocation to extend an existing run without touching
        # completed records.  New specs use a separate deterministic RNG seed.
        existing = list(state.get("stage1_specs", []))
        if args.stage1_count > len(existing):
            seen = {item["id"] for item in existing}
            extras = dedupe_specs(random_specs(args.stage1_count * 2, args.seed + 1000003))
            for item in extras:
                if item["id"] not in seen:
                    existing.append(item)
                    seen.add(item["id"])
                    if len(existing) >= args.stage1_count:
                        break
            state["stage1_specs"] = existing
            dump_state(state_path, state)
        print(f"resuming {state_path}; completed={len(state.get('completed', {}))}", flush=True)
    else:
        specs = dedupe_specs(random_specs(args.stage1_count, args.seed))
        state = {
            "schema_version": 1,
            "protocol": "resumable_overnight_esn_search",
            "status": "running",
            "started_unix": time.time(),
            "hours_budget": args.hours,
            "observation_contract": "q,qdot,nominal_twist,pose_error,wbc_twist_error only; no board/contact truth",
            "teacher_traces": list(TRACE_PATHS) + [NEUTRAL_PATH],
            "selection_rule": "success first, then equal-weight peak-force/impulse/post-contact-error ratio to same-budget VMC",
            "stage1_specs": specs,
            "completed": {},
            "stage2": [],
            "stage3": [],
            "final": [],
        }
        dump_state(state_path, state)
    menagerie = args.menagerie

    # Cache training archives by target budget; action normalization is the
    # only budget-dependent part of fitting.
    train_cache = {}
    vmc_cache = {}
    stage1_tilts, stage1_yaws, stage1_seeds = [37.5], [60, 75, 90, 105, 120], [20264001, 20264002]
    stage2_tilts, stage2_yaws, stage2_seeds = [35, 40], [60, 75, 90, 105, 120], [20264011, 20264012, 20264013, 20264014]
    stage3_tilts, stage3_yaws, stage3_seeds = [35, 37.5, 40, 42.5], [45, 60, 75, 90, 105, 120, 135], [20264021, 20264022, 20264023, 20264024, 20264025, 20264026]
    model_dir = args.out / "models"
    model_dir.mkdir(exist_ok=True)

    def get_train_data(budget):
        key = f"{budget:.6f}"
        if key not in train_cache:
            train_cache[key] = load_training_data(budget)
        return train_cache[key]

    def get_vmc(budget, tilts, yaws, seeds, name):
        key = (float(budget), tuple(tilts), tuple(yaws), tuple(seeds))
        if key not in vmc_cache:
            vmc_cache[key], _ = evaluate_controller(
                menagerie, make_vmc(budget), name, budget, tilts, yaws, seeds,
            )
        return vmc_cache[key]

    started = time.time()
    # Stage 1: broad cheap screen.  Checkpoint after every model.
    for index, spec in enumerate(state["stage1_specs"]):
        if time.time() >= deadline:
            break
        ident = spec["id"]
        if ident in state["completed"]:
            continue
        budget = float(spec["target_budget"])
        model_path = model_dir / f"{ident}.npz"
        model = None
        try:
            model, fit_meta = fit_candidate(spec, model_path, get_train_data(budget))
            vmc = get_vmc(budget, stage1_tilts, stage1_yaws, stage1_seeds, f"VMC_stage1_b{budget:g}")
            summary, _ = evaluate_controller(menagerie, model, ident, budget, stage1_tilts, stage1_yaws, stage1_seeds)
            state["completed"][ident] = {
                "spec": spec, "model": str(model_path), "fit": fit_meta,
                "summary": summary, "vmc": vmc,
                "relative_loss_vs_vmc": relative_loss(summary, vmc),
                "stage": 1, "index": index, "finished_unix": time.time(),
            }
            print(json.dumps({"stage": 1, "index": index, "id": ident, "summary": summary,
                              "relative_loss": state["completed"][ident]["relative_loss_vs_vmc"]}), flush=True)
        except Exception as exc:  # preserve failures for later auditing
            state["completed"][ident] = {"spec": spec, "stage": 1, "index": index,
                                          "status": "failed", "error": repr(exc), "finished_unix": time.time()}
            print(json.dumps({"stage": 1, "index": index, "id": ident, "error": repr(exc)}), flush=True)
        dump_state(state_path, state)
        if model is not None:
            del model
        gc.collect()

    successful = [item for item in state["completed"].values() if item.get("status", "ok") != "failed"]
    successful.sort(key=lambda item: score(item["summary"], item["vmc"]), reverse=True)
    # Keep at least four candidates per budget, then fill by global score.
    selected2, used = [], set()
    for budget in (0.015, 0.020, 0.025, 0.030):
        for item in successful:
            if abs(float(item["spec"]["target_budget"]) - budget) < 1e-9:
                selected2.append(item); used.add(item["spec"]["id"])
                if len([x for x in selected2 if abs(float(x["spec"]["target_budget"]) - budget) < 1e-9]) >= 4:
                    break
    for item in successful:
        if item["spec"]["id"] not in used and len(selected2) < args.stage2_count:
            selected2.append(item); used.add(item["spec"]["id"])
    # Stage 2: stronger cross-angle screen.
    for item in selected2:
        if time.time() >= deadline:
            break
        ident = item["spec"]["id"]
        if any(row.get("id") == ident for row in state["stage2"]):
            continue
        budget = float(item["spec"]["target_budget"])
        try:
            model = load_controller(item["model"])
            vmc = get_vmc(budget, stage2_tilts, stage2_yaws, stage2_seeds, f"VMC_stage2_b{budget:g}")
            summary, _ = evaluate_controller(menagerie, model, ident, budget, stage2_tilts, stage2_yaws, stage2_seeds)
            row = {"id": ident, "model": item["model"], "spec": item["spec"], "summary": summary,
                   "vmc": vmc, "relative_loss_vs_vmc": relative_loss(summary, vmc), "stage": 2}
            state["stage2"].append(row)
            print(json.dumps({"stage": 2, "id": ident, "summary": summary,
                              "relative_loss": row["relative_loss_vs_vmc"]}), flush=True)
        except Exception as exc:
            state["stage2"].append({"id": ident, "stage": 2, "status": "failed", "error": repr(exc)})
            print(json.dumps({"stage": 2, "id": ident, "error": repr(exc)}), flush=True)
        dump_state(state_path, state)
        gc.collect()

    stage2_ok = [item for item in state["stage2"] if item.get("status", "ok") != "failed"]
    stage2_ok.sort(key=lambda item: score(item["summary"], item["vmc"]), reverse=True)
    selected3 = stage2_ok[:args.stage3_count]

    # Stage 3: wide stress grid, then evaluate simple ensembles of the best
    # independent reservoirs.  This stage is deliberately geometry-diverse.
    for item in selected3:
        if time.time() >= deadline:
            break
        ident = item["id"]
        if any(row.get("id") == ident for row in state["stage3"]):
            continue
        budget = float(item["spec"]["target_budget"])
        try:
            model = load_controller(item["model"])
            vmc = get_vmc(budget, stage3_tilts, stage3_yaws, stage3_seeds, f"VMC_stage3_b{budget:g}")
            summary, _ = evaluate_controller(menagerie, model, ident, budget, stage3_tilts, stage3_yaws, stage3_seeds)
            row = {"id": ident, "model": item["model"], "spec": item["spec"], "summary": summary,
                   "vmc": vmc, "relative_loss_vs_vmc": relative_loss(summary, vmc), "stage": 3}
            state["stage3"].append(row)
            print(json.dumps({"stage": 3, "id": ident, "summary": summary,
                              "relative_loss": row["relative_loss_vs_vmc"]}), flush=True)
        except Exception as exc:
            state["stage3"].append({"id": ident, "stage": 3, "status": "failed", "error": repr(exc)})
            print(json.dumps({"stage": 3, "id": ident, "error": repr(exc)}), flush=True)
        dump_state(state_path, state)
        gc.collect()

    stage3_ok = [item for item in state["stage3"] if item.get("status", "ok") != "failed"]
    stage3_ok.sort(key=lambda item: score(item["summary"], item["vmc"]), reverse=True)

    # Final stage: robust test for the best eight candidates and two-member
    # ensembles.  No model is selected using the final test itself; rows are
    # retained for later human inspection.
    final_candidates = stage3_ok[:args.final_count]
    for item in final_candidates:
        if time.time() >= deadline:
            break
        ident = f"final_{item['id']}"
        if any(row.get("id") == ident for row in state["final"]):
            continue
        budget = float(item["spec"]["target_budget"])
        try:
            model = load_controller(item["model"])
            vmc = get_vmc(budget, [35, 40], [90, 120], [20264031, 20264032, 20264033, 20264034, 20264035], f"VMC_final_b{budget:g}")
            summary, _ = evaluate_controller(menagerie, model, ident, budget, [35, 40], [90, 120], [20264031, 20264032, 20264033, 20264034, 20264035])
            state["final"].append({"id": ident, "model": item["model"], "spec": item["spec"],
                                   "summary": summary, "vmc": vmc,
                                   "relative_loss_vs_vmc": relative_loss(summary, vmc), "stage": "final"})
            print(json.dumps({"stage": "final", "id": ident, "summary": summary}), flush=True)
        except Exception as exc:
            state["final"].append({"id": ident, "stage": "final", "status": "failed", "error": repr(exc)})
            print(json.dumps({"stage": "final", "id": ident, "error": repr(exc)}), flush=True)
        dump_state(state_path, state)
        gc.collect()

    state["status"] = "completed" if time.time() < deadline else "time_budget_reached"
    state["finished_unix"] = time.time()
    state["elapsed_hours"] = (state["finished_unix"] - started) / 3600.0
    dump_state(state_path, state)
    print(json.dumps({"status": state["status"], "elapsed_hours": state["elapsed_hours"],
                      "completed": len(state["completed"]), "stage2": len(state["stage2"]),
                      "stage3": len(state["stage3"]), "final": len(state["final"])}), flush=True)


if __name__ == "__main__":
    main()
