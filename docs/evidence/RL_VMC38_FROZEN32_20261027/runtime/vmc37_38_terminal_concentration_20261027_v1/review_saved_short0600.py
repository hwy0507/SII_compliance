from pathlib import Path
import hashlib,json,time,os
os.sched_setaffinity(0,{52})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');root=B/'runs/vmc37_38_terminal_concentration_20261027_v1';inputs={}
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):inputs[str(p)]=sha(p);return json.loads(p.read_text())
rows=[]
for c in [37,38]:
 r=B/f'runs/parameter_capacity_pool30_cycle{c}_20261026_v1/vmc/train/cycle_{c:05}/active_short_train_0600';rollout=read(r/'rollout.json');terminal=read(r/'TERMINAL.json')
 for name in ['office_task_v4_20260917.py','planned_hand_corner_20261002.py','validate_office_apparatus_v5_20260917.py']:
  p=B/'runtime/source_train17_clock/source/scripts'/name;inputs[str(p)]=sha(p);assert rollout['source_sha256'][name]==inputs[str(p)]
 model=r/'rollout.mjb';inputs[str(model)]=sha(model);assert inputs[str(model)]==rollout['model_sha256']==terminal['model_sha256']
 result=terminal['result']
 for k in ['task_success','strict_success','physical_valid','full_task_horizon_completed','abort_reason']:assert result[k]==rollout[k]
 peak=rollout['stats']['max_external_penetration_m'];assert result['physical_valid']==(peak<=.0002);assert result['strict_success']==(result['task_success'] and result['physical_valid'])
 assert result['full_task_horizon_completed'] and result['abort_reason'] is None and result['task_success']
 rows.append(dict(cycle=c,result=result,peak_external_penetration_mm=peak*1000,margin_below_existing_gate_mm=(.0002-peak)*1000,worst_external_pair=rollout['stats']['worst_external_pair'],model_sha256=inputs[str(model)],completion_time_s=terminal['completion_time_s'],task_events=rollout['task_events']))
assert rows[0]['model_sha256']==rows[1]['model_sha256']
for p,h in inputs.items():assert sha(p)==h
out=dict(passed=True,time=time.time(),condition='active_short_train_0600',controller='vmc',cycles=rows,inputs=inputs,source_sha256=sha(__file__),new_physics=0,neural_inference=0,optimizer_updates=0,convergence_claim=False,scope='Saved complete37/38 JSON aggregate and original source/model hashes. Confirms recorded Strict switch matches original0.2mm external penetration gate; no new raw-substep reconstruction, causal policy claim, threshold adjustment, or counterfactual replay.')
with (root/'SAVED_SHORT0600_REVIEW.json').open('x') as f:f.write(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['inputs']},indent=2))
