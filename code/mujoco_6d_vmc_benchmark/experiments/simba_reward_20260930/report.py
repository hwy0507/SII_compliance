"""Summarize a live or completed paired SimbaV2 campaign without reward ranking."""
from __future__ import annotations
import argparse, csv, datetime, json, math, statistics
from collections import defaultdict
from pathlib import Path

CORE = ("rmse_cm", "peak_torque_nm", "peak_velocity_mps")
GATES = ("strict_success", "task_success", "physical_valid", "placement_complete")
GROUPS = {"office_task": "primary", "metric": "primary", "metric_nosmooth": "secondary_ablation"}

def read(path, warnings):
    path = Path(path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        warnings.append(f"Unreadable {path}: {exc}")
        return None

def lines(path, warnings):
    if not path.exists():
        return
    with path.open() as stream:
        for index, line in enumerate(stream, 1):
            try:
                yield json.loads(line)
            except ValueError:
                warnings.append(f"Ignored malformed/incomplete line {index}: {path}")

def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

def mean(values):
    v = [float(x) for x in values if finite(x)]
    return statistics.mean(v) if v else None

def sd(values):
    v = [float(x) for x in values if finite(x)]
    return statistics.stdev(v) if len(v) > 1 else None

def write_json(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)

def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        if fields:
            writer.writeheader()
            for row in rows:
                writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                                 for k, v in row.items()})

def metrics(row):
    m = row.get("metrics", row)
    rmse = m.get("position_rmse_3d_m")
    return dict(rmse_cm=100 * rmse if finite(rmse) else None,
                peak_torque_nm=m.get("peak_torque_nm", m.get("generalized_actuator_torque_peak_nm")),
                peak_velocity_mps=m.get("peak_velocity_mps", m.get("linear_speed_peak_mps")))

def run_info(root, spec, warnings):
    p = Path(spec.get("path", root / spec["id"]))
    config = read(p / "PROTOCOL.json", warnings) or {}
    progress = read(p / "progress.json", warnings) or {}
    complete = read(p / "COMPLETE.json", warnings) or {}
    failure = read(p / "FAILED.json", warnings) or read(p / "FAILURE.json", warnings)
    mode = "metric_nosmooth" if spec["id"].startswith("metric_nosmooth") else spec.get("mode", config.get("reward", {}).get("mode", "unknown"))
    rows = list(lines(p / "episode_summaries.jsonl", warnings) or [])
    steps = complete.get("steps", progress.get("step", 0))
    substeps, sim_s, logged_controls = 0, 0.0, 0
    for row in lines(p / "control_audit.jsonl", warnings) or []:
        iv = row.get("interval", {})
        substeps += int(iv.get("substeps", 0))
        sim_s += float(iv.get("elapsed_s", 0))
        logged_controls += 1
    curve = []
    for row in rows:
        curve.append(dict(run=spec["id"], group=mode, seed=spec.get("seed"), step=row.get("step"),
                          episode=row.get("episode"), **metrics(row),
                          **{k: row.get(k) for k in GATES},
                          episode_return_diagnostic_only=row.get("episode_return"),
                          abort_reason=row.get("abort_reason"),
                          cumulative_logged_episode_physics_substeps=None))
    tail = rows[-10:]
    diagnostics = dict(last10_complete_episodes=len(tail),
                       last10_task_success_rate=mean([int(x["task_success"]) for x in tail if isinstance(x.get("task_success"), bool)]),
                       last10_strict_success_rate=mean([int(x["strict_success"]) for x in tail if isinstance(x.get("strict_success"), bool)]),
                       last10_rmse_cm=mean([metrics(x)["rmse_cm"] for x in tail]),
                       convergence="not established by this finite-budget experiment")
    return dict(run=spec["id"], group=mode, role=GROUPS.get(mode, "diagnostic"),
                seed=spec.get("seed"), status=complete.get("status", progress.get("status", "not_started")),
                transitions=steps, updates=complete.get("updates", progress.get("updates", 0)),
                episodes=complete.get("episodes", progress.get("episodes", len(rows))),
                elapsed_s=complete.get("elapsed_s", progress.get("elapsed_s")),
                planned_transitions=config.get("total_step_budget"),
                physics_dt=config.get("train_physics_dt"),
                actual_logged_physics_substeps=substeps,
                actual_logged_simulated_seconds=sim_s,
                logged_control_transitions=logged_controls,
                physical_budget_complete=(steps == logged_controls),
                failure=failure, diagnostics=diagnostics, path=str(p)), curve

