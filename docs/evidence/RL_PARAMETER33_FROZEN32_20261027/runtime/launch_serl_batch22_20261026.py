from pathlib import Path
import json,os,subprocess,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
out=B/'runs/serl_multistep_batch65536_cycle22_20261026_v1'
review=B/'runs/serl_multistep_batch65536_cycle21_review_20261026_v1'
assert json.loads((review/'FINISHED.json').read_text())['completed']
assert json.loads((review/'REVIEW.json').read_text())['passed']
assert json.loads((out/'CHECK_ONLY_COMPLETE.json').read_text())['passed']
assert not (out/'LAUNCH.json').exists() and not Path('/proc/2826774').exists()
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(B/'runtime/jax_compilation_cache'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
cmd=json.loads((out/'COMMAND.json').read_text())['command']
with (out/'train.log').open('x') as log:p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
(out/'LAUNCH.json').write_text(json.dumps(dict(command=cmd,pid=p.pid,time=time.time()),indent=2)+'\n');print('learner',p.pid,flush=True)
subprocess.run(['python',str(B/'runtime/setup_serl_batch22_monitors_20261026.py')],check=True)
