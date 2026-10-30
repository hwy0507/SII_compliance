from pathlib import Path
import json,subprocess,time,sys,hashlib,os,traceback
D=Path(__file__).parent;B=D.parents[1];H=B/'runs/recovery85_history_reconstruction_20261030_v1';read=lambda p:json.loads(p.read_text());os.sched_setaffinity(0,{54})
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
try:
 for n in ['SAVED_REVIEW.json','PLOT_REVIEW.json']:assert not (H/n).exists()
 plan=read(H/'PLAN.json');deadline=plan['time']+2100
 sources={n:hashlib.sha256((H/n).read_bytes()).hexdigest() for n in ['review_saved.py','plot.py']}
 put(D/'HISTORY_REVIEW_LAUNCH.json',dict(time=time.time(),pid=os.getpid(),proc_start_ticks=Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()[19],wait_deadline=deadline,sources=sources,review_timeout_s=900,plot_timeout_s=60,new_physics=0,optimizer_updates=0))
 while not (H/'FINISHED.json').exists():
  assert not (H/'FAILURE.json').exists(),'Original history reconstruction failed'
  assert time.time()<deadline,'History audit wait deadline expired'
  time.sleep(5)
 assert read(H/'FINISHED.json')['passed']
 for n,timeout in [('review_saved.py',900),('plot.py',60)]:
  assert hashlib.sha256((H/n).read_bytes()).hexdigest()==sources[n]
  subprocess.run([sys.executable,str(H/n)],check=True,timeout=timeout)
 put(D/'HISTORY_REVIEW_FINISHED.json',dict(passed=True,time=time.time(),new_physics=0,optimizer_updates=0));print('History saved review and plot complete; image inspection still needed')
except BaseException as e:put(D/'HISTORY_REVIEW_FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
