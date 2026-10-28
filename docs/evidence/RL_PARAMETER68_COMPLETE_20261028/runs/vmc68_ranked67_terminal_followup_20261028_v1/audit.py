"""Saved-value-only68 followup of all2034 rows, retaining fixed67 ranking."""
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
 assert (root/'FINISHED.json').exists() and read(root/'FINISHED.json')['completed'],'Incomplete68 terminal followup'
 assert read(root/'SAVED_VALUES_REVIEW.json')['passed']
 for n,h in plan['sources'].items():assert sha(OUT/n)==h
 for x in plan['inputs'].values():assert sha(x['path'])==x['sha256']
 before=read(plan['inputs']['ranked67']['path']);after=read(root/'REVIEW.json');assert before['passed'] and after['passed'] and sha(root/'values.npz')==after['values_sha256']
 rows=[]
 with np.load(plan['inputs']['values67']['path'],allow_pickle=False) as a,np.load(root/'values.npz',allow_pickle=False) as b:
  assert len(a['indices'])==2034 and len(b['indices'])==2064
  for k in ['indices','rewards','masks']:
   expected=b[k][:2034] if k!='masks' else b[k][:,:2034]
   np.testing.assert_array_equal(a[k],expected)
  np.testing.assert_array_equal(a['q_after'],b['q_before']);np.testing.assert_array_equal(a['denominator'],b['old_denominator'])
  pos={int(idx):k for k,idx in enumerate(a['indices'])}
  for item in before['all2034_ranked']:
   idx=item['replay_index'];k=pos[idx]
   def sse(q):return math.fsum(float(a['masks'][i,k])*(float(q[i,k])-float(a['rewards'][k]))**2 for i in range(5))
   old=sse(a['q_after']);new=sse(b['q_after']);near(old,item['sse67'])
   def contribution(q,den):return math.fsum(128*float(a['masks'][i,k])*(float(q[i,k])-float(a['rewards'][k]))**2/float(den[i]) for i in range(5))
   oldc=contribution(a['q_after'],a['denominator']);near(oldc,item['contribution67'])
   rows.append(dict(original67_rank=item['rank'],replay_index=idx,sse67=old,sse68=new,sse_change=new-old,contribution67=oldc,contribution68=contribution(b['q_after'],b['denominator']),contribution68_using67_denominator=contribution(b['q_after'],a['denominator'])))
  assert len(rows)==2034 and [x['original67_rank'] for x in rows]==list(range(1,2035))
  totals={key:math.fsum(x[key] for x in rows) for key in ['sse67','sse68','sse_change','contribution67','contribution68','contribution68_using67_denominator']}
  near(totals['sse67'],after['old2034_sse_before']);near(totals['sse68'],after['old2034_sse_after']);near(totals['contribution67'],after['old2034_contribution_before']);near(totals['contribution68'],after['old2034_contribution_after']);near(totals['contribution68_using67_denominator'],after['old2034_after_using_old_denominator'])
  focus=[x for x in rows if x['replay_index'] in plan['fixed67_top2_indices']];assert [x['replay_index'] for x in focus]==plan['fixed67_top2_indices']
 report=dict(passed=True,time=time.time(),all2034_original_ranked_followup=rows,totals=totals,original67_top2=focus,improve=sum(x['sse_change']<0 for x in rows),worsen=sum(x['sse_change']>0 for x in rows),all67_arrays_preserved=True,original68_full2034_review_reproduced=True,original68_review_sha256=sha(root/'REVIEW.json'),values68_sha256=sha(root/'values.npz'),plan_sha256=sha(OUT/'PLAN.json'),new_physics=0,new_forward=0,optimizer_updates=0,replay_writes=0,causal_claim=False,convergence_claim=False,limitation='67 ranking selected posthoc, before68 completion; all2034 retained. Fixedtop2 followup cannot replace full2034 result or original fivefocus. No new stopping criterion.')
 assert not (OUT/'REVIEW.json').exists();(OUT/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(totals=totals,original67_top2=focus),indent=2))
if __name__=='__main__':main()
