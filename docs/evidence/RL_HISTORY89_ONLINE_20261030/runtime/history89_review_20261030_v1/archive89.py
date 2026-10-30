from pathlib import Path
import os,json,time,hashlib,shutil,subprocess
os.sched_setaffinity(0,{53})
D=Path(__file__).parent;B=D.parents[1];R=B/'runs/parameter_history_cycle89_20261030_v1';A=B/'runs/parameter_history_cycle89_archive_20261030_v1';V=B/'runs/parameter_history_cycle89_view_20261030_v1';O=B/'runs/parameter_history_cycle89_review_20261030_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 f=p.read_text().rsplit(')',1)[1].split();return f[19]==j['proc_start_ticks'] and f[0]!='Z'
try:
 jobs=read(R/'LAUNCH.json')['jobs'];deadline=time.monotonic()+14400;assert not A.exists() and not V.exists()
 for n,h in read(D/'SOURCES.json')['files'].items():assert sha(D/n)==h
 for j in jobs:
  m=j['controller'];run=R/m/'train'
  while not (run/'FINISHED.json').exists():
   assert live(j) and time.monotonic()<deadline
   assert not (run/'FAILURE.json').exists() and not (run.parent/'DRIVER_FAILURE.json').exists();time.sleep(5)
  assert read(run/'FINISHED.json')['status']=='stopped_at_complete_cycle'
  import torch
  torch.set_num_threads(1);cp=run/'checkpoint_latest.pt';x=torch.load(cp,map_location='cpu',weights_only=False);assert x['cycle']==89 and x['boundary']=='complete_condition_cycle' and x['recovery_continuation']['parent_cycle']==88 and x['history_critic_amendment']['first_cycle']==88;del x
  dest=A/m;dest.mkdir(parents=True);q=dest/'cycle_00089.pt';shutil.copyfile(cp,q);assert sha(q)==sha(cp);put(dest/'cycle_00089.json',dict(path=str(q),sha256=sha(q),source=str(cp),cycle=89,time=time.time()))
 put(A/'FINISHED.json',dict(completed=True,cycle=89,time=time.time()));V.mkdir()
 for j in jobs:(V/j['controller']).symlink_to(R/j['controller']/'train')
 shutil.copyfile(R/'LAUNCH.json',V/'LAUNCH.json')
 subprocess.run([str(B/'env/bin/python'),str(D/'review89.py')],check=True)
 subprocess.run([str(B/'env/bin/python'),str(D/'health89.py'),'--runtime',str(B/'runtime/source_train17_clock'),'--run',str(V),'--output',str(O/'health'),'--cycle-archive',str(A),'--cycle','89'],check=True,env=dict(os.environ,PYTHONPATH=str(D)+':'+str(B/'runtime/source_train17_clock/source/tools')))
 subprocess.run([str(B/'env/bin/python'),str(D/'loss89.py')],check=True)
 put(O/'FINISHED.json',dict(completed=True,time=time.time(),plots_still_require_actual_inspection=True,convergence_claim=False,automatic90=False));put(R/'ARCHIVE_REVIEW_FINISHED.json',dict(completed=True,time=time.time(),review=str(O)))
except BaseException as e:put(R/'ARCHIVE_REVIEW_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
