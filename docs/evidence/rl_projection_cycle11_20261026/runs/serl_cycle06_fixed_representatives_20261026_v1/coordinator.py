from pathlib import Path
import os,json,hashlib,subprocess,time
out=Path(__file__).parent;b=out.parents[1]
os.sched_setaffinity(0,{54})
reg=json.loads((out/'REGISTRATION.json').read_text())
deadline=time.monotonic()+3600
while not Path(reg['required_review']).exists():
 if time.monotonic()>deadline:raise RuntimeError('Complete cycle6 review not available within observation budget')
 time.sleep(2)
review=json.loads(Path(reg['required_review']).read_text());assert review['passed']
row=review['methods']['direct'];cp=Path(reg['checkpoint'])
with cp.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['checkpoint_sha256']
rt=b/'runtime/serl_cycle06_fixed_representatives_20261026_v1'
for name,digest in reg['source_hashes'].items():assert hashlib.sha256((rt/name).read_bytes()).hexdigest()==digest
cmd=[str(b/'serl_env/bin/python'),str(rt/'evaluate_serl_state_20261026.py'),'--runtime',reg['runtime'],'--registration',reg['training_registration'],'--checkpoint',str(cp),'--output',str(out/'evaluation'),'--device','cuda:0','--learner-cpu','54','--physics-cpu','54','--audit-substeps','--serl-upstream',str(b/'runtime/serl_upstream_1fa2af7'),'--serl-manifest',str(b/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json'),'--sampler-python',str(b/'env/bin/python')]
for case in reg['case_ids']:cmd+=['--case-id',case]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(b/'runtime/jax_compilation_cache'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONPATH=str(b/'runtime/source_train17_clock/source/tools'))
with (out/'evaluator.log').open('x') as log:child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
(out/'EVALUATOR_LAUNCH.json').write_text(json.dumps({'pid':child.pid,'command':cmd,'checkpoint_sha256':row['checkpoint_sha256'],'time':time.time()},indent=2)+'\n')
if child.wait()!=0:raise RuntimeError('Frozen evaluator failed; retain evidence')
for case in reg['case_ids']:
 folder=out/'evaluation'/case
 commands=[('summarize_published_episode_audit_20261025.py',['--method','direct','--case-id',case],'PHYSICS_REVIEW.json'),('replay_published_filter_audit_20261025.py',[],'FILTER_REVIEW.json'),('replay_published_torque_audit_20261025.py',[],'TORQUE_REVIEW.json')]
 for script,extra,name in commands:
  subprocess.run([str(b/'env/bin/python'),str(rt/script),'--episode',str(folder),'--output',str(folder/name)]+extra,check=True,env=env)
(out/'PHYSICAL_AUDITS_COMPLETE.json').write_text(json.dumps(dict(time=time.time(),episodes=3,optimizer_updates=0))+'\n')
subprocess.run([str(b/'serl_env/bin/python'),str(out/'review_complete.py')],check=True,env=env)
(out/'FINISHED.json').write_text(json.dumps(dict(time=time.time(),episodes=3,optimizer_updates=0,scientific_review_complete=True,convergence_claim=False))+'\n')
