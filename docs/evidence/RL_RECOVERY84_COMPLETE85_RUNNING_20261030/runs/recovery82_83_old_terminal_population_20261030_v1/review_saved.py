from pathlib import Path
import json,math,hashlib,time,os
import numpy as np
os.sched_setaffinity(0,{3})
D=Path(__file__).parent;B=D.parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b):assert math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-8),(a,b)
r=read(D/'REVIEW.json');plan=read(D/'PLAN.json');assert r['passed'] and sha(D/'audit.py')==plan['source_sha256']
for x in plan['inputs'].values():assert sha(Path(x['path']))==x['sha256']
for m,res in r['methods'].items():
 rows=[json.loads(l) for l in (D/(m+'_all2454.jsonl')).read_text().splitlines()];assert len(rows)==2454 and sha(D/(m+'_all2454.jsonl'))==res['allrows_sha256']
 with np.load(B/f'runs/{m}_recovery83_terminal_followup_20261029_v1/values.npz',allow_pickle=False) as z:
  assert [x['replay_index'] for x in rows]==z['indices'][:2454].tolist()
  for j,x in enumerate(rows):
   assert x['terminal_reward']==float(z['rewards'][j]) and x['masks']==z['masks'][:,j].tolist() and x['q82']==z['q_before'][:,j].tolist() and x['q83']==z['q_after'][:,j].tolist()
   for suffix in ['82','83']:close(math.fsum(w*(q-x['terminal_reward'])**2 for w,q in zip(x['masks'],x['q'+suffix])),x['sse'+suffix])
   close(x['sse83']-x['sse82'],x['delta_sse'])
 for c,stats in enumerate(res['critics']):
  for suffix in ['82','83']:close(math.fsum(x['masks'][c]*(x['q'+suffix][c]-x['terminal_reward'])**2 for x in rows),stats['sse'+suffix]);assert sum(x['masks'][c]==1 and x['q'+suffix][c]*x['terminal_reward']<0 for x in rows)==stats['opposite_sign'+suffix]
  close(stats['sse83']-stats['sse82'],stats['delta']);assert sum(x['masks'][c] for x in rows)==stats['inmask_rows']
 groups={'all2454':rows,'before82':rows[:2424],'new_in82':rows[2424:],'positive_terminal_reward':[x for x in rows if x['terminal_reward']>0],'negative_terminal_reward':[x for x in rows if x['terminal_reward']<0],'zero_terminal_reward':[x for x in rows if x['terminal_reward']==0]}
 for key,items in groups.items():
  stats=res['groups'][key];assert len(items)==stats['rows']
  for suffix in ['82','83']:close(math.fsum(x['sse'+suffix] for x in items),stats['sse'+suffix]);assert sum(w==1 and q*x['terminal_reward']<0 for x in items for w,q in zip(x['masks'],x['q'+suffix]))==stats['opposite_sign'+suffix]
  close(math.fsum(x['delta_sse'] for x in items),stats['delta']);assert sum(sum(x['masks']) for x in items)==stats['inmask_pairs']
 up=sorted([x for x in rows if x['delta_sse']>0],key=lambda x:x['delta_sse'],reverse=True);down=sorted([x for x in rows if x['delta_sse']<0],key=lambda x:x['delta_sse']);ch=res['row_changes'];assert len(up)==ch['increased'] and len(down)==ch['decreased'] and 2454-len(up)-len(down)==ch['unchanged'];assert up[:10]==res['largest10_increases'] and down[:10]==res['largest10_decreases']
 close(math.fsum(x['delta_sse'] for x in up),ch['sum_increases']);close(math.fsum(x['delta_sse'] for x in down),ch['sum_decreases']);close(math.fsum(x['delta_sse'] for x in up[:10])/math.fsum(x['delta_sse'] for x in up),ch['top10_increase_fraction'])
 with np.load(B/f'runs/{m}_recovery83_terminal_followup_20261029_v1/anchor82.npz',allow_pickle=False) as z:
  f=z['features'];unique=np.unique(f,axis=0);assert len(unique)==2454 and res['exact_feature_duplicate_groups']==0 and res['conflicting_targets_same_features_and_active_critic']==[]
out=dict(passed=True,time=time.time(),methods=2,rows_per_method=2454,critic_predictions_checked=24540,all_original_arrays_exact=True,all_scalar_groups_and_top10_verified=True,exact_feature_unique_numpy_verified=True,source_sha256=sha(Path(__file__)),new_physics=0,optimizer_updates=0,new_network_forward=0,limitation='Saved arithmetic independently recomputed using math.fsum; original NumPy Q inputs are shared, no independent neural forward or physical validation.')
with (D/'SAVED_REVIEW.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(out))
