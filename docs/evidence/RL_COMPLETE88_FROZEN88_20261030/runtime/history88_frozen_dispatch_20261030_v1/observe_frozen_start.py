from pathlib import Path
import json,os,time,hashlib
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter88_history_frozen_full30_20261030_v1';P=B/'runtime/history88_frozen_postprocess_20261030_v1'
os.sched_setaffinity(0,{10});read=lambda p:json.loads(p.read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def live(j):
 f=Path(f"/proc/{j['pid']}/stat").read_text().rsplit(')',1)[1].split();assert f[0]!='Z' and f[19]==str(j['start'])
jobs=read(R/'LAUNCH.json')['jobs'];watchers=[read(R/'REVIEW_LAUNCH.json'),read(P/'PROCESS.json')];start=time.time()
put(D/'FROZEN_OBSERVATION_PLAN.json',dict(time=start,maximum_startup_wait_seconds=600,live_observation_seconds=90,jobs=jobs,watchers=watchers,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
while not all((R/j['controller']/'CURRENT_PHYSICS.json').exists() for j in jobs):
 assert time.time()-start<600
 for j in jobs:live(j);assert not (R/j['controller']/'FAILURE.json').exists()
 for j in watchers:live(j)
 time.sleep(3)
rows=[];observed=time.time()
for i in range(10):
 methods={}
 for j in jobs:
  live(j);m=j['controller'];folder=R/m;assert not (folder/'FAILURE.json').exists();startup=read(folder/'STARTUP_REVIEW.json');assert startup['passed'] and startup['validated_parent_cycle']==88
  reg=read(folder/'REGISTRATION.json');assert startup['checkpoint_sha256']==reg['checkpoint_sha256']
  current=read(folder/'CURRENT_PHYSICS.json');pid=current['pid'];fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();assert fields[0]!='Z' and os.sched_getaffinity(pid)=={reg['cpu']}
  methods[m]=dict(current_physics=current,physics_start_ticks=fields[19],progress=read(folder/'PROGRESS.json') if (folder/'PROGRESS.json').exists() else None)
 for j in watchers:live(j)
 rows.append(dict(time=time.time(),methods=methods))
 with (D/'FROZEN_OBSERVATIONS.jsonl').open('a') as f:f.write(json.dumps(rows[-1])+'\n')
 if i<9:time.sleep(10)
assert all(rows[-1]['methods'][j['controller']]['progress'] is not None for j in jobs)
put(D/'FROZEN_OBSERVATION_REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.time()-observed,samples=len(rows),original_evaluator_and_watcher_identities_held=True,physics_cpu_affinity_verified=True,actual_physics_progress=True,full90_and_final_invariance_still_pending=True))
print(json.dumps(rows[-1]),flush=True)
