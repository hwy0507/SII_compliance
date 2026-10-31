from pathlib import Path
import hashlib,json,time,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];T=B/'runs/parameter_violation_cycle93_20261031_v1';F=B/'runs/violation93_fixed92_terminal_followup_20261031_v1'
read=lambda p:json.loads(Path(p).read_text())
def ident(pid):
 s=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z';return dict(pid=pid,start=s[19])
def live(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['start']
try:
 plan=read(D/'OBSERVATION_PLAN.json');assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==plan['source_sha256']
 jobs=read(T/'LAUNCH.json')['jobs'];ids=jobs+[read(T/'MONITOR_LAUNCH.json'),read(F/'PROCESS.json'),read(B/'runtime/violation93_completion_20261031_v1/PROCESS.json')]
 for j in jobs:
  children=list(map(int,Path('/proc',str(j['pid']),'task',str(j['pid']),'children').read_text().split()));assert len(children)==30;ids.extend(ident(pid) for pid in children)
 for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]:ids.append(dict(pid=pid,start=start))
 ids=[dict(pid=j['pid'],start=str(j.get('start',j.get('proc_start_ticks')))) for j in ids];start=time.monotonic();rows=[]
 with (D/'OBSERVATIONS.jsonl').open('x') as out:
  while True:
   for j in ids:live(j)
   assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not list(F.glob('*FAILURE*')) and not list((B/'runtime/violation93_completion_20261031_v1').glob('COMPARISON_FAILURE_*'))
   steps={}
   for m in ['impedance','admittance','vmc']:
    assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists();steps[m]=read(T/m/'train/PROGRESS.json')['steps']
   row=dict(time=time.time(),elapsed_s=time.monotonic()-start,steps=steps,identity_count=len(ids));rows.append(row);out.write(json.dumps(row)+'\n');out.flush()
   if time.monotonic()-start>=plan['duration_seconds']:break
   time.sleep(plan['interval_seconds'])
 assert all(rows[-1]['steps'][m]>rows[0]['steps'][m] for m in steps)
 with (D/'OBSERVATION_REVIEW.json').open('x') as out:json.dump(dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,samples=len(rows),identities=ids,first=rows[0],last=rows[-1]),out,indent=2);out.write('\n')
 print('Original',len(ids),'identities held for',time.monotonic()-start,'seconds; all3 training streams progressed')
except BaseException as e:
 with (D/'OBSERVATION_FAILURE.json').open('x') as out:json.dump(dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()),out,indent=2)
 raise
