#!/usr/bin/env python3
"""Closed-loop DAgger for the Direct ESN compliant controller.

Each iteration first executes the *current student* in the fixed-WBC MuJoCo
task.  The rollout archive stores only deployable state as ESN input, while a
separate privileged section records contact diagnostics for offline labels.
The teacher action is generated after the rollout; it never enters the online
controller.  This corrects the distribution shift that appears when a small
student residual creates a state not present in the original teacher trace.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from direct_esn_compliance import (
    DirectESNConfig,
    DirectESNController,
    DirectESNObservation,
    build_privileged_teacher_trace,
)
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv


def _normal_from_fixture_side(side: str) -> np.ndarray:
    # This is privileged label-side geometry, not an ESN observation. The
    # current fixture family approaches from ±y; the resulting target yields
    # away from the approaching rod.
    if side == "negative_y":
        return np.array([0.0, -1.0, 0.0])
    if side == "positive_y":
        return np.array([0.0, 1.0, 0.0])
    raise ValueError(f"unsupported rod approach side {side!r}")


def collect_student_visited_archive(
    controller_path: Path,
    *,
    menagerie: Path,
    fixture_index: int,
    rod_enabled: bool,
    seed: int,
    output_path: Path,
    iteration: int,
) -> dict:
    """Run one student rollout and construct a privileged DAgger archive."""

    controller = DirectESNController.from_npz(controller_path)
    env = PandaWBCVelocityResidualEnv(
        menagerie=menagerie,
        fan_ye_model_npz=None,
        fan_ye_train_summary_json=None,
        observation_mode="direct_esn",
        rod_enabled=rod_enabled,
        seed=seed,
    )
    records: list[dict[str, np.ndarray | float]] = []
    try:
        env.reset(seed=seed, options={"fixture_index": fixture_index})
        controller.reset()
        terminated = False
        info: dict = {}
        normal = _normal_from_fixture_side(env.fixture.rod_approach_side)
        while not terminated:
            diagnostic = env.diagnostics()
            action = controller.act(
                diagnostic["joint_position"], diagnostic["joint_velocity"], diagnostic["nominal_twist"],
                pose_error=diagnostic["wbc_pose_error"], twist_error=diagnostic["wbc_twist_error"],
            )
            _, _, terminated, _, info = env.step(action.bounded_filter_action)
            records.append({
                "joint_position": diagnostic["joint_position"].copy(),
                "joint_velocity": diagnostic["joint_velocity"].copy(),
                "wbc_task_twist": diagnostic["nominal_twist"].copy(),
                "pose_error": diagnostic["wbc_pose_error"].copy(),
                "wbc_twist_error": diagnostic["wbc_twist_error"].copy(),
                "student_action": action.bounded_filter_action.copy(),
                # All fields below this line are offline teacher diagnostics.
                "contact_force": float(env.last_action_contact_force),
                "contact_normal": normal.copy(),
                "contact_duration_s": float(env.dagger_contact_duration_s),
                "signed_distance_m": -float(env.last_action_contact_penetration) if env.last_action_contact_seen else 0.02,
            })
    finally:
        env.close()
    if not records:
        raise RuntimeError("Direct ESN DAgger rollout produced no records")
    force = np.asarray([row["contact_force"] for row in records], dtype=float)
    normal = np.asarray([row["contact_normal"] for row in records], dtype=float)
    duration = np.asarray([row["contact_duration_s"] for row in records], dtype=float)
    distance = np.asarray([row["signed_distance_m"] for row in records], dtype=float)
    pose_error = np.asarray([row["pose_error"] for row in records], dtype=float)
    teacher_action = build_privileged_teacher_trace(force, normal, duration, distance, pose_error)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        joint_position=np.asarray([row["joint_position"] for row in records]),
        joint_velocity=np.asarray([row["joint_velocity"] for row in records]),
        wbc_task_twist=np.asarray([row["wbc_task_twist"] for row in records]),
        pose_error=pose_error,
        wbc_twist_error=np.asarray([row["wbc_twist_error"] for row in records]),
        teacher_action=teacher_action,
        student_action=np.asarray([row["student_action"] for row in records]),
        contact_force=force,
        contact_normal=normal,
        contact_duration_s=duration,
        signed_distance_m=distance,
        dagger_iteration=np.full(len(records), iteration, dtype=int),
        rod_enabled=np.full(len(records), rod_enabled, dtype=bool),
    )
    return {
        "archive": str(output_path),
        "samples": len(records),
        "fixture_index": fixture_index,
        "rod_enabled": rod_enabled,
        "teacher_nonzero_fraction": float(np.mean(np.linalg.norm(teacher_action, axis=1) > 1.0e-5)),
        "student_action_mean_norm": float(np.mean(np.linalg.norm(np.asarray([row["student_action"] for row in records]), axis=1))),
        "terminal": info,
    }


def _load_episode(path: Path, sample_stride: int) -> tuple[list[DirectESNObservation], np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        required = {"joint_position", "joint_velocity", "wbc_task_twist", "pose_error", "wbc_twist_error", "teacher_action"}
        missing = required - set(archive.files)
        if missing:
            raise ValueError(f"{path}: missing fields {sorted(missing)}")
        sample = slice(None, None, sample_stride)
        q = np.asarray(archive["joint_position"], dtype=float)[sample]
        qdot = np.asarray(archive["joint_velocity"], dtype=float)[sample]
        twist = np.asarray(archive["wbc_task_twist"], dtype=float)[sample]
        pose = np.asarray(archive["pose_error"], dtype=float)[sample]
        twist_error = np.asarray(archive["wbc_twist_error"], dtype=float)[sample]
        target = np.asarray(archive["teacher_action"], dtype=float)[sample]
    if not (q.shape == (len(q), 7) and qdot.shape == q.shape and twist.shape == (len(q), 6) and pose.shape == (len(q), 6) and twist_error.shape == (len(q), 6) and target.shape == (len(q), 7)):
        raise ValueError(f"{path}: invalid Direct ESN archive dimensions")
    observations = [DirectESNObservation(qi, qdoti, twisti, posei, twist_error_i) for qi, qdoti, twisti, posei, twist_error_i in zip(q, qdot, twist, pose, twist_error)]
    return observations, np.clip(target, -1.0, 1.0)


def fit_dagger_readout(
    specs: list[tuple[Path, int, bool]], *,
    config: DirectESNConfig,
    washout_steps: int,
    neutral_repeat: int,
    rod_repeat: int,
) -> tuple[DirectESNController, dict]:
    """Fit one readout from base demonstrations plus student-visited labels."""

    model = DirectESNController(config)
    features_all, targets_all, episodes = [], [], []
    for path, stride, neutral in specs:
        observations, targets = _load_episode(path, stride)
        if washout_steps >= len(observations):
            raise ValueError(f"{path}: washout exceeds episode length")
        features = model.features(observations, washout_steps=washout_steps)
        repeat = neutral_repeat if neutral else rod_repeat
        features_all.extend([features] * repeat)
        targets_all.extend([targets[washout_steps:]] * repeat)
        episodes.append({"path": str(path), "sample_stride": stride, "samples": len(features), "neutral_repeat": repeat})
    design = np.concatenate(features_all, axis=0)
    targets = np.concatenate(targets_all, axis=0)
    mse = model.fit_readout(design, targets)
    return model, {"training_samples": len(design), "readout_training_mse": mse, "episodes": episodes}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--initial-model", type=Path, required=True)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--base-rod-trace", type=Path, required=True, help="4 ms privileged teacher trace; fitting decimates it by 10")
    parser.add_argument("--base-no-rod-trace", type=Path, required=True, help="40 ms fixed-WBC neutral teacher trace")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--fixture-index", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--washout-steps", type=int, default=3)
    parser.add_argument("--neutral-repeat", type=int, default=20)
    parser.add_argument("--rod-repeat", type=int, default=1, help="relative ridge-fit weight for rod-contact teacher traces")
    args = parser.parse_args()
    if args.iterations < 1 or args.neutral_repeat < 1 or args.rod_repeat < 1:
        raise ValueError("iterations and repeat weights must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    current_model = args.initial_model
    all_dagger_specs: list[tuple[Path, int, bool]] = []
    rounds = []
    for iteration in range(1, args.iterations + 1):
        rod_archive = args.output_dir / f"iteration_{iteration:02d}_rod_student_visited.npz"
        no_rod_archive = args.output_dir / f"iteration_{iteration:02d}_no_rod_student_visited.npz"
        rod = collect_student_visited_archive(
            current_model, menagerie=args.menagerie, fixture_index=args.fixture_index,
            rod_enabled=True, seed=args.seed + iteration * 10, output_path=rod_archive, iteration=iteration,
        )
        no_rod = collect_student_visited_archive(
            current_model, menagerie=args.menagerie, fixture_index=args.fixture_index,
            rod_enabled=False, seed=args.seed + iteration * 10 + 1, output_path=no_rod_archive, iteration=iteration,
        )
        all_dagger_specs.extend([(rod_archive, 1, False), (no_rod_archive, 1, True)])
        parent = DirectESNController.from_npz(current_model)
        specs = [(args.base_rod_trace, 10, False), (args.base_no_rod_trace, 1, True), *all_dagger_specs]
        model, fit = fit_dagger_readout(
            specs, config=parent.config, washout_steps=args.washout_steps,
            neutral_repeat=args.neutral_repeat, rod_repeat=args.rod_repeat,
        )
        output_model = args.output_dir / f"direct_esn_dagger_iteration_{iteration:02d}.npz"
        model.save_npz(output_model)
        current_model = output_model
        rounds.append({"iteration": iteration, "rod": rod, "no_rod": no_rod, "fit": fit, "model": str(output_model)})
    summary = {
        "schema_version": 1,
        "method": "direct_esn_dagger_privileged_teacher",
        "student_input": list(DirectESNController.from_npz(current_model).contract()["student_input_fields"]),
        "forbidden_online_inputs": DirectESNController.from_npz(current_model).contract()["forbidden_online_inputs"],
        "base_traces": {"rod": str(args.base_rod_trace), "no_rod": str(args.base_no_rod_trace)},
        "iterations": rounds,
        "final_model": str(current_model),
    }
    (args.output_dir / "dagger_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
