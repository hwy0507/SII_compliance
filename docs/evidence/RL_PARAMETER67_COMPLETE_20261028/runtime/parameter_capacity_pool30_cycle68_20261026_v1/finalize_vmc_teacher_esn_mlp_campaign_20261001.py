#!/usr/bin/env python3
"""Freeze metadata for the 2026-10-01 VMC-teacher student comparison."""
from __future__ import annotations
import argparse, hashlib, json, platform, sys
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""): h.update(block)
    return h.hexdigest()


def summary(path):
    data = json.loads((path / "rollout.json").read_text())
    metrics = data["metrics"]
    return {
        "path": str(path), "rollout_sha256": sha(path / "rollout.json"),
        "model_sha256": data.get("neural_logging", {}).get("model_sha256"),
        "task_success": data.get("task_success"), "strict_success": data.get("strict_success"),
        "physical_valid": data.get("physical_valid"), "placement_complete": data.get("placement_complete"),
        "final_task_stage": data.get("final_task_stage"), "contact_coverage_valid": data.get("contact_coverage_valid"),
        "external_penetration_mm": 1000.0 * data["stats"]["max_external_penetration_m"],
        "position_rmse_3d_mm": 1000.0 * metrics["position_rmse_3d_m"],
        "peak_torque_nm": metrics["generalized_actuator_torque_peak_nm"],
        "peak_speed_mps": metrics["linear_speed_peak_mps"],
        "rod_contact": data["stats"].get("contact_diagnostics", {}).get("rod_longest_run"),
        "source_sha256": data.get("source_sha256", {}),
        "files_sha256": {str(p.relative_to(path)): sha(p) for p in sorted(path.rglob("*")) if p.is_file()},
    }


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--audit", type=Path, required=True); ap.add_argument("--esn", type=Path, required=True)
    ap.add_argument("--esn-model", type=Path, required=True); ap.add_argument("--mlp", type=Path, required=True)
    ap.add_argument("--mlp-model", type=Path, required=True); ap.add_argument("--vmc", type=Path, required=True)
    ap.add_argument("--reset", type=Path, required=True); ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    rows = [summary(args.vmc), summary(args.esn), summary(args.mlp), summary(args.reset)]
    labels = ["vmc_teacher", "esn", "mlp", "esn_memory_reset_ablation"]
    cases = {label: row for label, row in zip(labels, rows)}
    models = {"esn": {"path": str(args.esn_model), "sha256": sha(args.esn_model)},
              "mlp": {"path": str(args.mlp_model), "sha256": sha(args.mlp_model)}}
    report = {
        "campaign": "VMC teacher -> pure ESN/MLP office-v5 comparison",
        "host": platform.node(), "python": sys.executable, "models": models,
        "manifest_sha256": "6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3",
        "cases": cases, "independent_audit": str(args.audit),
        "policy_contract": "canonical48D/action7 pure proprioception; no contact truth, object state, event time, stage, visual/range",
        "development_dt_s": 1e-4, "formal_dt_s": 5e-5,
        "formal_rerun": "not unlocked: VMC, ESN and MLP all strict=false in the development combined fixture",
        "failure_semantics": {
            "esn": "task=false, final stage lift, placement incomplete",
            "mlp": "task=true and placement complete, strict=false because sustained rod contact coverage failed",
            "vmc_teacher": "task=true and placement complete, strict=false because sustained rod contact coverage failed",
            "esn_memory_reset_ablation": "task=false, final stage align; reset reservoir is a causal memory ablation",
        },
        "limitations": [
            "Only nine certified VMC fixtures existed; held-out replay has no active_long identity.",
            "All closed-loop runs are development dt=1e-4; no formal claim.",
            "The common fixture's contact coverage remains false for all methods; action imitation MSE is not task success.",
        ],
    }
    (args.output / "CAMPAIGN_REPORT.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
