"""Render all16 repaired methods after both independent final audits pass.

Separate full55s and short trajectories, retain every failure in success rates,
and show all contacts and all ESN paired comparisons without outcome selection.
This tool performs no training, physics, checkpoint selection or gate changes.
"""
import argparse
import statistics
from pathlib import Path

from office_v7_uniform24_20261008 import read, write, sha, now
from report_office_v7_uniform24_20261008 import LABELS


def average(rows, key):
    return statistics.fmean(row['metrics'][key] for row in rows) if rows else None


def aggregate(report):
    assert report['complete'] and report['completed'] == report['planned'] == 384
    assert {r['family'] for r in report['rows']} == set(LABELS)
    output = []
    for family, label in LABELS.items():
        rows = [r for r in report['rows'] if r['family'] == family]
        assert len(rows) == len({r['condition_id'] for r in rows}) == 24
        assert all(r['status'] == 'complete' for r in rows)
        full = [r for r in rows if r['metrics']['full_horizon']]
        short = [r for r in rows if not r['metrics']['full_horizon']]
        successful = [r for r in full if r['metrics']['strict_success']]
        subsets = {}
        for name, subset in [('all_observed', rows), ('full55s', full),
                             ('short', short), ('strict_full55s', successful)]:
            subsets[name] = dict(n=len(subset), condition_ids=[r['condition_id'] for r in subset],
                **{k: average(subset, k) for k in ('rmse_mm', 'peak_torque_nm', 'peak_speed_mps')})
        parent = next(f for f in report['families'] if f['family'] == family)
        whole = [r['metrics']['supplemental_contact']['whole_observed_horizon']['external_robot'] for r in full]
        exposed = [c for c in whole if c['exposure']]
        external = dict(full_episodes=len(full), exposed=len(exposed),
            mean_p95_n=statistics.fmean(c['contact_p95_force_n'] for c in exposed) if exposed else None,
            mean_impulse_ns=statistics.fmean(c['impulse_ns'] for c in exposed) if exposed else None,
            semantics='Whole55s external-robot summed contact magnitudes; excludes payload. Not sum of event channels.')
        output.append(dict(family=family, label=label, task=parent['task'], strict=parent['strict'],
            task_wilson95=parent['task_wilson95'], strict_wilson95=parent['strict_wilson95'],
            max_penetration_mm=parent['max_penetration_mm'], subsets=subsets,
            contacts=parent['contacts'], recovery=parent['recovery'], whole55s_external_robot=external))
    return output


def fmt(value, digits=3):
    return 'NA' if value is None else f'{value:.{digits}f}'


def interval(value):
    return 'NA' if value is None else f'{100*value[0]:.1f}–{100*value[1]:.1f}%'


