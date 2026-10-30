from pathlib import Path
import os,json,time,hashlib,shutil,subprocess
os.sched_setaffinity(0,{53})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'runs/parameter_partial75_recovery_cycle86_20261029_v1';A=B/'runs/parameter_partial75_recovery_cycle86_archive_20261029_v1';V=B/'runs/parameter_partial75_recovery_cycle86_archive_20261029_v1_view';D=B/'runs/parameter_partial75_recovery_cycle86_review_20261029_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 f=p.read_text().rsplit(')',1)[1].split();return f[19]==j['proc_start_ticks'] and f[0]!='Z'
try:
 jobs=read(R/'LAUNCH.json')['jobs'];deadline=time.monotonic()+14400;assert not A.exists() and not V.exists()
 for j in jobs:
  m=j['controller'];run=R/m/'train'
  while not (run/'FINISHED.json').exists():
   assert live(j) and time.monotonic()<deadline
   assert not (run/'FAILURE.json').exists() and not (run.parent/'DRIVER_FAILURE.json').exists();time.sleep(5)
  assert read(run/'FINISHED.json')['status']=='stopped_at_complete_cycle'
  import torch
  torch.set_num_threads(1);cp=run/'checkpoint_latest.pt';x=torch.load(cp,map_location='cpu',weights_only=False);assert x['cycle']==86 and x['boundary']=='complete_condition_cycle' and x['interruption_recovery']['parent_cycle']==75 and x['recovery_continuation']['parent_cycle']==85;del x
  dest=A/m;dest.mkdir(parents=True);q=dest/'cycle_00086.pt';shutil.copyfile(cp,q);assert sha(q)==sha(cp);write(dest/'cycle_00086.json',dict(path=str(q),sha256=sha(q),source=str(cp),cycle=86,time=time.time()))
 write(A/'FINISHED.json',dict(completed=True,cycle=86,time=time.time()));V.mkdir()
 for j in jobs:(V/j['controller']).symlink_to(R/j['controller']/'train')
 shutil.copyfile(R/'LAUNCH.json',V/'LAUNCH.json')
 for item in read(D/'SOURCE_REVIEW.json')['files']:assert sha(D/item['name'])==item['sha256']
 subprocess.run([str(B/'env/bin/python'),str(D/'coordinator.py')],check=True)
 write(R/'ARCHIVE_REVIEW_FINISHED.json',dict(completed=True,time=time.time(),review=str(D)))
except BaseException as e:
 write(R/'ARCHIVE_REVIEW_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
