from pathlib import Path
import os,subprocess,json,time
p=Path(__file__).parent;b=p.parents[1];os.sched_setaffinity(0,{52})
subprocess.run([str(b/'env/bin/python'),str(p/'review.py')],check=True)
e=dict(os.environ,CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(b/'runtime/jax_compilation_cache'))
subprocess.run([str(b/'serl_env/bin/python'),str(p/'diagnose.py')],check=True,env=e)
(p/'FINISHED.json').write_text(json.dumps(dict(completed=True,time=time.time())))
