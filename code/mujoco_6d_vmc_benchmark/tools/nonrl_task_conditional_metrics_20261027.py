"""Task-conditional time efficiency; never rewrites legacy SPT receipts."""
from __future__ import annotations

from copy import deepcopy
import math
import statistics


def aggregate(rows):
    rows = deepcopy(rows)
    identities = [(r['method'], r['condition']) for r in rows]
    if len(set(identities)) != len(identities):
        raise ValueError('Duplicate method-condition episode')
    successful = [r for r in rows if r['task_success']]
    for r in successful:
        t = r['completion_time_s']
        if t is None or not math.isfinite(t) or t <= 0:
            raise ValueError('Task success requires a finite positive completion time')
    tref = min((r['completion_time_s'] for r in successful), default=None)
    for r in rows:
        if 'spt' in r:
            r['legacy_spt'] = r.pop('spt')
        r['spt_task_conditional'] = (tref / max(tref, r['completion_time_s'])
                                     if r['task_success'] else None)

    def summary(name, group):
        successes = [r for r in group if r['task_success']]
        contact = sum(r['comfort']['human_contact_duration_s'] for r in group)
        compliant = sum((r['comfort']['human_comfort_torque_compliance'] or 0) *
                        r['comfort']['human_contact_duration_s'] for r in group)
        return dict(method=name, episodes=len(group), task_success=len(successes),
            strict_success=sum(r['strict_success'] for r in group),
            task_and_strict_success=sum(r['task_success'] and r['strict_success'] for r in group),
            spt_task_conditional_n=len(successes),
            spt_task_conditional_mean=statistics.mean(r['spt_task_conditional'] for r in successes) if successes else None,
            completion_time_mean_s_task=statistics.mean(r['completion_time_s'] for r in successes) if successes else None,
            peak_torque_mean_nm=statistics.mean(r['peak_torque_nm'] for r in group),
            peak_torque_worst_nm=max(r['peak_torque_nm'] for r in group),
            human_comfort_torque_compliance_contact_time_weighted=compliant/contact if contact else None,
            human_contact_duration_s_total=contact,
            machine_safety_violation_rate=statistics.mean(r['comfort']['machine_safety_violation'] for r in group))
    methods = [summary(n, [r for r in rows if r['method'] == n])
               for n in sorted({r['method'] for r in rows})]
    # Only fitted seeds are pooled as families. Classical finalists are distinct
    # fixed configurations, not independent training seeds or test-selected winners.
    families = [summary(f, [r for r in rows if r['method'].startswith(f + '_s')])
                for f in ('esn', 'rnn', 'mlp')
                if any(r['method'].startswith(f + '_s') for r in rows)]
    return dict(t_ref_s=tref, t_ref_definition='One global minimum over all Task-success times in this explicitly named matrix, irrespective of Strict; post-hoc empirical reference, not optimal time.',
                spt_formula='mean(T_ref / max(T_i, T_ref) | Task_i=true); no Task successes => null/NA; Strict reported separately',
                methods=methods, learned_family_pooled=families, rows=rows)


def render(report):
    def num(v): return 'NA' if v is None else f'{v:.4f}'
    lines = ['# Task成功条件下的SPT（非RL）', '',
        f"状态：{report['status']}；共同后验 T_ref={num(report['t_ref_s'])}秒。", '',
        '只对Task成功回合求时间效率均值，Strict失败不会排除；失败回合SPT为NA，成功率及安全指标仍保留全部回合。',
        'ESN/RNN/MLP汇总为三个训练seed的回合池；传统参数配置各自列出，不将两套参数当随机seed，也不按测试结果选赢家。', '',
        '| 方法 | Task | Task且Strict | 条件SPT | 成功平均秒数 | 平均回合峰矩Nm | 最坏峰矩Nm | 接触期力矩合规比例 | 机器违规率 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    groups = report['learned_family_pooled'] + [m for m in report['methods'] if m['method'].startswith('historical_')]
    for m in groups:
        lines.append(f"| {m['method']} | {m['task_success']}/{m['episodes']} | {m['task_and_strict_success']}/{m['episodes']} | {num(m['spt_task_conditional_mean'])} | {num(m['completion_time_mean_s_task'])} | {num(m['peak_torque_mean_nm'])} | {num(m['peak_torque_worst_nm'])} | {num(m['human_comfort_torque_compliance_contact_time_weighted'])} | {num(m['machine_safety_violation_rate'])} |")
    lines += ['', '各方法成功子集不同，应结合成功率阅读；条件SPT不能替代整体任务完成能力。舒适阈值为经验驱动力矩代理，不是人体舒适认证。',
              '旧报告/旧SPT不覆盖；新表的合规/违规列是0–1比例。完整逐seed结果及逐回合hash见JSON。']
    return '\n'.join(lines) + '\n'
