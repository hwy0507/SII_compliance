from pathlib import Path
import json,time,os,hashlib,socket
os.sched_setaffinity(0,{54})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;RUN=B/'runs/parameter_partial75_recovery_cycle77_20261029_v1';P=B/'runtime/prepare_recovery78_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6')
read=lambda p:json.loads(p.read_text())
def write(p,x):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat');f=p.read_text().rsplit(')',1)[1].split() if p.exists() else None;return f is not None and f[19]==j['proc_start_ticks'] and f[0]!='Z'
folders=[B/'runs'/n for n in ['parameter_recovery77_loss_20261029_v1','parameter_recovery77_task_labels_20261029_v1','vmc_recovery77_terminal_followup_20261029_v1','admittance_recovery77_terminal_followup_20261029_v1']]
expected=[(RUN/'ARCHIVE_REVIEW_FINISHED.json','completed'),(B/'runs/parameter_partial75_recovery_cycle77_review_20261029_v1/FINISHED.json','completed'),(folders[0]/'SAVED_REVIEW.json','passed'),(folders[1]/'FINISHED.json','completed'),(folders[2]/'FINISHED.json','completed'),(folders[3]/'FINISHED.json','completed'),(P/'FINISHED.json','prepared'),(B/'runs/parameter_partial75_recovery_cycle78_20261029_v1/CHECK_ONLY_COMPLETE.json','passed')]
jobs=read(RUN/'LAUNCH.json')['jobs'];others=[(read(RUN/'MONITOR_LAUNCH.json'),RUN/'ARCHIVE_REVIEW_FINISHED.json')]+[(read(p/'LAUNCH.json'),p/('SAVED_REVIEW.json' if p==folders[0] else 'FINISHED.json')) for p in folders]+[(read(P/'LAUNCH.json'),P/'FINISHED.json')]
assert all(live(j) for j in jobs) and all(live(j) for j,p in others)
start=time.time();deadline=time.monotonic()+1200
write(D/'REGISTRATION.json',dict(time=start,seconds=1200,interval_seconds=10,jobs=jobs,other_jobs=[dict(identity=j,completion_file=str(p)) for j,p in others],expected=[dict(path=str(p),key=k) for p,k in expected],source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),automatic_training=False,scientific_restart=False))
write(D/'LAUNCH.json',dict(pid=os.getpid(),proc_start_ticks=Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()[19],host=socket.gethostname(),time=time.time()))
try:
 while True:
  row=dict(time=time.time(),methods={},complete={},other_live={})
  for j in jobs:
   p=RUN/j['controller']/'train';assert not (p/'FAILURE.json').exists() and not (p.parent/'DRIVER_FAILURE.json').exists();alive=live(j);finished=read(p/'FINISHED.json') if (p/'FINISHED.json').exists() else None
   if not alive:assert finished and finished['status']=='stopped_at_complete_cycle'
   row['methods'][j['controller']]=dict(live=alive,finished=finished,progress=read(p/'PROGRESS.json'))
  assert not (RUN/'ARCHIVE_REVIEW_FAILURE.json').exists()
  for p in folders+[P]:assert not (p/'FAILURE.json').exists() and not (p/'WAIT_FAILURE.json').exists()
  for j,p in others:
   alive=live(j);row['other_live'][str(j['pid'])]=alive
   if not alive:assert p.exists(),f'Observer requires inspection: {j} without {p}'
  for p,k in expected:row['complete'][str(p.relative_to(B))]=p.exists() and bool(read(p)[k])
  g=read(G/'LAUNCH.json');assert Path(f'/proc/{g["pid"]}/stat').exists() and not (G/'FAILURE.json').exists();sample=json.loads((G/'samples.jsonl').read_text().splitlines()[-1]);assert time.time()-sample['time']<15;row['guard']=sample
  with (D/'SAMPLES.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  write(D/'LATEST.json',row)
  if all(row['complete'].values()):write(D/'FINISHED.json',dict(time=time.time(),completed=True,elapsed=time.time()-start,all_expected_saved_results_present=True,new_physics=0,optimizer_updates=0));break
  if time.monotonic()>=deadline:write(D/'OBSERVATION_EXPIRED.json',dict(time=time.time(),elapsed=time.time()-start,scientific_restart=False));break
  time.sleep(10)
except BaseException as e:write(D/'FAILURE.json',dict(time=time.time(),error=repr(e),scientific_restart=False));raise
