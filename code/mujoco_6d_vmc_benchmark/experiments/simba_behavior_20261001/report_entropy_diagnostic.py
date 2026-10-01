"""Audit the post-main entropy diagnostic separately from the 100k matrix."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import numpy as np
from audit_raw_metrics import audit
from report_campaign import sha, METRICS


def build(root):
    if not root.is_dir():
        raise FileNotFoundError(root)
    protocol=json.loads((root/'PROTOCOL.json').read_text())
    common=json.loads((root/'COMMON_BUDGET.json').read_text()) if (root/'COMMON_BUDGET.json').exists() else None
    rows=[];errors=[];pending=[];models=defaultdict(dict);checkpoints=[]
    for setting in ('standard','low_entropy'):
        for spec in protocol['specs']:
            name=setting+'_'+spec['id'];folder=root/'evaluation'/name
            if not (folder/'SUMMARY.json').exists():
                pending.append(name);continue
            s=json.loads((folder/'SUMMARY.json').read_text())
            if s.get('status')!='complete':
                pending.append(name);continue
            p=json.loads((folder/'PROTOCOL.json').read_text())
            checks=dict(manifest=p['manifest_sha256']==protocol['manifest_sha256'],
                dt=p['physics_dt']==.00005,duration=p['duration_s']==55,
                six_cases=len(s['rows'])==len(p['cases'])==6,
                normalizer=s.get('normalizers_before') is not None and s['normalizers_before']==s.get('normalizers_after'),
                checkpoint_step=common is not None and Path(p['checkpoint']).name=='checkpoint_step_%07d'%common['step'])
            cp=Path(p['checkpoint'])
            expected_base=Path(protocol['control_source']) if setting=='standard' else root
            checks['checkpoint_path']=cp.parent==expected_base/spec['id']
            metadata=json.loads((cp/'official_agent_state.json').read_text())
            checks['seed']=metadata['config']['seed']==spec['seed']
            checks['method']=p['method']=='rl'
            checks['checkpoint_hashes']=bool(p.get('checkpoint_sha256')) and all(
                sha(Path(k) if Path(k).is_absolute() else cp/k)==digest for k,digest in p['checkpoint_sha256'].items())
            checkpoints.append(dict(run=name,checks=checks))
            for k,v in checks.items():
                if not v:errors.append(name+': '+k)
            for i,row in enumerate(s['rows']):
                rawpath=Path(row['raw_result']);raw=json.loads(rawpath.read_text());case=row['case']
                if case!=p['cases'][i]:errors.append(name+': condition order')
                if row['metrics']!=raw['metrics']:errors.append(name+': summary/raw metrics differ')
                for k in ('seed','variant','ball_speed','person_stroke','rod_stroke'):
                    if raw['arguments'][k]!=case[k]:errors.append(name+': '+k)
                if raw['arguments']['dt']!=.00005 or raw['arguments']['duration']!=55:errors.append(name+': raw timing')
                model=sha(rawpath.with_suffix('.mjb'))
                if model!=raw['model_sha256']:errors.append(name+': model artifact hash')
                models[case['id']][name]=model
                b=row['behavior']
                if not set(raw['contact_required']).issubset(b['required_contacts']):errors.append(name+': required exposure removed')
                e=dict(run=name,setting=setting,reward=spec['reward'],seed=spec['seed'],case=case,raw=str(rawpath),
                    placement=raw['placement_complete'],physical=raw['physical_valid'],full55=raw['full_task_horizon_completed'],
                    abort_reason=raw['abort_reason'],stage=raw['final_task_stage'],events=b['event_results'],
                    joint_coverage_behavior=b['compliant_progress_success'])
                e.update({k:raw['metrics'][source]*scale for k,(source,scale) in METRICS.items()})
                rows.append(e)
    for case,hashes in models.items():
        if len(set(hashes.values()))!=1:errors.append(case+': physical model differs between policies')
    raw_audit=audit(root)
    raw_audit['expected_rows']=48
    raw_audit['complete_expected_matrix']=len(raw_audit['rows'])==48 and not raw_audit['skipped_incomplete']
    raw_audit['all54_present_not_applicable']=raw_audit.pop('all54_present')
    # The original helper's 54-case flag belongs to main; diagnostic completeness is explicit48.
    groups=[]
    for reward in ('office_task','metric'):
        for setting in ('standard','low_entropy'):
            es=[e for e in rows if e['reward']==reward and e['setting']==setting]
            seeds=sorted({e['seed'] for e in es})
            metric={}
            for key in METRICS:
                means=[np.mean([e[key] for e in es if e['seed']==seed]) for seed in seeds]
                metric[key]=dict(mean=float(np.mean(means)) if means else None,
                    seed_sd=float(np.std(means,ddof=1)) if len(means)>1 else None,
                    seed_means=[dict(seed=seed,value=float(value)) for seed,value in zip(seeds,means)])
            event=defaultdict(Counter)
            for e in es:
                for ev in e['events']:event[ev['obstacle_id']][ev['status']]+=1
            groups.append(dict(reward=reward,setting=setting,n=len(es),metrics=metric,
                placement=sum(e['placement'] for e in es),physical=sum(e['physical'] for e in es),
                full55=sum(e['full55'] for e in es),stage_counts=dict(Counter(e['stage'] for e in es)),
                event_counts={k:dict(v) for k,v in event.items()}))
    if raw_audit['rows_audited'] and not raw_audit['all_observed_pass']:errors.append('raw metric recomputation failed')
    complete=len(rows)==48 and not pending and raw_audit['complete_expected_matrix']
    out=dict(created_utc=datetime.now(timezone.utc).isoformat(),status='complete' if complete else 'partial',
        classification=protocol['classification'],common_budget=common,groups=groups,rows=rows,
        checkpoints=checkpoints,model_hashes=dict(models),errors=errors,pending=pending,
        raw_audit=raw_audit,complete_full55_matrix=complete and not errors and all(e['full55'] for e in rows),
        uncertainty='sample SD of two paired training-seed means, six conditions each; exploratory post-main diagnostic')
    dest=root/'report';dest.mkdir(exist_ok=True)
    (dest/'SUMMARY.json').write_text(json.dumps(out,indent=2)+'\n')
    lines=['# 独立熵目标诊断（主结果之后的探索）','',f'状态：{out["status"]}；共同step：{common}；已完成{len(rows)}/48条。','',
      'standard=-0.5、low_entropy=-2.0；其他训练配置相同；两奖励各2个配对seed。测试条件已经见过，不是独立确认。','',
      '| Reward | Entropy setting | n | 55s | physical | placement | RMSE cm | peak Nm | peak m/s |',
      '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for g in groups:
        values=[]
        for key in METRICS:
            v=g['metrics'][key];values.append('pending' if v['mean'] is None else f'{v["mean"]:.6g} ± {v["seed_sd"]:.4g}' if v['seed_sd'] is not None else str(v['mean']))
        lines.append('| '+' | '.join(map(str,[g['reward'],g['setting'],g['n'],g['full55'],g['physical'],g['placement'],*values]))+' |')
    lines+=['','全部失败保留。若存在提前终止，指标均值仅描述实际记录，不作完整55秒统一排名。','',
      '## 阶段及逐类局部响应','']
    for g in groups:lines.append(f'- {g["reward"]}/{g["setting"]}: stage={g["stage_counts"]}; events={g["event_counts"]}')
    lines+=['','## 审计','',f'错误：{errors}；待完成：{pending}。',
      'raw子步复算、原始时长、同条件MJB、checkpoint路径/seed/hash/共同step、manifest及记录的normalizer诊断核对；不以阶段或未曝光替代成功。']
    (dest/'REPORT.md').write_text('\n'.join(lines)+'\n')
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--diagnostic',type=Path,required=True);a=p.parse_args()
    result=build(a.diagnostic)
    print(json.dumps(dict(status=result['status'],rows=len(result['rows']),errors=result['errors'],pending=result['pending'])))
    raise SystemExit(2 if result['errors'] else 0)
