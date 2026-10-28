from pathlib import Path
import json,time,hashlib,subprocess,sys,os
os.sched_setaffinity(0,{54})
p=Path(__file__).parent

def read(f):return json.loads(f.read_text())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def live(j):
 f=Path(f'/proc/{j["pid"]}/stat')
 if not f.exists():return False
 s=f.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
try:
 plan=read(p/'PLAN.json');root=Path(plan['frozen55']);deadline=time.monotonic()+plan['wait_seconds']
 for name,h in plan['sources'].items():assert sha(p/name)==h
 assert sha(root/'PLAN.json')==plan['original_plan55_sha256']
 while True:
  assert not (root/'REVIEW_FAILURE.json').exists()
  for j in plan['evaluators']:
   d=root/j['controller'];assert not (d/'FAILURE.json').exists()
   if not (d/'FINISHED.json').exists():assert live(j),'Original evaluator vanished before FINISHED'
  if (root/'REVIEW.json').exists():
   assert read(root/'REVIEW.json')['passed']
   if not any(live(j) for j in plan['evaluators']+[plan['root_review']]):break
  else:assert live(plan['root_review']),'Original rootreview vanished before REVIEW'
  assert time.monotonic()<deadline,'Fixed7200s comparison observation expired; no restart'
  time.sleep(5)
 subprocess.run([sys.executable,str(p/'review_compare.py')],check=True)
 (p/'FINISHED.json').write_text(json.dumps(dict(completed=True,time=time.time(),automatic_training=False))+'\n')
except BaseException as error:
 (p/'FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(error)))+'\n');raise
