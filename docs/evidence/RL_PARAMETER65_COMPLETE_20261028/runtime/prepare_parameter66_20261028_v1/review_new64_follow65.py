"""Independent vector verification of all fixed30 saved64->65 terminal results."""
from pathlib import Path
import json,math,hashlib,os,time
os.sched_setaffinity(0,{53})
import numpy as np
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');P=B/'runs/vmc65_new64_terminal_followup_20261028_v1';T=B/'runs/vmc65_terminal_anchor_followup_20261028_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def near(a,b):assert math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-12),(a,b)
assert read(P/'FINISHED.json')['completed'] and read(T/'SAVED_VALUES_REVIEW.json')['passed']
r=read(P/'REVIEW.json');plan=read(P/'PLAN.json');assert r['passed'];assert sha(T/'values.npz')==r['values65_sha256']
a=read(Path(plan['inputs']['new64_review']['path']));old={x['replay_index']:x for x in a['all30']};assert len(old)==30
with np.load(T/'values.npz',allow_pickle=False) as v:
 loc={int(i):k for k,i in enumerate(v['indices'])};ks=np.array([loc[x['replay_index']] for x in r['all30']]);assert len(ks)==30 and set(ks)==set(range(1914,1944))
 mask=v['masks'][:,ks].astype(np.float64);target=v['rewards'][ks].astype(np.float64)
 before=v['q_before'][:,ks].astype(np.float64);after=v['q_after'][:,ks].astype(np.float64)
 s0=mask*(before-target)**2;s1=mask*(after-target)**2;d0=v['old_denominator'].astype(np.float64);d1=v['denominator'].astype(np.float64)
 per0=s0.sum(axis=0);per1=s1.sum(axis=0);c0=(128*s0/d0[:,None]).sum(axis=0);c1=(128*s1/d1[:,None]).sum(axis=0);c10=(128*s1/d0[:,None]).sum(axis=0)
 for i,row in enumerate(r['all30']):
  o=old[row['replay_index']];assert row['condition']==o['condition'] and row['task64']==o['task'] and row['strict64']==o['strict'] and row['terminal_reward64']==o['terminal_reward']==target[i]
  assert row['q_before']==before[:,i].tolist() and row['q_after']==after[:,i].tolist() and row['masks']==mask[:,i].tolist()
  for key,arr in [('sse_before',per0),('sse_after',per1),('contribution_before',c0),('contribution_after',c1),('after_using_old_denominator',c10)]:near(row[key],arr[i])
 summary=r['summary']
 for key,arr in [('sse_before',per0),('sse_after',per1),('contribution_before',c0),('contribution_after',c1),('after_using_old_denominator',c10)]:near(summary[key],arr.sum())
 assert summary['improved']==int((per1<per0).sum()) and summary['worsened']==int((per1>per0).sum())
 near(c0.sum(),a['new30_contribution'])
out=P/'SAVED_REVIEW.json';assert not out.exists();out.write_text(json.dumps(dict(time=time.time(),passed=True,all30_independently_verified=True,summary=summary,review_sha256=sha(P/'REVIEW.json'),values_sha256=sha(T/'values.npz'),source_sha256=sha(Path(__file__)),new_physics=0,optimizer_updates=0,new_network_forward=0,convergence_claim=False),indent=2)+'\n');print(json.dumps(summary,indent=2))
