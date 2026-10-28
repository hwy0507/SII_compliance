"""Saved-value-only66 followup of all1974 rows, retaining fixed65 ranking."""
from pathlib import Path
import json,hashlib,math,os,time
os.sched_setaffinity(0,{53})
import numpy as np
OUT=Path(__file__).parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def near(a,b):assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),(a,b)

def main():
 plan=read(OUT/'PLAN.json');root=Path(plan['parent_followup'])
 assert (root/'FINISHED.json').exists() and read(root/'FINISHED.json')['completed'],'Incomplete66 terminal followup'
 assert read(root/'SAVED_VALUES_REVIEW.json')['passed']
 for n,h in plan['sources'].items():assert sha(OUT/n)==h
 for x in plan['inputs'].values():assert sha(x['path'])==x['sha256']
 before=read(plan['inputs']['ranked65']['path']);after=read(root/'REVIEW.json');assert before['passed'] and after['passed'] and sha(root/'values.npz')==after['values_sha256']
 rows=[]
 with np.load(plan['inputs']['values65']['path'],allow_pickle=False) as a,np.load(root/'values.npz',allow_pickle=False) as b:
  assert len(a['indices'])==1974 and len(b['indices'])==2004
  for k in ['indices','rewards','masks']:
   expected=b[k][:1974] if k!='masks' else b[k][:,:1974]
   np.testing.assert_array_equal(a[k],expected)
  np.testing.assert_array_equal(a['q_after'],b['q_before']);np.testing.assert_array_equal(a['denominator'],b['old_denominator'])
  pos={int(idx):k for k,idx in enumerate(a['indices'])}
  for item in before['all1974_ranked']:
   idx=item['replay_index'];k=pos[idx]
   def sse(q):return math.fsum(float(a['masks'][i,k])*(float(q[i,k])-float(a['rewards'][k]))**2 for i in range(5))
   old=sse(a['q_after']);new=sse(b['q_after']);near(old,item['masked_sse'])
   def contribution(q,den):return math.fsum(128*float(a['masks'][i,k])*(float(q[i,k])-float(a['rewards'][k]))**2/float(den[i]) for i in range(5))
   oldc=contribution(a['q_after'],a['denominator']);near(oldc,item['contribution'])
   rows.append(dict(original65_rank=item['rank'],replay_index=idx,sse65=old,sse66=new,sse_change=new-old,contribution65=oldc,contribution66=contribution(b['q_after'],b['denominator']),contribution66_using65_denominator=contribution(b['q_after'],a['denominator'])))
  assert len(rows)==1974 and [x['original65_rank'] for x in rows]==list(range(1,1975))
  totals={key:math.fsum(x[key] for x in rows) for key in ['sse65','sse66','sse_change','contribution65','contribution66','contribution66_using65_denominator']}
  near(totals['sse65'],after['old1974_sse_before']);near(totals['sse66'],after['old1974_sse_after']);near(totals['contribution65'],after['old1974_contribution_before']);near(totals['contribution66'],after['old1974_contribution_after']);near(totals['contribution66_using65_denominator'],after['old1974_after_using_old_denominator'])
  focus=[x for x in rows if x['replay_index'] in plan['fixed65_top2_indices']];assert [x['replay_index'] for x in focus]==plan['fixed65_top2_indices']
 report=dict(passed=True,time=time.time(),all1974_original_ranked_followup=rows,totals=totals,original65_top2=focus,improve=sum(x['sse_change']<0 for x in rows),worsen=sum(x['sse_change']>0 for x in rows),all65_arrays_preserved=True,original66_full1974_review_reproduced=True,original66_review_sha256=sha(root/'REVIEW.json'),values66_sha256=sha(root/'values.npz'),plan_sha256=sha(OUT/'PLAN.json'),new_physics=0,new_forward=0,optimizer_updates=0,replay_writes=0,causal_claim=False,convergence_claim=False,limitation='65 ranking selected posthoc, before66 completion; all1974 retained. Fixedtop2 followup cannot replace full1974 result or original fivefocus. No new stopping criterion.')
 assert not (OUT/'REVIEW.json').exists();(OUT/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(totals=totals,original65_top2=focus),indent=2))
if __name__=='__main__':main()
