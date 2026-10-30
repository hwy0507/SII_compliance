"""Replay every frozen v7 MLP candidate on the seen rod_00 train episode."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from current_student_policy_20260921 import load_current

FIT = ROOT / "outputs/contact_yield_recovery_retrain_20261030_v7"
TEACHER = ROOT / "outputs/contact_yield_scrape_collection_20261030_v1/rod_00/rod"
DEST = ROOT.parents[1] / "docs/evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_V7_MLP_CANDIDATE_GRID_TRAIN_FIT_20261031.json"
WINDOWS = ((0.0, 4.2), (4.2, 4.7), (4.7, 5.0), (5.0, 8.0), (8.0, 12.76))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    if DEST.exists():
        raise FileExistsError(f"Preserve prior evidence: {DEST}")

    execution = read(FIT / "execution.json")
    audit = read(FIT / "FIT_AUDIT.json")
    lock = read(FIT / "MODEL_LOCK.json")
    data_meta = read(FIT / "data/DATA_COMPLETE.json")
    assert execution["status"] == "complete" and len(execution["fits"]) == 75
    assert audit["status"] == "passed" and len(audit["candidate_jobs"]) == 75
    assert lock["status"] == "frozen" and len(lock["models"]) == 9

    data_path = FIT / "data/training_data.npz"
    assert sha(data_path) == data_meta["training_data_sha256"]
    with np.load(data_path, allow_pickle=False) as data:
        ids = np.flatnonzero((data["episode"] == 0) & data["train"])
        observations = data["observation"][ids].copy()
        target = data["requested_teacher_action"][ids].copy()
        importance = data["importance"][ids].copy()
    with np.load(TEACHER / "trajectory.npz", allow_pickle=False) as tape:
        teacher_obs = tape["observation"].copy()
        teacher_action = tape["action"].copy()
        times = tape["time"].copy()
    assert len(ids) == 500 and np.all(importance > 0)
    assert np.array_equal(observations, teacher_obs)
    assert np.array_equal(target, teacher_action)
    assert times.shape == (500,) and np.all(np.isfinite(observations))

    fits = [item for item in execution["fits"] if item["family"] == "mlp_scratch"]
    assert len(fits) == 36 and all(item["status"] == "complete" for item in fits)
    rows = []
    for item in fits:
        output = Path(item["output"])
        checkpoint = output / "checkpoint.npz"
        metadata_path = output / "TRAINING_COMPLETE.json"
        metadata = read(metadata_path)
        assert sha(checkpoint) == item["checkpoint_sha256"] == metadata["checkpoint_sha256"]
        assert metadata["updates"] == metadata["selected_update"] == 32000
        assert metadata["trainable_parameters"] == 5504

        actor = load_current(checkpoint)
        actor.reset()
        prediction = np.asarray([actor.act(obs) for obs in observations])
        error = prediction - target
        windows = []
        for start, end in WINDOWS:
            mask = (times >= start) & (times < end)
            values = error[mask]
            windows.append({
                "start_s": start,
                "end_s": end,
                "frames": int(mask.sum()),
                "requested_action_rmse": float(np.sqrt(np.mean(values ** 2))),
            })

        validation = next(
            result["validation_mse"] for result in audit["candidate_jobs"]
            if result["name"] == item["name"]
        )
        model = next(
            result for result in lock["models"]
            if result["family"] == "mlp_scratch" and result["seed"] == item["seed"]
        )
        rows.append({
            "name": item["name"],
            "seed": item["seed"],
            "selected_by_registered_validation": model["selected_trial"] == item["name"],
            "validation_mse": validation,
            "checkpoint_sha256": item["checkpoint_sha256"],
            "metadata_sha256": sha(metadata_path),
            "architecture": {
                "width": metadata["width"],
                "trainable_parameters": metadata["trainable_parameters"],
                "learning_rate": metadata["learning_rate"],
                "weight_decay": metadata["weight_decay"],
                "lr_schedule": metadata["lr_schedule"],
            },
            "full_rod_00_train_rmse": float(np.sqrt(np.mean(error ** 2))),
            "windows": windows,
        })

    best = {}
    for seed in sorted({row["seed"] for row in rows}):
        seed_rows = [row for row in rows if row["seed"] == seed]
        chosen = next(row for row in seed_rows if row["selected_by_registered_validation"])
        minimum = min(seed_rows, key=lambda row: row["full_rod_00_train_rmse"])
        best[str(seed)] = {
            "selected_candidate": chosen["name"],
            "selected_train_rmse": chosen["full_rod_00_train_rmse"],
            "best_train_candidate": minimum["name"],
            "best_train_rmse": minimum["full_rod_00_train_rmse"],
            "selected_to_best_ratio": chosen["full_rod_00_train_rmse"] / minimum["full_rod_00_train_rmse"],
        }

    result = {
        "schema": "sii-contact-yield-v7-mlp-candidate-grid-train-fit-v1",
        "status": "complete_frozen_candidate_train_sequence_replay",
        "dataset_sha256": data_meta["training_data_sha256"],
        "data_metadata_sha256": sha(FIT / "data/DATA_COMPLETE.json"),
        "fit_execution_sha256": sha(FIT / "execution.json"),
        "fit_audit_sha256": sha(FIT / "FIT_AUDIT.json"),
        "model_lock_sha256": sha(FIT / "MODEL_LOCK.json"),
        "teacher_episode_sha256": sha(TEACHER / "trajectory.npz"),
        "analyzer_sha256": sha(Path(__file__)),
        "identity": {
            "dataset_episode": 0,
            "frames": len(ids),
            "observations_exactly_match_teacher": True,
            "requested_action_labels_exactly_match_teacher": True,
            "all_rows_positive_weight_training_rows": True,
        },
        "candidate_count": len(rows),
        "selected_vs_best_train_fit": best,
        "rows": rows,
        "limitations": [
            "This replay evaluates only a previously seen training episode; it is not independent validation or closed-loop evidence.",
            "Candidate selection remains the registered six-identity validation MSE; this analysis does not reselect models.",
            "The v7 MLP search varied learning rate and weight decay while keeping a 128-unit, 5504-parameter single-hidden-layer network fixed.",
            "Requested-action error does not establish the cause of the fixed27 penetration failures.",
            "No physics, optimizer update, model reselection, or final108 access occurred.",
        ],
        "new_physics_steps": 0,
        "new_optimizer_updates": 0,
        "model_reselection": False,
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(DEST)
    print("validated MLP candidates:", len(rows))
    for seed, summary in best.items():
        print(seed, summary)
    print("all candidate train RMSE:", min(row["full_rod_00_train_rmse"] for row in rows),
          "to", max(row["full_rod_00_train_rmse"] for row in rows))


if __name__ == "__main__":
    main()
