"""Read frozen evidence and report all 26 methods without rerunning physics.

This is descriptive postprocessing, not model selection. Failure episodes are
included in the all-run matrix; no-contact cells are NA, never zero rewards.
"""
import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path


METHODS = [
    ('recovery035_esn_fixed', 'Proposed 纯ESN seed1'),
    ('recovery035_esn_seed2', 'Proposed 纯ESN seed2'),
    ('recovery_lift0.035_distance0.02', '增强VMC teacher'),
    ('paired_recovery035__fp64', '普通MLP seed1'),
    ('paired_recovery035_mlp_seed2', '普通MLP seed2'),
    ('paired_recovery035_rnn_fp64', '普通RNN seed1'),
    ('paired_recovery035_rnn_seed2', '普通RNN seed2'),
    ('paired_feature_matched_mlp', '同特征MLP'),
    ('paired_feature_matched_rnn', '同特征RNN seed1'),
    ('paired_feature_matched_rnn_seed2', '同特征RNN seed2'),
    ('recovery035_esn_memoryless', '无记忆重训对照'),
    ('parameter_admittance', 'RL调参·导纳'),
    ('parameter_impedance', 'RL调参·阻抗'),
    ('parameter_vmc', 'RL调参·VMC'),
    ('direct_metric_74001', 'RL action·metric·74001'),
    ('direct_metric_74002', 'RL action·metric·74002'),
    ('direct_office_task_74001', 'RL action·task·74001'),
    ('direct_office_task_74002', 'RL action·task·74002'),
    ('fixed_admittance', '固定导纳'),
    ('fixed_impedance', '固定阻抗'),
    ('fixed_vmc', '固定VMC'),
    ('original_vmc_native', '原始VMC'),
    ('admittance_01', '本轮调参导纳'),
    ('impedance_12', '本轮调参阻抗'),
    ('original_vmc_04', '本轮调参原VMC'),
    ('zero', '名义执行zero'),
]
EVENTS = ('ball', 'human', 'rod', 'unknown_edge', 'pillar')
SCALARS = ('rmse_mm', 'peak_torque_nm', 'peak_speed_mps', 'penetration_mm',
           'position_error_integral_m_s', 'time_above_25mm_s',
           'absolute_joint_mechanical_work_j', 'torque_total_variation_nm')
FORCES = ('contact_p95_force_n', 'peak_force_n', 'impulse_ns', 'contact_duration_s')
TIER = 'heldout_development_dt'
SOURCE = 'arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_rl_20261002_141136/'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values):
    values = [float(v) for v in values if v is not None]
    assert all(math.isfinite(v) for v in values)
    return dict(n=len(values), median=statistics.median(values) if values else None,
                minimum=min(values) if values else None, maximum=max(values) if values else None)


def number(s, digits=2, scale=1):
    return 'NA' if s['median'] is None else f"{s['median'] * scale:.{digits}f}"


