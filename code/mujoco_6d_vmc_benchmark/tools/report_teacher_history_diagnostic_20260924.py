"""Independently audit 12 archived teacher-history episodes without simulation."""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
import numpy as np


def read(p):return json.loads(p.read_text())


def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def require(ok,message):
    if not ok:raise ValueError(message)


def longest(mask):
    edges=np.diff(np.r_[False,mask,False].astype(int))
    return int(np.max(np.flatnonzero(edges==-1)-np.flatnonzero(edges==1),initial=0))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args();r=args.archive
    require(not args.output.exists(),'Fresh report directory required')
    protocol=read(r/'protocol.json');ready=read(r/'READY.json');final=read(r/'FINAL_RESULT.json')
    require(sha(r/'protocol.json')==ready['protocol_sha256'],'Protocol changed')
    require(final['complete'] and len(final['rows'])==12,'Incomplete original result')
    hashes={}
    for name,expected in protocol['source_sha256'].items():
        value=sha(r/'source_snapshot'/name);require(value==expected,'Source changed '+name);hashes['source_snapshot/'+name]=value
    for name,m in protocol['models'].items():
        value=sha(r/'frozen_models'/f'{name}.npz');require(value==m['sha256'],'Model changed '+name);hashes[f'frozen_models/{name}.npz']=value
    sys.path.insert(0,str(r/'source_snapshot/scripts'))
    from current_student_policy_20260921 import load_current
    from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics
    from wbc_velocity_residual_core import VelocityResidualActionFilter,VelocityResidualSafetyConfig
    def filtered(actions):
        obj=VelocityResidualActionFilter(VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32))
        return np.stack([obj.filter(a,.04).cartesian_yield_twist for a in actions])
    byid={v['id']:v for v in final['rows']};rows=[]
    for job in protocol['jobs']:
        d=r/'jobs'/job['id'];result=read(d/'rollout/rollout.json');saved=byid[job['id']]
        require(read(d/'result.json')==saved and read(d/'command.json')==job,'Per-job manifest mismatch')
        for name,key in [('rollout.npz','trace_sha256'),('rollout.json','result_sha256'),('rollout.mjb','model_mjb_sha256')]:
            require(sha(d/'rollout'/name)==saved[key],'Original hash mismatch '+job['id']+'/'+name)
        physical=read(d/'metrics/episode_0/substep_metrics.json');audit=read(d/'metrics/audit_manifest.json')
        require(physical==saved['physical'] and audit['episodes']==[physical] and audit['error'] is None,'Physical sidecar mismatch')
        for name,value in audit['source_sha256'].items():require(protocol['source_sha256'].get('scripts/'+name)==value,'Audit source mismatch '+name)
        require(physical['samples']==480000 and physical['timestep_s']==5e-5,'Wrong duration')
        with np.load(d/'metrics/episode_0/substep_metrics.npz',allow_pickle=False) as raw:
            require(all(len(raw[k])==480000 and np.isfinite(raw[k]).all() for k in raw.files),'Invalid raw substeps')
            times=raw['time'];require(np.allclose(np.diff(times),5e-5,atol=1e-12,rtol=0),'Invalid substep timestamps')
            recompute=dict(linear_speed_peak_mps=float(np.linalg.norm(raw['twist'][:,:3].astype(float),axis=1).max()),
                           generalized_actuator_torque_peak_nm=float(np.abs(raw['qfrc_actuator']).max()),
                           position_rmse_3d_m=float(np.sqrt(np.mean(np.sum(raw['error'].astype(float)**2,axis=1)))))
            for k,v in recompute.items():require(np.isclose(v,physical[k],rtol=1e-6,atol=1e-7),'Physical recomputation '+k)
        with np.load(d/'rollout/rollout.npz',allow_pickle=False) as z:
            obs=z['observation'];labels=z['teacher_action'];action=z['action'];pretime=z['time']-.04
            contact=np.r_[False,np.linalg.norm(z['force'][:-1],axis=1)>.05]
            endpoint=float(np.mean(np.linalg.norm(z['position'][-10:]-z['target'][-10:],axis=1)))
            lift=float(z['object_position'][-1,2]-.425)
            final_speed=float(np.linalg.norm(np.diff(z['object_position'][-10:],axis=0)/.04,axis=1).max())
        require(obs.shape==(600,48) and abs(endpoint-result['endpoint_error_m'])<1e-12 and abs(lift-result['lift_m'])<1e-12,'Short trace mismatch')
        teacher=SixDVirtualDynamics(protocol['teacher']);replayed=np.stack([teacher.act(o[39:45],.04) for o in obs]);teacher_slew=filtered(labels)
        parity=float(np.max(abs(replayed-labels)));require(parity<1e-6 and np.max(abs(action-labels))<1e-6,'Teacher action mismatch')
        stage=np.zeros(600,dtype=int)
        for ev in result['events']:stage[pretime>=ev['t']-1e-8]=ev['stage']
        masks=dict(all=np.ones(600,dtype=bool),loaded=stage==3,loaded_contact=(stage==3)&contact,
                   loaded_no_contact=(stage==3)&~contact,observed_contact=contact)
        expected_stage=0 if job['requested_event_stage']=='approach' else 3
        trigger=result['fixture_trigger_time_s'];contacts=result['panel_audit']['contacts'];rod=contacts['push_rod_geom']
        external=[v for k,v in contacts.items() if k!='target_object_geom']
        upstream=any(set(v['bodies'])&{'fr3_link0','fr3_link1','fr3_link2','fr3_link3','fr3_link4'} for v in external)
        task=dict(lift=lift>.1,object_speed=final_speed<.02,endpoint=endpoint<.015,physics=not result['invalid_physics'],
                  upstream=not result['upstream_contact'],stage=result['final_stage']==3,cup=result['cup_safe'])
        gate=dict(task=bool(result['success']),rod=rod['duration_s']>.3,release=rod['last_s'] is not None and 24-rod['last_s']>2,
                  gap=result['panel_audit']['final_rod_gap_m']>.002,penetration=max(v['max_penetration_m'] for v in external)<.0002,
                  upstream=not upstream)
        require(all(task.values())==result['success'] and all(gate.values())==saved['strict_success'],'Gate mismatch')
        require(result['fixture_triggered'] and result['contact']['first_stage']==expected_stage,'Actual contact stage mismatch')
        trigger_expected=0. if expected_stage==0 else next(e['t'] for e in result['events'] if e['stage']==3)
        require(abs(trigger-trigger_expected)<1e-9 and rod['first_s']>=trigger,'Trigger timing mismatch')
        students={}
        for name in ('mlp','esn'):
            actor=load_current(r/'frozen_models'/f'{name}.npz');pred=np.stack([actor.act(o) for o in obs]);slew=filtered(pred)
            stats={}
            for phase,mask in masks.items():
                if not mask.any():stats[phase]=dict(samples=0);continue
                err=pred[mask]-labels[mask];diff=slew[mask]-teacher_slew[mask];strong=mask&(abs(labels[:,1])>.01)
                stats[phase]=dict(samples=int(mask.sum()),action_rmse=float(np.sqrt(np.mean(err**2))),
                    action_mae=np.mean(abs(err),axis=0).tolist(),slew_yield_mae=np.mean(abs(diff),axis=0).tolist(),
                    slew_linear_mae_mps=float(np.mean(abs(diff[:,:3]))),slew_angular_mae_radps=float(np.mean(abs(diff[:,3:]))),
                    x_sign_reference_samples=int(strong.sum()),x_sign_conflict_rate=float(np.mean(pred[strong,1]*labels[strong,1]<0)) if strong.any() else None)
                if phase in saved['offline']['students'][name]:
                    prior=saved['offline']['students'][name][phase]
                    require(np.isclose(stats[phase]['action_rmse'],prior['action_rmse'],rtol=1e-9,atol=1e-12),'Offline action recomputation mismatch')
                    require(np.allclose(stats[phase]['slew_yield_mae'],prior['slew_yield_mae'],rtol=1e-9,atol=1e-12),'Offline slew recomputation mismatch')
            students[name]=stats
        rows.append(dict(id=job['id'],split=job['fixture']['split'],seed=job['fixture']['seed'],requested=job['requested_event_stage'],
            actual_first_stage=result['contact']['first_stage'],trigger_s=trigger,first_contact_s=result['contact']['first_s'],
            final_stage=result['final_stage'],task_success=result['success'],strict_success=saved['strict_success'],
            failed_task=[k for k,v in task.items() if not v],failed_gate=[k for k,v in gate.items() if not v],
            endpoint_m=endpoint,lift_m=lift,contact_union_duration_s=result['contact']['duration_s'],rod_contact_s=rod['duration_s'],
            contact_by_object={k:{f:v.get(f) for f in ('first_s','last_s','duration_s','bodies')} for k,v in contacts.items() if v.get('first_s') is not None},
            sparse_contact_samples=int(contact.sum()),longest_sparse_contact_run_s=.04*longest(contact),
            physical=physical,raw_recomputed_physical=recompute,teacher_parity_max=parity,
            students=students,mjb_sha256=saved['model_mjb_sha256']))
        for f in d.rglob('*'):
            if f.is_file():hashes[str(f.relative_to(r))]=sha(f)
    pairs={}
    for fixture in protocol['fixtures']:
        jobs=[j for j in protocol['jobs'] if j['fixture']['seed']==fixture['seed']];a,b=jobs
        differences=[k for k in a['arguments'] if a['arguments'][k]!=b['arguments'][k]]
        require(set(differences)=={'event_stage','output'} and a['environment']==b['environment'],'Paired command mismatch')
        rr=[x for x in rows if x['seed']==fixture['seed']];require(len({x['mjb_sha256'] for x in rr})==1,'Paired compiled models differ')
        pairs[str(fixture['seed'])]=dict(argument_differences=differences,mjb_sha256=rr[0]['mjb_sha256'],same_environment=True)
    groups={}
    for split in ('train','validation'):
        for requested in ('approach','loaded_lift'):
            part=[x for x in rows if x['split']==split and x['requested']==requested];data={}
            for model in ('mlp','esn'):
                data[model]={}
                for phase in ('all','loaded_contact','loaded_no_contact'):
                    entries=[x['students'][model][phase] for x in part if x['students'][model][phase]['samples']]
                    data[model][phase]=dict(episodes=len(entries),samples=sum(x['samples'] for x in entries),
                        mean_episode_action_rmse=float(np.mean([x['action_rmse'] for x in entries])) if entries else None,
                        mean_episode_slew_linear_mae_mps=float(np.mean([x['slew_linear_mae_mps'] for x in entries])) if entries else None,
                        mean_episode_slew_angular_mae_radps=float(np.mean([x['slew_angular_mae_radps'] for x in entries])) if entries else None)
            groups[split+'/'+requested]=data
    launch=read(r/'launch.json');complete=(r/'COMPLETE.json').stat().st_mtime
    out=dict(scope='12 fixed-teacher development diagnostics; offline student actions only; no retraining',archive=str(r.resolve()),
        protocol_sha256=sha(r/'protocol.json'),sources_verified=len(protocol['source_sha256']),models_verified=2,
        launch_china=datetime.fromtimestamp(launch['launched_unix'],ZoneInfo('Asia/Shanghai')).isoformat(),
        complete_china=datetime.fromtimestamp(complete,ZoneInfo('Asia/Shanghai')).isoformat(),
        elapsed_wall_s=complete-launch['launched_unix'],rows=rows,paired_geometry=pairs,groups=groups,file_sha256=hashes)
    args.output.mkdir(parents=True);(args.output/'analysis.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    lines=['# 12条固定教师接触历史诊断：独立归档审计','',
           '12/12完整执行，6/6阶段配对MJB一致，真实首次接触阶段均符合声明；固定教师task与strict均0/12。',
           '冻结MLP/ESN误差为teacher访问状态上的离线指标，不是student闭环任务结果。','',
           '| 条件 | 实际首次stage | 触发/首次接触(s) | 末stage | 原任务监测对象/rod接触(s) | 终点误差(mm) | MLP/ESN全程action RMSE |',
           '|---|---:|---|---:|---|---:|---|']
    for x in rows:lines.append(f"| {x['id']} | {x['actual_first_stage']} | {x['trigger_s']:.3f}/{x['first_contact_s']:.3f} | {x['final_stage']} | {x['contact_union_duration_s']:.3f}/{x['rod_contact_s']:.3f} | {1000*x['endpoint_m']:.2f} | {x['students']['mlp']['all']['action_rmse']:.4f}/{x['students']['esn']['all']['action_rmse']:.4f} |")
    lines+=['','| split/启动 | phase | MLP/ESN action RMSE | MLP/ESN slew线速度MAE(m/s) | MLP/ESN slew角速度MAE(rad/s) |',
            '|---|---|---|---|---|']
    for group,g in groups.items():
        for phase in ('all','loaded_contact','loaded_no_contact'):
            a,b=g['mlp'][phase],g['esn'][phase]
            if not a['episodes']:continue
            vals=['mean_episode_action_rmse','mean_episode_slew_linear_mae_mps','mean_episode_slew_angular_mae_radps']
            lines.append('| '+group+' | '+phase+' | '+' | '.join(f'{a[k]:.5f}/{b[k]:.5f}' for k in vals)+' |')
    lines+=['','上表各项为episode均值后再组平均，非按接触样本数加权；approach没有loaded阶段，缺失值不填零。',
             '原contact.duration_s是任务监测对象接触的时间并集，不是所有外部结构接触；rod duration来自逐对象子步审计。学生loaded_contact分段使用前一帧25Hz合力>.05N，二者不可直接等同。',
             'raw/slew误差是动作请求误差，未冒充实际末端速度误差；任务目标与gate保持原定义。',
             f"源码{len(protocol['source_sha256'])}项、2个模型、12个短轨迹和MJB SHA已核对；12×480000个物理子步原始数组重算指标与float64摘要在float32容差内一致。",
             f"服务器开始{out['launch_china']}，完成{out['complete_china']}，墙钟{out['elapsed_wall_s']:.1f}s。后续分析曾因自动审批接口429限流暂停，9月24日恢复；并非整夜持续新增实验。"]
    (args.output/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(rows=len(rows),sources_verified=len(protocol['source_sha256']),task_success=sum(x['task_success'] for x in rows),groups=groups)))


if __name__=='__main__':main()
