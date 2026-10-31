from pathlib import Path
import os,json,time,hashlib,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle99_20261031_v1'
read=lambda p:json.loads(p.read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def current(pid):
 s=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z';return s[19]
def check(j):assert current(j['pid'])==j.get('start',j.get('proc_start_ticks'))
def read_last_guard(path):
 with path.open('rb') as f:
  f.seek(0,2);end=f.tell();f.seek(max(0,end-65536));return json.loads(f.read().splitlines()[-1])
try:
 os.sched_setaffinity(0,{54});plan=read(D/'OBSERVATION_PLAN.json');assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==plan['source_sha256'];ids=[]
 for j in read(R/'LAUNCH.json')['jobs']:
  check(j);ids.append(dict(pid=j['pid'],start=current(j['pid'])))
  children=list(map(int,Path('/proc',str(j['pid']),'task',str(j['pid']),'children').read_text().split()));assert len(children)==30
  ids.extend(dict(pid=pid,start=current(pid)) for pid in children)
 for p in [R/'MONITOR_LAUNCH.json',B/'runs/census99_fixed98_terminal_20261031_v1/PROCESS.json',B/'runtime/census99_prefix_comparison_20261031_v1/PROCESS.json',B/'runs/census99_new_terminal_diagnosis_20261031_v1/LAUNCH.json',B/'runtime/census99_completion_20261031_v1/PROCESS.json']:
  j=read(p);check(j);ids.append(dict(pid=j['pid'],start=current(j['pid'])))
 g=read(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');assert not (Path(g['root'])/'STOP').exists()
 for j in g['identities']:check(j);ids.append(j)
 assert len(ids)==103;methods=['impedance','admittance','vmc'];first={m:read(R/m/'train/PROGRESS.json')['steps'] for m in methods};start=time.monotonic();rows=[]
 with (D/'ONLINE_OBSERVATIONS.jsonl').open('x') as f:
  while True:
   for j in ids:check(j)
   assert not (Path(g['root'])/'STOP').exists()
   steps={m:read(R/m/'train/PROGRESS.json')['steps'] for m in methods}
   for m in methods:assert not (R/m/'train/FAILURE.json').exists() and not (R/m/'DRIVER_FAILURE.json').exists()
   assert not list((B/'runtime/census99_completion_20261031_v1').glob('WAIT_FAILURE*')) and not (R/'ARCHIVE_REVIEW_FAILURE.json').exists() and not list((B/'runtime/census99_prefix_comparison_20261031_v1').glob('COMPARISON_FAILURE*')) and not list((B/'runs/census99_new_terminal_diagnosis_20261031_v1').glob('*FAILURE*')) and not list((B/'runs/census99_fixed98_terminal_20261031_v1').glob('*FAILURE*'))
   sample=read_last_guard(Path(g['root'])/'samples.jsonl');assert time.time()-sample['time']<30;util=[v['utilization'] for v in sample['gpus']];assert len(util)==4 and min(util)>=50
   row=dict(time=time.time(),elapsed=time.monotonic()-start,steps=steps,identity_count=len(ids),gpu=util);rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
   if time.monotonic()-start>=plan['duration_seconds']:break
   time.sleep(plan['interval_seconds'])
 assert all(steps[m]>first[m] for m in methods)
 put(D/'ONLINE_OBSERVATION_REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,first_steps=first,last_steps=steps,identities=ids,identity_count=len(ids),samples=len(rows),convergence_claim=False))
 print('Verified observation passed',len(ids),first,steps,flush=True)
except BaseException:put(D/'OBSERVATION_FAILURE.json',dict(time=time.time(),traceback=traceback.format_exc()));raise
