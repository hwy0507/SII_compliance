from pathlib import Path
import json,hashlib,time,os,subprocess,signal
O=Path(__file__).parent;B=O.parents[1];os.sched_setaffinity(0,{54});plan=json.loads((O/'PLAN.json').read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(name,d):
 p=O/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2)+'\n');t.replace(p)
def live(pid,expected):
 try:
  s=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();return s[19]==expected['start_ticks'] and s[0]!='Z'
 except FileNotFoundError:return False
try:
 assert sha(__file__)==plan['waiter_sha256']
 static=Path(plan['static_directory']);assert sha(static/'SOURCE_MANIFEST.json')==plan['static_manifest_sha256']
 for name,expected in json.loads((static/'SOURCE_MANIFEST.json').read_text()).items():assert sha(static/name)==expected
 review=B/'runs/parameter_capacity_pool30_cycle47_review_20261026_v1';deadline=time.monotonic()+plan['wait_seconds']
 while True:
  assert time.monotonic()<deadline,'Bounded47 wait expired; no automatic extension/retry'
  for method in ['impedance','admittance','vmc']:assert not (B/'runs/parameter_capacity_pool30_cycle47_20261026_v1'/method/'train/FAILURE.json').exists()
  parents_live=any(live(pid,identity) for pid,identity in plan['parent_identities'].items())
  if (review/'FINISHED.json').exists() and not parents_live:break
  time.sleep(5)
 assert json.loads((review/'FINISHED.json').read_text())['completed']
 assert json.loads((review/'REVIEW.json').read_text())['passed']
 assert (review/'health/DIAGNOSIS.json').exists()
 cmd=[str(B/'env/bin/python'),str(static/'prepare.py')]
 with (O/'check_only_driver.log').open('x') as log:p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 write('CHECK_ONLY_LAUNCH.json',dict(time=time.time(),pid=p.pid,command=cmd,new_physics=0,optimizer_updates=0))
 try:code=p.wait(timeout=1000)
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
  raise
 assert code==0,code
 assert json.loads((B/'runs/parameter_capacity_pool30_cycle48_20261026_v1/CHECK_ONLY_COMPLETE.json').read_text())['passed']
 write('FINISHED.json',dict(time=time.time(),passed=True,automatic_training=False,actual_complete47_restore=True,new_physics=0,optimizer_updates=0))
except BaseException as e:
 write('FAILURE.json',dict(time=time.time(),error=repr(e)));raise
