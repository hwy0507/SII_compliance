from pathlib import Path
import json,time,hashlib,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;R=B/'runs/parameter_partial75_recovery_cycle79_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261030_v7');os.sched_setaffinity(0,{7})
read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,j):
 with p.open('x') as f:f.write(json.dumps(j,indent=2)+'\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat');s=p.read_text().rsplit(')',1)[1].split() if p.exists() else None
 return s is not None and s[19]==j['proc_start_ticks'] and s[0]!='Z'
jobs=[]
for j in read(R/'LAUNCH.json')['jobs']:jobs.append(dict(identity=j,terminal=str(R/j['controller']/'train/FINISHED.json'),failures=[str(R/j['controller']/'train/FAILURE.json'),str(R/j['controller']/'DRIVER_FAILURE.json')]))
for root,launch,terminal,failures in [(R,'MONITOR_LAUNCH.json','ARCHIVE_REVIEW_FINISHED.json',['ARCHIVE_REVIEW_FAILURE.json']),(B/'runs/parameter_recovery79_loss_20261029_v1','LAUNCH.json','FINISHED.json',['FAILURE.json']),(B/'runs/parameter_recovery79_task_labels_20261029_v1','LAUNCH.json','FINISHED.json',['FAILURE.json']),(B/'runs/vmc_recovery79_terminal_followup_20261029_v1','LAUNCH.json','FINISHED.json',['FAILURE.json']),(B/'runs/admittance_recovery79_terminal_followup_20261029_v1','LAUNCH.json','FINISHED.json',['FAILURE.json']),(B/'runs/parameter_recovery79_81_reward_stability_20261030_v1','LAUNCH.json','REVIEW.json',['FAILURE.json']),(D,'LAUNCH.json','FINISHED.json',['FAILURE.json'])]:jobs.append(dict(identity=read(root/launch),terminal=str(root/terminal),failures=[str(root/x) for x in failures]))
g=read(G/'LAUNCH.json')
for pid in [g['pid']]+list(g['workers'].values()):
 start=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19];jobs.append(dict(identity=dict(pid=pid,proc_start_ticks=start),terminal=None,failures=[str(G/'FAILURE.json')]))
source_bindings={str(D/n):h for n,h in read(D/'REGISTRATION.json')['sources'].items()}
source_bindings[str(G/'guard.py')]=sha(G/'guard.py')
put(D/'OBSERVATION_PLAN.json',dict(time=time.time(),jobs=jobs,sources=source_bindings,samples=11,interval_s=30,scientific_restart=False))
start=time.monotonic();rows=[]
try:
 for i in range(11):
  row=dict(time=time.time(),identities=[],parameter={})
  for j in jobs:
   assert all(not Path(p).exists() for p in j['failures']),j
   status='live' if live(j['identity']) else ('terminal_receipt' if j['terminal'] and Path(j['terminal']).exists() else 'missing');assert status!='missing',j
   if status=='terminal_receipt':
    t=read(Path(j['terminal']));assert t.get('completed',t.get('passed',t.get('prepared',t.get('finished',False))))
   row['identities'].append(dict(pid=j['identity']['pid'],proc_start_ticks=j['identity']['proc_start_ticks'],status=status))
  for m in ['impedance','admittance','vmc']:row['parameter'][m]=read(R/m/'train/PROGRESS.json')
  guard=list(map(json.loads,(G/'samples.jsonl').read_text().splitlines()));assert time.time()-guard[-1]['time']<20;row['guard']=guard[-1];rows.append(row)
  with (D/'OBSERVATIONS.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  for p,h in source_bindings.items():assert sha(Path(p))==h
  if i<10:time.sleep(30)
 for m in rows[0]['parameter']:assert all(a['parameter'][m]['steps']<=z['parameter'][m]['steps'] for a,z in zip(rows,rows[1:]))
 put(D/'OBSERVATION_FINISHED.json',dict(passed=True,time=time.time(),elapsed=time.monotonic()-start,samples=len(rows),identities=len(jobs),all_original_identities_live_or_verified_terminal=True,first_steps={m:v['steps'] for m,v in rows[0]['parameter'].items()},last_steps={m:v['steps'] for m,v in rows[-1]['parameter'].items()},source_hashes_unchanged=True,scientific_restart=False))
except BaseException as e:put(D/'OBSERVATION_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
