from pathlib import Path
import json,time,subprocess,hashlib,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
O=B/'runtime/parameter71_verified_wait_2244_20261028_v1';O.mkdir(exist_ok=False)
os.sched_setaffinity(0,{54})
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
snap=read(B/'runtime/parameter71_presave_snapshot_20261028_v1/SNAPSHOT.json')
jobs=[*snap['learners'],snap['archive_monitor'],*snap['waiters'].values(),*snap['guard_processes']]
start=time.time();registration=dict(time=start,seconds=180,interval_seconds=30,jobs=jobs,source_sha256=sha(Path(__file__)),automatic_training=False,scientific_restart=False)
write(O/'REGISTRATION.json',registration)
ticks=Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()[19]
write(O/'LAUNCH.json',dict(pid=os.getpid(),proc_start_ticks=ticks,registration_sha256=sha(O/'REGISTRATION.json')))
rows=[]
try:
 for i in range(7):
  if i:time.sleep(max(0,start+i*30-time.time()))
  row=dict(time=time.time(),identities=[],progress={})
  for j in jobs:
   p=Path(f'/proc/{j["pid"]}/stat');f=p.read_text().rsplit(')',1)[1].split() if p.exists() else None
   live=f is not None and f[19]==j['proc_start_ticks'] and f[0]!='Z'
   row['identities'].append(dict(pid=j['pid'],proc_start_ticks=j['proc_start_ticks'],live=live,state=f[0] if f else None))
  root=B/'runs/parameter_capacity_pool30_cycle71_20261026_v1'
  for m in ['impedance','admittance','vmc']:
   p=root/m/'train';row['progress'][m]=read(p/'PROGRESS.json');assert not (p/'FAILURE.json').exists()
  row['archive_finished']=(root/'ARCHIVE_REVIEW_FINISHED.json').exists()
  assert not (root/'ARCHIVE_REVIEW_FAILURE.json').exists()
  row['gpus']=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
  with (O/'SAMPLES.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  rows.append(row)
  if not all(x['live'] for x in row['identities']):
   write(O/'BOUNDARY_REQUIRES_INSPECTION.json',dict(time=time.time(),sample=row,note='Handle changed or terminal; inspect original outputs, do not restart science.'));break
 write(O/'FINISHED.json',dict(time=time.time(),samples=len(rows),all_original_identities_live=all(x['live'] for r in rows for x in r['identities']),first_steps={m:p['steps'] for m,p in rows[0]['progress'].items()},last_steps={m:p['steps'] for m,p in rows[-1]['progress'].items()},elapsed=time.time()-start,observation_only=True,scientific_restart=False))
 print(json.dumps(read(O/'FINISHED.json'),indent=2))
except BaseException as e:
 write(O/'FAILURE.json',dict(time=time.time(),error=repr(e),scientific_restart=False));raise
