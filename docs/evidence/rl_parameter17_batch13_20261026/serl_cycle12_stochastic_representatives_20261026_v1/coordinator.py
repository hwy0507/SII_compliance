from pathlib import Path
import os,json,hashlib,subprocess,time
out=Path(__file__).parent;b=out.parents[1];reg=json.loads((out/'REGISTRATION.json').read_text());os.sched_setaffinity(0,{reg['cpu']});os.nice(19)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
deadline=time.monotonic()+1800
while not Path(reg['wait_for_profile']).exists():
 if time.monotonic()>deadline:raise RuntimeError('Original pure-formal profile is pending; inspect original handles')
 time.sleep(2)
assert len(json.loads(Path(reg['wait_for_profile']).read_text())['samples'])==180
assert sha(reg['required_review'])==reg['required_review_sha256'];review=json.loads(Path(reg['required_review']).read_text());assert review['passed'] and review['methods']['direct']['checkpoint_sha256']==sha(reg['checkpoint'])==reg['checkpoint_sha256']
rt=Path(reg['audit_runtime'])
for name,h in reg['source_hashes'].items():assert sha(rt/name)==h
assert sha(out/'review_complete.py')==reg['reviewer_sha256'] and sha(__file__)==reg['coordinator_sha256']
cmd=[str(b/'serl_env/bin/python'),str(rt/'evaluate_serl_seeded_multistep_20261026.py'),'--runtime',reg['runtime'],'--registration',reg['training_registration'],'--checkpoint',reg['checkpoint'],'--output',str(out/'evaluation'),'--device','cuda:0','--learner-cpu',str(reg['cpu']),'--physics-cpu',str(reg['cpu']),'--audit-substeps','--stochastic','--action-seed',str(reg['action_seed']),'--serl-upstream',str(b/'runtime/serl_upstream_1fa2af7'),'--serl-manifest',str(b/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json'),'--sampler-python',str(b/'env/bin/python')]
for case in reg['case_ids']:cmd+=['--case-id',case]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(b/'runtime/jax_compilation_cache'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
with (out/'evaluator.log').open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env)
(out/'EVALUATOR_LAUNCH.json').write_text(json.dumps(dict(pid=p.pid,command=cmd,time=time.time()),indent=2)+'\n')
if p.wait()!=0:raise RuntimeError('Frozen stochastic evaluation failed; retain all evidence')
subprocess.run([str(b/'serl_env/bin/python'),str(out/'review_complete.py')],check=True,env=env)
(out/'FINISHED.json').write_text(json.dumps(dict(time=time.time(),scientific_review_complete=True,optimizer_updates=0,convergence_claim=False))+'\n')
