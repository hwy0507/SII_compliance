"""Independently validate archived frozen search and report all 78 episodes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np


GATE_LABELS = dict(task='任务失败', rod_contact_over_0p3s='杆接触≤0.3s',
    released_over_2s='末次杆接触距结束≤2s或无接触',final_gap_over_2mm='末端杆间隙≤2mm',
    penetration_below_0p2mm='穿透≥0.2mm',no_upstream_contact='上游接触',
    object_lift_over_100mm='物体抬升≤100mm',final_object_speed_below_20mmps='末段物体速度≥20mm/s',
    endpoint_below_15mm='末10点平均误差≥15mm',valid_physics='物理有效性失败',
    no_task_upstream_contact='任务上游接触',final_stage_3='未到最终阶段',cup_safe='杯安全失败')


def read(path):
    return json.loads(path.read_text())


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def independent_selection(rows, candidates):
    selection = {}
    for family in ('impedance', 'admittance'):
        scores = []
        for candidate in candidates:
            if candidate['family'] != family:
                continue
            part = [r for r in rows if r['candidate'] == candidate]
            values = [[r['tracking_rmse_25hz_m'], r['actuator_torque_peak_nm'],
                       r['linear_speed_peak_substep_mps']] for r in part]
            scores.append(dict(candidate=candidate,
                strict_success=sum(r['strict_success'] for r in part),
                task_success=sum(r['task_success'] for r in part),
                means=np.mean(values, axis=0).tolist()))
        for score in scores:
            rank = 0.
            for column, value in enumerate(score['means']):
                ordered = sorted(s['means'][column] for s in scores)
                positions = [i+1 for i, v in enumerate(ordered) if v == value]
                rank += sum(positions)/len(positions)
            score['metric_rank_sum'] = rank
        scores.sort(key=lambda s: (-s['strict_success'], -s['task_success'],
                                  s['metric_rank_sum'], s['candidate']['id']))
        selection[family] = dict(selected=scores[0]['candidate'], scores=scores,
            reliable_on_all_development_conditions=scores[0]['strict_success'] == 3)
    return selection


def audit_phase(directory, rows, candidates, fixtures, source_hashes):
    expected = {(c['id'], f['seed']) for c in candidates for f in fixtures}
    actual = [(r['candidate']['id'], r['fixture']['seed']) for r in rows]
    require(len(actual) == len(set(actual)) and set(actual) == expected, 'Incomplete/duplicate matrix')
    require(all('execution_error' not in r for r in rows), 'Execution errors present')
    model_hashes, details, file_hashes = {}, [], {}
    for row in rows:
        candidate, fixture = row['candidate'], row['fixture']
        require(candidate in candidates and fixture in fixtures, 'Configuration differs from frozen matrix')
        job = directory / candidate['id'] / str(fixture['seed'])
        require(read(job/'result.json') == row, 'Aggregate/job result mismatch')
        command = read(job/'command.json')
        require(all(row[k] == v for k, v in command.items()), 'Command manifest mismatch')
        rollout = job/'rollout/rollout.json'
        require(digest(rollout) == row['result_sha256'], 'Result hash mismatch')
        model = digest(job/'rollout/rollout.mjb')
        require(model == row['model_mjb_sha256'], 'MJB hash mismatch')
        model_hashes.setdefault(str(fixture['seed']), set()).add(model)
        result = read(rollout)
        physical = read(job/'metrics/episode_0/substep_metrics.json')
        require(physical == row['physical'], 'Physical sidecar differs from aggregate')
        audit = read(job/'metrics/audit_manifest.json')
        require(audit['enabled'] and audit['error'] is None and audit['episodes'] == [physical], 'Invalid audit')
        require(all(source_hashes.get(k) == v for k,v in audit['source_sha256'].items()), 'Instrumented source hash mismatch')
        require(physical['samples'] == 480000 and physical['timestep_s'] == 5e-5, 'Wrong physical duration')
        with np.load(job/'rollout/rollout.npz', allow_pickle=False) as trace:
            require(trace['observation'].shape == (600, 48), 'Observation contract differs')
            rmse = float(np.sqrt(np.mean(np.sum((trace['position']-trace['target'])**2, axis=1))))
            require(rmse == row['tracking_rmse_25hz_m'], '25Hz RMSE recomputation mismatch')
            sampled_speed = float(np.linalg.norm(trace['twist'][:, :3], axis=1).max())
            command_torque = float(np.abs(trace['torque']).max())
            endpoint = float(np.mean(np.linalg.norm(trace['position'][-10:]-trace['target'][-10:],axis=1)))
            lift = float(trace['object_position'][-1,2]-.425)
            final_object_speed = float(np.linalg.norm(np.diff(trace['object_position'][-10:],axis=0)/.04,axis=1).max())
            require(endpoint == result['endpoint_error_m'] and lift == result['lift_m'], 'Task geometry recomputation mismatch')
        with np.load(job/'metrics/episode_0/substep_metrics.npz', allow_pickle=False) as raw:
            require(all(raw[k].shape[0] == 480000 for k in raw.files), 'Incomplete raw physical trace')
            require(all(np.isfinite(raw[k]).all() for k in raw.files), 'Nonfinite physical samples')
            times = raw['time']
            require(np.all(np.diff(times) > 0) and np.allclose(np.diff(times), 5e-5, rtol=0, atol=1e-12), 'Physical timestamps invalid')
            require(abs(times[0]-5e-5)<1e-10 and abs(times[-1]-24)<1e-7, 'Physical timestamps do not span 24s')
            raw_recomputed = dict(
                linear_speed_peak_mps=float(np.linalg.norm(raw['twist'][:, :3].astype(np.float64), axis=1).max()),
                generalized_actuator_torque_peak_nm=float(np.abs(raw['qfrc_actuator']).max()),
                position_rmse_3d_m=float(np.sqrt(np.mean(np.sum(np.square(raw['error'],dtype=np.float64),axis=1)))),
                position_rmse_xyz_m=np.sqrt(np.mean(np.square(raw['error'],dtype=np.float64),axis=0)).tolist())
            for key,value in raw_recomputed.items():
                require(np.allclose(value,physical[key],rtol=1e-6,atol=1e-7), f'Raw physical metric mismatch: {key}')
            stages = raw['stage']
            errors = raw['error'].astype(np.float64)
            require(set(np.unique(stages)) == {int(k) for k in physical['stages']}, 'Raw stages mismatch')
            for key,stats in physical['stages'].items():
                selected = stages == int(key)
                require(int(selected.sum()) == stats['count'], 'Stage count mismatch')
                stage_rmse = float(np.sqrt(np.mean(np.sum(errors[selected]**2,axis=1))))
                require(np.isclose(stage_rmse,stats['position_rmse_3d_m'],rtol=1e-6,atol=1e-7), 'Stage RMSE mismatch')
        contacts = result['panel_audit']['contacts']
        rod = contacts['push_rod_geom']
        external = [v for k, v in contacts.items() if k != 'target_object_geom']
        upstream = any(set(v['bodies']) & {'fr3_link0','fr3_link1','fr3_link2','fr3_link3','fr3_link4'} for v in external)
        task_components = dict(object_lift_over_100mm=lift>.1, final_object_speed_below_20mmps=final_object_speed<.02,
            endpoint_below_15mm=endpoint<.015, valid_physics=not result['invalid_physics'],
            no_task_upstream_contact=not result['upstream_contact'], final_stage_3=result['final_stage']==3,
            cup_safe=result['cup_safe'])
        require(all(task_components.values()) == result['success'], 'Task acceptance recomputation mismatch')
        gates = dict(task=bool(result['success']), rod_contact_over_0p3s=rod['duration_s'] > .3,
            released_over_2s=rod['last_s'] is not None and 24-rod['last_s'] > 2,
            final_gap_over_2mm=result['panel_audit']['final_rod_gap_m'] > .002,
            penetration_below_0p2mm=max(v['max_penetration_m'] for v in external) < .0002,
            no_upstream_contact=not upstream)
        require(all(gates.values()) == row['strict_success'], 'Strict gate recomputation mismatch')
        require(gates['task'] == row['task_success'], 'Task flag mismatch')
        require(physical['generalized_actuator_torque_peak_nm'] == row['actuator_torque_peak_nm'], 'Torque mismatch')
        require(physical['linear_speed_peak_mps'] == row['linear_speed_peak_substep_mps'], 'Speed mismatch')
        details.append(dict(candidate=candidate['id'], family=candidate['family'], fixture=fixture,
            task_success=row['task_success'], strict_success=row['strict_success'], gates=gates,
            failed_gates=[k for k, v in gates.items() if not v],
            task_components=task_components,task_failed_components=[k for k,v in task_components.items() if not v],
            object_lift_m=lift,final_object_speed_mps=final_object_speed,
            rmse_25hz_m=rmse, rmse_substep_m=physical['position_rmse_3d_m'],
            speed_25hz_mps=sampled_speed, speed_substep_mps=row['linear_speed_peak_substep_mps'],
            torque_command_25hz_peak_nm=command_torque, torque_actual_peak_nm=row['actuator_torque_peak_nm'],
            endpoint_error_m=row['endpoint_error_m'], max_penetration_mm=row['max_penetration_mm'],
            rod_contact_s=row['rod_contact_s'], model_mjb_sha256=model,
            physical=physical, raw_recomputed_physical=raw_recomputed, archive_job=str(job)))
        for path in sorted(job.rglob('*')):
            if path.is_file():
                file_hashes[str(path.relative_to(directory.parent))] = digest(path)
    require(all(len(v) == 1 for v in model_hashes.values()), 'Paired physical models differ')
    return dict(rows=sorted(details, key=lambda r:(r['candidate'],r['fixture']['seed'])),
        paired_model_sha256={k:next(iter(v)) for k,v in model_hashes.items()},
        file_sha256=file_hashes)


def summarize(rows):
    summary = {}
    for name in sorted({r['candidate'] for r in rows}):
        part = [r for r in rows if r['candidate'] == name]
        keys = ('rmse_25hz_m','rmse_substep_m','speed_25hz_mps','speed_substep_mps',
                'torque_command_25hz_peak_nm','torque_actual_peak_nm','endpoint_error_m',
                'max_penetration_mm','rod_contact_s')
        xyz_mse = np.mean([np.square(r['physical']['position_rmse_xyz_m']) for r in part],axis=0)
        lift_mse = np.mean([r['physical']['stages']['3']['count']/480000 *
                           r['physical']['stages']['3']['position_rmse_3d_m']**2 for r in part])
        summary[name] = dict(n=len(part), task=sum(r['task_success'] for r in part),
            strict=sum(r['strict_success'] for r in part),
            failed_gate_counts={k:sum(k in r['failed_gates'] for r in part)
                                for k in sorted({k for r in part for k in r['failed_gates']})},
            task_failed_component_counts={k:sum(k in r['task_failed_components'] for r in part)
                                          for k in sorted({k for r in part for k in r['task_failed_components']})},
            metrics={k:dict(mean=float(np.mean([r[k] for r in part])),
                            worst=float(max(r[k] for r in part)),
                            sample_std=float(np.std([r[k] for r in part],ddof=1))) for k in keys},
            pooled_xyz_squared_error_fraction=(xyz_mse/xyz_mse.sum()).tolist(),
            pooled_lift_squared_error_fraction=float(lift_mse/xyz_mse.sum()))
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    archive=args.archive.resolve()
    campaign=archive/'measured_campaign'
    budget=campaign/'fixed_budget'
    frozen=archive/'source_fixed_budget'
    protocol=read(budget/'protocol.json')
    require(read(campaign/'status.json')['status']=='complete', 'Campaign not complete')
    require(read(campaign/'COMPLETE.json')==dict(measured_episodes=28,budget_development=48,budget_validation=30), 'Missing campaign completion')
    require(read(budget/'COMPLETE.json')==dict(development_episodes=48,validation_episodes=30,
        selection_sha256=digest(budget/'selection.json')), 'Budget completion mismatch')
    require(digest(archive/'frozen_inputs/base_protocol.json')==protocol['base_protocol_sha256'], 'Base protocol mismatch')
    require(digest(frozen/'docs/CLASSICAL_TUNING_PROTOCOL_20260923.md')==protocol['specification_sha256'], 'Specification mismatch')
    for name, sha in protocol['source_sha256'].items():
        require(digest(frozen/'scripts'/name)==sha, f'Frozen source changed: {name}')
    for name, record in protocol['frozen_models'].items():
        require(digest(archive/'frozen_inputs'/name/'best.npz')==record['sha256'], f'Model changed: {name}')
    development=read(budget/'development/FINAL_RESULT.json')['rows']
    validation=read(budget/'validation/FINAL_RESULT.json')['rows']
    selection=independent_selection(development,protocol['candidates'])
    require(selection==read(budget/'selection.json'), 'Independent selection differs')
    runner=runpy.run_path(str(frozen/'scripts/run_classical_fixed_budget_20260923.py'))
    require(runner['select'](development,protocol['candidates'],protocol['development_fixtures'])==selection, 'Frozen selection differs')
    configs=[selection[k]['selected'] for k in ('impedance','admittance')]
    configs += [dict(id=k,family=k,parameters={}) for k in ('vmc','mlp','esn')]
    phases=dict(development=audit_phase(budget/'development',development,protocol['candidates'],protocol['development_fixtures'],protocol['source_sha256']),
                validation=audit_phase(budget/'validation',validation,configs,protocol['validation_fixtures'],protocol['source_sha256']))
    summaries={k:summarize(v['rows']) for k,v in phases.items()}
    report=dict(scope=protocol['scope'], archive=str(archive), checks=dict(unique_development=48,unique_validation=30,
        execution_errors=0,selection_independently_recomputed=True,frozen_runner_selection_recomputed=True,
        observation_shape=[600,48],physical_samples_per_episode=480000,all_raw_files_hashed=True,
        raw_physical_finite_and_timestamps_verified=True,raw_physical_metrics_recomputed=True,
        raw_float32_vs_summary_float64_tolerance=dict(rtol=1e-6,atol=1e-7),
        all_job_models_locally_hashed=True,frozen_source_files_hashed=len(protocol['source_sha256']),
        frozen_protocol_and_checkpoints_verified=True),selection=selection,summary=summaries,phases=phases,
        protocol_sha256=digest(budget/'protocol.json'),frozen_models=protocol['frozen_models'])
    lines=['# 固定预算经典控制器搜索与六条件独立验证','',
        '48个开发回合和30个验证回合全部完成、无执行错误。每条24秒、600×48观测、480000个50微秒物理子步。所有失败回合保留。', '',
        '## 开发选择：完整16候选','',
        '按预先冻结规则：完整gate数优先，其次任务数，再按25Hz位置RMSE、物理子步实际峰矩与峰速的均值排名和选择；不使用验证数据选参数。','',
        '| 候选 | task /3 | gate /3 | 25Hz RMSE mm | 实际峰矩 Nm | 子步峰速 m/s | 三指标排名和 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for family in ('impedance','admittance'):
        for score in selection[family]['scores']:
            e,t,v=score['means']
            lines.append(f"| {score['candidate']['id']} | {score['task_success']} | {score['strict_success']} | {e*1000:.3f} | {t:.3f} | {v:.6f} | {score['metric_rank_sum']:.1f} |")
    lines += ['', '选中阻抗K=900、ζ=1.2；导纳K=150、ζ=0.7。两者均未在全部开发条件通过完整gate，因此选择只说明符合预声明开发规则，不代表已得到可靠经典baseline。参数全集、排名、每回合结果见同名JSON。','',
        '本轮每家族仅8个候选，搜索各向同性平移K与ζ，Krot按比例固定；不能声称充分调优或全局最优。VMC teacher使用6D各向异性参数，控制家族自由度差异仍存在。后续可研究Z恢复刚度与横向让位解耦，但应建立新协议与新验证条件，不能用940x结果返选本轮参数。','',
        '## 六条件共同验证','',
        '这是冻结的同layout验证，不是office blind test，不是六次独立训练；结果不可用于重新选择本轮参数。','',
        '| 方法 | task /6 | gate /6 | 25Hz RMSE mm | 子步RMSE mm | 实际峰矩 Nm | 子步峰速 m/s |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for name,s in summaries['validation'].items():
        m=s['metrics']
        lines.append(f"| {name} | {s['task']} | {s['strict']} | {m['rmse_25hz_m']['mean']*1000:.3f} | {m['rmse_substep_m']['mean']*1000:.3f} | {m['torque_actual_peak_nm']['mean']:.3f} | {m['speed_substep_mps']['mean']:.6f} |")
    lines += ['', '表中为每回合指标的算术均值；JSON保留样本标准差、最坏值和每条件原值。不能凭失败回合低RMSE或低速度判其更优，也不能从这6个确定性条件外推统计显著性。','',
        '| 方法 | 失败门计数（允许重叠） |','|---|---|']
    for name,s in summaries['validation'].items():
        failures='；'.join(f'{GATE_LABELS[k]} {n}/6' for k,n in s['failed_gate_counts'].items())
        lines.append(f'| {name} | {failures} |')
    lines += ['',
        '| 方法 | 条件 | task | gate | 失败门 | 终点误差 mm | 最大穿透 mm | 杆接触 s |',
        '|---|---:|---:|---:|---|---:|---:|---:|']
    for r in phases['validation']['rows']:
        failures = [GATE_LABELS[k] if k!='task' else '任务['+'、'.join(GATE_LABELS[v] for v in r['task_failed_components'])+']' for k in r['failed_gates']]
        lines.append(f"| {r['candidate']} | {r['fixture']['seed']} | {int(r['task_success'])} | {int(r['strict_success'])} | {', '.join(failures) or '—'} | {r['endpoint_error_m']*1000:.3f} | {r['max_penetration_mm']:.6f} | {r['rod_contact_s']:.5f} |")
    lines += ['', '门含义：任务完成；杆接触>0.3秒；最后杆接触距24秒结束>2秒；最终杆间隙>2mm；非目标物外部穿透<0.2mm；无link0–4上游接触。边界使用严格不等式，未放宽任何验收。','',
        '## 采样口径与阶段解释','',
        '| 方法 | Z平方误差占比 | loaded-lift平方误差占比 | 子步峰速均值相对25Hz变化 | 实际子步峰矩−25Hz样本命令峰矩的均值 Nm |',
        '|---|---:|---:|---:|---:|']
    for name,s in summaries['validation'].items():
        m=s['metrics']
        delta=100*(m['speed_substep_mps']['mean']/m['speed_25hz_mps']['mean']-1)
        torque=m['torque_actual_peak_nm']['mean']-m['torque_command_25hz_peak_nm']['mean']
        lines.append(f"| {name} | {100*s['pooled_xyz_squared_error_fraction'][2]:.2f}% | {100*s['pooled_lift_squared_error_fraction']:.2f}% | {delta:+.4f}% | {torque:+.6f} |")
    lines += ['',
        '误差相对状态机waypoint，主要反映抬升/恢复进度，不单独代表横向接触让位质量。25Hz与子步在状态/目标更新时间上不同，不能混成一个历史分数；本轮冻结选择始终使用25Hz误差。', '',
        '速度为步末scratch运动学J(q)qdot，力矩为该物理步保留的live qfrc_actuator前7关节；力矩求值可能早于步末速度，不能声称严格同时。全物理步离散峰值也不等于数学连续时间真实峰值。', '',
        '这里的旧峰矩从同一rollout.npz的25Hz torque数组重算，故表中差值包含稀疏采样遗漏，不应解读为执行器实现误差；它与历史报告中控制更新频率在线累计的命令峰矩也不是同一采样口径。', '',
        '经典控制器冻结了参考整形、限制器、48D信息和同一物理环境；冻结学生权重未重训。导纳经WBC执行、阻抗为笛卡尔力矩控制，这种结构差异应在论文保留，不能称为完全相同控制架构。', '',
        '尤其reference admittance的residual=s×(WBCshift−WBCnominal)，与原nominal组合后重新经过nominal_speed=0.08的速度整形；ESN/MLP/VMC在名义WBC后叠加yield。外层关节/力矩限制相同不代表内部可请求速度集合相同。导纳约0.08m/s的低峰速不能单独归因于策略更好，这也不是实际物理速度始终不超过0.08的保证。', '',
        '## 证据与复核','',
        f'- 完整本机归档：`{archive}`，含78条原始JSON/NPZ/MJB、子步raw NPZ、命令和运行日志，以及28条历史测量回合。',
        '- 本报告独立枚举48+30配对矩阵、重算25Hz误差与全部gate、检查每条600×48/480000样本、验证78个实际MJB hash及各fixture跨方法一致性。逐条检验raw物理样本有限、时间单调/步长/24秒终点，并独立重算物理峰速、峰矩、全程/XYZ/各阶段RMSE；float32 raw与float64在线累积采用rtol=1e-6、atol=1e-7的舍入容差。',
        '- 独立实现选择规则并调用冻结选择函数，两者均与selection.json完全一致；冻结脚本、协议和两个学生checkpoint hash全部匹配。',
        '- 同名JSON列出归档中所有开发/验证job文件SHA256、每个条件的共享MJB SHA256、每阶段统计。物理峰值来自float64在线累积，raw向量保存float32，离线重算会存在舍入差。',
        '- [归档校验证书](evidence/classical_20260923/fixed_budget/ARCHIVE_VERIFICATION.json)记录106条服务器/本机checksum dry-run结果；该传输检查独立于本报告的78条raw复算。',
        '- [预声明协议](CLASSICAL_TUNING_PROTOCOL_20260923.md)；[测量与不变性](PHYSICS_SUBSTEP_MEASUREMENT_20260923.md)；[原24条对比](SUBSTEP_THREE_METRIC_COMPARISON_20260923.md)。','']
    args.output.write_text('\n'.join(lines))
    args.output.with_suffix('.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(output=str(args.output),checks=report['checks'],validation={k:dict(task=v['task'],strict=v['strict']) for k,v in summaries['validation'].items()}),indent=2))


if __name__=='__main__':
    main()
