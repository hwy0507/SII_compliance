from pathlib import Path
import os,sys,json,time,subprocess,hashlib,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation92_terminal_census_20261031_v1';plan=json.loads((O/'PLAN.json').read_text());assert hashlib.sha256((D/'census.py').read_bytes()).hexdigest()==plan['source_sha256']
children=[];jobs=[];start=time.monotonic()
try:
 for m,e in plan['methods'].items():
  log=(O/(m+'.log')).open('x');cmd=[sys.executable,'-u',str(D/'census.py'),'--method',m];p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'),start_new_session=True);children.append(p);stat=Path('/proc',str(p.pid),'stat').read_text().rsplit(')',1)[1].split();jobs.append(dict(method=m,pid=p.pid,start=stat[19],command=cmd,device=e['device'],cpu=e['cpu']))
 with (O/'LAUNCH.json').open('x') as f:json.dump(dict(time=time.time(),jobs=jobs,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),f,indent=2);f.write('\n')
 print(json.dumps(jobs),flush=True)
 while any(p.poll() is None for p in children):
  assert all(p.returncode in (None,0) for p in children),'probe failed; inspect preserved failure'
  if time.monotonic()-start>plan['budget_seconds']+30:raise TimeoutError('bounded diagnostic')
  time.sleep(2)
 assert all(p.returncode==0 for p in children)
 for m in plan['methods']:assert json.loads((O/(m+'_REVIEW.json')).read_text())['passed']
 with (O/'FINISHED.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,optimizer_updates=0,new_physics=0,actual_plot_review_pending=True),f,indent=2);f.write('\n')
 print('All3 terminal censuses completed; no optimizer updates.',flush=True)
except BaseException as e:
 for p in children:
  if p.poll() is None:p.terminate()
 with (O/'LAUNCH_FAILURE.json').open('x') as f:json.dump(dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()),f,indent=2)
 raise
