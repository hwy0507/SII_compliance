from pathlib import Path
import os,sys,json,subprocess,time,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle94_20261031_v1'
read=lambda p:json.loads(p.read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def identity(pid):return int(Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19])
start=time.monotonic();budget=read(D/'PREFLIGHT_PLAN.json')['budget_seconds'];jobs={};children=[];env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
try:
 with (D/'contract.log').open('x') as log:subprocess.run([sys.executable,'-u',str(D/'check_contract.py')],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=budget,env=env)
 for j in read(R/'COMMANDS.json')['jobs']:
  m=j['controller'];log=(D/(m+'_preflight.log')).open('x');p=subprocess.Popen(j['command']+['--check-only'],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True);children.append(p);jobs[m]=dict(pid=p.pid,start_ticks=identity(p.pid),command=j['command']+['--check-only'])
 put(D/'PREFLIGHT_PROCESSES.json',dict(time=time.time(),jobs=jobs))
 while any(p.poll() is None for p in children):
  if time.monotonic()-start>budget:raise TimeoutError('preflight')
  assert all(p.returncode in (None,0) for p in children);time.sleep(5)
 assert all(p.returncode==0 for p in children)
 for m in jobs:assert read(R/m/'CHECK_ONLY_REVIEW.json')['passed']
 put(D/'PREFLIGHT_FINISHED.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,clone_updates=6,formal_updates=0,physics=0))
except BaseException:
 for p in children:
  if p.poll() is None:p.terminate()
 put(D/'PREFLIGHT_FAILURE.json',dict(time=time.time(),traceback=traceback.format_exc()));raise
