"""Report the complete, unchanged 24-rollout substep audit separately from ablations."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


METHODS = ('vmc', 'impedance', 'admittance', 'mlp', 'esn',
           'impedance_k300_reference', 'impedance_k900_reference', 'admittance_r2_reference')
OLD_NAMES = dict(impedance_k300_reference='impedance_reference (initial_reference_r1)',
                 impedance_k900_reference='impedance_reference (K900)',
                 admittance_r2_reference='admittance_reference (snapshot_r2)')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--measured', type=Path, required=True)
    p.add_argument('--invariance', type=Path, required=True)
    p.add_argument('--previous', type=Path, required=True)
    p.add_argument('--protocol', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    measured = json.loads(args.measured.read_text())
    invariance = json.loads(args.invariance.read_text())
    previous = json.loads(args.previous.read_text())['summary']
    fixtures = {f['seed']:f for f in json.loads(args.protocol.read_text())['fixtures']}
    rows = [r for r in measured['rows'] if r['method'] in METHODS]
    expected = {(method, seed) for method in METHODS for seed in fixtures}
    actual = [(r['method'],r['fixture']['seed']) for r in rows]
    identical = {(r['method'],r['seed']) for r in invariance['comparison']
                 if not r['unequal'] and r['compared_arrays'] == 18}
    if len(actual) != len(set(actual)) or set(actual) != expected or identical != expected:
        raise ValueError('Incomplete paired matrix or missing exact trajectory invariance')
    summaries = {}
    for method in METHODS:
        part = [r for r in rows if r['method'] == method]
        for r in part:
            if (r['fixture'] != fixtures[r['fixture']['seed']] or r['returncode'] != 0 or
                    r['audit_error'] is not None or len(r['metrics']) != 1):
                raise ValueError('Invalid paired rollout')
        metrics = [r['metrics'][0] for r in part]
        if any(m['samples'] != 480000 or m['timestep_s'] != 5e-5 for m in metrics):
            raise ValueError('Unexpected physical step/duration')
        values = np.array([[m['position_rmse_3d_m'], m['generalized_actuator_torque_peak_nm'],
                            m['linear_speed_peak_mps']] for m in metrics])
        if not np.isfinite(values).all():
            raise ValueError('Nonfinite measurements')
        xyz_mse = np.mean([np.square(m['position_rmse_xyz_m']) for m in metrics], axis=0)
        lift_mse = np.mean([m['stages']['3']['count']/m['samples']*
                            m['stages']['3']['position_rmse_3d_m']**2 for m in metrics])
        old = previous[OLD_NAMES.get(method,method)]['metrics']
        summaries[method] = dict(n=3, task_pass=sum(r['task_success'] for r in part),
            strict_pass=sum(r['strict_success'] for r in part),
            metric_order=['substep_waypoint_rmse_m','substep_actuator_torque_peak_nm','substep_linear_speed_peak_mps'],
            mean=values.mean(axis=0).tolist(), worst=values.max(axis=0).tolist(),
            sample_std=values.std(axis=0,ddof=1).tolist(),
            pooled_xyz_squared_error_fraction=(xyz_mse/xyz_mse.sum()).tolist(),
            pooled_lift_squared_error_fraction=float(lift_mse/xyz_mse.sum()),
            previous_speed_peak_25hz_mean=old['speed_peak_25hz_mps']['mean'],
            speed_peak_mean_increase_pct=float(100*(values[:,2].mean()/old['speed_peak_25hz_mps']['mean']-1)),
            torque_mean_difference_nm=float(values[:,1].mean()-old['control_step_applied_torque_peak_nm']['mean']),
            rod_contact_s=[r['rod_contact_s'] for r in part])
    lines = ['# 三条件统一物理子步对比与误差解释', '',
        '8个原方法/版本×3个条件全部完成，每条24秒、480000物理步。24条原rollout的每条18个数组与历史实验逐元素一致，说明新增测量没有改变这批控制行为。4条策略干预另见因果报告，不混入本表。', '',
        '| 方法/版本 | task | 完整gate | 子步位置RMSE mm | 实际关节力矩峰值 Nm | 子步速度峰值 m/s |',
        '|---|---:|---:|---:|---:|---:|']
    for method, s in summaries.items():
        error, torque, speed = s['mean']
        lines.append(f"| {method} | {s['task_pass']}/3 | {s['strict_pass']}/3 | {1000*error:.3f} | {torque:.3f} | {speed:.5f} |")
    lines += ['', '数值为每回合指标再平均，失败回合保留；标准差和最坏值见同名JSON。原impedance是绕过速度参考整形的失配接口诊断，不能凭其低RMSE参与正式排名。', '',
        '## 为什么低误差或低峰值不一定更好', '',
        '| 方法/版本 | Z方向占全程平方误差 | loaded-lift占全程平方误差 | 相比25Hz峰速均值变化 | 实际峰矩均值−旧命令峰矩均值 Nm |',
        '|---|---:|---:|---:|---:|']
    for method, s in summaries.items():
        lines.append(f"| {method} | {100*s['pooled_xyz_squared_error_fraction'][2]:.2f}% | {100*s['pooled_lift_squared_error_fraction']:.2f}% | {s['speed_peak_mean_increase_pct']:+.3f}% | {s['torque_mean_difference_nm']:+.6f} |")
    lines += ['',
        '位置误差是实际末端到当前状态机waypoint的距离，并非到连续时间规划轨迹的距离。Z方向和loaded lift贡献大，意味着主要衡量抬升/恢复进度，不能独自代表横向接触让位品质。相同目标规则不保证不同控制器切换阶段的时刻相同。', '',
        '例如K300阻抗的较低峰值伴随任务0/3，不能判为优于完成任务的方法。固定低通后的VMC也已出现峰值降低但任务失败的反例，见 [因果诊断](ESN_PANEL_CAUSAL_DIAGNOSIS_20260923.md)。三个维度必须与完整gate、失败原因和阶段指标一起解释，不构造掩盖任务失败的总分。', '',
        'r2导纳约0.08 m/s的峰值还需结合执行结构解释：其残差由“移动参考的有界WBC输出−原WBC输出”构成，因而重新经过当前nominal_speed=0.08的参考速度整形；ESN/MLP/VMC则在名义WBC之后叠加yield。两者共享外层关节/力矩安全限制，但内部可请求的速度并不完全等价。导纳低峰值不能独立证明更好的接触策略；这是一项控制器家族差异，不是实际末端速度必然≤0.08的数学保证（仍有离散保持、slew、关节投影和动力学）。依据为run_panel_admittance_reference_20260923.py、admittance_reference_core_20260923.py、run_primitive_teacher_v7_20260917.py与fixed_panda_wbc.py。', '',
        '## 口径与局限', '',
        '- 这里位置、速度均使用50微秒物理子步的更新后qpos/qvel，在独立scratch运动学中重建。误差目标取当时task stage，旧25Hz的记录时刻/目标更新口径不同，两套RMSE不应要求逐值相同。',
        '- 力矩为每个物理步live qfrc_actuator前7关节的绝对最大值；其动力学求值时刻可能早于步末速度，因此不声称力矩和速度严格同步。该模型本轮实际峰矩与原命令峰矩相同是观测结果，不是对所有执行器模型的假设。',
        '- 新峰值揭示25Hz稀疏采样遗漏的短瞬态；50微秒离散仿真采样仍不是数学意义的连续时间真实极值。',
        '- 这些仍为原三个开发条件；参数搜索及预先冻结的六条件验证必须另报，不能用调参后的胜出结果覆盖本表。', '',
        '## 证据', '',
        '- [原方法周报与模型来源](BASELINE_WEEKLY_REPORT_20260923.md)',
        '- [统一测量实现及一致性检查](PHYSICS_SUBSTEP_MEASUREMENT_20260923.md)',
        '- [持续实验入口](CONTINUOUS_BASELINE_PROGRESS_20260923.md)', '']
    sources = {str(path):hashlib.sha256(path.read_bytes()).hexdigest()
               for path in (args.measured,args.invariance,args.previous,args.protocol)}
    args.output.write_text('\n'.join(lines))
    args.output.with_suffix('.json').write_text(json.dumps(dict(summary=summaries,sources_sha256=sources),indent=2,allow_nan=False)+'\n')
    print(args.output)


if __name__ == '__main__':
    main()
