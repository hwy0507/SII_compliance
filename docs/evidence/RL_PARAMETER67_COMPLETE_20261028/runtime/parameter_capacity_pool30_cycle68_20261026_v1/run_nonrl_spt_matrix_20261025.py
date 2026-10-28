#!/usr/bin/env python3
"""Run and audit the non-RL comparison under the 2026-10-25 metric contract.

This creates a new physical-evaluation directory from the already frozen model
lock and prospective conditions.  It does not retrain models, alter MuJoCo,
gates, actor inputs, filters, actuator limits, or ``dt``.  SPT is explicitly
marked exploratory here because the requested ``T_ref`` is the minimum
completion time observed in this matrix rather than an independently frozen
reference planner time.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import numpy as np


METHODS = (
    "esn_gradient_s2026101301",
    "rnn_scratch_s2026101301",
    "mlp_scratch_s2026101301",
    "historical_esn",
    "historical_matched_rnn",
    "historical_matched_mlp",
    "historical_ordinary_rnn",
    "historical_ordinary_mlp",
)
COMFORT_RATIO = 0.5
HUMAN_FORCE_THRESHOLD_N = 0.05
PENETRATION_LIMIT_MM = 0.2
TORQUE_EPSILON = 1e-6


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def load_diagnostic_models(path: Path) -> dict[str, Any]:
    """Only separately frozen non-RL learned-model diagnostic grids are accepted."""
    lock = read(path)
    if lock.get('schema') != 'sii-nonrl-learning-diagnostic-lock-v1' or lock.get('status') != 'frozen':
        raise ValueError('Expected frozen non-RL diagnostic model lock')
    models = lock['models']; names = [m['name'] for m in models]
    if not models or len(set(names)) != len(names):
        raise ValueError('Empty or duplicate models')
    for model in models:
        if not model['name'].replace('_','').isalnum():
            raise ValueError('Invalid model name')
        if model['family'] not in ('esn_gradient','rnn_scratch','mlp_scratch','esn_ridge'):
            raise ValueError('Not an allowed non-RL family')
        if model['worker_kind'] != 'office' or model['config'] != {}:
            raise ValueError('Diagnostic only changes learned checkpoint')
        for key in ('checkpoint','metadata'):
            if sha(Path(model[key])) != model[key+'_sha256']:
                raise ValueError(f'{key} hash mismatch')
        meta = read(Path(model['metadata']))
        if (meta['family'] != model['family'] or meta['seed'] != model['seed'] or
                meta['checkpoint_sha256'] != model['checkpoint_sha256'] or
                meta['training_data_sha256'] != lock['training_data_sha256']):
            raise ValueError('Training lineage mismatch')
    return lock


def completion_time(run: Path) -> float | None:
    """Return the first sampled final-placement gate crossing."""
    summary = read(run / "rollout.json")
    if not bool(summary.get("task_success")):
        return None
    hold = summary.get("placement_hold_s")
    trace = run / "rollout.npz"
    if hold is None or not trace.exists():
        return None
    n = int(round(float(hold) / 0.04))
    with np.load(trace, allow_pickle=False) as z:
        t = np.asarray(z["time"], dtype=float)
    if n < 13 or n > len(t) or not np.isfinite(t).all() or not np.allclose(np.diff(t), 0.04, rtol=0.0, atol=1e-8):
        return None
    return float(t[len(t) - n + 12])


def comfort_and_safety(run: Path) -> dict[str, Any]:
    with np.load(run / "rollout_metrics/substep_metrics.npz") as z:
        dt = np.asarray(z["dt"], dtype=float)
        torque = np.asarray(z["qfrc_actuator"], dtype=float)
    with np.load(run / "research_substeps.npz") as z:
        human_force = np.asarray(z["contact_force_sum"][:, 2], dtype=float)
        external_penetration = np.asarray(z["external_penetration_m"], dtype=float)
        edge_penetration = np.asarray(z["edge_penetration_m"], dtype=float)
    summary = read(run / "rollout.json")
    model = __import__("mujoco").MjModel.from_binary_path(str(run / "rollout.mjb"))
    limits = np.abs(np.asarray(model.actuator_ctrlrange[:7, 1], dtype=float))
    threshold = COMFORT_RATIO * limits
    shape_ok = torque.ndim == 2 and torque.shape[1] >= 7 and len(dt) == len(torque) == len(human_force)
    finite = shape_ok and np.isfinite(dt).all() and np.isfinite(torque[:, :7]).all() and np.isfinite(human_force).all()
    if shape_ok:
        torque = torque[:, :7]
        contact = human_force > HUMAN_FORCE_THRESHOLD_N
    else:
        dt = np.zeros(0, dtype=float); torque = np.zeros((0, 7), dtype=float); contact = np.zeros(0, dtype=bool)
    contact_duration = float(dt[contact].sum())
    within = np.max(np.abs(torque) / threshold, axis=1) <= 1.0 + TORQUE_EPSILON if len(torque) else np.zeros(0, dtype=bool)
    compliant_duration = float(dt[contact & within].sum())
    comfort_ratio = (compliant_duration / contact_duration) if contact_duration > 0 else None
    torque_ratio = np.max(np.abs(torque) / limits, axis=1) if finite else np.array([np.inf])
    max_slew = None
    if len(torque) > 1 and np.all(dt[1:] > 0):
        max_slew = float(np.max(np.abs(np.diff(torque, axis=0) / dt[1:, None])))
    penetration_mm = 1000.0 * np.maximum(external_penetration, edge_penetration)
    finite_penetration = len(penetration_mm) > 0 and np.isfinite(penetration_mm).all()
    penetration_violation = (not finite_penetration) or bool(np.nanmax(penetration_mm) > PENETRATION_LIMIT_MM + 1e-12)
    torque_violation = bool(np.nanmax(torque_ratio) > 1.0 + TORQUE_EPSILON)
    nonfinite_violation = not finite or not np.isfinite(external_penetration).all() or not np.isfinite(edge_penetration).all()
    reasons = []
    if penetration_violation: reasons.append("penetration_gt_0.2mm")
    if torque_violation: reasons.append("actuator_torque_gt_limit")
    if nonfinite_violation: reasons.append("nonfinite_physics_telemetry")
    if summary.get("abort_reason"): reasons.append(f"episode_abort:{summary['abort_reason']}")
    return {
        "human_contact_duration_s": contact_duration,
        "human_comfort_torque_compliance": comfort_ratio,
        "comfort_threshold_ratio_of_actuator_limit": COMFORT_RATIO,
        "comfort_threshold_nm": threshold.tolist(),
        "human_force_threshold_n": HUMAN_FORCE_THRESHOLD_N,
        "max_torque_limit_ratio": float(np.nanmax(torque_ratio)),
        "peak_torque_by_joint_nm": np.nanmax(np.abs(torque), axis=0).tolist() if len(torque) else [None] * 7,
        "p95_torque_nm": float(np.nanpercentile(np.abs(torque), 95)) if len(torque) else None,
        "max_torque_slew_nm_per_s": max_slew,
        "max_penetration_mm": float(np.nanmax(penetration_mm)),
        "machine_safety_violation": bool(reasons),
        "machine_safety_violation_reasons": reasons,
    }


def metric_row(method: str, condition: dict[str, Any], run: Path, metric: Path) -> dict[str, Any]:
    m = read(metric)
    c = comfort_and_safety(run)
    audit = read(run / "AUDIT.json")
    if audit.get("actor_replay_performed") is False or audit.get("common_filter_replay_max_abs") not in (0, 0.0):
        raise RuntimeError(f"replay audit failed: {run}")
    return {
        "method": method,
        "condition": condition["id"],
        "run": str(run),
        "task_success": bool(m["task_success"]),
        "strict_success": bool(m["strict_success"]),
        "completion_time_s": completion_time(run),
        "duration_s": float(m["duration_s"]),
        "peak_torque_nm": float(m["peak_torque_nm"]),
        "comfort": c,
        "metric_sha256": sha(metric),
        "audit_sha256": sha(run / "AUDIT.json"),
        "trace_sha256": sha(run / "rollout.npz"),
        "model_sha256": sha(run / "rollout.mjb"),
        "execution_sha256": sha(run / "execution.json"),
        "chain_sha256": sha(run / "execution_chain.npz"),
        "substep_metrics_sha256": sha(run / "rollout_metrics/substep_metrics.npz"),
        "research_substeps_sha256": sha(run / "research_substeps.npz"),
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    qualified_times = [
        r["completion_time_s"]
        for r in rows
        if r["task_success"] and r["strict_success"] and r["completion_time_s"] is not None
    ]
    t_ref = min(qualified_times) if qualified_times else None
    for r in rows:
        t = r["completion_time_s"]
        r["spt"] = float(t_ref / max(t, t_ref)) if t_ref is not None and r["task_success"] and r["strict_success"] and t is not None else 0.0
    methods = []
    for method in sorted({r["method"] for r in rows}):
        group = [r for r in rows if r["method"] == method]
        contact = [r["comfort"]["human_contact_duration_s"] for r in group]
        compliant = [
            (r["comfort"]["human_comfort_torque_compliance"], r["comfort"]["human_contact_duration_s"])
            for r in group
            if r["comfort"]["human_comfort_torque_compliance"] is not None
        ]
        weighted = sum(v * d for v, d in compliant) / sum(d for _, d in compliant) if compliant and sum(d for _, d in compliant) > 0 else None
        methods.append({
            "method": method,
            "episodes": len(group),
            "task_success": sum(r["task_success"] for r in group),
            "strict_success": sum(r["strict_success"] for r in group),
            "spt_mean": float(np.mean([r["spt"] for r in group])),
            "completion_time_mean_s_task": float(np.mean([r["completion_time_s"] for r in group if r["completion_time_s"] is not None])) if any(r["completion_time_s"] is not None for r in group) else None,
            "peak_torque_mean_nm": float(np.mean([r["peak_torque_nm"] for r in group])),
            "peak_torque_worst_nm": float(np.max([r["peak_torque_nm"] for r in group])),
            "human_comfort_torque_compliance_contact_time_weighted": weighted,
            "human_contact_duration_s_total": float(sum(contact)),
            "machine_safety_violation_rate": float(np.mean([r["comfort"]["machine_safety_violation"] for r in group])),
            "machine_safety_violation_episodes": sum(r["comfort"]["machine_safety_violation"] for r in group),
            "failure_reasons": sorted({reason for r in group for reason in r["comfort"]["machine_safety_violation_reasons"]}),
        })
    return {
        "t_ref_s": float(t_ref) if t_ref is not None else None,
        "t_ref_definition": "minimum sampled final-placement gate crossing time among all Task AND Strict successes in this matrix",
        "t_ref_status": "post_hoc_exploratory_user_requested",
        "spt_formula": "(Task AND Strict) * T_ref / max(T, T_ref); failures are 0",
        "comfort_definition": "dt-weighted fraction of actual human contact substeps with max_j(abs(qfrc_actuator_j)/(0.5*actuator_limit_j)) <= 1",
        "machine_safety_definition": "episode violation if max external/edge penetration >0.2 mm, torque exceeds frozen actuator limit, nonfinite telemetry, or a registered worker abort; torque slew is reported diagnostically because no independent slew limit is registered",
        "methods": methods,
        "rows": rows,
    }


def render(summary: dict[str, Any]) -> str:
    lines = [
        "# Non-RL SPT 指标矩阵（2026-10-25）", "",
        "本报告基于新建物理评估回合；不含 RL。SPT 的 T_ref 按用户要求取本矩阵中所有 Task AND Strict 成功回合的最短采样终态 gate crossing 时间，因此是后验探索性指标，不是独立参考规划器基准。", "",
        f"- T_ref: `{summary['t_ref_s']:.6f} s`" if summary['t_ref_s'] is not None else "- T_ref: `NA`（没有 Task AND Strict 成功回合；所有 SPT=0）", "- 舒适力矩阈值：每关节冻结执行器力矩上限的 0.5 倍；只在人机实际接触子步计分。", "- 机器安全违规：穿透超过 0.2 mm、力矩超过冻结上限或物理遥测非有限值。", "",
        "| 方法 | 回合 | Task | Strict | SPT | 平均完成时间(s) | 峰值力矩(Nm) | 舒适力矩合规率 | 机器安全违规率 |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for m in summary["methods"]:
        def pct(v): return "NA" if v is None else f"{100*v:.2f}%"
        lines.append(f"| {m['method']} | {m['episodes']} | {m['task_success']}/{m['episodes']} | {m['strict_success']}/{m['episodes']} | {m['spt_mean']:.4f} | {m['completion_time_mean_s_task'] if m['completion_time_mean_s_task'] is not None else 'NA'} | {m['peak_torque_mean_nm']:.3f} | {pct(m['human_comfort_torque_compliance_contact_time_weighted'])} | {100*m['machine_safety_violation_rate']:.2f}% |")
    lines += ["", "逐回合结果、失败原因和 hash 见 `REPORT.json`；无人体接触的回合舒适合规率为 NA，不填零。"]
    return "\n".join(lines) + "\n"


def prepare_and_run(args: argparse.Namespace) -> None:
    source_run = args.source_run.resolve()
    root = args.root.resolve()
    resume = False
    if root.exists():
        if not args.resume or not (root / "execution.json").exists():
            raise FileExistsError(root)
        prior = read(root / "execution.json")
        if prior.get("status") != "failed_preserved":
            raise RuntimeError(f"refusing to resume non-failed run: {prior.get('status')}")
        resume = True
    custom = getattr(args, 'model_lock', None)
    if custom and resume:
        raise ValueError('Custom diagnostic resume requires a separately reviewed boundary receipt')
    lock = load_diagnostic_models(custom) if custom else read(source_run / "MODEL_LOCK.json")
    methods = tuple(m['name'] for m in lock['models']) if custom else METHODS
    conditions = read(source_run / "CONDITIONS.json")["conditions"]
    models = {m["name"]: m for m in lock["models"]}
    missing = [name for name in methods if name not in models]
    if missing:
        raise KeyError(f"missing frozen model(s): {missing}")
    if args.dry_run:
        episodes = len(methods)*len(conditions)
        free = shutil.disk_usage(source_run.parent).free
        required = episodes*192*1024**2 + 1024**3
        print(json.dumps({"root": str(root), "episodes": episodes, "methods": methods, "conditions": [c["id"] for c in conditions],
                          "disk_free_bytes":free,"disk_required_bytes":required,"disk_admitted":free>=required}, ensure_ascii=False, indent=2))
        return
    if custom:
        required = len(methods)*len(conditions)*192*1024**2 + 1024**3
        if shutil.disk_usage(root.parent).free < required:
            raise RuntimeError(f'Insufficient disk for complete diagnostic grid; require {required} bytes including reserve')
    if not resume:
        root.mkdir(parents=True, exist_ok=False)
        (root / "evaluation").mkdir()
        (root / "configs").mkdir()
        (root / "checkpoints").mkdir()
        shutil.copy2(source_run / "CONDITIONS.json", root / "CONDITIONS.json")
        shutil.copy2(source_run / "PROTOCOL.json", root / "PARENT_PROTOCOL.json")
        shutil.copy2(source_run / "SOURCE_HASHES.json", root / "PARENT_SOURCE_HASHES.json")
    source = root / "source"
    if not source.exists():
        shutil.copytree(source_run / "source", source)
    selected = []
    for name in methods:
        model = dict(models[name])
        cp = Path(model["checkpoint"])
        local_cp = root / "checkpoints" / (name + cp.suffix)
        shutil.copy2(cp, local_cp)
        if sha(local_cp) != model["checkpoint_sha256"]:
            raise RuntimeError(f"checkpoint hash mismatch: {name}")
        model["checkpoint"] = str(local_cp)
        selected.append(model)
    protocol = {
        "schema": "sii-nonrl-spt-matrix-20261025-v1",
        "created_utc": now(),
        "authorization": "User requested a new non-RL physical comparison under Task/Strict/SPT/torque/comfort/safety metrics",
        "source_run": str(source_run),
        "methods": methods,
        "conditions": [c["id"] for c in conditions],
        "physics_dt": 5e-5,
        "horizon_s": 55.0,
        "server_compute": False,
        "unchanged": ["MJB", "geometry", "Task/Strict gates", "canonical48 actor input", "common action filter", "actuator limits"],
        "spt": {"t_ref_rule": "minimum sampled final-placement gate crossing over Task AND Strict successes in this matrix", "post_hoc": True},
        "comfort": {"ratio_of_actuator_limit": COMFORT_RATIO, "human_force_threshold_n": HUMAN_FORCE_THRESHOLD_N, "denominator": "actual human contact dt only"},
        "machine_safety": {"penetration_limit_mm": PENETRATION_LIMIT_MM, "torque_epsilon": TORQUE_EPSILON},
        "models": selected,
    }
    if custom:
        shutil.copy2(custom, root/'INPUT_MODEL_LOCK.json')
        shutil.copy2(Path(__file__), root/'coordinator.py')
        protocol.update(schema='sii-nonrl-spt-diagnostic-20261026-v1',
                        model_lock_sha256=sha(root/'INPUT_MODEL_LOCK.json'),
                        coordinator_sha256=sha(root/'coordinator.py'),
                        interpretation='Seen 8-condition diagnostic; one seed, not unseen generalization or final superiority',
                        comparison=lock['comparison'])
    if not resume:
        write(root / "REGISTRATION.json", protocol)
    state = read(root / "execution.json") if resume else {"status": "running", "started_utc": now(), "expected": len(methods) * len(conditions), "completed": 0, "rows": [], "results": []}
    state["status"] = "running"
    state["resumed_utc"] = now()
    state.setdefault("rows", [])
    state.setdefault("results", [])
    write(root / "execution.json", state)
    python = args.python or sys.executable
    worker_env = os.environ.copy()
    worker_env.update({"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
                       "MUJOCO_MENAGERIE_PATH": str(args.runtime / "menagerie")})
    rows = list(state["results"])
    completed_names = {r["method"] + "__" + r["condition"] for r in state["rows"] if r.get("returncode") == 0}
    for condition in conditions:
        for model in selected:
            name = model["name"] + "__" + condition["id"]
            if name in completed_names:
                continue
            if custom and shutil.disk_usage(root).free < 1024**3 + 192*1024**2:
                state.update(status='failed_preserved',error='disk guard at safe episode boundary')
                write(root/'execution.json',state)
                raise RuntimeError(state['error'])
            out = root / "evaluation" / name
            config = root / "configs" / (name + ".json")
            write(config, model.get("config", {}))
            command = [python, str(source / "tools/baseline_repair_worker_20261008.py"),
                       "--research-protocol", str(source_run / "PROTOCOL.json"),
                       "--protocol-sha256", read(source_run / "REGISTRATION.json")["protocol_sha256"],
                       "--research-condition", condition["id"], "--phase", "acceptance",
                       "--worker-kind", model["worker_kind"],
                       "--v6-input", str(args.runtime / "v6"),
                       "--reference", str(args.runtime / "v6/esn_original_v2/rollout.json"),
                       "--config", str(config), "--output", str(out), "--contact-audit", "--physics-dt", ".00005",
                       "--checkpoint", model["checkpoint"]]
            row_state = {"method": model["name"], "condition": condition["id"], "command": command, "started_utc": now()}
            state["rows"].append(row_state); write(root / "execution.json", state)
            out.parent.mkdir(parents=True, exist_ok=True)
            log_path = root / (name + ".log")
            if log_path.exists():
                suffix = 1
                while (root / (name + f".retry{suffix}.log")).exists():
                    suffix += 1
                log_path = root / (name + f".retry{suffix}.log")
            with log_path.open("x") as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, env=worker_env,
                                        pass_fds=(args.compute_lock_fd,) if custom else ())
            row_state.update(returncode=result.returncode, ended_utc=now())
            if result.returncode != 0:
                state["status"] = "failed_preserved"; state["error"] = f"{name} rc={result.returncode}"; write(root / "execution.json", state)
                raise RuntimeError(state["error"])
            metric = root / "metrics" / (name + ".json")
            metric.parent.mkdir(exist_ok=True)
            subprocess.run([python, str(source / "tools/paper_metrics_20261002.py"), "--run", str(out), "--output", str(metric)], check=True)
            rows.append(metric_row(model["name"], condition, out, metric))
            state["results"] = rows
            state["completed"] = len(rows); write(root / "execution.json", state)
            partial = aggregate(rows) if any(r["task_success"] and r["strict_success"] and r["completion_time_s"] is not None for r in rows) else None
            write(root / "REPORT.json", {"status": "running", "rows": rows, "summary": partial})
    summary = aggregate(rows)
    report = {"status": "complete", "updated_utc": now(), "registration_sha256": sha(root / "REGISTRATION.json"), "rows": rows, **summary}
    write(root / "REPORT.json", report)
    (root / "REPORT.md").write_text(render(report))
    state.update(status="complete", ended_utc=now(), report_sha256=sha(root / "REPORT.json"))
    write(root / "execution.json", state)
    print(json.dumps({"status": "complete", "root": str(root), "episodes": len(rows), "t_ref_s": summary["t_ref_s"]}, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--python", type=str)
    parser.add_argument("--model-lock", type=Path, help="Frozen learned-model lock for a separate seen diagnostic grid")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true", help="resume a failed-preserved run at a safe boundary")
    args = parser.parse_args()
    if args.model_lock and not args.dry_run:
        cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
        if int((cg/'memory.max').read_text()) > 3*1024**3 or int((cg/'memory.swap.max').read_text()) != 0:
            raise RuntimeError('Diagnostic grid requires <=3 GiB and zero worker swap')
        with (args.source_run.resolve().parent/'.local-rl-compute.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            args.compute_lock_fd = lock.fileno()
            prepare_and_run(args)
    else:
        prepare_and_run(args)


if __name__ == "__main__":
    main()
