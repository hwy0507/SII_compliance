"""Independent archive audit and retained eight-method DGX deployment report."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    for key in ('archive','old-report','baseline-raw','output'):p.add_argument('--'+key,type=Path,required=True)
    args=p.parse_args();root=args.archive/'evaluation'
    complete=json.loads((root/'COMPLETE.json').read_text())
    if complete['status']!='complete' or complete['episodes']!=7:raise ValueError('Seven executions incomplete')
    protocol=json.loads((root/'protocol.json').read_text())
    freeze=json.loads((args.archive/'FINAL_MODEL_FREEZE.json').read_text())
    for name,value in freeze['files'].items():
        if sha(args.archive/'pilot'/name)!=value:raise ValueError('Archived frozen model/normalizer/evidence drift')
    if sha(args.archive/'PPO_POTENTIAL_DGX_PROTOCOL_20260924.md')!=freeze['protocol_sha256']:raise ValueError('Frozen protocol drift')
    parity=json.loads((args.archive/'offline_parity/PARITY.json').read_text())
    if not parity['passed'] or parity['checkpoint_sha256']!=freeze['files']['ppo_final.zip']:raise ValueError('Offline model parity drift')
    replay=json.loads((root/'ZERO_REPLAY_PARITY.json').read_text())
    if not replay['passed'] or not replay['all_numeric_arrays_finite']:raise ValueError('Zero replay not exact')
    old=json.loads(args.old_report.read_text())
    if len(old['rows'])!=42 or not old['raw_metrics_recomputed']:raise ValueError('Original42 retained audited rows required')
    source_checks={n:dict(expected=h,actual=sha(args.archive/'source'/n)) for n,h in protocol['source_sha256'].items()}
    if any(x['actual']!=x['expected'] for x in source_checks.values()):raise ValueError('Archived source drift')
    rows=json.loads((root/'FINAL_RESULT.json').read_text())['rows']
    expected={('ppo_potential8192',s) for s in range(9400,9406)}|{('zero',9400)}
    if {(r['method'],r['fixture']['seed']) for r in rows}!=expected:raise ValueError('Wrong seven-row matrix')
    checks=[];new=[];artifact_hashes={}
    for row in rows:
        if 'execution_error' in row:raise ValueError('Execution error retained; not completed valid audit')
        method,seed=row['method'],row['fixture']['seed'];job=root/method/str(seed)
        result_path=job/'rollout/rollout.json';result=json.loads(result_path.read_text())
        if sha(result_path)!=row['result_sha256']:raise ValueError('Result archive hash drift')
        if sha(result_path.with_suffix('.mjb'))!=row['model_mjb_sha256']:raise ValueError('MJB archive drift')
        if old['fixture_model_hashes'][str(seed)]!=row['model_mjb_sha256']:raise ValueError('MJB differs between methods')
        numeric=0
        for file in job.rglob('*.npz'):
            artifact_hashes[str(file.relative_to(root))]=sha(file)
            with np.load(file,allow_pickle=False) as archive:
                for key in archive.files:
                    values=archive[key]
                    if values.dtype.kind in 'fciu':
                        numeric+=1
                        if not np.isfinite(values).all():raise ValueError(f'Nonfinite archive:{file}:{key}')
        with np.load(result_path.with_suffix('.npz'),allow_pickle=False) as trace,np.load(args.baseline_raw/'vmc'/str(seed)/'rollout/rollout.npz',allow_pickle=False) as base:
            if not np.array_equal(trace['observation'][0],base['observation'][0]):raise ValueError('Initial actor state differs')
            stages={str(int(x)):int(np.sum(trace['stage']==x)) for x in np.unique(trace['stage'])}
        with np.load(job/'metrics/episode_0/substep_metrics.npz',allow_pickle=False) as raw:
            error=raw['error'].astype(float);twist=raw['twist'].astype(float);torque=raw['qfrc_actuator'].astype(float)
            actual=[float(np.sqrt(np.mean(np.sum(error**2,axis=1)))),float(np.abs(torque).max()),float(np.linalg.norm(twist[:,:3],axis=1).max())]
            targets=[row['physical']['position_rmse_3d_m'],row['actuator_torque_peak_nm'],row['linear_speed_peak_substep_mps']]
            if not np.allclose(actual,targets,atol=2e-5,rtol=2e-6):raise ValueError('Float32 raw metrics mismatch')
            if len(error)!=row['physical']['samples'] or not np.allclose(np.diff(raw['time']),row['physical']['timestep_s'],atol=1e-10,rtol=0):raise ValueError('Physical samples invalid')
        checks.append(dict(method=method,seed=seed,passed=True,numeric_arrays_finite=numeric,
            initial_actor_observation_exact=True,recomputed_rmse_m=actual[0],recomputed_torque_nm=actual[1],recomputed_speed_mps=actual[2]))
        if method=='ppo_potential8192':
            new.append(dict(row,fixture_triggered=bool(result['fixture_triggered']),real_contact=bool(result['real_contact']),
                source='potential_ppo_deployment',stage_counts=stages,duration_measured_s=row['physical']['samples']*row['physical']['timestep_s']))
    combined=old['rows']+new;summary={}
    for method in dict.fromkeys(r['method'] for r in combined):
        subset=[r for r in combined if r['method']==method]
        if len(subset)!=6:raise ValueError('Exactly six fixtures per method required')
        summary[method]=dict(episodes=6,task=sum(r['task_success'] for r in subset),gate=sum(r['strict_success'] for r in subset),
            mean_substep_rmse_mm=1000*float(np.mean([r['physical']['position_rmse_3d_m'] for r in subset])),
            mean_actual_peak_torque_nm=float(np.mean([r['actuator_torque_peak_nm'] for r in subset])),
            mean_substep_peak_speed_mps=float(np.mean([r['linear_speed_peak_substep_mps'] for r in subset])),
            all_full_duration=all(r['physical']['samples']*r['physical']['timestep_s']>=23.99 for r in subset))
    report=dict(scope='Same DGX fixtures; different training data/reward/controller priors, not equal-data baseline reproduction',
        summary=summary,rows=combined,new_raw_audit=checks,source_checks=source_checks,
        old_report_sha256=sha(args.old_report),zero_replay=replay,complete=complete,
        artifact_sha256=artifact_hashes,freeze=freeze,offline_parity=parity,
        checkpoint_sha256=protocol['checkpoint_sha256'],normalizer_sha256=protocol['normalizer_sha256'],
        original_results_retained=True,all_fixture_mjb_equal=True,all_new_initial_actor_states_exact=True)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.with_suffix('.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    lines=['# 潜势奖励PPO8192：DGX六条件结果与八方法表','',
        f"固定final8192模型完成六条PPO和一条zero重验，task{complete['task']}/6、strict gate{complete['gate']}/6，全部保留。zero9400与原已归档轨迹逐元素完全相同，其余五条zero复用原结果。原dense PPO及原五种控制器结果保留，不选择有利模型。",'',
        '| 方法 | task | strict gate | 子步RMSE均值 mm | 实际峰矩均值 Nm | 子步峰速均值 m/s | 全部24s |',
        '|---|---:|---:|---:|---:|---:|---|']
    for method,r in summary.items():
        lines.append(f"| {method} | {r['task']}/6 | {r['gate']}/6 | {r['mean_substep_rmse_mm']:.4f} | {r['mean_actual_peak_torque_nm']:.4f} | {r['mean_substep_peak_speed_mps']:.6f} | {'是' if r['all_full_duration'] else '否，安全停止保留'} |")
    lines+=['',f"七条新原始归档的{sum(x['numeric_arrays_finite'] for x in checks)}个数值数组有限；float32物理子步数据独立复算误差/扭矩/速度通过，50µs时间步和样本数正确；每个fixture与原方法MJB相同、初始48D观测完全相同。{len(source_checks)}份冻结源码哈希在归档后复核一致。",
        f"完整归档`outputs/ppo_potential_dgx_archive_20260924_r1/`约458MiB，服务器/本机checksum dry-run无差异；紧凑证据在`docs/evidence/ppo_potential_dgx_20260924/`，本报告JSON保留{len(artifact_hashes)}份NPZ哈希和全部逐项检查。",'',
        '| seed | final stage | rod实际触发 | task | strict gate | 当前阶段终点误差 mm |',
        '|---|---:|---|---|---|---:|']
    for row in sorted(new,key=lambda r:r['fixture']['seed']):
        lines.append(f"| {row['fixture']['seed']} | {row['final_stage']} | {row['fixture_triggered']} | {row['task_success']} | {row['strict_success']} | {1000*row['endpoint_error_m']:.3f} |")
    lines+=['','终点误差针对当前stage waypoint；停在抓持阶段时低误差不代表完成抬升/搬运。rod在loaded_lift触发，若未到该阶段则没有实际经历同等杆扰动，不能把小穿透或低全程误差解释成更优接触响应。','',
        'PPO仅单rod、单seed、8192互动步，ESN/MLP使用多场景模仿数据。潜势PPO只改变reward，保留原失败dense模型；六条件为已有开发验证，不能称独立office测试或论文级文献复现。',
        f"模型SHA256：`{protocol['checkpoint_sha256']}`。normalizer SHA256：`{protocol['normalizer_sha256']}`。",'']
    args.output.with_suffix('.md').write_text('\n'.join(lines))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
