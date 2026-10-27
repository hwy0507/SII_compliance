from pathlib import Path
import json,hashlib,math,time,os
os.sched_setaffinity(0,{54})
b=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');run=b/'runs/parameter_capacity_pool30_cycle39_20261026_v1/impedance';folder=run/'train/cycle_00039/active_long_train_0000';inputs={}
def raw(p):
 d=p.read_bytes();inputs[str(p)]=hashlib.sha256(d).hexdigest();return d
def read(p):return json.loads(raw(p))
es=[json.loads(l) for l in raw(run/'train/episodes.jsonl').splitlines()];assert len(es)==30
aborts=[e for e in es if e['abort_reason']];assert len(aborts)==1;e=aborts[0]
r=read(folder/'rollout.json');t=read(folder/'TERMINAL.json');reg=read(run/'REGISTRATION.json');condition=next(c for c in reg['conditions'] if c['id']==e['condition'])
assert e['condition']=='active_long_train_0000' and e['steps']==555
assert e['abort_reason']==t['result']['abort_reason']==r['abort_reason']=='global_penetration_exceeded_2mm'
assert not e['task_success'] and not e['strict_success'] and not e['full_task_horizon_completed']
assert r['metrics']['samples']==555*800 and r['metrics']['timestep_s']==5e-5
assert math.isclose(t['terminal_time_s'],555*.04,abs_tol=1e-8)
assert r['stats']['max_penetration_m']>.002
assert r['stats']['max_external_penetration_m']<.0002
assert hashlib.sha256((folder/'rollout.mjb').read_bytes()).hexdigest()==r['model_sha256']==t['model_sha256']==e['model_sha256']==condition['model_sha256']
source=raw(folder/'executed_evaluator.py.txt').decode();assert "if stats['max_penetration_m']>.002:abort_reason='global_penetration_exceeded_2mm';break" in source
for p,h in inputs.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
out=dict(passed=True,time=time.time(),inputs=inputs,condition=e['condition'],steps=e['steps'],time_s=t['terminal_time_s'],physical_samples=r['metrics']['samples'],global_penetration_mm=r['stats']['max_penetration_m']*1000,worst_pair=r['stats']['worst_pair'],external_penetration_mm=r['stats']['max_external_penetration_m']*1000,worst_external_pair=r['stats']['worst_external_pair'],full_horizon_count=sum(x['full_task_horizon_completed'] for x in es),denominator=30,new_physics=0,optimizer_updates=0,limitation='Saved aggregate, original executable gate and model binding verification; no raw substep recomputation, causal replay or alteration of original threshold. Global includes payload contacts and is distinct from external robot penetration.')
p=b/'runs/parameter_capacity_pool30_cycle39_review_20261026_v1/SAVED_ABORT_REVIEW.json'
with p.open('x') as f:f.write(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
