from pathlib import Path
import json,time,hashlib,os,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=B/'runtime/prepare_recovery77_20261029_v1';O=B/'runtime/recovery77_verified_wait_0705_20261029_v1';O.mkdir(exist_ok=False);R=B/'runs/parameter_partial75_recovery_cycle77_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6')
os.sched_setaffinity(0,{54})
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def identity(j):
 p=Path(f'/proc/{j["pid"]}/stat');f=p.read_text().rsplit(')',1)[1].split() if p.exists() else None
 return dict(pid=j['pid'],proc_start_ticks=j['proc_start_ticks'],live=f is not None and f[19]==j['proc_start_ticks'] and f[0]!='Z',state=f[0] if f else None)
jobs=read(R/'LAUNCH.json')['jobs']+[read(R/'MONITOR_LAUNCH.json')]
for n in ['parameter_recovery77_loss_20261029_v1','parameter_recovery76_78_reward_stability_20261029_v1','parameter_recovery77_task_labels_20261029_v1','vmc_recovery77_terminal_followup_20261029_v1','admittance_recovery77_terminal_followup_20261029_v1']:jobs.append(read(B/'runs'/n/'LAUNCH.json'))
g=read(G/'LAUNCH.json')
for pid in [g['pid'],*g['workers'].values()]:
 f=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();jobs.append(dict(pid=pid,proc_start_ticks=f[19]))
assert all(identity(j)['live'] for j in jobs)
start=time.time();write(O/'REGISTRATION.json',dict(time=start,seconds=300,interval_seconds=30,jobs=jobs,source=dict(path=str(Path(__file__)),sha256=sha(Path(__file__))),automatic_training=False,scientific_restart=False));write(O/'LAUNCH.json',dict(pid=os.getpid(),proc_start_ticks=Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()[19],registration_sha256=sha(O/'REGISTRATION.json')))
rows=[]
try:
 for i in range(11):
  if i:time.sleep(max(0,start+30*i-time.time()))
  row=dict(time=time.time(),identities=[identity(j) for j in jobs],progress={})
  for m in ['impedance','admittance','vmc']:
   p=R/m/'train';assert not (p/'FAILURE.json').exists();row['progress'][m]=read(p/'PROGRESS.json')
  assert not (R/'ARCHIVE_REVIEW_FAILURE.json').exists() and not (G/'FAILURE.json').exists()
  latest=json.loads((G/'samples.jsonl').read_text().splitlines()[-1]);row['guard_sample_age']=time.time()-latest['time'];assert row['guard_sample_age']<15;row['guard_sample']=latest;row['archive_finished']=(R/'ARCHIVE_REVIEW_FINISHED.json').exists()
  with (O/'SAMPLES.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  rows.append(row)
  if not all(x['live'] for x in row['identities']):write(O/'BOUNDARY_REQUIRES_INSPECTION.json',row);break
 write(O/'FINISHED.json',dict(time=time.time(),samples=len(rows),elapsed=time.time()-start,all_original_identities_live=all(x['live'] for r in rows for x in r['identities']),first_steps={m:x['steps'] for m,x in rows[0]['progress'].items()},last_steps={m:x['steps'] for m,x in rows[-1]['progress'].items()},scientific_restart=False,observation_only=True));print(json.dumps(read(O/'FINISHED.json')))
except BaseException as e:write(O/'FAILURE.json',dict(time=time.time(),error=repr(e)));raise