def force_cell(g, event, key='contact_p95_force_n', scope='contact', digits=1, scale=1):
    s = g[scope][event][key]
    return number(s, digits, scale) + f" [{s['n']}/4]"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    paths = {k: args.evidence / v for k, v in {
        'report': 'final_report/results.json', 'windows': 'FINAL_CONTACT_WINDOWS.json',
        'compliance': 'final_compliance/COMPLIANCE.json', 'lock': 'VALIDATION_LOCK.json'}.items()}
    data = {k: json.loads(v.read_text()) for k, v in paths.items()}
    assert data['windows']['report_sha256'] == sha(paths['report'])
    assert data['compliance']['report_sha256'] == sha(paths['report'])
    assert data['compliance']['contact_window_audit_sha256'] == sha(paths['windows'])
    assert data['report']['validation_lock_sha256'] == sha(paths['lock'])
    rows = [r for r in data['report']['rows'] if r['tier'] == TIER]
    assert len(rows) == 104 and all(r['full_horizon'] for r in rows)
    assert all(abs(r['duration_s'] - 55) < 1e-6 for r in rows)
    assert all(r['frozen_model_configuration_verified'] for r in rows)
    assert len({r['model_sha256'] for r in rows}) == 1
    assert len({(r['condition'], r['name']) for r in rows}) == 104
    assert {r['name'] for r in rows} == {n for n, _ in METHODS}
    assert {c['name'] for c in data['lock']['candidates']} == {n for n, _ in METHODS}
    index = {(r['condition'], r['name']): r for r in data['windows']['rows'] if r['tier'] == TIER}
    groups = []
    for name, label in METHODS:
        sample = [r for r in rows if r['name'] == name]
        assert len(sample) == 4 and {r['condition'] for r in sample} == {'h1', 'h2', 'h3', 'h4'}
        g = dict(name=name, label=label, n=4, task=sum(r['task_success'] for r in sample),
                 strict=sum(r['strict_success'] for r in sample),
                 metrics={k: stats([r[k] for r in sample]) for k in SCALARS},
                 contact={}, full_task_contact={}, recovery={}, episodes=sample)
        for r in sample:
            assert r['trace_sha256'] == index[(r['condition'], name)]['trace_sha256']
            for event in EVENTS:
                audited = index[(r['condition'], name)]['events'][event]['predeclared']
                for key in ('exposure',) + FORCES:
                    assert r['contact'][event][key] == audited[key]
        for scope in ('contact', 'full_task_contact'):
            for event in EVENTS:
                contacts = [r['contact'][event] if scope == 'contact' else
                            index[(r['condition'], name)]['events'][event]['full_observed_task'] for r in sample]
                exposed = [c for c in contacts if c['exposure']]
                g[scope][event] = dict(exposed=len(exposed),
                                      **{k: stats([c[k] for c in exposed]) for k in FORCES})
        for event in ('ball', 'human', 'rod'):
            records = [r['recovery'][event] for r in sample]
            g['recovery'][event] = dict(exposed=sum(c['exposed'] for c in records),
                observed=sum(c['settled_rejoin_time_s'] is not None for c in records),
                censored=sum(c['right_censored'] for c in records),
                time_observed_only=stats([c['settled_rejoin_time_s'] for c in records]))
        g['rod_hold_gap_s'] = stats([r['contact']['rod'].get('extended_no_contact_longest_s')
                                    for r in sample if r['contact']['rod']['exposure']])
        groups.append(g)
    pairs = [p for p in data['compliance']['pairs'] if p['tier'] == TIER]
    result = dict(source=SOURCE, input_sha256={k: sha(v) for k, v in paths.items()},
                  script_sha256=sha(Path(__file__)), tier=TIER, groups=groups,
                  both_strict_pairs=pairs,
                  aggregation='Median of per-episode metrics; all four episodes including failures. Force medians use actually exposed episodes only, explicit denominator. No pooling seeds or physics resolutions.')
    lines = ['# ESN 与全部 baseline 的统一柔顺性矩阵', '',
        '这是冻结结果的描述性整理，未训练、未重跑仿真、未改变模型选择或门槛。', '',
        '同一 office-validation-v6、同一原生 Spark 运行库/MJB，h1–h4 四条件，每方法4条完整55秒回合；'
        '物理步长 dt=1e-4（开发步长），不混入正式 dt=5e-5 或随机补充。', '',
        '数值为逐回合指标的中位数，**包含失败回合**；接触指标只在实际接触的回合统计，'
        '`[n/4]`为接触覆盖。NA表示未接触，不能视为零力或胜出。JSON保留范围、全部104条原结果、trace/hash、失败原因和成对证据。', '',
        'P95在每回合的接触子步上计算，再取回合中位数；峰矩/峰速是逐回合峰值的中位数，'
        '不是四回合最坏值（最坏值在JSON maximum）。力是接触力模之和，不是净合力。', '',
        '## 统一主矩阵', '',
        '| 方法 | Task /4 | Strict /4 | RMSE mm | 峰矩 Nm | 峰速 m/s | 球峰力 kN [n/4] | 人手P95 N [n/4] | 杆P95 N [n/4] | 桌角P95 N [n/4] |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for g in groups:
        m = g['metrics']
        cells = [g['label'], str(g['task']), str(g['strict']), number(m['rmse_mm']),
                 number(m['peak_torque_nm']), number(m['peak_speed_mps'], 3),
                 force_cell(g, 'ball', 'peak_force_n', digits=2, scale=.001),
                 force_cell(g, 'human'), force_cell(g, 'rod'), force_cell(g, 'unknown_edge')]
        lines.append('| ' + ' | '.join(cells) + ' |')
    lines += ['', '## 累计接触负担与时长（同样包含失败回合）', '',
        '沿用各条件预登记事件窗口：h1/h4球2–4.5s、人手4.5–11.5s、杆12.5–22s；'
        'h2/h3球2–3.5s、人手3.5–10.5s、杆13.5–23s；桌角/柱子为全程。'
        '力模积分单位N·s，不是净动量变化；短接触或不同接触部位也能降低此数，不能单独解释成更软。', '',
        '| 方法 | 球积分 N·s | 人手积分 N·s | 杆积分 N·s | 桌角积分 N·s | 人手接触 s | 杆接触 s | 杆保持最长间隙 ms |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for g in groups:
        cells = [g['label']] + [force_cell(g, e, 'impulse_ns') for e in EVENTS[:4]]
        cells += [force_cell(g, e, 'contact_duration_s', digits=3) for e in ('human', 'rod')]
        cells += [number(g['rod_hold_gap_s'], 2, 1000)]
        lines.append('| ' + ' | '.join(cells) + ' |')
    lines += ['', '## 恢复证据（观测数/暴露数；括号为右删失数）', '',
        '恢复沿用原定义：位置误差≤25mm、实际速度≤25mm/s，保持0.5s，且后续规划进度前进。'
        '下一障碍打断或观察窗结束仍未恢复记为右删失，不能记0秒，也不能把只观察到的恢复者均值当整体均值。'
        '杆保持期无接触间隙不等于有控制的持续滑脱；还需检查接触和任务推进轨迹。', '',
        '| 方法 | 球恢复 | 人手恢复 | 杆恢复 |', '|---|---:|---:|---:|']
    for g in groups:
        cells = [g['label']]
        for event in ('ball', 'human', 'rod'):
            r = g['recovery'][event]
            cells.append(f"{r['observed']}/{r['exposed']} ({r['censored']})" if r['exposed'] else 'NA')
        lines.append('| ' + ' | '.join(cells) + ' |')
    lines += ['', '## 全任务接触覆盖补充（事后诊断）', '',
        '人手等会在原指令窗口外再接触，不能忽略。此表是此前审计已计算的全55秒补充，'
        '与主表并列，不替换预登记终点；仍包含全部失败，覆盖分母显式列出。', '',
        '| 方法 | 人手P95 N | 人手积分 N·s | 杆P95 N | 杆积分 N·s |', '|---|---:|---:|---:|---:|']
    for g in groups:
        cells = [g['label']] + [force_cell(g, e, k, scope='full_task_contact')
                               for e in ('human', 'rod') for k in ('contact_p95_force_n', 'impulse_ns')]
        lines.append('| ' + ' | '.join(cells) + ' |')
    lines += ['', '## 解读边界', '',
        '- 七个RL模型全部列入：三种在线参数控制及两种reward×两个seed的直接action控制；'
        '经典固定/本轮调参、teacher、全部MLP/RNN/ESN和无记忆对照均未遗漏。',
        '- RL及七个经典baseline本组task均0/4，因此与ESN没有共同strict成功条件。'
        '可以报告上面的实际接触负担，但不能据此算“同等完成任务下ESN降低力百分比”。',
        '- 低RMSE可能来自卡住或不让位，低力可能来自未碰到障碍。接触位置、持续时间、任务进度不同，'
        '本矩阵不是固有刚度/导纳的辨识。大量恢复被删失，恢复时间不足以全面排名。',
        '- 球峰力为毫秒级刚性接触仿真瞬态，步长/接触求解器敏感；不是实际机器人碰撞力或人体安全结论。',
        '- 训练曝光不等：ESN/MLP/RNN使用本轮office teacher数据，RL来自此前primitive训练的冻结迁移；'
        '同宽128也不等参数量。结论只针对这些checkpoint在当前世界的表现，不宣称算法族普遍优越。',
        '- 已知正式步长dt=5e-5的两个ESN均放置失败；本矩阵不替代该结果。'
        '随机补充和formal只测开发合格子集，不能并入完整26方法的分母。', '',
        '## 复现与来源', '', f'原始物理与审计归档：`{SOURCE}`。', '',
        '基于Git main `965be4b04f157eeece21f182ce2fab62fe0ef128`、baseline '
        '`ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6`。原模型锁与各回合来源均保存在JSON，不覆盖历史产物。', '',
        '同目录 `MATRIX.json` 为机器可读数值/分母/范围/回合/成对证据；'
        '`tools/build_unified_compliance_matrix_20261003.py` 使用Python标准库复算。', '',
        '生成命令（在benchmark目录）：', '', '```bash',
        'python3 tools/build_unified_compliance_matrix_20261003.py --evidence docs/evidence/paper_esn_12h_20261003 --output docs/evidence/unified_compliance_20261003', '```', '']
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'MATRIX.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    (args.output / 'MATRIX.md').write_text('\n'.join(lines))
    print(json.dumps(dict(models=len(groups), episodes=len(rows), output=str(args.output))))


if __name__ == '__main__':
    main()
