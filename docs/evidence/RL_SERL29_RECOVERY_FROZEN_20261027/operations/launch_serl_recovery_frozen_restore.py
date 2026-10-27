from pathlib import Path
import json,time,subprocess,os,hashlib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/serl_recovery_frozen_preparation_20261027_v1';RT=B/'runtime'/O.name
p=B/'runs/serl_recovery26_take27_20261027_v1/REGISTRATION.json';cp=B/'runs/serl_recovery26_take27_archive_20261027_v1/direct/cycle_00027.pt';review=json.loads((B/'runs/serl_recovery26_take27_review_20261027_v1/REVIEW.json').read_text());assert review['passed']
cmd=['taskset','-c','52-54','nice','-n','15',str(B/'serl_env/bin/python'),str(RT/'evaluate_serl_recovery_frozen_20261027.py'),'--runtime',str(B/'runtime/source_train17_clock'),'--registration',str(p),'--checkpoint',str(cp),'--expected-cycle','27','--output',str(O/'restore27_v1'),'--device','cuda:0','--learner-cpu','52','--physics-cpu','53','--serl-upstream',str(B/'runtime/serl_upstream_1fa2af7'),'--serl-manifest',str(B/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json'),'--sampler-python',str(B/'env/bin/python'),'--stochastic','--action-seed','2026102626','--audit-substeps','--check-only']
(O/'RESTORE_PLAN.json').write_text(json.dumps(dict(time=time.time(),cycle=27,command=cmd,checkpoint_sha256=review['methods']['direct']['checkpoint_sha256'],timeout_seconds=600,new_physics=0,optimizer_updates=0,formal_policy_modified=False,scope='Actual complete27 restoration validation for new recovery-aware evaluator only; not frozen physical27 or actual29 restore'),indent=2)+'\n')
s='''from pathlib import Path
import json,subprocess,os,time,signal
O=Path(__file__).parent;os.sched_setaffinity(0,{52});plan=json.loads((O/'RESTORE_PLAN.json').read_text())
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',JAX_PLATFORMS='cuda',XLA_PYTHON_CLIENT_PREALLOCATE='false',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
try:
 with (O/'restore27_v1.log').open('x') as log:p=subprocess.Popen(plan['command'],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 (O/'RESTORE_WORKER.json').write_text(json.dumps(dict(pid=p.pid,time=time.time(),command=plan['command']))+'\\n')
 try:code=p.wait(timeout=plan['timeout_seconds'])
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
  raise
 assert code==0,code
 review=json.loads((O/'restore27_v1/CHECK_ONLY_REVIEW.json').read_text());assert review['passed'] and review['cycle']==27 and review['checkpoint_sha256']==plan['checkpoint_sha256']
 (O/'RESTORE_FINISHED.json').write_text(json.dumps(dict(time=time.time(),passed=True,actual27_restore=True,actual29_restore=False,new_physics=0,optimizer_updates=0))+'\\n')
except BaseException as e:
 (O/'RESTORE_FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)))+'\\n');raise
'''
(O/'restore_supervisor.py').write_text(s)
with (O/'supervisor.log').open('x') as log:proc=subprocess.Popen([str(B/'env/bin/python'),str(O/'restore_supervisor.py')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(O/'RESTORE_LAUNCH.json').write_text(json.dumps(dict(pid=proc.pid,time=time.time(),command=[str(B/'env/bin/python'),str(O/'restore_supervisor.py')]),indent=2)+'\n');print('restore supervisor',proc.pid)
