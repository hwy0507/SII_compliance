from pathlib import Path
import json,os,subprocess,time
O=Path(__file__).parent;B=O.parents[1]
try:
 env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='')
 cmd=[str(B/'env/bin/python'),str(B/'runtime'/O.name/'validate_parameter_replay_capacity4m_20261027.py'),'--registration',str(O/'REGISTRATION.json'),'--output',str(O)]
 with (O/'audit.log').open('x') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=600)
 assert r.returncode==0,r.returncode
 assert json.loads((O/'REVIEW.json').read_text())['passed']
 (O/'FINISHED.json').write_text(json.dumps(dict(time=time.time(),passed=True,formal_deployment=False))+'\n')
except BaseException as e:
 (O/'SUPERVISOR_FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)))+'\n');raise
