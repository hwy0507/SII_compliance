from pathlib import Path
import json,hashlib,shutil,subprocess,os,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
R=B/'repository/SII_compliance';oldname='parameter_batch65536_cycle16_20261026_v1';name='parameter_batch65536_cycle17_20261026_v1'
OUT=B/'runs'/name;RT=B/'runtime'/name

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
review=B/'runs/parameter_batch65536_cycle16_review_20261026_v1'
assert json.loads((review/'FINISHED.json').read_text())['completed']
assert json.loads((review/'REVIEW.json').read_text())['passed']
OUT.mkdir();shutil.copytree(B/'runtime'/oldname,RT,ignore=shutil.ignore_patterns('__pycache__'))
driver='resume_cheq_batch65536_reviewed_continuation_20261026.py';shutil.copyfile(R/'code/mujoco_6d_vmc_benchmark/tools'/driver,RT/driver)
write(OUT/'SCIENTIFIC_DECISION.json',dict(parent_cycle=16,new_cycles=1,settings_unchanged=True,auxiliary_weights_imported=False,reason='One finite unchanged cycle after reviewed16 to assess persistence of online reward and value behavior. Full formal state and original task retained; convergence not claimed.',required_review=ref(review/'REVIEW.json'),required_health=ref(review/'health/DIAGNOSIS.json')))
oldjobs=json.loads((B/'runs'/oldname/'LAUNCH.json').read_text())['jobs'];commands=[]
for job in oldjobs:
 m=job['controller'];dest=OUT/m;dest.mkdir();parentreg=B/'runs'/oldname/m/'REGISTRATION.json';p=json.loads(parentreg.read_text());p['resume_parent_registration']=ref(parentreg)
 p['completed_stage_continuation']['parent_cycle']=16;p['completed_stage_continuation']['review']=ref(OUT/'SCIENTIFIC_DECISION.json')
 trial=p['batch_size_stage'];trial['parent_cycle']=16;trial['checkpoint']=ref(B/'runs/parameter_batch65536_cycle16_archive_20261026_v1'/m/'cycle_00016.pt');trial['driver_sha256']=sha(RT/driver);trial['dependency_hashes'][driver]=sha(RT/driver);trial['cycle_review']=ref(review/'REVIEW.json');trial['health_review']=ref(review/'health/DIAGNOSIS.json');trial['reason']='Continue unchanged from complete16 for one cycle; inspect reward/value stability without resetting state.'
 write(dest/'REGISTRATION.json',p)
 cmd=list(job['command']);cmd[1]=str(RT/driver)
 for flag,value in [('--registration',dest/'REGISTRATION.json'),('--resume',trial['checkpoint']['path']),('--output',dest/'train')]:cmd[cmd.index(flag)+1]=str(value)
 commands.append(dict(controller=m,command=cmd))
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
for job in commands:
 with (OUT/job['controller']/'check_only.log').open('x') as log:subprocess.run(['taskset','-c','54']+job['command']+['--check-only'],stdout=log,stderr=subprocess.STDOUT,check=True,env=env)
write(OUT/'CHECK_ONLY_COMPLETE.json',dict(passed=True,new_optimizer_updates=0,time=time.time()))
write(OUT/'COMMANDS.json',dict(jobs=commands))
print(str(OUT),flush=True)
