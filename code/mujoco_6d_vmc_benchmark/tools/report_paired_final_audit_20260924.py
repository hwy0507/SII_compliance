"""Final-only offline handoff: run the frozen auditor and verify final artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
import types
import zipfile
import numpy as np


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):return json.loads(Path(path).read_text())


def require(ok,message):
    if not ok:raise ValueError(message)


def validate_model_seed(model,manifest,complete):
    require('seed' in model,'Final model seed metadata missing')
    expected=manifest['training']['seed']
    require(model['seed']==expected,'Final model seed metadata mismatch')
    if 'seed' in complete:
        require(complete['seed']==expected,'COMPLETE seed metadata mismatch')
    return expected


def validate_evaluation_trace(raw,result,episode):
    observation=np.asarray(raw['observation']);count=len(observation)
    require(1<=count<=600 and observation.shape==(count,48),'Invalid final evaluation length/shape')
    require(episode['complete'] and episode['transitions']==count,'Final eval lacks audited terminal transition')
    early=count<600
    require(not early or bool(result['invalid_physics']),'Short eval without actual invalid-physics termination')
    times=np.asarray(raw['time'])
    require(times.shape==(count,) and np.isfinite(times).all(),'Invalid evaluation timestamps')
    require(np.allclose(times,.04*np.arange(1,count+1),rtol=0.,atol=1e-6),'Action count/duration mismatch')
    require(abs(result['duration_s']-times[-1])<1e-6,'Result/raw duration mismatch')
    window=min(10,count)
    endpoint=float(np.mean(np.linalg.norm(raw['position'][-window:]-raw['target'][-window:],axis=1)))
    return dict(action_steps=count,duration_s=result['duration_s'],safety_early_termination=early,
                invalid_physics=bool(result['invalid_physics']),endpoint_window_frames=window),endpoint


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('run','snapshot','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--audit-output',type=Path)
    args=parser.parse_args();run=args.run.resolve();snapshot=args.snapshot.resolve();output=args.output
    audit_output=args.audit_output or output.with_name(output.stem+'_transitions.json')
    require(not output.exists() and not output.with_suffix('.md').exists() and not audit_output.exists(),'Fresh report outputs required')
    require(audit_output.resolve()!=output.resolve(),'Flat audit and report paths must differ')
    complete=read(run/'COMPLETE.json');manifest=read(run/'manifest.json')
    require(complete['status']=='complete' and not (run/'FAILED.json').exists(),'Final COMPLETE required; no partial-run success')
    require(complete['training_steps']==8192 and complete['normalization_frozen'],'Wrong final budget or normalization')
    auditor=snapshot/'tools/audit_paired_transitions_20260924.py'
    require(sha(auditor)==manifest['source_hashes']['tools/audit_paired_transitions_20260924.py'],'Frozen auditor changed')
    # Compile verified frozen source without creating bytecode in the snapshot.
    module=types.ModuleType('verified_frozen_final_auditor');module.__file__=str(auditor)
    exec(compile(auditor.read_text(),str(auditor),'exec'),module.__dict__)
    audit=module.audit_run(run,snapshot);audit['audit_tool_sha256']=sha(auditor)
    require(audit['training_transitions']==8192,'Frozen audit not full training budget')
    with zipfile.ZipFile(run/'ppo_final.zip') as archive:model= json.loads(archive.read('data'))
    require(model['num_timesteps']==8192 and model['_n_updates']==complete['updates']==384,'Not fixed-final8192 model')
    validate_model_seed(model,manifest,complete)
    for name,field in [('ppo_final.zip','checkpoint_sha256'),('vecnormalize_train_only.pkl','normalizer_sha256')]:
        require(sha(run/name)==complete[field],'Final artifact hash mismatch: '+name)
    evaluations=read(run/'evaluation.json')
    require(evaluations==complete['results'],'Final evaluation aggregate mismatch')
    require(set(evaluations)=={'train/zero','train/ppo','validation/zero','validation/ppo'},'Missing final evaluation')
    ns=module.load_frozen(snapshot,manifest);rows=[]
    for key in ('train/zero','train/ppo','validation/zero','validation/ppo'):
        split,policy=key.split('/');directory=run/'eval'/split/policy/'episode_00000'
        result=read(directory/'rollout.json');recomputed=ns['evaluation_summary'](result,manifest['fixture_specs'][split])
        require(all(evaluations[key][name]==value for name,value in recomputed.items()),'Evaluation recomputation mismatch: '+key)
        audited=[row for row in audit['episodes'] if Path(row['directory']).resolve()==directory.resolve()]
        require(len(audited)==1,'Final evaluation missing from frozen transition audit')
        with np.load(directory/'rollout.npz',allow_pickle=False) as raw:
            timing,endpoint=validate_evaluation_trace(raw,result,audited[0])
        require(abs(endpoint-recomputed['endpoint_error_m'])<1e-12,'Endpoint raw evidence mismatch')
        rows.append(dict(condition=key,**recomputed,**timing,lift_m=result['lift_m'],result_sha256=sha(directory/'rollout.json')))
    train=[row for row in audit['episodes'] if Path(row['directory']).is_relative_to(run/'train')]
    full=[row for row in train if row['complete']];partial=[row for row in train if not row['complete'] and row['transitions']]
    train_summary=dict(episodes=len(train),complete_episodes=len(full),complete_task_success=sum(row['task_success'] for row in full),
        complete_development_gate=sum(row['development_gate'] for row in full),
        complete_step_counts=[row['transitions'] for row in full],partial_step_counts=[row['transitions'] for row in partial],
        complete_and_partial_rewards_audited=8192,sb3_received_rewards=audit['sb3_received_rewards'])
    artifacts={name:dict(path=str(run/name),sha256=sha(run/name)) for name in
        ('ppo_final.zip','vecnormalize_train_only.pkl','manifest.json','COMPLETE.json','evaluation.json','model_architecture.json')}
    audit_output.parent.mkdir(parents=True,exist_ok=True)
    audit_output.write_text(json.dumps(audit,indent=2,allow_nan=False)+'\n')
    report=dict(mode=manifest['mode'],seed=manifest['training']['seed'],passed=True,scope='Complete fixed-final8192 run plus all four final evaluations; no intermediate checkpoint selection',
        frozen_transition_audit=audit,training=train_summary,evaluations=rows,final_artifacts=artifacts,
        flat_transition_audit=dict(path=str(audit_output.resolve()),sha256=sha(audit_output)),
        final_model_metadata=dict(num_timesteps=model['num_timesteps'],updates=model['_n_updates'],seed=model['seed']),
        final_report_tool_sha256=sha(__file__),limitations=[
            'Endpoint is distance to current stage waypoint; smaller error before stage3 is not completed lift.',
            'Force is max external single-object resultant contact force, not simultaneous sum over all objects.',
            'Zero parameter6 is analytic nominal VMC; zero direct7 is zero execution residual. They are different controls.',
            'Gym/VecEnv reward conversion is verified; actual critic values, advantages and bootstrap values were not logged.',
            'Single seed and one train/one validation fixture do not establish generalization or paper reproduction.'])
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    lines=[f"# {manifest['mode']} seed={manifest['training']['seed']} PPO8192：最终独立审计",'',
        f"完整运行通过：固定8192步/384更新、四项最终eval、冻结源、全部实际transition奖励和SB3 float32转换已核验。完整训练episode {len(full)}条，task {train_summary['complete_task_success']}/{len(full)}，gate {train_summary['complete_development_gate']}/{len(full)}；partial步数{train_summary['partial_step_counts']}。",'',
        '| 条件 | task/gate | steps / 实际s / 安全早停 | final stage | lift m | 当前阶段endpoint mm | 外部单对象力峰N |',
        '|---|---|---|---:|---:|---:|---:|']
    for row in rows:lines.append(f"| {row['condition']} | {row['task_success']}/{row['development_gate']} | {row['action_steps']} / {row['duration_s']:.2f} / {row['safety_early_termination']} | {row['final_stage']} | {row['lift_m']:.6g} | {1000*row['endpoint_error_m']:.3f} | {row['peak_external_resultant_force_n']:.3f} |")
    lines+=['','stage1是抓取对齐，stage2闭爪，stage3抬升；当前waypoint误差不能替代最终抬升成功。两模式zero含义不同，不将zero6解析VMC与zero7执行残差混为一谈。', '',
        '安全早停作为已终止的失败评估保留，须有invalid_physics及独立terminal审计；实际时长按记录核对，未伪称满24s。endpoint仅取实有末min(10,步数)帧。', '',
        '审计报告中的逐episode列表包含完整与partial全部实际奖励、末next、控制器重播和telescoping残差。未记录critic/advantages，不能据此宣称实际bootstrap值已核验；单seed/少量fixture亦不构成泛化结论。','',
        f"供后续prepare入口使用的flat原审计：`{audit_output.resolve()}`，SHA256 `{sha(audit_output)}`。",'',
        f"最终checkpoint SHA256 `{complete['checkpoint_sha256']}`。",'',f"训练normalizer SHA256 `{complete['normalizer_sha256']}`。"]
    output.with_suffix('.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(passed=True,mode=manifest['mode'],output=str(output),flat_audit=str(audit_output),training=train_summary,artifacts=artifacts)))


if __name__=='__main__':main()
