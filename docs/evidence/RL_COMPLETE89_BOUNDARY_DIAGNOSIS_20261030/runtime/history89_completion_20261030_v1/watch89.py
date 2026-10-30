from pathlib import Path
import json,time,hashlib,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];T=B/'runs/parameter_history_cycle89_20261030_v1';V=B/'runs/parameter_history_cycle89_review_20261030_v1';F=B/'runs/parameter88_history_frozen_full30_20261030_v1';O=B/'runs/history89_fixed87_terminal_followup_20261030_v1';P=B/'runtime/history88_frozen_postprocess_20261030_v1'
read=lambda p:json.loads(Path(p).read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def live(j):
 p=Path('/proc',str(j['pid']),'stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[0]!='Z' and s[19]==str(j.get('start',j.get('proc_start_ticks')))
try:
 plan=read(D/'WATCH_PLAN.json');assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==plan['source_sha256'];start=time.monotonic();end=start+plan['maximum_seconds'];rows=[]
 jobs=read(T/'LAUNCH.json')['jobs'];monitor=read(T/'MONITOR_LAUNCH.json');follow=read(O/'PROCESS.json');frozen=read(F/'LAUNCH.json')['jobs']+[read(F/'REVIEW_LAUNCH.json'),read(P/'PROCESS.json')];guards=[dict(pid=pid,start=start) for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]]
 with (D/'OBSERVATIONS.jsonl').open('x') as out:
  while True:
   assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not list(O.glob('*FAILURE*.json'))
   for j in frozen+guards:assert live(j),j
   methods={}
   for j in jobs:
    m=j['controller'];run=T/m/'train';assert not (run/'FAILURE.json').exists() and not (run.parent/'DRIVER_FAILURE.json').exists()
    if (run/'FINISHED.json').exists():
     finish=read(run/'FINISHED.json');assert finish['status']=='stopped_at_complete_cycle';methods[m]=dict(status='normal_complete_cycle',progress=read(run/'PROGRESS.json'),finished=finish)
    else:assert live(j),j;methods[m]=dict(status='running',progress=read(run/'PROGRESS.json'))
   full=(V/'FINISHED.json').exists();fixed=(O/'FINISHED.json').exists()
   if full:assert read(V/'FINISHED.json')['completed']
   else:assert live(monitor)
   if fixed:assert read(O/'FINISHED.json')['passed']
   else:assert live(follow)
   sample=Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl')
   with sample.open('rb') as f:f.seek(max(0,sample.stat().st_size-8192));raw=f.read().splitlines()
   gpu=json.loads(raw[-1]);assert time.time()-gpu['time']<25
   row=dict(time=time.time(),elapsed_s=time.monotonic()-start,methods=methods,complete89_review=full,fixed87_followup=fixed,frozen_progress={j['controller']:read(F/j['controller']/'PROGRESS.json') for j in frozen if 'controller' in j},gpu=gpu)
   rows.append(row);out.write(json.dumps(row)+'\n');out.flush()
   if len(rows)%2==1:print(json.dumps(dict(elapsed=round(row['elapsed_s']),steps={m:v['progress']['steps'] for m,v in methods.items()},statuses={m:v['status'] for m,v in methods.items()},review=full,followup=fixed,gpu=[g['utilization'] for g in gpu['gpus']])),flush=True)
   if full and fixed:break
   if time.monotonic()>=end:break
   time.sleep(plan['interval_seconds'])
 put(D/'WATCH_REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,samples=len(rows),completed89_review=full,completed_fixed87_followup=fixed,observation_timeout_not_terminal=not(full and fixed),last=rows[-1],automatic90=False))
except BaseException as e:put(D/'WATCH_FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
