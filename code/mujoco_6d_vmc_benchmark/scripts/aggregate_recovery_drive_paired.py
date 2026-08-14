#!/usr/bin/env python3
"""Aggregate strict rod/no-rod paired evaluations of VMC return-drive settings.

Each fixture must contain the exact same controller configuration twice: a
physical rod perturbation and a rod-disabled task run.  The latter is used as
the task-matched reference; it is deliberately not described as online WBC.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


SUMMARY_GLOB = "rod_perturbation_*_summary.json"
TRACE_GLOB = "rod_perturbation_*_trace.npz"
METRICS = (
    "peak_paired_offset_mm",
    "paired_offset_rmse_mm",
    "recovery_rmse_mm",
    "rejoin_latency_ms",
    "peak_torque_nm",
    "jerk_peak_mps3",
)


def load_one(path: Path, pattern: str) -> Path:
    matches = sorted(path.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {pattern} in {path}, found {len(matches)}")
    return matches[0]


def mean_std(values: list[float]) -> dict[str, float]:
    vector = np.asarray(values, dtype=float)
    return {"mean": float(np.mean(vector)), "std": float(np.std(vector, ddof=0))}


def valid(summary: dict[str, Any], require_contact: bool) -> tuple[bool, list[str]]:
    task = summary["task_validity"]
    failures: list[str] = []
    for key in ("simulation_finite", "target_lifted_after_recovery", "target_held_at_end"):
        if not task[key]:
            failures.append(key)
    if require_contact and not task["rod_hand_contact_observed"]:
        failures.append("missing_rod_hand_contact")
    if require_contact and summary["phase_analysis"]["rejoin_time_s"] is None:
        failures.append("no_stable_rejoin")
    if summary["torque"]["hard_limit_fraction"] != 0.0:
        failures.append("hard_torque_limit")
    if require_contact:
        diagnostics = summary["rod_diagnostics"]
        if diagnostics["peak_contact_force_n"] < 15.0:
            failures.append("ineffective_collision_peak_force")
        if diagnostics["contact_impulse_ns"] < 0.45:
            failures.append("ineffective_collision_impulse")
    return not failures, failures


def paired_metrics(rod_trace: Path, no_rod_trace: Path) -> dict[str, float]:
    with np.load(rod_trace) as rod, np.load(no_rod_trace) as no_rod:
        if rod["time"].shape != no_rod["time"].shape or not np.allclose(rod["time"], no_rod["time"]):
            raise RuntimeError("Rod/no-rod traces do not share the same time grid")
        offset = np.linalg.norm(rod["ee_position"] - no_rod["ee_position"], axis=1)
    return {
        "peak_paired_offset_mm": float(np.max(offset) * 1000.0),
        "paired_offset_rmse_mm": float(np.sqrt(np.mean(offset**2)) * 1000.0),
    }


def collect(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    protocol: dict[str, Any] | None = None
    for fixture_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        for drive_dir in sorted(path for path in fixture_dir.iterdir() if path.is_dir()):
            try:
                drive = float(drive_dir.name.removeprefix("d"))
            except ValueError as exc:
                raise RuntimeError(f"Drive directory must be named d<value>: {drive_dir}") from exc
            rod_dir, no_rod_dir = drive_dir / "rod", drive_dir / "no_rod"
            rod_summary = json.loads(load_one(rod_dir, SUMMARY_GLOB).read_text())
            no_rod_summary = json.loads(load_one(no_rod_dir, SUMMARY_GLOB).read_text())
            if protocol is None:
                protocol = json.loads((rod_dir / "evaluation_matrix.json").read_text())["protocol"]
            rod_ok, rod_failures = valid(rod_summary, require_contact=True)
            no_rod_ok, no_rod_failures = valid(no_rod_summary, require_contact=False)
            metrics = paired_metrics(load_one(rod_dir, TRACE_GLOB), load_one(no_rod_dir, TRACE_GLOB))
            phase = rod_summary["phase_analysis"]
            diagnostics = rod_summary["rod_diagnostics"]
            metrics.update({
                "recovery_rmse_mm": rod_summary["tracking"]["recovery_position_rmse_m"] * 1000.0,
                "rejoin_latency_ms": phase["release_to_rejoin_latency_s"] * 1000.0,
                "peak_torque_nm": rod_summary["torque"]["applied_peak_nm"],
                "jerk_peak_mps3": rod_summary["motion"]["jerk_peak_mps3"],
                "peak_force_n": diagnostics["peak_contact_force_n"],
                "impulse_ns": diagnostics["contact_impulse_ns"],
            })
            records.append({
                "fixture": fixture_dir.name,
                "recovery_drive_scale": drive,
                "valid": rod_ok and no_rod_ok,
                "invalid_reasons": rod_failures + [f"no_rod:{item}" for item in no_rod_failures],
                "fixture_parameters": {
                    "rod_stroke_m": rod_summary["rod_motion"]["stroke_m"],
                    "rod_height_m": rod_summary["rod_motion"]["height_m"],
                    "rod_start_time_s": rod_summary["rod_motion"]["start_time_s"],
                },
                **metrics,
            })
    if not records or protocol is None:
        raise RuntimeError(f"No paired records found under {root}")
    return records, protocol


def make_report(records: list[dict[str, Any]], protocol: dict[str, Any]) -> dict[str, Any]:
    drives = sorted({record["recovery_drive_scale"] for record in records})
    fixtures = sorted({record["fixture"] for record in records})
    by_drive: dict[str, Any] = {}
    for drive in drives:
        subset = [record for record in records if record["recovery_drive_scale"] == drive]
        by_drive[str(int(drive) if drive.is_integer() else drive)] = {
            "fixture_count": len(subset),
            "valid_count": sum(record["valid"] for record in subset),
            "metrics": {name: mean_std([record[name] for record in subset]) for name in METRICS},
            "collision": {
                "peak_force_n": mean_std([record["peak_force_n"] for record in subset]),
                "impulse_ns": mean_std([record["impulse_ns"] for record in subset]),
            },
        }
    deltas: list[dict[str, Any]] = []
    if len(drives) == 2:
        low, high = drives
        low_records = {record["fixture"]: record for record in records if record["recovery_drive_scale"] == low}
        high_records = {record["fixture"]: record for record in records if record["recovery_drive_scale"] == high}
        for fixture in fixtures:
            before, after = low_records[fixture], high_records[fixture]
            deltas.append({
                "fixture": fixture,
                "all_valid": before["valid"] and after["valid"],
                **{name: after[name] - before[name] for name in METRICS},
            })
    return {
        "scope": {
            "description": "Strict physical-rod versus matched rod-disabled paired scan of static six-spring VMC return-drive scale.",
            "reference_definition": "The paired rod-disabled task rollout, not an online WBC controller.",
            "effective_collision_gate": {"minimum_peak_force_n": 15.0, "minimum_impulse_ns": 0.45},
        },
        "protocol": {
            "controller_mode": protocol["controller_mode"],
            "kappa_vector": protocol["kappa_vector"],
            "damping_ratio": protocol["damping_ratio"],
            "contact_carriage_drive_scale": protocol["carriage_drive_scale"],
            "recovery_ramp_s": protocol["recovery_ramp"],
            "explicit_translational_carriage": protocol["explicit_translational_carriage"],
            "carriage_mass_kg": protocol["carriage_mass_kg"],
        },
        "records": records,
        "by_drive": by_drive,
        "paired_deltas_high_minus_low": deltas,
    }


def markdown(report: dict[str, Any]) -> str:
    drives = list(report["by_drive"])
    rows = report["records"]
    lines = [
        "# 静态六弹簧 VMC：回归 carriage-drive 严格配对扫描",
        "",
        "## 结论边界",
        "",
        "这是静态 six-kappa VMC 的物理 MuJoCo 实验，比较杆释放后 `recovery carriage-drive scale=8` 与 `14`。每个条件均有同一任务、同一参考、同一控制器配置的 rod/no-rod 配对运行；偏差定义为两条末端轨迹的欧氏距离。该 no-rod 轨迹是任务匹配参考，**不是在线 WBC 基线**。",
        "",
        "有效碰撞门槛为峰值接触力 ≥15 N 且冲量 ≥0.45 Ns；任务有效性要求有限仿真、接触/回归、完成抓取与抬升、末端持物，并且无硬力矩限幅。",
        "",
        "## 每个 fixture 的结果",
        "",
        "| Fixture | drive | 有效 | 峰值配对偏差 (mm) | 配对 RMSE (mm) | 回归 RMSE (mm) | 回归时延 (ms) | 峰值力矩 (Nm) | Jerk 峰值 (m/s³) | 峰值力 (N) | 冲量 (Ns) |",
        "|---|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['fixture']} | {row['recovery_drive_scale']:.0f} | {'是' if row['valid'] else '否'} | "
            f"{row['peak_paired_offset_mm']:.3f} | {row['paired_offset_rmse_mm']:.3f} | {row['recovery_rmse_mm']:.3f} | "
            f"{row['rejoin_latency_ms']:.1f} | {row['peak_torque_nm']:.3f} | {row['jerk_peak_mps3']:.1f} | "
            f"{row['peak_force_n']:.2f} | {row['impulse_ns']:.3f} |"
        )
    lines += ["", "## 按 drive 汇总（均值 ± 标准差）", "", "| drive | 有效 fixtures | 峰值偏差 (mm) | 配对 RMSE (mm) | 回归 RMSE (mm) | 回归时延 (ms) | 峰值力矩 (Nm) | Jerk 峰值 (m/s³) |", "|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for drive, group in report["by_drive"].items():
        metric = group["metrics"]
        def f(name: str) -> str:
            return f"{metric[name]['mean']:.3f} ± {metric[name]['std']:.3f}"
        lines.append(f"| {drive} | {group['valid_count']}/{group['fixture_count']} | {f('peak_paired_offset_mm')} | {f('paired_offset_rmse_mm')} | {f('recovery_rmse_mm')} | {f('rejoin_latency_ms')} | {f('peak_torque_nm')} | {f('jerk_peak_mps3')} |")
    if report["paired_deltas_high_minus_low"]:
        lines += ["", "## 同 fixture 差值（drive 14 − drive 8）", "", "负值表示该指标降低。", "", "| Fixture | 全部有效 | 峰值偏差 Δ (mm) | 配对 RMSE Δ (mm) | 回归 RMSE Δ (mm) | 回归时延 Δ (ms) | 峰值力矩 Δ (Nm) | Jerk Δ (m/s³) |", "|---|:---:|---:|---:|---:|---:|---:|---:|"]
        for delta in report["paired_deltas_high_minus_low"]:
            lines.append(f"| {delta['fixture']} | {'是' if delta['all_valid'] else '否'} | {delta['peak_paired_offset_mm']:.3f} | {delta['paired_offset_rmse_mm']:.3f} | {delta['recovery_rmse_mm']:.3f} | {delta['rejoin_latency_ms']:.1f} | {delta['peak_torque_nm']:.3f} | {delta['jerk_peak_mps3']:.1f} |")
    lines += ["", "## 可解释性", "", "六个虚拟弹簧仍是 `[x, y, z, roll, pitch, yaw]` 六个通道，扫描的量不是“第七根弹簧”，而是接触释放后 virtual carriage 返回名义轨迹的驱动增益。若高 drive 在全部有效 fixture 中降低回归误差且不增加力矩/jerk，才能将其作为下一阶段对照的静态回归机制。这个扫描本身不构成 RL 成果，也不代表实机结论。", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    records, protocol = collect(args.input_root)
    report = make_report(records, protocol)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "recovery_drive_paired_summary.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.output_dir / "recovery_drive_paired_report.md").write_text(markdown(report))
    print(json.dumps(report["by_drive"], indent=2))


if __name__ == "__main__":
    main()
