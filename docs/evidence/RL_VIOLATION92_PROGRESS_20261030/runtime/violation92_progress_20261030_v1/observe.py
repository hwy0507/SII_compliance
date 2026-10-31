from pathlib import Path
import time,json,hashlib,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_violation_cycle92_20261030_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';O=B/'runs/violation92_fixed87_terminal_followup_20261030_v1';P=B/'runtime/violation90_frozen_postprocess_20261030_v1'
read=lambda p:json.loads(p.read_text())
def identity(pid):
 s=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z';return dict(pid=pid,start=s[19])
def check(j):assert identity(j['pid'])['start']==str(j.get('start',j.get('proc_start_ticks')))
try:
 plan=read(D/'OBSERVATION_PLAN.json');assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==plan['script_sha256']
 jobs=read(R/'LAUNCH.json')['jobs'];ids=jobs+[read(R/'MONITOR_LAUNCH.json')]+read(F/'LAUNCH.json')['jobs']+[read(F/'REVIEW_LAUNCH.json'),read(P/'PROCESS.json'),read(O/'PROCESS.json')]
 for j in jobs:
  children=list(map(int,Path('/proc',str(j['pid']),'task',str(j['pid']),'children').read_text().split()));assert len(children)==30;ids.extend(identity(pid) for pid in children)
 for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]:ids.append(dict(pid=pid,start=start))
 ids=[dict(pid=j['pid'],start=str(j.get('start',j.get('proc_start_ticks')))) for j in ids]
 start=time.monotonic();rows=[]
 with (D/'OBSERVATIONS.jsonl').open('x') as out:
  while True:
   for j in ids:check(j)
   assert not (R/'ARCHIVE_REVIEW_FAILURE.json').exists() and not list(O.glob('WAIT_FAILURE_*.json'))
   steps={};frozen={}
   for m in ['impedance','admittance','vmc']:
    assert not (R/m/'DRIVER_FAILURE.json').exists() and not (R/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
    steps[m]=read(R/m/'train/PROGRESS.json')['steps'];frozen[m]=read(F/m/'PROGRESS.json')
   row=dict(time=time.time(),elapsed_s=time.monotonic()-start,steps=steps,frozen=frozen,identity_count=len(ids));rows.append(row);out.write(json.dumps(row)+'\n');out.flush()
   if time.monotonic()-start>=plan['duration_seconds']:break
   time.sleep(plan['interval_seconds'])
 assert all(rows[-1]['steps'][m]>rows[0]['steps'][m] for m in steps)
 with (D/'OBSERVATION_REVIEW.json').open('x') as out:json.dump(dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,samples=len(rows),identities=ids,first=rows[0],last=rows[-1]),out,indent=2);out.write('\n')
 print('Original',len(ids),'identities held; all three training streams progressed')
except BaseException as e:
 with (D/'OBSERVATION_FAILURE.json').open('x') as out:json.dump(dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()),out,indent=2)
 raise
