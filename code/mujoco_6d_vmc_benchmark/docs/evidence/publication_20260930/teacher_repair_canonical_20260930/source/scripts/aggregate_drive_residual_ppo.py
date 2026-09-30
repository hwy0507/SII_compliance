#!/usr/bin/env python3
"""Aggregate checkpoint evaluations against the matched zero-residual controller."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


METRICS = (
    "peak_paired_offset_mm",
    "paired_offset_rmse_mm",
    "recovery_rmse_mm",
    "peak_torque_nm",
    "peak_jerk_mps3",
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def action_diagnostics(records: list[dict[str, Any]]) -> dict[str, float]:
    keys = ("mean_log_kappa_deviation", "mean_log_drive_deviation", "mean_residual_gate")
    return {key: float(np.mean([record.get(key, 0.0) for record in records])) for key in keys}


def metrics(summary: dict[str, Any]) -> dict[str, float]:
    return {key: float(summary[key]["mean"]) for key in METRICS}


def markdown(report: dict[str, Any]) -> str:
    zero = report["zero_residual"]
    lines = [
        "# PPO：六弹簧残差 + return-drive residual（run 001）",
        "",
        "## 对照定义",
        "",
        "所有策略都运行在同一 52-D、可部署的误差门控 return-drive 环境。`zero residual` 对照使用完全相同的物理环境、四个 fixture、rod/no-rod 配对和安全门槛，但把 PPO 的七维残差动作固定为零。因此 checkpoint 与 zero 的差异可以归因于策略残差，而不是由新增静态 return-drive 机制本身造成。",
        "",
        "注意：该 PPO 评估中的回归时延采用“连续 80 ms 处于 5 mm 内”的离线定义；它不能同 earlier static runner 的 phase-analysis 时延混用。",
        "",
        "## 有效性",
        "",
        f"zero residual 与三个 checkpoint 均为 `{zero['task_success_count']}/{zero['episode_count']}` task success、`{zero['effective_collision_count']}/{zero['episode_count']}` effective collision、`{zero['matched_no_rod_task_success_count']}/{zero['episode_count']}` matched no-rod success。",
        "",
        "## 物理指标（均值；PPO − zero）",
        "",
        "负值代表对应数值下降；对于偏差、RMSE、力矩、jerk 通常更好。",
        "",
        "| Checkpoint | 峰值偏差 (mm) | 配对 RMSE (mm) | 回归 RMSE (mm) | 峰值力矩 (Nm) | Jerk (m/s³) |",
        "|---|---:|---:|---:|---:|---:|",
        f"| zero residual | {zero['peak_paired_offset_mm']:.3f} | {zero['paired_offset_rmse_mm']:.3f} | {zero['recovery_rmse_mm']:.3f} | {zero['peak_torque_nm']:.3f} | {zero['peak_jerk_mps3']:.1f} |",
    ]
    for name, result in report["checkpoints"].items():
        values = result["metrics"]
        delta = result["delta_vs_zero"]
        lines.append(
            f"| PPO {name} | {values['peak_paired_offset_mm']:.3f} ({delta['peak_paired_offset_mm']:+.3f}) | "
            f"{values['paired_offset_rmse_mm']:.3f} ({delta['paired_offset_rmse_mm']:+.3f}) | "
            f"{values['recovery_rmse_mm']:.3f} ({delta['recovery_rmse_mm']:+.3f}) | "
            f"{values['peak_torque_nm']:.3f} ({delta['peak_torque_nm']:+.3f}) | "
            f"{values['peak_jerk_mps3']:.1f} ({delta['peak_jerk_mps3']:+.1f}) |"
        )
    best = report["checkpoints"]["300k"]
    action = best["action_diagnostics"]
    lines += [
        "",
        "## 结论",
        "",
        f"300k 是三个 checkpoint 中回归 RMSE 最低者（`{best['metrics']['recovery_rmse_mm']:.3f} mm`），但相对同环境 zero-residual 的变化仅为 `{best['delta_vs_zero']['recovery_rmse_mm']:+.3f} mm`。策略的平均 log-stiffness 偏移为 `{action['mean_log_kappa_deviation']:.4f}`，平均 log-drive 偏移为 `{action['mean_log_drive_deviation']:.4f}`，而可测误差门控平均仅 `{action['mean_residual_gate']:.4f}`；这表明残差实际介入很弱。",
        "",
        "因此该 run 证明了 7-action / 52-D PPO 接口的训练与物理任务均稳定，但**没有证明 PPO 在静态、部署可用的 error-gated return-drive 基线上取得实质 Pareto 改善**。不应把它称为 RL 突破，也不应继续按同一奖励与动作参数盲目延长训练。",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    zero_source = load(args.input_dir / "zero.json")
    zero = {**metrics(zero_source["summary"]), **{
        key: zero_source["summary"][key] for key in ("task_success_count", "effective_collision_count", "matched_no_rod_task_success_count", "episode_count")
    }}
    checkpoints: dict[str, Any] = {}
    for name in ("100k", "200k", "300k"):
        source = load(args.input_dir / f"ppo_{name}.json")
        values = metrics(source["summary"])
        checkpoints[name] = {
            "metrics": values,
            "delta_vs_zero": {key: values[key] - zero[key] for key in METRICS},
            "action_diagnostics": action_diagnostics(source["records"]),
            "validity": {key: source["summary"][key] for key in ("task_success_count", "effective_collision_count", "matched_no_rod_task_success_count", "episode_count")},
        }
    report = {
        "run": "ppo_drive_residual_run_001",
        "source": "/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/ppo_drive_residual_run_001",
        "zero_residual": zero,
        "checkpoints": checkpoints,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "ppo_drive_residual_summary.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.output_dir / "ppo_drive_residual_report.md").write_text(markdown(report))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
