from pathlib import Path
import json,time,hashlib,subprocess,sys,os
os.sched_setaffinity(0,{3})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;O=B/'runs/serl_take33_frozen_full30_20261029_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2)+'\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat');s=p.read_text().rsplit(')',1)[1].split() if p.exists() else None
 return s is not None and s[19]==j['proc_start_ticks'] and s[0]!='Z'
try:
 p=read(O/'COMPARISON_PLAN.json');assert sha(D/'compare.py')==p['source_sha256'] and sha(__file__)==p['waiter_sha256'];j=read(O/'REVIEW_LAUNCH.json');deadline=time.monotonic()+21600
 while not (O/'REVIEW.json').exists():
  assert not (O/'REVIEW_FAILURE.json').exists(),'Original frozen33 review failed; retain science and failure'
  assert live(j),'Original review absent without completion'
  assert time.monotonic()<deadline,'Observer expired; no scientific restart'
  time.sleep(5)
 assert read(O/'REVIEW.json')['passed'];subprocess.run([sys.executable,str(D/'compare.py')],check=True)
 write(O/'COMPARISON_FINISHED.json',dict(completed=True,time=time.time(),source_sha256=p['source_sha256'],scientific_restart=False))
except BaseException as e:write(O/'COMPARISON_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
