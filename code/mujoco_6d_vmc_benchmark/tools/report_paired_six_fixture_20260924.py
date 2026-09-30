"""Offline report for complete18-job paired deployment plus frozen old8 methods.

All joins use exact (method, seed), fixture content, and compiled-model hash.
Only report artifacts are written; no model selection or physics execution.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'scripts')]
import run_paired_six_fixture_deployment_20260924 as driver
from audit_paired_transitions_20260924 import exact,require,read
from canonical48_paired_deployment_20260924 import sha

NEW=('parameter6','direct7','nominal_train_vmc')
OLD=('impedance_k900_z1.2','admittance_k150_z0.7','vmc','mlp','esn','ppo8192','zero','ppo_potential8192')
SEEDS=range(9400,9406)

TASK_LABELS=dict(object_lift_over_100mm='物体抬升≤100mm',final_object_speed_below_20mmps='末段物体速度≥20mm/s或不可计算',
    endpoint_below_15mm='末10帧当前waypoint误差≥15mm',valid_physics='原物理有效性失败',
    no_task_upstream_contact='原task主审计上游接触',final_stage_3='未到loaded-lift阶段3',cup_safe='原cup_safe失败')
CONTACT_LABELS=dict(rod_contact_over_0p3s='杆接触≤0.3s',rod_released_over_2s='杆释放间隔≤2s或无杆接触',
    final_rod_gap_over_2mm='末端杆间隙≤2mm',penetration_below_0p2mm='最大非目标物穿透≥0.2mm',
    no_rod_upstream_contact='杆发生上游接触',no_external_upstream_contact='任意非目标外物发生上游接触')


def goal_constructor(source):
    """Extract only archived pure goal construction; never import a simulator."""
    layout=ast.parse((source/'primitive_contact_scene_v7_20260917.py').read_text())
    task=ast.parse((source/'run_primitive_teacher_v7_20260917.py').read_text())
    panel=ast.parse((source/'run_panel_push_20260920.py').read_text())
    layout_function=next(n for n in layout.body if isinstance(n,ast.FunctionDef) and n.name=='task_layout')
    task_class=next(n for n in task.body if isinstance(n,ast.ClassDef) and n.name=='BlindTask')
    initializer=next(n for n in task_class.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
    namespace={'np':np}
    exec(compile(ast.Module(body=[layout_function,initializer],type_ignores=[]),'archived_pure_goal','exec'),namespace)
    assignments={}
    for n in ast.walk(panel):
        if isinstance(n,ast.Assign) and len(n.targets)==1 and ast.unparse(n.targets[0]) in ('task.goals[3][2]','task.goals[3][0]'):
            key=ast.unparse(n.targets[0]);require(key not in assignments,'Ambiguous archived goal assignment');assignments[key]=n.value
    require(len(assignments)==2,'Missing archived final goal overrides')
    def construct(config):
        initial,grasp=namespace['task_layout'](SimpleNamespace(kind='push'))
        obj=SimpleNamespace(direction=lambda:np.array([0.,0.,1.]))
        namespace['__init__'](obj,initial,grasp,np.eye(3),None,None,None)
        goal=obj.goals[3].copy()
        for axis in (2,0):
            if axis==0 and 'lift_goal_x' not in config:continue
            goal[axis]=eval(compile(ast.Expression(assignments[f'task.goals[3][{axis}]']),'archived_panel_goal','eval'),{'PANEL':config,'float':float})
        return goal
    return construct


def failure_diagnostics(result,trace,final_goal):
    """Reproduce existing push task/panel/strict gates; add non-gating distances."""
    require(result['arguments']['scene']=='push','Failure decomposition only covers original push task')
    position,target,objects=trace['position'],trace['target'],trace['object_position']
    error=np.linalg.norm(position-target,axis=1)
    endpoint=float(np.mean(error[-10:]));lift=float(objects[-1,2]-.425)
    motion=float(np.max(np.linalg.norm(np.diff(objects[-10:],axis=0)/.04,axis=1))) if len(objects)>1 else None
    require(np.isclose(endpoint,result['endpoint_error_m'],rtol=0,atol=1e-12) and np.isclose(lift,result['lift_m'],rtol=0,atol=1e-12),'Original endpoint/lift differs from raw trace')
    task=dict(object_lift_over_100mm=lift>.10,final_object_speed_below_20mmps=motion is not None and motion<.02,
        endpoint_below_15mm=endpoint<.015,valid_physics=not result['invalid_physics'],
        no_task_upstream_contact=not result['upstream_contact'],final_stage_3=result['final_stage']==3,cup_safe=bool(result['cup_safe']))
    require(all(task.values())==result['success'],'Original task gate reconstruction failed')
    require(bool(task['object_lift_over_100mm'] and task['final_object_speed_below_20mmps'])==result['grasp_lift_success'],'Original grasp_lift_success reconstruction failed')
    contacts=result['panel_audit']['contacts'];rod=contacts['push_rod_geom']
    external={n:c for n,c in contacts.items() if n!='target_object_geom'}
    peak_name=max(external,key=lambda n:external[n]['max_penetration_m']);penetration=external[peak_name]['max_penetration_m']
    release=None if rod['last_s'] is None else float(result['arguments']['duration']-rod['last_s'])
    gap=float(result['panel_audit']['final_rod_gap_m'])
    panel=dict(task=bool(result['success']),rod_contact_over_0p3s=rod['duration_s']>.3,
        rod_released_over_2s=release is not None and release>2.,final_rod_gap_over_2mm=gap>.002,
        penetration_below_0p2mm=penetration<.0002,no_rod_upstream_contact=not bool(set(rod['bodies']) & driver.UPSTREAM))
    require(all(panel.values())==result['accepted_panel_demo'],'Original panel gate reconstruction failed')
    no_external_upstream=not any(set(c['bodies']) & driver.UPSTREAM for c in external.values())
    strict=dict(panel,no_external_upstream_contact=no_external_upstream)
    delta=1000*(position[-1]-final_goal)
    mask=(trace['time']>18.+1e-8)&(trace['time']<=24.+1e-8)
    tail=None
    if len(position)==600:
        require(mask.sum()==150,'Final6s absolute window is incomplete')
        e=1000*(position[mask]-final_goal)
        tail=dict(samples=150,rmse_3d_mm=float(np.sqrt(np.mean(np.sum(e**2,axis=1)))),
            rmse_xy_mm=float(np.sqrt(np.mean(np.sum(e[:,:2]**2,axis=1)))),rmse_z_mm=float(np.sqrt(np.mean(e[:,2]**2))))
    return dict(raw_flags={k:result[k] for k in ('success','grasp_lift_success','invalid_physics','upstream_contact','cup_safe','cup_stable','cup_support_contact','real_contact','accepted_panel_demo')},
        task_components=task,panel_components=panel,strict_components=strict,strict_success_recomputed=all(strict.values()),
        task_failure_reasons=[TASK_LABELS[k] for k,v in task.items() if not v],
        contact_failure_reasons=[CONTACT_LABELS[k] for k,v in strict.items() if k!='task' and not v],
        values=dict(object_lift_mm=1000*lift,final_object_speed_mmps=None if motion is None else 1000*motion,
            last10_current_waypoint_mean_error_mm=1000*endpoint,rod_duration_s=rod['duration_s'],rod_last_contact_s=rod['last_s'],
            rod_release_interval_to_requested_end_s=release,requested_episode_duration_s=result['arguments']['duration'],
            final_rod_gap_mm=1000*gap,max_external_penetration_mm=1000*penetration,
            penetration_margin_um=200-1e6*penetration,peak_penetration_obstacle=peak_name,
            primary_contact_duration_s=result['contact']['duration_s'],final_bilateral_grasp=result['panel_audit']['final_bilateral_grasp']),
        final_goal_diagnostic=dict(goal_m=final_goal.tolist(),trace_final_residual_xyz_mm=delta.tolist(),
            trace_final_distance_3d_mm=float(np.linalg.norm(delta)),trace_final_distance_xy_mm=float(np.linalg.norm(delta[:2])),
            trace_final_distance_z_mm=float(abs(delta[2])),last6s_absolute_window=tail,
            non_gating=True,position_semantics='Archived25Hz live d.xpos, not newly reconstructed physical substep position'))


def index_rows(rows,methods):
    keys=[(r['method'],r['fixture']['seed']) for r in rows]
    expected={(m,s) for m in methods for s in SEEDS}
    require(len(keys)==len(set(keys)) and set(keys)==expected,'Missing/duplicate/wrong method-fixture matrix')
    require(all('execution_error' not in r for r in rows),'Execution errors cannot form a completed matrix')
    return dict(zip(keys,rows))


def distribution(values):
    a=np.asarray(values,dtype=float)
    require(np.isfinite(a).all(),'Nonfinite summary value')
    return dict(values=a.tolist(),mean=float(a.mean()),std_population=float(a.std()),minimum=float(a.min()),maximum=float(a.max()))


def summarize(rows):
    answer={}
    for method in dict.fromkeys(r['method'] for r in rows):
        part=sorted([r for r in rows if r['method']==method],key=lambda r:r['fixture']['seed'])
        require(len(part)==6,'Expected six fixtures per method')
        answer[method]=dict(episodes=6,task=sum(r['task_success'] for r in part),strict=sum(r['strict_success'] for r in part),
            full24=sum(r['physical']['samples']*r['physical']['timestep_s']>=23.99 for r in part),
            waypoint_rmse_mm=distribution([1000*r['physical']['position_rmse_3d_m'] for r in part]),
            actual_peak_torque_nm=distribution([r['physical']['generalized_actuator_torque_peak_nm'] for r in part]),
            substep_peak_speed_mps=distribution([r['physical']['linear_speed_peak_mps'] for r in part]))
        if all('non_target_external_contacts' in r for r in part):
            answer[method].update(final_stages=dict(Counter(str(r['final_stage']) for r in part)),
                rod_triggered=sum(r['fixture_triggered'] for r in part),rod_contact=sum(r['rod_contact_s']>0 for r in part),
                any_non_target_external_contact=sum(bool(r['non_target_external_contacts']) for r in part),
                rod_duration_s=distribution([r['rod_contact_s'] for r in part]))
    return answer


def audit(archive,old_report,old_hash):
    require(not (archive/'FAILED.json').exists(),'FAILED and COMPLETE cannot both be accepted')
    complete=read(archive/'COMPLETE.json');final=read(archive/'FINAL_RESULT.json')
    execution=read(archive/'execution_manifest.json');plan=read(archive/'frozen_plan.json')
    require(complete['status']=='complete' and complete['episodes']==18 and complete['source_unchanged'],'Incomplete deployment')
    plan_hash=sha(archive/'frozen_plan.json')
    require(plan_hash==complete['plan_sha256']==final['plan_sha256']==execution['plan_sha256'],'Plan hash mismatch')
    require(final['execution_errors']==0,'Execution errors in completed output')
    require(sha(Path(driver.__file__))==execution['driver_sha256'],'Metric checker source differs from executed frozen driver')
    require(sha(old_report)==old_hash,'Old8-method report is not the explicitly pinned artifact')
    old=read(old_report)
    require(old['all_fixture_mjb_equal'] and old['all_new_initial_actor_states_exact'],'Old report lacks paired deployment audit')
    previous=index_rows(old['rows'],OLD);new=index_rows(final['rows'],NEW);planned=index_rows(plan['jobs'],NEW)
    inputs={str(p):sha(p) for p in (old_report,archive/'COMPLETE.json',archive/'FINAL_RESULT.json',archive/'execution_manifest.json',archive/'frozen_plan.json',Path(__file__),Path(driver.__file__))}
    for name,value in execution['source_sha256'].items():
        p=(archive/'source_snapshot'/name).resolve()
        require(p.is_relative_to((archive/'source_snapshot').resolve()) and sha(p)==value,'Copied source snapshot drift')
        inputs[str(p)]=value
    require(all(execution['source_sha256'].get(k)==v for k,v in plan['source_sha256'].items()),'Execution source set does not cover frozen plan')
    require(sha(archive/'deployment_protocol.md')==plan['protocol_sha256'],'Archived protocol drift')
    inputs[str(archive/'deployment_protocol.md')]=plan['protocol_sha256']
    construct_goal=goal_constructor(archive/'source_snapshot/scripts')
    common_goal=None
    rows=[];initial_by_seed={}
    for method in NEW:
        for seed in SEEDS:
            original=new[(method,seed)];command=planned[(method,seed)]
            job=archive/method/str(seed)
            require(read(job/'command.json')==command,'Archived command differs from plan')
            require(all(original[k]==v for k,v in command.items()),'Final row does not describe frozen job')
            require(read(job/'result.json')==original,'Aggregate/per-job row mismatch')
            require(original['initial_actor_observation_exact'] and original['policy_trace_exact'],'Driver did not verify original actor/control alignment')
            require(original['fixture']==previous[('vmc',seed)]['fixture'],'New and old fixture content differs')
            require(command['reference_result_sha256']==previous[('vmc',seed)]['result_sha256'],'Plan references a different original VMC fixture')
            for name,value in original['artifact_sha256'].items():
                p=(job/name).resolve()
                require(p.is_relative_to(job.resolve()) and sha(p)==value,'Raw deployment artifact hash mismatch')
                inputs[str(p)]=value
            inputs[str(job/'result.json')]=sha(job/'result.json')
            stem=job/'rollout/rollout'
            result=read(stem.with_suffix('.json'))
            final_goal=construct_goal(json.loads(command['environment']['PANEL_CONFIG']))
            if common_goal is None:common_goal=final_goal.copy()
            else:exact(final_goal,common_goal,'Common preexisting final task goal')
            require(sha(stem.with_suffix('.json'))==original['result_sha256'],'Raw result hash mismatch')
            model=sha(stem.with_suffix('.mjb'))
            require(model==original['model_mjb_sha256']==command['expected_mjb_sha256'],'Raw MJB differs from frozen plan')
            require(all(previous[(m,seed)]['model_mjb_sha256']==model for m in OLD),'Old and new compiled models differ within fixture')
            for name,value in result['source_sha256'].items():
                require(plan['source_sha256'].get('scripts/'+name)==value,'Raw physics source differs from frozen plan')
            physical=read(job/'metrics/episode_0/substep_metrics.json')
            metrics=read(job/'metrics/audit_manifest.json')
            require(physical==original['physical'] and metrics['enabled'] and metrics['error'] is None and metrics['episodes']==[physical],'Physical summary/manifest mismatch')
            for name,value in metrics['source_sha256'].items():
                require(plan['source_sha256'].get('scripts/'+name)==value,'Physical instrumentation source drift')
            recomputed=driver.physical_raw_audit(job/'metrics/episode_0/substep_metrics.npz',physical,result['duration_s'])
            for file in job.rglob('*.npz'):
                require(str(file.relative_to(job)) in original['artifact_sha256'],'Unbound NPZ data file')
                with np.load(file,allow_pickle=False) as data:
                    require(all(np.isfinite(data[k]).all() for k in data.files if data[k].dtype.kind in 'fciu'),'Nonfinite raw array')
            with np.load(stem.with_suffix('.npz'),allow_pickle=False) as trace,np.load(job/'rollout/paired_policy_trace.npz',allow_pickle=False) as policy:
                count=len(trace['time'])
                require(1<=count<=600 and trace['observation'].shape==(count,48) and trace['action'].shape==(count,7),'Invalid25Hz trace')
                require(np.allclose(trace['time'],np.arange(1,count+1)*.04,rtol=0,atol=1e-8),'Invalid25Hz time grid')
                require(count==600 or result['invalid_physics'],'Unexplained short episode')
                require(abs(count*.04-result['duration_s'])<1e-6,'Recorded duration differs from actual time window')
                exact(policy['observation'],trace['observation'],'Policy raw48 alignment')
                exact(policy['execution_action'],trace['action'],'Policy action7 alignment')
                if seed in initial_by_seed:exact(trace['observation'][0],initial_by_seed[seed],'New methods initial48D equality')
                else:initial_by_seed[seed]=trace['observation'][0].copy()
                stages=dict(Counter(str(int(s)) for s in trace['stage']))
                require(int(trace['stage'][-1])==result['final_stage'],'Final stage differs from raw trace')
                if np.any(trace['stage']==3):
                    require(np.all(trace['target'][trace['stage']==3]==final_goal),'Visited final-stage target differs from archived constructor')
                diagnosis=failure_diagnostics(result,trace,final_goal)
            branch='direct7' if method=='direct7' else 'parameter6'
            deployment=read(stem.with_suffix('.paired_deployment.json'))
            for key in ('checkpoint_sha256','normalizer_sha256'):
                require(deployment[key]==plan['training'][branch][key],'Model/normalizer lineage differs')
            require(deployment['mode']==method and deployment['training_manifest_sha256']==plan['training'][branch]['manifest_sha256'],'Wrong deployment branch')
            contacts=result['panel_audit']['contacts']
            external={n:c for n,c in contacts.items() if n!='target_object_geom'}
            upstream=any(set(c['bodies']) & driver.UPSTREAM for c in external.values())
            task=bool(result['success']);strict=bool(result['accepted_panel_demo'] and not upstream)
            require(task==original['task_success'] and strict==original['strict_success'],'Task/strict outcome drift')
            require(diagnosis['strict_success_recomputed']==strict,'Detailed strict gate differs from original outcome')
            for key,target in (('tracking_rmse_substep_m','position_rmse_3d_m'),('actuator_torque_peak_nm','generalized_actuator_torque_peak_nm'),('linear_speed_peak_substep_mps','linear_speed_peak_mps')):
                require(original[key]==physical[target],'Reported physical metric drift')
            active={n:c for n,c in external.items() if c['duration_s']>0}
            rows.append(dict(method=method,fixture=original['fixture'],task_success=task,strict_success=strict,
                physical=physical,raw_metric_audit=recomputed,model_mjb_sha256=model,result_sha256=original['result_sha256'],
                completed_24s=count==600,safety_terminated_early=count<600,actual_duration_s=result['duration_s'],
                final_stage=result['final_stage'],stage_counts=stages,fixture_triggered=result['fixture_triggered'],
                fixture_trigger_time_s=result['fixture_trigger_time_s'],rod_contact_s=contacts['push_rod_geom']['duration_s'],
                rod_first_contact_s=contacts['push_rod_geom']['first_s'],non_target_external_contacts=active,
                deployment=deployment,diagnosis=diagnosis,source='new_paired_DGX_deployment',archive_job=str(job)))
    for method in NEW:
        part=[r for r in rows if r['method']==method]
        require(sum(r['task_success'] for r in part)==complete['task'][method] and sum(r['strict_success'] for r in part)==complete['gate'][method],'COMPLETE counts differ')
    require(sum(r['safety_terminated_early'] for r in rows)==complete['safety_short_episodes'],'Safety-short count mismatch')
    for seed in SEEDS:
        parameter=next(r for r in rows if r['method']=='parameter6' and r['fixture']['seed']==seed)
        nominal=next(r for r in rows if r['method']=='nominal_train_vmc' and r['fixture']['seed']==seed)
        require(parameter['deployment']['nominal_options']==nominal['deployment']['nominal_options'],'Nominal control changed adapter options')
        require(previous[('zero',seed)]['shared_configuration_equal'],'Oldzero lacks original shared-configuration audit')
    paired=[]
    indexed={(r['method'],r['fixture']['seed']):r for r in rows}
    for method,reference in (('parameter6','nominal_train_vmc'),('direct7','zero')):
        for seed in SEEDS:
            a=indexed[(method,seed)];b=indexed[(reference,seed)] if reference in NEW else previous[(reference,seed)]
            paired.append(dict(method=method,reference=reference,seed=seed,
                delta_waypoint_rmse_mm=1000*(a['physical']['position_rmse_3d_m']-b['physical']['position_rmse_3d_m']),
                delta_peak_torque_nm=a['physical']['generalized_actuator_torque_peak_nm']-b['physical']['generalized_actuator_torque_peak_nm'],
                delta_peak_speed_mps=a['physical']['linear_speed_peak_mps']-b['physical']['linear_speed_peak_mps'],
                task=[b['task_success'],a['task_success']],strict=[b['strict_success'],a['strict_success']],
                both_full24=a['completed_24s'] and b['physical']['samples']*b['physical']['timestep_s']>=23.99))
    combined=[previous[(m,s)] for m in OLD for s in SEEDS]+rows
    return dict(scope='Paired DGX8192 deployment diagnostic; all failures retained; no checkpoint selection',
        summary=summarize(rows),rows=rows,paired_learning_comparisons=paired,eleven_method_summary=summarize(combined),
        old_eight_method_rows=[previous[(m,s)] for m in OLD for s in SEEDS],old_report_sha256=old_hash,
        old_evidence_rule='Old48 rows are reused from pinned previously audited JSON, not re-audited from old raw by this tool',
        plan_sha256=plan_hash,complete=complete,all_new_raw_metrics_recomputed=True,input_sha256=inputs,
        all_new_original_gate_components_recomputed=True,common_final_task_goal_m=common_goal.tolist(),
        comparison_limits='Equal new RL interaction budget, different action dimensions/controller priors/memory; old PPO trained on local platform, all compared deployment episodes on DGX')


def markdown(report,eleven):
    lines=['# 同DGX配对RL与训练名义VMC：六条件结果','',
        '18条全部纳入，原raw子步误差/实际actuator矩/末端速度已独立复算；任务失败、strict失败和真实安全早停均保留。物理dt=50µs，表中各峰为每回合真实子步峰再对六条件取均值。','',
        '本次只重算新18条raw。旧48条从绑定SHA256的已审计JSON复用，没有在本次重新计算旧raw；可选11方法附表不能描述为66条全部重新审计。位置RMSE相对各策略状态机waypoint，不是共同时间连续目标，也不是共同最终目标距离。未到stage3时不能凭较低RMSE判断更优。','',
        '| 方法 | task | strict | waypoint RMSE均值 mm | 实际峰矩均值 Nm | 子步峰速均值 m/s | 完整24s |',
        '|---|---:|---:|---:|---:|---:|---:|']
    def row(method,r):
        return f"| {method} | {r['task']}/6 | {r['strict']}/6 | {r['waypoint_rmse_mm']['mean']:.4f} | {r['actual_peak_torque_nm']['mean']:.4f} | {r['substep_peak_speed_mps']['mean']:.6f} | {r['full24']}/6 |"
    lines += [row(m,r) for m,r in report['summary'].items()]
    lines += ['',
        'parameter6的学习增益应相对nominal_train_vmc判断：两者使用完全相同的训练名义options，后者从reset起持续zero6，并非旧fixture名义VMC。direct7的学习增益相对原zero7判断；本工具只复用明确固定的旧审计JSON中同fixture、同MJB且共同配置检查通过的zero行。逐fixture差值保存在JSON，不把不同阶段的小waypoint误差当任务成功。','',
        '| 方法 | final stage分布 | 杆触发 | 杆有力接触 | 任意非目标物外接触 | 杆接触时长范围 s |',
        '|---|---|---:|---:|---:|---:|']
    for m,r in report['summary'].items():
        d=r['rod_duration_s']
        lines.append(f"| {m} | {r['final_stages']} | {r['rod_triggered']}/6 | {r['rod_contact']}/6 | {r['any_non_target_external_contact']}/6 | {d['minimum']:.6f}—{d['maximum']:.6f} |")
    lines += ['', '有力接触沿用原审计>0.05N口径；非目标外接触包括桌面、护板和杆，排除抓取目标物。杆在loaded-lift阶段触发，未到阶段的策略可能没有实际经历杆扰动，即使其他外接触存在；因此名义相同fixture不等于实际相同扰动曝光。','',
        '| 方法 | seed | 时长 s | task/strict | final stage | 杆触发 | 杆时长 s | waypoint RMSE mm | 实际峰矩 Nm | 峰速 m/s | 非目标物外接触 |',
        '|---|---:|---:|---|---:|---|---:|---:|---:|---:|---|']
    for r in report['rows']:
        p=r['physical'];contacts='; '.join(f"{n}:{c['duration_s']:.4f}s" for n,c in r['non_target_external_contacts'].items()) or '无'
        lines.append(f"| {r['method']} | {r['fixture']['seed']} | {r['actual_duration_s']:.2f} | {r['task_success']}/{r['strict_success']} | {r['final_stage']} | {r['fixture_triggered']} | {r['rod_contact_s']:.6f} | {1000*p['position_rmse_3d_m']:.4f} | {p['generalized_actuator_torque_peak_nm']:.4f} | {p['linear_speed_peak_mps']:.6f} | {contacts} |")
    lines += ['', '## 逐回合任务失败解释：严格复算原门','',
        '原task要求物体抬升>100mm、最后10点物体速度峰<20mm/s、末10帧当前waypoint平均误差<15mm、物理有效、原主审计无上游接触、最终stage3及cup_safe。grasp_lift_success仅对应前两项。表中cup_safe等标志来自原JSON；cup_stable/cup_support_contact同时保存在JSON，但不把无杯场景的cup_support_contact=False另造为失败门。',
        f"最终目标残差使用冻结源码/原PANEL_CONFIG恢复的共同手端目标`{report['common_final_task_goal_m']}`m，仅作辅助解释，不替换waypoint主指标或任务门；没有抓物时手端接近目标也不能称任务完成。",'',
        '| 方法 | seed | grasp_lift | invalid / 原upstream / cup_safe | 抬升 mm | 末段物速 mm/s | 当前waypoint末10均误差 mm | trace末帧距最终目标 mm | 原task失败项 |',
        '|---|---:|---|---|---:|---:|---:|---:|---|']
    number=lambda v:'—' if v is None else f'{v:.6f}'
    for r in report['rows']:
        d=r['diagnosis'];v=d['values'];f=d['raw_flags']
        lines.append(f"| {r['method']} | {r['fixture']['seed']} | {f['grasp_lift_success']} | {f['invalid_physics']} / {f['upstream_contact']} / {f['cup_safe']} | {v['object_lift_mm']:.6f} | {number(v['final_object_speed_mmps'])} | {v['last10_current_waypoint_mean_error_mm']:.6f} | {d['final_goal_diagnostic']['trace_final_distance_3d_mm']:.6f} | {'；'.join(d['task_failure_reasons']) or '无，原task通过'} |")
    lines += ['',
        '| 方法 | seed | 杆时长 s | 原释放间隔 s | 最终杆间隙 mm | 最大外部穿透 mm | 穿透门余量 μm | 原接触/上游门失败项 |',
        '|---|---:|---:|---:|---:|---:|---:|---|']
    for r in report['rows']:
        d=r['diagnosis'];v=d['values']
        lines.append(f"| {r['method']} | {r['fixture']['seed']} | {v['rod_duration_s']:.6f} | {number(v['rod_release_interval_to_requested_end_s'])} | {v['final_rod_gap_mm']:.6f} | {v['max_external_penetration_mm']:.6f} | {v['penetration_margin_um']:+.3f} | {'；'.join(d['contact_failure_reasons']) or '无，接触子门通过（仍需task）'} |")
    lines += ['',
        '原panel门另要求杆时长>0.3s、计划结束时刻−杆末触>2s、最终杆间隙>2mm、所有非目标物最大穿透<0.2mm及杆无上游接触；原strict再要求所有非目标外物均无上游接触。释放间隔严格使用原代码的计划24s，即使安全提前终止也不改其公式；task中的物理失败仍阻止通过。穿透余量=200−峰深度(μm)，仅作连续解释，不放宽原门。',
        'JSON保留所有原布尔标志、逐项重算结果、失败项、峰穿透障碍、原主接触时长、最终双侧抓持，以及共同目标末帧XYZ残差；完整24s回合另外给出绝对(18,24]末6秒150帧诊断，短回合留空，不补造未来位置。以上均来自既有归档，没有新仿真。','']
    if eleven:
        lines += ['', '## 11方法附表：共同部署条件，训练来源不同','',
            '| 方法 | task | strict | waypoint RMSE均值 mm | 实际峰矩均值 Nm | 子步峰速均值 m/s | 完整24s |',
            '|---|---:|---:|---:|---:|---:|---:|']
        lines += [row(m,r) for m,r in report['eleven_method_summary'].items()]
    lines += ['',
        '两种新RL同DGX、同8192互动预算，但parameter6含解析VMC记忆/控制先验且输出6维，direct7输出7维，不能称相同函数类。旧dense/potential PPO在本机训练，本轮配对RL在DGX训练；这里比较的实际六条件部署均为DGX。旧ESN/MLP模仿数据及经典搜索预算也不同，11方法附表不表示等训练条件。',
        '存在安全短回合时，指标来自各自实际时长，不能与完整24s窗口直接排名；所有失败仍计入分母6。waypoint由状态机推进，指标需与阶段、task/strict、扰动曝光一起解释。没有按验证成绩挑checkpoint、改变reward或放宽gate。',
        f"输入和工具hash共{len(report['input_sha256'])}项保存在同名JSON。旧8方法JSON SHA256：`{report['old_report_sha256']}`；部署plan SHA256：`{report['plan_sha256']}`。",'']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--old-report',type=Path,required=True)
    p.add_argument('--old-report-sha256',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--include-eleven-method-table',action='store_true')
    args=p.parse_args()
    require(not args.output.with_suffix('.json').exists() and not args.output.with_suffix('.md').exists(),'Fresh report outputs required')
    report=audit(args.archive.resolve(),args.old_report.resolve(),args.old_report_sha256)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.with_suffix('.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    args.output.with_suffix('.md').write_text(markdown(report,args.include_eleven_method_table))
    print(json.dumps(report['summary'],ensure_ascii=False))


if __name__=='__main__':main()
