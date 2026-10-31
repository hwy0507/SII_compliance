from pathlib import Path
import subprocess,time,sys,json,os,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/history89_violation_pipeline_preflight_20261030_v1'
plan=json.loads((D/'PLAN.json').read_text());ids={97370:'570509460',97399:'570509475',97400:'570509475',97401:'570509475',97402:'570509475',2675653:'575369491',2675660:'575369492',2675662:'575369492',2675665:'575369492',2713409:'575376596'}
def check():
 for pid,start in ids.items():
  s=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==start

def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
start=time.monotonic();count=0;children=[];child=None
check();put(O/'LAUNCH.json',dict(time=time.time(),supervisor_pid=os.getpid(),budget_seconds=plan['budget_seconds'],original_identities=ids))
def run(name,cmd):
 global child,count
 with (O/(name+'.log')).open('x') as log:
  child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(dict(name=name,pid=child.pid,command=cmd))
  while child.poll() is None:
   check();count+=1
   if time.monotonic()-start>plan['budget_seconds']:child.terminate();raise TimeoutError(name)
   time.sleep(5)
  assert child.returncode==0,(name,child.returncode);check()
try:
 run('pipeline',[sys.executable,'-u',str(D/'check_pipeline.py')]);run('prepare_consumers',[sys.executable,str(D/'prepare_consumers.py')])
 cp=json.loads((O/'CONSUMER_PLAN.json').read_text())
 for job in cp['commands']:run(job['name'],job['command'])
 put(O/'RUN_REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,identity_observations=count,original_identities=ids,jobs=children,physics_steps=0,formal_updates=0,clone_native_updates=6,training90=False))
except BaseException:
 if child and child.poll() is None:child.terminate()
 put(O/'RUN_FAILURE.json',dict(time=time.time(),traceback=traceback.format_exc(),jobs=children));raise
