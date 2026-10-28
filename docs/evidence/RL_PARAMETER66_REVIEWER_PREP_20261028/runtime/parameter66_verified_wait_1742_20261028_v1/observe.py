from pathlib import Path
import json,time,subprocess,os
os.sched_setaffinity(0,{52})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=Path(__file__).parent;RUN=B/'runs/parameter_capacity_pool30_cycle66_20261026_v1'
def read(p):return json.loads(p.read_text())
def ident(pid,ticks):
 try:s=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
 except FileNotFoundError:return dict(pid=pid,expected_start=ticks,live=False)
 return dict(pid=pid,expected_start=ticks,actual_start=s[19],state=s[0],live=s[19]==ticks and s[0]!='Z')
jobs=read(RUN/'LAUNCH.json')['jobs'];watch=read(B/'runtime/parameter66_verified_snapshot_1716_20261028_v1/SNAPSHOT.json')['watchers']
watch['ranked66']={'pid':2077714,'expected_start':'40411411'}
start=time.time();deadline=time.monotonic()+1200;i=0
with (OUT/'SAMPLES.jsonl').open('x') as f:
 while True:
  rows=[]
  for j in jobs:
   p=RUN/j['controller']/'train';v=ident(j['pid'],j['proc_start_ticks']);v.update(controller=j['controller'],progress=read(p/'PROGRESS.json'),finished=read(p/'FINISHED.json') if (p/'FINISHED.json').exists() else None,failure=(p/'FAILURE.json').exists());rows.append(v)
  s=dict(index=i,time=time.time(),learners=rows,watchers={k:ident(v['pid'],v['expected_start']) for k,v in watch.items()},gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu','--format=csv,noheader'],text=True));f.write(json.dumps(s)+'\n');f.flush()
  print(json.dumps(dict(index=i,time=s['time'],steps=[v['progress']['steps'] for v in rows],learner_live=[v['live'] for v in rows],gpu=s['gpu'])),flush=True)
  assert all(not v['failure'] and (v['live'] or v['finished']) for v in rows),'Inspect original job; do not restart'
  assert all(v['live'] for k,v in s['watchers'].items() if k.startswith('guard'))
  ready=[B/'runtime/prepare_parameter67_20261028_v1/parameter_FINISHED.json',B/'runs/parameter66_loss_20261028_v1/FINISHED.json',B/'runs/vmc66_terminal_anchor_followup_20261028_v1/FINISHED.json',B/'runs/vmc66_ranked65_terminal_followup_20261028_v1/FINISHED.json',B/'runs/parameter_task_label_audit66_20261028_v1/FINISHED66.json']
  if all(v.exists() for v in ready) or time.monotonic()>=deadline:break
  i+=1;time.sleep(min(30,max(0,deadline-time.monotonic())))
(OUT/'FINISHED.json').write_text(json.dumps(dict(time=time.time(),start=start,samples=i+1,completed=True,science_restarted=False,scientific_completion=False),indent=2)+'\n')
