from pathlib import Path
import hashlib,json,time,math,os
import numpy as np
D=Path(__file__).parent;B=D.parents[1];os.sched_setaffinity(0,{54})
def read(p):return json.loads(p.read_text())
def ref(p):
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return dict(path=str(p),sha256=h)
def close(x,y):assert math.isclose(x,y,rel_tol=1e-11,abs_tol=1e-10),(x,y)
plan=read(D/'PLAN.json');assert plan['registered_after_top5_preview'] and plan['fixed_old_rows']==2394
for r in plan['inputs']:
 assert ref(Path(r['path']))==r
methods={}
for m in ['vmc','admittance']:
 t=B/f'runs/{m}_recovery81_terminal_followup_20261029_v1';report=read(t/'REVIEW.json');assert read(t/'SAVED_VALUES_REVIEW.json')['passed']
 mapping={};episode_refs=[]
 for cycle in list(range(49,75))+list(range(76,81)):
  folder=f'parameter_capacity_pool30_cycle{cycle}_20261026_v1' if cycle<75 else f'parameter_partial75_recovery_cycle{cycle}_20261029_v1'
  ep=B/'runs'/folder/m/'train/episodes.jsonl';episode_refs.append(ref(ep))
  for line in ep.read_text().splitlines():
   e=json.loads(line);ix=e['total_steps']-1;assert ix not in mapping
   terminal=Path(e['episode_path'])/'TERMINAL.json'
   mapping[ix]=dict(cycle=cycle,condition=e['condition'],episode_reward=e['reward'],task=e['task_success'],strict=e['strict_success'],terminal=ref(terminal))
 with np.load(t/'values.npz',allow_pickle=False) as z:
  rows=[]
  for k in range(2394):
   ix=int(z['indices'][k]);reward=float(z['rewards'][k]);mask=z['masks'][:,k];qb=z['q_before'][:,k];qa=z['q_after'][:,k]
   before=math.fsum(float(mask[c])*(float(qb[c])-reward)**2 for c in range(5));after=math.fsum(float(mask[c])*(float(qa[c])-reward)**2 for c in range(5))
   oldden=math.fsum(128*float(mask[c])*(float(qa[c])-reward)**2/float(z['old_denominator'][c]) for c in range(5))
   newden=math.fsum(128*float(mask[c])*(float(qa[c])-reward)**2/float(z['denominator'][c]) for c in range(5))
   provenance=mapping.get(ix)
   if provenance:
    terminal=read(Path(provenance['terminal']['path']));assert terminal['result']['task_success']==provenance['task'] and terminal['result']['strict_success']==provenance['strict']
   rows.append(dict(replay_index=ix,reward=reward,masks=mask.tolist(),q80=qb.tolist(),q81=qa.tolist(),sse80=before,sse81=after,delta_sse=after-before,after_with_old_denominator=oldden,after_with_new_denominator=newden,provenance=provenance))
 close(math.fsum(r['sse80'] for r in rows),report['old2394_sse_before']);close(math.fsum(r['sse81'] for r in rows),report['old2394_sse_after']);close(math.fsum(r['after_with_old_denominator'] for r in rows),report['old2394_after_using_old_denominator']);close(math.fsum(r['after_with_new_denominator'] for r in rows),report['old2394_contribution_after'])
 increases=sorted(rows,key=lambda r:r['delta_sse'],reverse=True);decreases=sorted(rows,key=lambda r:r['delta_sse']);positive=math.fsum(max(r['delta_sse'],0) for r in rows);negative=math.fsum(min(r['delta_sse'],0) for r in rows)
 methods[m]=dict(rows=rows,old_rows=2394,mapped_rows=sum(r['provenance'] is not None for r in rows),mapping_scope='Only complete49-74 and76-80; original partial75 and earlier remain unmapped, not dropped from arithmetic',increased=sum(r['delta_sse']>0 for r in rows),decreased=sum(r['delta_sse']<0 for r in rows),positive_sse_change=positive,negative_sse_change=negative,net_sse_change=positive+negative,top5_increases=increases[:5],top5_decreases=decreases[:5],top5_share_positive=sum(r['delta_sse'] for r in increases[:5])/positive,episode_refs=episode_refs)
 close(positive+negative,report['old2394_sse_after']-report['old2394_sse_before'])
for r in plan['inputs']:assert ref(Path(r['path']))==r
result=dict(passed=True,time=time.time(),methods=methods,all2394_scalar_sse_and_both_denominators_match_prior_review=True,plan=ref(D/'PLAN.json'),new_network_forward=0,optimizer_updates=0,new_physics=0,causal_claim=False,convergence_claim=False,limitation=plan['limitation'])
with (D/'REVIEW.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
for m,r in methods.items():print(m,json.dumps({k:r[k] for k in ['increased','decreased','positive_sse_change','negative_sse_change','net_sse_change','top5_share_positive','mapped_rows']}));print('top5',[(v['replay_index'],v['sse80'],v['sse81'],v['provenance']['condition'] if v['provenance'] else 'unmapped') for v in r['top5_increases']])
