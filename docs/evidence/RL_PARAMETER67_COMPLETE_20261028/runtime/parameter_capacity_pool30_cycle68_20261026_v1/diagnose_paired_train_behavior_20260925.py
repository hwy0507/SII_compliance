"""Offline train-only behavior statistics bound to independent transition audits."""
import argparse
import hashlib
import json
from pathlib import Path
import types
import numpy as np


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):return json.loads(Path(path).read_text())


def distribution(values):
    values=np.asarray(values)
    return dict(mean=float(values.mean()),p95=float(np.quantile(values,.95)),min=float(values.min()),max=float(values.max()))


def parameter_rate(log_scale,policy_action,controller_class):
    # Reinitialize at each episode. A concatenation across episode boundaries
    # would incorrectly attribute reset jumps to the gain-rate limiter.
    previous=np.vstack([np.zeros((1,6)),log_scale[:-1]])
    limit=controller_class.log_scale_rate_per_s*controller_class.action_period_s
    requested_delta=controller_class.log_scale_limit*policy_action-previous
    actual_delta=log_scale-previous
    require(np.allclose(actual_delta,np.clip(requested_delta,-limit,limit),rtol=0.,atol=2e-16),'Recorded rate update does not match frozen controller')
    return np.abs(requested_delta)>limit+1e-12,actual_delta,limit


