from pathlib import Path
import json,hashlib,shutil,subprocess,os,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance'
oldname='serl_multistep_gather_cycle11_20261026_v1';name='serl_multistep_transfer_cycle12_20261026_v1';OUT=B/'runs'/name;RT=B/'runtime'/name

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
review=B/'runs/serl_multistep_gather_cycle11_review_20261026_v1'
assert (review/'FINISHED.json').exists() and json.loads((review/'REVIEW.json').read_text())['passed']
OUT.mkdir();shutil.copytree(B/'runtime'/oldname,RT,ignore=shutil.ignore_patterns('__pycache__'))
driver='resume_serl_multistep_transfer_stage_20261026.py'
for n in [driver,'serl_multistep_batch_transfer_20261026.py']:shutil.copyfile(R/'code/mujoco_6d_vmc_benchmark/tools'/n,RT/n)
parentreg=B/'runs'/oldname/'REGISTRATION.json';p=json.loads(parentreg.read_text());p['resume_parent_registration']=ref(parentreg)
stage=p['reviewed_continuation_stage'];stage['parent_cycle']=11;stage['checkpoint']=ref(B/'runs/serl_multistep_gather_cycle11_archive_20261026_v1/direct/cycle_00011.pt');stage['driver_sha256']=sha(RT/driver);stage['cycle_review']=ref(review/'REVIEW.json');stage['health_review']=ref(review/'DIAGNOSIS.json');stage['decision']='One finite unchanged-algorithm cycle from full formal11 with reviewed equivalent single batch transfer. Full replay/state retained; no auxiliary weights or convergence claim.'
gather=p['gather_stage'];gather['prepared_checkpoint']=stage['checkpoint'];gather['transfer_review']=ref(B/'runs/serl_multistep_transfer_probe_20261026_v1/REVIEW.json')
for n in [driver,'serl_multistep_batch_transfer_20261026.py']:gather['source_hashes'][n]=sha(RT/n)
write(OUT/'REGISTRATION.json',p)
launch=json.loads((B/'runs'/oldname/'LAUNCH.json').read_text());cmd=list(launch['command']);cmd[1]=str(RT/driver)
for flag,value in [('--registration',OUT/'REGISTRATION.json'),('--resume',stage['checkpoint']['path']),('--output',OUT/'direct')]:cmd[cmd.index(flag)+1]=str(value)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(B/'runtime/jax_compilation_cache'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
with (OUT/'check_only.log').open('x') as log:subprocess.run(['taskset','-c','54']+cmd+['--check-only'],stdout=log,stderr=subprocess.STDOUT,check=True,env=env)
write(OUT/'CHECK_ONLY_COMPLETE.json',dict(passed=True,new_optimizer_updates=0,time=time.time()))
write(OUT/'COMMAND.json',dict(command=cmd));print(str(OUT),flush=True)
