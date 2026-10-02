"""Summarize only declared evaluations; never select checkpoints by test score."""
import argparse,csv,json
from pathlib import Path
import numpy as np
HORIZONS=dict(ball=30.,push=24.,corner=56.,table_corner=13.)
METRICS=['rmse_m','peak_torque_nm','peak_speed_mps','max_external_penetration_m']
def stats(rows):
    valid=[r for r in rows if not r.get('initial_state_rejected') and 'duration_s' in r]
    full=[r for r in valid if abs(r['duration_s']-HORIZONS[r['scene']])<.041]
    out=dict(total=len(rows),initial_state_rejected=len(rows)-len(valid),executed=len(valid),full_horizon=len(full),task_success=sum(bool(r.get('task_success')) for r in rows),strict_success=sum(bool(r.get('strict_success')) for r in rows),contact_exposed=sum(bool(r.get('contact_exposed')) for r in rows),numeric_physical_valid=sum(bool(r.get('physical_valid')) for r in rows))
    for label,subset in [('executed',valid),('full_horizon',full)]:
        out[label+'_metrics']={k:dict(median=float(np.median([r[k] for r in subset])),maximum=float(max(r[k] for r in subset))) for k in METRICS} if subset else None
    return out
def build(catalog,output):
    entries=json.loads(catalog.read_text());models={};protocols={};flat=[]
    for entry in entries['models']:
        p=Path(entry['output'])
        rows=json.loads((p/'ROWS.json').read_text()) if (p/'ROWS.json').exists() else []
        protocol=json.loads((p/'PROTOCOL.json').read_text()) if (p/'PROTOCOL.json').exists() else None
        seen={}
        for r in rows:
            if r['fixture_id'] in seen:raise ValueError('Duplicate fixture in '+entry['id'])
            seen[r['fixture_id']]=r
            flat.append(dict(model=entry['id'],**{k:r.get(k) for k in ['fixture_id','scene','initial_state_rejected','task_success','strict_success','contact_exposed','physical_valid','duration_s',*METRICS,'model_sha256','physical_hash']}))
        if protocol and protocol['split']!=entries['split']:raise ValueError('Mixed evaluation splits')
        models[entry['id']]=seen;protocols[entry['id']]=protocol
    common=sorted(set.intersection(*(set(v) for v in models.values()))) if models else []
    pair_audit=[]
    for fixture in sorted(set.union(*(set(v) for v in models.values()))) if models else []:
        rows=[(name,rs[fixture]) for name,rs in models.items() if fixture in rs and not rs[fixture].get('initial_state_rejected')]
        hashes={r['model_sha256'] for _,r in rows};physical={r.get('physical_hash') for _,r in rows}
        ok=len(hashes)<=1 and len(physical)<=1
        pair_audit.append(dict(fixture=fixture,models=[name for name,_ in rows],same_model=ok,model_hashes=sorted(hashes)))
        if not ok:raise RuntimeError('Unpaired models/physical definitions for '+fixture)
    summaries={}
    for entry in entries['models']:
        rs=models[entry['id']]
        summaries[entry['id']]=dict(label=entry['label'],planned=entries.get('planned_per_model'),completed=len(rs),complete=(Path(entry['output'])/'COMPLETE.json').exists(),all_completed=stats(list(rs.values())),common_paired=stats([rs[f] for f in common]),by_scene={s:stats([r for r in rs.values() if r['scene']==s]) for s in HORIZONS})
    pairs={}
    for pair in entries.get('comparisons',[]):
        a,b=pair;ids=sorted(set(models[a])&set(models[b]));rr=[]
        for f in ids:
            x,y=models[a][f],models[b][f]
            row=dict(fixture=f,task_a=bool(x.get('task_success')),task_b=bool(y.get('task_success')))
            if 'duration_s' in x and 'duration_s' in y:
                row['equal_duration']=abs(x['duration_s']-y['duration_s'])<.041
                row['b_minus_a']={k:y[k]-x[k] for k in METRICS}
            rr.append(row)
        pairs[a+' -> '+b]=rr
    output.mkdir(exist_ok=True,parents=True)
    result=dict(split=entries['split'],catalog=str(catalog),common_fixture_ids=common,models=summaries,model_pairing_audit=pair_audit,pairwise=pairs,protocols=protocols,limitations=['Development primitive fixtures retain heterogeneous native timestep/task supervisor.','Numeric physical gate is finite peak torque and <=0.2 mm penetration, not a complete safety or passivity certificate.','Primitive strict includes intended contact, unlike the new office-v5 strict definition.','No omitted failures; initial-state rejections stay in attempted count.','Metrics condition on successful execution/full horizon explicitly; an aborted low RMSE is not a win.'])
    (output/'SUMMARY.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    if flat:
        with (output/'EPISODES.csv').open('w') as f:
            writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    text=['# Primitive baseline evaluation', '', 'Split: '+entries['split']+'. Common completed paired conditions: '+str(len(common))+'.', '', '| Method | Done | Task | Strict | Contact | Full horizon | RMSE median mm | Torque maximum Nm | Speed maximum m/s |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for key,s in summaries.items():
        v=s['all_completed'];m=v['full_horizon_metrics'];n=v['total']
        fmt=lambda k,scale=1:('%.3f'%(m[k]['median' if k=='rmse_m' else 'maximum']*scale)) if m else '—'
        text.append('| '+s['label']+' | '+str(s['completed'])+' | '+str(v['task_success'])+'/'+str(n)+' | '+str(v['strict_success'])+'/'+str(n)+' | '+str(v['contact_exposed'])+'/'+str(n)+' | '+str(v['full_horizon'])+'/'+str(n)+' | '+fmt('rmse_m',1000)+' | '+fmt('peak_torque_nm')+' | '+fmt('peak_speed_mps')+' |')
    text+=['', 'The table lists all completed conditions per method; use SUMMARY.json/common_paired when incomplete models have different coverage. Missing runs are not successes or failures.', '', *['- '+s for s in result['limitations']]]
    (output/'SUMMARY.md').write_text('\n'.join(text)+'\n')
    print(json.dumps(dict(models=len(models),episodes=len(flat),common=len(common),output=str(output))))
def main():
    p=argparse.ArgumentParser();p.add_argument('--catalog',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();build(a.catalog,a.output)
if __name__=='__main__':main()
