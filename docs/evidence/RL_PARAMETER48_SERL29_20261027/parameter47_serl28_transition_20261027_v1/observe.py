from pathlib import Path
import json,time,os
O=Path(__file__).parent;B=O.parents[1];os.sched_setaffinity(0,{54});plan=json.loads((O/'PLAN.json').read_text());deadline=time.monotonic()+plan['budget_seconds'];observations={};changes=[]
def identity(pid):
 p=Path(f'/proc/{pid}')
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split()
  return dict(start_ticks=st[19],state=st[0],command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode())
 except FileNotFoundError:return None
def write(name,d):
 p=O/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2)+'\n');t.replace(p)
try:
 while True:
  now=time.time();all_started=True
  for g in plan['groups']:
   released=True
   for pid in g['parents']:
    key=str(pid);r=observations.setdefault(key,dict(last_seen_alive=None,first_seen_exited=None));i=identity(pid);original=g['identities'][key]
    alive=i and i['start_ticks']==original['start_ticks'] and i['state']!='Z'
    if alive:r['last_seen_alive']=now;released=False
    elif r['first_seen_exited'] is None:r['first_seen_exited']=now
   finished=(B/'runs'/g['review_run']/'FINISHED.json').exists()
   if released and not finished:
    pid=g['review_pid'];i=identity(pid)
    if i and i['start_ticks']==g['identities'][str(pid)]['start_ticks']:
     children=Path(f'/proc/{pid}/task/{pid}/children').read_text().split()
     for q in [pid]+list(map(int,children)):
      try:
       x=identity(q)
       if not x or g['review_run'] not in x['command']:continue
       before=sorted(os.sched_getaffinity(q))
       if before!=[g['cpu']]:
        os.sched_setaffinity(q,{g['cpu']});changes.append(dict(time=time.time(),pid=q,start_ticks=x['start_ticks'],before=before,after=sorted(os.sched_getaffinity(q)),group=g['name']))
      except ProcessLookupError:pass
   path=B/'runs'/g['next_run']/'LAUNCH.json'
   if path.exists():
    launch=json.loads(path.read_text());observations[g['name']]=dict(first_observed_next_launch=observations.get(g['name'],{}).get('first_observed_next_launch',now),launch=launch)
   else:all_started=False
  write('OBSERVATION.json',dict(time=now,parent_observations=observations,allocation_changes=changes,all_next_launched=all_started,scope='Process exit-to-spawn observation bounds only, not exact GPU idle time'))
  if all_started:break
  if time.monotonic()>=deadline:break
  time.sleep(plan['interval_seconds'])
 write('FINISHED.json',dict(time=time.time(),all_next_launched=all_started,bounded_observation_finished=True))
except BaseException as e:
 write('FAILURE.json',dict(time=time.time(),error=repr(e)));raise
