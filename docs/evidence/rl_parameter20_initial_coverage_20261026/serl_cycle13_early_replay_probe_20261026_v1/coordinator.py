from pathlib import Path
import os,json,subprocess,time
out=Path(__file__).parent
os.sched_setaffinity(0,{54})
reg=json.loads((out/'REGISTRATION.json').read_text());deadline=time.monotonic()+1800
while not Path(reg['wait_for_profile']).exists():
 if time.monotonic()>deadline:raise RuntimeError('Original registered profile pending; no duplicate probe')
 time.sleep(2)
profile=json.loads(Path(reg['wait_for_profile']).read_text());assert len(profile['samples'])==180
assert all(v['original_live_all_samples'] for v in profile['summary'].values())
cmd=json.loads((out/'COMMAND.json').read_text())
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR='/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/jax_compilation_cache',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
with (out/'probe.log').open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env)
(out/'PROBE_LAUNCH.json').write_text(json.dumps(dict(pid=p.pid,command=cmd,time=time.time()))+'\n')
code=p.wait()
if code:raise RuntimeError('Probe failed; preserve receipt, no automatic rerun: '+str(code))
assert json.loads((out/'REVIEW.json').read_text())['passed']
(out/'FINISHED.json').write_text(json.dumps(dict(time=time.time(),completed=True,independent_review_pending=True))+'\n')
