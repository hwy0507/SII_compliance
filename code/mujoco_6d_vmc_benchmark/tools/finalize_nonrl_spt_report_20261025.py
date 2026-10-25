#!/usr/bin/env python3
"""Finalize and audit a completed non-RL SPT matrix.

This is read-only with respect to episode evidence.  It verifies the matrix
contains the registered method/condition grid, checks every pinned hash, and
then writes compact tables and PNG figures beside REPORT.json.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_METHODS = {
    "esn_gradient_s2026101301", "rnn_scratch_s2026101301", "mlp_scratch_s2026101301",
    "historical_esn", "historical_matched_rnn", "historical_matched_mlp",
    "historical_ordinary_rnn", "historical_ordinary_mlp",
}
EXPECTED_CONDITIONS = {f"prospective_20261013_acceptance_{i:03d}" for i in range(8)}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    report_path = root / "REPORT.json"
    execution_path = root / "execution.json"
    require(report_path.exists() and execution_path.exists(), "matrix is not finalized")
    report = read(report_path)
    execution = read(execution_path)
    require(execution.get("status") == "complete", f"execution status is {execution.get('status')}")
    require(report.get("status") == "complete", f"report status is {report.get('status')}")
    rows = report.get("rows", [])
    require(len(rows) == 64, f"expected 64 rows, found {len(rows)}")
    keys = {(r.get("method"), r.get("condition")) for r in rows}
    require({k[0] for k in keys} == EXPECTED_METHODS, "method grid mismatch")
    require({k[1] for k in keys} == EXPECTED_CONDITIONS, "condition grid mismatch")
    require(len(keys) == len(rows), "duplicate method/condition rows")
    for row in rows:
        run = Path(row["run"])
        require(run.is_dir(), f"missing run: {run}")
        for field, filename in {
            "metric_sha256": root / "metrics" / f"{row['method']}__{row['condition']}.json",
            "audit_sha256": run / "AUDIT.json",
            "trace_sha256": run / "rollout.npz",
            "model_sha256": run / "rollout.mjb",
            "execution_sha256": run / "execution.json",
            "chain_sha256": run / "execution_chain.npz",
            "substep_metrics_sha256": run / "rollout_metrics" / "substep_metrics.npz",
            "research_substeps_sha256": run / "research_substeps.npz",
        }.items():
            require(filename.exists(), f"missing {field}: {filename}")
            require(sha(filename) == row.get(field), f"hash mismatch {field}: {filename}")
        audit = read(run / "AUDIT.json")
        require(audit.get("actor_replay_performed") is True, f"actor replay missing: {run}")
        require(float(audit.get("common_filter_replay_max_abs", 1.0)) == 0.0, f"filter replay mismatch: {run}")

    # Matplotlib is intentionally imported only for this final presentation step.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    methods = sorted(EXPECTED_METHODS)
    grouped = {m: [r for r in rows if r["method"] == m] for m in methods}
    labels = [m.replace("_s2026101301", "") for m in methods]
    def mean(m: str, key: str) -> float:
        return float(np.mean([float(r[key]) for r in grouped[m]]))
    def success(m: str, key: str) -> float:
        return float(np.mean([bool(r[key]) for r in grouped[m]]))
    def comfort(m: str) -> float:
        vals = [(r["comfort"]["human_comfort_torque_compliance"], r["comfort"]["human_contact_duration_s"])
                for r in grouped[m] if r["comfort"]["human_comfort_torque_compliance"] is not None]
        return float(sum(v * d for v, d in vals) / sum(d for _, d in vals)) if vals and sum(d for _, d in vals) else np.nan
    def draw(name: str, title: str, series: list[tuple[str, list[float]]], ylabel: str) -> None:
        fig, ax = plt.subplots(figsize=(13, 6))
        x = np.arange(len(labels)); width = 0.8 / max(1, len(series))
        for i, (label, values) in enumerate(series):
            ax.bar(x + (i - (len(series)-1)/2) * width, values, width, label=label)
        ax.set_xticks(x, labels, rotation=35, ha="right")
        ax.set_ylabel(ylabel); ax.set_title(title); ax.grid(axis="y", alpha=.25); ax.legend()
        fig.tight_layout(); fig.savefig(root / name, dpi=180); plt.close(fig)

    draw("metrics_success_spt.png", "Non-RL Task/Strict success and SPT", [
        ("Task success", [success(m, "task_success") for m in methods]),
        ("Strict success", [success(m, "strict_success") for m in methods]),
        ("SPT", [mean(m, "spt") for m in methods]),
    ], "rate / SPT")
    draw("metrics_torque_comfort.png", "Non-RL peak torque and human-contact comfort compliance", [
        ("Peak torque (Nm)", [mean(m, "peak_torque_nm") for m in methods]),
        ("Comfort compliance ×100", [100 * comfort(m) for m in methods]),
    ], "value")
    draw("metrics_machine_safety.png", "Non-RL machine-safety violation rate", [
        ("Violation rate ×100", [100 * float(np.mean([r["comfort"]["machine_safety_violation"] for r in grouped[m]])) for m in methods]),
    ], "percent")

    summary = {
        "status": "passed",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "report_sha256": sha(report_path),
        "execution_sha256": sha(execution_path),
        "verified_rows": len(rows),
        "t_ref_s": report.get("t_ref_s"),
        "figures": ["metrics_success_spt.png", "metrics_torque_comfort.png", "metrics_machine_safety.png"],
        "limitation": "T_ref is the post-hoc minimum successful Task AND Strict gate crossing requested by the user; historical methods are unequal-training auxiliary references, while the three s*_2026101301 methods are the matched primary cohort.",
    }
    (root / "FINAL_AUDIT.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
