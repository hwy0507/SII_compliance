from pathlib import Path
import json,time,hashlib,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];T=B/'runs/parameter_violation_cycle92_20261030_v1';V=B/'runs/parameter_violation_cycle92_review_20261030_v1';O=B/'runs/violation92_fixed87_terminal_followup_20261030_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1'
read=lambda p:json.loads(p.read_text())
def state(j):
 p=Path('/proc',str(j['pid']),'stat')
 if not p.exists():return 'absent'
 s=p.read_text().rsplit(')',1)[1].split()
 return s[0] if s[19]==j['start'] else 'reused_pid'
plan=read(D/'WAIT_PLAN.json');assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==plan['source_sha256'];start=time.monotonic();rows=[]
with (D/'WAIT_SAMPLES.jsonl').open('x') as out:
 while True:
  jobs={str(j['pid']):state(j) for j in plan['identities']}
  training={m:read(T/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']};frozen={m:read(F/m/'PROGRESS.json') for m in training}
  finished={m:(T/m/'train/FINISHED.json').exists() for m in training}
  failures=list(T.rglob('*FAILURE*.json'))+list(O.glob('WAIT_FAILURE_*.json'))+list(F.glob('*/FAILURE.json'))
  row=dict(time=time.time(),elapsed_s=time.monotonic()-start,states=jobs,training=training,frozen=frozen,learner_finished=finished,review_finished=(V/'FINISHED.json').exists(),terminal_finished=(O/'FINISHED.json').exists(),failures=[str(p) for p in failures]);rows.append(row);out.write(json.dumps(row)+'\n');out.flush()
  if failures:outcome='attention';break
  if row['review_finished'] and row['terminal_finished']:outcome='ready';break
  if row['elapsed_s']>=plan['maximum_seconds']:outcome='observation_limit_only';break
  time.sleep(plan['interval_seconds'])
with (D/'WAIT_REVIEW.json').open('x') as out:json.dump(dict(time=time.time(),outcome=outcome,samples=len(rows),first=rows[0],last=rows[-1],no_restart=True,observation_timeout_is_not_job_terminal=True),out,indent=2);out.write('\n')
print(outcome)
