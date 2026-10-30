from pathlib import Path
import json,hashlib,time,os,subprocess,sys
D=Path(__file__).parent
os.sched_setaffinity(0,{53})
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def live(j):
 q=Path(f'/proc/{j["pid"]}/stat')
 if not q.exists():return False
 s=q.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
try:
 plan=read(D/'REGISTRATION.json');run=Path(plan['parent_run']);review=Path(plan['parent_review'])
 for n,h in plan['sources'].items():assert sha(D/n)==h
 assert sha(run/'LAUNCH.json')==plan['parent_launch_sha256'];deadline=time.monotonic()+14400
 while True:
  assert not (run/'ARCHIVE_REVIEW_FAILURE.json').exists()
  for j in plan['learners']:
   p=run/j['controller'];assert not (p/'train/FAILURE.json').exists() and not (p/'DRIVER_FAILURE.json').exists()
  if (run/'ARCHIVE_REVIEW_FINISHED.json').exists():
   assert read(run/'ARCHIVE_REVIEW_FINISHED.json')['completed'] and read(review/'FINISHED.json')['completed'] and read(review/'REVIEW.json')['passed']
   if not any(live(j) for j in plan['learners']):break
  else:assert live(plan['monitor']),'Original monitor absent without completion'
  assert time.monotonic()<deadline,'Fixed4h preparation observation expired; no restart'
  time.sleep(5)
 for n,h in plan['sources'].items():assert sha(D/n)==h
 subprocess.run([sys.executable,str(D/'prepare.py')],check=True)
 write(D/'FINISHED.json',dict(time=time.time(),prepared=True,automatic_training=False))
except BaseException as e:
 write(D/'FAILURE.json',dict(time=time.time(),error=repr(e)));raise
