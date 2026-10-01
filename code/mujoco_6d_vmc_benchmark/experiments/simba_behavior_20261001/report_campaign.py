"""Auditable partial/final campaign reporting; no policy/result mutation."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np

METRICS = {
    "rmse_cm": ("position_rmse_3d_m", 100.),
    "peak_torque_nm": ("generalized_actuator_torque_peak_nm", 1.),
    "peak_velocity_mps": ("linear_speed_peak_mps", 1.),
}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def _count(values):
    return {"true": sum(x is True for x in values),
            "false": sum(x is False for x in values),
            "unknown": sum(x is None for x in values)}


def counts(episodes):
    out = {key: _count([e.get(key) for e in episodes]) for key in
           ("compliant_progress_success", "strict_compliant_progress_success",
            "physical_valid", "placement_success", "legacy_task_success",
            "legacy_strict_success", "full55", "contact_coverage_valid")}
    event = Counter()
    obstacle = defaultdict(Counter)
    for e in episodes:
        for ev in e.get("event_results", []):
            status = ev.get("status", "unknown")
            event[status] += 1
            obstacle[ev.get("obstacle_id", "unknown")][status] += 1
    out["event_status_counts"] = dict(event)
    out["event_status_by_obstacle"] = {k: dict(v) for k, v in obstacle.items()}
    return out


def average(rows):
    result = {}
    for name in METRICS:
        xs = [r.get(name) for r in rows]
        result[name] = float(np.mean(xs)) if xs and all(x is not None and np.isfinite(x) for x in xs) else None
    return result


def aggregate_groups(runs):
    groups = []
    for name in ("office_task", "metric", "esn", "hybrid", "zero"):
        rs = [r for r in runs if r["group"] == name]
        episodes = [e for r in rs for e in r["episodes"]]
        g = dict(group=name, expected_runs=len(rs),
                 completed_runs=sum(r["status"] == "complete" for r in rs),
                 observed_episodes=len(episodes), counts=counts(episodes),
                 fully_observed=bool(rs and all(r["status"] == "complete" and r["case_count_matches"] for r in rs)))
        if name in ("office_task", "metric"):
            observed = [r for r in rs if r["episodes"]]
            metrics = {}
            for key in METRICS:
                vals = [r["mean_all_observed"][key] for r in observed]
                valid = bool(vals and all(x is not None for x in vals))
                metrics[key] = dict(mean=float(np.mean(vals)) if valid else None,
                    seed_sd=float(np.std(vals, ddof=1)) if valid and len(vals)>1 else None,
                    contributing_seeds=len(vals),
                    seed_values=[dict(seed=r["training_seed"], value=r["mean_all_observed"][key],
                                      episodes=len(r["episodes"])) for r in observed])
            g.update(metrics=metrics, uncertainty_unit="sample SD across training-seed means; each mean averages its observed fixtures",
                     warning=None if g["fully_observed"] else "PARTIAL: unequal/missing seed or fixture coverage; not a final comparison")
        else:
            metrics = {}
            for key in METRICS:
                vals = [e.get(key) for e in episodes]
                valid = bool(vals and all(x is not None for x in vals))
                metrics[key] = dict(mean=float(np.mean(vals)) if valid else None,
                    seed_sd=None, condition_sd=float(np.std(vals, ddof=1)) if valid and len(vals)>1 else None,
                    conditions=len(vals))
            g.update(metrics=metrics, uncertainty_unit="one frozen policy; SD across physical conditions only, NOT training-seed uncertainty",
                     warning=None if g["fully_observed"] else "PARTIAL: conditions pending")
        groups.append(g)
    return groups


def report(campaign, *, sensitivity=False, output=None):
    campaign = Path(campaign)
    if not campaign.is_dir():
        raise FileNotFoundError("Campaign directory has not been created; reporter never reserves a future run path: "+str(campaign))
    output = Path(output) if output else campaign/"report"
    errors, pending, runs, model_hashes = [], [], [], defaultdict(dict)
    def error(where, message):
        errors.append(dict(where=str(where), message=message))
    protocol_path = campaign/"PROTOCOL.json"
    protocol = read(protocol_path) if protocol_path.exists() else {}
    if not protocol:
        pending.append(str(protocol_path))
    specs = [dict(x, method="rl", group=x["reward"], training_seed=x["seed"]) for x in protocol.get("runs", [])]
    specs += [dict(id=x, method=x, group=x, training_seed=None) for x in ("esn", "hybrid", "zero")]
    expected_manifest = protocol.get("evaluation_manifest_sha256")
    expected_duration = float(protocol.get("duration_s", 55.))
    expected_dt = float(protocol.get("evaluation_dt", .00005))
    reference_cases = None
    sensitivities = []
    for spec in specs:
        folder = campaign/"evaluation"/spec["id"]
        summary_path, ep_path = folder/"SUMMARY.json", folder/"PROTOCOL.json"
        s = read(summary_path) if summary_path.exists() else {}
        ep = read(ep_path) if ep_path.exists() else {}
        run = dict(id=spec["id"], group=spec["group"], training_seed=spec["training_seed"],
                   method=spec["method"], status=s.get("status", "pending"),
                   source_summary=str(summary_path), source_protocol=str(ep_path),
                   episodes=[], case_count_matches=False, normalizer_check="pending")
        if not s:
            pending.append(str(summary_path))
        if not ep:
            pending.append(str(ep_path))
        else:
            if ep.get("method") != spec["method"]:
                error(ep_path, "method differs from campaign run specification")
            if expected_manifest is not None and ep.get("manifest_sha256") != expected_manifest:
                error(ep_path, "manifest SHA differs from campaign")
            if ep.get("duration_s") != expected_duration or ep.get("physics_dt") != expected_dt:
                error(ep_path, "evaluation duration/dt differs from campaign")
            cases = ep.get("cases", [])
            if reference_cases is None:
                reference_cases = cases
            elif cases != reference_cases:
                error(ep_path, "ordered physical condition manifest differs across methods")
            checkpoint = ep.get("checkpoint")
            if spec["method"] == "rl" and checkpoint:
                state_path = Path(checkpoint)/"official_agent_state.json"
                if not state_path.is_file():
                    error(state_path, "RL checkpoint metadata missing; training seed unverified")
                elif read(state_path).get("config", {}).get("seed") != spec["training_seed"]:
                    error(state_path, "checkpoint training seed differs from campaign run")
                common_path = campaign/"COMMON_BUDGET.json"
                if common_path.exists() and Path(checkpoint).name != "checkpoint_step_%07d" % read(common_path)["step"]:
                    error(state_path, "checkpoint is not the registered common periodic budget")
            for key, digest in ep.get("checkpoint_sha256", {}).items():
                artifact = Path(key) if Path(key).is_absolute() else Path(checkpoint)/key
                if not artifact.is_file():
                    error(ep_path, "checkpoint artifact missing: "+str(artifact))
                elif sha(artifact) != digest:
                    error(ep_path, "checkpoint artifact hash mismatch: "+str(artifact))
        if spec["method"] == "rl" and s.get("status") == "complete":
            before, after = s.get("normalizers_before"), s.get("normalizers_after")
            run["normalizer_check"] = "pass" if before is not None and before == after else "failed"
            if run["normalizer_check"] != "pass":
                error(summary_path, "missing or changed normalizer diagnostics")
        elif spec["method"] != "rl":
            run["normalizer_check"] = "not_applicable_frozen_non_RL"
        rows = s.get("rows", [])
        run["case_count_matches"] = bool(ep and len(rows) == len(ep.get("cases", [])))
        if s.get("status") == "complete" and not run["case_count_matches"]:
            error(summary_path, "complete summary has missing/extra cases")
        for index, row in enumerate(rows):
            case = row.get("case", {})
            if index >= len(ep.get("cases", [])) or case != ep["cases"][index]:
                error(summary_path, "case ordering/seed/physical settings mismatch at index"+str(index))
            raw_path = Path(row["raw_result"])
            raw = read(raw_path) if raw_path.exists() else {}
            if not raw:
                error(raw_path, "raw rollout missing")
            arguments = raw.get("arguments", {})
            for key in ("seed", "variant", "ball_speed", "person_stroke", "rod_stroke"):
                if key in case and arguments.get(key) != case[key]:
                    error(raw_path, key+" differs from declared condition")
            if arguments.get("dt") != expected_dt or arguments.get("duration") != expected_duration:
                error(raw_path, "raw duration/dt differs from campaign")
            behavior = row.get("behavior", {})
            required = set(raw.get("contact_required", []))
            if not required.issubset(behavior.get("required_contacts", [])):
                error(raw_path, "behavior removes original required contact(s)")
            metric = row.get("metrics", {})
            if metric != raw.get("metrics"):
                error(raw_path, "summary metrics differ from raw rollout metrics")
            episode = dict(run=spec["id"], group=spec["group"], training_seed=spec["training_seed"],
                case_index=index, case=case, raw_result=str(raw_path),
                compliant_progress_success=behavior.get("compliant_progress_success"),
                strict_compliant_progress_success=behavior.get("strict_compliant_progress_success"),
                physical_valid=raw.get("physical_valid"), placement_success=raw.get("placement_complete"),
                legacy_task_success=raw.get("task_success"), legacy_strict_success=raw.get("strict_success"),
                contact_coverage_valid=raw.get("contact_coverage_valid"),
                contact_required=raw.get("contact_required"), event_results=behavior.get("event_results", []),
                abort_reason=raw.get("abort_reason"), reported_full_horizon=raw.get("full_task_horizon_completed"),
                planned_duration_s=expected_duration, actual_duration_s=None, full55=None)
            for dest, (source, scale) in METRICS.items():
                val = metric.get(source)
                episode[dest] = float(val)*scale if val is not None and np.isfinite(val) else None
                if episode[dest] is None:
                    error(raw_path, "missing/nonfinite metric "+source)
            npz = raw_path.parent/(raw_path.stem+"_metrics")/"substep_metrics.npz"
            if npz.exists():
                with np.load(npz, allow_pickle=False) as z:
                    dt, times = z["dt"], z["time"]
                    actual = float(dt.sum())
                    valid_times = bool(len(times) == len(dt) and len(dt) > 0 and
                        np.isfinite(dt).all() and np.isfinite(times).all() and
                        np.all(dt > 0) and np.all(np.diff(times) > 0))
                    if not valid_times:
                        error(npz, "invalid physical-substep time arrays")
                    if len(times) and abs(float(times[-1])-actual)>1e-6:
                        error(npz, "final physical time differs from accumulated dt")
                    if len(dt) != metric.get("samples"):
                        error(npz, "sample count differs from summary")
                    if not np.allclose(dt, expected_dt, atol=1e-12, rtol=0):
                        error(npz, "actual physics dt differs from registered evaluation dt")
                    episode.update(actual_duration_s=actual, physical_substeps=len(dt),
                                   actual_last_time_s=float(times[-1]) if len(times) else None)
                    full = bool(valid_times and abs(actual-expected_duration)<1e-6 and
                                not raw.get("abort_reason") and raw.get("execution_complete") and
                                raw.get("full_task_horizon_completed"))
                    episode["full55"] = full
                    if bool(raw.get("full_task_horizon_completed")) and not full:
                        error(npz, "claimed full horizon inconsistent with actual duration/execution")
            else:
                error(npz, "raw substep arrays missing; actual duration not verified")
            mjb = raw_path.with_suffix(".mjb")
            if mjb.exists():
                digest = sha(mjb)
                episode["actual_model_sha256"] = digest
                if digest != row.get("model_sha256") or digest != raw.get("model_sha256"):
                    error(mjb, "actual MJB SHA differs from row/raw recorded hash")
                identity = json.dumps(case, sort_keys=True)
                model_hashes[identity][spec["id"]] = digest
            else:
                error(mjb, "compiled physical model missing")
            if sensitivity:
                from behavior_evaluate import evaluate
                from behavior_protocol import DEFAULT
                trace = raw_path.parent/(raw_path.stem+"_behavior.npz")
                for factor in (.5, 1., 2.):
                    th = replace(DEFAULT, position_m=DEFAULT.position_m*factor,
                        rotation_rad=DEFAULT.rotation_rad*factor, speed_mps=DEFAULT.speed_mps*factor,
                        tangent_m=DEFAULT.tangent_m*factor, progress_m=DEFAULT.progress_m*factor)
                    result = evaluate(raw, trace, thresholds=th)
                    sensitivities.append(dict(run=spec["id"], case_index=index, factor=factor,
                        compliant_progress_success=result["compliant_progress_success"],
                        strict_compliant_progress_success=result["strict_compliant_progress_success"],
                        behavior_status=result["behavior_status"]))
            run["episodes"].append(episode)
        run["mean_all_observed"] = average(run["episodes"])
        run["mean_full55_only_diagnostic"] = average([e for e in run["episodes"] if e["full55"] is True])
        run["counts"] = counts(run["episodes"])
        runs.append(run)
    hash_checks = []
    for identity, hashes in model_hashes.items():
        match = len(set(hashes.values())) <= 1
        hash_checks.append(dict(case=json.loads(identity), hashes_by_run=hashes, identical=match))
        if not match:
            error("cross_method_model", "physical MJB hash mismatch for "+identity)
    all_episodes = [e for run in runs for e in run["episodes"]]
    complete = bool(protocol and all(r["status"] == "complete" and r["case_count_matches"] for r in runs))
    all_full = bool(all_episodes and all(e["full55"] is True for e in all_episodes))
    statuses = {}
    for phase in ("TRAINING", "EVALUATION"):
        path = campaign/(phase+"_STATUS.json")
        statuses[phase.lower()] = read(path) if path.exists() else None
        if not path.exists():
            pending.append(str(path))
        if statuses[phase.lower()] is not None:
            for job in statuses[phase.lower()]:
                if job.get("returncode") != 0:
                    error(path, "job failed/skipped: "+str(job.get("id")))
    if not (campaign/"COMMON_BUDGET.json").exists():
        pending.append(str(campaign/"COMMON_BUDGET.json"))
    complete = bool(complete and not pending)
    output_data = dict(created_utc=datetime.now(timezone.utc).isoformat(), campaign=str(campaign),
        status="complete" if complete else "partial", campaign_protocol=protocol,
        common_budget=read(campaign/"COMMON_BUDGET.json") if (campaign/"COMMON_BUDGET.json").exists() else None,
        groups=aggregate_groups(runs), runs=runs, pending=sorted(set(pending)), job_status=statuses,
        audits=dict(errors=errors, pass_all_completed_checks=not errors,
            cross_method_physical_models=hash_checks,
            raw_duration_scope="all available episode physical-substep dt arrays",
            normalizer_scope="recorded before/after sample/scale/counter diagnostics, not full tensor hash"),
        all_observed_full55=all_full,
        comparable_full55_matrix=bool(complete and all_full and not errors),
        early_or_unverified_horizon=[e for e in all_episodes if e["full55"] is not True],
        sensitivity=dict(enabled=sensitivity, factors=[.5,1.,2.],
            scope="position/rotation/speed recovery tolerances and tangent/progress distance thresholds scaled jointly; time windows, required exposure and physical gates unchanged; all factors reported, no best-factor selection",
            rows=sensitivities),
        limitations=[
            "Finite-budget results do not establish convergence or inherent algorithm inferiority.",
            "New physical parameter draws use previously seen office geometry, not unseen-office or hardware validation.",
            "ESN uses earlier teacher pretraining; training budgets and data are not equal to from-scratch RL.",
            "Behavior is local impact recovery/onward progress or sustained-contact net progress, not complete obstacle clearance or placement.",
            "False, unknown and not_exposed are retained; physical validity and placement remain separate.",
            "RL uncertainty uses training-seed means. ESN/hybrid/zero condition SD is not training-seed uncertainty.",
            "All observed failures remain in metric means; mixed-duration means are diagnostic and cannot support rankings.",
            "Threshold factors are development sensitivity analysis, not an opportunity to select favorable success definitions."])
    output.mkdir(parents=True, exist_ok=True)
    (output/"SUMMARY.json").write_text(json.dumps(output_data, indent=2, allow_nan=False)+"\n")
    lines = ["# Shared Office baseline campaign report", "",
        "Status: **"+output_data["status"]+"**. Available episodes: "+str(len(all_episodes))+".",
        "Comparison gate: "+("all required checks and full-duration matrix passed" if output_data["comparable_full55_matrix"] else
        "**not eligible for a complete full55s ranking** (pending evidence, early/unverified duration or audit errors)."), "",
        "All recorded episodes, including failures, enter descriptive metric means. Stable placement is separate from local compliant progress.", "",
        "| Method | Runs complete | Episodes | Local progress T/F/? | Strict T/F/? | Placement T/F/? | Physical T/F/? | Full55 T/F/? | RMSE cm | Peak torque Nm | Peak speed m/s |",
        "|---|---:|---:|---|---|---|---|---|---|---|---|"]
    def fmt_count(v): return "/".join(str(v[k]) for k in ("true","false","unknown"))
    def fmt_metric(v, rl):
        if v["mean"] is None: return "pending"
        sd = v["seed_sd"] if rl else v.get("condition_sd")
        return f'{v["mean"]:.6g}'+(f" ± {sd:.4g}" if sd is not None else " (SD unavailable)")
    for g in output_data["groups"]:
        ct = g["counts"]
        cells = [g["group"], f'{g["completed_runs"]}/{g["expected_runs"]}', str(g["observed_episodes"])]
        cells += [fmt_count(ct[k]) for k in ("compliant_progress_success","strict_compliant_progress_success","placement_success","physical_valid","full55")]
        cells += [fmt_metric(g["metrics"][k], g["group"] in ("office_task","metric")) for k in METRICS]
        lines.append("| "+" | ".join(cells)+" |")
    lines += ["", "RL: mean ± sample SD across training-seed means. ESN/hybrid/zero: one frozen policy, mean ± condition SD only. Missing data is pending, not zero.", "",
              "## Exposure and per-event outcomes", ""]
    for g in output_data["groups"]:
        lines.append("- "+g["group"]+": "+json.dumps(g["counts"]["event_status_by_obstacle"], sort_keys=True))
    lines += ["", "## Horizon audit", ""]
    early = output_data["early_or_unverified_horizon"]
    lines += [f'- {e["run"]} case{e["case_index"]}: actual={e["actual_duration_s"]}s; planned={e["planned_duration_s"]}s; abort={e["abort_reason"]}.' for e in early] or ["No early/unverified horizons among observed episodes."]
    lines += ["", "## Audit errors and pending evidence", ""]
    lines += ["- "+e["where"]+": "+e["message"] for e in errors] or ["No inconsistency detected in available completed checks."]
    lines += ["- Pending: "+x for x in output_data["pending"]]
    lines += ["", "## Interpretation boundaries", ""]+["- "+x for x in output_data["limitations"]]
    lines += ["", "Sensitivity: "+("all three factors included in SUMMARY.json; none selected" if sensitivity else "not requested; pending"), "",
              "Machine-readable per-case, seed, contact-status, hash, normalizer and duration evidence: "+str(output/"SUMMARY.json")]
    (output/"REPORT.md").write_text("\n".join(lines)+"\n")
    return output_data


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--campaign", type=Path, required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--sensitivity", action="store_true")
    a = p.parse_args()
    data = report(a.campaign, sensitivity=a.sensitivity, output=a.output)
    print(json.dumps(dict(status=data["status"], report=str((a.output or a.campaign/"report")/"REPORT.md"),
                         audit_errors=len(data["audits"]["errors"]),
                         comparable_full55_matrix=data["comparable_full55_matrix"])))
    # Partial reports are intentionally valid; completed inconsistent matrices
    # still produce evidence, but return nonzero for the campaign supervisor.
    if data["status"] == "complete" and data["audits"]["errors"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
