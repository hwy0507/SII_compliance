"""One bounded, identity-checked preparation; no training dispatch."""
from pathlib import Path
import json,os,sys,time,hashlib,subprocess
ROOT=Path(__file__).resolve().parent
kind=sys.argv[1]
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def live(job):
 try:
  fields=Path(f"/proc/{job['pid']}/stat").read_text().split(') ')[1].split()
  return fields[19]==job['proc_start_ticks'] and fields[0]!='Z'
 except FileNotFoundError:return False
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
try:
 reg=read(ROOT/'REGISTRATION.json')['jobs'][kind];os.sched_setaffinity(0,{52 if kind=='direct' else 53})
 root=Path(reg['parent_run']);review=Path(reg['parent_review']);source=Path(reg['prepare_source'])
 assert sha(source)==reg['prepare_source_sha256'];assert sha(root/'LAUNCH.json')==reg['parent_launch_sha256']
 deadline=time.monotonic()+14400
 while True:
  assert time.monotonic()<deadline,'Fixed four-hour preparation wait expired'
  for p in [root/'ARCHIVE_REVIEW_FAILURE.json',*root.glob('*/FAILURE.json'),*root.glob('*/*/FAILURE.json')]:
   if p.exists():raise RuntimeError(str(p))
  ready=root/'ARCHIVE_REVIEW_FINISHED.json'
  if ready.exists():
   assert read(ready)['completed'] and read(review/'FINISHED.json')['completed'] and read(review/'REVIEW.json')['passed']
   if not any(live(job) for job in reg['learners']):break
  else:
   assert live(reg['monitor']), 'Original archive/review monitor exited without completion'
  time.sleep(5)
 write(ROOT/f'{kind}_PARENT_READY.json',dict(time=time.time(),parent_review_sha256=sha(review/'REVIEW.json'),all_original_learners_exited=True))
 env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
 subprocess.run([reg['python'],str(source)],check=True,env=env)
 write(ROOT/f'{kind}_FINISHED.json',dict(time=time.time(),prepared=True,automatic_training=False))
except BaseException as error:
 write(ROOT/f'{kind}_FAILURE.json',dict(time=time.time(),error=repr(error)));raise