def episode_rows(root, run, partition, selections, steps, warnings):
    directory = root / partition / run["run"]
    source = directory / "SUMMARY.json"
    raw = read(source, warnings)
    reused = False
    if raw is None and partition == "fixed_final":
        selection = selections.get(run["run"], {})
        chosen = selection.get("selected_checkpoint", "")
        if Path(chosen).name == f"checkpoint_step_{steps:07d}":
            source = root / "test" / run["run"] / "SUMMARY.json"
            raw = read(source, warnings)
            reused = raw is not None
    if raw is None:
        return [], dict(run=run["run"], partition=partition, status="pending_or_missing", source=str(source))
    protocol = raw.get("protocol", {})
    rows = []
    for index, row in enumerate(raw.get("rows", [])):
        rows.append(dict(run=run["run"], group=run["group"], role=run["role"], seed=run["seed"],
            partition=partition, evaluation_status=raw.get("status", "unknown"),
            case_index=row.get("case_index", index), **metrics(row),
            **{k: row.get(k) for k in GATES},
            peak_torque_by_joint_nm=row.get("peak_torque_by_joint_nm"),
            contact_coverage_valid=row.get("contact_coverage_valid"),
            substep_samples=row.get("substep_samples"),
            condition=row.get("condition"), abort_reason=row.get("abort_reason"),
            checkpoint=protocol.get("checkpoint"), manifest_sha256=protocol.get("manifest_sha256"),
            duration_s=protocol.get("duration_s"), physics_dt=(row.get("condition") or {}).get("physics_dt"),
            reused_selected_as_fixed_final=reused,
            source=str(source)))
    return rows, dict(run=run["run"], partition=partition, status=raw.get("status", "unknown"),
                      completed_episodes=len(rows), source=str(source))

def by_seed(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["partition"], row["group"], row["seed"])].append(row)
    result = []
    for (partition, group, seed), block in sorted(grouped.items()):
        result.append(dict(partition=partition, group=group, role=GROUPS.get(group, "diagnostic"),
            seed=seed, episodes=len(block),
            evaluation_complete=all(x["evaluation_status"] == "complete" for x in block),
            **{k: mean([x[k] for x in block]) for k in CORE},
            **{k+"_rate": mean([int(x[k]) for x in block if isinstance(x[k], bool)]) for k in GATES},
            worst_peak_torque_nm=max((x["peak_torque_nm"] for x in block if finite(x["peak_torque_nm"])), default=None),
            worst_peak_velocity_mps=max((x["peak_velocity_mps"] for x in block if finite(x["peak_velocity_mps"])), default=None),
            physical_invalid_episodes=sum(x["physical_valid"] is False for x in block)))
    return result

def across_seeds(rows):
    grouped = defaultdict(list)
    for row in rows:
        if row["evaluation_complete"]:
            grouped[(row["partition"], row["group"])].append(row)
    result = []
    for (partition, group), block in sorted(grouped.items()):
        values = dict(partition=partition, group=group, role=GROUPS.get(group, "diagnostic"),
                      independent_training_seeds=len(block), seeds=[x["seed"] for x in block],
                      episodes_per_seed=[x["episodes"] for x in block],
                      statistical_unit="independent training seed; equal weight per seed",
                      confidence_interval="not reported: n<=3 is exploratory; seed SD is descriptive")
        for key in (*CORE, *(x+"_rate" for x in GATES)):
            values[key+"_mean"] = mean([x[key] for x in block])
            values[key+"_seed_sd"] = sd([x[key] for x in block])
        result.append(values)
    return result

