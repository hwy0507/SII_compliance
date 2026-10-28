"""Combine explicitly matched development revisions, keeping failures visible."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-result', type=Path, required=True)
    parser.add_argument('--base-protocol', type=Path, required=True)
    parser.add_argument('--revision', nargs=3, action='append', default=[],
                        metavar=('LABEL', 'RESULT', 'PROTOCOL'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    base = json.loads(args.base_protocol.read_text())
    base_sha = hashlib.sha256(args.base_protocol.read_bytes()).hexdigest()
    fixtures = {f['seed']: f for f in base['fixtures']}
    groups = {}
    sources = []
    jobs = [('base', args.base_result, args.base_protocol)] + [
        (label, Path(result), Path(protocol)) for label, result, protocol in args.revision]
    if len({label for label, _, _ in jobs}) != len(jobs):
        raise ValueError('Revision labels must be unique')
    for label, result_path, protocol_path in jobs:
        protocol = json.loads(protocol_path.read_text())
        if label != 'base':
            if protocol['base_protocol_sha256'] != base_sha or protocol['duration_override'] is not None:
                raise ValueError(f'Unmatched reference protocol or duration: {label}')
            if {f['seed']: f for f in protocol['fixture_list']} != fixtures:
                raise ValueError(f'Unmatched physical fixtures: {label}')
        rows = json.loads(result_path.read_text())['rows']
        if not rows:
            raise ValueError(f'Empty result: {label}')
        if label == 'base' and {r['method'] for r in rows} != {'vmc', 'impedance', 'admittance', *base['models']}:
            raise ValueError('Missing or unexpected base method')
        seen = set()
        for row in rows:
            key = (row['method'], row['fixture']['seed'])
            if key in seen or row['fixture'] != fixtures.get(key[1]):
                raise ValueError(f'Duplicate or mismatched row: {label}/{key}')
            seen.add(key)
            group = row['method'] if label == 'base' else f'{row["method"]} ({label})'
            groups.setdefault(group, []).append(row)
        for method in {r['method'] for r in rows}:
            if {seed for m, seed in seen if m == method} != set(fixtures):
                raise ValueError(f'Incomplete method: {label}/{method}')
        sources.append(dict(label=label, result=str(result_path), protocol=str(protocol_path),
                            result_sha256=hashlib.sha256(result_path.read_bytes()).hexdigest(),
                            protocol_sha256=hashlib.sha256(protocol_path.read_bytes()).hexdigest()))
    summary = {}
    for name, rows in groups.items():
        completed = [r for r in rows if 'execution_error' not in r]
        metrics = {}
        for key in ('tracking_rmse_3d_m', 'control_step_applied_torque_peak_nm', 'speed_peak_25hz_mps'):
            values = [float(r['physics_peak_motor_torque_nm'] if
                            key == 'control_step_applied_torque_peak_nm' and key not in r else r[key])
                      for r in completed]
            if not np.isfinite(values).all():
                raise ValueError(f'Nonfinite metric: {name}/{key}')
            metrics[key] = dict(mean=float(np.mean(values)), worst=float(max(values)),
                                std=float(np.std(values, ddof=1)) if len(values) > 1 else None) if values else None
        summary[name] = dict(planned=len(rows), completed=len(completed),
                             task_success=sum(r['task_success'] for r in completed),
                             panel_gate_success=sum(r['strict_success'] for r in completed), metrics=metrics)
    lines = ['# 本周 baseline 进展与三维对比（2026-09-23）', '',
             '后续修正与持续实验见 [持续推进记录](CONTINUOUS_BASELINE_PROGRESS_20260923.md) 和 [动作振荡因果诊断](ESN_PANEL_CAUSAL_DIAGNOSIS_20260923.md)。下表保留本轮原开发结果；新的物理子步测量与参数搜索独立报告，不覆盖旧结果。', '',
             '已完成当前 48D 模型与传统控制器的配对开发实验，并针对经典控制器接口问题完成独立修正对照。'
             '以下是开发结果，不是已充分调优或未见测试集上的论文排名。所有完整回合（包括任务/物理失败）保留在数值中；执行错误不填零分。', '',
             '| 方法/版本 | 执行完成 | 任务通过 | panel gate | 位置 RMSE (mm) | 峰值力矩 (N·m) | 峰值速度 (m/s) |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for name, s in summary.items():
        cells = []
        for key, scale, digits in [('tracking_rmse_3d_m', 1000, 3),
                                    ('control_step_applied_torque_peak_nm', 1, 3),
                                    ('speed_peak_25hz_mps', 1, 4)]:
            m = s['metrics'][key]
            cells.append(f"{m['mean'] * scale:.{digits}f}" if m else '执行失败，无指标')
        n = s['planned']
        task = f"{s['task_success']}/{n}" if s['completed'] else '不适用（执行错误）'
        gate = f"{s['panel_gate_success']}/{n}" if s['completed'] else '不适用（执行错误）'
        lines.append(f"| {name} | {s['completed']}/{n} | {task} | {gate} | " + ' | '.join(cells) + ' |')
    lines += ['', '表中为三个物理条件的回合均值；峰值列是“先计算每回合峰值，再求均值”。标准差和最坏值保存在同名 JSON。', '',
              '## 当前判断与版本说明', '',
              '本轮不能支持 proposed ESN 的整体优势。修正版导纳的三项均值均低于 ESN，但两者完整 panel gate 都仅通过 1/3；低误差、低峰值不能替代接触与任务完成。K900 阻抗虽然任务通过 3/3，仍未通过完整 panel gate。', '',
              '原 impedance 直接追踪跳变 waypoint，绕过速度参考整形且没有有效杆接触，仅作接口失配诊断，不参与正式排名。原 admittance 为 velocity-only 接口。initial_reference_r1 中阻抗为 K300，导纳为 K95（执行错误）；K900 为独立阻抗候选，snapshot_r2 为保持 K95 的导纳快照修正版。', '',
              '## 公平性与指标定义', '',
              '- 三个条件为 seed 9300/9301/9302，联动改变角度、推杆高度、物块质量。所有完整对照均为 24 s、48D 本体观测协议、相同任务/几何/solver；原 impedance 的参考接口差异见上文，不冒充等价实现。',
              '- 新版本协议的 base_protocol_sha256 必须与原 48D 协议相同；此工具拒绝改时长、改条件或缺少配对记录的修正版。编译模型 MJB 按条件逐字节一致的证据另行保存。',
              '- 位置 RMSE 相对当前状态机 waypoint，包含抬升阶段，不是相同绝对时间轴的规划轨迹误差。各控制器到达阶段的时刻可不同。',
              '- 力矩为 4 ms 控制更新的 applied command 峰值；速度为 25 Hz 末端线速度采样峰值，可能漏掉子步瞬态。不能声称已测得物理连续时间的真实峰值。',
              '- panel gate 包含任务、真实杆接触、脱离/间隙、0.2 mm 穿透门和无上游误碰，不等同于最终办公室稳定放置门。所有方法使用原门槛，未因结果放宽。',
              '- 直接力矩阻抗复用 torque box/slew，但替换了速度伺服；其内部执行结构与 ESN/MLP/VMC 的 action7 分支不同，必须作为控制器家族对照解释。',
              '- 参数修正和 K300/K900 候选只属于开发阶段；不能把开发集选出的最好参数当作无偏测试结果。当前单个冻结模型的三个评估条件也不等于三次独立训练。', '',
              '## 已完成核验', '',
              '- 全套 105 项测试通过；120 个原始捕获源码的导出一致性及语法检查通过。',
              '- 原五方法 15 条、K900 阻抗 3 条与 r2 导纳 3 条原始 trace 已独立复算位置 RMSE 和 25 Hz 峰值速度；r2 每条包含 600 个有限数值样本。审计文件位于 docs/evidence/classical_20260923/ 下。',
              '- 两份 server_model_metadata*.json 共记录 29 份 MJB 哈希（含 smoke）；非 smoke 的每个条件下，9 个方法/版本的编译模型哈希一致。冻结 checkpoint 与 teacher split 的来源已单独核验。',
              '- 本轮服务器实验已结束，原始结果、错误日志、协议与隔离源码快照均保留；没有遗留的后台训练或仿真。', '',
              '## 诊断与证据入口', '',
              '- [经典控制器最终开发记录与失败原因](REFERENCE_CLASSICAL_DEVELOPMENT_20260923.md)',
              '- [原五方法矩阵、阶段 RMSE 与原始 trace 复算](PANEL_MATCHED48_COMPARISON_20260923.md)',
              '- [当前 ESN/MLP checkpoint、teacher split 与哈希](CANONICAL_MODEL_PROVENANCE_20260923.md)',
              '- [阻抗积分平衡点修正](IMPEDANCE_MOVING_REFERENCE_20260923.md)',
              '- [导纳位姿参考修正及快照时序问题](ADMITTANCE_REFERENCE_VARIANT_20260923.md)',
              '- [历史 120 条结果审计：不纳入当前论文主表](FAIR_METHOD_COMPARISON_20260923.md)',
              '- [四类 primitive 的早期经典 baseline 诊断](CLASSICAL_BASELINES_20260923.md)',
              '- [RL 调参的三篇文献](RL_PARAMETER_LITERATURE_20260923.md)；[RL 直接动作的三篇文献](RL_ACTION_LITERATURE_20260923.md)',
              '- [已有本机 PPO/SAC 工程预实验](RL_AND_BASELINE_PROGRESS_20260923.md)：legacy 输入协议，仅证明训练链可运行，不加入本表。', '',
              '## 仍需完成的论文验收', '',
              '修正接口后的传统控制器仍需固定预算调参和独立验证；正式矩阵需增加所有方法共用的物理子步速度/实际 actuator torque 审计、接触/恢复阶段指标、更多物理条件和训练 seed。'
              'RL 仍需迁移至同一 48D/action7 与训练 split。全部参数/模型冻结后才能做新的 office blind test，不能从本轮开发表推出 proposed 的整体优势。', '',
              '## 机器可读结果来源', '', '```json', json.dumps(sources, indent=2), '```', '']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text('\n'.join(lines))
    args.output.with_suffix('.json').write_text(json.dumps(dict(summary=summary, sources=sources), indent=2, allow_nan=False) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
