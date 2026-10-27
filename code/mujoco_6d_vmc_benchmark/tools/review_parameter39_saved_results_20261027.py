"""Check complete39 saved scalar results and paired38-to39 outcomes; no model loading."""
from pathlib import Path
import hashlib,json,math,os,statistics,time
os.sched_setaffinity(0,{52})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
root=B/'runs/parameter_capacity_pool30_cycle39_review_20261026_v1'
report=dict(time=time.time(),passed=True,inputs={},methods={},new_physics=0,optimizer_updates=0,model_forward_calls=0,convergence_claim=False,limitation='Saved scalar arithmetic and paired condition outcomes only; no causal attribution to policy, exploration, or optimizer noise.')
def read(p):
 data=p.read_bytes();report['inputs'][str(p)]=hashlib.sha256(data).hexdigest();return json.loads(data)
def lines(p):
 data=p.read_bytes();assert data.endswith(b'\n');report['inputs'][str(p)]=hashlib.sha256(data).hexdigest();return [json.loads(line) for line in data.splitlines()]
def near(a,b):assert math.isclose(a,b,rel_tol=0,abs_tol=1e-9),(a,b)
assert read(root/'FINISHED.json')['completed']
review=read(root/'REVIEW.json');assert review['passed']
health=read(root/'health/DIAGNOSIS.json')
parent=B/'runs/parameter_capacity_pool30_cycle38_review_20261026_v1'
assert read(parent/'FINISHED.json')['completed'];oldreview=read(parent/'REVIEW.json');assert oldreview['passed']
for m in ['impedance','admittance','vmc']:
 row=review['methods'][m];h=health['methods'][m]
 assert h['checkpoint_sha256']==row['checkpoint_sha256']
 episodes=[]
 for cycle,rr in [(38,oldreview),(39,review)]:
  run=B/f'runs/parameter_capacity_pool30_cycle{cycle}_20261026_v1'/m
  reg=read(run/'REGISTRATION.json');cond={c['id']:c for c in reg['conditions']}
  es=lines(run/'train/episodes.jsonl');assert len(es)==len(cond)==30 and {e['condition'] for e in es}==set(cond)
  assert all(e['cycle']==cycle and e['model_sha256']==cond[e['condition']]['model_sha256'] for e in es)
  near(statistics.mean(e['reward'] for e in es),rr['methods'][m]['reward_mean'])
  assert sum(e['task_success'] for e in es)==rr['methods'][m]['task'] and sum(e['strict_success'] for e in es)==rr['methods'][m]['strict']
  episodes.append({e['condition']:e for e in es})
 before,after=episodes;assert before.keys()==after.keys()
 paired=[]
 for name in sorted(before):
  a,b=before[name],after[name];assert a['model_sha256']==b['model_sha256']
  paired.append(dict(condition=name,reward_before=a['reward'],reward_after=b['reward'],delta=b['reward']-a['reward'],mean_contribution=(b['reward']-a['reward'])/30,task_before=a['task_success'],task_after=b['task_success'],strict_before=a['strict_success'],strict_after=b['strict_success']))
 delta=statistics.mean(r['delta'] for r in paired);near(delta,row['reward_mean']-oldreview['methods'][m]['reward_mean'])
 updates=lines(B/f'runs/parameter_capacity_pool30_cycle39_20261026_v1/{m}/train/optimizer.jsonl')
 assert len(updates)==row['new_transitions']
 assert [r['step'] for r in updates]==list(range(row['steps']-len(updates)+1,row['steps']+1))
 assert all(math.isfinite(v) for r in updates for v in r.values() if isinstance(v,(int,float)))
 loss=[r['agent_train/q_loss'] for r in updates];alpha=[r['agent_train/entropy_coefficient'] for r in updates]
 assert min(loss)>=0 and min(alpha)>0
 report['methods'][m]=dict(checkpoint_sha256=row['checkpoint_sha256'],steps=row['steps'],updates=row['updates'],task=row['task'],strict=row['strict'],reward_mean=row['reward_mean'],mean_delta=delta,outcome_switches=[r for r in paired if r['task_before']!=r['task_after'] or r['strict_before']!=r['strict_after']],all_conditions=paired,loss=dict(count=len(loss),first1000=statistics.mean(loss[:1000]),last1000=statistics.mean(loss[-1000:]),mean=statistics.mean(loss),maximum=max(loss)),alpha=dict(first1000=statistics.mean(alpha[:1000]),last1000=statistics.mean(alpha[-1000:]),minimum=min(alpha),maximum=max(alpha)),terminal_mae=h['terminal_q_absolute_error']['mean'],terminal_inbag_mae=h['terminal_q_in_bag_absolute_error']['mean'],full_horizon=row['full_horizon_count'],aborts=row['aborts'])
for p,h in report['inputs'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
with (root/'SAVED_RESULTS_REVIEW.json').open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
print(json.dumps({m:{k:v for k,v in r.items() if k!='all_conditions'} for m,r in report['methods'].items()},indent=2))
