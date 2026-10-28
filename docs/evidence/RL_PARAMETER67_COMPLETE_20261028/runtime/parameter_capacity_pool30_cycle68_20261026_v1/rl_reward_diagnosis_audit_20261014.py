"""Historical train-only reward information and online-parameter census.

No simulation, updates, heldout access, or success filtering from denominators.
Explicit outcome-stratified examples serve mechanism diagnosis, not ranking.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import numpy as np


def read(p):return json.loads(Path(p).read_text())


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def write(p,value):
    Path(p).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def basic(values):
    x=np.asarray(values,float)
    return dict(n=len(x),mean=float(x.mean()),std=float(x.std()),min=float(x.min()),max=float(x.max())) if len(x) else dict(n=0)


def parameter_statistics(run):
    path=run/'parameter_trace.json'
    if not path.exists():return None
    rows=read(path)
    raw=np.asarray([r['raw_action'] for r in rows]);applied=np.asarray([r['applied_parameters'] for r in rows])
    unlimited=np.asarray([r['unrestricted_parameters'] for r in rows]);requested=np.asarray([r['requested_parameters'] for r in rows])
    previous=np.asarray([r['previous_parameters'] for r in rows]);scale=np.asarray([r['energy_scale'] for r in rows])
    assert len(raw)==len(applied) and np.isfinite(applied).all() and np.min(applied)>0
    with np.load(run/'rollout.npz',allow_pickle=False) as trace:
        time=trace['time'];stage=trace['stage']
    assert len(time)==len(rows)
    return dict(trace_sha256=sha(path),ticks=len(rows),actor_dt_s=.04,
        changed_tick_fraction=float(np.mean(np.max(np.abs(applied-previous),axis=1)>1e-9)),
        action_saturated_fraction=float(np.mean(np.abs(raw)>=.95)),
        rate_limited_tick_fraction=float(np.mean(np.max(np.abs(np.log(unlimited/requested)),axis=1)>1e-8)),
        energy_limited_tick_fraction=float(np.mean(scale<1-1e-8)),
        min_applied=applied.min(0).tolist(),max_applied=applied.max(0).tolist(),
        max_min_ratio=(applied.max(0)/applied.min(0)).tolist(),
        stage_statistics={str(s):dict(ticks=int(np.sum(stage==s)),start_s=float(time[stage==s].min()),
            end_s=float(time[stage==s].max()),mean_parameters=applied[stage==s].mean(0).tolist()) for s in np.unique(stage)},
        limitation='Recorded stage is analysis-only; no stage is added to actor. Parameter changes do not by themselves prove useful control authority.')


def counterfactual(row,gamma):
    from decoupled_task_safety_reward_20261009 import TaskSafetyPenalty
    run=Path(row['run']);ivs=read(run/'RL_INTERVALS.json')
    assert ivs[0] is None and len(ivs)==row['steps']+1
    with np.load(run/'research_substeps.npz',allow_pickle=False) as f:
        p=f['external_penetration_m'].copy()
    penalty=TaskSafetyPenalty();offset=0;elapsed=0.;discounted=0.;total=0.
    for i,iv in enumerate(ivs[1:]):
        stop=offset+iv['substeps'];maximum=float(p[offset:stop].max());offset=stop
        elapsed+=iv['elapsed_s'];cost,_=penalty(maximum,terminated=i==len(ivs)-2,elapsed_s=elapsed)
        discounted+=gamma**i*cost;total+=cost
    assert offset==len(p)
    adjustment=40. if row['task'] and not row['strict'] else 0.
    return dict(original_discounted_return=row['discounted_return'],
        task_safety_discounted_return=row['discounted_return']+gamma**(row['steps']-1)*adjustment-discounted,
        task_terminal_adjustment=adjustment,discounted_safety_cost=discounted,undiscounted_safety_cost=total,
        physical_research_sha256=sha(run/'research_substeps.npz'),intervals_sha256=sha(run/'RL_INTERVALS.json'),
        description='Same recorded behavior counterfactual; not a newly learned policy or causal outcome improvement')


def historical(base,out):
    out.mkdir(parents=True,exist_ok=False)
    methods=['direct_office_task','direct_office_task_historical_entropy','direct_metric',
             'parameter_admittance','parameter_impedance','parameter_vmc','parameter_impedance_historical_entropy']
    all_rows=[];sources=[]
    for method in methods:
        candidates=[base/'campaign_v2'/f'{method}_segment011k',
                    base/'campaign_v2'/f'{method}_extended055000',
                    base/'campaign_v2'/f'{method}_extended110000',
                    base/'recovery_20261011_v1'/f'{method}_step165000',
                    base/'completion_20261012_v1'/f'{method}_step165000']
        keys=set()
        for segment in candidates:
            if not (segment/'execution.json').exists():continue
            ex=read(segment/'execution.json');spec=read(segment/'PROTOCOL.json')
            assert ex['status']=='complete',segment
            gamma=spec['reward']['gamma'];acc={}
            source=dict(segment=str(segment.resolve()),execution_sha256=sha(segment/'execution.json'),
                        protocol_sha256=sha(segment/'PROTOCOL.json'),training_sha256=sha(segment/'training.jsonl'))
            sources.append(source)
            for line in (segment/'training.jsonl').open():
                record=json.loads(line);t=record['terms'];ep=record['episode']
                a=acc.setdefault(ep,dict(n=0,discounted=0.,undiscounted=0.,components=defaultdict(float),
                    initial=t['current_potential'],terminated=0,positive=0))
                assert not a['terminated']
                for k in ('task','progress','error','peak_torque','time','physical_slew','failure_continuation'):
                    a['components'][k]+=gamma**a['n']*t.get(k,0.)
                a['discounted']+=gamma**a['n']*t['final_reward'];a['undiscounted']+=t['final_reward'];a['n']+=1
                a['terminated']+=int(t['terminated']);a['positive']+=int(t['task']>0)
            for row in ex['rows']:
                if 'result' not in row:continue
                key=(row['episode'],row['step_after'])
                assert key not in keys,('Repeated lineage episode',method,key)
                keys.add(key);a=acc[row['episode']]
                assert a['terminated']==1 and a['n']==row['steps']
                np.testing.assert_allclose(a['undiscounted'],row['return_value'],atol=1e-8)
                np.testing.assert_allclose(a['components']['progress'],-spec['reward']['progress_weight']*a['initial'],atol=1e-9)
                path=Path(row['run']);assert sha(path/'AUDIT.json')==row['audit_sha256']
                audit=read(path/'AUDIT.json');result=row['result']
                all_rows.append(dict(method=method,episode=row['episode'],steps=row['steps'],
                    step_before=row['step_before'],step_after=row['step_after'],run=str(path),
                    condition=row['condition_id'],task=result['task_success'],strict=result['strict_success'],
                    full_horizon=audit['full_horizon'],stage=audit['stage'],penetration_mm=audit['penetration_mm'],
                    placement_error_xy_m=audit['placement_error_xy_m'],
                    positive_terminal=a['positive']==1,discounted_return=a['discounted'],
                    undiscounted_return=a['undiscounted'],discounted_components=dict(a['components']),
                    warmup='random' if row['step_after']<=5000 else 'mixed' if row['step_before']<5000 else 'learned',
                    gamma=gamma,audit_sha256=row['audit_sha256']))
        print(method,'episodes',sum(r['method']==method for r in all_rows),flush=True)
    summaries=[];examples=[]
    for method in methods:
        rows=[r for r in all_rows if r['method']==method]
        summaries.append(dict(method=method,episodes=len(rows),steps=max(r['step_after'] for r in rows),
            task=sum(r['task'] for r in rows),strict=sum(r['strict'] for r in rows),
            positive_terminal=sum(r['positive_terminal'] for r in rows),
            stage_counts=dict(__import__('collections').Counter(r['stage'] for r in rows)),
            groups={name:dict(episodes=len(subset),task=sum(r['task'] for r in subset),strict=sum(r['strict'] for r in subset),
                    discounted=basic([r['discounted_return'] for r in subset]),
                    undiscounted=basic([r['undiscounted_return'] for r in subset]))
                for name,subset in [('task_and_strict',[r for r in rows if r['strict']]),
                    ('task_not_strict',[r for r in rows if r['task'] and not r['strict']]),
                    ('full_failure',[r for r in rows if r['full_horizon'] and not r['task']]),
                    ('early_failure',[r for r in rows if not r['full_horizon']])]}))
        # Explicit first representative of each outcome class, plus the latest
        # learned episode for current parameter behavior. No example ranking.
        selected=[]
        for predicate in [lambda r:r['strict'],lambda r:r['task'] and not r['strict'],
                          lambda r:r['full_horizon'] and not r['task'],lambda r:not r['full_horizon']]:
            found=next((r for r in rows if predicate(r)),None)
            if found:selected.append(found)
        selected.append(rows[-1])
        seen=set()
        for row in selected:
            if row['run'] in seen:continue
            seen.add(row['run'])
            examples.append(dict(row=row,counterfactual=counterfactual(row,row['gamma']),
                                 parameters=parameter_statistics(Path(row['run']))))
    write(out/'HISTORICAL_CENSUS.json',dict(status='passed',created_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sha(__file__),sources=sources,methods=summaries,episodes=all_rows,
        shaping='All completed discounted potential sums equal -weight*initial_potential. This is proper potential shaping, not proof of ineffective TD guidance.',
        limits='Training behavior across different conditions, single historical seed, no unbiased policy ranking or universal unsuitability conclusion'))
    write(out/'MECHANISM_EXAMPLES.json',dict(selection='First chronological episode per outcome class and latest per method; all episodes retained in census',examples=examples))
    write(out/'execution.json',dict(status='complete',command=sys.argv,host=__import__('platform').node(),
        ended_utc=datetime.now(timezone.utc).isoformat(),new_physics_steps=0,new_gradient_updates=0))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();historical(a.base.resolve(),a.out.resolve())