def mode_statistics(archive,audits,mode):
    run=archive/'training'/mode;snapshot=archive/'source'
    manifest=read(run/'manifest.json');audit_file=audits/f'{mode}_training_transition_audit.json';audit=read(audit_file)
    require(audit['passed'] and audit['training_transitions']==8192 and sha(run/'manifest.json')==audit['manifest_sha256'],'Independent final audit provenance mismatch')
    auditor=snapshot/'tools/audit_paired_transitions_20260924.py'
    require(sha(auditor)==audit['audit_tool_sha256']==manifest['source_hashes']['tools/audit_paired_transitions_20260924.py'],'Frozen auditor differs')
    frozen=types.ModuleType('train_statistics_frozen_auditor');frozen.__file__=str(auditor)
    exec(compile(auditor.read_text(),str(auditor),'exec'),frozen.__dict__)
    numerical=frozen.load_frozen(snapshot,manifest);controller=numerical['Canonical48VMCTuning']
    audited={Path(row['directory']).resolve():row for row in audit['episodes']}
    scopes={'training':sorted((run/'train').glob('episode_*')),
            'train_zero':[run/'eval/train/zero/episode_00000'],
            'train_ppo':[run/'eval/train/ppo/episode_00000']}
    answer=dict(mode=mode,seed=manifest['training']['seed'],audit_sha256=sha(audit_file),manifest_sha256=sha(run/'manifest.json'),scopes={})
    for name,directories in scopes.items():
        blocks=[];rate_blocks=[];delta_blocks=[];episodes=[]
        for directory in directories:
            verified=audited[directory.resolve()]
            for filename,digest in verified['hashes'].items():require(sha(directory/filename)==digest,'Audited train evidence changed: '+str(directory/filename))
            with np.load(directory/'transitions.npz',allow_pickle=False) as data:values={key:data[key].copy() for key in data.files}
            blocks.append(values);actions=values['execution_action']
            if mode=='parameter6':
                active,delta,limit=parameter_rate(values['log_scale'],values['policy_action'],controller)
                rate_blocks.append(active);delta_blocks.append(delta)
            episodes.append(dict(episode=directory.name,transitions=len(actions),complete=verified['complete'],
                task_success=verified['task_success'],development_gate=verified['development_gate'],
                final_observed_stage=int(values['next_stage'][-1]),reward_sum=float(values['reward'].sum()),
                discounted_reward=verified['discounted_actual_reward'],slowdown_mean=float(actions[:,0].mean()),
                yield_abs_mean=float(np.abs(actions[:,1:]).mean()),trace_sha256=sha(directory/'transitions.npz')))
        all_data={key:np.concatenate([block[key] for block in blocks]) for key in ('execution_action','policy_action','log_scale','stage','reward')}
        actions=all_data['execution_action'];requests=all_data['policy_action'];log_scale=all_data['log_scale']
        stats=dict(transitions=len(actions),episodes=episodes,reward_sum_including_partial=float(all_data['reward'].sum()),
            stage_counts={str(k):int(v) for k,v in zip(*np.unique(all_data['stage'],return_counts=True))},
            slowdown=distribution(actions[:,0]),slowdown_zero_fraction=float(np.mean(actions[:,0]==0.)),
            slowdown_one_fraction=float(np.mean(actions[:,0]==1.)),yield_absolute=distribution(np.abs(actions[:,1:])),
            yield_near_limit_fraction=float(np.mean(np.abs(actions[:,1:])>=.99)),
            policy_upper_or_abs_one_fraction_by_axis=np.mean(np.abs(requests)>=1.-1e-7,axis=0).tolist())
        if name=='training':require(stats['transitions']==8192,'Not full8192 train statistics')
        if mode=='parameter6':
            active=np.concatenate(rate_blocks);delta=np.concatenate(delta_blocks);scale=np.exp(log_scale)
            stats['gain_rate']=dict(limit_per_step=limit,active_axis_updates=int(active.sum()),axis_updates=int(active.size),
                active_axis_fraction=float(active.mean()),active_by_axis_fraction=active.mean(axis=0).tolist(),
                any_axis_active_steps=int(np.any(active,axis=1).sum()),any_axis_active_fraction=float(np.any(active,axis=1).mean()),
                actual_max_abs_delta_by_axis=np.max(np.abs(delta),axis=0).tolist())
            stats['stiffness_ratio']=dict(min_by_axis=scale.min(axis=0).tolist(),max_by_axis=scale.max(axis=0).tolist(),
                mean_by_axis=scale.mean(axis=0).tolist(),gain_bound_fraction=float(np.mean(np.abs(log_scale)>=controller.log_scale_limit-1e-12)))
        full=[episode for episode in episodes if episode['complete']]
        stats['complete_episode_outcome_groups']={}
        for success in (False,True):
            group=[episode for episode in full if episode['task_success']==success]
            if group:stats['complete_episode_outcome_groups'][str(success)]=dict(episodes=len(group),
                reward_sum_mean=float(np.mean([r['reward_sum'] for r in group])),
                discounted_reward_mean=float(np.mean([r['discounted_reward'] for r in group])),
                slowdown_mean=float(np.mean([r['slowdown_mean'] for r in group])),
                final_stage_counts={str(stage):sum(r['final_observed_stage']==stage for r in group) for stage in range(4)})
        if name!='training':
            directory=directories[0];result=read(directory/'rollout.json')
            evaluated=numerical['evaluation_summary'](result,manifest['fixture_specs']['train'])
            require(evaluated['task_success']==episodes[0]['task_success'] and evaluated['development_gate']==episodes[0]['development_gate'],'Train eval result differs from audited labels')
            with np.load(directory/'rollout.npz',allow_pickle=False) as raw:
                endpoint=float(np.mean(np.linalg.norm(raw['position'][-10:]-raw['target'][-10:],axis=1)))
                stats['last_target_position_m']=raw['target'][-1].tolist()
            require(abs(endpoint-result['endpoint_error_m'])<1e-12,'Train endpoint evidence differs')
            stats['evaluation']=dict(**evaluated,lift_m=result['lift_m'],result_sha256=sha(directory/'rollout.json'))
        answer['scopes'][name]=stats
    answer['train_eval_same_final_target']=answer['scopes']['train_zero']['last_target_position_m']==answer['scopes']['train_ppo']['last_target_position_m']
    return answer


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','audits','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();require(not args.output.exists() and not args.output.with_suffix('.md').exists(),'Fresh outputs required')
    modes={mode:mode_statistics(args.archive.resolve(),args.audits.resolve(),mode) for mode in ('parameter6','direct7')}
    result=dict(scope='Only all8192 train transitions and final train/zero, train/PPO; no validation trajectories or six-fixture matrix read',
        selection='All existing seed20260923 episodes, including failures and partial; fixed final policy',
        formulas=dict(rate='previous logscale resets to0 per episode; request_delta=log(2)*policy_action-previous; active iff abs(request_delta)>rate_per_s*dt+1e-12; verify actual_delta=clip(request_delta)',
            gain='K/K0=exp(logscale); gain amplitude bound and temporal rate bound are separate',
            action='Actual action7; yield near bound iff abs(yield)>=.99. Gym request is already SB3-clipped, not latent Gaussian.',
            returns='Undiscounted sums separate from audited gamma=.995 discounted returns; partial not grouped with complete episodes'),
        modes=modes,tool_sha256=sha(__file__),limitations=['Single seed descriptive associations, not causal evidence.',
            'Train exploration request rate statistics do not describe deterministic final policy.',
            'Different control priors/action sets/hidden VMC state remain; no reward or controller change.'])
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    lines=['# 配对PPO训练行为诊断：训练探索与确定性策略分开统计','',
        '只使用seed20260923的全部8192训练transition和最终train/zero、train/PPO。源hash、每episode日志hash与独立审计一致；没有读取validation轨迹或六条件验证，没有调参、重新训练或选择checkpoint。','',
        '| parameter6统计范围 | transition | 限速轴更新 / 总轴更新 | 至少一轴限速的步数比例 | K幅值触限比例 |',
        '|---|---:|---:|---:|---:|']
    for name,scope in modes['parameter6']['scopes'].items():
        rate=scope['gain_rate'];lines.append(f"| {name} | {scope['transitions']} | {rate['active_axis_updates']}/{rate['axis_updates']} ({100*rate['active_axis_fraction']:.3f}%) | {100*rate['any_axis_active_fraction']:.3f}% | {100*scope['stiffness_ratio']['gain_bound_fraction']:.3f}% |")
    lines+=['','限速按每个episode的初态logscale=0逐步重建，核对实际更新等于clip后的目标差。幅值未触0.5×/2×界不代表限速器未激活；训练探索与最终确定性策略必须分别解读。','',
        '| 模式/范围 | slowdown均值 | slowdown恰为0比例 | yield绝对均值 | yield近界比例 |',
        '|---|---:|---:|---:|---:|']
    for mode,data in modes.items():
        for name,scope in data['scopes'].items():lines.append(f"| {mode}/{name} | {scope['slowdown']['mean']:.6f} | {100*scope['slowdown_zero_fraction']:.3f}% | {scope['yield_absolute']['mean']:.6f} | {100*scope['yield_near_limit_fraction']:.3f}% |")
    lines+=['','| 完整训练episode组 | episode数 | mean未折扣reward和 | mean折扣return | mean slowdown | final stage计数0/1/2/3 |',
        '|---|---:|---:|---:|---:|---|']
    for mode,data in modes.items():
        for label,group in data['scopes']['training']['complete_episode_outcome_groups'].items():
            stages='/'.join(str(group['final_stage_counts'][str(i)]) for i in range(4))
            lines.append(f"| {mode}/task={label} | {group['episodes']} | {group['reward_sum_mean']:.6f} | {group['discounted_reward_mean']:.9f} | {group['slowdown_mean']:.6f} | {stages} |")
    lines+=['','成功与失败组的reward差异包含终端基础奖励，不能当作额外独立性能指标。所有完整非成功且无invalid惩罚轨迹的折扣return受potential恒等式约束为−Φ(initial)，与其最终stage不同并不矛盾。两条392步partial各自保留在JSON，未混入完整episode组；其有限前缀return不等于完整任务return。','',
        '| 最终train/zero→train/PPO | task | 当前阶段endpoint mm | 外部单对象力峰N | 同一最终target |',
        '|---|---|---:|---:|---|']
    for mode,data in modes.items():
        a,b=[data['scopes'][name]['evaluation'] for name in ('train_zero','train_ppo')]
        lines.append(f"| {mode} | {a['task_success']}→{b['task_success']} | {1000*a['endpoint_error_m']:.3f}→{1000*b['endpoint_error_m']:.3f} | {a['peak_external_resultant_force_n']:.3f}→{b['peak_external_resultant_force_n']:.3f} | {data['train_eval_same_final_target']} |")
    lines+=['','parameter6的zero是名义解析VMC，direct7的zero是全零执行动作。执行动作及slowdown既受策略也受反馈轨迹影响，成功组较低slowdown或确定性PPO动作较小均是相关性，不能仅凭这些轨迹建立因果解释或泛化结论。', '',
        f"重现工具：`tools/diagnose_paired_train_behavior_20260925.py`，SHA256 `{result['tool_sha256']}`。完整逐episode统计、公式、日志/审计hash见同名JSON。"]
    args.output.with_suffix('.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(output=str(args.output),parameter_rates={name:scope['gain_rate'] for name,scope in modes['parameter6']['scopes'].items()})))


if __name__=='__main__':main()
