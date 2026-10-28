from pathlib import Path
import json,time,hashlib,subprocess,os,sys
ROOT=Path(sys.argv[1]);RT=Path(__file__).parent
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def read(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def live(j):
 try:
  s=Path(f"/proc/{j['pid']}/stat").read_text().split(') ')[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
 except FileNotFoundError:return False
try:
 os.sched_setaffinity(0,{0});plan=read(ROOT/'PLAN.json');run=Path(plan['parent_run']);review=B/'runs/parameter_capacity_pool30_cycle55_review_20261026_v1'
 assert sha(RT/'track.py')==plan['source_sha256'] and sha(RT/'review.py')==plan['review_source_sha256']
 assert sha(plan['parent_launch']['path'])==plan['parent_launch']['sha256']
 for x in plan['inputs'].values():assert sha(x['path'])==x['sha256']
 deadline=time.monotonic()+plan['wait_seconds']
 while True:
  assert not (run/'ARCHIVE_REVIEW_FAILURE.json').exists()
  assert not any((run/j['controller']/'train/FAILURE.json').exists() for j in plan['learners'])
  if (run/'ARCHIVE_REVIEW_FINISHED.json').exists():
   assert read(run/'ARCHIVE_REVIEW_FINISHED.json')['completed'] and read(review/'FINISHED.json')['completed'] and read(review/'REVIEW.json')['passed']
   if not any(live(j) for j in plan['learners']):break
  else:assert live(plan['monitor']),'Original monitor exited before full review'
  assert time.monotonic()<deadline,'Fixed7200s observation expired; no restart or training dispatch'
  time.sleep(5)
 reg=dict(plan);reg['inputs']=dict(plan['inputs']);reg['inputs'].update(health55=ref(review/'health/DIAGNOSIS.json'),review55=ref(review/'REVIEW.json'),checkpoint55=ref(B/'runs/parameter_capacity_pool30_cycle55_archive_20261026_v1/impedance/cycle_00055.pt'));write(ROOT/'REGISTRATION.json',reg)
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 for name in ['track','review']:
  p=subprocess.Popen([sys.executable,str(RT/(name+'.py')),'--root',str(ROOT)],env=env)
  write(ROOT/(name+'_LAUNCH.json'),dict(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().split(') ')[1].split()[19],time=time.time()))
  code=p.wait();assert code==0,(name,code)
 write(ROOT/'FINISHED.json',dict(completed=True,time=time.time(),new_physics=0,optimizer_updates=0))
except BaseException as error:
 write(ROOT/'WAIT_FAILURE.json',dict(time=time.time(),error=repr(error)));raise
