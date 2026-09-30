"""Report matched development rollouts without hiding failed episodes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def summarize(result: dict, protocol: dict) -> dict:
    methods = ["vmc", "impedance", "admittance", *protocol["models"]]
    expected = {(method, f["seed"]) for method in methods for f in protocol["fixtures"]}
    seen = set()
    summary = {}
    records = result["rows"]
    for row in records:
        key = (row["method"], row["fixture"]["seed"])
        if key in seen or key not in expected:
            raise ValueError(f"Duplicate or unexpected rollout: {key}")
        seen.add(key)
        fixture = next(f for f in protocol["fixtures"] if f["seed"] == key[1])
        if row["fixture"] != fixture:
            raise ValueError(f"Mismatched physical fixture: {key}")
    if seen != expected:
        raise ValueError(f"Incomplete matrix: missing {sorted(expected - seen)}")
    for method in methods:
        rows = [r for r in records if r["method"] == method]
        completed = [r for r in rows if "execution_error" not in r]
        metrics = {}
        for key in ("tracking_rmse_3d_m", "control_step_applied_torque_peak_nm",
                    "speed_peak_25hz_mps", "speed_p95_25hz_mps", "max_penetration_mm"):
            values = []
            for row in completed:
                # The first frozen runner used a misleading field name. This
                # alias only corrects the name; the original value is retained.
                field = key
                if field not in row and key == "control_step_applied_torque_peak_nm":
                    field = "physics_peak_motor_torque_nm"
                values.append(float(row[field]))
            if not np.isfinite(values).all():
                raise ValueError(f"Nonfinite metric in {method}/{key}")
            metrics[key] = dict(mean=float(np.mean(values)),
                                std=float(np.std(values, ddof=1)) if len(values) > 1 else None,
                                worst=float(max(values))) if values else None
        summary[method] = dict(planned=len(rows), completed=len(completed),
                               task_success=sum(r["task_success"] for r in completed),
                               panel_gate_success=sum(r["strict_success"] for r in completed),
                               no_rod_contact=sum(r["rod_contact_s"] <= 0 for r in completed),
                               penetration_over_0p2mm=sum(r["max_penetration_mm"] > .2 for r in completed),
                               metrics=metrics)
    return summary


def render(summary: dict, protocol: dict, source: str, protocol_source: str) -> str:
    lines = ["# 当前 48D 模型与 classical baseline 配对开发结果（2026-09-23）", "",
             "本表为全新重跑的 panel push 开发诊断，参数尚未完成公平预算调优，不能作为论文最终排名。"
             "VMC、impedance、admittance、冻结 MLP、冻结 nonlinear ESN 共享三组物理条件和任务规则。"
             "全部仿真完成回合均计入指标，包括失败回合；执行错误单列，不按零误差处理。", "",
             "| 方法 | 完成数 | 任务通过 | panel gate通过 | 位置 RMSE (mm) | 峰值力矩 (N·m) | 峰值速度 (m/s) | 速度 P95 (m/s) | 最坏穿透 (mm) |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for method, s in summary.items():
        def metric(key, scale=1., worst=False):
            m = s["metrics"][key]
            if m is None:
                return "缺失"
            if worst:
                return f"{m['worst'] * scale:.4f}"
            sd = m['std'] * scale if m['std'] is not None else float('nan')
            return f"{m['mean'] * scale:.4f} ± {sd:.4f}"
        n = s['planned']
        lines.append(f"| {method} | {s['completed']}/{n} | {s['task_success']}/{n} | {s['panel_gate_success']}/{n} | "
                     + " | ".join((metric("tracking_rmse_3d_m", 1000),
                                    metric("control_step_applied_torque_peak_nm"),
                                    metric("speed_peak_25hz_mps"), metric("speed_p95_25hz_mps"),
                                    metric("max_penetration_mm", worst=True))) + " |")
    lines += ["", "数值为回合均值 ± 回合标准差（n=3），不是训练 seed 置信区间；穿透列为最坏回合。", "",
              "## 评价口径与公平性边界", "",
              "- RMSE：25 Hz 的末端位置相对当前任务 waypoint 的欧氏误差。任务阶段按状态切换，"
              "各方法的切换时刻可不同；这是相同参考规则下的 waypoint 跟踪指标，不能称为同一绝对时钟轨迹误差。",
              "- 力矩：4 ms 控制步更新的 applied command 最大绝对关节力矩，细物理步保持命令。"
              "早期快照字段名 physics_peak_motor_torque_nm 在此更正语义，数值不改；不是子步实际 qfrc_actuator 测量峰值。",
              "- 速度：25 Hz 末端线速度范数的峰值及 P95，可能漏掉更短瞬态。最终正式矩阵应增加所有方法共用的 physics-substep 审计。",
              "- panel gate：任务通过、杆接触 >0.3 s、终止前 2 s 已脱离杆、杆末态距离 >2 mm、"
              "非目标物外部穿透 <0.2 mm、所有外物接触均无 link0–link4 误碰；它仍不是最终办公室稳定放置门。",
              "- impedance 替换速度伺服为 Jᵀ Cartesian wrench，复用力矩限幅和 slew，"
              "但名义速度/加速度约束不能直接约束其实际运动；高速度、力矩饱和和无杆接触结果只能视为待修正实现诊断。",
              "- admittance 当前仍仅输出虚拟速度，尚未加入完整虚拟位姿参考跟踪；该固定参数失败不能代表充分调优的导纳控制。",
              "- 三组条件的角度、高度、质量联动变化，不是全因子 test。三组均为开发条件，不用于 office blind-test 结论。", "",
              "## 物理条件", "", "```json", json.dumps(protocol["fixtures"], indent=2), "```", "",
              "## 模型与运行来源", "", "```json", json.dumps(protocol["models"], indent=2), "```", "",
              f"原始汇总：`{source}`。协议：`{protocol_source}`。",
              "协议保存运行源码 hashes、参考 arguments、VMC 参数和模型 hashes；每回合保留 command/log/JSON/NPZ。",
              "", "## 下一步验收", "",
              "为传统控制器修正接口并在同一开发集上固定调参预算；通过真实接触、任务和物理门后，"
              "与冻结 ESN/MLP 在新的一组预先固定物理条件上评估。保留失败率、三项指标和阶段统计，"
              "不从本轮失败表推导 proposed 的论文级优势。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--result', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.result.read_text())
    protocol = json.loads(args.protocol.read_text())
    if protocol['observation'] != 'proprio48':
        raise ValueError('This report requires the matched 48D matrix')
    summary = summarize(result, protocol)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(summary, protocol, str(args.result), str(args.protocol)))
    evidence = dict(summary=summary, source_sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (args.result, args.protocol, Path(__file__))})
    args.output.with_suffix('.json').write_text(json.dumps(evidence, indent=2, allow_nan=False) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
