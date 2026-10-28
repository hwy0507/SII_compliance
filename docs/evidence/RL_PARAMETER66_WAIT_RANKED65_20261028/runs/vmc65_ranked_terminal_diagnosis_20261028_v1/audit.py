"""Posthoc complete65 saved terminal ranking; all1974 rows retained, no new forward."""
from pathlib import Path
import json,hashlib,math,os,time
os.sched_setaffinity(0,{53})
import numpy as np
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=Path(__file__).parent;prior=B/'runs/vmc65_terminal_anchor_followup_20261028_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def read(p):return json.loads(p.read_text())
assert read(prior/'SAVED_VALUES_REVIEW.json')['passed'];review=read(prior/'REVIEW.json');assert sha(prior/'values.npz')==review['values_sha256']
with np.load(prior/'values.npz',allow_pickle=False) as v:
 idx=v['indices'];reward=v['rewards'].astype(float);mask=v['masks'];q=v['q_after'].astype(float);qb=v['q_before'].astype(float)
 assert len(idx)==1974 and len(qb[0])==1944
 perhead=mask*(q-reward[None])**2;oldhead=mask[:,:1944]*(qb-reward[None,:1944])**2
 ss=perhead.sum(axis=0);old=oldhead.sum(axis=0);contrib=(128*perhead/v['denominator'][:,None]).sum(axis=0)
 assert math.isclose(math.fsum(map(float,ss[:1944])),review['old1944_sse_after'],rel_tol=1e-12)
 assert math.isclose(math.fsum(map(float,contrib)),review['all_terminal_contribution'],rel_tol=1e-12)
 order=sorted(range(1974),key=lambda k:(-float(ss[k]),int(idx[k])))
 allrows=[dict(rank=i+1,replay_index=int(idx[k]),terminal_reward=float(reward[k]),masked_sse=float(ss[k]),contribution=float(contrib[k]),sse64=float(old[k]) if k<1944 else None,per_head_sse=perhead[:,k].tolist()) for i,k in enumerate(order)]
 focus=[];inputs={'values':ref(prior/'values.npz'),'prior_review':ref(prior/'REVIEW.json'),'prior_saved_review':ref(prior/'SAVED_VALUES_REVIEW.json')}
 for rank,k,(cycle,expected,condition,strict) in zip([1,2],order[:2],[(58,2423122,'active_short_train_0200',True),(59,2464220,'active_short_train_0600',False)]):
  assert int(idx[k])==expected and k<1944
  run=B/f'runs/parameter_capacity_pool30_cycle{cycle}_20261026_v1/vmc/train';eps=run/'episodes.jsonl';matches=[e for e in map(json.loads,eps.read_text().splitlines()) if e['total_steps']==expected+1];assert len(matches)==1;e=matches[0]
  assert e['condition']==condition and e['task_success'] and e['strict_success']==strict and e['physical_valid']==strict and not e['abort_reason']
  transition=run/'transitions.jsonl';tr=[]
  with transition.open() as f:
   for line in f:
    t=json.loads(line)
    if t['step']==expected+1:tr.append(t)
  assert len(tr)==1;t=tr[0];assert t['done'] and t['condition']==condition and float(np.float32(t['reward']))==reward[k]
  folder=Path(e['episode_path']);roll=read(folder/'rollout.json');pmm=1000*roll['stats']['max_external_penetration_m'];physical=roll['abort_reason'] is None and roll['stats']['max_external_penetration_m']<=.0002
  assert physical==roll['physical_valid']==e['physical_valid'];assert roll['task_success']==e['task_success'] and roll['strict_success']==e['strict_success']
  assert sha(folder/'rollout.mjb')==roll['model_sha256']==e['model_sha256'];assert "physical_valid=abort_reason is None and stats['max_external_penetration_m']<=.0002" in (folder/'executed_evaluator.py.txt').read_text()
  inputs[f'cycle{cycle}_episodes']=ref(eps);inputs[f'cycle{cycle}_transitions']=ref(transition);inputs[f'cycle{cycle}_rollout']=ref(folder/'rollout.json');inputs[f'cycle{cycle}_evaluator']=ref(folder/'executed_evaluator.py.txt')
  focus.append(dict(allrows[rank-1],historical_cycle=cycle,condition=condition,task=e['task_success'],strict=strict,physical_valid=physical,penetration_mm=pmm,episode_cumulative_reward=e['reward'],terminal_transition_reward=t['reward'],sse_increment=float(ss[k]-old[k]),critic_head_masks=mask[:,k].tolist(),q64=qb[:,k].tolist(),q65=q[:,k].tolist(),rollout=ref(folder/'rollout.json')))
 top_delta=math.fsum(x['sse_increment'] for x in focus);total_delta=review['old1944_sse_after']-review['old1944_sse_before'];top_sse=math.fsum(x['masked_sse'] for x in focus)
 report=dict(passed=True,time=time.time(),inputs=inputs,posthoc_diagnostic=True,all1974_ranked=allrows,top2=focus,full1944_sse_increment=total_delta,top2_sse_increment=top_delta,remaining1942_sse_increment=total_delta-top_delta,top2_share_of_full1974_sse=top_sse/math.fsum(map(float,ss)),all1974_sse=math.fsum(map(float,ss)),all1974_contribution=math.fsum(map(float,contrib)),new_physics=0,new_forward=0,optimizer_updates=0,replay_writes=0,new_stopping_gate=False,causal_claim=False,limitation='Full1974 saved65 values ranked after observing65, during66 before completion. Top2 checked against actual historical terminal transition and physical labels; original fivefocus/full population retained. No claim of representational aliasing, replay-gradient causality, generalization or new stopping threshold.')
for x in inputs.values():assert sha(Path(x['path']))==x['sha256']
assert not(OUT/'REVIEW.json').exists();(OUT/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['all1974_ranked','inputs']},indent=2))
