#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from residual_compliance_fetch.utils import ensure_dir


ARM_DOF = 7
INF = float("inf")


def _as_vec(record: dict[str, Any], key: str, dim: int = ARM_DOF) -> np.ndarray:
    arr = np.asarray(record.get(key, [0.0] * dim), dtype=np.float32)
    if arr.shape != (dim,):
        raise ValueError(f"Expected {key} to have shape ({dim},), got {arr.shape}")
    return arr


def _resolve_record_path(raw_path: str, summary_path: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    candidates = [
        PROJECT_ROOT / path,
        summary_path.parent / path,
        Path.cwd() / path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _collect_record_paths(
    summary_path: Path,
    mode: str,
    *,
    exclude_failures: bool = False,
    min_score_delta: float | None = None,
    max_penetration_delta: float | None = None,
    max_contact_steps_delta: float | None = None,
) -> tuple[list[tuple[int, Path]], dict[str, Any]]:
    with summary_path.open("r", encoding="utf-8") as f:
        summary = json.load(f)

    paths: list[tuple[int, Path]] = []
    excluded: dict[str, int] = {}
    score_deltas: list[float] = []
    penetration_deltas: list[float] = []
    contact_step_deltas: list[float] = []

    def reject(reason: str) -> None:
        excluded[reason] = excluded.get(reason, 0) + 1

    for episode in summary.get("episodes", []):
        ep_idx = int(episode.get("episode", len(paths)))
        rollouts = episode.get("rollouts", {})
        rollout = rollouts.get(mode)
        if not rollout:
            reject("missing_rollout")
            continue
        raw_records = rollout.get("records")
        if not raw_records:
            reject("missing_records")
            continue

        if exclude_failures and ((not bool(rollout.get("success", False))) or bool(rollout.get("collision", False))):
            reject("teacher_failure_or_collision")
            continue

        baseline = rollouts.get("baseline")
        if baseline is not None:
            score_delta = float(rollout.get("compliance_score", 0.0)) - float(
                baseline.get("compliance_score", 0.0)
            )
            penetration_delta = float(rollout.get("max_penetration", 0.0)) - float(
                baseline.get("max_penetration", 0.0)
            )
            contact_step_delta = float(rollout.get("contact_steps", 0.0)) - float(
                baseline.get("contact_steps", 0.0)
            )
            score_deltas.append(score_delta)
            penetration_deltas.append(penetration_delta)
            contact_step_deltas.append(contact_step_delta)

            if min_score_delta is not None and score_delta < float(min_score_delta):
                reject("score_delta_too_low")
                continue
            if (
                max_penetration_delta is not None
                and penetration_delta > float(max_penetration_delta)
            ):
                reject("penetration_delta_too_high")
                continue
            if (
                max_contact_steps_delta is not None
                and contact_step_delta > float(max_contact_steps_delta)
            ):
                reject("contact_steps_delta_too_high")
                continue

        paths.append((ep_idx, _resolve_record_path(str(raw_records), summary_path)))

    stats = {
        "candidate_episodes": len(summary.get("episodes", [])),
        "kept_episodes": len(paths),
        "excluded_episodes": int(sum(excluded.values())),
        "excluded_reasons": excluded,
        "exclude_failures": bool(exclude_failures),
        "min_score_delta": min_score_delta,
        "max_penetration_delta": max_penetration_delta,
        "max_contact_steps_delta": max_contact_steps_delta,
    }
    if score_deltas:
        stats.update(
            {
                "mean_score_delta_vs_baseline": float(np.mean(score_deltas)),
                "mean_penetration_delta_vs_baseline": float(np.mean(penetration_deltas)),
                "mean_contact_steps_delta_vs_baseline": float(np.mean(contact_step_deltas)),
            }
        )
    return paths, stats


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _build_link_vocab(record_paths: list[tuple[int, Path]]) -> list[str]:
    names = {"none"}
    for _, path in record_paths:
        data = _load_json(path)
        for record in data.get("records", []):
            link = record.get("active_link")
            names.add("none" if link is None else str(link))
    return ["none"] + sorted(name for name in names if name != "none")


def _feature_names(link_vocab: list[str]) -> list[str]:
    names: list[str] = []
    names.extend(f"q_arm_{i}" for i in range(ARM_DOF))
    names.extend(f"q_target_{i}" for i in range(ARM_DOF))
    names.extend(f"q_error_{i}" for i in range(ARM_DOF))
    names.extend(f"qdot_nom_{i}" for i in range(ARM_DOF))
    names.extend(f"prev_qdot_residual_{i}" for i in range(ARM_DOF))
    names.extend(
        [
            "contact_depth",
            "force_proxy_level",
            "qvel_tracking_error",
            "contact_level",
            "contact_flag",
        ]
    )
    names.extend(f"active_link_{name}" for name in link_vocab)
    return names


def _make_feature(
    record: dict[str, Any],
    prev_residual: np.ndarray,
    link_to_index: dict[str, int],
    prev_qvel_tracking_error: float,
) -> np.ndarray:
    q_arm = _as_vec(record, "q_arm")
    q_target = _as_vec(record, "q_target")
    qdot_nom = _as_vec(record, "qdot_nom")

    contact_depth = float(record.get("contact_depth", 0.0))
    force_proxy_level = float(record.get("force_proxy_level", 0.0))
    qvel_tracking_error = float(prev_qvel_tracking_error)
    contact_level = float(record.get("risk", 0.0))
    contact_flag = float(
        contact_depth > 1e-8 or force_proxy_level > 1e-8 or contact_level > 1e-8
    )

    link_name = record.get("active_link")
    link_name = "none" if link_name is None else str(link_name)
    one_hot = np.zeros(len(link_to_index), dtype=np.float32)
    one_hot[link_to_index.get(link_name, link_to_index["none"])] = 1.0

    return np.concatenate(
        [
            q_arm,
            q_target,
            q_target - q_arm,
            qdot_nom,
            prev_residual.astype(np.float32),
            np.asarray(
                [
                    contact_depth,
                    force_proxy_level,
                    qvel_tracking_error,
                    contact_level,
                    contact_flag,
                ],
                dtype=np.float32,
            ),
            one_hot,
        ]
    ).astype(np.float32)


def _sample_weight(record: dict[str, Any], action: np.ndarray) -> float:
    contact_depth = float(record.get("contact_depth", 0.0))
    force_proxy_level = float(record.get("force_proxy_level", 0.0))
    contact_level = float(record.get("risk", 0.0))
    contact_signal = contact_depth > 1e-8 or force_proxy_level > 1e-8 or contact_level > 1e-8
    action_signal = float(np.linalg.norm(action)) > 1e-2
    return 1.0 + (4.0 if contact_signal else 0.0) + (2.0 if action_signal else 0.0)


def build_dataset(
    summary_path: Path,
    mode: str,
    output_path: Path,
    *,
    exclude_failures: bool = False,
    min_score_delta: float | None = None,
    max_penetration_delta: float | None = None,
    max_contact_steps_delta: float | None = None,
) -> dict[str, Any]:
    record_paths, filter_stats = _collect_record_paths(
        summary_path,
        mode,
        exclude_failures=exclude_failures,
        min_score_delta=min_score_delta,
        max_penetration_delta=max_penetration_delta,
        max_contact_steps_delta=max_contact_steps_delta,
    )
    if not record_paths:
        raise RuntimeError(f"No record files found for mode={mode!r} in {summary_path}")

    for _, path in record_paths:
        if not path.exists():
            raise FileNotFoundError(f"Record file not found: {path}")

    link_vocab = _build_link_vocab(record_paths)
    link_to_index = {name: idx for idx, name in enumerate(link_vocab)}

    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    weights: list[float] = []
    episode_indices: list[int] = []
    step_indices: list[int] = []
    contact_steps = 0

    for episode_idx, path in record_paths:
        data = _load_json(path)
        prev_residual = np.zeros(ARM_DOF, dtype=np.float32)
        prev_qvel_tracking_error = 0.0
        for step_idx, record in enumerate(data.get("records", [])):
            action = _as_vec(record, "qdot_residual")
            observation = _make_feature(
                record,
                prev_residual,
                link_to_index,
                prev_qvel_tracking_error=prev_qvel_tracking_error,
            )
            observations.append(observation)
            actions.append(action)
            weights.append(_sample_weight(record, action))
            episode_indices.append(episode_idx)
            step_indices.append(step_idx)
            if observation[-len(link_vocab) - 1] > 0.0:
                contact_steps += 1
            prev_residual = action
            prev_qvel_tracking_error = float(record.get("qvel_tracking_error", 0.0))

    x = np.stack(observations).astype(np.float32)
    y = np.stack(actions).astype(np.float32)
    w = np.asarray(weights, dtype=np.float32)
    ep = np.asarray(episode_indices, dtype=np.int32)
    step = np.asarray(step_indices, dtype=np.int32)
    feature_names = np.asarray(_feature_names(link_vocab), dtype=object)

    ensure_dir(output_path.parent)
    np.savez_compressed(
        output_path,
        observations=x,
        actions=y,
        sample_weights=w,
        episode_indices=ep,
        step_indices=step,
        feature_names=feature_names,
        link_vocab=np.asarray(link_vocab, dtype=object),
    )

    action_norm = np.linalg.norm(y, axis=1)
    stats = {
        "summary_path": str(summary_path),
        "mode": mode,
        "output_path": str(output_path),
        "filter": filter_stats,
        "num_record_files": len(record_paths),
        "num_samples": int(x.shape[0]),
        "observation_dim": int(x.shape[1]),
        "action_dim": int(y.shape[1]),
        "contact_or_residual_weighted_samples": int(np.sum(w > 1.0)),
        "mean_sample_weight": float(np.mean(w)),
        "nonzero_action_ratio": float(np.mean(action_norm > 1e-2)),
        "mean_action_norm": float(np.mean(action_norm)),
        "max_action_norm": float(np.max(action_norm)),
        "link_vocab": link_vocab,
        "feature_names": feature_names.tolist(),
    }

    stats_path = output_path.with_suffix(".stats.json")
    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a contact-only behavior cloning dataset from rollout records."
    )
    parser.add_argument(
        "--summary",
        default="outputs/contact_heavy_strict_500/randomized_summary.json",
        help="Path to randomized_summary.json.",
    )
    parser.add_argument(
        "--mode",
        default="contact_compliance",
        choices=["baseline", "contact_compliance"],
        help="Rollout mode to imitate.",
    )
    parser.add_argument(
        "--output",
        default="data/contact_heavy_strict_500_bc.npz",
        help="Output npz dataset path.",
    )
    parser.add_argument(
        "--exclude-failures",
        action="store_true",
        help="Drop teacher episodes where the selected mode fails or collides.",
    )
    parser.add_argument(
        "--min-score-delta",
        type=float,
        default=None,
        help=(
            "Keep only episodes where selected_mode_score - baseline_score is at least this value. "
            "Use 0.0 to imitate only teacher rollouts that are no worse than baseline."
        ),
    )
    parser.add_argument(
        "--max-penetration-delta",
        type=float,
        default=None,
        help=(
            "Keep only episodes where selected_mode_max_penetration - baseline_max_penetration "
            "is no larger than this value."
        ),
    )
    parser.add_argument(
        "--max-contact-steps-delta",
        type=float,
        default=None,
        help=(
            "Keep only episodes where selected_mode_contact_steps - baseline_contact_steps "
            "is no larger than this value."
        ),
    )
    args = parser.parse_args()

    summary_path = Path(args.summary)
    if not summary_path.is_absolute():
        summary_path = PROJECT_ROOT / summary_path
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    stats = build_dataset(
        summary_path=summary_path,
        mode=str(args.mode),
        output_path=output_path,
        exclude_failures=bool(args.exclude_failures),
        min_score_delta=args.min_score_delta,
        max_penetration_delta=args.max_penetration_delta,
        max_contact_steps_delta=args.max_contact_steps_delta,
    )
    print(json.dumps(stats, indent=2))
    print(f"Saved dataset to {output_path}")
    print(f"Saved stats to {output_path.with_suffix('.stats.json')}")


if __name__ == "__main__":
    main()
