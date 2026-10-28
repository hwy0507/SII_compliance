"""Read-only training reward audit; no validation-dependent tuning or model selection."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from canonical48_rl_env_20260923 import reward_from_transition


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze_episode(folder, gamma):
    source = folder/'actor_trace.npz'
    with np.load(source, allow_pickle=False) as raw:
        obs, actions, phases = [raw[k].copy() for k in ('observation','action','phase_reward_metadata')]
    result_path = folder/'rollout.json'
    if not result_path.exists():
        return dict(episode=folder.name, samples=len(actions), partial=True,
                    counted_in_complete_statistics=False, trace_sha256=sha(source))
    result = json.loads(result_path.read_text())
    values, by_term, transitions = [], {}, []
    for i, action in enumerate(actions):
        last = i == len(actions)-1
        next_obs = obs[i] if last else obs[i+1]
        next_phase = result['final_stage'] if last else int(phases[i+1])
        reward, terms = reward_from_transition(next_obs, action, actions[i-1] if i else np.zeros(7),
                                               next_phase-int(phases[i]), result if last else None)
        values.append(reward)
        for key, value in terms.items():
            by_term.setdefault(key, []).append(value)
        if next_phase != phases[i]:
            transitions.append(dict(action_index=i, from_stage=int(phases[i]), to_stage=int(next_phase),
                                    previous_pose_error_m=float(np.linalg.norm(obs[i,20:23])),
                                    next_pose_error_m=float(np.linalg.norm(next_obs[20:23])),
                                    reward_progress=terms['progress'], reward_position=terms['position']))
    values = np.asarray(values)
    discounts = gamma**np.arange(len(values))
    # State penalties are calculated from new actor observations, matching the
    # frozen reward implementation; final shaping reuses the last observation.
    assert np.isfinite(values).all()
    counts = {str(int(stage)):int(np.sum(phases == stage)) for stage in np.unique(phases)}
    return dict(episode=folder.name, samples=len(actions), partial=False, task=bool(result['success']),
                final_stage=result['final_stage'], endpoint_error_m=result['endpoint_error_m'],
                lift_m=result['lift_m'], undiscounted_return=float(values.sum()),
                discounted_return_from_reset=float(discounts@values),
                terminal_bonus_raw=by_term['terminal'][-1],
                terminal_bonus_discounted_from_reset=float(discounts[-1]*by_term['terminal'][-1]),
                reward_terms={k:dict(raw=float(np.sum(v)), discounted=float(discounts@np.asarray(v)))
                              for k,v in by_term.items()},
                stage_sample_counts=counts, stage_transitions=transitions,
                trace_sha256=sha(source), result_sha256=sha(result_path))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    manifest = json.loads((args.run/'manifest.json').read_text())
    gamma = manifest['training']['gamma']
    snapshot = Path(manifest['argv'][0]).resolve().parents[1]
    reward_file = ROOT/'scripts/canonical48_rl_env_20260923.py'
    if sha(reward_file) != manifest['source_hashes']['scripts/canonical48_rl_env_20260923.py']:
        raise ValueError('Reward source differs from frozen training run; do not silently recompute')
    rows = [analyze_episode(f,gamma) for f in sorted((args.run/'train').glob('episode_*'))]
    complete = [r for r in rows if not r['partial']]
    if not complete or sum(r['samples'] for r in rows) != manifest['training']['timesteps']:
        raise ValueError('Incomplete or unexpected training sample count')
    ranked = sorted(complete,key=lambda r:r['discounted_return_from_reset'],reverse=True)
    for r in complete:
        r['discounted_return_rank'] = next(i+1 for i, item in enumerate(ranked) if item['episode']==r['episode'])
    terminal_weights = {str(steps):float(gamma**(steps-1)) for steps in (64,200,400,600)}
    success_ranks = [r['discounted_return_rank'] for r in complete if r['task']]
    report = dict(scope='train episodes only; descriptive reward audit, not policy selection or causal attribution',
                  gamma=gamma, action_period_s=.04, manifest_sha256=sha(args.run/'manifest.json'),
                  reward_source_sha256=sha(reward_file), source_snapshot=str(snapshot),
                  samples=sum(r['samples'] for r in rows), complete_episodes=len(complete),
                  task_successes=sum(r['task'] for r in complete), success_return_ranks=success_ranks,
                  discount_weights=terminal_weights, rows=rows,
                  limitations=['episodes use evolving policies and train-only online normalization',
                    'discounted return from reset is a descriptive objective, not SB3 measured gradient or minibatch loss',
                    'critic bootstrapping and GAE can propagate rewards beyond a rollout; n_steps64 is not an absolute horizon',
                    'low task alignment does not alone prove the cause of deterministic policy collapse',
                    'no validation/test trajectories used; no intermediate checkpoint selected'])
    lines = ['# PPO8192训练目标审计：reward与任务门的关系', '',
             '仅重读本轮13条完整训练轨迹和392步partial；没有使用验证轨迹、改变reward或重选checkpoint。按冻结源码逐步复算reward。', '',
             '| 训练episode | task | 最终stage | 抬升 mm | 终点误差 mm | 未折扣return | 从reset折扣return | 折扣return排名 |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in complete:
        lines.append(f"| {r['episode']} | {int(r['task'])} | {r['final_stage']} | {1000*r['lift_m']:.2f} | {1000*r['endpoint_error_m']:.2f} | {r['undiscounted_return']:.4f} | {r['discounted_return_from_reset']:.4f} | {r['discounted_return_rank']} |")
    lines += ['',f"任务成功{sum(r['task'] for r in complete)}/{len(complete)}；成功回合按从reset折扣return由高到低的名次为{success_ranks}。训练episode来自不断更新的随机策略，不是同一个冻结策略的多seed评估，不能将排序解释为学习器主动选择了某回合。", '',
        '## 定量解释', '',
        f"gamma={gamma}，每action40ms。第600步的终端成功+5，从episode起点折扣后只贡献{5*terminal_weights['600']:.4f}；第200步后权重约{terminal_weights['200']:.4f}，第400步后约{terminal_weights['400']:.4f}。因此固定终点才给出的稳定抓持奖励，对早期动作的直接折扣贡献较弱。", '',
        '位置项为每步−0.16×当前waypoint距离，阶段切换会换成更远的新目标；进展奖励每阶段只给+0.5。保持在近处旧目标和进入尚未完成的抬升阶段，会改变密集惩罚的持续时间。这是reward设计需检验的激励差异，不证明拖延一定是可实现最优策略，也不能由最终失败倒推reward hacking。逐次stage切换前后误差与奖励保存在JSON。', '',
        '终端success同时要求抬升、末端位置、双指保持、物体静止等；reward没有对每个完整panel gate逐项奖励或惩罚。完整gate低与reward优化并不矛盾。唯一成功样本与失败样本return的次序，可以揭示奖励和验收未完全一致，但并不能排除小预算、PPO更新噪声、观测归一化变化、接触历史或确定性/随机动作差异。', '',
        'PPO的64步rollout约2.56s；价值函数bootstrap和GAE可将更远奖励传回，因此不能称它只能学习2.56s内的行为。此处折扣分析也不是实测梯度或训练loss。', '',
        '## 后续可检验改动（尚未运行）', '',
        '若继续改进，应单独预声明一个任务进度潜势差形式的reward变体，在统一有限时域终端边界下处理潜势；用同一训练/验证fixture、互动预算、seed和最后checkpoint规则对照。要同时看完整gate、三维物理指标与终端状态，不能只报reward提高。不据本次validation失败扫描超参数，也不删除原PPO8192失败模型。当前先完成它在DGX同平台的冻结评估。', '',
        '完整逐回合证据与source/hash见同名JSON；[原8192协议](CANONICAL48_PPO_8192_PROTOCOL_20260923.md)。', '']
    args.output.write_text('\n'.join(lines))
    args.output.with_suffix('.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(output=str(args.output),success_ranks=success_ranks,discounts=terminal_weights)))


if __name__ == '__main__':
    main()
