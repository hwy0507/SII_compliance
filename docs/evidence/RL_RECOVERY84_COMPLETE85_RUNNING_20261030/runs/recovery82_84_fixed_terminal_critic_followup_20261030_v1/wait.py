from pathlib import Path
import json,time,os,subprocess,hashlib
D=Path(__file__).parent;B=D.parents[1];os.sched_setaffinity(0,{3})
def read(p):return json.loads(Path(p).read_text())
def put(p,r):
 with p.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
try:
 p=read(D/'PLAN.json')
 for name,h in p['sources'].items():assert hashlib.sha256((D/name).read_bytes()).hexdigest()==h
 while True:
  ready=[]
  for x in p['wait_for']:
   for failure in x['failures']:assert not Path(failure).exists(),failure
   if live(x['launch']):ready.append(False)
   else:
    for req in x['receipts']:assert read(req['path'])[req['key']]==req['value'],req
    ready.append(True)
  if all(ready):break
  assert time.time()<p['original84_monitor_deadline'],'Original84 deadline expired; inspect original jobs, no restart or extension'
  time.sleep(5)
 for name,h in p['sources'].items():assert hashlib.sha256((D/name).read_bytes()).hexdigest()==h
 subprocess.run([str(B/'env/bin/python'),str(D/'audit.py')],check=True)
 assert read(D/'REVIEW.json')['passed'] and read(D/'SAVED_REVIEW.json')['passed']
 put(D/'FINISHED.json',dict(passed=True,time=time.time(),automatic_training=False,new_physics=0,optimizer_updates=0))
except BaseException as e:put(D/'FAILURE.json',dict(time=time.time(),error=repr(e)));raise
