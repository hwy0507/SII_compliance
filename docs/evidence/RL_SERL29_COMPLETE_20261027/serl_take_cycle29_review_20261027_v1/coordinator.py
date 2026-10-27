from pathlib import Path
import subprocess,os,json,time
p=Path(__file__).parent;b=p.parents[1]
os.sched_setaffinity(0,{52,53})
os.nice(15)
subprocess.run([str(b/'env/bin/python'),str(p/'review.py')],check=True)
subprocess.run([str(b/'serl_env/bin/python'),str(p/'diagnose.py')],check=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(b/'runtime/jax_compilation_cache')))
(p/'FINISHED.json').write_text(json.dumps(dict(time=time.time(),completed=True,convergence_claim=False))+'\n')
