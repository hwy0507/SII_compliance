from pathlib import Path
import hashlib,json,time,math,os
os.sched_setaffinity(0,{54})
import numpy as np
D=Path(__file__).parent;B=D.parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
plan=read(D/'PLAN.json');root=Path(plan['parent_run']);rev=Path(plan['parent_review'])
assert (root/'ARCHIVE_REVIEW_FINISHED.json').exists(),'Complete85 review not ready'
assert read(root/'ARCHIVE_REVIEW_FINISHED.json')['completed'] and read(rev/'FINISHED.json')['completed'] and read(rev/'REVIEW.json')['passed']
assert plan['fixed_rows']==2514 and plan['all_critics']==[0,1,2,3,4]
for r in plan['inputs']:assert sha(Path(r['path']))==r['sha256']
results={}
for m in plan['methods']:
 t=B/f'runs/{m}_recovery85_terminal_followup_20261029_v1';assert read(t/'FINISHED.json')['completed'] and read(t/'SAVED_VALUES_REVIEW.json')['passed'];prior=read(t/'REVIEW.json');assert prior['passed'] and prior['original_fixed_observations_actions_rewards_masks_exact']
 with np.load(t/'anchor84.npz',allow_pickle=False) as z:a={k:z[k].copy() for k in z.files}
 with np.load(t/'values.npz',allow_pickle=False) as z:v={k:z[k].copy() for k in z.files}
 n=2514;assert len(v['indices'])==2544 and a['features'].shape==(2514,57)
 for k in ['indices','rewards']:np.testing.assert_array_equal(a[k],v[k][:n])
 np.testing.assert_array_equal(a['masks'],v['masks'][:,:n]);np.testing.assert_array_equal(a['q_after'],v['q_before']);np.testing.assert_array_equal(a['denominator'],v['old_denominator'])
 before=a['q_after'].astype(float);after=v['q_after'][:,:n].astype(float);rewards=a['rewards'].astype(float);mask=a['masks'].astype(float);sb=mask*(before-rewards[None,:])**2;sa=mask*(after-rewards[None,:])**2
 episodes=[json.loads(l) for l in (B/f'runs/parameter_partial75_recovery_cycle84_20261029_v1/{m}/train/episodes.jsonl').read_text().splitlines()];emap={e['total_steps']-1:e['condition'] for e in episodes};assert set(emap)==set(map(int,a['indices'][-30:]));rows=[]
 for i,index in enumerate(a['indices']):
  rows.append(dict(index=int(index),condition84=emap.get(int(index)),cohort='new84' if i>=2484 else 'before84',reward=float(rewards[i]),masks=mask[:,i].tolist(),q84=before[:,i].tolist(),q85=after[:,i].tolist(),sse84=math.fsum(sb[:,i]),sse85=math.fsum(sa[:,i])))
 path=D/(m+'_all2514.jsonl')
 with path.open('x') as f:
  for r in rows:f.write(json.dumps(r)+'\n')
 saved=[json.loads(l) for l in path.read_text().splitlines()];assert saved==rows
 for i,r in enumerate(saved):
  for cycle,q in [(84,before),(85,after)]:
   expected=math.fsum(float(mask[c,i])*(float(q[c,i])-float(rewards[i]))**2 for c in range(5));assert math.isclose(expected,r['sse'+str(cycle)],rel_tol=1e-12,abs_tol=1e-12)
 critics=[dict(critic=c,inmask_rows=int(mask[c].sum()),sse84=math.fsum(sb[c]),sse85=math.fsum(sa[c]),opposite_sign84=int(((before[c]*rewards<0)&(mask[c]==1)).sum()),opposite_sign85=int(((after[c]*rewards<0)&(mask[c]==1)).sum())) for c in range(5)]
 assert math.isclose(math.fsum(r['sse84'] for r in rows),prior['old2514_sse_before'],rel_tol=1e-12) and math.isclose(math.fsum(r['sse85'] for r in rows),prior['old2514_sse_after'],rel_tol=1e-12)
 results[m]=dict(critics=critics,all30_new84=[r for r in rows if r['cohort']=='new84'],total_sse84=math.fsum(r['sse84'] for r in rows),total_sse85=math.fsum(r['sse85'] for r in rows),all2514_saved_scalar_verified=True,allrows_sha256=sha(path),values_sha256=sha(t/'values.npz'),features_actions_rewards_masks_exact=True)
put(D/'REVIEW.json',dict(passed=True,time=time.time(),methods=results,new_physics=0,new_network_forward=0,optimizer_updates=0,convergence_claim=False,limitation='Same2514 fixed inputs/masks at84 and85, all5 critics and complete new84 cohort. Descriptive followup to frozen84 gradient opposition; no historical gradient/minibatch reconstruction or new health gate.'))
assert read(D/'REVIEW.json')['methods']==results
put(D/'SAVED_REVIEW.json',dict(passed=True,time=time.time(),all5028_rows_and25140_q_pairs_scalar_recomputed=True,report_sha256=sha(D/'REVIEW.json')))
