from pathlib import Path
import json,time,os
O=Path(__file__).parent;B=O.parents[1];plan=json.loads((O/'PLAN.json').read_text());os.sched_setaffinity(0,{54});os.nice(15)
limit=time.monotonic()+plan['maximum_seconds'];events={};last={j['controller']:plan['time'] for j in plan['jobs']}
while time.monotonic()<limit:
 now=time.time()
 for j in plan['jobs']:
  m=j['controller'];p=Path(f"/proc/{j['pid']}/stat");s=p.read_text().rsplit(')',1)[1].split() if p.exists() else []
  alive=bool(s and s[0]!='Z' and s[19]==j['start_ticks'])
  if alive:last[m]=now
  elif m not in events:
   events[m]=dict(parent_pid=j['pid'],exit_observed_after=last[m],exit_observed_before=now)
   print(m,'exit observed',flush=True)
 launch=B/'runs/parameter_capacity_pool30_cycle44_20261026_v1/LAUNCH.json'
 if launch.exists():
  for j in json.loads(launch.read_text())['jobs']:
   m=j['controller']
   if m in events:
    events[m].update(new_pid=j['pid'],new_launch_time=j['time'],exit_to_spawn_seconds_lower=j['time']-events[m]['exit_observed_before'],exit_to_spawn_seconds_upper=j['time']-events[m]['exit_observed_after'])
  if len(events)==3 and all('new_pid' in x for x in events.values()):
   (O/'REVIEW.json').write_text(json.dumps(dict(passed=True,time=now,events=events,limitation='Process exit-to-next-spawn bounds only; not exact GPU idle time or guaranteed utilization',new_physics=0,optimizer_updates=0),indent=2)+'\n');break
 (O/'PROGRESS.json').write_text(json.dumps(dict(time=now,events=events),indent=2)+'\n');time.sleep(2)
else:(O/'TIMEOUT.json').write_text(json.dumps(dict(time=time.time(),events=events,reason='Finite observation expired; no restart or training'))+'\n')
