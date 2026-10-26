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
import math
from pathlib import Path
from typing import Any

import numpy as np


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


def expected_grid(registration):
    if registration.get('schema') == 'sii-nonrl-spt-diagnostic-20261026-v1':
        methods = registration['methods']
        require(bool(methods) and len(set(methods)) == len(methods), 'invalid diagnostic model grid')
        require(set(methods) == {m['name'] for m in registration['models']}, 'registered models mismatch')
        require(set(registration['conditions']) == EXPECTED_CONDITIONS, 'diagnostic conditions changed')
        return set(methods), EXPECTED_CONDITIONS
    require(registration.get('schema') == 'sii-nonrl-spt-matrix-20261025-v1', 'unknown matrix schema')
    return EXPECTED_METHODS, EXPECTED_CONDITIONS


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
    require(execution.get("report_sha256") == sha(report_path), "coordinator report hash mismatch")
    registration = read(root / "REGISTRATION.json")
    require(report.get("registration_sha256") == sha(root / "REGISTRATION.json"), "registration hash mismatch")
    models = {m["name"]: m for m in registration["models"]}
    expected_methods, expected_conditions = expected_grid(registration)
    diagnostic = registration['schema'] == 'sii-nonrl-spt-diagnostic-20261026-v1'
    if diagnostic:
        require(sha(root/'INPUT_MODEL_LOCK.json') == registration['model_lock_sha256'], 'model lock mismatch')
        require(sha(root/'coordinator.py') == registration['coordinator_sha256'], 'coordinator mismatch')
    verified_sources: set[tuple[str, str]] = set()
    contact_supplement = []
    rows = report.get("rows", [])
    expected_count = len(expected_methods)*len(expected_conditions)
    require(len(rows) == expected_count, f"expected {expected_count} rows, found {len(rows)}")
    require(execution.get('expected') == expected_count and execution.get('completed') == expected_count, 'execution grid incomplete')
    keys = {(r.get("method"), r.get("condition")) for r in rows}
    require(keys == {(m,c) for m in expected_methods for c in expected_conditions}, "method/condition grid mismatch")
    require(len(keys) == len(rows), "duplicate method/condition rows")
    qualified = [r["completion_time_s"] for r in rows if r["task_success"] and r["strict_success"]]
    require(all(t is not None and math.isfinite(t) and t > 0 for t in qualified), "invalid successful completion time")
    t_ref = min(qualified) if qualified else None
    require(report["t_ref_s"] == t_ref, "T_ref does not match full matrix")
    for row in rows:
        expected = t_ref / max(row["completion_time_s"], t_ref) if t_ref is not None and row["task_success"] and row["strict_success"] else 0.0
        require(math.isclose(row["spt"], expected, rel_tol=1e-12, abs_tol=1e-12), "SPT mismatch")
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
        require(audit.get("action_replay_max_abs") == 0.0, f"actor replay mismatch: {run}")
        require(float(audit.get("common_filter_replay_max_abs", 1.0)) == 0.0, f"filter replay mismatch: {run}")
        receipt = read(run / "execution.json")
        require(receipt.get("status") == "complete", f"unfinished episode: {run}")
        checkpoint_hash = models[row["method"]]["checkpoint_sha256"]
        require(sha(run / "checkpoint.npz") == checkpoint_hash == receipt.get("checkpoint_sha256"), f"checkpoint mismatch: {run}")
        config = root / "configs" / f"{row['method']}__{row['condition']}.json"
        require(sha(config) == receipt.get("config_sha256"), f"config hash mismatch: {run}")
        require(receipt["runtime_provenance"]["condition_id"] == row["condition"], f"condition mismatch: {run}")
        require(receipt["runtime_provenance"]["physics_dt_s"] == 5e-5, f"physics dt mismatch: {run}")
        require(bool(audit["task_success"]) == row["task_success"] and bool(audit["strict_success"]) == row["strict_success"], f"success flags mismatch: {run}")
        for relative, digest in receipt["source_sha256"].items():
            if (relative, digest) not in verified_sources:
                require(sha(root / "source" / relative) == digest, f"source hash mismatch: {relative}")
                verified_sources.add((relative, digest))
        with np.load(run / "rollout_metrics/substep_metrics.npz", allow_pickle=False) as z:
            dt = z["dt"].copy()
            torque = np.abs(z["qfrc_actuator"][:, :7])
        with np.load(run / "research_substeps.npz", allow_pickle=False) as z:
            force = z["contact_force_sum"][:, 2].copy()
        require(len(dt) == len(torque) == len(force), f"substep alignment mismatch: {run}")
        require(np.isfinite(dt).all() and np.all(dt > 0) and np.isfinite(torque).all() and np.isfinite(force).all(), f"invalid contact telemetry: {run}")
        threshold = np.asarray(row["comfort"]["comfort_threshold_nm"])
        contact = force > row["comfort"]["human_force_threshold_n"]
        excess = np.maximum(torque - threshold, 0.)
        contact_supplement.append({
            "method": row["method"], "condition": row["condition"],
            "human_force_peak_n": float(force.max()),
            "human_contact_impulse_ns": float(np.sum(force[contact] * dt[contact])),
            "human_contact_duration_s": float(dt[contact].sum()),
            "comfort_exceed_duration_s": float(dt[contact & np.any(torque / threshold > 1. + 1e-6, axis=1)].sum()),
            "comfort_excess_integral_nm_s_by_joint": (excess[contact] * dt[contact, None]).sum(0).tolist(),
            "task_failure_stage": audit.get("stage") if not row["task_success"] else None,
            "abort_reason": audit.get("abort_reason"),
            "machine_safety_violation_reasons": row["comfort"]["machine_safety_violation_reasons"],
        })
        del dt, torque, force, excess, contact

    supplement_path = root / "SUPPLEMENTAL_CONTACT.json"
    supplement_path.write_text(json.dumps({"rows": contact_supplement,
        "definition": "Human force channel index 2; contact force >0.05N; impulse over contact dt. Torque excess integral uses exact empirical thresholds; exceed duration uses the registered 1e-6 relative tolerance."}, indent=2) + "\n")

    # Matplotlib is intentionally imported only for this final presentation step.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    primary = ['esn_gradient_s2026101301', 'rnn_scratch_s2026101301', 'mlp_scratch_s2026101301']
    methods = registration['methods'] if diagnostic else primary + sorted(EXPECTED_METHODS - set(primary))
    subtitle = ('Seen diagnostic conditions; constant/cosine 32k controls + analytic ridge auxiliary'
                if diagnostic else 'Left: matched one-seed controls | Right: historical auxiliary, unequal training')
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
        if not diagnostic: ax.axvline(2.5, color='black', linestyle='--', alpha=.5)
        ax.set_ylabel(ylabel); ax.set_title(title + '\n' + subtitle); ax.grid(axis="y", alpha=.25); ax.legend()
        fig.tight_layout(); fig.savefig(root / name, dpi=180); plt.close(fig)

    draw("metrics_success_spt.png", "Non-RL Task/Strict success and SPT", [
        ("Task success", [success(m, "task_success") for m in methods]),
        ("Strict success", [success(m, "strict_success") for m in methods]),
        ("SPT", [mean(m, "spt") for m in methods]),
    ], "rate / SPT")
    fig, axes = plt.subplots(2, 1, figsize=(13, 10), sharex=True)
    axes[0].bar(labels, [mean(m, "peak_torque_nm") for m in methods])
    axes[0].set_ylabel("Mean episode peak torque (Nm)")
    axes[1].bar(labels, [100 * comfort(m) for m in methods])
    axes[1].set_ylabel("Contact-time compliance (%)")
    axes[1].set_ylim(0, 105)
    for ax in axes:
        ax.grid(axis="y", alpha=.25)
        if not diagnostic: ax.axvline(2.5, color='black', linestyle='--', alpha=.5)
    axes[1].tick_params(axis="x", labelrotation=35)
    for label in axes[1].get_xticklabels():
        label.set_ha("right")
    fig.suptitle("Peak torque and empirical comfort proxy\n" + subtitle)
    fig.tight_layout()
    fig.savefig(root / "metrics_torque_comfort.png", dpi=180)
    plt.close(fig)
    draw("metrics_machine_safety.png", "Non-RL machine-safety violation rate", [
        ("Violation rate ×100", [100 * float(np.mean([r["comfort"]["machine_safety_violation"] for r in grouped[m]])) for m in methods]),
    ], "percent")

    summary = {
        "status": "passed",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "report_sha256": sha(report_path),
        "execution_sha256": sha(execution_path),
        "verified_rows": len(rows),
        "verified_source_entries": len(verified_sources),
        "contact_supplement_sha256": sha(supplement_path),
        "t_ref_s": t_ref,
        "figures": ["metrics_success_spt.png", "metrics_torque_comfort.png", "metrics_machine_safety.png"],
        "limitation": "T_ref is the post-hoc minimum Task AND Strict successful completion time. " + subtitle + '. Not final multi-seed superiority evidence.',
    }
    (root / "FINAL_AUDIT.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
