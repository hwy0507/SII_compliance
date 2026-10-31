from pathlib import Path
import json,time,hashlib,traceback,os
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle94_20261031_v1';V=B/'runs/parameter_census_cycle94_review_20261031_v1';T=B/'runs/census94_fixed93_terminal_20261031_v1';C=B/'runtime/census94_comparison_20261031_v1'
read=lambda p:json.loads(Path(p).read_text())
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def identity(j):
 try:
  s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();return s[0]!='Z' and s[19]==str(j.get('start',j.get('proc_start_ticks')))
 except FileNotFoundError:return False
try:
 os.sched_setaffinity(0,{54});plan=read(D/'WATCH_PLAN.json');assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==plan['source_sha256'];jobs=read(R/'LAUNCH.json')['jobs'];guard=read(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');started=time.monotonic();rows=[]
 tasks={j['controller']:(j,R/j['controller']/'train/FINISHED.json') for j in jobs};tasks.update(archive=(read(R/'MONITOR_LAUNCH.json'),V/'FINISHED.json'),terminal_compare=(read(T/'LAUNCH.json'),T/'FINISHED.json'),training_compare=(read(C/'PROCESS.json'),C/'COMPARISON_FINISHED.json'))
 for name,(j,p) in tasks.items():assert identity(j),name
 for j in guard['identities']:assert identity(j)
 put(D/'WATCH_IDENTITIES.json',dict(time=time.time(),tasks={k:dict(identity=j,completion=str(p)) for k,(j,p) in tasks.items()},guard=guard))
 with (D/'OBSERVATIONS.jsonl').open('x') as f:
  while True:
   assert all(identity(j) for j in guard['identities']) and not (Path(guard['root'])/'STOP').exists()
   assert not list(R.rglob('*FAILURE.json')) and not list(T.glob('*FAILURE*')) and not list(C.glob('*FAILURE*'))
   state={}
   for name,(j,p) in tasks.items():
    active=identity(j);complete=p.exists()
    if not(active or complete):
     time.sleep(2);active=identity(j);complete=p.exists()
    assert active or complete,name+' missing identity and completion'
    state[name]=dict(live=active,completion_present=complete)
   progress={m:read(R/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
   row=dict(time=time.time(),elapsed_s=time.monotonic()-started,tasks=state,progress=progress);rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
   if all(x['completion_present'] for x in state.values()):reason='all_existing_training_and_consumers_finished';break
   if time.monotonic()-started>=plan['maximum_observe_seconds']:reason='finite_observation_budget_reached_existing_jobs_left_running';break
   assert time.time()<plan['original_archive_deadline'];time.sleep(plan['interval_seconds'])
 put(D/'WATCH_REVIEW.json',dict(passed=True,time=time.time(),reason=reason,samples=len(rows),elapsed_s=time.monotonic()-started,first=rows[0],last=rows[-1],identities=read(D/'WATCH_IDENTITIES.json'),convergence_claim=False,automatic95=False))
except BaseException as e:put(D/'WATCH_FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
