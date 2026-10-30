from pathlib import Path
import hashlib,json,time,math,os
import numpy as np
os.sched_setaffinity(0,{0})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent
def read(p):return json.loads(p.read_text())
def ref(p):
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return dict(path=str(p),sha256=h)
result={}
for m in ['vmc','admittance']:
 t=B/f'runs/{m}_recovery82_terminal_followup_20261029_v1';assert read(t/'SAVED_VALUES_REVIEW.json')['passed'] and read(t/'FINISHED.json')['completed']
 ep=B/f'runs/parameter_partial75_recovery_cycle82_20261029_v1/{m}/train/episodes.jsonl';rows=[json.loads(l) for l in ep.read_text().splitlines()];assert len(rows)==30
 with np.load(t/'values.npz',allow_pickle=False) as z:
  idx=z['indices'];q=z['q_after'];rewards=z['rewards'];masks=z['masks'];den=z['denominator'];assert len(idx)==2454
  cases=[]
  for row in rows:
   index=row['total_steps']-1;k=int(np.flatnonzero(idx==index)[0]);assert k>=2424
   rollout=Path(row['episode_path'])/'rollout.json';r=read(rollout)
   sse=math.fsum(float(masks[c,k])*(float(q[c,k])-float(rewards[k]))**2 for c in range(5))
   contrib=math.fsum(128*float(masks[c,k])*(float(q[c,k])-float(rewards[k]))**2/float(den[c]) for c in range(5))
   cases.append(dict(condition=row['condition'],replay_index=index,terminal_reward=float(rewards[k]),task=row['task_success'],strict=row['strict_success'],physical_valid=row['physical_valid'],masked_sse=sse,contribution=contrib,rollout=ref(rollout)))
  assert len({r['replay_index'] for r in cases})==30
  total=math.fsum(r['contribution'] for r in cases)
  expected=float((128*masks[:,2424:]*(q[:,2424:].astype(float)-rewards[None,2424:].astype(float))**2/den[:,None]).sum());assert math.isclose(total,expected,rel_tol=1e-12)
  for r in cases:r['share_of_new30']=r['contribution']/total
 result[m]=dict(cases=sorted(cases,key=lambda r:r['contribution'],reverse=True),total_new30_contribution=total,values=ref(t/'values.npz'),episodes=ref(ep))
out=dict(passed=True,time=time.time(),methods=result,no_new_network_forward=True,new_physics=0,optimizer_updates=0,limitation='Retrospective complete82 terminal decomposition and episode mapping; not historical optimizer minibatch causality or independent physics reconstruction.')
with (D/'NEW82_TERMINAL_CASE_REVIEW.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
for m,r in result.items():print(m,r['total_new30_contribution'],[(x['condition'],x['contribution'],x['share_of_new30']) for x in r['cases'][:3]])
