"""Offline ESN state/feature coverage audit.

This tool only replays saved observations.  It does not create MuJoCo, modify
checkpoints, or select a policy.  Train, held-out, and student traces are
reported separately so the held-out set cannot silently become a tuning set.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_model(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k].copy() for k in z.files}


def encode(model: dict[str, np.ndarray], observation: np.ndarray) -> dict[str, np.ndarray]:
    obs = np.asarray(observation, dtype=np.float64)
    mean = np.asarray(model["mean"], dtype=np.float64)
    std = np.asarray(model["std"], dtype=np.float64)
    mask = np.asarray(model["input_mask"], dtype=np.float64)
    win = np.asarray(model["win"], dtype=np.float64)
    recurrent = np.asarray(model["w"], dtype=np.float64)
    leak = np.asarray(model["leak"], dtype=np.float64)
    raw_z = (obs - mean) / std
    x = np.clip(raw_z, -12.0, 12.0) * mask
    state = np.zeros(recurrent.shape[0], dtype=np.float64)
    states = []
    for row in x:
        state += leak * (np.tanh(win @ np.r_[1.0, row] + recurrent @ state) - state)
        states.append(state.copy())
    states = np.asarray(states)
    features = np.c_[x, states]
    fmean = np.asarray(model["fmean"], dtype=np.float64)
    fstd = np.asarray(model["fstd"], dtype=np.float64)
    feature_z = (features - fmean) / fstd
    return {"raw_z": raw_z, "x": x, "state": states, "features": features, "feature_z": feature_z}


def quantiles(a: np.ndarray) -> dict[str, float]:
    a = np.asarray(a, dtype=np.float64).reshape(-1)
    finite = a[np.isfinite(a)]
    if not len(finite):
        return {"mean": None, "std": None, "rms": None, "p95_abs": None, "max_abs": None}
    return {
        "mean": float(np.mean(finite)),
        "std": float(np.std(finite)),
        "rms": float(np.sqrt(np.mean(finite * finite))),
        "p95_abs": float(np.quantile(np.abs(finite), 0.95)),
        "max_abs": float(np.max(np.abs(finite))),
    }


def summarize(encoded: dict[str, np.ndarray], stage: np.ndarray) -> dict:
    stage = np.asarray(stage, dtype=np.int64)
    out = {
        "samples": int(len(stage)),
        "stages": {str(int(s)): int(np.sum(stage == s)) for s in np.unique(stage)},
        "raw_input_z": quantiles(encoded["raw_z"]),
        "feature_z": quantiles(encoded["feature_z"]),
        "state_norm": quantiles(np.linalg.norm(encoded["state"], axis=1)),
        "input_clip_fraction": float(np.mean(np.abs(encoded["raw_z"]) > 12.0)),
        "feature_nonfinite": int(np.sum(~np.isfinite(encoded["feature_z"]))),
    }
    out["by_stage"] = {}
    for s in np.unique(stage):
        mask = stage == s
        out["by_stage"][str(int(s))] = {
            "samples": int(np.sum(mask)),
            "raw_input_z": quantiles(encoded["raw_z"][mask]),
            "feature_z": quantiles(encoded["feature_z"][mask]),
            "state_norm": quantiles(np.linalg.norm(encoded["state"][mask], axis=1)),
            "input_clip_fraction": float(np.mean(np.abs(encoded["raw_z"][mask]) > 12.0)),
        }
    return out


def load_trace(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with np.load(path, allow_pickle=False) as z:
        return z["observation"].astype(np.float64), z["stage"].astype(np.int64), z["action"].astype(np.float64)


def action_stats(action: np.ndarray) -> dict:
    delta = np.diff(action, axis=0)
    return {"range": quantiles(action), "delta": quantiles(delta), "delta_rms_by_channel": [float(np.sqrt(np.mean(d * d))) for d in delta.T]}


def timing_stats(time: np.ndarray, stage: np.ndarray, action: np.ndarray) -> dict:
    time = np.asarray(time, dtype=np.float64)
    stage = np.asarray(stage, dtype=np.int64)
    changes = np.flatnonzero(stage[1:] != stage[:-1]) + 1
    transitions = [{"time_s": float(time[i]), "from": int(stage[i - 1]), "to": int(stage[i])} for i in changes]
    by_stage = {}
    for s in np.unique(stage):
        mask = stage == s
        by_stage[str(int(s))] = {"samples": int(np.sum(mask)), "action": action_stats(action[mask])}
    return {"first_time_s": float(time[0]), "last_time_s": float(time[-1]), "transitions": transitions, "by_stage": by_stage}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--train", type=Path, nargs="+", required=True)
    p.add_argument("--heldout", type=Path, nargs="+", required=True)
    p.add_argument("--student", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)
    model = load_model(args.checkpoint)
    groups = {"train": args.train, "heldout": args.heldout, "student": args.student}
    report: dict = {
        "method": "offline_esn_state_feature_coverage_audit",
        "checkpoint": str(args.checkpoint.resolve()),
        "checkpoint_sha256": sha(args.checkpoint),
        "groups": {},
        "limitations": [
            "observation replay only; no MuJoCo or new physical measurement",
            "heldout statistics are descriptive and were not used for model selection",
            "student traces may share a deterministic fixed scene and are not independent geometries",
        ],
    }
    for group, paths in groups.items():
        items = []
        for path in paths:
            with np.load(path, allow_pickle=False) as z:
                time = z["time"].astype(np.float64)
            obs, stage, action = load_trace(path)
            encoded = encode(model, obs)
            items.append({
                "path": str(path.resolve()),
                "sha256": sha(path),
                "stage_summary": summarize(encoded, stage),
                "action_summary": action_stats(action),
                "timing": timing_stats(time, stage, action),
            })
        report["groups"][group] = items
    # Aggregate distributions without mixing group labels in the main report.
    for group, paths in groups.items():
        raw, feat, states, stages, actions, times = [], [], [], [], [], []
        for path in paths:
            with np.load(path, allow_pickle=False) as z:
                time = z["time"].astype(np.float64)
            obs, stage, action = load_trace(path)
            enc = encode(model, obs)
            raw.append(enc["raw_z"]); feat.append(enc["feature_z"]); states.append(enc["state"])
            stages.append(stage); actions.append(action); times.append(time)
        enc = {"raw_z": np.concatenate(raw), "feature_z": np.concatenate(feat), "state": np.concatenate(states)}
        report["groups"][group + "_aggregate"] = {
            "stage_summary": summarize(enc, np.concatenate(stages)),
            "action_summary": action_stats(np.concatenate(actions)),
            "timing": timing_stats(np.concatenate(times), np.concatenate(stages), np.concatenate(actions)),
            "trace_count": len(paths),
        }
    (args.output / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = ["# ESN state and feature coverage audit", "", "Offline replay only; no MuJoCo was created.", ""]
    lines += [f"- checkpoint SHA256: `{report['checkpoint_sha256']}`", "- held-out statistics are descriptive only; no model selection used", ""]
    for group in ("train_aggregate", "heldout_aggregate", "student_aggregate"):
        s = report["groups"][group]["stage_summary"]
        lines += [f"## {group}", "", f"- traces: `{report['groups'][group]['trace_count']}`; samples: `{s['samples']}`",
                  f"- raw input z RMS / p95 / max: `{s['raw_input_z']['rms']:.4f}` / `{s['raw_input_z']['p95_abs']:.4f}` / `{s['raw_input_z']['max_abs']:.4f}`",
                  f"- feature z RMS / p95 / max: `{s['feature_z']['rms']:.4f}` / `{s['feature_z']['p95_abs']:.4f}` / `{s['feature_z']['max_abs']:.4f}`",
                  f"- reservoir state norm RMS / p95 / max: `{s['state_norm']['rms']:.4f}` / `{s['state_norm']['p95_abs']:.4f}` / `{s['state_norm']['max_abs']:.4f}`",
                  f"- input clipping fraction: `{s['input_clip_fraction']:.6f}`", ""]
    lines += ["## Interpretation", "", "The student group is compared against the training-side feature range as a diagnostic only. A large tail or clipping rate indicates a closed-loop coverage gap and does not by itself prove causality. Stage-stratified timing and action delta summaries are retained in `audit.json`; no checkpoint or filter was changed.", ""]
    (args.output / "REPORT.md").write_text("\n".join(lines))
    print(json.dumps({"output": str(args.output), "checkpoint_sha256": report["checkpoint_sha256"], "groups": list(report["groups"])}, indent=2))


if __name__ == "__main__":
    main()
