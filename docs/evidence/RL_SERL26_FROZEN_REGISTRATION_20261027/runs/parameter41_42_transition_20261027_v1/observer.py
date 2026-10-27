from pathlib import Path
import json,time,os
os.sched_setaffinity(0,{54})
o=Path(__file__).parent;r=json.loads((o/'REGISTRATION.json').read_text());limit=time.monotonic()+r['timeout_seconds'];last={m:r['time'] for m in r['parents']};exits={};launches={}
while time.monotonic()<limit:
 now=time.time()
 for m,v in r['parents'].items():
  if m in exits:continue
  p=Path('/proc')/str(v['pid'])
  try:
   start=(p/'stat').read_text().rsplit(')',1)[1].split()[19];assert start==v['starttime'],'Parent PID reused';last[m]=now
  except FileNotFoundError:exits[m]=dict(exit_after=last[m],exit_before=now)
 for m,p in r['next_launches'].items():
  if m in launches:continue
  try:launches[m]=json.loads(Path(p).read_text())
  except (FileNotFoundError,json.JSONDecodeError):pass
 result=dict(time=now,parent_exits=exits,next_launches=launches,scope='Original process exit brackets to next spawn, not complete GPU idle duration')
 (o/'STATUS.json').write_text(json.dumps(result,indent=2)+'\n')
 if len(exits)==len(r['parents']) and len(launches)==len(r['next_launches']):
  (o/'FINISHED.json').write_text(json.dumps(dict(completed=True,time=now))+'\n');break
 time.sleep(r['poll_seconds'])
else:(o/'TIMEOUT.json').write_text(json.dumps(dict(time=time.time(),reason='Finite observation expired; no automatic retry or training'))+'\n')
