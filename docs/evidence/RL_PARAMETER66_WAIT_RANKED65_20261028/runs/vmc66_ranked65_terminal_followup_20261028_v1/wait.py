from pathlib import Path
import json,hashlib,time,os,subprocess,sys
os.sched_setaffinity(0,{53});OUT=Path(__file__).parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
try:
 plan=read(OUT/'PLAN.json');root=Path(plan['parent_followup']);deadline=time.monotonic()+7200
 for n,h in plan['sources'].items():assert sha(OUT/n)==h
 assert sha(root/'PLAN.json')==plan['parent_plan_sha256'] and sha(root/'LAUNCH.json')==plan['parent_launch_sha256']
 while True:
  assert not (root/'WAIT_FAILURE.json').exists()
  if (root/'FINISHED.json').exists():
   assert read(root/'FINISHED.json')['completed'] and read(root/'SAVED_VALUES_REVIEW.json')['passed']
   if not live(plan['parent_waiter']):break
  else:assert live(plan['parent_waiter']),'Original terminal followup absent without completion'
  assert time.monotonic()<deadline,'Fixed7200s observation expired; no scientific restart'
  time.sleep(5)
 subprocess.run([sys.executable,str(OUT/'audit.py')],check=True)
 (OUT/'FINISHED.json').write_text(json.dumps(dict(completed=True,time=time.time()))+'\n')
except BaseException as error:
 (OUT/'WAIT_FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(error)))+'\n');raise
