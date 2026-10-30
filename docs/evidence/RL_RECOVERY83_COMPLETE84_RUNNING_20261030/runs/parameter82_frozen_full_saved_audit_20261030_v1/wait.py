from pathlib import Path
import json,time,subprocess,os,hashlib
D=Path(__file__).parent;B=D.parents[1];F=B/'runs/parameter82_frozen_full30_20261030_v1';os.sched_setaffinity(0,{3})
def read(p):return json.loads(p.read_text())
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[0]!='Z' and s[19]==j['proc_start_ticks']
try:
 plan=read(D/'PLAN.json');assert hashlib.sha256((D/'audit.py').read_bytes()).hexdigest()==plan['source']['sha256'];assert hashlib.sha256((F/'PLAN.json').read_bytes()).hexdigest()==plan['evaluation_plan']['sha256']
 while True:
  assert not (F/'REVIEW_FAILURE.json').exists()
  for m in plan['controllers']:assert not (F/m/'FAILURE.json').exists()
  if (F/'REVIEW.json').exists() and not live(plan['original_review_launch']):break
  assert live(plan['original_review_launch']),'Original root reviewer absent without successful review'
  assert time.time()<plan['original_deadline'],'Original review deadline expired; no extension or restart'
  time.sleep(5)
 assert read(F/'REVIEW.json')['passed']
 put(D/'FULL82_BINDING.json',dict(time=time.time(),root_review_sha256=hashlib.sha256((F/'REVIEW.json').read_bytes()).hexdigest(),all90=True))
 subprocess.run([str(B/'env/bin/python'),str(D/'audit.py')],check=True)
 assert read(D/'REVIEW.json')['passed'] and read(D/'SAVED_REVIEW.json')['passed']
 put(D/'FINISHED.json',dict(time=time.time(),passed=True,new_physics=0,optimizer_updates=0,automatic_training=False))
except BaseException as e:put(D/'FAILURE.json',dict(time=time.time(),error=repr(e)));raise
