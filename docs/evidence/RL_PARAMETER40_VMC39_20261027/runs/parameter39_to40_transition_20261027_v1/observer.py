from pathlib import Path
import json,time,os
os.sched_setaffinity(0,{54})
o=Path(__file__).parent
reg=json.loads((o/'REGISTRATION.json').read_text());limit=time.monotonic()+900;last={p:reg['time'] for p,v in reg['parent_pids'].items() if v['live']};exits={p:dict(exit_before=reg['time'],exit_after=None) for p,v in reg['parent_pids'].items() if not v['live']}
while time.monotonic()<limit:
 now=time.time()
 for p in reg['parent_pids']:
  if p in exits:continue
  if Path('/proc/'+p).exists():last[p]=now
  else:exits[p]=dict(exit_after=last[p],exit_before=now)
 launch=Path(reg['next_run'])/'LAUNCH.json'
 result=dict(time=now,parent_exits=exits,launch=json.loads(launch.read_text()) if launch.exists() else None,scope='Process exit brackets to next learner spawn; not all GPU idle duration')
 (o/'STATUS.json').write_text(json.dumps(result,indent=2)+'\n')
 if len(exits)==3 and launch.exists():
  (o/'FINISHED.json').write_text(json.dumps(dict(completed=True,time=now))+'\n');break
 time.sleep(2)
else:raise TimeoutError('Bounded transition observer expired')
