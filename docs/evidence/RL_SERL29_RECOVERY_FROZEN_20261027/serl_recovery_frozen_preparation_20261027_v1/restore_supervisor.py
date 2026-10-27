from pathlib import Path
import json,subprocess,os,time,signal
O=Path(__file__).parent;os.sched_setaffinity(0,{52});plan=json.loads((O/'RESTORE_PLAN.json').read_text())
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',JAX_PLATFORMS='cuda',XLA_PYTHON_CLIENT_PREALLOCATE='false',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
try:
 with (O/'restore27_v1.log').open('x') as log:p=subprocess.Popen(plan['command'],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 (O/'RESTORE_WORKER.json').write_text(json.dumps(dict(pid=p.pid,time=time.time(),command=plan['command']))+'\n')
 try:code=p.wait(timeout=plan['timeout_seconds'])
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
  raise
 assert code==0,code
 review=json.loads((O/'restore27_v1/CHECK_ONLY_REVIEW.json').read_text());assert review['passed'] and review['cycle']==27 and review['checkpoint_sha256']==plan['checkpoint_sha256']
 (O/'RESTORE_FINISHED.json').write_text(json.dumps(dict(time=time.time(),passed=True,actual27_restore=True,actual29_restore=False,new_physics=0,optimizer_updates=0))+'\n')
except BaseException as e:
 (O/'RESTORE_FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)))+'\n');raise
