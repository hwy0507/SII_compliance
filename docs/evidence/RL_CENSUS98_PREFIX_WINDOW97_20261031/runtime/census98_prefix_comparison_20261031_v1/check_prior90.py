"""Read actual full97 conditions, rollout labels, model identities and reward arithmetic."""
from pathlib import Path
import json,math,time,hashlib,os
os.sched_setaffinity(0,{10});D=Path(__file__).resolve().parent;B=D.parents[1]
read=lambda p:json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
plan=read(D/'COMPARISON_PLAN.json')
for p,h in plan['prior_inputs'].items():assert sha(p)==h
P=B/'runs/parameter_census_cycle97_review_20261031_v1';r=read(P/'REVIEW.json');health=read(P/'health/DIAGNOSIS.json');loss=read(P/'loss/REVIEW.json');out={}
for m in plan['methods']:
 reg=read(B/'runs/parameter_census_cycle98_20261031_v1'/m/'REGISTRATION.json');prev=read(reg['post_interruption_continuation']['parent_registration']['path']);assert reg['conditional_terminal_amendment']==plan['conditional_amendments'][m]
 from capacity_contract import verify_science
 verify_science(reg,prev)
 episodes=[e for e in health['methods'][m]['episodes'] if e['cycle']==97];assert len(episodes)==30 and len({e['condition'] for e in episodes})==30;by={e['condition']:e for e in episodes};records=[]
 for c in reg['conditions']:
  e=by[c['id']];p=B/'runs/parameter_census_cycle97_20261031_v1'/m/'train/cycle_00097'/c['id']/'rollout.json';roll=read(p)
  for k in ['task_success','strict_success','abort_reason','final_task_stage']:assert e[k]==roll[k]
  assert roll['model_sha256']==c['model_sha256'] and sha(c['path'])==c['sha256']
  assert math.isclose(math.fsum(e['reward_terms'].values()),e['reward'],abs_tol=1e-7) and all(math.isfinite(v) for v in e['reward_terms'].values())
  records.append(dict(condition=c['id'],source=str(p),sha256=sha(p),model_sha256=roll['model_sha256'],reward=e['reward'],task=e['task_success'],strict=e['strict_success'],abort=e['abort_reason'],full_horizon=roll['full_task_horizon_completed']))
 assert sum(e['task_success'] for e in episodes)==r['methods'][m]['task'] and sum(e['strict_success'] for e in episodes)==r['methods'][m]['strict']
 assert math.isclose(math.fsum(e['reward'] for e in episodes)/30,r['methods'][m]['reward_mean'],abs_tol=1e-12)
 for k in ['agent_train/original_sampled_q_loss','agent_train/actor_loss']:assert k in loss['methods'][m]['stats']
 out[m]=dict(records=records,task=r['methods'][m]['task'],strict=r['methods'][m]['strict'],reward_mean=r['methods'][m]['reward_mean'],abort_count=sum(e['abort_reason'] is not None for e in episodes),all_model_labels_and_reward_terms_checked=True)
result=dict(passed=True,time=time.time(),methods=out,all90_complete97_only=True,scope='Actual complete97 inputs/90 saved rollout labels/frozen models/reward decomposition and totals. Complete98 not fabricated or evaluated.',physics_steps=0,optimizer_updates=0)
with (D/'PRIOR90_REVIEW.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print('Actual complete97 all90 input checks passed')
