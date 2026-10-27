from pathlib import Path
import json,hashlib,time,math
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/parameter45_46_saved_outcomes_20261027_v1';O.mkdir()
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
refs={};methods={}
for m in ['impedance','admittance','vmc']:
 maps=[]
 for c in [45,46]:
  p=B/f'runs/parameter_capacity_pool30_cycle{c}_20261026_v1'/m/'train/episodes.jsonl';r=B/f'runs/parameter_capacity_pool30_cycle{c}_review_20261026_v1/REVIEW.json';reg=p.parent.parent/'REGISTRATION.json';rows=[json.loads(l) for l in p.read_text().splitlines()];d=json.loads(r.read_text());proto=json.loads(reg.read_text())
  assert d['passed'] and len(rows)==30 and len({x['condition'] for x in rows})==30
  assert all(x['cycle']==c for x in rows);assert abs(sum(x['reward'] for x in rows)/30-d['methods'][m]['reward_mean'])<1e-10
  assert {x['condition']:x['model_sha256'] for x in rows}=={x['id']:x['model_sha256'] for x in proto['conditions']}
  maps.append({x['condition']:x for x in rows})
  for f in [p,r,reg]:refs[str(f)]=sha(f)
 a,b=maps;assert a.keys()==b.keys();changes=[]
 for k in sorted(a):
  assert a[k]['model_sha256']==b[k]['model_sha256']
  changed=(a[k]['task_success'],a[k]['strict_success'])!=(b[k]['task_success'],b[k]['strict_success'])
  entry=dict(condition=k,task=[a[k]['task_success'],b[k]['task_success']],strict=[a[k]['strict_success'],b[k]['strict_success']],reward=[a[k]['reward'],b[k]['reward']],completion_time_s=[a[k]['completion_time_s'],b[k]['completion_time_s']],reward_delta=b[k]['reward']-a[k]['reward'],contribution_to_mean=(b[k]['reward']-a[k]['reward'])/30,success_changed=changed)
  if changed:
   physics=[]
   for old in [a[k],b[k]]:
    folder=Path(old['episode_path']);p=folder/'rollout.json';evaluator=folder/'executed_evaluator.py.txt';d=json.loads(p.read_text());source=evaluator.read_text()
    assert "physical_valid=abort_reason is None and stats['max_external_penetration_m']<=.0002" in source
    assert "result['strict_success']=bool(result['task_success'] and result['physical_valid'])" in source
    assert d['task_success']==old['task_success'] and d['strict_success']==old['strict_success']
    assert d['physical_valid']==(d['abort_reason'] is None and d['stats']['max_external_penetration_m']<=.0002)
    assert sha(folder/'rollout.mjb')==old['model_sha256']==d['model_sha256']
    physics.append(dict(external_penetration_mm=1000*d['stats']['max_external_penetration_m'],peak_motor_torque_nm=d['stats']['peak_motor_torque_nm'],physical_valid=d['physical_valid'],source_sha256=sha(evaluator),model_sha256=d['model_sha256']))
    refs[str(p)]=sha(p);refs[str(evaluator)]=sha(evaluator)
   entry['saved_physics']=physics
  changes.append(entry)
 total=sum(x['reward_delta'] for x in changes)/30;changed=sum(x['contribution_to_mean'] for x in changes if x['success_changed']);other=sum(x['contribution_to_mean'] for x in changes if not x['success_changed']);assert abs(total-changed-other)<1e-12
 methods[m]=dict(mean_delta=total,success_changed_contribution=changed,other_conditions_contribution=other,conditions=changes)
for p,h in refs.items():assert sha(Path(p))==h
report=dict(passed=True,time=time.time(),cycles=[45,46],methods=methods,input_hashes=refs,new_physics=0,optimizer_updates=0,reward_or_gate_changed=False,limitation='Arithmetic attribution of saved online outcomes and original physical-valid reducer only; no causal learning-versus-randomness decomposition, no raw substep recomputation, no convergence claim.')
(O/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({m:{k:v for k,v in d.items() if k!='conditions'} for m,d in methods.items()},indent=2))
