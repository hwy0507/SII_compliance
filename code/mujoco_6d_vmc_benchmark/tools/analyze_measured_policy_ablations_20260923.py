"""Analyze completed 24s paired policy ablations, never short smoke scores.

Reads short action NPZ and physical-substep JSON summaries, not large physics
NPZ files. Original/checkpoint raw actions are reconstructed on visited states;
this is not a claim about the unobserved counterfactual state trajectory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from current_student_policy_20260921 import load_current
from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics
from wbc_velocity_residual_core import VelocityResidualActionFilter, VelocityResidualSafetyConfig

METHODS = ('vmc', 'mlp', 'esn', 'esn_no_x_yield', 'esn_lowpass_025', 'mlp_lowpass_025', 'vmc_lowpass_025')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lag1(values):
    if len(values)<3 or values[1:].std()<1.e-10 or values[:-1].std()<1.e-10:
        return None
    return float(np.corrcoef(values[1:], values[:-1])[0,1])


def filter_actions(actions):
    filt = VelocityResidualActionFilter(VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32))
    rows = [filt.filter(a,.04) for a in actions]
    return np.stack([r.cartesian_yield_twist for r in rows]), sum(r.slew_limited for r in rows)


def action_diagnostics(actions, base_actions):
    filtered, slew_count = filter_actions(actions)
    unfiltered_counterfactual, _ = filter_actions(base_actions)
    indices = np.arange(max(0,len(actions)-25),len(actions))
    a, raw, applied = actions[indices], base_actions[indices], filtered[indices]
    scale = np.array([.32,.32,.32,.6,.6,.6])
    return dict(slew_limited_steps=int(slew_count),
                last_1s=dict(base_x_action_lag1=lag1(raw[:,1]),
                    base_x_action_std=float(raw[:,1].std()),
                    intervention_x_action_lag1=lag1(a[:,1]),
                    intervention_x_action_std=float(a[:,1].std()),
                    intervention_x_sign_flip_fraction=float(np.mean(a[1:,1]*a[:-1,1]<0)),
                    base_raw_yield_mean=(raw[:,1:]*scale).mean(0).tolist(),
                    intervention_raw_yield_mean=(a[:,1:]*scale).mean(0).tolist(),
                    slew_filtered_yield_mean=applied.mean(0).tolist(),
                    slew_bias_mean=(applied-a[:,1:]*scale).mean(0).tolist(),
                    unchanged_action_openloop_slew_yield_mean=unfiltered_counterfactual[indices].mean(0).tolist()),
                tail_samples=[dict(index=int(i),base_raw_action=base_actions[i].tolist(),
                                   intervention_action=actions[i].tolist(),
                                   safety_slew_yield=filtered[i].tolist()) for i in indices])


def same_state_memory_diagnostic(observations, vmc_options, esn_checkpoint):
    teacher=SixDVirtualDynamics(vmc_options)
    actor=load_current(esn_checkpoint)
    reset_actor=load_current(esn_checkpoint)
    teacher_actions=[];esn_actions=[];reset_actions=[];memory_norms=[]
    for obs in observations:
        teacher_actions.append(teacher.act(obs[39:45],.04))
        esn_actions.append(actor.act(obs))
        memory_norms.append([np.linalg.norm(actor.obj.state[sl]) for sl in
                             (slice(0,43),slice(43,86),slice(86,128))])
        reset_actor.reset()
        reset_actions.append(reset_actor.act(obs))
    return dict(scope='offline same visited observations, not alternate closed-loop trajectories',
                reset_caveat='per-frame reset is a sensitivity test outside normal history distribution, never a proposed fix',
                tail_estimated_wrench_mean=observations[-25:,39:45].mean(0).tolist(),
                tail_reference_vmc_action_mean=np.mean(teacher_actions[-25:],axis=0).tolist(),
                tail_stateful_esn_action_mean=np.mean(esn_actions[-25:],axis=0).tolist(),
                tail_per_frame_reset_esn_action_mean=np.mean(reset_actions[-25:],axis=0).tolist(),
                tail_stateful_reservoir_norms_mean_fast_medium_slow=np.mean(memory_norms[-25:],axis=0).tolist(),
                tail_action_stateful_vs_reset_mae=np.mean(abs(np.asarray(esn_actions[-25:])-np.asarray(reset_actions[-25:])),axis=0).tolist())


def analyze_job(root, method, seed, checkpoints):
    job = root/method/str(seed)
    required = [job/'command.json',job/'rollout/rollout.json',job/'rollout/rollout.npz',job/'metrics/audit_manifest.json']
    if not all(p.exists() for p in required):
        return dict(method=method,seed=seed,status='pending',missing=[str(p) for p in required if not p.exists()])
    command,result,manifest = [json.loads(p.read_text()) for p in (required[0],required[1],required[3])]
    if manifest.get('error') or not manifest.get('enabled') or len(manifest.get('episodes',[]))!=1:
        return dict(method=method,seed=seed,status='audit_invalid',audit_error=manifest.get('error'))
    metrics = manifest['episodes'][0]
    with np.load(required[2],allow_pickle=False) as trace:
        obs=trace['observation'];actions=trace['action'];times=trace['time']
        error=np.linalg.norm(trace['position']-trace['target'],axis=1)
    duration=float(result.get('arguments',{}).get('duration',len(times)*.04))
    if duration<23.99 or len(times)<600 or times[-1]-times[0]<23.95 or metrics['samples']<int(23.99/metrics['timestep_s']):
        return dict(method=method,seed=seed,status='short_or_incomplete_not_performance',duration_s=duration,
                    actions=len(times),physical_samples=metrics['samples'])
    base_method=method.split('_')[0]
    if base_method=='vmc':
        options=json.loads(command['environment']['CORE_VMC_CONFIG'])
        teacher=SixDVirtualDynamics(options)
        base_actions=np.stack([teacher.act(o[39:45],.04) for o in obs])
    else:
        actor=load_current(checkpoints[base_method])
        base_actions=np.stack([actor.act(o) for o in obs])
    expected=base_actions.copy()
    if method.endswith('_no_x_yield'):
        expected[:,1]=0.
    elif method.endswith('_lowpass_025'):
        previous=np.zeros(7)
        for i,a in enumerate(base_actions):
            previous += .25*(a-previous)
            expected[i]=previous
    replay_error=float(abs(expected-actions).max())
    contacts=result['panel_audit']['contacts']
    external={k:v for k,v in contacts.items() if k!='target_object_geom' and v.get('last_s') is not None}
    upstream=any(set(v['bodies'])&{'fr3_link0','fr3_link1','fr3_link2','fr3_link3','fr3_link4'} for v in external.values())
    last_contact=max((v['last_s'] for v in external.values()),default=None)
    recovery=None
    if last_contact is not None:
        for i in range(len(times)-9):
            if times[i]>=last_contact and np.all(error[i:i+10]<.015):
                recovery=float(times[i]-last_contact)
                break
    return dict(method=method,seed=seed,status='complete',
                task_success=bool(result['success']),strict_success=bool(result.get('accepted_panel_demo') and not upstream),
                endpoint_error_m=float(result['endpoint_error_m']),
                peak_external_penetration_m=float(result['contact']['all_external_max_penetration_m']),
                physical_metrics=metrics,action_diagnostics=action_diagnostics(actions,base_actions),
                same_state_memory_diagnostic=same_state_memory_diagnostic(obs,
                    json.loads(command['environment']['CORE_VMC_CONFIG']),checkpoints['esn']),
                action_replay_max_error=replay_error,
                contact_by_object={k:{field:v.get(field) for field in ('first_s','last_s','duration_s','peak_point_force_n','max_penetration_m','bodies')} for k,v in external.items()},
                last_external_contact_s=last_contact,
                recovery_to_15mm_for_10samples_after_last_contact_s=recovery,
                result_path=str(required[1]),sha256={p.name:sha(p) for p in required})


def decision(rows):
    by_name={r['method']:r for r in rows}
    needed=[by_name.get(k,{}) for k in METHODS]
    if any(r.get('status')!='complete' for r in needed):
        return 'WAIT_FULL_PAIRED_RESULTS', '完整24秒配对结果尚未齐全，不据smoke或部分轨迹扩展。'
    if any(r['action_replay_max_error']>1.e-6 for r in needed):
        return 'CHECK_ACTION_REPLAY', '有动作重放不一致，先核对checkpoint、包装器和时间序列。'
    original,lp=by_name['esn'],by_name['esn_lowpass_025']
    if lp['strict_success']:
        return 'REPLICATE_OTHER_DEVELOPMENT_FIXTURES', '9301低通通过原严格gate；可用同一alpha在9300/9302做开发复核，不替换原ESN结果。'
    op=original['action_diagnostics']['last_1s'];np_=lp['action_diagnostics']['last_1s']
    smoother=np_['intervention_x_action_std']<op['intervention_x_action_std']
    if smoother:
        return 'SMOOTHER_BUT_GATE_NOT_PASSED', '动作更平滑但未通过严格gate；区分任务、穿透/接触和恢复瓶颈，暂不将全fixture扩展作为修复验收。'
    return 'HYPOTHESIS_NOT_SUPPORTED_YET', '固定低通未同时提供动作机制与严格gate改善；保留原结果并检查其他分量/接触动力学。'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaign',type=Path,required=True)
    p.add_argument('--esn',type=Path,required=True)
    p.add_argument('--mlp',type=Path,required=True)
    p.add_argument('--seed',type=int,default=9301)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    protocol=json.loads((args.campaign/'protocol.json').read_text())
    checkpoints={'esn':args.esn,'mlp':args.mlp}
    for name,path in checkpoints.items():
        if sha(path)!=protocol['models'][name]['sha256']:
            raise ValueError('Frozen checkpoint mismatch: '+name)
    rows=[analyze_job(args.campaign,m,args.seed,checkpoints) for m in METHODS]
    code,reason=decision(rows)
    out=dict(scope='fixed-alpha same-checkpoint development causal diagnostics',rows=rows,
             decision=code,reason=reason,alpha=.25,equivalent_tau_s=-.04/np.log(.75),
             campaign_protocol_sha256=sha(args.campaign/'protocol.json'),tool_sha256=sha(__file__),
             limitations=['action/observation pre-step; time/kinematics post-step',
                          'safety-slew yield precedes joint and torque feasibility projections',
                          'base raw actions replayed on intervention visited states are not unmodified-policy closed-loop results',
                          'last-contact and recovery are diagnostic only; no task/strict gate changes'])
    args.output.mkdir(parents=True)
    (args.output/'analysis.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    lines=['# 固定alpha动作消融：完整配对开发结果','',f'fixture={args.seed}；alpha=.25；{reason}','',
           '| 方法 | 状态 | task/strict | 位置RMSE xyz / 3D (mm) | 物理峰值速度 (m/s) | 物理峰值关节力矩 (Nm) |',
           '|---|---|---|---|---:|---:|']
    for row in rows:
        if row['status']!='complete':
            lines.append(f'| {row["method"]} | {row["status"]} | — | — | — | — |');continue
        metric=row['physical_metrics']
        xyz='/'.join(f'{v*1000:.2f}' for v in metric['position_rmse_xyz_m'])
        lines.append(f'| {row["method"]} | complete | {row["task_success"]}/{row["strict_success"]} | {xyz} / {metric["position_rmse_3d_m"]*1000:.2f} | {metric["linear_speed_peak_mps"]:.4f} | {metric["generalized_actuator_torque_peak_nm"]:.3f} |')
    lines += ['', '| 方法 | 尾1秒x action std | raw x→slew x均值 (m/s) | 最末外接触(s) | 终点误差(mm) | 最大穿透(mm) |', '|---|---:|---|---:|---:|---:|']
    for row in rows:
        if row['status']!='complete':continue
        a=row['action_diagnostics']['last_1s'];last=row['last_external_contact_s']
        lines.append(f'| {row["method"]} | {a["intervention_x_action_std"]:.5f} | {a["intervention_raw_yield_mean"][0]:+.5f} → {a["slew_filtered_yield_mean"][0]:+.5f} | {last if last is not None else "none"} | {row["endpoint_error_m"]*1000:.2f} | {row["peak_external_penetration_m"]*1000:.3f} |')
    lines += ['','raw与slew为动作请求及执行filter重放，未冒充实际速度；task/strict沿用原gate。详细阶段指标、接触物体、动作重放误差与SHA见analysis.json。','']
    (args.output/'REPORT.md').write_text('\n'.join(lines))
    print(json.dumps(dict(output=str(args.output),decision=code,status={r['method']:r['status'] for r in rows})))


if __name__=='__main__':main()
