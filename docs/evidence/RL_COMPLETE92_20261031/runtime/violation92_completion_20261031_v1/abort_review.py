from pathlib import Path
import json,hashlib,math,time
D=Path(__file__).resolve().parent;B=D.parents[1];T=B/'runs/parameter_violation_cycle92_20261030_v1/impedance/train';C=T/'cycle_00092/active_long_train_0000';P=B/'runs/parameter_violation_cycle91_20261030_v1/impedance/train/cycle_00091/active_long_train_0000/rollout.json'
read=lambda p:json.loads(p.read_text())
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
x=read(C/'rollout.json');term=read(C/'TERMINAL.json');old=read(P)
intervals=[json.loads(s) for s in (C/'actor_intervals.jsonl').read_text().splitlines()]
rows=[]
with (T/'transitions.jsonl').open() as f:
 for line in f:
  if not line.endswith('\n'):break
  r=json.loads(line)
  if r['condition']=='active_long_train_0000':rows.append(r)
episodes=[json.loads(s) for s in (T/'episodes.jsonl').read_text().splitlines() if s.endswith('}')];episode=[r for r in episodes if r['condition']=='active_long_train_0000'];assert len(episode)==1;episode=episode[0]
assert len(rows)==len(intervals)==episode['steps']==x['baseline_policy']['actions']==687
assert all(r['cycle']==92 for r in rows) and sum(r['done'] for r in rows)==1 and rows[-1]['done']
assert not x['task_success'] and not x['strict_success'] and not x['full_task_horizon_completed'] and not x['physical_valid']
assert x['abort_reason']==term['result']['abort_reason']==episode['abort_reason']=='global_penetration_exceeded_2mm'
assert math.isclose(math.fsum(r['reward'] for r in rows),episode['reward'],abs_tol=1e-10)
assert math.isclose(term['terminal_time_s'],687*.04,abs_tol=1e-8)
assert x['model_sha256']==term['model_sha256']==episode['model_sha256']==old['model_sha256']
current=intervals[-1]['interval']['external_penetration_peak_m'];nxt=term['interval']['external_penetration_peak_m'];assert current<=.0002 and nxt<=.0002 and x['stats']['max_penetration_m']>.002
put(D/'ABORT_TRANSITIONS.json',dict(source=str(T/'transitions.jsonl'),condition='active_long_train_0000',rows=rows,scope='Complete ended condition extracted from still-growing cycle journal; original file not modified.'))
put(D/'ABORT_EPISODE.json',dict(source=str(T/'episodes.jsonl'),episode=episode))
put(D/'ABORT_REVIEW.json',dict(passed=True,time=time.time(),method='impedance',condition=episode['condition'],cycle=92,actual_actions=len(rows),terminal_time_s=term['terminal_time_s'],reward=episode['reward'],task=False,strict=False,abort=x['abort_reason'],global_peak_penetration_mm=x['stats']['max_penetration_m']*1000,worst_global_pair=x['stats']['worst_pair'],external_peak_penetration_mm=x['stats']['max_external_penetration_m']*1000,worst_external_pair=x['stats']['worst_external_pair'],last_current_and_terminal_raw_external_bit=[float(current>.0002),float(nxt>.0002)],prior91={k:old[k] for k in ['task_success','strict_success','abort_reason','full_task_horizon_completed']},prior91_global_peak_mm=old['stats']['max_penetration_m']*1000,sources=[ref(p) for p in [C/'rollout.json',C/'TERMINAL.json',C/'actor_intervals.jsonl',P,D/'ABORT_TRANSITIONS.json',D/'ABORT_EPISODE.json']],new_physics=0,optimizer_updates=0,scope='Saved completed-condition/raw journal arithmetic; no checkpoint replay claim, independent dynamics or causal attribution. Global target/corner failure is distinct from external bit. Preserve actual shortened episode and original gates.'))
print(json.dumps(read(D/'ABORT_REVIEW.json'),indent=2))
