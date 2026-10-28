from pathlib import Path
import json,hashlib,copy,shutil,subprocess,os,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
name='serl_take_cycle34_20261027_v1'; OUT=B/'runs'/name; RT=B/'runtime'/name
prevdir=B/'runs/serl_take_cycle33_20261027_v1'; prevreg=prevdir/'REGISTRATION.json'; arc=B/'runs/serl_take_cycle33_archive_20261027_v1/direct/cycle_00033.pt'; review=B/'runs/serl_take_cycle33_review_20261027_v1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
 return h.hexdigest()
def ref(p): return {'path':str(p),'sha256':sha(p)}
def write(p,d): Path(p).write_text(json.dumps(d,indent=2)+'\n')
assert review.joinpath('REVIEW.json').exists() and review.joinpath('DIAGNOSIS.json').exists()
assert not OUT.exists()
shutil.copytree(B/'runtime/serl_take_cycle33_20261027_v1',RT,ignore=shutil.ignore_patterns('__pycache__'))
OUT.mkdir()
p=json.loads(prevreg.read_text()); stage=copy.deepcopy(p['recovery_continuation_stage'])
stage.update(parent_cycle=33,new_cycle=34,parent_registration=ref(prevreg),checkpoint=ref(arc),cycle_review=ref(review/'REVIEW.json'),health_review=ref(review/'DIAGNOSIS.json'))
stage['runtime']=str(RT)
stage['reason']='One finite complete33 to34 continuation, preserving all state and original quarantine.'
p['recovery_continuation_stage']=stage
write(OUT/'REGISTRATION.json',p)
decision={'passed':True,'parent_cycle':33,'new_cycle':34,'new_cycles':1,'maximum_new_actions':41250,'maximum_physical_substeps':33000000,'automatic_followup':False,'auxiliary_weights_imported':False,'optimizer_settings_changed':False,'checkpoint':stage['checkpoint'],'review':stage['cycle_review'],'health':stage['health_review'],'reason':'Continue latest complete Direct33 for one finite unchanged cycle34; retain all replay/RNG/history and 930 quarantined pending tails; no convergence claim.'}
cmd=[str(B/'serl_env/bin/python'),str(RT/'resume_serl_take_recovery_continuation_20261027.py'),'--runtime',str(B/'runtime/source_train17_clock'),'--registration',str(OUT/'REGISTRATION.json'),'--resume',str(arc),'--output',str(OUT/'direct'),'--serl-upstream',str(B/'runtime/serl_upstream_1fa2af7'),'--serl-manifest',str(B/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json'),'--sampler-python',str(B/'env/bin/python'),'--device','cuda:0','--cpus','0,1,2,3,4,5,6,7,8,9,10,11,12','--workers','30']
write(OUT/'COMMAND.json',{'command':cmd})
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(B/'runtime/jax_compilation_cache'))
log=(OUT/'check_only.log').open('w'); pproc=subprocess.run(['taskset','-c','0']+cmd+['--check-only'],stdout=log,stderr=subprocess.STDOUT,env=env)
write(OUT/'CHECK_ONLY_EXIT.json',{'exit_code':pproc.returncode,'time':time.time()})
if pproc.returncode: raise SystemExit(pproc.returncode)
assert json.loads((OUT/'CHECK_ONLY_REVIEW.json').read_text())['passed']
write(OUT/'PREPARATION_REVIEW.json',dict(decision,time=time.time(),registration_sha256=sha(OUT/'REGISTRATION.json'),check_only=ref(OUT/'CHECK_ONLY_REVIEW.json')))
print(json.dumps({'out':str(OUT),'registration_sha256':sha(OUT/'REGISTRATION.json'),'command':cmd},indent=2))
