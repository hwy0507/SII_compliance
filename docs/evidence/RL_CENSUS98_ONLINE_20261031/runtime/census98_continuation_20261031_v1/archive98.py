from pathlib import Path
import os,sys,time,json,shutil,subprocess,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];sys.path.insert(0,str(D));from driver import read,sha,put,validate_checkpoint
R=B/'runs/parameter_census_cycle98_20261031_v1';A=B/'runs/parameter_census_cycle98_archive_20261031_v1';V=B/'runs/parameter_census_cycle98_view_20261031_v1';O=B/'runs/parameter_census_cycle98_review_20261031_v1'
os.sched_setaffinity(0,{53})
def live(j):
 try:s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();return s[0]!='Z' and s[19]==j['proc_start_ticks']
 except FileNotFoundError:return False
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
  torch.set_num_threads(1);cp=run/'checkpoint_latest.pt';ck=torch.load(cp,map_location='cpu',weights_only=False);validate_checkpoint(ck,read(run.parent/'REGISTRATION.json'),complete=True);del ck
  dest=A/m;dest.mkdir(parents=True);q=dest/'cycle_00098.pt';shutil.copyfile(cp,q);assert sha(q)==sha(cp);put(dest/'cycle_00098.json',dict(path=str(q),sha256=sha(q),source=str(cp),cycle=98,time=time.time()))
 put(A/'FINISHED.json',dict(completed=True,cycle=98,time=time.time()));V.mkdir()
 for j in jobs:(V/j['controller']).symlink_to(R/j['controller']/'train')
 shutil.copyfile(R/'LAUNCH.json',V/'LAUNCH.json')
 env=dict(os.environ,PYTHONPATH=str(D)+':'+str(B/'runtime/source_train17_clock/source/tools'))
 for command in [[str(D/'review98.py')],[str(D/'health98.py'),'--runtime',str(B/'runtime/source_train17_clock'),'--run',str(V),'--output',str(O/'health'),'--cycle-archive',str(A),'--cycle','98'],[str(D/'loss98.py')]]:subprocess.run([str(B/'env/bin/python'),*command],check=True,env=env)
 put(O/'FINISHED.json',dict(completed=True,time=time.time(),plots_still_require_actual_inspection=True,convergence_claim=False,automatic98=False));put(R/'ARCHIVE_REVIEW_FINISHED.json',dict(completed=True,time=time.time(),review=str(O)))
except BaseException:put(R/'ARCHIVE_REVIEW_FAILURE.json',dict(time=time.time(),traceback=traceback.format_exc()));raise
