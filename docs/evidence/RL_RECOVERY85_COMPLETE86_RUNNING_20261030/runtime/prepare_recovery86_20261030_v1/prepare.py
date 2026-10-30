"""After full85 review, restore-check exact86 state only. Never launch training."""
from pathlib import Path
import json,time,hashlib,importlib.util,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;RUN=B/'runs/parameter_partial75_recovery_cycle85_20261029_v1';REV=B/'runs/parameter_partial75_recovery_cycle85_review_20261029_v1';OUT=B/'runs/parameter_partial75_recovery_cycle86_20261029_v1';ARC=B/'runs/parameter_partial75_recovery_cycle85_archive_20261029_v1';OLD=B/'runtime/parameter75_interruption_recovery_20261029_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def require_parent():
 for p,key in [(RUN/'ARCHIVE_REVIEW_FINISHED.json','completed'),(REV/'FINISHED.json','completed'),(REV/'REVIEW.json','passed')]:
  assert p.exists() and read(p)[key],f'Incomplete recovery85: {p}'
 assert (REV/'health/DIAGNOSIS.json').exists()
 for j in read(RUN/'LAUNCH.json')['jobs']:
  q=Path(f'/proc/{j["pid"]}/stat')
  if q.exists():
   s=q.read_text().rsplit(')',1)[1].split();assert s[19]!=j['proc_start_ticks'] or s[0]=='Z','Original85 learner still active'
def main():
 require_parent()
 reg=read(D/'REGISTRATION.json')
 for n,h in reg['sources'].items():assert sha(D/n)==h
 assert os.environ.get('CUDA_VISIBLE_DEVICES')!='','CUDA visibility must retain checkpoint CUDA RNG; do not hide devices for CPU check-only'
 assert not OUT.exists();OUT.mkdir()
 spec=importlib.util.spec_from_file_location('recovery86',D/'resume_recovery85.py');driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
 jobs=[]
 for j in read(RUN/'LAUNCH.json')['jobs']:
  m=j['controller'];dest=OUT/m;dest.mkdir();parent=RUN/m/'REGISTRATION.json';p=read(parent);old=p['interrupted_episode_recovery'];cp=ARC/m/'cycle_00085.pt'
  st=dict(version=1,parent_cycle=85,new_cycle=86,new_cycles=1,controller=m,parent_registration=ref(parent),checkpoint=ref(cp),cycle_review=ref(REV/'REVIEW.json'),health_review=ref(REV/'health/DIAGNOSIS.json'),recovery_driver=ref(OLD/'resume_partial75.py'),previous_driver=ref(B/'runtime/prepare_recovery85_20261030_v1/resume_recovery84.py'),driver_sha256=sha(D/'resume_recovery85.py'),original_runtime=old['original_runtime'],source_hashes=old['source_hashes'],trainer_path=old['trainer_path'],trainer_sha256=old['trainer_sha256'],patched_trainer_sha256=hashlib.sha256(driver.transform(Path(old['trainer_path']).read_text()).encode()).hexdigest(),maximum_new_actions=41250,environment_state_saved=False,old_window_continuity_claim=False,automatic_followup=False,optimizer_settings_changed=False,physical_semantics='New finite86 from exact complete recovery85. Retain all saved partial75 exposure and absent complete75 history; historical stage fields unchanged, this binding identifies current complete parent.')
  p['post_interruption_continuation']=st;driver.validate_protocol(st['parent_registration']['sha256'],p,'');write(dest/'REGISTRATION.json',p)
  cmd=list(j['command']);cmd[1]=str(D/'resume_recovery85.py')
  for flag,v in [('--registration',dest/'REGISTRATION.json'),('--resume',cp),('--output',dest/'train')]:cmd[cmd.index(flag)+1]=str(v)
  jobs.append(dict(controller=m,command=cmd))
 write(OUT/'COMMANDS.json',dict(jobs=jobs,automatic_training=False))
 processes={};env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
 for j in jobs:
  with (OUT/j['controller']/'check_only.log').open('x') as f:processes[j['controller']]=subprocess.Popen(j['command']+['--check-only'],stdout=f,stderr=subprocess.STDOUT,env=env)
 codes={m:p.wait() for m,p in processes.items()};write(OUT/'CHECK_ONLY_EXIT_CODES.json',codes);assert all(x==0 for x in codes.values()),codes
 for m in codes:assert read(OUT/m/'CHECK_ONLY_REVIEW.json')['passed'] and not (OUT/m/'train').exists()
 write(OUT/'CHECK_ONLY_COMPLETE.json',dict(passed=True,time=time.time(),new_physics=0,optimizer_updates=0,automatic_training=False,required_before_training='Explicit decision after full85 loss, labels, health, terminal and plot review; separate actual startup and archive setup.'))
 print('Exact86 restore-only preparation complete; no training dispatched')
if __name__=='__main__':main()
