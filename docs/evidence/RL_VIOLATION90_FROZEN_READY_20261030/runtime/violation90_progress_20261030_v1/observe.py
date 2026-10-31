from pathlib import Path
import os,json,time,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_violation_cycle90_20261030_v1';F=B/'runs/parameter88_history_frozen_full30_20261030_v1';P=B/'runtime/violation90_frozen_preparation_20261030_v1';read=lambda p:json.loads(p.read_text())
def identity(pid):
 f=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split();assert f[0]!='Z';return f[19]
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
plan=read(D/'OBSERVATION_PLAN.json');os.sched_setaffinity(0,{54});rows=[];start=time.monotonic()
try:
 with (D/'OBSERVATIONS.jsonl').open('x') as out:
  while True:
   for pid,tick in plan['identities'].items():assert identity(int(pid))==tick
   assert not (R/'ARCHIVE_REVIEW_FAILURE.json').exists()
   for m in ['impedance','admittance','vmc']:
    assert not (R/m/'DRIVER_FAILURE.json').exists() and not (R/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
   row=dict(time=time.time(),elapsed_s=time.monotonic()-start,steps={m:read(R/m/'train/PROGRESS.json')['steps'] for m in ['impedance','admittance','vmc']},frozen={m:read(F/m/'PROGRESS.json')['completed_conditions'] for m in ['impedance','admittance','vmc']});rows.append(row);out.write(json.dumps(row)+'\n');out.flush()
   if time.monotonic()-start>=plan['duration_seconds']:break
   time.sleep(plan['interval_seconds'])
 assert all(rows[-1]['steps'][m]>rows[0]['steps'][m] for m in rows[0]['steps'])
 put(D/'OBSERVATION_REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,samples=len(rows),identity_count=len(plan['identities']),original_identities=plan['identities'],first=rows[0],last=rows[-1],scope='Original training90, samplers, frozen88 and guard preserved during learned-bit frozen-interface checks',convergence_claim=False))
except BaseException:
 put(D/'OBSERVATION_FAILURE.json',dict(time=time.time(),traceback=traceback.format_exc()));raise
