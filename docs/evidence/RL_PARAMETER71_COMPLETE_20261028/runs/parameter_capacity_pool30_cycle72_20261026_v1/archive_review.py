"""Archive one explicitly selected finite stage, then review; never launches training."""
from pathlib import Path
import os,json,shutil,hashlib,subprocess,time,re,sys
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
kind=sys.argv[1];cycle=int(sys.argv[2]);direct=kind=='serl_take';date='20261027' if direct else '20261026';methods=['direct'] if direct else ['impedance','admittance','vmc'];os.sched_setaffinity(0,{52} if direct else {53})
name=f'{kind}_cycle{cycle}_{date}_v1';runroot=B/'runs'/name;arc=B/'runs'/f'{kind}_cycle{cycle}_archive_{date}_v1';out=B/'runs'/f'{kind}_cycle{cycle}_review_{date}_v1'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def identity(pid):return Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()[19]
def check_failure(run):
 for n in ['FAILURE.json','DRIVER_FAILURE.json']:
  if (run/n).exists():raise RuntimeError(str(run/n))
try:
 assert not arc.exists() and not out.exists()
 launch=json.loads((runroot/'LAUNCH.json').read_text());jobs=launch['jobs'];deadline=time.monotonic()+14400
 for m in methods:
  run=runroot/m if direct else runroot/m/'train';job=next(j for j in jobs if j['controller']==m)
  while not (run/'FINISHED.json').exists():
   check_failure(run);check_failure(run.parent)
   assert time.monotonic()<deadline,'Fixed four-hour monitor deadline exceeded'
   assert identity(job['pid'])==job['proc_start_ticks'],'Learner exited or PID reused before FINISHED'
   time.sleep(5)
  assert json.loads((run/'FINISHED.json').read_text())['status']=='stopped_at_complete_cycle'
  # FINISHED is written after atomic final checkpoint publication.
  import torch
  torch.set_num_threads(1);src=run/'checkpoint_latest.pt';x=torch.load(src,map_location='cpu',weights_only=False)
  assert x['cycle']==cycle and x['boundary']=='complete_condition_cycle'
  assert x['steps']==x['replay']['size']==x['replay']['cursor'];del x
  d=arc/m;d.mkdir(parents=True);dst=d/f'cycle_{cycle:05d}.pt';shutil.copyfile(src,dst);h=sha(dst);assert h==sha(src)
  write(d/f'cycle_{cycle:05d}.json',dict(path=str(dst),sha256=h,source=str(src),cycle=cycle,time=time.time()))
 write(arc/'FINISHED.json',dict(completed=True,cycle=cycle,time=time.time()))
 prev=cycle-1;old=B/'runs'/f'{kind}_cycle{prev}_review_{date}_v1';out.mkdir()
 if direct:
  names={'review.py':'review.py','diagnose.py':'diagnose.py',f'audit_serl_take{prev}_replay_20261027.py':f'audit_serl_take{cycle}_replay_20261027.py','coordinator.py':'coordinator.py'}
  for a,z in names.items():
   s=(old/a).read_text().replace(f'cycle{prev}',f'cycle{cycle}').replace(f'cycle_{prev:05d}',f'cycle_{cycle:05d}').replace(f'take{prev}',f'take{cycle}')
   s=re.sub(r'=='+str(prev)+r'\b','=='+str(cycle),s)
   s=s.replace(f"old['cycle']=={prev-1}",f"old['cycle']=={prev}").replace(f"['parent_cycle']=={prev-1}",f"['parent_cycle']=={prev}")
   s=s.replace(f'complete_parent{prev-1}=True',f'complete_parent{prev}=True')
   s=s.replace(f'len(terminal)=={prev*30}',f'len(terminal)=={cycle*30}').replace(f'terminal_count={prev*30}',f'terminal_count={cycle*30}')
   (out/z).write_text(s)
 else:
  for n in ['review.py','coordinator.py','diagnose_published_training_20261025.py','diagnose_published_value_bound_20261025.py']:
   s=(old/n).read_text()
   if n in ['review.py','coordinator.py']:
    s=s.replace(f'cycle{prev}',f'cycle{cycle}').replace(f'cycle_{prev:05d}',f'cycle_{cycle:05d}').replace(f'Cycle{prev}',f'Cycle{cycle}')
    s=re.sub(r'=='+str(prev)+r'\b','=='+str(cycle),s);s=re.sub(r'=='+str(prev-1)+r'\b','=='+str(prev),s)
    s=s.replace(f"'--cycle','{prev}'",f"'--cycle','{cycle}'")
   (out/n).write_text(s)
  view=B/'runs'/f'{kind}_cycle{cycle}_archive_{date}_v1_view';view.mkdir()
  for m in methods:(view/m).symlink_to(runroot/m/'train')
  shutil.copyfile(runroot/'LAUNCH.json',view/'LAUNCH.json')
 for p in out.glob('*.py'):compile(p.read_text(),str(p),'exec')
 subprocess.run([str(B/'env/bin/python'),str(out/'coordinator.py')],check=True)
 write(runroot/'ARCHIVE_REVIEW_FINISHED.json',dict(completed=True,time=time.time(),review=str(out)))
except BaseException as e:
 write(runroot/'ARCHIVE_REVIEW_FAILURE.json',dict(error=repr(e),time=time.time()));raise
