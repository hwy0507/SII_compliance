from pathlib import Path
import hashlib,json,time,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];F=B/'runs/parameter88_history_frozen_full30_20261030_v1'
read=lambda p:json.loads(p.read_text())
def live(pid,start):
 p=Path('/proc',str(pid),'stat')
 if not p.exists():return False
 v=p.read_text().rsplit(')',1)[1].split();return v[0]!='Z' and v[19]==str(start)
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
started=time.monotonic();jobs=[(97370,570509460),(97399,570509475),(97400,570509475),(97401,570509475),(97402,570509475),(2675653,575369491),(2675660,575369492),(2675662,575369492),(2675665,575369492),(2713409,575376596)];launch=read(D/'PROCESS.json');count=0
try:
 with (D/'OBSERVATIONS.jsonl').open('x') as out:
  while True:
   assert all(live(p,s) for p,s in jobs),'Original frozen/guard identity changed; inspect before any restart'
   assert not list(D.glob('*FAILURE*.json'))
   finished=(D/'RUN_FINISHED.json').exists()
   if finished:assert read(D/'RUN_FINISHED.json')['passed']
   else:assert live(launch['pid'],launch['start']),'Original paired-fit supervisor missing without completion'
   assert time.monotonic()-started<1200,'Observation deadline, not permission to restart or extend fitting'
   lines=Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines();gpu=next(json.loads(x) for x in reversed(lines) if x.endswith('}'));assert time.time()-gpu['time']<25
   progress={}
   for method in ('impedance','admittance','vmc'):
    p=D/(method+'_curve.jsonl');progress[method]=None
    if p.exists():
     lines=p.read_text().splitlines();progress[method]=next((json.loads(x)['step'] for x in reversed(lines) if x.endswith('}')),None)
   row=dict(time=time.time(),elapsed_s=time.monotonic()-started,original10_identities_live=True,fit_finished=finished,fit_steps=progress,frozen={m:read(F/m/'PROGRESS.json') for m in progress},gpu=gpu)
   out.write(json.dumps(row)+'\n');out.flush();count+=1
   if finished:break
   time.sleep(10)
 put(D/'OBSERVATION_REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-started,samples=count,last=row,original_live_identities=[dict(pid=p,start=str(s)) for p,s in jobs],fit_completed_normally=True,automatic90=False))
except BaseException as e:put(D/('OBSERVATION_FAILURE_'+str(time.time_ns())+'.json'),dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
