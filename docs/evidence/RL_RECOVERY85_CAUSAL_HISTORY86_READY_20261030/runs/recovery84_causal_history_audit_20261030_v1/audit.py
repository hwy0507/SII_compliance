from pathlib import Path
import json,time,hashlib,math,os
import numpy as np
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent
read=lambda p:json.loads(p.read_text())
def ref(p):
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
def write(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
plan=read(D/'PLAN.json');os.sched_setaffinity(0,{plan['cpu']});start=time.time()
for x in plan['source']:assert ref(Path(x['path']))['sha256']==x['sha256']
methods={};sources={}
for m in plan['methods']:
 ep=B/f'runs/parameter_partial75_recovery_cycle84_20261029_v1/{m}/train/episodes.jsonl'
 rows=[json.loads(l) for l in ep.read_text().splitlines()];assert len(rows)==30 and len({r['condition'] for r in rows})==30
 sources[m]=ref(ep);cases=[]
 for row in rows:
  assert time.time()-start<plan['budget_seconds']
  p=Path(row['episode_path']);paths=[p/n for n in ['actor_intervals.jsonl','TERMINAL.json','rollout.json','rollout.npz']];before=[ref(a) for a in paths]
  js=[json.loads(l) for l in paths[0].read_text().splitlines()];term=read(paths[1]);roll=read(paths[2]);n=len(js);assert n==1375==row['steps']
  assert js[0]['interval'] is None and all(x['interval'] is not None for x in js[1:])
  iv=[x['interval'] for x in js[1:]]+[term['interval']]
  peaks=np.array([0.]+[x['external_penetration_peak_m'] for x in iv],dtype=np.float64)
  dt=np.array([x['elapsed_s'] for x in iv]);counts=np.array([x['substeps'] for x in iv])
  assert np.isfinite(peaks).all() and (peaks>=0).all() and (np.diff(peaks)>=0).all()
  assert np.all(counts==800) and np.allclose(dt,.04,rtol=0,atol=1e-12)
  with np.load(paths[3],allow_pickle=False) as z:
   times=z['neuron_time'].copy();assert np.array_equal(z['observation'],np.array([x['observation'] for x in js]))
   assert np.array_equal(z['applied_action'],np.array([x['executed_action'] for x in js]))
   assert len(times)==n and abs(times[0])<plan['clock_atol_s']
  cumulative=np.r_[0.,np.cumsum(dt)]
  clock_error=float(np.max(np.abs(times-cumulative[:-1])));assert clock_error<plan['clock_atol_s']
  assert abs(term['terminal_time_s']-cumulative[-1])<plan['clock_atol_s']
  assert peaks[-1]==roll['stats']['max_external_penetration_m']
  for k in ['task_success','strict_success','physical_valid','abort_reason','full_task_horizon_completed']:
   assert row[k]==term['result'][k]==roll[k]
  assert row['abort_reason'] is None and row['full_task_horizon_completed']
  # Current physical_valid also includes other gates. Do not equate penetration alone with it.
  if peaks[-1]>.0002:assert not row['physical_valid'] and not row['strict_success']
  if row['strict_success']:assert row['task_success'] and row['physical_valid'] and peaks[-1]<=.0002
  bad=np.flatnonzero(peaks[:-1]>.0002);cross=np.flatnonzero((peaks[:-1]<=.0002)&(peaks[1:]>.0002))
  out=D/m;out.mkdir(exist_ok=True);npz=out/(row['condition']+'.npz')
  assert not npz.exists();np.savez_compressed(npz,action_time_s=times,preaction_peak_m=peaks[:-1],next_observation_peak_m=peaks[1:],preaction_penetration_gate_valid=peaks[:-1]<=.0002)
  case=dict(condition=row['condition'],actions=n,task=row['task_success'],strict=row['strict_success'],physical_valid=row['physical_valid'],final_peak_m=float(peaks[-1]),last_preaction_peak_m=float(peaks[-2]),preactions_after_violation=len(bad),first_bad_preaction_index=int(bad[0]) if len(bad) else None,first_bad_preaction_time_s=float(times[bad[0]]) if len(bad) else None,crossing_transition_indices=cross.tolist(),terminal_only_violation=bool(peaks[-2]<=.0002<peaks[-1]),clock_max_abs_error_s=clock_error,sources=before,derived=ref(npz))
  assert before==[ref(a) for a in paths];cases.append(case)
 methods[m]=dict(cases=cases,total_actions=sum(c['actions'] for c in cases),episodes_with_penetration_violation=sum(c['final_peak_m']>.0002 for c in cases),episodes_with_known_preaction_violation=sum(c['preactions_after_violation']>0 for c in cases),terminal_only_violations=sum(c['terminal_only_violation'] for c in cases),task_true_strict_false=[c['condition'] for c in cases if c['task'] and not c['strict']])
write(D/'REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.time()-start,plan=ref(D/'PLAN.json'),episode_manifests=sources,methods=methods,new_physics_steps=0,new_optimizer_updates=0,new_network_forwards=0,replay_writes=0,limitations=plan['limitations']))
print({m:{k:v for k,v in x.items() if k!='cases'} for m,x in methods.items()})
