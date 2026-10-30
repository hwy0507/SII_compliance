from pathlib import Path
import hashlib,json,subprocess,time,traceback
D=Path(__file__).resolve().parent;B=D.parents[1]
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
try:
 plan=json.loads((D/'PLAN.json').read_text());assert plan['new_optimizer_updates']==plan['new_physics']==0
 assert not (D/'REVIEW.json').exists() and not list(D.glob('*_causal_history.npy'))
 for script,timeout in [('build.py',plan['budget_seconds']+30),('review_saved.py',180)]:
  with (D/(script+'.log')).open('x') as log:
   p=subprocess.Popen([str(B/'env/bin/python'),'-u',str(D/script)],stdout=log,stderr=subprocess.STDOUT)
   stat=Path('/proc',str(p.pid),'stat').read_text().rsplit(')',1)[1].split()
   put(D/(script+'_PROCESS.json'),dict(time=time.time(),pid=p.pid,start=stat[19],source_sha256=sha(D/script),timeout_seconds=timeout))
   try:status=p.wait(timeout=timeout)
   except subprocess.TimeoutExpired:p.kill();p.wait();raise
   assert status==0,(script,status)
 assert json.loads((D/'FINISHED.json').read_text())['passed']
 put(D/'RUN_FINISHED.json',dict(passed=True,time=time.time(),plan_sha256=sha(D/'PLAN.json'),finished_sha256=sha(D/'FINISHED.json'),no_promotion=True))
except BaseException as exc:put(D/('RUN_FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(exc),traceback=traceback.format_exc()));raise
