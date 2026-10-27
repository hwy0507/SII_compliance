"""Complete capacity24 saved arithmetic and paired23 outcomes; no model loading."""
from pathlib import Path
import hashlib,json,math,os,statistics,time
os.sched_setaffinity(0,{54})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
root=B/'runs/serl_capacity_batch65536_cycle24_review_20261027_v1'
report=dict(time=time.time(),passed=True,inputs={},new_physics=0,optimizer_updates=0,model_forward_calls=0,convergence_claim=False,limitation='Saved scalar arithmetic and paired outcomes only; capacity changed1m to2m at24, so not a no-intervention causal comparison.')
def read(p):
 data=p.read_bytes();report['inputs'][str(p)]=hashlib.sha256(data).hexdigest();return json.loads(data)
def lines(p):
 data=p.read_bytes();assert data.endswith(b'\n');report['inputs'][str(p)]=hashlib.sha256(data).hexdigest();return [json.loads(s) for s in data.splitlines()]
def near(a,b):assert math.isclose(a,b,rel_tol=0,abs_tol=1e-9),(a,b)
assert read(root/'FINISHED.json')['completed'];review=read(root/'REVIEW.json');assert review['passed'];health=read(root/'DIAGNOSIS.json');row=review['methods']['direct'];assert health['checkpoint_sha256']==row['checkpoint_sha256'] and health['network_optimizer_rng_unchanged']
parent=B/'runs/serl_multistep_batch65536_cycle23_review_20261026_v1';assert read(parent/'FINISHED.json')['completed'];old=read(parent/'REVIEW.json');assert old['passed']
runs={23:B/'runs/serl_multistep_batch65536_cycle23_20261026_v1',24:B/'runs/serl_capacity_batch65536_cycle24_20261027_v1'}
es={}
for cycle,rr in [(23,old),(24,review)]:
 reg=read(runs[cycle]/'REGISTRATION.json');conds={c['id']:c for c in reg['conditions']};rows=lines(runs[cycle]/'direct/episodes.jsonl');assert len(rows)==len(conds)==30 and {e['condition'] for e in rows}==set(conds)
 assert all(e['cycle']==cycle and e['model_sha256']==conds[e['condition']]['model_sha256'] for e in rows)
 near(statistics.mean(e['reward'] for e in rows),rr['methods']['direct']['reward_mean'])
 assert sum(e['task_success'] for e in rows)==rr['methods']['direct']['task'] and sum(e['strict_success'] for e in rows)==rr['methods']['direct']['strict']
 es[cycle]={e['condition']:e for e in rows}
paired=[]
assert es[23].keys()==es[24].keys()
for name in sorted(es[23]):
 a,c=es[23][name],es[24][name];assert a['model_sha256']==c['model_sha256'];paired.append(dict(condition=name,reward_before=a['reward'],reward_after=c['reward'],delta=c['reward']-a['reward'],task_before=a['task_success'],task_after=c['task_success'],strict_before=a['strict_success'],strict_after=c['strict_success']))
near(statistics.mean(x['delta'] for x in paired),row['reward_mean']-old['methods']['direct']['reward_mean'])
updates=lines(runs[24]/'direct/optimizer.jsonl');assert len(updates)==row['new_transitions'];assert [x['step'] for x in updates]==list(range(row['steps']-len(updates)+1,row['steps']+1));assert all(math.isfinite(v) for x in updates for v in x.values() if isinstance(v,(int,float)))
loss=[x['serl/critic/critic_loss'] for x in updates];alpha=[x['serl/actor/temperature'] for x in updates];assert min(loss)>=0 and min(alpha)>0
report.update(steps=row['steps'],updates=row['updates'],checkpoint_sha256=row['checkpoint_sha256'],task=row['task'],strict=row['strict'],reward_mean=row['reward_mean'],mean_delta=statistics.mean(x['delta'] for x in paired),paired_conditions=paired,loss=dict(count=len(loss),first1000=statistics.mean(loss[:1000]),last1000=statistics.mean(loss[-1000:]),mean=statistics.mean(loss),maximum=max(loss)),alpha=dict(first1000=statistics.mean(alpha[:1000]),last1000=statistics.mean(alpha[-1000:]),minimum=min(alpha),maximum=max(alpha)),full_horizon=row['full_horizon_count'],aborts=row['aborts'])
for p,h in report['inputs'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
with (root/'SAVED_RESULTS_REVIEW.json').open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['inputs','paired_conditions']},indent=2))
