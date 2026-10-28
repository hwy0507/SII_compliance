from pathlib import Path
import json,time,subprocess,os
os.sched_setaffinity(0,{52})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=Path(__file__).parent;RUN=B/'runs/parameter_capacity_pool30_cycle64_20261026_v1'
def read(p):return json.loads(p.read_text())
def identity(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 try:s=p.read_text().rsplit(')',1)[1].split()
 except FileNotFoundError:return dict(pid=j['pid'],expected_start=j['proc_start_ticks'],live=False)
 return dict(pid=j['pid'],expected_start=j['proc_start_ticks'],actual_start=s[19],state=s[0],live=s[19]==j['proc_start_ticks'] and s[0]!='Z')
jobs=read(RUN/'LAUNCH.json')['jobs']
watchers={name:read(p) for name,p in [('archive',RUN/'MONITOR_LAUNCH.json'),('loss',B/'runs/parameter64_loss_20261028_v1/LAUNCH.json'),('terminal',B/'runs/vmc64_terminal_anchor_followup_20261028_v1/LAUNCH.json'),('labels',B/'runs/parameter_task_label_audit64_20261028_v1/LAUNCH64.json'),('ranked',B/'runs/vmc64_ranked63_terminal_followup_20261028_v1/LAUNCH.json'),('restore',B/'runtime/prepare_parameter65_20261028_v1/parameter_LAUNCH.json'),('window',B/'runs/parameter_capacity62_64_reward_stability_20261028_v1/LAUNCH.json')]}
for n,p,t in [('guard',3256866,'37410686'),('guard0',3256867,'37410690'),('guard1',3256868,'37410690'),('guard2',3256869,'37410691'),('guard3',3256870,'37410693')]:watchers[n]=dict(pid=p,proc_start_ticks=t)
required=[RUN/'ARCHIVE_REVIEW_FINISHED.json',B/'runs/parameter64_loss_20261028_v1/FINISHED.json',B/'runs/vmc64_terminal_anchor_followup_20261028_v1/FINISHED.json',B/'runs/parameter_task_label_audit64_20261028_v1/FINISHED64.json',B/'runs/vmc64_ranked63_terminal_followup_20261028_v1/FINISHED.json',B/'runtime/prepare_parameter65_20261028_v1/parameter_FINISHED.json',B/'runs/parameter_capacity62_64_reward_stability_20261028_v1/REVIEW.json']
failures=[RUN/'ARCHIVE_REVIEW_FAILURE.json',*[RUN/j['controller']/'train/FAILURE.json' for j in jobs],B/'runs/parameter64_loss_20261028_v1/FAILURE.json',B/'runs/vmc64_terminal_anchor_followup_20261028_v1/WAIT_FAILURE.json',B/'runs/parameter_task_label_audit64_20261028_v1/WAIT64_FAILURE.json',B/'runs/vmc64_ranked63_terminal_followup_20261028_v1/WAIT_FAILURE.json',B/'runtime/prepare_parameter65_20261028_v1/parameter_FAILURE.json',B/'runs/parameter_capacity62_64_reward_stability_20261028_v1/WAIT_FAILURE.json',B/'runs/parameter_capacity62_64_reward_stability_20261028_v1/FAILURE.json']
deadline=time.monotonic()+1800;i=0
with (OUT/'SAMPLES.jsonl').open('x') as f:
 while True:
  learners=[]
  for j in jobs:
   p=RUN/j['controller']/'train';v=identity(j);v.update(controller=j['controller'],progress=read(p/'PROGRESS.json'),finished=read(p/'FINISHED.json') if (p/'FINISHED.json').exists() else None);learners.append(v)
  missing=[str(p) for p in required if not p.exists()];bad=[str(p) for p in failures if p.exists()]
  s=dict(index=i,time=time.time(),learners=learners,watchers={k:identity(j) for k,j in watchers.items()},missing=missing,failures=bad,gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu','--format=csv,noheader'],text=True));f.write(json.dumps(s)+'\n');f.flush()
  print(json.dumps(dict(index=i,time=s['time'],steps=[x['progress']['steps'] for x in learners],learner_live=[x['live'] for x in learners],missing=len(missing),failures=bad,gpu=s['gpu'])),flush=True)
  assert not bad,bad
  assert all(x['live'] or x['finished'] for x in learners),'Learner absent without FINISHED; inspect, do not restart'
  assert all(v['live'] for k,v in s['watchers'].items() if k.startswith('guard'))
  if not missing:break
  assert time.monotonic()<deadline,'Finite1800s observer expired; do not restart science'
  i+=1;time.sleep(30)
(OUT/'OBSERVATION_READY.json').write_text(json.dumps(dict(time=time.time(),all_required_paths_present=True,observer_finished=True,science_restarted=False,scientific_review_still_required=True),indent=2)+'\n')
