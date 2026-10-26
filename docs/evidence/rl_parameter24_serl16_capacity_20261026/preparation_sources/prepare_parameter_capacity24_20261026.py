from pathlib import Path
import json,hashlib,shutil,subprocess,os,time,sys
import torch
torch.set_num_threads(1)
os.sched_setaffinity(0,{54})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance'
oldname='parameter_pool30_cycle23_20261026_v1';name='parameter_capacity_pool30_cycle24_20261026_v1';OUT=B/'runs'/name;RT=B/'runtime'/name
sys.path[:0]=[str(R/'code/mujoco_6d_vmc_benchmark/tools'),str(B/'runtime'/oldname)]
from validate_published_finite_check_20261025 import digest
from parameter_replay_capacity_20261026 import MARKER

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
review=B/'runs/parameter_pool30_cycle23_review_20261026_v1';prep=B/'runs/parameter_capacity_preparation_20261026_v2/REVIEW.json'
assert json.loads((review/'FINISHED.json').read_text())['completed'] and json.loads((review/'REVIEW.json').read_text())['passed']
assert json.loads(prep.read_text())['passed']
OUT.mkdir();shutil.copytree(B/'runtime'/oldname,RT,ignore=shutil.ignore_patterns('__pycache__'))
driver='resume_cheq_capacity_pool30_20261026.py';helper='parameter_replay_capacity_20261026.py'
for n in [driver,helper]:shutil.copyfile(R/'code/mujoco_6d_vmc_benchmark/tools'/n,RT/n)
write(OUT/'SCIENTIFIC_DECISION.json',dict(parent_cycle=23,new_cycles=1,learner_settings_unchanged=True,capacity_before=1_000_000,capacity_after=2_000_000,auxiliary_weights_imported=False,reason='Preserve all formal replay across imminent1m boundary; append without overwrite and persist strict capacity marker. Sampling after1m differs from the old ring overwrite because older data remain eligible. One finite cycle24, no convergence claim.',required_review=ref(review/'REVIEW.json'),required_health=ref(review/'health/DIAGNOSIS.json'),preparation_review=ref(prep)))
oldjobs=json.loads((B/'runs'/oldname/'LAUNCH.json').read_text())['jobs'];commands=[]
for job in oldjobs:
 m=job['controller'];dest=OUT/m;dest.mkdir();parentreg=B/'runs'/oldname/m/'REGISTRATION.json';p=json.loads(parentreg.read_text());p['resume_parent_registration']=ref(parentreg)
 p['completed_stage_continuation']['parent_cycle']=23;p['completed_stage_continuation']['review']=ref(OUT/'SCIENTIFIC_DECISION.json')
 trial=p['batch_size_stage'];trial['parent_cycle']=23;cp=B/'runs/parameter_pool30_cycle23_archive_20261026_v1'/m/'cycle_00023.pt';trial['checkpoint']=ref(cp);trial['driver_sha256']=sha(RT/driver);trial['dependency_hashes'][driver]=sha(RT/driver);trial['cycle_review']=ref(review/'REVIEW.json');trial['health_review']=ref(review/'health/DIAGNOSIS.json');trial['reason']='Latest complete23 fullstate; expand replay to2m retaining every row/RNG/history, same learner settings; finite cycle24.'
 ck=torch.load(cp,map_location='cpu',weights_only=False);s=ck['replay'];assert s['capacity']==1_000_000 and s['size']==s['cursor']==ck['steps'] and s['size']<1_000_000
 assert ck['cycle']==23 and ck['boundary']=='complete_condition_cycle' and s['arrays']['observations'].shape[1]==50
 p['replay_capacity_stage']=dict(parent_cycle=23,old_capacity=1_000_000,new_capacity=2_000_000,marker=MARKER,auxiliary_weights_imported=False,helper_sha256=sha(RT/helper),preparation_review=ref(prep),entry_checkpoint=trial['checkpoint'],legacy_replay_digest=digest(s));del ck,s
 trial['dependency_hashes'][helper]=sha(RT/helper);write(dest/'REGISTRATION.json',p)
 cmd=list(job['command']);cmd[1]=str(RT/driver)
 for flag,value in [('--registration',dest/'REGISTRATION.json'),('--resume',cp),('--output',dest/'train')]:cmd[cmd.index(flag)+1]=str(value)
 commands.append(dict(controller=m,command=cmd))
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
checks=[]
for cpu,job in zip([52,53,54],commands):
 with (OUT/job['controller']/'check_only.log').open('x') as log:proc=subprocess.Popen(['taskset','-c',str(cpu)]+job['command']+['--check-only'],stdout=log,stderr=subprocess.STDOUT,env=env)
 checks.append((job['controller'],proc))
statuses={method:proc.wait() for method,proc in checks}
write(OUT/'CHECK_ONLY_EXIT_CODES.json',statuses)
assert all(code==0 for code in statuses.values()),statuses
write(OUT/'CHECK_ONLY_COMPLETE.json',dict(passed=True,new_optimizer_updates=0,time=time.time()));write(OUT/'COMMANDS.json',dict(jobs=commands));print(OUT,flush=True)
