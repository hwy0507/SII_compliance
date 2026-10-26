from pathlib import Path
import subprocess,time,json,os
out=Path(__file__).parent;b=out.parents[1];os.sched_setaffinity(0,{52});deadline=time.monotonic()+3600
while not (out/'REVIEW.json').exists():
 if (out/'FAILURE.json').exists():raise RuntimeError('Original prefix probe failed; preserve it, no rerun')
 if time.monotonic()>deadline:raise RuntimeError('Original prefix probe observation deadline; inspect original handle')
 time.sleep(3)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(b/'runtime/jax_compilation_cache'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
subprocess.run([str(b/'serl_env/bin/python'),str(b/'runtime'/out.name/'review_serl_initial_noise_gate_20261026.py'),'--run',str(out)],check=True,env=env)
(out/'FINISHED.json').write_text(json.dumps(dict(time=time.time(),completed=True,convergence_claim=False))+'\n')