def markdown(rows, paired, root):
    lines = ['# 修复后全部16方法：同一新24条件比较', '',
        '所有方法使用相同冻结office-v7模型、55秒上限、formal dt=5e-5、原任务/安全判据和执行器限制。',
        '新测试条件在全部模型锁定后才打开。下表是固定系统的同测试比较；历史示范、搜索和在线学习预算并不相等。', '',
        '## 任务、安全与完整时长指标', '',
        '任务/Strict分母始终为24，包括物理提前失败。RMSE/峰矩/峰速列仅统计实际完整55秒回合；',
        '它们仍包含完整时长的任务失败，不能凭较低数值判优。不同方法的完整子集可能不同，严格配对见后表。', '',
        '|方法|Task /24|Strict /24|Strict Wilson 95%|完整/提前终止|完整RMSE mm|完整平均峰矩 Nm|完整平均峰速 m/s|全24最坏穿透 mm|',
        '|---|---:|---:|---|---:|---:|---:|---:|---:|']
    for row in rows:
        full, short = row['subsets']['full55s'], row['subsets']['short']
        lines.append('|'+ '|'.join([row['label'],str(row['task']),str(row['strict']),
            interval(row['strict_wilson95']),f"{full['n']}/{short['n']}",
            *[fmt(full[k]) for k in ('rmse_mm','peak_torque_nm','peak_speed_mps')],
            fmt(row['max_penetration_mm'])])+'|')
    lines += ['', '## 接触覆盖及受力（描述性，不单独排名）', '',
        '每格为实际接触回合数/24、这些回合的平均接触P95力和平均冲量。无接触写NA，不填零。',
        '包含任务失败和短回合；接触时长、路径及完成状态不同，较低受力不能自动解释为更好的柔顺控制。', '',
        '|方法|球：覆盖 / P95 N / 冲量 Ns|手：覆盖 / P95 N / 冲量 Ns|棍：覆盖 / P95 N / 冲量 Ns|桌角：覆盖 / P95 N / 冲量 Ns|',
        '|---|---|---|---|---|']
    for row in rows:
        cells = [row['label']]
        for event in ('ball','human','rod','unknown_edge'):
            c = row['contacts'][event]
            cells.append(f"{c['exposed']}/24 / {fmt(c['mean_contact_p95_n'])} / {fmt(c['mean_impulse_ns'])}")
        lines.append('|'+'|'.join(cells)+'|')
    lines += ['', '## 完整55秒的全部外部机器人接触', '',
        '补充上表固定扰动窗口外的负载，包括放置时再次碰到静止人体；原始统计已在测试前登记。',
        '这里不含物块接触，事件通道也不可相加。覆盖分母为完整55秒回合，P95/冲量仅平均其中发生接触的回合。', '',
        '|方法|接触/完整回合|平均P95 N|平均冲量 Ns|', '|---|---:|---:|---:|']
    for row in rows:
        w = row['whole55s_external_robot']
        lines.append(f"|{row['label']}|{w['exposed']}/{w['full_episodes']}|{fmt(w['mean_p95_n'])}|{fmt(w['mean_impulse_ns'])}|")
    lines += ['', '## 扰动后的恢复与删失', '',
        '每格为恢复/实际接触数、未观察到恢复数、已恢复回合的条件平均时间；未恢复不填零。',
        '时间取既定误差和速度阈值下持续稳定回归，原指标定义不变。条件平均不是全体恢复时间估计。', '',
        '|方法|球：恢复/接触；删失；条件秒|手：恢复/接触；删失；条件秒|棍：恢复/接触；删失；条件秒|',
        '|---|---|---|---|']
    for row in rows:
        cells = [row['label']]
        for event in ('ball','human','rod'):
            r = paired['recovery'][row['family']][event]
            times = r['observed_recovery_times_s']
            cells.append(f"{r['recovered']}/{r['exposed']}；{r['right_censored']}；{fmt(statistics.fmean(times) if times else None)}")
        lines.append('|'+'|'.join(cells)+'|')
    lines += ['', '## ESN与其余15方法的配对结果', '',
        '成功检验按相同条件配对，Task与Strict分别对15个对照做Holm校正；不只挑ESN占优的方法。',
        '连续指标为ESN减对照，仅在双方完整55秒的相同条件上计算。对应探索性区间和双方Strict子集见JSON。', '',
        '|对照|Task：ESN独成功/对照独成功；校正p|Strict：ESN独成功/对照独成功；校正p|共同完整n|ΔRMSE mm|Δ峰矩 Nm|Δ峰速 m/s|',
        '|---|---|---|---:|---:|---:|---:|']
    for family, label in LABELS.items():
        if family == 'esn':
            continue
        c = paired['comparisons'][family]
        cells = [label]
        for key in ('task_success','strict_success'):
            v = c[key]
            cells.append(f"{v['esn_only']}/{v['comparator_only']}；{fmt(v['holm_adjusted_p_over_15_comparators'],4)}")
        metrics = [c['global_metrics'][k]['jointly_full'] for k in ('rmse_mm','peak_torque_nm','peak_speed_mps')]
        assert len({v['paired_conditions'] for v in metrics}) == 1
        cells.append(str(metrics[0]['paired_conditions']))
        cells.extend(fmt(v['difference']) for v in metrics)
        lines.append('|'+'|'.join(cells)+'|')
    lines += ['', '## 解释边界', '',
        '- 每族仅一个经开发选择的冻结模型；24条件反映条件变化，不代表训练seed方差或真实硬件泛化。',
        '- ESN/matched RNN/ordinary RNN选中新teacher20/5版本；两种MLP/memoryless选中旧18/6版本。',
        '  128宽度不等于相同参数量；本批不能单独证明储备池结构因果优势。',
        '- 纯RL未使用teacher或BC；无成功曝光/未收敛时只能报告有限预算表现，不能当算法能力上限。',
        '- enhanced teacher使用本体输入和共享名义命令上的手工恢复，必须纳入，不能因表现好就自动排为特权方法。',
        '- 接触配对连续统计还要求双方Strict且接触，属于结果条件化的探索性子集；总失败数仍在首表。',
        '- 控制器状态/动作重放与限制检查不等于完整机器人动力学重放、无源性证明或真实机器人安全认证。', '',
        '服务器主根：`arm1@192.168.31.70:'+str(root)+'`。',
        '完整原始轨迹、checkpoint/source哈希及失败保留；每项审计与输入哈希见本报告目录RECEIPT.json。', '']
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--verified', type=Path, required=True)
    p.add_argument('--controllers', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    root = a.root.resolve()
    report_path = root/'final_evaluation/REPORT.json'
    report = read(report_path)
    verified = read(a.verified/'VERIFIED_SUMMARY.json')
    assert verified['complete'] and verified['episodes_verified'] == 384
    assert verified['report_sha256'] == sha(report_path)
    assert verified['lock_sha256'] == sha(root/'FINAL_MODEL_LOCK.json')
    controls = read(a.controllers/'execution.json')
    assert controls['status'] == 'complete' and controls['expected'] == controls['passed'] == 144
    assert read(a.controllers/'REGISTRATION.json')['lock_sha256'] == verified['lock_sha256']
    paired = read(a.verified/'PAIRED_COMPARISONS.json')
    assert set(paired['comparisons']) == set(LABELS)-{'esn'}
    rows = aggregate(report)
    a.output.mkdir(parents=True)
    write(a.output/'ALL_METHOD_SUBSETS.json', dict(created_utc=now(), families=rows,
        scope='All observed, full55s, short and strict-full subsets explicitly separated. No method or failure removed.'))
    (a.output/'COMPARISON.md').write_text(markdown(rows, paired, root))
    inputs = [report_path, root/'FINAL_MODEL_LOCK.json', a.verified/'VERIFIED_SUMMARY.json',
        a.verified/'PAIRED_COMPARISONS.json', a.controllers/'execution.json', a.controllers/'REGISTRATION.json']
    write(a.output/'RECEIPT.json', dict(created_utc=now(),source_sha256=sha(__file__),
        inputs={str(p.resolve()):sha(p) for p in inputs},
        outputs={p.name:sha(p) for p in a.output.iterdir() if p.is_file()},
        no_training_or_model_selection=True))


if __name__ == '__main__':
    main()
