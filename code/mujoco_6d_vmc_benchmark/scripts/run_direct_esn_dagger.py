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
from counterfactual_direct_esn_teacher import CounterfactualTeacherConfig, select_counterfactual_action
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv, VelocityResidualFixture


def _normal_from_fixture_side(side: str) -> np.ndarray:
    # This is privileged label-side geometry, not an ESN observation. The
    # current fixture family approaches from ±y; the resulting target yields
    # away from the approaching rod.
    if side == "negative_y":
        return np.array([0.0, -1.0, 0.0])
    if side == "positive_y":
        return np.array([0.0, 1.0, 0.0])
    raise ValueError(f"unsupported rod approach side {side!r}")


def _parse_dagger_fixtures(value: str | None) -> tuple[VelocityResidualFixture, ...] | None:
    """Parse an optional randomized rod pool, e.g. ``0.170,0.541,1.085;0.176,...``.

    Each entry encodes ``rod_stroke_m,rod_height_m,rod_start_time_s`` and
    becomes one pool fixture indexed by ``--fixture-indices``.  The default
    fixtures stay untouched when the flag is absent so matched evaluation
    remains exactly reproducible.
    """

    if value is None:
        return None
    fixtures = []
    for entry in value.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        parts = [part.strip() for part in entry.split(",")]
        if len(parts) != 3:
            raise ValueError("each dagger fixture needs rod_stroke_m,rod_height_m,rod_start_time_s")
        try:
            stroke, height, start = (float(part) for part in parts)
        except ValueError as exc:
            raise ValueError("dagger fixture fields must be numeric") from exc
        if min(stroke, height, start) <= 0.0:
            raise ValueError("dagger fixture fields must be positive")
        fixtures.append(VelocityResidualFixture(stroke, height, start))
    if not fixtures:
        raise ValueError("dagger fixture pool must not be empty")
    return tuple(fixtures)


def _parse_fixture_indices(value: str | None, fallback: int) -> tuple[int, ...]:
    """Parse a deterministic train-fixture pool without changing old CLI use."""

    if value is None:
        return (fallback,)
    try:
        indices = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    except ValueError as exc:
        raise ValueError("fixture indices must be comma-separated integers") from exc
    if not indices or len(set(indices)) != len(indices) or any(index < 0 for index in indices):
        raise ValueError("fixture indices must be unique non-negative integers")
    return indices


