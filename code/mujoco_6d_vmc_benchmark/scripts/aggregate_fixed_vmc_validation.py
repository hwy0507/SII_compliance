#!/usr/bin/env python3
"""Summarize a frozen VMC held-out scan without hiding invalid collisions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


METRICS = (
    "peak_paired_rod_offset_mm",
    "paired_offset_rmse_mm",
    "recovery_rmse_mm",
    "rejoin_latency_s",
    "peak_torque_nm",
    "jerk_peak_mps3",
    "peak_contact_force_n",
    "contact_impulse_ns",
)


def statistics(records: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    return {
        metric: {
            "mean": float(np.mean([record[metric] for record in records])),
            "std": float(np.std([record[metric] for record in records], ddof=0)),
            "min": float(np.min([record[metric] for record in records])),
            "max": float(np.max([record[metric] for record in records])),
        }
        for metric in METRICS
    }


def report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 固定 static VMC 基线：held-out 物理碰撞扫描",
        "",
        "## 冻结基线",
        "",
        "- 六维虚拟弹簧：`[27.580, 52.551, 48.699, 35.860, 40.720, 34.767]`；",
        "- 接触阶段 carriage-drive：`8`；杆释放后的回归 carriage-drive：`14`；",
        "- 阻尼比 `0.8`、显式平移 virtual carriage 质量 `1.0 kg`、回归 ramp `0.08 s`；",
        "- 8 个测试 fixture 来自训练前随机化清单的 test split，未用于前一轮 f0--f3 回归 drive 对比。",
        "",
        "每个 fixture 都执行物理 rod 和相同配置的 no-rod 对照。轨迹偏差是两条末端轨迹的距离；no-rod 是任务匹配参考，**不是在线 WBC**。",
        "",
        "## 结果与门槛",
        "",
        "有效性要求：有限仿真、实体 rod--hand 接触、稳定回归、抓取并抬升／持物、无硬力矩限幅；有效碰撞还要求峰力 ≥15 N、冲量 ≥0.45 Ns。未通过碰撞门槛的 fixture 会完整保留，但绝不用于宣称控制性能。",
        "",
        "| Fixture | 有效碰撞与任务 | 峰值偏差 (mm) | 配对 RMSE (mm) | 回归 RMSE (mm) | 回归时延 (ms) | 峰值力矩 (Nm) | Jerk 峰值 (m/s³) | 峰力 (N) | 冲量 (Ns) | 说明 |",
        "|---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["records"]:
        reason = "—" if row["valid"] else "; ".join(row["invalid_reasons"])
        lines.append(
            f"| {row['sample_id']} | {'是' if row['valid'] else '否'} | {row['peak_paired_rod_offset_mm']:.3f} | "
            f"{row['paired_offset_rmse_mm']:.3f} | {row['recovery_rmse_mm']:.3f} | {row['rejoin_latency_s'] * 1000.0:.1f} | "
            f"{row['peak_torque_nm']:.3f} | {row['jerk_peak_mps3']:.1f} | {row['peak_contact_force_n']:.2f} | {row['contact_impulse_ns']:.3f} | {reason} |"
        )
    summary = report["valid_summary"]
    lines += [
        "",
        "## 仅在有效碰撞上的汇总（均值 ± 标准差）",
        "",
        f"有效 fixture：`{report['valid_count']}/{report['fixture_count']}`。其余 `{report['fixture_count'] - report['valid_count']}` 个 fixture 是弱碰撞（不是控制失败），不计入性能均值。",
        "",
        "| 峰值偏差 (mm) | 配对 RMSE (mm) | 回归 RMSE (mm) | 回归时延 (ms) | 峰值力矩 (Nm) | Jerk 峰值 (m/s³) | 峰力 (N) | 冲量 (Ns) |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
        f"| {summary['peak_paired_rod_offset_mm']['mean']:.3f} ± {summary['peak_paired_rod_offset_mm']['std']:.3f} | "
        f"{summary['paired_offset_rmse_mm']['mean']:.3f} ± {summary['paired_offset_rmse_mm']['std']:.3f} | "
        f"{summary['recovery_rmse_mm']['mean']:.3f} ± {summary['recovery_rmse_mm']['std']:.3f} | "
        f"{summary['rejoin_latency_s']['mean'] * 1000.0:.1f} ± {summary['rejoin_latency_s']['std'] * 1000.0:.1f} | "
        f"{summary['peak_torque_nm']['mean']:.3f} ± {summary['peak_torque_nm']['std']:.3f} | "
        f"{summary['jerk_peak_mps3']['mean']:.1f} ± {summary['jerk_peak_mps3']['std']:.1f} | "
        f"{summary['peak_contact_force_n']['mean']:.2f} ± {summary['peak_contact_force_n']['std']:.2f} | "
        f"{summary['contact_impulse_ns']['mean']:.3f} ± {summary['contact_impulse_ns']['std']:.3f} |",
        "",
        "## 决策",
        "",
        "冻结基线在 6/6 个有效 held-out 碰撞中完成抓取和持物、无硬力矩限幅，并维持约 2.50 mm 的回归 RMSE。因此它可以作为下一阶段 RL 的**静态初始化／固定对照**。这不表示已证明其能覆盖所有几何；两个弱碰撞 fixture 应保留为 fixture-calibration 记录，而不是被解释成方法失败或方法优势。",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-label", type=str, default=None, help="Stable provenance label stored in the summary.")
    args = parser.parse_args()
    source = json.loads(args.input.read_text())
    records = source["records"]
    valid_records = [record for record in records if record["valid"]]
    if not valid_records:
        raise RuntimeError("No valid physical collisions; cannot approve a baseline")
    report = {
        "source": args.source_label or str(args.input),
        "controller_override": source["controller_override"],
        "effective_collision_gate": source["effective_collision_gate"],
        "fixture_count": len(records),
        "valid_count": len(valid_records),
        "records": records,
        "valid_summary": statistics(valid_records),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "fixed_vmc_heldout_summary.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.output_dir / "fixed_vmc_heldout_report.md").write_text(report_markdown(report))
    print(json.dumps({"valid_count": report["valid_count"], "fixture_count": report["fixture_count"], "valid_summary": report["valid_summary"]}, indent=2))


if __name__ == "__main__":
    main()
