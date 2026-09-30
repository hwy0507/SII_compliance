"""Compare all six predeclared final runs only after all independent audits pass."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

SEEDS=(20260923,20260924,20260925)
MODES=('parameter6','direct7')


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):return json.loads(Path(path).read_text())


def load_run(report_path,seed,mode):
    report=read(report_path)
    require(report['passed'] and report['mode']==mode,'Independent final audit missing or wrong mode')
    artifacts=report['final_artifacts']
    for name,artifact in artifacts.items():require(sha(artifact['path'])==artifact['sha256'],'Final artifact changed: '+name)
    manifest=read(artifacts['manifest.json']['path']);complete=read(artifacts['COMPLETE.json']['path'])
    require(manifest['training']['seed']==seed and manifest['mode']==mode,'Manifest seed/mode mismatch')
    require(report.get('seed',seed)==seed,'Final report seed mismatch')
    with zipfile.ZipFile(artifacts['ppo_final.zip']['path']) as archive:model=json.loads(archive.read('data'))
    require('seed' in model and model['seed']==seed,'Final checkpoint must explicitly match seed')
    require(model['num_timesteps']==8192 and model['_n_updates']==384,'Not fixed final8192 model')
    require(complete['status']=='complete' and complete.get('seed',seed)==seed,'Completion seed/status mismatch')
    require(not (Path(artifacts['COMPLETE.json']['path']).parent/'FAILED.json').exists(),'Run has FAILED marker')
    flat_ref=report['flat_transition_audit'];require(sha(flat_ref['path'])==flat_ref['sha256'],'Flat audit changed')
    flat=read(flat_ref['path'])
    require(flat['passed'] and flat['training_transitions']==8192,'Full training audit absent')
    require(flat['manifest_sha256']==artifacts['manifest.json']['sha256'],'Flat audit manifest mismatch')
    require(flat['sb3_received_rewards']['transitions']==8192 and flat['sb3_received_rewards']['all_float32_conversions_exact'],'SB3 reward audit incomplete')
    expected={'train/zero','train/ppo','validation/zero','validation/ppo'}
    require({row['condition'] for row in report['evaluations']}==expected,'Four final evaluations required')
    keys=('condition','task_success','development_gate','final_stage','endpoint_error_m','lift_m',
          'action_steps','duration_s','safety_early_termination','invalid_physics')
    evaluations=[{key:row[key] for key in keys} for row in report['evaluations']]
    return dict(seed=seed,mode=mode,training=report['training'],evaluations=evaluations,
        final_model_metadata=dict(seed=model['seed'],steps=model['num_timesteps'],updates=model['_n_updates']),
        report_provenance=dict(path=str(report_path.resolve()),sha256=sha(report_path)),
        flat_audit_provenance=flat_ref,final_artifacts=artifacts),manifest


def controlled_direct_seed_difference(audits,rows):
    # Bind the already completed seed23/24 controls and seed24 policy replay;
    # do not imply that a pending seed25 deployment has been verified.
    reference=next(row for row in rows if row['seed']==20260923 and row['mode']=='direct7')
    current=next(row for row in rows if row['seed']==20260924 and row['mode']=='direct7')
    zero_path=audits/'seed20260924_direct7_zero.json';replay_path=audits/'seed20260924_direct7_replay.json'
    zero=read(zero_path);replay=read(replay_path)
    require(zero['passed'] and zero['seed']==20260924 and zero['reference_seed']==20260923 and zero['mode']=='direct7','Wrong controlled zero evidence')
    for prefix,row in ((zero['reference_run'],reference),(zero['current_run'],current)):
        for name in ('manifest.json','COMPLETE.json'):
            require(zero['input_sha256'][str(Path(prefix)/name)]==row['final_artifacts'][name]['sha256'],'Zero evidence run binding mismatch')
    require(all(zero['comparisons'][split]['passed'] for split in ('train','validation')),'Zero fixture parity failed')
    require(replay['passed'] and replay['mode']=='direct7' and replay['end_to_end_exact'],'Deployment input replay mismatch')
    for key,name in [('training_manifest_sha256','manifest.json'),('checkpoint_sha256','ppo_final.zip'),('normalizer_sha256','vecnormalize_train_only.pkl')]:
        require(replay['metadata'][key]==current['final_artifacts'][name]['sha256'],'Deployment replay artifact binding mismatch')
    return dict(mode='direct7',compared_training_seeds=[20260923,20260924],zero_fixture_parity=True,
        seed20260924_deployment_input_replay_exact=True,
        evidence={str(path.resolve()):sha(path) for path in (zero_path,replay_path)},
        interpretation='Different training seeds change initialization/sampling jointly; this is not evidence that retraining the same seed is irreproducible. Deployment input replay does not synthesize a new closed-loop trajectory.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('original-audits','multiseed-audits','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();require(not args.output.exists() and not args.output.with_suffix('.md').exists(),'Fresh outputs required')
    rows=[];manifests=[]
    for seed in SEEDS:
        for mode in MODES:
            path=(args.original_audits/f'{mode}_final_audit.json' if seed==20260923 else
                  args.multiseed_audits/f'seed{seed}_{mode}_final.json')
            row,manifest=load_run(path,seed,mode);rows.append(row);manifests.append(manifest)
    baseline=manifests[0]
    for row,manifest in zip(rows,manifests):
        protocol_key='protocol_sha256' if row['seed']==20260923 else 'base_protocol_sha256'
        require(protocol_key in manifest and manifest[protocol_key]==baseline['protocol_sha256'],'Base protocol hash mismatch')
        for key in ('fixture_specs','asset_hashes','nominal_options','reward','runtime','device'):
            require(manifest[key]==baseline[key],'Comparison protocol mismatch: '+key)
        require({k:v for k,v in manifest['training'].items() if k!='seed'}==
                {k:v for k,v in baseline['training'].items() if k!='seed'},'Learning budget/options differ beyond seed')
        require(all(manifest['source_hashes'].get(name)==digest for name,digest in baseline['source_hashes'].items()),'Original execution source bytes differ')
    aggregate={}
    for mode in MODES:
        subset=[row for row in rows if row['mode']==mode];conditions={}
        for condition in ('train/zero','train/ppo','validation/zero','validation/ppo'):
            selected=[next(x for x in row['evaluations'] if x['condition']==condition) for row in subset]
            conditions[condition]=dict(training_seeds=3,task_successful_seeds=sum(x['task_success'] for x in selected),
                gate_successful_seeds=sum(x['development_gate'] for x in selected),
                final_stages_in_seed_order=[x['final_stage'] for x in selected],
                endpoint_mm_in_seed_order=[1000*x['endpoint_error_m'] for x in selected])
        aggregate[mode]=conditions
    controlled=controlled_direct_seed_difference(args.multiseed_audits,rows)
    result=dict(scope='All three predeclared training seeds and both modes; canonical train/validation fixtures only, not the six-fixture deployment matrix',
        seeds=list(SEEDS),training_runs=6,total_online_training_steps=6*8192,
        same_original_execution_source_files=len(baseline['source_hashes']),same_fixture_and_assets=True,
        same_base_protocol_sha256=baseline['protocol_sha256'],
        same_optimizer_options_except_seed=True,rows=rows,aggregate=aggregate,controlled_direct_seed_comparison=controlled,tool_sha256=sha(__file__),
        interpretation=['Three training seeds per method, one fixed training fixture; not18 independent training repetitions.',
            'Training episode successes come from evolving stochastic policies and are not independent final-policy evaluations.',
            'parameter6 has analytic VMC memory/nominal controller prior and six parameter outputs; direct7 outputs seven execution controls.',
            'Each method has24576 online transitions across three seeds; no exported demonstration was injected into these PPO runs.',
            'Endpoint uses current stage target. No pooled endpoint average across differing stages; all failures retained.',
            'No sampled training torque/speed metrics imported into a physics-substep comparison table.',
            'Three seeds describe this fixed small-budget recipe; no convergence, broad generalization, or method superiority established.'])
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    lines=['# 配对PPO：三个预声明训练seed的最终对照','',
        '全部六run完成独立审计，固定每run8192步/384更新，最终模型seed显式匹配。旧报告、新报告、flat奖励审计及模型/normalizer/manifest hash均逐项绑定；原执行源、基础协议hash、fixture、资产和除seed外的学习参数一致。未选择中间checkpoint，未丢弃失败。','',
        '| 训练seed | 模式 | 完整训练episode task/gate成功数 | 完整episode数 | partial步数 |',
        '|---|---|---|---:|---|']
    for row in rows:
        train=row['training'];lines.append(f"| {row['seed']} | {row['mode']} | {train['complete_task_success']}/{train['complete_development_gate']} | {train['complete_episodes']} | {train['partial_step_counts']} |")
    lines+=['','训练episode来自不断更新且带采样探索的策略，其成功数不能当作最终模型的独立重复测试；三个训练seed才是本对照的训练重复单位。','',
        '| seed | 模式 | 最终评估 | task/gate | stage | 当前阶段endpoint mm | lift mm | 步数/实际s/早停 |',
        '|---|---|---|---|---:|---:|---:|---|']
    for row in rows:
        for ev in row['evaluations']:
            lines.append(f"| {row['seed']} | {row['mode']} | {ev['condition']} | {ev['task_success']}/{ev['development_gate']} | {ev['final_stage']} | {1000*ev['endpoint_error_m']:.3f} | {1000*ev['lift_m']:.3f} | {ev['action_steps']}/{ev['duration_s']:.2f}/{ev['safety_early_termination']} |")
    lines+=['','| 最终PPO条件 | parameter6成功seed数 | direct7成功seed数 |', '|---|---|---|']
    for condition in ('train/ppo','validation/ppo'):
        lines.append(f"| {condition} | {aggregate['parameter6'][condition]['task_successful_seeds']}/3 | {aggregate['direct7'][condition]['task_successful_seeds']}/3 |")
    lines+=['','stage1仍是抓取对齐、尚未闭爪抬升；stage2闭爪，stage3抬升。endpoint指当时阶段目标，不能跨stage平均后宣称共同精度改善。零控制也不同：parameter6 zero是训练名义参数的解析VMC，direct7 zero是全零action7。','',
        'direct7的seed20260923最终train/validation均到stage3，seed20260924均停在stage1。对应两个fixture的同模式zero原始轨迹/MJB已精确核对，seed20260924最终模型部署输入回放也与存档执行动作逐值一致，证据hash已绑定到JSON。因此这里看到的是改变训练seed后初始化/采样整体不同所伴随的策略差异，不能分离归因给其中一个因素，也不能据此声称同seed不可复现。部署输入回放不是新造的闭环物理轨迹。','',
        '这套配方只在同一个训练fixture学习，每分支三个seed合计24576条在线transition，无示范数据注入。parameter6含VMC隐状态、反馈先验与六维参数接口，direct7直接输出七维控制；结果不能解释成只改变网络输出维度的消融。三个seed仅描述小预算配方的重复性，不能保证收敛或跨场景泛化。','',
        '本报告不包含六条件部署矩阵，也不把训练日志中的低频力矩/速度混入50µs子步主表。后续六fixture应先按训练seed聚合，再描述三个训练seed，不能把相关fixture或训练episode当作额外独立训练重复。','',
        f"完整数值和每个原报告/模型hash见同名JSON；汇总工具SHA256 `{result['tool_sha256']}`。"]
    args.output.with_suffix('.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(output=str(args.output),runs=6,aggregate=aggregate)))


if __name__=='__main__':main()
