from pathlib import Path
import os,json,subprocess,time
out=Path(__file__).parent
os.sched_setaffinity(0,{54})
reg=json.loads((out/'REGISTRATION.json').read_text())
deadline=time.monotonic()+600
while not Path(reg['wait_for_profile']).exists():
 if time.monotonic()>deadline:raise RuntimeError('Original profile has not finished; inspect it, do not rerun')
 time.sleep(1)
profile=json.loads(Path(reg['wait_for_profile']).read_text())
assert len(profile['samples'])==180
cmd=json.loads((out/'COMMAND.json').read_text())
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR='/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/jax_compilation_cache',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
with (out/'audit.log').open('x') as log:p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
(out/'AUDITOR_LAUNCH.json').write_text(json.dumps(dict(pid=p.pid,command=cmd,time=time.time()))+'\n')
if p.wait()!=0:raise RuntimeError('Read-only preference diagnosis failed; preserve original evidence')
(out/'FINISHED.json').write_text(json.dumps(dict(time=time.time(),new_physics=0,new_optimizer_updates=0))+'\n')
