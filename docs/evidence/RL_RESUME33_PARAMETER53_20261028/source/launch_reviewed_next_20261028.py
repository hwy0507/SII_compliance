from pathlib import Path
import os,json,time,hashlib,shutil,subprocess,sys
b=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');kind=sys.argv[1];direct=kind=='serl_take';cycle=33 if direct else 53;date='20261027' if direct else '20261026';out=b/'runs'/f'{kind}_cycle{cycle}_{date}_v1'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
assert not (out/'LAUNCH.json').exists()
assert json.loads((out/('CHECK_ONLY_REVIEW.json' if direct else 'CHECK_ONLY_COMPLETE.json')).read_text())['passed']
review=out/('PRELAUNCH_REVIEW.json' if direct else 'PRELAUNCH_SCIENTIFIC_REVIEW.json');r=json.loads(review.read_text());r.update(plot_inspected=True,loss_review=dict(path=str(b/'runs/resume_loss_review_20261028_v1/REVIEW.json'),sha256=sha(b/'runs/resume_loss_review_20261028_v1/REVIEW.json')),scientific_assessment='Direct32 loss stable; I52 loss decreases, V52 critic bounded with actor drift, A52 late critic loss rise retained and requires tracking. Parameter49-51 reward stability fails. One unchanged finite cycle for further evidence; no full convergence claim.');write(review,r)
jobs=[dict(controller='direct',command=json.loads((out/'COMMAND.json').read_text())['command'])] if direct else json.loads((out/'COMMANDS.json').read_text())['jobs']
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
if direct:env.update(CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(b/'runtime/jax_compilation_cache'))
for job in jobs:
 log=out/(job['controller']+'_driver.log');p=subprocess.Popen(job['command'],stdout=log.open('x'),stderr=subprocess.STDOUT,env=env,start_new_session=True)
 job.update(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().split(') ')[1].split()[19],time=time.time(),log=str(log))
write(out/'LAUNCH.json',dict(time=time.time(),jobs=jobs,env_overrides={k:env[k] for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']},new_cycles=1,automatic_followup=False))
monitor=out/'archive_review.py';shutil.copyfile('/tmp/archive_review_next_20261028.py',monitor)
p=subprocess.Popen([str(b/'env/bin/python'),str(monitor),kind,str(cycle)],stdout=(out/'archive_review.log').open('x'),stderr=subprocess.STDOUT,env=env,start_new_session=True)
write(out/'MONITOR_LAUNCH.json',dict(pid=p.pid,time=time.time(),script_sha256=sha(monitor)))
print(json.dumps(dict(jobs=jobs,monitor_pid=p.pid),indent=2))
