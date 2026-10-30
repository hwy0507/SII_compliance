from pathlib import Path
import json,time,hashlib,os,math
import numpy as np
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;os.sched_setaffinity(0,{54})
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
plan=read(D/'PLAN.json');assert sha(Path(__file__))==plan['source']['sha256'];labels=read(B/'runs/parameter_recovery84_task_labels_20261029_v1/COMPLETE83_84.json');results={};inputs=[]
for m in ['impedance','admittance','vmc']:
 episodes={}
 for c in [83,84]:
  p=B/f'runs/parameter_partial75_recovery_cycle{c}_20261029_v1/{m}/train/episodes.jsonl';rows=[json.loads(l) for l in p.read_text().splitlines()];assert len(rows)==30;episodes[c]={r['condition']:r for r in rows};assert len(episodes[c])==30;inputs.append(ref(p))
 assert set(episodes[83])==set(episodes[84])
 values=None
 if m!='impedance':
  t=B/f'runs/{m}_recovery84_terminal_followup_20261029_v1';assert read(t/'REVIEW.json')['passed'] and read(t/'SAVED_VALUES_REVIEW.json')['passed'];assert sha(t/'values.npz')==read(t/'REVIEW.json')['values_sha256'];inputs.append(ref(t/'values.npz'))
  with np.load(t/'values.npz',allow_pickle=False) as z:values={n:z[n].copy() for n in z.files}
  assert len(values['indices'])==2514;by_index={int(v):i for i,v in enumerate(values['indices'])}
 paired=[]
 for case in sorted(episodes[83]):
  pair={}
  for c in [83,84]:
   e=episodes[c][case];p=Path(e['episode_path'])/'rollout.json';r=read(p);assert r['task_success']==e['task_success'] and r['strict_success']==e['strict_success'] and r['physical_valid']==e['physical_valid']
   stages=r['task_events'];assert all(x['time_s']>=0 for x in stages) and all(y['time_s']>=x['time_s'] for x,y in zip(stages,stages[1:]))
   pair[str(c)]=dict(task=r['task_success'],strict=r['strict_success'],physical_valid=r['physical_valid'],abort=r['abort_reason'],stage=r['final_task_stage'],task_events=stages,placement_hold_s=r['placement_hold_s'],placement_error_xy_m=r['placement_error_xy_m'],object_final_position=r['object_final_position'],max_lift_m=r['max_lift_m'],rollout=ref(p),terminal_replay_index=e['total_steps']-1,episode_reward=e['reward'])
   if values is not None:
    k=by_index[e['total_steps']-1];assert (k<2484 if c==83 else k>=2484)
    reward=float(values['rewards'][k]);mask=values['masks'][:,k];q=values['q_after'][:,k];sse=math.fsum(float(mask[j])*(float(q[j])-reward)**2 for j in range(5));contrib=math.fsum(128*float(mask[j])*(float(q[j])-reward)**2/float(values['denominator'][j]) for j in range(5))
    pair[str(c)]['terminal_prediction']=dict(reward=reward,masks=mask.tolist(),complete84_q=q.tolist(),complete84_masked_sse=sse,complete84_contribution=contrib,mask_in_sign_mismatch_critics=[j for j in range(5) if mask[j] and float(q[j])*reward<0])
    if c==83:
     q0=values['q_before'][:,k];pair[str(c)]['terminal_prediction'].update(complete83_q=q0.tolist(),complete83_masked_sse=math.fsum(float(mask[j])*(float(q0[j])-reward)**2 for j in range(5)))
  a,b=pair['83'],pair['84'];paired.append(dict(condition=case,task_changed=a['task']!=b['task'],strict_changed=a['strict']!=b['strict'],stage_changed=a['stage']!=b['stage'],cases=pair))
 for c in [83,84]:
  assert sum(p['cases'][str(c)]['task'] for p in paired)==labels['methods'][m]['counts'][str(c)]['task']
  assert sum(p['cases'][str(c)]['strict'] for p in paired)==labels['methods'][m]['counts'][str(c)]['strict']
 results[m]=dict(pairs=paired,task_changes=[p['condition'] for p in paired if p['task_changed']],strict_changes=[p['condition'] for p in paired if p['strict_changed']],stage_changes=[p['condition'] for p in paired if p['stage_changed']])
put(D/'REVIEW.json',dict(passed=True,time=time.time(),methods=results,inputs=inputs,behavior_pairs=90,terminal_prediction_pairs=60,new_physics=0,optimizer_updates=0,new_network_forward=0,convergence_claim=False,limitation='Retrospective all30 conditions each method; map saved task events and endpoint criteria to fixed complete84 Q on old83 and new84 terminal rows. Same-condition rows have different states/actions/masks and collection-time policies; differences do not isolate critic causality or historical optimizer minibatches. Saved task events not independently reconstructed physics. No changes to55s horizon, gate, reward or policy.'))
r=read(D/'REVIEW.json');assert r['methods']==results
put(D/'SAVED_REVIEW.json',dict(passed=True,time=time.time(),all90_pairs_read_back=True,source=ref(Path(__file__)),review=ref(D/'REVIEW.json')))
for m,x in results.items():
 print(m,'task_changes',x['task_changes'],'strict_changes',x['strict_changes'])
 for p in x['pairs']:
  if p['task_changed'] or p['strict_changed']:
   print(p['condition'],json.dumps(p['cases']))
