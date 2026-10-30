from pathlib import Path
import ast,hashlib,json,math,time,os
os.sched_setaffinity(0,{54})
import numpy as np
D=Path(__file__).parent;B=D.parents[1]
def read(p):return json.loads(p.read_text())
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def put(p,r):
 with p.open('x') as f:json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
plan=read(D/'INPUT_REVIEW_PLAN.json')
for x in plan['inputs']:assert ref(Path(x['path']))==x
assert ref(Path(__file__))==plan['source']
report=read(D/'REVIEW.json');age=read(D/'UPDATE_AVAILABILITY_REVIEW.json');result={}
for m in ['vmc','admittance']:
 p=B/f'runs/{m}_recovery85_terminal_followup_20261029_v1';assert read(p/'ANCHOR_SAVED_REVIEW.json')['passed']
 with np.load(p/'anchor84.npz',allow_pickle=False) as z:a={k:z[k].copy() for k in z.files}
 x=a['features'].astype(float);idx=a['indices'];reward=a['rewards'].astype(float);mask=a['masks'];q=a['q_after'];assert x.shape==(2514,57)
 positions={int(v):i for i,v in enumerate(idx)};pairs={r['condition']:r for r in report['methods'][m]['pairs']};timing={r['condition']:r for r in age['methods'][m]};rows=[]
 for condition,pair in sorted(pairs.items()):
  old=pair['cases']['83'];new=pair['cases']['84'];i=positions[new['terminal_replay_index']];j=positions[old['terminal_replay_index']];assert i>=2484 and j<2484
  pred=new['terminal_prediction'];assert pred['reward']==float(reward[i]) and pred['masks']==mask[:,i].tolist() and pred['complete84_q']==q[:,i].tolist()
  d2=np.sum((x-x[i])**2,axis=1);d2[i]=np.inf;neighbors=[]
  for c in range(5):
   if not mask[c,i]:continue
   for sign in ['same','opposite']:
    eligible=np.flatnonzero((mask[c]==1)&((reward*reward[i]>0) if sign=='same' else (reward*reward[i]<0))&(np.arange(len(idx))!=i))
    assert len(eligible)>0;nearest=int(eligible[np.argmin(d2[eligible])]);manual=math.fsum((float(v)-float(w))**2 for v,w in zip(x[i],x[nearest]));assert math.isclose(manual,float(d2[nearest]),rel_tol=1e-12,abs_tol=1e-12)
    neighbors.append(dict(critic=c,sign=sign,candidates=len(eligible),index=int(idx[nearest]),reward=float(reward[nearest]),input_l2=math.sqrt(manual),observation_l2=math.sqrt(math.fsum((x[i,k]-x[nearest,k])**2 for k in range(50))),action_l2=math.sqrt(math.fsum((x[i,k]-x[nearest,k])**2 for k in range(50,57))),critic_q=float(q[c,nearest])))
  rows.append(dict(condition=condition,replay_index=int(idx[i]),reward=float(reward[i]),task=new['task'],strict=new['strict'],updates_available=timing[condition]['optimizer_updates_after_append_including_same_step'],masked_sse=pred['complete84_masked_sse'],same_condition83_input_l2=float(np.linalg.norm(x[i]-x[j])),same_condition83_reward=float(reward[j]),nearest_by_active_critic=neighbors))
 groups={}
 for j,feature in enumerate(x):groups.setdefault(tuple(map(float,feature)),[]).append(j)
 duplicates=[g for g in groups.values() if len(g)>1];assert len(groups)==len(np.unique(x,axis=0))
 result[m]=dict(all30_new_terminal_rows=rows,all2514_exact_duplicate_feature_groups=len(duplicates),anchor=ref(p/'anchor84.npz'))
runtime=B/'runtime/source_train17_clock';hashes=read(runtime/'SOURCE_HASHES.json')
sources={}
for rel in ['scripts/validate_office_apparatus_v5_20260917.py','tools/published_compliance_learner_20261025.py','tools/spt_rl_reward_20261025.py']:
 p=runtime/'source'/rel;assert ref(p)['sha256']==hashes[rel];sources[rel]=p.read_text()
e=sources['scripts/validate_office_apparatus_v5_20260917.py'];l=sources['tools/published_compliance_learner_20261025.py'];r=sources['tools/spt_rl_reward_20261025.py']
assert 'observation=np.r_[q[:7],dq[:7],command,error,command-twist,load,wrench,direction]' in e
assert "physical_valid=abort_reason is None and stats['max_external_penetration_m']<=.0002" in e
assert "result['strict_success']=bool(result['task_success'] and result['physical_valid'])" in e
assert 'value = value / OBSERVATION_SCALE' in l and 'self.hybrid.get_mixing_parameter()' in l and '(1375-self.episode_actions[stream])/1375' in l
assert "success = bool(terminated and task_success and strict_success)" in r and "terms['terminal'] = (cfg['success_bonus'] if success else -cfg['failure_penalty']) if terminated else 0." in r
interpretation='Source-bound critic input is scaled canonical48, mixing coefficient, remaining clock and7 actions. Canonical48 lists current proprioceptive/command/error/load/wrench/direction fields, not an explicit cumulative penetration maximum or strict-validity history flag. Original terminal reward is+25/-25 according to Strict plus unchanged shaping/completion bonus. This motivates investigating partial observability but does not prove impossible fitting or causal gradient interference: inputs here are distinct, current signals may carry indirect history, and actual minibatch inclusion is unknown. L2 is a descriptive distance in existing network input coordinates, not a validated metric, threshold, or new health gate; all30/method and all active critics included.'
put(D/'INPUT_REVIEW.json',dict(passed=True,time=time.time(),methods=result,original_source_hashes_verified=True,interpretation=interpretation,new_physics=0,new_network_forward=0,optimizer_updates=0,replay_writes=0,convergence_claim=False))
saved=read(D/'INPUT_REVIEW.json');assert saved['methods']==result
put(D/'INPUT_SAVED_REVIEW.json',dict(passed=True,time=time.time(),all60_rows_and_neighbors_read_back=True,selected_distance_independent_math_fsum=True,exact_duplicates_second_algorithm_verified=True,review=ref(D/'INPUT_REVIEW.json')))
for m,x in result.items():
 print(m,'duplicate_groups',x['all2514_exact_duplicate_feature_groups'])
 for row in x['all30_new_terminal_rows']:
  if m=='vmc' and row['condition'] in ['active_short_train_0600','active_long_train_0400','active_short_train_0200']:print(json.dumps(row))
