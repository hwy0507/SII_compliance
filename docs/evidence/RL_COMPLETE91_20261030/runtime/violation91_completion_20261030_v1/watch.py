from pathlib import Path
import json,time,traceback,os
D=Path(__file__).resolve().parent;B=D.parents[1];T=B/'runs/parameter_violation_cycle91_20261030_v1';O=B/'runs/parameter_violation_cycle91_review_20261030_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';N=B/'runs/violation91_fixed87_terminal_followup_20261030_v1';P=B/'runtime/violation90_frozen_postprocess_20261030_v1'
read=lambda p:json.loads(p.read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def live(j):
 p=Path('/proc',str(j['pid']),'stat')
 if not p.exists():return False
 f=p.read_text().rsplit(')',1)[1].split();return f[0]!='Z' and f[19]==str(j.get('start',j.get('proc_start_ticks')))
os.sched_setaffinity(0,{54});jobs=read(T/'LAUNCH.json')['jobs'];archive=read(T/'MONITOR_LAUNCH.json');waiter=read(N/'PROCESS.json');fixed=read(F/'LAUNCH.json')['jobs']+[read(F/'REVIEW_LAUNCH.json'),read(P/'PROCESS.json')]+[dict(pid=p,start=s) for p,s in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]]
identities=jobs+[archive,waiter]+fixed
for j in identities:assert live(j)
put(D/'WATCH_PLAN.json',dict(time=time.time(),duration_seconds=2400,interval_seconds=10,identities=identities,scope='Wait original91 including normal completion; no restart or job-deadline extension',normal_exit_requires_actual_finished_receipt=True))
start=time.monotonic();count=0
try:
 with (D/'OBSERVATIONS.jsonl').open('x') as out:
  while True:
   assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not list(N.glob('WAIT_FAILURE*')) and not list(N.glob('FAILURE_*'))
   for j in fixed:assert live(j),j
   states={}
   for j in jobs:
    m=j['controller'];r=T/m/'train';assert not (r/'FAILURE.json').exists() and not (r.parent/'DRIVER_FAILURE.json').exists()
    running=live(j);finish=read(r/'FINISHED.json') if (r/'FINISHED.json').exists() else None
    if not running:assert finish and finish['status']=='stopped_at_complete_cycle'
    states[m]=dict(alive=running,progress=read(r/'PROGRESS.json'),finished=finish,children=len(Path('/proc',str(j['pid']),'task',str(j['pid']),'children').read_text().split()) if running else 0)
   archive_live=live(archive);waiter_live=live(waiter)
   if not archive_live:assert read(O/'FINISHED.json')['completed']
   if not waiter_live:assert read(N/'FINISHED.json')['passed']
   ready=(O/'FINISHED.json').exists() and (N/'FINISHED.json').exists()
   row=dict(time=time.time(),elapsed_s=time.monotonic()-start,training=states,archive_alive=archive_live,terminal_waiter_alive=waiter_live,frozen={m:read(F/m/'PROGRESS.json') for m in states},complete_reviews_ready=ready)
   out.write(json.dumps(row)+'\n');out.flush();count+=1
   if ready or time.monotonic()-start>=2400:break
   time.sleep(10)
 put(D/'WATCH_REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,samples=count,identities=identities,last=row,complete_reviews_ready=ready,goal='active'))
 print('Observation finished; complete91 reviews ready:',ready)
except BaseException as e:put(D/'WATCH_FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