def collect_student_visited_archive(
    controller_path: Path,
    *,
    menagerie: Path,
    fixture_index: int,
    rod_enabled: bool,
    seed: int,
    output_path: Path,
    iteration: int,
    teacher_mode: str = "phase",
    counterfactual_config: CounterfactualTeacherConfig | None = None,
    counterfactual_label_dilation_steps: int = 0,
    fixtures: tuple[VelocityResidualFixture, ...] | None = None,
) -> dict:
    """Run one student rollout and construct a privileged DAgger archive."""

    if teacher_mode not in ("phase", "counterfactual"):
        raise ValueError("teacher mode must be 'phase' or 'counterfactual'")
    if teacher_mode == "counterfactual" and counterfactual_config is None:
        counterfactual_config = CounterfactualTeacherConfig()
    if counterfactual_label_dilation_steps < 0:
        raise ValueError("counterfactual label dilation must be non-negative")
    if fixtures is not None and not 0 <= fixture_index < len(fixtures):
        raise ValueError(f"fixture index {fixture_index} outside the custom pool of {len(fixtures)}")
    controller = DirectESNController.from_npz(controller_path)
    env = PandaWBCVelocityResidualEnv(
        menagerie=menagerie,
        fan_ye_model_npz=None,
        fan_ye_train_summary_json=None,
        observation_mode="direct_esn",
        rod_enabled=rod_enabled,
        seed=seed,
        fixtures=fixtures,
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
            counterfactual = None
            if teacher_mode == "counterfactual":
                # Label-side only: this evaluates cloned MjData while the
                # student rollout below still executes its own online action.
                counterfactual = select_counterfactual_action(
                    env, diagnostic["time_s"], env.previous_policy_action, counterfactual_config,
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
                "counterfactual_teacher_action": np.zeros(7, dtype=float) if counterfactual is None else counterfactual.action.copy(),
                "counterfactual_teacher_cost": 0.0 if counterfactual is None else counterfactual.cost,
                "counterfactual_predicted_peak_force_n": 0.0 if counterfactual is None else counterfactual.predicted_peak_force_n,
                "counterfactual_predicted_terminal_error_m": 0.0 if counterfactual is None else counterfactual.predicted_terminal_error_m,
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
    teacher_action = (
        build_privileged_teacher_trace(force, normal, duration, distance, pose_error)
        if teacher_mode == "phase"
        else np.asarray([row["counterfactual_teacher_action"] for row in records], dtype=float)
    )
    if teacher_mode == "counterfactual" and rod_enabled and counterfactual_label_dilation_steps:
        teacher_action = _dilate_counterfactual_labels(
            teacher_action, radius_steps=counterfactual_label_dilation_steps,
        )
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
        teacher_mode=np.full(len(records), teacher_mode),
        counterfactual_teacher_cost=np.asarray([row["counterfactual_teacher_cost"] for row in records]),
        counterfactual_predicted_peak_force_n=np.asarray([row["counterfactual_predicted_peak_force_n"] for row in records]),
        counterfactual_predicted_terminal_error_m=np.asarray([row["counterfactual_predicted_terminal_error_m"] for row in records]),
    )
    return {
        "archive": str(output_path),
        "samples": len(records),
        "fixture_index": fixture_index,
        "rollout_fixture": {
            "rod_stroke_m": env.fixture.rod_stroke_m,
            "rod_height_m": env.fixture.rod_height_m,
            "rod_start_time_s": env.fixture.rod_start_time_s,
            "grasp_time_s": env.fixture.grasp_time_s,
        },
        "rod_enabled": rod_enabled,
        "teacher_mode": teacher_mode,
        "counterfactual_horizon_steps": None if teacher_mode == "phase" else counterfactual_config.horizon_steps,
        "counterfactual_label_dilation_steps": counterfactual_label_dilation_steps,
        "teacher_nonzero_fraction": float(np.mean(np.linalg.norm(teacher_action, axis=1) > 1.0e-5)),
        "student_action_mean_norm": float(np.mean(np.linalg.norm(np.asarray([row["student_action"] for row in records]), axis=1))),
        "terminal": info,
    }


def _load_episode(path: Path, sample_stride: int) -> tuple[list[DirectESNObservation], np.ndarray, bool]:
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
        counterfactual = bool(
            "teacher_mode" in archive.files
            and len(archive["teacher_mode"])
            and str(archive["teacher_mode"][0]) == "counterfactual"
        )
    if not (q.shape == (len(q), 7) and qdot.shape == q.shape and twist.shape == (len(q), 6) and pose.shape == (len(q), 6) and twist_error.shape == (len(q), 6) and target.shape == (len(q), 7)):
        raise ValueError(f"{path}: invalid Direct ESN archive dimensions")
    observations = [DirectESNObservation(qi, qdoti, twisti, posei, twist_error_i) for qi, qdoti, twisti, posei, twist_error_i in zip(q, qdot, twist, pose, twist_error)]
    return observations, np.clip(target, -1.0, 1.0), counterfactual


def _error_aligned_targets(targets: np.ndarray) -> np.ndarray:
    """Encode 6-D yield labels as magnitudes for the aligned ESN interface.

    At deployment, direction comes from the measured WBC pose deviation.  The
    readout must therefore learn only the timing and strength of the linear and
    angular compliant response, rather than an accidental world-frame axis.
    """

    values = np.asarray(targets, dtype=float)
    if values.ndim != 2 or values.shape[1] != 7:
        raise ValueError("Direct ESN targets must be T x 7")
    aligned = values.copy()
    aligned[:, 1] = np.linalg.norm(values[:, 1:4], axis=1)
    aligned[:, 2:4] = 0.0
    aligned[:, 4] = np.linalg.norm(values[:, 4:7], axis=1)
    aligned[:, 5:7] = 0.0
    return np.clip(aligned, -1.0, 1.0)


def _dilate_counterfactual_labels(
    actions: np.ndarray, *, radius_steps: int, decay: float = 0.72,
) -> np.ndarray:
    """Spread sparse contact labels into an offline pre-contact ramp.

    This happens only in the teacher archive. A nonzero counterfactual label
    is copied only to *earlier* student-visited states with exponential
    attenuation.  States after the selected collision response keep their
    zero label, so WBC—not a persistent residual—owns rejoin.  No-rod archives
    contain no seeds and remain exactly neutral.
    """

    values = np.asarray(actions, dtype=float)
    if values.ndim != 2 or values.shape[1] != 7:
        raise ValueError("counterfactual labels must be T x 7")
    if radius_steps < 0 or not 0.0 < decay <= 1.0:
        raise ValueError("label dilation radius/decay is invalid")
    output = values.copy()
    for seed in np.flatnonzero(np.linalg.norm(values, axis=1) > 1.0e-5):
        for offset in range(-radius_steps, 1):
            index = int(seed + offset)
            if not 0 <= index < len(values):
                continue
            candidate = values[seed] * decay ** abs(offset)
            if np.linalg.norm(candidate) > np.linalg.norm(output[index]):
                output[index] = candidate
    return np.clip(output, -1.0, 1.0)


def fit_dagger_readout(
    specs: list[tuple[Path, int, bool]], *,
    config: DirectESNConfig,
    washout_steps: int,
    neutral_repeat: int,
    rod_repeat: int,
    counterfactual_zero_repeat: int,
    counterfactual_nonzero_repeat: int,
    prior_readout: np.ndarray | None = None,
    prior_readout_weight: float = 0.0,
) -> tuple[DirectESNController, dict]:
    """Fit one readout from base demonstrations plus student-visited labels."""

    model = DirectESNController(config)
    features_all, targets_all, episodes = [], [], []
    for path, stride, neutral in specs:
        observations, targets, counterfactual = _load_episode(path, stride)
        if washout_steps >= len(observations):
            raise ValueError(f"{path}: washout exceeds episode length")
        features = model.features(observations, washout_steps=washout_steps)
        labels = targets[washout_steps:]
        if config.error_aligned_yield:
            labels = _error_aligned_targets(labels)
        if counterfactual:
            nonzero = np.linalg.norm(labels, axis=1) > 1.0e-5
            repeats = np.where(nonzero, counterfactual_nonzero_repeat, counterfactual_zero_repeat)
            features_all.append(np.repeat(features, repeats, axis=0))
            targets_all.append(np.repeat(labels, repeats, axis=0))
            episodes.append({
                "path": str(path), "sample_stride": stride, "samples": len(features),
                "counterfactual": True, "nonzero_labels": int(np.sum(nonzero)),
                "zero_repeat": counterfactual_zero_repeat, "nonzero_repeat": counterfactual_nonzero_repeat,
            })
        else:
            repeat = neutral_repeat if neutral else rod_repeat
            features_all.extend([features] * repeat)
            targets_all.extend([labels] * repeat)
            episodes.append({"path": str(path), "sample_stride": stride, "samples": len(features), "repeat": repeat})
    design = np.concatenate(features_all, axis=0)
    targets = np.concatenate(targets_all, axis=0)
    mse = model.fit_readout(
        design, targets, prior_readout=prior_readout, prior_weight=prior_readout_weight,
    )
    return model, {
        "training_samples": len(design), "readout_training_mse": mse, "episodes": episodes,
        "prior_readout_weight": prior_readout_weight,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--initial-model", type=Path, required=True)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--base-rod-trace", type=Path, required=True, help="4 ms privileged teacher trace; fitting decimates it by 10")
    parser.add_argument("--base-no-rod-trace", type=Path, required=True, help="40 ms fixed-WBC neutral teacher trace")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--fixture-index", type=int, default=0)
    parser.add_argument("--fixture-indices", type=str, default=None, help="comma-separated rod-train fixture pool")
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--washout-steps", type=int, default=3)
    parser.add_argument("--neutral-repeat", type=int, default=20)
    parser.add_argument("--rod-repeat", type=int, default=1, help="relative ridge-fit weight for rod-contact teacher traces")
    parser.add_argument("--teacher-mode", choices=("phase", "counterfactual"), default="phase")
    parser.add_argument("--counterfactual-horizon-steps", type=int, default=8)
    parser.add_argument("--teacher-torque-rate-weight", type=float, default=None)
    parser.add_argument("--teacher-surge-weight", type=float, default=None)
    parser.add_argument("--counterfactual-zero-repeat", type=int, default=1)
    parser.add_argument("--counterfactual-nonzero-repeat", type=int, default=24)
    parser.add_argument("--counterfactual-label-dilation-steps", type=int, default=0)
    parser.add_argument("--prior-readout-weight", type=float, default=0.0)
    parser.add_argument("--dagger-fixtures", type=str, default=None, help="semicolon list of rod_stroke_m,rod_height_m,rod_start_time_s replacing the default pool")
    args = parser.parse_args()
    if min(args.iterations, args.neutral_repeat, args.rod_repeat, args.counterfactual_zero_repeat, args.counterfactual_nonzero_repeat) < 1 or args.counterfactual_label_dilation_steps < 0 or args.prior_readout_weight < 0.0:
        raise ValueError("iterations and repeat weights must be positive")
    teacher_kwargs = {}
    if args.teacher_torque_rate_weight is not None:
        teacher_kwargs["torque_rate_weight"] = args.teacher_torque_rate_weight
    if args.teacher_surge_weight is not None:
        teacher_kwargs["surge_weight"] = args.teacher_surge_weight
    counterfactual_config = CounterfactualTeacherConfig(
        horizon_steps=args.counterfactual_horizon_steps, **teacher_kwargs)
    dagger_fixtures = _parse_dagger_fixtures(args.dagger_fixtures)
    pool_size = len(dagger_fixtures) if dagger_fixtures is not None else 4
    fixture_indices = _parse_fixture_indices(args.fixture_indices, args.fixture_index)
    if dagger_fixtures is not None and any(index >= pool_size for index in fixture_indices):
        raise ValueError(f"fixture indices {fixture_indices} exceed the custom pool of {pool_size}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    current_model = args.initial_model
    all_dagger_specs: list[tuple[Path, int, bool]] = []
    rounds = []
    for iteration in range(1, args.iterations + 1):
        rod_archives: list[tuple[int, Path]] = [
            (fixture_index, args.output_dir / f"iteration_{iteration:02d}_fixture_{fixture_index:02d}_rod_student_visited.npz")
            for fixture_index in fixture_indices
        ]
        no_rod_archive = args.output_dir / f"iteration_{iteration:02d}_no_rod_student_visited.npz"
        rod = []
        for fixture_offset, (fixture_index, rod_archive) in enumerate(rod_archives):
            rod.append(collect_student_visited_archive(
                current_model, menagerie=args.menagerie, fixture_index=fixture_index,
                rod_enabled=True, seed=args.seed + iteration * 100 + fixture_offset, output_path=rod_archive, iteration=iteration,
                teacher_mode=args.teacher_mode, counterfactual_config=counterfactual_config,
                counterfactual_label_dilation_steps=args.counterfactual_label_dilation_steps,
                fixtures=dagger_fixtures,
            ))
        no_rod = collect_student_visited_archive(
            current_model, menagerie=args.menagerie, fixture_index=fixture_indices[0],
            rod_enabled=False, seed=args.seed + iteration * 100 + 50, output_path=no_rod_archive, iteration=iteration,
            teacher_mode=args.teacher_mode, counterfactual_config=counterfactual_config,
            counterfactual_label_dilation_steps=args.counterfactual_label_dilation_steps,
            fixtures=dagger_fixtures,
        )
        all_dagger_specs.extend([(archive, 1, False) for _, archive in rod_archives])
        all_dagger_specs.append((no_rod_archive, 1, True))
        parent = DirectESNController.from_npz(current_model)
        specs = [(args.base_rod_trace, 10, False), (args.base_no_rod_trace, 1, True), *all_dagger_specs]
        model, fit = fit_dagger_readout(
            specs, config=parent.config, washout_steps=args.washout_steps,
            neutral_repeat=args.neutral_repeat, rod_repeat=args.rod_repeat,
            counterfactual_zero_repeat=args.counterfactual_zero_repeat,
            counterfactual_nonzero_repeat=args.counterfactual_nonzero_repeat,
            prior_readout=parent.readout_copy(), prior_readout_weight=args.prior_readout_weight,
        )
        output_model = args.output_dir / f"direct_esn_dagger_iteration_{iteration:02d}.npz"
        model.save_npz(output_model)
        current_model = output_model
        rounds.append({"iteration": iteration, "rod": rod, "no_rod": no_rod, "fit": fit, "model": str(output_model)})
    summary = {
        "schema_version": 1,
        "method": f"direct_esn_dagger_{args.teacher_mode}_privileged_teacher",
        "teacher_mode": args.teacher_mode,
        "counterfactual_teacher": None if args.teacher_mode == "phase" else asdict(counterfactual_config),
        "counterfactual_label_weighting": None if args.teacher_mode == "phase" else {
            "zero_repeat": args.counterfactual_zero_repeat,
            "nonzero_repeat": args.counterfactual_nonzero_repeat,
            "dilation_steps": args.counterfactual_label_dilation_steps,
            "prior_readout_weight": args.prior_readout_weight,
        },
        "student_input": list(DirectESNController.from_npz(current_model).contract()["student_input_fields"]),
        "forbidden_online_inputs": DirectESNController.from_npz(current_model).contract()["forbidden_online_inputs"],
        "base_traces": {"rod": str(args.base_rod_trace), "no_rod": str(args.base_no_rod_trace)},
        "train_fixture_indices": list(fixture_indices),
        "dagger_fixture_pool": None if dagger_fixtures is None else [
            {"rod_stroke_m": f.rod_stroke_m, "rod_height_m": f.rod_height_m, "rod_start_time_s": f.rod_start_time_s}
            for f in dagger_fixtures
        ],
        "iterations": rounds,
        "final_model": str(current_model),
    }
    (args.output_dir / "dagger_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
