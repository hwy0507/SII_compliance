"""Compare only the two fixed-final-budget local PPO experiments after COMPLETE."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
import zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def read(p):return json.loads(p.read_text())


def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def require(ok,message):
    if not ok:raise ValueError(message)


def inspect_run(run):
    complete=read(run/'COMPLETE.json');manifest=read(run/'manifest.json');evaluation=read(run/'evaluation.json')
    require(complete['status']=='complete' and not (run/'FAILED.json').exists(),'Incomplete/failed run')
    require(complete['results']==evaluation,'Final evaluation aggregate mismatch')
    require(complete['normalization_frozen'],'Evaluation normalization not frozen')
    require(sha(run/'ppo_final.zip')==complete['checkpoint_sha256'],'Final checkpoint hash mismatch')
    with zipfile.ZipFile(run/'ppo_final.zip') as z:data=json.loads(z.read('data'))
    require(data['num_timesteps']==8192 and manifest['training']['timesteps']==8192,'Wrong final budget')
    entry=Path(manifest['argv'][0]);entry=entry if entry.is_absolute() else ROOT/entry;snapshot=entry.resolve().parents[1]
    mismatches=[k for k,v in manifest['source_hashes'].items() if sha(snapshot/k)!=v]
    require(not mismatches,'Source snapshot mismatch '+str(mismatches))
    argv=manifest['argv'];assets=Path(argv[argv.index('--assets')+1])/'menagerie'
    assets=assets if assets.is_absolute() else ROOT/assets
    require(all(sha(assets/k)==v for k,v in manifest['asset_hashes'].items()),'Recorded model asset changed')
    tree=ast.parse((snapshot/'scripts/canonical48_rl_env_20260923.py').read_text())
    func=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='evaluation_summary')
    ns={};exec(compile(ast.Module(body=[func],type_ignores=[]),'<frozen pure evaluator>','exec'),ns)
    rows=[]
    for split in ('train','validation'):
        for policy in ('zero','ppo'):
            key=f'{split}/{policy}';d=run/'eval'/split/policy/'episode_00000'
            result=read(d/'rollout.json');expected=ns['evaluation_summary'](result,manifest['source_fixtures'][split])
            require(all(evaluation[key][k]==v for k,v in expected.items()),'Evaluation recomputation mismatch '+key)
            with np.load(d/'actor_trace.npz',allow_pickle=False) as z:require(z['observation'].shape==(600,48),'Incomplete evaluation')
            with np.load(d/'rollout.npz',allow_pickle=False) as z:
                endpoint=float(np.mean(np.linalg.norm(z['position'][-10:]-z['target'][-10:],axis=1)))
                require(abs(endpoint-expected['endpoint_error_m'])<1e-12,'Endpoint recomputation mismatch')
            rows.append(dict(policy=policy,**expected,lift_m=result['lift_m'],result_sha256=sha(d/'rollout.json'),
                             actor_trace_sha256=sha(d/'actor_trace.npz')))
    return dict(run=str(run.resolve()),manifest=manifest,rows=rows,snapshot=str(snapshot),
                artifacts=dict(checkpoint=str((run/'ppo_final.zip').resolve()),checkpoint_sha256=sha(run/'ppo_final.zip'),
                  normalizer=str((run/'vecnormalize_train_only.pkl').resolve()),normalizer_sha256=sha(run/'vecnormalize_train_only.pkl'),
                  num_timesteps=data['num_timesteps'],updates=data['_n_updates'],manifest_sha256=sha(run/'manifest.json')))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--old',type=Path,required=True)
    p.add_argument('--potential',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    require(not args.output.exists(),'Fresh output required');old=inspect_run(args.old);new=inspect_run(args.potential)
    require(old['manifest']['source_fixtures']==new['manifest']['source_fixtures'],'Different evaluation fixture specs')
    require(old['manifest']['training']==new['manifest']['training'],'Different optimizer/budget specification')
    require(old['manifest']['versions']==new['manifest']['versions'],'Different software versions')
    require(old['manifest']['asset_hashes']==new['manifest']['asset_hashes'],'Different model asset hashes')
    shared=set(old['manifest']['source_hashes'])&set(new['manifest']['source_hashes'])
    different=[k for k in sorted(shared) if old['manifest']['source_hashes'][k]!=new['manifest']['source_hashes'][k]]
    core=['run_panel_push_20260920.py','run_primitive_teacher_v7_20260917.py','canonical48_rl_env_20260923.py',
          'run_vmc_6d_constrained_push_20260918.py','wbc_velocity_residual_core.py','wbc_velocity_residual_env.py',
          'audited_velocity_env.py','fixed_panda_wbc.py','haptic_vmc_teacher_20260916.py']
    require(not any('scripts/'+k in different for k in core),'Relevant bridge/control source changed')
    parity={}
    for split in ('train','validation'):
        arrays={}
        for filename in ('actor_trace.npz','physics_states.npz','contact_samples.npz','rollout.npz'):
            a=args.old/'eval'/split/'zero'/'episode_00000'/filename;b=args.potential/'eval'/split/'zero'/'episode_00000'/filename
            with np.load(a,allow_pickle=False) as x,np.load(b,allow_pickle=False) as y:
                require(set(x.files)==set(y.files),'Zero trace key mismatch')
                for k in x.files:
                    equal=np.array_equal(x[k],y[k],equal_nan=True) if x[k].dtype.kind in 'fc' else np.array_equal(x[k],y[k])
                    arrays[filename+':'+k]=dict(equal=bool(equal),shape=list(x[k].shape))
        parity[split]=dict(all_equal=all(x['equal'] for x in arrays.values()),arrays=arrays)
    changes={}
    for a,b in zip(old['rows'],new['rows']):
        changes[a['split']+'/'+a['policy']]=dict(task_before=a['task_success'],task_after=b['task_success'],
            gate_before=a['development_gate'],gate_after=b['development_gate'],
            final_stage_before=a['final_stage'],final_stage_after=b['final_stage'],
            lift_before_m=a['lift_m'],lift_after_m=b['lift_m'],
            endpoint_delta_mm=1000*(b['endpoint_error_m']-a['endpoint_error_m']),
            peak_single_object_resultant_force_delta_n=b['peak_external_resultant_force_n']-a['peak_external_resultant_force_n'])
    out=dict(scope='Same local platform two frozen-final8192 experiments; single seed and two evaluation fixtures, not DGX comparison',
        old={k:v for k,v in old.items() if k!='manifest'},potential={k:v for k,v in new.items() if k!='manifest'},
        same_training_spec=True,same_fixture_specs=True,same_software_versions=True,
        same_model_asset_hashes=True,model_asset_files_verified=len(new['manifest']['asset_hashes']),
        different_shared_source_files=different,zero_control_trace_parity=parity,changes=changes,
        tool_sha256=sha(Path(__file__)),limitations=['No intermediate checkpoint selection or fresh simulation.',
            'Reward versions define different objectives; their episode return magnitudes are not compared as performance.',
            'Both potential PPO evaluations stop at stage1 ALIGN TO GRASP, before CLOSE GRIPPER or LOADED LIFT. Their endpoint errors are to the current stage waypoint, not the final lift goal. Old validation PPO stops at stage0, so its endpoint is a different target.',
            'Force is the maximum of external single-object resultant-force peaks in the existing substep contact audit, not the simultaneously summed force across all objects.',
            'Existing speed_p95 and peak_torque result fields are retained as original sampled metrics, not relabelled as full physics-substep speed/torque measurements.',
            'One training seed and one train/one validation fixture per frozen policy cannot establish statistically robust improvement.'])
    lines=['# 本机旧奖励与潜势奖励PPO8192：最终模型同平台对照','',
           '两轮均使用固定8192步最终模型，未选择中间checkpoint；同train/validation fixture、PPO训练参数和软件版本。此处不拼接DGX实验指标。','',
           '| 条件 | 原模型task/gate | 潜势模型task/gate | 原→潜势最终stage | 原→潜势当前阶段终点误差mm | 原→潜势外部单对象合力峰值N |',
           '|---|---|---|---|---|---|']
    for a,b in zip(old['rows'],new['rows']):lines.append(f"| {a['split']}/{a['policy']} | {a['task_success']}/{a['development_gate']} | {b['task_success']}/{b['development_gate']} | {a['final_stage']}→{b['final_stage']} | {1000*a['endpoint_error_m']:.2f}→{1000*b['endpoint_error_m']:.2f} | {a['peak_external_resultant_force_n']:.2f}→{b['peak_external_resultant_force_n']:.2f} |")
    lines+=['',f"两种zero对照原始数组完全一致：train={parity['train']['all_equal']}（{len(parity['train']['arrays'])}数组），validation={parity['validation']['all_equal']}（{len(parity['validation']['arrays'])}数组）。这核对同平台reward变化未改变zero动作物理对照，不证明跨平台动力学一致。",'',
        f"共同使用的9项bridge/控制核心源hash一致，fixture完整规格一致，{len(new['manifest']['asset_hashes'])}项模型资产hash相同且已复核当前文件。其他共享源变化明细在JSON。",'',
        '终点误差沿用最后10帧到当前任务目标的平均值，未到最终阶段时较小数值不代表完成了抬升；完整phase、task、gate记录在JSON。合力峰值来自既有物理子步逐对象接触审计；没有把25Hz速度/力矩指标改称全物理子步峰值。', '',
        '潜势PPO在train和validation均停在stage1 ALIGN TO GRASP（抓取对齐阶段，尚未闭爪/抬升）；stage2才是CLOSE GRIPPER，stage3才是LOADED LIFT。两条轨迹lift_m均约−1.41448e−7 m，实际没有抬升。15.74/15.49 mm仅是stage1当前waypoint误差，不是到最终抬升目标的误差。旧validation PPO停在stage0，两者endpoint所指目标不同，不能把94.43→15.49 mm单独解释成公平的同目标精度改善。', '',
        '结论：两个PPO模型的task/gate均为0/2。潜势模型外部单对象力峰下降，但仍未恢复任务；没有任务成功或三项指标共同改善的证据。最终训练奖励审计见PPO_POTENTIAL_REWARD_AUDIT_20260924_FINAL.md：13个完整600步episode与392步部分episode合计8192步，13个完整episode全部失败，未获得成功终端基础奖励；部分episode只可重建391个奖励，未作完整return或实际critic bootstrap验证。', '',
        '两个reward定义不同，不比较episode_reward大小来宣称改善。最终解释须同时看task/gate、阶段和力峰值；仅一次训练seed和两条fixture，不能作显著性或论文级泛化结论。','',
        f"潜势最终checkpoint：`{new['artifacts']['checkpoint']}`，SHA256 `{new['artifacts']['checkpoint_sha256']}`。",'',
        f"冻结normalizer：`{new['artifacts']['normalizer']}`，SHA256 `{new['artifacts']['normalizer_sha256']}`。",'',
        f"最终模型timesteps={new['artifacts']['num_timesteps']}，优化updates={new['artifacts']['updates']}。DGX部署前仍需推理parity和同MJB物理条件核对。"]
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text('\n'.join(lines)+'\n')
    args.output.with_suffix('.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(output=str(args.output),potential_artifacts=new['artifacts'],changes=changes)))


if __name__=='__main__':main()
