from pathlib import Path
import os,json,time,hashlib,traceback
D=Path(__file__).parent;B=D.parents[1];R=B/'runs/parameter_census_cycle96_20261031_v1'
read=lambda p:json.loads(p.read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def identity(pid):
 f=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();assert f[0]!='Z';return dict(pid=pid,start=f[19])
def check(j):assert identity(j['pid'])['start']==j.get('start',j.get('proc_start_ticks'))
plan=read(D/'OBSERVATION_PLAN.json');assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==plan['source_sha256'];os.sched_setaffinity(0,{54});jobs=read(R/'LAUNCH.json')['jobs'];monitor=read(D/'ARCHIVE_REPAIR_LAUNCH.json');startup=read(D/'STARTUP_REPAIR_LAUNCH.json');deadline=time.monotonic()+plan['startup_wait_seconds']
try:
 while not (R/'startup_repaired/REVIEW.json').exists():
  for j in jobs+[monitor,startup]:check(j)
  for m in ['impedance','admittance','vmc']:
   assert not (R/m/'DRIVER_FAILURE.json').exists() and not (R/m/'train/FAILURE.json').exists()
  assert time.monotonic()<deadline;time.sleep(5)
 assert read(R/'startup_repaired/REVIEW.json')['passed'];ids=[identity(j['pid']) for j in jobs+[monitor]]
 for j in jobs:
  children=list(map(int,Path(f'/proc/{j["pid"]}/task/{j["pid"]}/children').read_text().split()));assert len(children)==30
  ids.extend(identity(pid) for pid in children)
 for j in read(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json')['identities']:
  actual=identity(j['pid']);assert actual['start']==j['start'];ids.append(actual)
 first={m:read(R/m/'train/PROGRESS.json')['steps'] for m in ['impedance','admittance','vmc']};start=time.monotonic();rows=[]
 with (D/'ONLINE_OBSERVATIONS.jsonl').open('x') as f:
  while True:
   for j in ids:check(j)
   steps={m:read(R/m/'train/PROGRESS.json')['steps'] for m in first}
   for m in first:assert not (R/m/'train/FAILURE.json').exists()
   row=dict(time=time.time(),elapsed=time.monotonic()-start,steps=steps,identity_count=len(ids));rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
   if time.monotonic()-start>=plan['observe_seconds']:break
   time.sleep(plan['interval_seconds'])
 assert all(steps[m]>first[m] for m in first)
 put(D/'ONLINE_OBSERVATION_REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,first_steps=first,last_steps=steps,identity_count=len(ids),identities=ids,samples=len(rows),startup_review_sha256=hashlib.sha256((R/'startup_repaired/REVIEW.json').read_bytes()).hexdigest(),convergence_claim=False))
except BaseException as e:put(D/'OBSERVATION_FAILURE.json',dict(error=repr(e),traceback=traceback.format_exc()));raise
