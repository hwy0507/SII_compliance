"""Read-only potential-reward reconstruction from completed training traces.

Can run during training. Never labels an unfinished episode terminal, loads
validation trajectories, constructs an environment, or steps a simulator.
"""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def read(path):return json.loads(path.read_text())


def require(condition,message):
    if not condition:raise ValueError(message)


def reconstruct(observations,phases,gamma,terminal_base=None):
    """Pure audit calculation; None means uncompleted, never zero terminal base."""
    obs=np.asarray(observations);phases=np.asarray(phases)
    require(obs.ndim==2 and obs.shape[1]==48 and len(obs)==len(phases),'Invalid observation/phase sequence')
    require(np.isfinite(obs).all() and np.isfinite(phases).all(),'Nonfinite trace')
    require(np.all(phases==np.floor(phases)) and np.all((phases>=0)&(phases<=3)),'Invalid stage metadata')
    phi=(phases-np.minimum(np.linalg.norm(obs[:,20:23],axis=1)/.30,1.))/3
    n=len(phi)
    if terminal_base is not None:
        require(n>0,'Empty completed episode')
        after=np.r_[phi[1:],0.];shaping=gamma*after-phi;base=np.zeros(n);base[-1]=terminal_base
        expected=-phi[0];known=n;missing=0
    else:
        # QueuePolicy stores obs only after receiving an action. Budget close
        # cancels the next queued actor boundary before storing its observation.
        shaping=gamma*phi[1:]-phi[:-1];base=np.zeros(max(0,n-1));known=max(0,n-1);missing=int(n>0)
        expected=float(-phi[0]+gamma**known*phi[-1]) if n else 0.
    discounts=gamma**np.arange(known);rewards=shaping+base
    actual=float(discounts@shaping);residual=actual-expected
    require(abs(residual)<1e-10,'Potential telescoping failed')
    return dict(samples=n,known_rewards=known,unrecoverable_boundary_rewards=missing,
        terminal_applied=terminal_base is not None,terminal_base=terminal_base,
        initial_potential=float(phi[0]) if n else None,last_recorded_potential=float(phi[-1]) if n else None,
        discounted_shaping=actual,expected_discounted_shaping=float(expected),telescoping_residual=float(residual),
        known_discounted_base=float(discounts@base),known_discounted_return=float(discounts@rewards),
        known_undiscounted_return=float(rewards.sum()),
        float32_reward_discounted_return=float(discounts@rewards.astype(np.float32).astype(float)),
        known_rewards_values=rewards.tolist(),known_potential_difference_values=shaping.tolist())


def frozen_reward(snapshot):
    path=snapshot/'scripts/canonical48_potential_reward_20260924.py'
    spec=importlib.util.spec_from_file_location('audited_frozen_potential',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    # Extract the actual pure evaluator rather than importing its simulator bridge.
    tree=ast.parse((snapshot/'scripts/canonical48_rl_env_20260923.py').read_text())
    function=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='evaluation_summary')
    ns={};exec(compile(ast.Module(body=[function],type_ignores=[]),str(snapshot/'scripts/canonical48_rl_env_20260923.py'),'exec'),ns)
    return module,ns['evaluation_summary']


