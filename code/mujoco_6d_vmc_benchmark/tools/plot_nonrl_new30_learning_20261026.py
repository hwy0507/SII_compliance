"""Plot immutable selected-model records; no fitting, selection or physics."""
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock_path = args.root / "MODEL_LOCK.json"
    lock = json.loads(lock_path.read_text())
    assert lock["status"] == "frozen" and len(lock["models"]) == 9
    records = []
    for model in lock["models"]:
        checkpoint, metadata = Path(model["checkpoint"]), Path(model["metadata"])
        assert sha(checkpoint) == model["checkpoint_sha256"]
        assert sha(metadata) == model["metadata_sha256"]
        record = {key: model[key] for key in (
            "name", "family", "seed", "selected_trial", "validation_mse",
            "checkpoint_sha256", "metadata_sha256")}
        if model["family"] != "esn":
            history_path = metadata.parent / "history.json"
            history = json.loads(history_path.read_text())
            updates = [row["update"] for row in history]
            assert all(a < b for a, b in zip(updates, updates[1:]))
            assert updates[-1] == 32000
            assert math.isclose(history[-1]["validation_mse"], model["validation_mse"], rel_tol=1e-12)
            curves = [{k: row[k] for k in (
                "update", "validation_mse", "full_train_deployed_mse") if k in row}
                for row in history]
            assert all(math.isfinite(v) and v > 0 for row in curves
                       for k, v in row.items() if k != "update")
            train = [row for row in curves if "full_train_deployed_mse" in row]
            tail = [row["full_train_deployed_mse"] for row in train if row["update"] >= 28800]
            record.update(history_path=str(history_path), history_sha256=sha(history_path),
                          curves=curves, train_points=len(train), validation_points=len(curves),
                          train_first=train[0]["full_train_deployed_mse"],
                          train_last=train[-1]["full_train_deployed_mse"],
                          tail_train_points=len(tail),
                          tail_train_relative_range=(max(tail)-min(tail))/(sum(tail)/len(tail)))
        records.append(record)
    expected = {(family, seed) for family in ("esn", "rnn", "mlp")
                for seed in (2026102601, 2026102602, 2026102603)}
    assert {(r["family"], r["seed"]) for r in records} == expected
    args.output.mkdir(parents=True, exist_ok=False)
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.4), sharex=True, sharey=True,
                             layout="constrained")
    for record in records:
        if record["family"] == "esn":
            continue
        row = ("rnn", "mlp").index(record["family"])
        col = record["seed"] - 2026102601
        ax = axes[row, col]
        curves = record["curves"]
        train = [p for p in curves if "full_train_deployed_mse" in p]
        ax.semilogy([p["update"] for p in curves], [p["validation_mse"] for p in curves],
                    color="#c46b17", lw=1.25, label="Validation (6 episodes)")
        ax.semilogy([p["update"] for p in train], [p["full_train_deployed_mse"] for p in train],
                    color="#246b9d", marker=".", ms=3, lw=1.3, label="Full train (24 episodes)")
        ax.set_title(f"{record['family'].upper()} | seed {record['seed']}\n{record['selected_trial'].split('_')[-1]}", fontsize=10)
        ax.grid(alpha=.2)
        ax.set_xlim(0, 32000)
        if row == 1:
            ax.set_xlabel("Optimizer updates")
        if col == 0:
            ax.set_ylabel("Deployed requested-action MSE (log)")
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("New 30 demonstrations | Locked terminal models | No smoothing", fontsize=12)
    fig.savefig(args.output / "selected_learning_curves.png", dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.2, 4.5), layout="constrained")
    for i, family in enumerate(("esn", "rnn", "mlp")):
        selected = sorted((r for r in records if r["family"] == family), key=lambda r: r["seed"])
        for j, record in enumerate(selected):
            ax.scatter(i+(j-1)*.13, record["validation_mse"], marker=("o", "s", "^")[j],
                       color=("#246b9d", "#c46b17", "#4b8342")[j],
                       label=f"seed {record['seed']}" if i == 0 else None)
    ax.set_xticks(range(3), ["ESN (analytic ridge)", "RNN", "MLP"])
    ax.set_yscale("log")
    ax.set_ylabel("Terminal validation action MSE (log)")
    ax.set_title("Same 6 selection-validation episodes; not closed-loop performance", fontsize=10)
    ax.grid(axis="y", alpha=.2)
    ax.legend(fontsize=8)
    fig.savefig(args.output / "terminal_validation_mse.png", dpi=160)
    plt.close(fig)
    evidence = dict(created_utc=datetime.now(timezone.utc).isoformat(), root=str(args.root.resolve()),
                    model_lock_sha256=sha(lock_path), script_sha256=sha(Path(__file__)), models=records,
                    notes=["Selected terminal models only; all candidates remain in the training archive.",
                           "No reward series: these are imitation learners.",
                           "ESN analytic ridge has no optimizer-update curve.",
                           "Training MSE is sparsely logged; straight segments connect actual samples.",
                           "Tail range is descriptive, not a registered convergence test.",
                           "Validation is used for selection, not an unseen test claim."],
                    figures={p.name: sha(p) for p in sorted(args.output.glob("*.png"))})
    (args.output / "LEARNING_CURVE_EVIDENCE.json").write_text(json.dumps(evidence, indent=2)+"\n")
    print(json.dumps({"output": str(args.output), "models": len(records), "figures": evidence["figures"]}))


if __name__ == "__main__":
    main()
