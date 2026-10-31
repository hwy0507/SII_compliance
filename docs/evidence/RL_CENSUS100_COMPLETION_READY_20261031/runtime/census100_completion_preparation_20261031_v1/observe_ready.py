from pathlib import Path
import json,time,os,traceback,hashlib
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle100_20261031_v1';rd=lambda p:json.loads(p.read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def check(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
def steps():return {m:rd(R/m/'train/PROGRESS.json')['steps'] for m in ['impedance','admittance','vmc']}
p=rd(D/'OBSERVATION_PLAN.json');assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==p['source_sha256'];os.sched_setaffinity(0,{9});start=time.monotonic();first=steps();count=0
try:
 with (D/'OBSERVATIONS.jsonl').open('x') as f:
  while True:
   for j in p['identities']:check(j)
   assert not list(R.rglob('*FAILURE*'))
   for root,pattern in [(B/'runtime/census100_completion_20261031_v1','WAIT_FAILURE*'),(B/'runs/census100_new_terminal_diagnosis_20261031_v1','WAIT_FAILURE*')]:assert not list(root.glob(pattern))
   g=Path('/tmp/sii_gpu_util_guard_20261031_recovery_v1');assert not (g/'STOP').exists() and not (g/'FAILURE.json').exists()
   row=dict(time=time.time(),elapsed_s=time.monotonic()-start,steps=steps(),identity_count=len(p['identities']));f.write(json.dumps(row)+'\n');f.flush();count+=1
   if row['elapsed_s']>=p['seconds']:break
   time.sleep(p['interval'])
 assert all(row['steps'][m]>first[m] for m in first)
 put(D/'OBSERVATION_REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,first_steps=first,last_steps=row['steps'],samples=count,identity_count=len(p['identities']),no_restarts=True,scope='Finite observation of original science and two newly registered read-only waiters. No convergence claim or automatic101.'))
 print('103 original/new consumer identities stable; training steps grew',flush=True)
except BaseException:
 put(D/'OBSERVATION_FAILURE.json',dict(time=time.time(),traceback=traceback.format_exc()));raise
