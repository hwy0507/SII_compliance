from pathlib import Path
import hashlib,json,shutil,subprocess,os,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
R=B/'repository/SII_compliance'
oldname='serl_multistep_batch65536_cycle20_20261026_v1'
name='serl_multistep_batch65536_cycle21_20261026_v1'
OUT=B/'runs'/name;RT=B/'runtime'/name
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def read(p):return json.loads(Path(p).read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
candidates=[B/'runs/serl_multistep_batch65536_cycle20_review_20261026_v1']
complete=[p for p in candidates if (p/'FINISHED.json').exists()]
assert len(complete)==1,'Require exactly one completed full20 scientific review'
review=complete[0];assert read(review/'FINISHED.json')['completed'] and read(review/'REVIEW.json')['passed']
cp=B/'runs/serl_multistep_batch65536_cycle20_archive_20261026_v1/direct/cycle_00020.pt'
assert read(review/'REVIEW.json')['methods']['direct']['checkpoint_sha256']==sha(cp)==read(review/'DIAGNOSIS.json')['checkpoint_sha256']
assert read(review/'DIAGNOSIS.json')['network_optimizer_rng_unchanged']
assert not Path('/proc/46632').exists(), 'Original20 learner must exit before reusing CPU0'
os.sched_setaffinity(0,{0})
OUT.mkdir();shutil.copytree(B/'runtime'/oldname,RT,ignore=shutil.ignore_patterns('__pycache__'))
driver='resume_serl_batch65536_reviewed_continuation_20261026.py';shutil.copyfile(R/'code/mujoco_6d_vmc_benchmark/tools'/driver,RT/driver)
parent=B/'runs'/oldname/'REGISTRATION.json';p=read(parent);p['resume_parent_registration']=ref(parent)
stage=p['reviewed_continuation_stage'];stage['parent_cycle']=20;stage['checkpoint']=ref(cp);stage['driver_sha256']=sha(RT/driver)
stage['cycle_review']=ref(review/'REVIEW.json');stage['health_review']=ref(review/'DIAGNOSIS.json')
stage['decision']='One finite unchanged batch65536 cycle21 from latest reviewed formal20 to assess stability; Completed temperature and actor-floor candidates remain unpromoted; no repeat or extension. All formal learner/optimizer/replay/RNG retained; no auxiliary weights or convergence claim.'
stage['patched_main_sha256']=sha(B/'runs'/oldname/'SAMPLER_MAIN.py.txt')
p['gather_stage']['prepared_checkpoint']=stage['checkpoint'];p['gather_stage']['source_hashes'][driver]=sha(RT/driver)
# The original batch trial continues to refer to formal12 and the formal11
# comparison. It must not be relabelled as an experiment on the new parent13.
assert p['batch_size_stage']==read(parent)['batch_size_stage']
write(OUT/'REGISTRATION.json',p)
cmd=list(read(B/'runs'/oldname/'LAUNCH.json')['command']);cmd[1]=str(RT/driver)
for flag,value in [('--registration',OUT/'REGISTRATION.json'),('--resume',cp),('--output',OUT/'direct')]:cmd[cmd.index(flag)+1]=str(value)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(B/'runtime/jax_compilation_cache'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
with (OUT/'check_only.log').open('x') as log:subprocess.run(['taskset','-c','0']+cmd+['--check-only'],stdout=log,stderr=subprocess.STDOUT,check=True,env=env)
write(OUT/'CHECK_ONLY_COMPLETE.json',dict(time=time.time(),passed=True,new_optimizer_updates=0))
write(OUT/'COMMAND.json',dict(command=cmd));print(OUT,flush=True)
