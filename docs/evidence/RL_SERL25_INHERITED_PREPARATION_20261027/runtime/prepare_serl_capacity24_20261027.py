from pathlib import Path
import hashlib,json,shutil,subprocess,os,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
R=B/'repository/SII_compliance'
oldname='serl_multistep_batch65536_cycle23_20261026_v1'
name='serl_capacity_batch65536_cycle24_20261027_v1'
OUT=B/'runs'/name;RT=B/'runtime'/name
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def read(p):return json.loads(Path(p).read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
candidates=[B/'runs/serl_multistep_batch65536_cycle23_review_20261026_v1']
complete=[p for p in candidates if (p/'FINISHED.json').exists()]
assert len(complete)==1,'Require exactly one completed full23 scientific review'
review=complete[0];assert read(review/'FINISHED.json')['completed'] and read(review/'REVIEW.json')['passed']
cp=B/'runs/serl_multistep_batch65536_cycle23_archive_20261026_v1/direct/cycle_00023.pt'
assert read(review/'REVIEW.json')['methods']['direct']['checkpoint_sha256']==sha(cp)==read(review/'DIAGNOSIS.json')['checkpoint_sha256']
assert read(review/'DIAGNOSIS.json')['network_optimizer_rng_unchanged']
assert not Path('/proc/257351').exists(), 'Original23 learner must exit before reusing CPU0'
os.sched_setaffinity(0,{0})
OUT.mkdir();shutil.copytree(B/'runtime'/oldname,RT,ignore=shutil.ignore_patterns('__pycache__'))
driver='resume_serl_capacity_reviewed_continuation_20261027.py'
helper='serl_replay_capacity_20261027.py'
for filename in [driver,helper]:shutil.copyfile(R/'code/mujoco_6d_vmc_benchmark/tools'/filename,RT/filename)
parent=B/'runs'/oldname/'REGISTRATION.json';p=read(parent);p['resume_parent_registration']=ref(parent)
stage=p['reviewed_continuation_stage'];stage['parent_cycle']=23;stage['checkpoint']=ref(cp);stage['driver_sha256']=sha(RT/driver)
stage['cycle_review']=ref(review/'REVIEW.json');stage['health_review']=ref(review/'DIAGNOSIS.json')
stage['patched_main_sha256']=sha(B/'runs'/oldname/'SAMPLER_MAIN.py.txt')
p['gather_stage']['prepared_checkpoint']=stage['checkpoint'];p['gather_stage']['source_hashes'][driver]=sha(RT/driver)
# The original batch trial continues to refer to formal12 and the formal11
# comparison. It must not be relabelled as an experiment on the new parent13.
assert p['batch_size_stage']==read(parent)['batch_size_stage']
import sys,torch
sys.path[:0]=[str(RT),str(B/'runtime/serl_state_adapter_20261026_v1')]
from serl_replay_capacity_20261027 import MARKER
from validate_serl_state_20261026 import digest
preparation=B/'runs/serl_capacity_driver_preparation_20261027_v1/REVIEW.json'
replay_preparation=B/'runs/serl_replay_capacity_validation_20261027_v1/REVIEW.json'
d=read(preparation);assert d['passed'] and d['full_next_update_state_metrics_rng_exact'] and d['expanded_restore_next_batch_exact']
assert d['checkpoint']==read(parent)['reviewed_continuation_stage']['checkpoint']
assert d['driver_sha256']==sha(RT/driver) and d['helper_sha256']==sha(RT/helper)
assert d['replay_preparation_sha256']==sha(replay_preparation)
x=torch.load(cp,map_location='cpu',weights_only=False)
assert x['cycle']==23 and x['boundary']=='complete_condition_cycle'
assert x['steps']==x['replay']['size']==x['replay']['cursor']<1_000_000
assert x['replay']['capacity']==1_000_000 and 'replay_capacity_extension' not in x['replay']
p['replay_capacity_stage']=dict(marker=MARKER,parent_cycle=23,old_capacity=1_000_000,new_capacity=2_000_000,
 entry_checkpoint=ref(cp),entry_replay_digest=digest(x['replay']),helper_sha256=sha(RT/helper),
 replay_preparation_review=ref(replay_preparation),driver_preparation_review=ref(preparation),auxiliary_weights_imported=False)
p['gather_stage']['source_hashes'][helper]=sha(RT/helper)
stage['decision']='One finite cycle24 from exact full23 with append-only replay1m to2m. Frozen learner/optimizer/targets/physics/reward unchanged; all raw/derived rows and RNG retained. No ring-overwrite equivalence or convergence claim, no auxiliary weights.'
del x
write(OUT/'REGISTRATION.json',p)
cmd=list(read(B/'runs'/oldname/'LAUNCH.json')['command']);cmd[1]=str(RT/driver)
for flag,value in [('--registration',OUT/'REGISTRATION.json'),('--resume',cp),('--output',OUT/'direct')]:cmd[cmd.index(flag)+1]=str(value)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(B/'runtime/jax_compilation_cache'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
with (OUT/'check_only.log').open('x') as log:subprocess.run(['taskset','-c','0']+cmd+['--check-only'],stdout=log,stderr=subprocess.STDOUT,check=True,env=env)
write(OUT/'CHECK_ONLY_COMPLETE.json',dict(time=time.time(),passed=True,new_optimizer_updates=0))
write(OUT/'COMMAND.json',dict(command=cmd));print(OUT,flush=True)
