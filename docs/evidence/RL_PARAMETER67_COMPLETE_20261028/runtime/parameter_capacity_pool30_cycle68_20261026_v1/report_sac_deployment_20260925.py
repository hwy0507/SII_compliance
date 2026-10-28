"""Independently read SAC12 raw, verify one zero7 parity, reuse pinned zero six."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'scripts')]
import prepare_sac_deployment_20260925 as prep
import run_sac_deployment_20260925 as driver
import run_paired_six_fixture_deployment_20260924 as physics
import report_paired_six_fixture_20260924 as metrics
from audit_paired_transitions_20260924 import read,require,exact
from canonical48_sac_deployment_20260925 import sha


def summarize(rows,controls):
    require(len(rows)==12 and {(r['method'],r['fixture']['seed']) for r in rows}=={(b,f) for b in prep.BRANCHES for f in prep.FIXTURES},'Twelve unique learned results required')
    indexed={r['fixture']['seed']:r for r in controls};require(len(controls)==6 and set(indexed)==set(prep.FIXTURES),'Six unique zero controls required')
    summary=metrics.summarize(rows);paired=[]
    for branch in prep.BRANCHES:
        part=[r for r in rows if r['method']==branch]
        summary[branch].update(training_seeds=[20260923],fixture_denominator=6,
            final_goal_distance_mm=metrics.distribution([r['diagnosis']['final_goal_diagnostic']['trace_final_distance_3d_mm'] for r in part]))
        tail=[r['diagnosis']['final_goal_diagnostic']['last6s_absolute_window'] for r in part]
        summary[branch]['last6s_goal_rmse_mm']=metrics.distribution([x['rmse_3d_mm'] for x in tail]) if all(x is not None for x in tail) else None
        summary[branch]['dispersion_unit']='six fixtures of one training seed; never independent training-seed uncertainty'
        differences=[]
        for row in sorted(part,key=lambda r:r['fixture']['seed']):
            base=indexed[row['fixture']['seed']];a=row['physical'];b=base['physical']
            differences.append(dict(fixture_seed=row['fixture']['seed'],task_zero=base['task_success'],task_sac=row['task_success'],
                strict_zero=base['strict_success'],strict_sac=row['strict_success'],
                waypoint_rmse_mm=1000*(a['position_rmse_3d_m']-b['position_rmse_3d_m']),
                actual_peak_torque_nm=a['generalized_actuator_torque_peak_nm']-b['generalized_actuator_torque_peak_nm'],
                substep_peak_speed_mps=a['linear_speed_peak_mps']-b['linear_speed_peak_mps']))
        paired.append(dict(branch=branch,reference='zero7',fixture_deltas=differences,
            mean_deltas={k:float(np.mean([r[k] for r in differences])) for k in ('waypoint_rmse_mm','actual_peak_torque_nm','substep_peak_speed_mps')}))
    return summary,paired


def audit(archive,old_path,zero_report_path,matched_path,zero_archive):
    require(sha(old_path)==prep.OLD_HASH and sha(zero_report_path)==prep.ZERO_REPORT_HASH,'Historical report hash mismatch')
    previous=read(old_path);zero_report=read(zero_report_path);require(sha(matched_path)==zero_report['old_report_sha256'],'Original matched lineage differs')
    plan=read(archive/'frozen_plan.json');complete=read(archive/'COMPLETE.json');final=read(archive/'FINAL_RESULT.json');execution=read(archive/'execution_manifest.json')
    require(not (archive/'FAILED.json').exists() and not (zero_archive/'FAILED.json').exists(),'FAILED execution cannot publish complete results')
    require(complete['status']=='complete' and complete['algorithm']=='standard SAC' and (complete['episodes'],complete['learned_episodes'],complete['parity_episodes'])==(13,12,1) and complete['source_unchanged'],'Incomplete SAC13')
    require(sha(archive/'frozen_plan.json')==complete['plan_sha256']==execution['plan_sha256']==final['plan_sha256'],'Plan/execution binding differs')
    require(final['planned_episodes']==13 and final['execution_errors']==0,'Execution errors are not task failure samples')
    require(plan['old_report_sha256']==prep.OLD_HASH and plan['zero_report_sha256']==prep.ZERO_REPORT_HASH and plan['matched_report_sha256']==sha(matched_path),'Wrong control lineage')
    prep.matrix_keys(plan['jobs']);prep.matrix_keys(final['rows'])
    inputs={str(p):sha(p) for p in (old_path,zero_report_path,matched_path,archive/'frozen_plan.json',archive/'COMPLETE.json',archive/'FINAL_RESULT.json',archive/'execution_manifest.json',Path(__file__))}
    require(execution['source_sha256']==plan['source_sha256'] and execution['driver_sha256']==plan['source_sha256']['tools/run_sac_deployment_20260925.py'],'Executed source differs')
    for module in (prep,driver,physics,metrics):
        name=str(Path(module.__file__).resolve().relative_to(ROOT));require(sha(module.__file__)==plan['source_sha256'][name],'Checker differs from executed snapshot')
    require(sha(__file__)==plan['source_sha256']['tools/report_sac_deployment_20260925.py'],'Report source differs')
    for name,value in plan['source_sha256'].items():
        path=(archive/'source_snapshot'/name).resolve();require(path.is_relative_to((archive/'source_snapshot').resolve()) and sha(path)==value,'Archived source drift');inputs[str(path)]=value
    require(sha(archive/'deployment_protocol.md')==plan['protocol_sha256'],'Frozen protocol differs');inputs[str(archive/'deployment_protocol.md')]=plan['protocol_sha256']
    # All previously bound old zero files are checked, with a single explicit
    # remote-root to local-archive mapping. Their metric values are reused.
    zero_origin=Path(plan['zero_archive']);bound_zero=0
    for name,value in plan['input_sha256'].items():
        if Path(name).is_relative_to(zero_origin):
            mapped=zero_archive/Path(name).relative_to(zero_origin);require(sha(mapped)==value,'Old zero artifact drift');inputs[str(mapped)]=value;bound_zero+=1
    require(bound_zero>=6*7,'Missing complete zero-control input binding')
    old_rows={(r['method'],r['fixture']['seed']):r for r in previous['old_eight_method_rows']}
    controls=[old_rows[('zero',f)] for f in prep.FIXTURES]
    planned={(j['method'],j['fixture']['seed']):j for j in plan['jobs']}
    construct_goal=metrics.goal_constructor(archive/'source_snapshot/scripts');rows=[];parity_row=None
    for original in final['rows']:
        method,fixture=original['method'],original['fixture']['seed'];job=planned[(method,fixture)];folder=archive/method/str(fixture)
        require(read(folder/'command.json')==job and all(original[k]==v for k,v in job.items()),'Archived command differs from plan')
        require(read(folder/'result.json')==original and 'execution_error' not in original,'Per-job aggregate mismatch')
        for name,value in original['artifact_sha256'].items():
            path=(folder/name).resolve();require(path.is_relative_to(folder.resolve()) and sha(path)==value,'New raw artifact changed');inputs[str(path)]=value
        inputs[str(folder/'result.json')]=sha(folder/'result.json')
        stem=folder/'rollout/rollout';result=read(stem.with_suffix('.json'));model=sha(stem.with_suffix('.mjb'))
        require(sha(stem.with_suffix('.json'))==original['result_sha256'],'New result hash differs')
        require(job['fixture']==old_rows[('zero',fixture)]['fixture'] and job['reference_result_sha256']==old_rows[('vmc',fixture)]['result_sha256'],'Original fixture identity differs')
        require(model==job['expected_mjb_sha256']==original['model_mjb_sha256']==old_rows[('zero',fixture)]['model_mjb_sha256'],'Fixture MJB differs')
        reference=zero_archive/'zero'/str(fixture)/'rollout/rollout';reference_result=read(reference.with_suffix('.json'))
        require(sha(reference.with_suffix('.json'))==old_rows[('zero',fixture)]['result_sha256'],'Control result hash differs')
        for field in ('scene','controller_6d_config','experiment_contract','simulation_timestep_s','source_sha256'):require(result[field]==reference_result[field],'Core physical configuration differs: '+field)
        for name,value in result['source_sha256'].items():require(plan['source_sha256'].get('scripts/'+name)==value,'Result source differs')
        require(not result['teacher_called'] and result['student_mixture']==0. and result['contract']=='proprio48_action7_6d_v1','Pure canonical48 contract differs')
        physical=read(folder/'metrics/episode_0/substep_metrics.json');measurement=read(folder/'metrics/audit_manifest.json')
        require(physical==original['physical'] and measurement['enabled'] and measurement['error'] is None and measurement['episodes']==[physical],'Measurement summary differs')
        for name,value in measurement['source_sha256'].items():require(plan['source_sha256'].get('scripts/'+name)==value,'Measurement source differs')
        raw_audit=physics.physical_raw_audit(folder/'metrics/episode_0/substep_metrics.npz',physical,result['duration_s'])
        for path in folder.rglob('*.npz'):
            require(str(path.relative_to(folder)) in original['artifact_sha256'],'Unbound NPZ')
            with np.load(path,allow_pickle=False) as data:require(all(np.isfinite(data[k]).all() for k in data.files if data[k].dtype.kind in 'bfciu'),'Nonfinite raw')
        goal=construct_goal(json.loads(job['environment']['PANEL_CONFIG']));exact(goal,previous['common_final_task_goal_m'],'Common final target')
        with np.load(stem.with_suffix('.npz'),allow_pickle=False) as trace,np.load(reference.with_suffix('.npz'),allow_pickle=False) as control:
            count=len(trace['time']);require(1<=count<=600 and (count==600 or result['invalid_physics']),'Unexplained short rollout')
            require(np.allclose(trace['time'],.04*np.arange(1,count+1),rtol=0,atol=1e-8) and abs(result['duration_s']-.04*count)<1e-6,'Actual25Hz timing differs')
            require(trace['observation'].shape==(count,48) and trace['action'].shape==(count,7),'Wrong canonical dimensions')
            exact(trace['observation'][0],control['observation'][0],'Original initial48 state')
            require(int(trace['stage'][-1])==result['final_stage'],'Final stage differs')
            if np.any(trace['stage']==3):require(np.all(trace['target'][trace['stage']==3]==goal),'Lift target changed')
            diagnosis=metrics.failure_diagnostics(result,trace,goal);stages=dict(Counter(str(int(x)) for x in trace['stage']))
            if method=='zero7':require(count==600 and not np.any(trace['action']),'Parity was not full zero7')
            else:
                with np.load(folder/'rollout/paired_policy_trace.npz',allow_pickle=False) as policy:
                    exact(policy['observation'],trace['observation'],'SAC raw48 alignment');exact(policy['execution_action'],trace['action'],'SAC actual action7 alignment')
                    require(policy['observation'].dtype==np.float64 and policy['policy_action'].shape==(count,7),'SAC raw/request contract differs')
                    require(np.all(policy['policy_action']>=np.array([0]+[-1]*6)) and np.all(policy['policy_action']<=1),'SAC request outside Box')
                    for field in ('log_scale','stiffness','damping'):require(policy[field].shape==(count,6),'SAC backend trace shape differs')
        require(bool(result['success'])==original['task_success'],'Original task result differs')
        deployment=None
        if method in prep.BRANCHES:
            require(diagnosis['strict_success_recomputed']==original['strict_success'],'Original strict gates differ')
            deployment=read(stem.with_suffix('.paired_deployment.json'));driver.validate_metadata(deployment,plan['training'][method],job)
        contacts=result['panel_audit']['contacts']
        row=dict(method=method,algorithm='standard SAC' if method in prep.BRANCHES else 'zero action7',training_seed=20260923 if method in prep.BRANCHES else None,
            fixture=job['fixture'],task_success=bool(result['success']),strict_success=diagnosis['strict_success_recomputed'],physical=physical,raw_metric_audit=raw_audit,
            result_sha256=original['result_sha256'],model_mjb_sha256=model,completed_24s=count==600,safety_terminated_early=count<600,actual_duration_s=result['duration_s'],
            final_stage=result['final_stage'],stage_counts=stages,fixture_triggered=result['fixture_triggered'],fixture_trigger_time_s=result['fixture_trigger_time_s'],
            rod_contact_s=contacts['push_rod_geom']['duration_s'],diagnosis=diagnosis,deployment=deployment,archive_job=str(folder),source='new raw recomputed')
        if method=='zero7':parity_row=row
        else:rows.append(row)
    require(len(rows)==12 and parity_row is not None,'Wrong learned/parity denominator')
    parity_path=archive/'ZERO7_REUSE_PARITY.json';saved=read(parity_path)
    require(sha(parity_path)==complete['zero7_reuse_parity_sha256'] and saved['passed'] and saved['zero_report_sha256']==prep.ZERO_REPORT_HASH,'Missing bound zero7 proof')
    parity=prep.zero_parity(zero_archive/'zero/9400',archive/'zero7/9400')
    require(parity['arrays']==saved['arrays'] and parity['model_mjb_sha256']==saved['model_mjb_sha256'],'Exact zero7 parity did not reproduce')
    inputs[str(parity_path)]=sha(parity_path);inputs.update(parity['input_sha256'])
    summary,paired=summarize(rows,controls)
    return dict(passed=True,algorithm='standard SAC',training_seeds=[20260923],new_learned_raw_recomputed=12,zero7_parity_raw_recomputed=1,
        reused_zero7_performance_rows=6,unique_learned_performance_rows=12,parity_excluded_from_performance=True,rows=rows,controls=controls,summary=summary,
        paired_learning_deltas=paired,parity=parity_row,zero7_parity_verification=parity,training=plan['training'],input_sha256=inputs,
        zero7_six_fixture_preparation_reaudits=plan['zero7_six_fixture_preparation_reaudits'],
        old_report_sha256=prep.OLD_HASH,zero_report_sha256=prep.ZERO_REPORT_HASH,matched_report_sha256=sha(matched_path),plan_sha256=sha(archive/'frozen_plan.json'),
        limitations=['Single SAC training seed, no training-seed SD or significance claim.',
            'demo_prefill uses8192 online+600 additional train-only demo=8792 total, zero offline updates; online_only total8192.',
            'Each SAC branch has8092 actor/critic/entropy updates, unlike PPO384; not equal network/gradient/data computation.',
            'Standard SAC adaptations, not RLPD or full paper reproduction; fixed final checkpoint, no reselection.',
            'Waypoint references depend on reached stage; failures and rod exposure accompany all errors.',
            'Final-point distance and absolute(18,24]s RMSE differ; safety-short tail absent, never extrapolated.',
            'Report stage recomputes new12 and parity raw; preparation separately recomputed old six zero7 raw/gates against pinned result/metric summaries then bound all files.',
            'Old matched report did not preserve all six zero7 NPZ hashes; do not claim retrospective original-byte identity for those unrecorded hashes.',
            'Historical ESN/MLP/classical/PPO remain pinned prior audits.'])


def markdown(report):
    lines=['# Standard SAC两分支：原六fixture部署','',
        '两模型均固定seed20260923/final8192/8092。新增12条性能结果，每branch分母6；另1条zero7/9400仅验证exact parity，不进均值。旧zero7六条是动作学习主对照。','',
        '旧6条zero7在本次prepare已按固定结果/指标摘要重算50µs raw和门，报告阶段hash绑定复用，不计新增物理。旧matched报告未保存全部六条NPZ历史hash，不能据此声称未记录的原始字节可追溯exact。','',
        'online_only总数据8192；demo_prefill为8192在线+600 train-only示范=8792，无离线更新。每模型actor/critic/entropy各8092步，与PPO384更新不等计算量；不称RLPD或论文完整复现。','',
        '| 分支 | task/6 | strict/6 | waypoint RMSE mm | 实际峰矩 Nm | 末端峰速 m/s | 末帧距共同目标 mm | 末6秒共同目标RMSE mm |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for branch,s in report['summary'].items():
        tail='缺失（含安全短回合）' if s['last6s_goal_rmse_mm'] is None else f"{s['last6s_goal_rmse_mm']['mean']:.4f}"
        lines.append(f"| {branch} | {s['task']} | {s['strict']} | {s['waypoint_rmse_mm']['mean']:.4f} | {s['actual_peak_torque_nm']['mean']:.4f} | {s['substep_peak_speed_mps']['mean']:.6f} | {s['final_goal_distance_mm']['mean']:.4f} | {tail} |")
    lines+=['','单训练seed，不报告训练seed标准差。waypoint依赖状态机阶段，不能用低误差单独判断完成任务。共同末帧距离与绝对(18,24]s的150帧RMSE分列。','',
        '| 分支 | fixture | task/strict | stage | 实际s | 杆触发/接触s | task失败项 | 接触/上游失败项 |','|---|---:|---|---:|---:|---|---|---|']
    for row in sorted(report['rows'],key=lambda r:(r['method'],r['fixture']['seed'])):
        d=row['diagnosis'];lines.append(f"| {row['method']} | {row['fixture']['seed']} | {row['task_success']}/{row['strict_success']} | {row['final_stage']} | {row['actual_duration_s']:.2f} | {row['fixture_triggered']}/{row['rod_contact_s']:.6f} | {'；'.join(d['task_failure_reasons']) or '通过'} | {'；'.join(d['contact_failure_reasons']) or '接触子门通过'} |")
    lines+=['','全部逐fixture raw指标、zero7配对差值、门诊断、源文件与输入hash见同名JSON。失败均保留，不重试、不删样本、不换checkpoint。',f"计划SHA256 `{report['plan_sha256']}`；校验输入 {len(report['input_sha256'])} 项。"]
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','old-report','zero-report','matched-report','zero-archive','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();json_path=args.output.with_suffix('.json');md_path=args.output.with_suffix('.md');require(not json_path.exists() and not md_path.exists(),'Fresh report outputs required')
    result=audit(args.archive.resolve(),args.old_report.resolve(),args.zero_report.resolve(),args.matched_report.resolve(),args.zero_archive.resolve())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with json_path.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    with md_path.open('x') as stream:stream.write(markdown(result))
    print(json.dumps(dict(passed=True,learned_raw=12,parity_raw=1,output=str(json_path))))


if __name__=='__main__':main()