def number(value, precision=3):
    return f"{value:.{precision}f}" if finite(value) else "—"

def report(root, out):
    warnings = []
    protocol = read(root / "CAMPAIGN_PROTOCOL.json", warnings) or read(root / "PROTOCOL.json", warnings) or {}
    state = read(root / "CAMPAIGN_STATE.json", warnings) or {}
    statuses = {name: read(root / (name + ".json"), warnings)
                for name in ("TRAIN_STATUS", "VALIDATION_STATUS", "TEST_STATUS", "COMPLETE")}
    selections = {r["id"]: r for r in (read(root / "SELECTIONS.json", warnings) or [])}
    specs = protocol.get("runs", [])
    if not specs:
        warnings.append("Campaign run manifest missing; no synthetic results inferred.")
    training, curves, episodes, pending = [], [], [], []
    for spec in specs:
        row, curve = run_info(root, spec, warnings)
        training.append(row);curves.extend(curve)
        result = next((x for x in (statuses["TRAIN_STATUS"] or []) if x.get("id") == spec["id"]), None)
        if result:
            row["process_returncode"] = result.get("returncode")
            if result.get("returncode") != 0:
                row["status"] = "process_failed"
                warnings.append("Training process failed: {}; log={}".format(spec["id"], result.get("log")))
        for partition in ("test", "fixed_final"):
            if partition == "fixed_final" and row["role"] != "primary":
                continue
            ev, status = episode_rows(root, row, partition, selections, int(protocol.get("steps", 0)), warnings)
            episodes.extend(ev);pending.append(status)
    for partition in ("test", "fixed_final"):
        block = [x for x in episodes if x["partition"] == partition]
        for key in ("manifest_sha256", "duration_s", "physics_dt"):
            observed = {x[key] for x in block if x[key] is not None}
            if len(observed) > 1:
                warnings.append(f"Protocol mismatch in {partition}: {key} has {observed}; cross-method ranking is not valid.")
    seeds = by_seed(episodes)
    groups = across_seeds(seeds)
    budget = []
    for group in GROUPS:
        runs = [x for x in training if x["group"] == group]
        budget.append(dict(group=group, runs=len(runs),
                           transitions=sum(x["transitions"] for x in runs),
                           updates=sum(x["updates"] for x in runs),
                           physics_substeps=sum(x["actual_logged_physics_substeps"] for x in runs),
                           simulated_seconds=sum(x["actual_logged_simulated_seconds"] for x in runs),
                           per_run_wall_s=[x["elapsed_s"] for x in runs]))
    limitations = [
        "This is Office simulation, not real FR3 hardware validation or a blind previously unseen benchmark.",
        "RMSE uses current task-stage waypoint and all physical substeps; no post-contact-only metric is silently substituted.",
        "Means include failures and physically invalid episodes; physical validity, task and strict success remain separate.",
        "Peak torque is actual qfrc_actuator Nm; group value is mean of per-episode maxima, not one global maximum.",
        "Peak velocity is a maximum, not P95. Lower speed/torque alone can indicate stalling rather than better control.",
        "Different reward totals are not comparable performance scores; never rank reward groups by total return.",
        "Training dt and formal evaluation dt may differ; source/model/fixture hashes and both timesteps must be retained.",
        "Fixed-budget and validation-selected checkpoint results are separate. Missing fixed-final results are not replaced by arbitrary selected checkpoints.",
        "Unequal achieved transitions, update counts or physical substep budgets limit causal comparison; report actual budgets.",
        "Zero successes or flat short learning curves do not prove inherent algorithm weakness or convergence.",
        "Three or fewer training seeds allow descriptive uncertainty only; episodes are not independent learner seeds.",
    ]
    payload = dict(generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        campaign=str(root),phase=state.get("phase", "unknown"),protocol=protocol,
        training=training,budgets=budget,evaluation_status=pending,
        per_seed=seeds,across_seed=groups,status_files=statuses,warnings=warnings,
        limitations=limitations,
        completion="complete" if statuses["COMPLETE"] else "in_progress_or_incomplete")
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "RESULTS.latest.json", payload)
    for name, rows in (("training",training),("learning_curves",curves),("episodes",episodes),
                       ("per_seed",seeds),("across_seed",groups),("budgets",budget)):
        write_csv(out / (name + ".csv"), rows)
    text = ["# SimbaV2 Office 奖励对照：实时报告", "",
            f"生成时间：{payload['generated_at']}；阶段：{payload['phase']}；状态：{payload['completion']}。",
            "", f"服务器目录：`{root}`", "",
            "主对照为 office_task 与 metric；metric_nosmooth 是平滑项消融。"
            "以下为仿真开发评估，不宣称真实机器人部署效果。", "",
            "## 实际训练预算", "",
            "| 方法 | Seed | 状态 | transitions | updates | 已记录物理子步 | wall h |",
            "|---|---:|---|---:|---:|---:|---:|"]
    for r in training:
        text.append(f"| {r['group']} | {r['seed']} | {r['status']} | {r['transitions']} | {r['updates']} | {r['actual_logged_physics_substeps']} | {number(r['elapsed_s']/3600 if finite(r['elapsed_s']) else None,2)} |")
    text += ["", "## 统一评测：按训练 seed 汇总", "",
             "每个 seed 先对相同评测条件求均值，再对独立训练 seed 等权统计。"
             "RMSE 单位 cm；力矩为每回合峰值实际 N·m；速度为每回合峰值 m/s。",
             "", "| 评测 | 方法 | Seed | episodes | 完整 | RMSE cm | 峰值力矩 | 峰值速度 | strict | task | physical |",
             "|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|"]
    for r in seeds:
        text.append(f"| {r['partition']} | {r['group']} | {r['seed']} | {r['episodes']} | {r['evaluation_complete']} | {number(r['rmse_cm'])} | {number(r['peak_torque_nm'])} | {number(r['peak_velocity_mps'],4)} | {number(r['strict_success_rate'])} | {number(r['task_success_rate'])} | {number(r['physical_valid_rate'])} |")
    if not seeds:
        text += ["", "评测尚无可读取结果；此处没有以训练 reward 或旧协议结果填充。"]
    text += ["", "## Seed 均值 ± 样本标准差", "",
             "| 评测 | 方法 | 独立 seeds | RMSE cm | 峰值力矩 N·m | 峰值速度 m/s |",
             "|---|---|---:|---:|---:|---:|"]
    for r in groups:
        fmt=lambda k: number(r[k+"_mean"],4)+" ± "+number(r[k+"_seed_sd"],4)
        text.append(f"| {r['partition']} | {r['group']} | {r['independent_training_seeds']} | {fmt('rmse_cm')} | {fmt('peak_torque_nm')} | {fmt('peak_velocity_mps')} |")
    text += ["", "未完成的评测不进入上述跨 seed 统计；n≤3 不给出夸大的显著性或置信区间结论。", "",
             "## 待完成与异常", ""]
    text.extend(f"- {r['run']} / {r['partition']}: {r['status']} ({r['source']})"
                for r in pending if r["status"] != "complete")
    text.extend("- "+w for w in warnings)
    text += ["", "## 解释边界", ""]
    text.extend("- "+x for x in limitations)
    text += ["", "曲线数据在 learning_curves.csv；逐评测回合 episodes.csv；"
             "逐训练 seed per_seed.csv；跨 seed across_seed.csv；实际预算 budgets.csv。"
             "恢复/停滞需结合阶段、完整任务成功率和录像诊断，不能只看总 reward。", ""]
    (out / "REPORT.latest.md").write_text("\n".join(text))
    return payload

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--campaign", type=Path, required=True)
    p.add_argument("--output", type=Path)
    a=p.parse_args()
    result=report(a.campaign.resolve(), (a.output or a.campaign/"report").resolve())
    print(json.dumps(dict(phase=result["phase"],completed_seed_evaluations=len(result["per_seed"]),
                         report=str((a.output or a.campaign/"report")/"REPORT.latest.md"))))
