"""Post-hoc descriptive attribution of saved63 terminal SSE; no new forward."""
from pathlib import Path
import json,hashlib,math,os,time
os.sched_setaffinity(0,{53})
import numpy as np
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=Path(__file__).parent;prior=B/'runs/vmc63_terminal_anchor_followup_20261028_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def read(p):return json.loads(p.read_text())
assert read(prior/'SAVED_VALUES_REVIEW.json')['passed'];review=read(prior/'REVIEW.json');assert sha(prior/'values.npz')==review['values_sha256']
with np.load(prior/'values.npz',allow_pickle=False) as v:
 idx=v['indices'];reward=v['rewards'].astype(float);mask=v['masks'];q=v['q_after'].astype(float);qb=v['q_before'].astype(float)
 assert len(idx)==1914 and len(qb[0])==1884
 perhead=mask*(q-reward[None])**2;oldhead=mask[:,:1884]*(qb-reward[None,:1884])**2
 ss=perhead.sum(axis=0);old=oldhead.sum(axis=0);contrib=(128*perhead/v['denominator'][:,None]).sum(axis=0)
 assert math.isclose(math.fsum(map(float,ss[:1884])),review['old1884_sse_after'],rel_tol=1e-12)
 assert math.isclose(math.fsum(map(float,contrib)),review['all_terminal_contribution'],rel_tol=1e-12)
 order=sorted(range(1914),key=lambda k:(-float(ss[k]),int(idx[k])))
 allrows=[dict(rank=i+1,replay_index=int(idx[k]),terminal_reward=float(reward[k]),masked_sse=float(ss[k]),contribution=float(contrib[k]),sse62=float(old[k]) if k<1884 else None,per_head_sse=perhead[:,k].tolist()) for i,k in enumerate(order)]
 focus=[];inputs={'values':ref(prior/'values.npz'),'prior_review':ref(prior/'REVIEW.json'),'prior_saved_review':ref(prior/'SAVED_VALUES_REVIEW.json')}
 for rank,k,cycle in zip([1,2],order[:2],[59,38]):
  expected={1:2464220,2:1603101}[rank];assert int(idx[k])==expected
  run=B/f'runs/parameter_capacity_pool30_cycle{cycle}_20261026_v1/vmc/train';eps=run/'episodes.jsonl';matches=[e for e in map(json.loads,eps.read_text().splitlines()) if e['total_steps']==expected+1];assert len(matches)==1;e=matches[0]
  assert e['condition']=='active_short_train_0600' and e['task_success'] and not e['strict_success'] and not e['physical_valid'] and not e['abort_reason']
  transition=run/'transitions.jsonl';tr=[]
  with transition.open() as f:
   for line in f:
    t=json.loads(line)
    if t['step']==expected+1:tr.append(t)
  assert len(tr)==1;t=tr[0];assert t['done'] and t['condition']==e['condition'] and float(np.float32(t['reward']))==reward[k]
  folder=Path(e['episode_path']);roll=read(folder/'rollout.json');pmm=1000*roll['stats']['max_external_penetration_m'];assert pmm>.2
  physical=roll['abort_reason'] is None and roll['stats']['max_external_penetration_m']<=.0002;assert physical==roll['physical_valid']==e['physical_valid'];assert roll['task_success']==e['task_success'] and roll['strict_success']==e['strict_success']
  assert sha(folder/'rollout.mjb')==roll['model_sha256']==e['model_sha256']
  inputs[f'cycle{cycle}_episodes']=ref(eps);inputs[f'cycle{cycle}_transitions']=ref(transition);inputs[f'cycle{cycle}_rollout']=ref(folder/'rollout.json')
  focus.append(dict(allrows[rank-1],historical_cycle=cycle,condition=e['condition'],task=True,strict=False,physical_valid=False,penetration_mm=pmm,episode_cumulative_reward=e['reward'],terminal_transition_reward=t['reward'],sse_increment=float(ss[k]-old[k]),critic_head_masks=mask[:,k].tolist(),q62=qb[:,k].tolist(),q63=q[:,k].tolist(),rollout=ref(folder/'rollout.json')))
 top_delta=math.fsum(x['sse_increment'] for x in focus);total_delta=review['old1884_sse_after']-review['old1884_sse_before'];top_sse=math.fsum(x['masked_sse'] for x in focus)
 report=dict(passed=True,time=time.time(),inputs=inputs,posthoc_diagnostic=True,all1914_ranked=allrows,top2=focus,full1884_sse_increment=total_delta,top2_sse_increment=top_delta,remaining1882_sse_increment=total_delta-top_delta,top2_share_of_full1914_sse=top_sse/math.fsum(map(float,ss)),all1914_sse=math.fsum(map(float,ss)),all1914_contribution=math.fsum(map(float,contrib)),new_physics=0,new_forward=0,optimizer_updates=0,replay_writes=0,new_stopping_gate=False,causal_claim=False,limitation='Full1914 saved63 values ranked after observing63. Top2 identity checked against original terminal transition and physical-valid labels. Episode cumulative reward differs from terminal reward; replay target is terminal transition reward. This does not establish representational aliasing, replay-gradient causality or generalization.')
for x in inputs.values():assert sha(Path(x['path']))==x['sha256']
(OUT/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['all1914_ranked','inputs']},indent=2))
