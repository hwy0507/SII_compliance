"""Posthoc scalar diagnosis of all30 new terminal rows; no new forward or training."""
from pathlib import Path
import json,hashlib,math,time,os
os.sched_setaffinity(0,{54})
import numpy as np
p=Path(__file__).parent;b=p.parents[1]
def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
r=json.loads((p/'REVIEW.json').read_text());assert sha(p/'values.npz')==r['values_sha256']
ep=b/'runs/parameter_capacity_pool30_cycle62_20261026_v1/vmc/train/episodes.jsonl';es=list(map(json.loads,ep.read_text().splitlines()));byindex={e['total_steps']-1:e for e in es};assert len(byindex)==30
rows=[]
with np.load(p/'values.npz',allow_pickle=False) as v:
 assert len(v['indices'])==1884
 for k in range(1854,1884):
  index=int(v['indices'][k]);e=byindex[index];target=float(v['rewards'][k]);q=[float(x) for x in v['q_after'][:,k]];m=[float(x) for x in v['masks'][:,k]]
  sse=[mask*(x-target)**2 for x,mask in zip(q,m)];contribution=math.fsum(128*s/float(d) for s,d in zip(sse,v['denominator']))
  rows.append(dict(replay_index=index,condition=e['condition'],episode_reward=e['reward'],terminal_reward=target,task=e['task_success'],strict=e['strict_success'],q=q,masks=m,per_critic_sse=sse,sse=math.fsum(sse),contribution=contribution))
 total=math.fsum(x['contribution'] for x in rows);assert math.isclose(total,r['new30_contribution'],rel_tol=1e-12,abs_tol=1e-12)
rows.sort(key=lambda x:x['contribution'],reverse=True)
out=dict(passed=True,time=time.time(),all30=rows,new30_contribution=total,largest_fraction=rows[0]['contribution']/total,values_sha256=sha(p/'values.npz'),episodes_sha256=sha(ep),source_sha256=sha(Path(__file__)),posthoc=True,causal_claim=False,new_physics=0,optimizer_updates=0,limitation='All30 terminal rows retained and mapped by actual total_steps-1. Saved scalar arithmetic only; no sampled online minibatches reconstructed, no causal inference or exclusion rule.')
(p/'NEW_TERMINALS_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(top3=rows[:3],total=total,largest_fraction=out['largest_fraction']),indent=2))