def analyze_episode(folder,gamma,source_spec,reward_module,evaluator):
    trace=folder/'actor_trace.npz';result_path=folder/'rollout.json';partial_path=folder/'partial_episode.json'
    if not trace.exists():
        return dict(episode=folder.name,status='pending_trace',samples=None,
                    result_present=result_path.exists(),partial_marker_present=partial_path.exists(),counted_complete=False)
    before=sha(trace)
    try:
        with np.load(trace,allow_pickle=False) as z:
            obs=z['observation'].copy();actions=z['action'].copy();phases=z['phase_reward_metadata'].copy()
    except (EOFError,ValueError,zipfile.BadZipFile):
        return dict(episode=folder.name,status='trace_write_in_progress',samples=None,counted_complete=False)
    if sha(trace)!=before:return dict(episode=folder.name,status='trace_changed_during_read',samples=None,counted_complete=False)
    if obs.size==0:obs=np.empty((0,48))
    require(actions.shape==(len(obs),7) or len(obs)==0,'Action trace shape mismatch')
    row=dict(episode=folder.name,trace_sha256=before)
    if result_path.exists():
        require(not partial_path.exists(),'Both completed and partial markers present')
        result=read(result_path);evaluation=evaluator(result,source_spec)
        base=5.*bool(evaluation['development_gate'])-5.*bool(result['invalid_physics'] or result['upstream_contact'])
        require(not (evaluation['development_gate'] and (result['invalid_physics'] or result['upstream_contact'])),'Contradictory final labels')
        with np.load(folder/'rollout.npz',allow_pickle=False) as z:
            require(np.array_equal(actions,z['action']) and np.array_equal(phases,z['stage']),'Actor vs rollout sequence mismatch')
            require(np.array_equal(obs,z['observation']),'Actor vs rollout observation mismatch')
        row.update(status='complete',counted_complete=True,result_sha256=sha(result_path),evaluation=evaluation,
                   invalid_physics=bool(result['invalid_physics']),upstream_contact=bool(result['upstream_contact']))
    else:
        base=None;row.update(status='partial' if partial_path.exists() else 'unscored_trace',counted_complete=False)
        if partial_path.exists():
            marker=read(partial_path);require(marker['samples']==len(actions),'Partial marker count mismatch')
            row['partial_marker']=marker
    calc=reconstruct(obs,phases,gamma,base)
    # Match an independently written expression against the exact frozen source.
    maximum=0.
    for i,value in enumerate(calc['known_rewards_values']):
        terminal=base is not None and i==len(obs)-1
        actual,_=reward_module.shaped_reward(obs[i],int(phases[i]),None if terminal else obs[i+1],
            None if terminal else int(phases[i+1]),terminal=terminal,
            gate_success=bool(row['evaluation']['development_gate']) if terminal else False,
            invalid_or_upstream=bool(row['invalid_physics'] or row['upstream_contact']) if terminal else False)
        maximum=max(maximum,abs(value-actual))
    require(maximum<1e-12,'Frozen reward source reconstruction mismatch')
    row.update(calc,frozen_reward_max_error=maximum)
    row['discounted_return_from_reset']=calc['known_discounted_return'] if base is not None else None
    row['partial_boundary_note']=None if base is not None else 'Final next observation was not persisted; last executed transition reward and rollout bootstrap value cannot be exactly reconstructed. Prefix remains nonterminal.'
    return row


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    require(not args.output.exists(),'Fresh audit output required');run=args.run.resolve();manifest=read(run/'manifest.json')
    require(isinstance(manifest['reward'],dict) and manifest['reward']['version']=='push4_gate_potential_v1','Not the potential-reward experiment')
    entry=Path(manifest['argv'][0]);entry=entry if entry.is_absolute() else ROOT/entry;snapshot=entry.resolve().parents[1]
    source_hashes={}
    for path,value in manifest['source_hashes'].items():
        got=sha(snapshot/path);require(got==value,'Frozen source changed '+path);source_hashes[path]=got
    for path,key in [(entry,'experiment_entrypoint_sha256'),(snapshot/'tools/run_canonical48_ppo_20260923.py','base_workflow_sha256')]:
        require(sha(path)==manifest[key],'Frozen entry/workflow changed '+key)
    reward,evaluator=frozen_reward(snapshot);gamma=float(manifest['training']['gamma'])
    require(gamma==reward.GAMMA==manifest['reward']['gamma']==.995,'Gamma mismatch')
    require(reward.protocol()==manifest['reward'],'Reward manifest differs from frozen code')
    progress_before=read(run/'progress.json') if (run/'progress.json').exists() else None
    rows=[analyze_episode(folder,gamma,manifest['source_fixtures']['train'],reward,evaluator)
          for folder in sorted((run/'train').glob('episode_*'))]
    complete=[x for x in rows if x['counted_complete']];finished=(run/'COMPLETE.json').exists()
    saved_samples=sum(x.get('samples') or 0 for x in rows)
    if finished:require(saved_samples==manifest['training']['timesteps'],'Completed run sample budget mismatch')
    report=dict(scope='train-only offline reconstruction; no simulator/validation/model selection',
        audited_utc=datetime.now(timezone.utc).isoformat(),run=str(run),snapshot=str(snapshot),
        experiment_complete=finished,experiment_failed=(run/'FAILED.json').exists(),
        manifest_sha256=sha(run/'manifest.json'),reward_source_sha256=sha(snapshot/'scripts/canonical48_potential_reward_20260924.py'),
        source_files_verified=len(source_hashes),source_sha256=source_hashes,tool_sha256=sha(Path(__file__)),
        progress_before=progress_before,progress_after=read(run/'progress.json') if (run/'progress.json').exists() else None,
        gamma=gamma,planned_steps=manifest['training']['timesteps'],persisted_action_samples=saved_samples,
        complete_episodes=len(complete),task_successes=sum(x['evaluation']['task_success'] for x in complete),
        gate_successes=sum(x['evaluation']['development_gate'] for x in complete),
        complete_episode_max_telescoping_error=max((abs(x['telescoping_residual']) for x in complete),default=None),rows=rows,
        limitations=['Actual Gym reward/terms and SB3 rollout values/advantages were not persisted; reconstruction is not a direct buffer comparison.',
            'A saved budget-partial trace lacks its final next actor observation; only its first N-1 rewards are reconstructible, with no terminal override.',
            'Running episodes may not yet have actor_trace.npz; reported persisted samples need not equal live progress.',
            'Reward is returned in float64 but DummyVecEnv stores float32 rewards; float32 reconstructed return is shown separately.',
            'Finite-task terminated=True correctly prevents terminal bootstrap; nonterminal rollout64 still bootstraps.',
            'The shaping identity is pathwise and does not prove PPO convergence, critic Markov sufficiency, or physical performance.'])
    lines=['# Potential PPO训练奖励独立审计','',f"运行完成：{finished}；已持久化动作：{saved_samples}/{manifest['training']['timesteps']}；完整训练回合：{len(complete)}。仅统计已落盘序列，不把partial或正在写入的轨迹当终端。",'',
        '| episode | 状态 | 动作/可复算reward数 | task/gate | 基础终端奖励 | 完整折扣return | 潜势恒等式残差 |',
        '|---|---|---|---|---|---|---|']
    for x in rows:
        done=x['counted_complete'];e=x.get('evaluation',{});ret=x.get('discounted_return_from_reset')
        lines.append(f"| {x['episode']} | {x['status']} | {x.get('samples')}/{x.get('known_rewards')} | {e.get('task_success')}/{e.get('development_gate')} | {x.get('terminal_base')} | {'—' if ret is None else f'{ret:.8f}'} | {x.get('telescoping_residual')} |")
    lines+=['',f"冻结源码{len(source_hashes)}项、入口/base workflow以及gamma/reward manifest一致。完整回合按真实obs/phase和冻结evaluation重算；新势函数奖励未调用旧密集reward。",'',
        '完整回合discounted shaping = −Φ(initial)，基础奖励仅在终端加入；本工具同时计算float32奖励折扣回报以反映VecEnv存储精度。partial已知前缀使用−Φ(initial)+γ^KΦ(last recorded)，不把末尾势设为零。','',
        '审计限制：没有保存Gym实际reward/terms或SB3 buffer，不能逐项核验当时被PPO消费的值；partial最后一个next observation未保存，最后一项reward及critic bootstrap不可精确恢复。源码和真实序列足以完整复算自然终止回合。运行中的缺失trace标pending，训练完成前不把样本数不足当失败。']
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text('\n'.join(lines)+'\n');args.output.with_suffix('.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(output=str(args.output),complete=finished,episodes=len(complete),saved_samples=saved_samples,
                         telescoping=report['complete_episode_max_telescoping_error'])))


if __name__=='__main__':main()
