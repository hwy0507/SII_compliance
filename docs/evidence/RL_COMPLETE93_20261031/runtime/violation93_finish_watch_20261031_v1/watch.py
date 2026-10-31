from pathlib import Path
import json,time,traceback,hashlib
D=Path(__file__).resolve().parent;B=D.parents[1];T=B/'runs/parameter_violation_cycle93_20261031_v1';V=B/'runs/parameter_violation_cycle93_review_20261031_v1';F=B/'runs/violation93_fixed92_terminal_followup_20261031_v1';C=B/'runtime/violation93_completion_20261031_v1';G=Path('/tmp/sii_gpu_util_guard_20261030_v7')
read=lambda p:json.loads(p.read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def live(j):
 p=Path('/proc',str(j['pid']),'stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[0]!='Z' and s[19]==str(j.get('start',j.get('proc_start_ticks')))
plan=read(D/'WATCH_PLAN.json');assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==plan['source_sha256'];jobs=read(T/'LAUNCH.json')['jobs'];monitor=read(T/'MONITOR_LAUNCH.json');terminal=read(F/'PROCESS.json');comparison=read(C/'PROCESS.json');start=time.monotonic();rows=[]
try:
 with (D/'OBSERVATIONS.jsonl').open('x') as f:
  while True:
   assert all(live(j) for j in plan['guard_identities']) and not (G/'STOP').exists() and not (G/'FAILURE.json').exists()
   failures=list(F.glob('*FAILURE*'))+list(C.glob('COMPARISON_FAILURE_*'))+list(T.glob('ARCHIVE_REVIEW_FAILURE.json'))
   for m in ['impedance','admittance','vmc']:failures+=list((T/m).glob('DRIVER_FAILURE.json'))+list((T/m/'train').glob('FAILURE.json'))
   assert not failures,failures
   row=dict(time=time.time(),elapsed_s=time.monotonic()-start,training={})
   for j in jobs:
    m=j['controller'];end=T/m/'train/FINISHED.json';alive=live(j)
    if not alive:assert end.exists() and read(end)['status']=='stopped_at_complete_cycle'
    row['training'][m]=dict(live=alive,finished=end.exists(),progress=read(T/m/'train/PROGRESS.json'))
   done={}
   for label,j,target in [('archive',monitor,V/'FINISHED.json'),('terminals',terminal,F/'FINISHED.json'),('comparison',comparison,C/'COMPARISON_FINISHED.json')]:
    alive=live(j);done[label]=target.exists()
    if not alive:assert target.exists(),(label,j)
    row[label]=dict(live=alive,finished=target.exists())
   latest=json.loads((G/'samples.jsonl').read_text().splitlines()[-1]);assert time.time()-latest['time']<25;row['gpu']=latest
   rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
   print(json.dumps(dict(elapsed=round(row['elapsed_s']),steps={m:x['progress']['steps'] for m,x in row['training'].items()},finished=done,gpu=[x['utilization'] for x in latest['gpus']])),flush=True)
   if all(done.values()):break
   if time.monotonic()-start>=plan['duration_seconds']:break
   time.sleep(15)
 put(D/'WATCH_REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,samples=len(rows),full93_consumers_complete=all(done.values()),last=rows[-1],first=rows[0],scope='Verified wait accepting only explicit normal completion; no training launch, restart, update, or original deadline extension.'))
except BaseException as e:
 put(D/'WATCH_FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
