"""Read new24 raw plus nominal parity; reuse pinned old18, aggregate by seed."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'scripts')]
import prepare_paired_multiseed_deployment_20260925 as prep
import run_paired_six_fixture_deployment_20260924 as old_driver
import report_paired_six_fixture_20260924 as old_report
from audit_paired_transitions_20260924 import read,require,exact
from canonical48_paired_deployment_20260924 import sha


def seed_statistics(rows, controls):
    """One inferential unit is a training seed, never an individual fixture."""
    seeds=(20260923,*prep.SEEDS)
    expected={(s,m,f) for s in seeds for m in prep.MODES for f in prep.FIXTURES}
    keys=[(r['training_seed'],r['method'],r['fixture']['seed']) for r in rows]
    require(len(keys)==len(set(keys))==36 and set(keys)==expected,'Need exact3seed × 2mode × 6fixture learned rows')
    require(all('execution_error' not in r for r in rows), 'Execution errors cannot be converted to task failures')
    require(len(controls['nominal_train_vmc'])==len(controls['zero'])==6,'Controls are unique six-fixture sets')
    metric_keys=('waypoint_rmse_mm','actual_peak_torque_nm','substep_peak_speed_mps')
    by_seed={};across={};paired=[]
    for mode in prep.MODES:
        by_seed[mode]={}
        reference='nominal_train_vmc' if mode=='parameter6' else 'zero'
        indexed={r['fixture']['seed']:r for r in controls[reference]}
        require(set(indexed)==set(prep.FIXTURES),'Control fixture coverage differs')
        for seed in seeds:
            part=sorted([r for r in rows if r['method']==mode and r['training_seed']==seed],key=lambda r:r['fixture']['seed'])
            summary=old_report.summarize(part)[mode]
            summary.update(task_rate=summary['task']/6,strict_rate=summary['strict']/6,
                final_goal_distance_mm=old_report.distribution([r['diagnosis']['final_goal_diagnostic']['trace_final_distance_3d_mm'] for r in part]))
            tail=[r['diagnosis']['final_goal_diagnostic']['last6s_absolute_window'] for r in part]
            summary['last6s_goal_rmse_mm']=old_report.distribution([r['rmse_3d_mm'] for r in tail]) if all(r is not None for r in tail) else None
            summary['last6s_rule']='None if any fixture is genuinely safety-short; never drop that failure from six-fixture denominator'
            by_seed[mode][str(seed)]=summary
            deltas=[]
            for row in part:
                base=indexed[row['fixture']['seed']];a=row['physical'];b=base['physical']
                deltas.append(dict(fixture_seed=row['fixture']['seed'],task_reference=bool(base['task_success']),task_learned=bool(row['task_success']),
                    strict_reference=bool(base['strict_success']),strict_learned=bool(row['strict_success']),
                    waypoint_rmse_mm=1000*(a['position_rmse_3d_m']-b['position_rmse_3d_m']),
                    actual_peak_torque_nm=a['generalized_actuator_torque_peak_nm']-b['generalized_actuator_torque_peak_nm'],
                    substep_peak_speed_mps=a['linear_speed_peak_mps']-b['linear_speed_peak_mps']))
            paired.append(dict(training_seed=seed,method=mode,reference=reference,fixture_deltas=deltas,
                seed_mean_deltas={k:float(np.mean([d[k] for d in deltas])) for k in metric_keys},
                shared_control_not_new_training_seed=True))
        items=by_seed[mode]
        across[mode]={k:old_report.distribution([items[str(s)][k]['mean'] for s in seeds]) for k in metric_keys}
        for k in ('task_rate','strict_rate'):
            across[mode][k]=old_report.distribution([items[str(s)][k] for s in seeds])
        across[mode]['final_goal_distance_mm']=old_report.distribution([items[str(s)]['final_goal_distance_mm']['mean'] for s in seeds])
        across[mode]['last6s_goal_rmse_mm']=(old_report.distribution([items[str(s)]['last6s_goal_rmse_mm']['mean'] for s in seeds])
            if all(items[str(s)]['last6s_goal_rmse_mm'] is not None for s in seeds) else None)
        across[mode]['independent_training_seeds']=list(seeds)
        across[mode]['standard_deviation_unit']='population SD across3 training-seed means, not18 fixture episodes'
    return dict(by_training_seed=by_seed,across_training_seeds=across,paired_learning_deltas=paired)


def audit(archive, previous_path, previous_archive):
    require(sha(previous_path)==prep.OLD_HASH,'Old18 report hash differs from predeclared artifact')
    previous=read(previous_path);plan=read(archive/'frozen_plan.json');final=read(archive/'FINAL_RESULT.json')
    complete=read(archive/'COMPLETE.json');execution=read(archive/'execution_manifest.json')
    require(not (archive/'FAILED.json').exists(),'FAILED marker retained; cannot publish completed aggregate')
    require(complete['status']=='complete' and complete['episodes']==25 and complete['learned_episodes']==24 and complete['parity_episodes']==1 and complete['source_unchanged'],'Incomplete25-job deployment')
    require(sha(archive/'frozen_plan.json')==complete['plan_sha256']==final['plan_sha256']==execution['plan_sha256'],'Plan/execution binding differs')
    require(final['execution_errors']==0 and final['planned_episodes']==25,'Execution errors cannot be converted to task failures')
    require(plan['old_report_sha256']==prep.OLD_HASH and plan['total_new_episodes']==25 and plan['learned_episodes']==24,'Wrong planned comparison')
    prep.matrix_keys(plan['jobs']);prep.matrix_keys(final['rows'])
    require(read(previous_archive/'COMPLETE.json')==previous['complete'] and sha(previous_archive/'frozen_plan.json')==previous['plan_sha256'],'Old local archive not report-matched')
    require(not (previous_archive/'FAILED.json').exists(),'Old archive FAILED marker')
    inputs={str(p):sha(p) for p in (previous_path,archive/'COMPLETE.json',archive/'FINAL_RESULT.json',archive/'frozen_plan.json',archive/'execution_manifest.json',Path(__file__))}
    require(execution['source_sha256']==plan['source_sha256'],'Executed source list differs from plan')
    require(execution['driver_sha256']==plan['source_sha256']['tools/run_paired_multiseed_deployment_20260925.py'],'Driver not frozen into plan')
    require(sha(__file__)==plan['source_sha256'][str(Path(__file__).resolve().relative_to(ROOT))], 'Report checker changed since execution')
    # These existing metric and gate implementations must match the executed snapshot.
    for module in (prep,old_driver,old_report):
        name=str(Path(module.__file__).resolve().relative_to(ROOT))
        require(sha(module.__file__)==plan['source_sha256'][name],'Current reused checker changed since execution')
    for name,value in execution['source_sha256'].items():
        path=(archive/'source_snapshot'/name).resolve()
        require(path.is_relative_to((archive/'source_snapshot').resolve()) and sha(path)==value,'Archived source drift')
        inputs[str(path)]=value
    require(sha(archive/'deployment_protocol.md')==plan['protocol_sha256'],'Archived protocol drift')
    inputs[str(archive/'deployment_protocol.md')]=plan['protocol_sha256']
    planned={(j['training_seed'],j['method'],j['fixture']['seed']):j for j in plan['jobs']}
    old_nominal={r['fixture']['seed']:r for r in previous['rows'] if r['method']=='nominal_train_vmc'}
    old_eight={(r['method'],r['fixture']['seed']):r for r in previous['old_eight_method_rows']}
    construct_goal=old_report.goal_constructor(archive/'source_snapshot/scripts')
    rows=[];nominal=None
    for original in final['rows']:
        seed,method,fixture=original['training_seed'],original['method'],original['fixture']['seed']
        job=planned[(seed,method,fixture)];folder=archive/str(seed)/method/str(fixture)
        require(read(folder/'command.json')==job and all(original[k]==v for k,v in job.items()),'Frozen job/command binding differs')
        require(read(folder/'result.json')==original,'Per-job and final aggregate differ')
        require('execution_error' not in original,'Execution failure must remain incomplete')
        for name,value in original['artifact_sha256'].items():
            p=(folder/name).resolve();require(p.is_relative_to(folder.resolve()) and sha(p)==value,'New raw artifact changed')
            inputs[str(p)]=value
        inputs[str(folder/'result.json')]=sha(folder/'result.json')
        stem=folder/'rollout/rollout';result=read(stem.with_suffix('.json'))
        require(sha(stem.with_suffix('.json'))==original['result_sha256'],'Result SHA differs')
        require(original['fixture']==old_nominal[fixture]['fixture'] and job['reference_result_sha256']==old_eight[('vmc',fixture)]['result_sha256'],'Fixture identity differs')
        model=sha(stem.with_suffix('.mjb'))
        require(model==original['model_mjb_sha256']==job['expected_mjb_sha256']==old_nominal[fixture]['model_mjb_sha256'],'MJB differs within fixture')
        require(all(old_eight[(m,fixture)]['model_mjb_sha256']==model for m in old_report.OLD),'Old eight methods not paired')
        reference=previous_archive/'nominal_train_vmc'/str(fixture)/'rollout/rollout'
        require(sha(reference.with_suffix('.json'))==old_nominal[fixture]['result_sha256'],'Old nominal result changed')
        reference_result=read(reference.with_suffix('.json'))
        for field in ('scene','controller_6d_config','experiment_contract','simulation_timestep_s','source_sha256'):
            require(result[field]==reference_result[field],'Core dynamics/config differs: '+field)
        for name,value in result['source_sha256'].items(): require(plan['source_sha256'].get('scripts/'+name)==value,'Result source differs from plan')
        require(not result['teacher_called'] and result['student_mixture']==0. and result['contract']=='proprio48_action7_6d_v1','Wrong pure canonical48 policy deployment')
        physical=read(folder/'metrics/episode_0/substep_metrics.json');measurement=read(folder/'metrics/audit_manifest.json')
        require(physical==original['physical'] and measurement['enabled'] and measurement['error'] is None and measurement['episodes']==[physical],'Measurement aggregate mismatch')
        for name,value in measurement['source_sha256'].items(): require(plan['source_sha256'].get('scripts/'+name)==value,'Instrumentation source differs')
        raw_audit=old_driver.physical_raw_audit(folder/'metrics/episode_0/substep_metrics.npz',physical,result['duration_s'])
        for path in folder.rglob('*.npz'):
            require(str(path.relative_to(folder)) in original['artifact_sha256'],'Unbound NPZ')
            with np.load(path,allow_pickle=False) as data:
                require(all(np.isfinite(data[k]).all() for k in data.files if data[k].dtype.kind in 'fciu'),'Nonfinite raw array')
        goal=construct_goal(json.loads(job['environment']['PANEL_CONFIG']))
        exact(goal,previous['common_final_task_goal_m'],'Common original final target')
        with np.load(stem.with_suffix('.npz'),allow_pickle=False) as trace,np.load(folder/'rollout/paired_policy_trace.npz',allow_pickle=False) as policy,np.load(reference.with_suffix('.npz'),allow_pickle=False) as reference_trace:
            count=len(trace['time'])
            require(1<=count<=600 and (count==600 or result['invalid_physics']),'Wrong rollout/safety-short contract')
            require(np.allclose(trace['time'],.04*np.arange(1,count+1),rtol=0,atol=1e-8) and abs(count*.04-result['duration_s'])<1e-6,'Wrong actual25Hz time window')
            require(trace['observation'].shape==(count,48) and trace['action'].shape==(count,7),'Wrong observation/action shapes')
            exact(trace['observation'][0],reference_trace['observation'][0],'Original initial48 state')
            exact(policy['observation'],trace['observation'],'Policy raw48 alignment');exact(policy['execution_action'],trace['action'],'Policy action7 alignment')
            dimension=7 if method=='direct7' else 6
            low=np.array([0]+[-1]*6) if dimension==7 else -np.ones(6)
            require(policy['policy_action'].shape==(count,dimension) and np.all(policy['policy_action']>=low) and np.all(policy['policy_action']<=1),'Invalid learned request space')
            require(int(trace['stage'][-1])==result['final_stage'],'Final stage differs')
            if np.any(trace['stage']==3): require(np.all(trace['target'][trace['stage']==3]==goal),'Actual loaded-lift target drift')
            diagnosis=old_report.failure_diagnostics(result,trace,goal)
            stages=dict(Counter(str(int(x)) for x in trace['stage']))
        require(diagnosis['strict_success_recomputed']==original['strict_success'] and result['success']==original['task_success'],'Raw gates differ from execution')
        deployment=read(stem.with_suffix('.paired_deployment.json'))
        branch='direct7' if method=='direct7' else 'parameter6';record=plan['training'][str(seed)][branch]
        require(deployment['mode']==method and deployment['device']==record['device'] and deployment['training_manifest_sha256']==record['manifest_sha256'],'Deployment provenance differs')
        for field in ('checkpoint_sha256','normalizer_sha256'): require(deployment[field]==record[field],'Final checkpoint/normalizer changed')
        require(deployment['nominal_options']==old_nominal[fixture]['deployment']['nominal_options'],'Training nominal options changed')
        require(deployment['runtime_fixture_CORE_VMC_CONFIG']==json.loads(job['environment']['CORE_VMC_CONFIG']),'Runtime CORE drift')
        contacts=result['panel_audit']['contacts']
        row=dict(training_seed=seed,method=method,fixture=original['fixture'],task_success=result['success'],strict_success=diagnosis['strict_success_recomputed'],
            physical=physical,raw_metric_audit=raw_audit,model_mjb_sha256=model,result_sha256=original['result_sha256'],
            completed_24s=count==600,safety_terminated_early=count<600,actual_duration_s=result['duration_s'],
            final_stage=result['final_stage'],stage_counts=stages,fixture_triggered=result['fixture_triggered'],
            fixture_trigger_time_s=result['fixture_trigger_time_s'],rod_contact_s=contacts['push_rod_geom']['duration_s'],
            non_target_external_contacts={n:c for n,c in contacts.items() if n!='target_object_geom' and c['duration_s']>0},
            diagnosis=diagnosis,deployment=deployment,archive_job=str(folder),source='new raw recomputed')
        if method=='nominal_train_vmc': nominal=row
        else: rows.append(row)
    require(len(rows)==24 and nominal is not None,'Wrong learned/parity count')
    parity_path=archive/'NOMINAL_REUSE_PARITY.json';parity=read(parity_path)
    require(sha(parity_path)==complete['nominal_reuse_parity_sha256'] and parity['passed'] and parity['old_report_sha256']==prep.OLD_HASH,'Nominal reuse proof missing')
    replayed_parity=prep.nominal_parity(previous_archive/'nominal_train_vmc/9400',Path(nominal['archive_job']))
    require(replayed_parity['arrays']==parity['arrays'] and replayed_parity['model_mjb_sha256']==parity['model_mjb_sha256'],'Nominal raw parity did not reproduce')
    inputs[str(parity_path)]=sha(parity_path);inputs.update(replayed_parity['input_sha256'])
    # Every reused nominal file remains hash-bound; no extra numerical re-audit claim.
    for fixture in prep.FIXTURES:
        folder=previous_archive/'nominal_train_vmc'/str(fixture)
        for name,value in read(folder/'result.json')['artifact_sha256'].items():
            require(sha(folder/name)==value,'Reused nominal artifact drift');inputs[str(folder/name)]=value
    learned_old=[dict(r,training_seed=20260923,source='pinned prior audit; old raw not recomputed this time') for r in previous['rows'] if r['method'] in prep.MODES]
    controls=dict(nominal_train_vmc=list(old_nominal.values()),zero=[r for r in previous['old_eight_method_rows'] if r['method']=='zero'])
    all_learned=learned_old+rows
    return dict(passed=True,new_learned_raw_recomputed=24,nominal_parity_raw_recomputed=1,old_learned_rows_reused=12,
        unique_performance_rows=42,shared_nominal_rows=6,additional_zero7_reference_rows=6,unique_deployment_records_excluding_zero7=43,
        old_report_sha256=prep.OLD_HASH,plan_sha256=sha(archive/'frozen_plan.json'),rows=all_learned,controls=controls,
        parity=nominal,nominal_parity_verification=replayed_parity,**seed_statistics(all_learned,controls),input_sha256=inputs,
        limitations=['Only3 training seeds on one training fixture; not multi-scene learning or significance evidence.',
            'Population SD is across3 seed means, never18 correlated fixture episodes.',
            'Shared nominal six rows reused once; old ESN/MLP have no3-seed uncertainty estimate.',
            'Waypoint RMSE has controller-dependent reference; see stages, rod exposure and all task/strict failures.',
            'Final-point and last6s diagnostics are distinct; safety-short rows are retained and not extrapolated.'])


def markdown(report):
    lines=['# 配对PPO三训练seed：同六fixture部署','',
        '新24条learned和1条nominalparity重新读取raw；旧12条learned及6条共享nominal复用固定hash审计。42条独特性能记录，额外parity不进均值；另列旧zero7六条作直接动作消融。', '',
        '先对每个训练seed的六fixture求均值，再描述三个seed均值的离散程度。失败始终计入分母6；不把18fixture当18独立训练重复。', '',
        '| 模式 | 训练seed | task /6 | strict /6 | waypoint RMSE mm | 峰矩 Nm | 峰速 m/s | 末帧距共同目标 mm | 末6秒共同目标RMSE mm |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for mode,seed_rows in report['by_training_seed'].items():
        for seed,row in seed_rows.items():
            tail='缺失（含安全短回合）' if row['last6s_goal_rmse_mm'] is None else f"{row['last6s_goal_rmse_mm']['mean']:.4f}"
            lines.append(f"| {mode} | {seed} | {row['task']} | {row['strict']} | {row['waypoint_rmse_mm']['mean']:.4f} | {row['actual_peak_torque_nm']['mean']:.4f} | {row['substep_peak_speed_mps']['mean']:.6f} | {row['final_goal_distance_mm']['mean']:.4f} | {tail} |")
    lines+=['','| 模式 | 三seed waypoint均值 ± SD mm | 峰矩均值 ± SD Nm | 峰速均值 ± SD m/s | task率均值 ± SD | strict率均值 ± SD |',
        '|---|---:|---:|---:|---:|---:|']
    for mode,row in report['across_training_seeds'].items():
        values=[f"{row[k]['mean']:.6f} ± {row[k]['std_population']:.6f}" for k in ('waypoint_rmse_mm','actual_peak_torque_nm','substep_peak_speed_mps','task_rate','strict_rate')]
        lines.append('| '+mode+' | '+' | '.join(values)+' |')
    lines+=['','SD是三个训练seed均值的总体标准差；仅描述小预算复验，不宣称显著性、收敛或泛化。共享nominal无独立训练seed，旧ESN/MLP单模型不赋予此SD。','','## 全部learned回合与失败','',
        '| 模式 | 训练seed | fixture | task/strict | stage | 实际s | 杆触发/接触s | task失败项 | 接触/上游失败项 |',
        '|---|---:|---:|---|---:|---:|---|---|---|']
    for row in sorted(report['rows'],key=lambda r:(r['training_seed'],r['method'],r['fixture']['seed'])):
        diagnosis=row['diagnosis']
        lines.append(f"| {row['method']} | {row['training_seed']} | {row['fixture']['seed']} | {row['task_success']}/{row['strict_success']} | {row['final_stage']} | {row['actual_duration_s']:.2f} | {row['fixture_triggered']}/{row['rod_contact_s']:.6f} | {'；'.join(diagnosis['task_failure_reasons']) or '通过'} | {'；'.join(diagnosis['contact_failure_reasons']) or '接触子门通过'} |")
    lines+=['','parameter6逐fixture相对训练nominal、direct7相对旧zero7的差值，以及每seed先聚合的差值保存在JSON。不同阶段及触杆曝光不能仅以低waypoint误差比较。共同末帧距离与绝对(18,24]s150帧RMSE不可混为一个指标；任何安全短回合均保留，末6秒量不补造。','',
        f"旧报告SHA256 `{report['old_report_sha256']}`；新plan SHA256 `{report['plan_sha256']}`。{len(report['input_sha256'])}项输入/工具hash保存在JSON。"]
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','old-report','old-archive','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();json_path=args.output.with_suffix('.json');md_path=args.output.with_suffix('.md')
    require(not json_path.exists() and not md_path.exists(),'Fresh report outputs required')
    report=audit(args.archive.resolve(),args.old_report.resolve(),args.old_archive.resolve())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with json_path.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False);stream.write('\n')
    with md_path.open('x') as stream:stream.write(markdown(report))
    print(json.dumps(dict(passed=True,new_learned_raw=24,training_seeds=3,unique_performance_rows=42,output=str(json_path))))


if __name__=='__main__':main()
