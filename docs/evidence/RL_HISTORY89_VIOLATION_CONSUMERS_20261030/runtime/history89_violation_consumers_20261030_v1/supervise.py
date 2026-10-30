from pathlib import Path
import sys,subprocess,time,json,traceback
D=Path(__file__).resolve().parent
stage=sys.argv[1];plan=json.loads((D/(stage.upper()+'_PLAN.json')).read_text());script={'cache':'check_cache_and_saved.py','consumer':'check_consumers.py'}[stage]
identities={97370:'570509460',97399:'570509475',97400:'570509475',97401:'570509475',97402:'570509475',2675653:'575369491',2675660:'575369492',2675662:'575369492',2675665:'575369492',2713409:'575376596'}
def check():
 for pid,start in identities.items():
  s=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==start,(pid,s)
def put(name,x):
 with (D/name).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
check();start=time.monotonic();p=None
try:
 with (D/(stage+'.log')).open('x') as log:
  p=subprocess.Popen([sys.executable,'-u',str(D/script)],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  put(stage.upper()+'_LAUNCH.json',dict(time=time.time(),pid=p.pid,plan=stage.upper()+'_PLAN.json',budget=plan['budget_seconds'],supervisor_pid=__import__('os').getpid(),original_identities=identities))
  count=0
  while p.poll() is None:
   check();count+=1
   if time.monotonic()-start>plan['budget_seconds']:p.terminate();raise TimeoutError(stage)
   time.sleep(5)
  assert p.returncode==0,p.returncode;check()
 put(stage.upper()+'_OBSERVATION_REVIEW.json',dict(passed=True,returncode=p.returncode,elapsed_s=time.monotonic()-start,identity_observations=count,original_identities=identities))
except BaseException:
 if p is not None and p.poll() is None:p.terminate()
 put(stage.upper()+'_SUPERVISOR_FAILURE.json',dict(traceback=traceback.format_exc(),elapsed_s=time.monotonic()-start));raise
