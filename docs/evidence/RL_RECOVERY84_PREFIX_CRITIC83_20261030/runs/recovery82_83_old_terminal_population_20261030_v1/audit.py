from pathlib import Path
import hashlib,json,time,math,os
import numpy as np
os.sched_setaffinity(0,{3})
D=Path(__file__).parent;B=D.parents[1]
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):
 with p.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
plan=read(D/'PLAN.json');assert plan['source_sha256']==sha(__file__)
for r in plan['inputs'].values():assert sha(r['path'])==r['sha256']
result={}
for m in plan['methods']:
 t=B/f'runs/{m}_recovery83_terminal_followup_20261029_v1';prior=read(t/'REVIEW.json');assert prior['passed'] and read(t/'SAVED_VALUES_REVIEW.json')['passed']
 with np.load(t/'anchor82.npz',allow_pickle=False) as z:a={k:z[k].copy() for k in z.files}
 with np.load(t/'values.npz',allow_pickle=False) as z:v={k:z[k].copy() for k in z.files}
 n=2454;assert len(a['indices'])==n and a['features'].shape==(n,57)
 for k in ['indices','rewards']:np.testing.assert_array_equal(a[k],v[k][:n])
 np.testing.assert_array_equal(a['masks'],v['masks'][:,:n]);np.testing.assert_array_equal(a['q_after'],v['q_before']);np.testing.assert_array_equal(a['denominator'],v['old_denominator'])
 idx=a['indices'];r=a['rewards'].astype(float);mask=a['masks'].astype(float);before=v['q_before'].astype(float);after=v['q_after'][:,:n].astype(float)
 assert np.isfinite(a['features']).all() and np.isfinite(before).all() and np.isfinite(after).all() and set(np.unique(mask))=={0,1}
 sb=mask*(before-r[None,:])**2;sa=mask*(after-r[None,:])**2;delta=sa-sb
 episodes=[json.loads(l) for l in (B/f'runs/parameter_partial75_recovery_cycle82_20261029_v1/{m}/train/episodes.jsonl').read_text().splitlines()];emap={x['total_steps']-1:x for x in episodes};assert len(emap)==30 and set(emap)==set(map(int,idx[-30:]))
 rows=[]
 for j,i in enumerate(idx):
  row=dict(replay_index=int(i),cohort='new_in82' if j>=2424 else 'before82',terminal_reward=float(r[j]),masks=mask[:,j].tolist(),q82=before[:,j].tolist(),q83=after[:,j].tolist(),sse82=math.fsum(sb[:,j]),sse83=math.fsum(sa[:,j]),delta_sse=math.fsum(delta[:,j]),condition82=emap[int(i)]['condition'] if int(i) in emap else None)
  rows.append(row)
 with (D/(m+'_all2454.jsonl')).open('x') as f:
  for row in rows:f.write(json.dumps(row)+'\n')
 def group(sel):
  z=np.asarray(sel,dtype=bool);return dict(rows=int(z.sum()),sse82=float(sb[:,z].sum()),sse83=float(sa[:,z].sum()),delta=float(delta[:,z].sum()),inmask_pairs=int(mask[:,z].sum()),opposite_sign82=int(((before[:,z]*r[None,z]<0)&(mask[:,z]==1)).sum()),opposite_sign83=int(((after[:,z]*r[None,z]<0)&(mask[:,z]==1)).sum()))
 groups={k:group(sel) for k,sel in {'all2454':np.ones(n,bool),'before82':np.arange(n)<2424,'new_in82':np.arange(n)>=2424,'positive_terminal_reward':r>0,'negative_terminal_reward':r<0,'zero_terminal_reward':r==0}.items()}
 assert math.isclose(groups['all2454']['sse82'],prior['old2454_sse_before'],rel_tol=1e-12) and math.isclose(groups['all2454']['sse83'],prior['old2454_sse_after'],rel_tol=1e-12)
 percritic=[dict(critic=c,inmask_rows=int(mask[c].sum()),sse82=float(sb[c].sum()),sse83=float(sa[c].sum()),delta=float(delta[c].sum()),opposite_sign82=int(((before[c]*r<0)&(mask[c]==1)).sum()),opposite_sign83=int(((after[c]*r<0)&(mask[c]==1)).sum())) for c in range(5)]
 positive=sorted((x for x in rows if x['delta_sse']>0),key=lambda x:x['delta_sse'],reverse=True);negative=sorted((x for x in rows if x['delta_sse']<0),key=lambda x:x['delta_sse']);positive_total=math.fsum(x['delta_sse'] for x in positive);negative_total=math.fsum(x['delta_sse'] for x in negative)
 # Equality uses all57 actual float feature values (including action/clock); -0 equals0.
 identical={}
 for j,feature in enumerate(a['features']):identical.setdefault(tuple(map(float,feature)),[]).append(j)
 duplicates=[g for g in identical.values() if len(g)>1];conflicts=[]
 for g in duplicates:
  for c in range(5):
   present=[j for j in g if mask[c,j]==1]
   if len(present)>1 and len({float(r[j]) for j in present})>1:conflicts.append(dict(critic=c,indices=[int(idx[j]) for j in present],rewards=[float(r[j]) for j in present]))
 out=dict(groups=groups,critics=percritic,row_changes=dict(increased=len(positive),decreased=len(negative),unchanged=n-len(positive)-len(negative),sum_increases=positive_total,sum_decreases=negative_total,top10_increase_fraction=math.fsum(x['delta_sse'] for x in positive[:10])/positive_total if positive_total else None),largest10_increases=positive[:10],largest10_decreases=negative[:10],new_in82_all30=[x for x in rows if x['cohort']=='new_in82'],exact_feature_duplicate_groups=len(duplicates),conflicting_targets_same_features_and_active_critic=conflicts,allrows_sha256=sha(D/(m+'_all2454.jsonl')))
 result[m]=out
for r in plan['inputs'].values():assert sha(r['path'])==r['sha256']
put(D/'REVIEW.json',dict(passed=True,time=time.time(),methods=result,new_physics=0,optimizer_updates=0,new_network_forward=0,replay_writes=0,convergence_claim=False,causal_claim=False,limitation='Retrospective all2454 unchanged features/actions/rewards/masks at checkpoints82/83. All old rows predate all41250 cycle83 updates, but actual sampling unknown. Largest10 selected after observing errors, descriptive only. Exact feature equality scan cannot exclude near-aliasing, insufficient representation, or other unobserved conflicts. No new health threshold.'))
for m,x in result.items():print(m,json.dumps({k:x[k] for k in ['groups','critics','row_changes','exact_feature_duplicate_groups']}));print('largest3',m,[(x['replay_index'],x['delta_sse'],x['terminal_reward']) for x in x['largest10_increases'][:3]])
