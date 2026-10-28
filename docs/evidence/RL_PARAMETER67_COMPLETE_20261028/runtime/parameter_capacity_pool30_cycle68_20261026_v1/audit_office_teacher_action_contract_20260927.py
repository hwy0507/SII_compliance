"""Quantify VMC-to-executor normalization and R34 teacher imitation gaps.

Reads exposed development histories only; no closed-loop performance claims.
Actual physical velocity is not equated to requested Cartesian yield velocity.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--benchmark', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    snapshot = a.benchmark / 'outputs/esn_office_r36_stress_20260927/source_snapshot'
    sys.path.insert(0, str(snapshot / 'scripts'))
    from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics
    from wbc_velocity_residual_core import VelocityResidualSafetyConfig, VelocityResidualActionFilter
    # Match the frozen create_environment constructor; do not use the generic
    # action filter's default .16 m/s when the office explicitly sets .32 m/s.
    source = snapshot / 'scripts/run_contact_transfer_20260916.py'
    assert 'safety_config=VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32)' in source.read_text()
    executor = VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32)
    limits = np.r_[np.repeat(executor.maximum_linear_yield_mps, 3),
                   np.repeat(executor.maximum_angular_yield_radps, 3)]
    teacher = SixDVirtualDynamics({})
    rows, raw = [], {}
    plan = json.loads((a.benchmark / 'configs/esn_office_r34_stress_20260927.json').read_text())
    for job in plan['jobs']:
        trace_path = a.benchmark / 'outputs/esn_office_r34_stress_20260927/results' / job['id'] / 'rollout.npz'
        with np.load(trace_path) as trace:
            obs = trace['observation'].copy()
            actions = trace['applied_action'].copy()
            stages = trace['stage'].copy()
        teacher = SixDVirtualDynamics({})
        labels = np.asarray([teacher.act(o[39:45], .04) for o in obs])
        filters = [VelocityResidualActionFilter(executor) for _ in range(2)]
        twists = [[], []]
        for applied, label in zip(actions, labels*.5):
            for i, action in enumerate((applied, label)):
                twists[i].append(filters[i].filter(action, .04).cartesian_yield_twist)
        diff = actions-labels*.5
        row = dict(case=job['id'], trace_sha256=sha(trace_path),
                   half_teacher_action_rmse=float(np.sqrt(np.mean(diff**2))),
                   half_teacher_action_rmse_by_channel=np.sqrt(np.mean(diff**2, axis=0)).tolist(),
                   requested_linear_twist_rmse_mps=float(np.sqrt(np.mean((np.asarray(twists[0])[:, :3]-np.asarray(twists[1])[:, :3])**2))),
                   stages=[])
        for stage in np.unique(stages):
            mask = stages == stage
            row['stages'].append(dict(stage_post_step=int(stage), samples=int(mask.sum()),
                half_teacher_action_rmse=float(np.sqrt(np.mean(diff[mask]**2))),
                mean_estimated_wrench=np.mean(obs[mask,39:45],axis=0).tolist()))
        rows.append(row)
        raw[job['id']+'_half_teacher_action'] = labels*.5
        raw[job['id']+'_esn_action'] = actions
    a.output.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(a.output/'shadow_actions.npz', **raw)
    report = dict(purpose='offline contract and imitation diagnostic, not teacher closed-loop evaluation',
                  deployment_linear_yield_limit_mps=executor.maximum_linear_yield_mps,
                  teacher_action_normalizers=teacher.action_limits.tolist(),
                  unsaturated_requested_twist_to_virtual_residual_ratio=(limits/teacher.action_limits).tolist(),
                  half_gain_ratio=(.5*limits/teacher.action_limits).tolist(), rows=rows,
                  caveats=['Ratios precede slew limiting, IK/WBC and physical integration.',
                           'Action0 also changes WBC feedback authority; halving all actions is not just Cartesian unit correction.',
                           'Shadow teacher uses ESN histories and cannot establish teacher closed-loop performance.',
                           'stage is saved post-step and used only for offline grouping, never actor input.'],
                  hashes={str(path):sha(path) for path in (Path(__file__), source,
                      snapshot/'scripts/run_vmc_6d_constrained_push_20260918.py',
                      snapshot/'scripts/wbc_velocity_residual_core.py', a.output/'shadow_actions.npz')})
    (a.output/'ACTION_CONTRACT_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    lines = ['# Teacher 动作归一化与 ESN 模仿差距：离线审计', '',
             '冻结办公室执行接口的线速度残差上限为 0.32 m/s；VMC 的 XYZ 归一化分别为 0.16/0.16/0.20 m/s。',
             '未饱和、未经过变化率限制时，默认 teacher 的 XYZ 请求速度分别为虚拟动态残差的 2/2/1.6 倍。',
             'R34 全局半幅使其变成 1/1/0.8 倍，同时旋转和 slowdown 也减半。',
             '这不是已经证实的失败原因；它说明解析 VMC 动态与部署的动作单位之间存在需要单独检验的映射差异。', '',
             '| 开发条件 | ESN vs 半幅 teacher action RMSE | 请求线速度逐分量 RMSE m/s |',
             '|---|---:|---:|']
    for row in rows:
        lines.append(f"| {row['case']} | {row['half_teacher_action_rmse']:.6f} | {row['requested_linear_twist_rmse_mps']:.6f} |")
    lines += ['', '全部基于原 R34 保存的同一观测历史。请求速度不等于实际末端速度。',
              '不能从这些离线差距推断 teacher 或 ESN 哪个闭环更好；须与 J1 完整任务结果结合。', '']
    (a.output/'ACTION_CONTRACT_AUDIT.md').write_text('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
