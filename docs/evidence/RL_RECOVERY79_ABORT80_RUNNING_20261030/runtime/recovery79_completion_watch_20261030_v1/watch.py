from pathlib import Path
import os,json,time,hashlib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;R=B/'runs/parameter_partial75_recovery_cycle79_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261030_v7');os.sched_setaffinity(0,{7})
read=lambda p:json.loads(Path(p).read_text())
def put(p,j):
 with p.open('x') as f:f.write(json.dumps(j,indent=2)+'\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat');s=p.read_text().rsplit(')',1)[1].split() if p.exists() else None
 return s is not None and s[19]==j.get('proc_start_ticks',j.get('start')) and s[0]!='Z'
jobs=[]
for j in read(R/'LAUNCH.json')['jobs']:jobs.append(dict(name=j['controller'],identity=j,terminal=str(R/j['controller']/'train/FINISHED.json'),failures=[str(R/j['controller']/'train/FAILURE.json'),str(R/j['controller']/'DRIVER_FAILURE.json')]))
for name,root,launch,terminal,failure in [('archive',R,'MONITOR_LAUNCH.json','ARCHIVE_REVIEW_FINISHED.json','ARCHIVE_REVIEW_FAILURE.json'),('loss',B/'runs/parameter_recovery79_loss_20261029_v1','LAUNCH.json','SAVED_REVIEW.json','FAILURE.json'),('labels',B/'runs/parameter_recovery79_task_labels_20261029_v1','LAUNCH.json','FINISHED.json','FAILURE.json'),('vmc_terminal',B/'runs/vmc_recovery79_terminal_followup_20261029_v1','LAUNCH.json','FINISHED.json','FAILURE.json'),('admittance_terminal',B/'runs/admittance_recovery79_terminal_followup_20261029_v1','LAUNCH.json','FINISHED.json','FAILURE.json'),('restore80',B/'runtime/prepare_recovery80_20261029_v1','LAUNCH.json','FINISHED.json','FAILURE.json')]:jobs.append(dict(name=name,identity=read(root/launch),terminal=str(root/terminal),failures=[str(root/failure)]))
put(D/'PLAN.json',dict(time=time.time(),jobs=jobs,deadline_s=3600,interval_s=30,new_physics=0,new_updates=0,automatic_scientific_restart=False));start=time.monotonic();count=0
try:
 while True:
  row=dict(time=time.time(),jobs=[],progress={})
  for j in jobs:
   assert all(not Path(p).exists() for p in j['failures']),j
   done=Path(j['terminal']).exists();alive=live(j['identity']);assert done or alive,j
   if done:
    result=read(j['terminal']);assert result.get('passed',result.get('completed',result.get('prepared',result.get('status')=='stopped_at_complete_cycle'))),j
   row['jobs'].append(dict(name=j['name'],pid=j['identity']['pid'],live=alive,terminal=done))
  for m in ['impedance','admittance','vmc']:row['progress'][m]=read(R/m/'train/PROGRESS.json')
  gs=list(map(json.loads,(G/'samples.jsonl').read_text().splitlines()));assert time.time()-gs[-1]['time']<20;row['guard']=gs[-1];count+=1
  with (D/'OBSERVATIONS.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  (D/'PROGRESS.json').write_text(json.dumps(row,indent=2)+'\n')
  print(json.dumps(dict(sample=count,elapsed=time.monotonic()-start,steps={m:v['steps'] for m,v in row['progress'].items()},completed={m:v['completed_conditions'] for m,v in row['progress'].items()},ready=[x['name'] for x in row['jobs'] if x['terminal']],gpu=[g['utilization'] for g in row['guard']['gpus']])),flush=True)
  if all(x['terminal'] for x in row['jobs']):break
  assert time.monotonic()-start<3600,'Observation expired; preserve science and inspect same identities, never automatic restart'
  time.sleep(30)
 put(D/'FINISHED.json',dict(passed=True,time=time.time(),elapsed=time.monotonic()-start,samples=count,complete79_and_restore80_ready=True,new_physics=0,new_updates=0,automatic_training=False))
except BaseException as e:put(D/'FAILURE.json',dict(time=time.time(),error=repr(e)));raise
