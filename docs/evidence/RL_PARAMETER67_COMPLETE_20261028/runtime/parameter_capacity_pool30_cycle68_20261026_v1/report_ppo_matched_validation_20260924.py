"""Aggregate the frozen DGX deployment matrix against existing same-platform rows."""
import argparse
import json
from pathlib import Path
import sys
import hashlib
import numpy as np


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--evaluation',type=Path,required=True)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--raw',type=Path)
    parser.add_argument('--baseline-raw',type=Path)
    args=parser.parse_args()
    complete=json.loads((args.evaluation/'COMPLETE.json').read_text())
    if complete['status']!='complete':raise ValueError('DGX matrix incomplete')
    manifest=json.loads((args.evaluation/'protocol.json').read_text())
    current=json.loads((args.evaluation/'FINAL_RESULT.json').read_text())['rows']
    old=json.loads(args.baseline.read_text())['rows']
    if len(current)!=12 or any('execution_error' in r for r in current):raise ValueError('Expected12 retained valid executions')
    expected={(m,s) for m in ('ppo8192','zero') for s in range(9400,9406)}
    if {(r['method'],r['fixture']['seed']) for r in current}!=expected:raise ValueError('Wrong current matrix')
    if len(old)!=30:raise ValueError('Expected fixed original30 validation episodes')
    all_rows=[];models={};raw_checks=[]
    for source,rows in [('baseline',old),('ppo_deployment',current)]:
        for original in rows:
            row=dict(original)
            method=row.get('method',row.get('candidate',{}).get('id'))
            seed=row['fixture']['seed'];models.setdefault(seed,set()).add(row['model_mjb_sha256'])
            row['method']=method;row['source']=source
            row['tracking_rmse_substep_m']=row['physical']['position_rmse_3d_m']
            row['duration_measured_s']=row['physical']['samples']*row['physical']['timestep_s']
            all_rows.append(row)
            if source=='ppo_deployment' and args.raw:
                folder=args.raw/method/str(seed)
                result_path=folder/'rollout/rollout.json'
                if digest(result_path)!=row['result_sha256']:raise ValueError('Archived result hash mismatch')
                result_data=json.loads(result_path.read_text())
                row['fixture_triggered']=bool(result_data['fixture_triggered'])
                row['real_contact']=bool(result_data['real_contact'])
                archived_mjb=digest(result_path.with_suffix('.mjb'))
                if archived_mjb!=row['model_mjb_sha256']:raise ValueError('Archived model hash mismatch')
                with np.load(folder/'metrics/episode_0/substep_metrics.npz',allow_pickle=False) as archive:
                    error=archive['error'].astype(float);twist=archive['twist'].astype(float)
                    torque=archive['qfrc_actuator'].astype(float)
                    calculated=dict(rmse=float(np.sqrt(np.mean(np.sum(error**2,axis=1)))),
                        speed=float(np.linalg.norm(twist[:,:3],axis=1).max()),
                        torque=float(np.abs(torque).max()),samples=len(error))
                    dt_valid=bool(np.allclose(np.diff(archive['time']),row['physical']['timestep_s'],atol=1e-10,rtol=0))
                    finite=bool(np.isfinite(error).all() and np.isfinite(twist).all() and np.isfinite(torque).all())
                targets=(row['tracking_rmse_substep_m'],row['linear_speed_peak_substep_mps'],row['actuator_torque_peak_nm'])
                raw_values=(calculated['rmse'],calculated['speed'],calculated['torque'])
                matches=bool(np.allclose(raw_values,targets,atol=2e-5,rtol=2e-6))
                if not matches or not dt_valid or not finite or calculated['samples']!=row['physical']['samples']:
                    raise ValueError('Float32 raw metric recomputation failed')
                raw_checks.append(dict(method=method,seed=seed,passed=True,recomputed=calculated,
                    model_mjb_sha256=archived_mjb,physical_time_steps_valid=dt_valid,raw_finite=finite))
                if args.baseline_raw:
                    with np.load(result_path.with_suffix('.npz'),allow_pickle=False) as new_trace, np.load(
                            args.baseline_raw/'vmc'/str(seed)/'rollout/rollout.npz',allow_pickle=False) as old_trace:
                        a,b=new_trace['observation'][0],old_trace['observation'][0]
                        maximum=float(np.max(np.abs(a-b)))
                    raw_checks[-1]['initial_actor_observation_max_abs_difference_from_vmc']=maximum
                    raw_checks[-1]['initial_actor_observation_equal_to_vmc']=bool(np.array_equal(a,b))
                    if maximum>1e-10:raise ValueError('Initial actor-boundary state differs from reference VMC')
    if any(len(hashes)!=1 for hashes in models.values()):raise ValueError('Methods have different compiled models within fixture')
    summary={}
    for method in dict.fromkeys(r['method'] for r in all_rows):
        part=[r for r in all_rows if r['method']==method]
        if len(part)!=6:raise ValueError('Need6 conditions per method')
        full=all(r['duration_measured_s']>=23.99 for r in part)
        summary[method]=dict(episodes=6,task=sum(r['task_success'] for r in part),
            gate=sum(r['strict_success'] for r in part),all_full_duration=full,
            mean_substep_rmse_mm=1000*float(np.mean([r['tracking_rmse_substep_m'] for r in part])),
            mean_actual_peak_torque_nm=float(np.mean([r['actuator_torque_peak_nm'] for r in part])),
            mean_substep_peak_speed_mps=float(np.mean([r['linear_speed_peak_substep_mps'] for r in part])),
            max_external_penetration_mm=max(r['max_penetration_mm'] for r in part))
    output=dict(scope='Same DGX deployment fixtures; training data/interaction budgets unequal',
        summary=summary,rows=all_rows,all_fixture_mjb_hashes_equal=True,
        fixture_model_hashes={str(seed):next(iter(hashes)) for seed,hashes in models.items()},
        checkpoint_sha256=manifest['checkpoint_sha256'],normalizer_sha256=manifest['normalizer_sha256'],
        raw_metric_checks=raw_checks,raw_metrics_recomputed=bool(args.raw),
        baseline_sha256=digest(args.baseline),deployment_complete=complete,
        caution='Partial safety-stopped episodes, if any, retain observed-window metrics and are not directly ranked against full24s.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.with_suffix('.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    lines=['# 冻结PPO8192：DGX同平台六条件部署比较','',
        'PPO与zero共12条完成；与原30条验证按9400–9405配对，42条的每个fixture MJB hash完全一致。PPO仅在一个rod fixture训练8192步，ESN/MLP使用多场景模仿数据，训练数据与预算不同；这是同部署条件比较，不是等训练预算结论。','',
        '| 方法 | task | strict gate | 子步RMSE均值 mm | 实际峰矩均值 Nm | 子步峰速均值 m/s | 全部24s |',
        '|---|---:|---:|---:|---:|---:|---|']
    for method,r in summary.items():
        lines.append(f"| {method} | {r['task']}/6 | {r['gate']}/6 | {r['mean_substep_rmse_mm']:.4f} | {r['mean_actual_peak_torque_nm']:.4f} | {r['mean_substep_peak_speed_mps']:.6f} | {'是' if r['all_full_duration'] else '否，保留安全提前停止'} |")
    lines.extend(['','统计使用原physics_substep_metrics定义；strict gate为原accepted_panel_demo加无外部upstream，不使用本机pilot的开发gate。若未完成抬升，低全程误差也不能称任务更好，需同时看阶段与task/gate。',
        '本轮PPO六条均停在stage0；扰动按loaded_lift触发，所以未达到触发阶段时未实际经历同等rod扰动。较小穿透或不同误差不能解释为更优接触响应。zero进入stage3但仍未完成任务。','',
        f"最终模型SHA256：`{manifest['checkpoint_sha256']}`；未用validation挑选中间模型。",
        f"原始物理float32数据独立复算：{'已通过全部12条' if args.raw else '本次仅汇总driver记录，尚未本地复算raw'}。",''])
    args.output.with_suffix('.md').write_text('\n'.join(lines))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
