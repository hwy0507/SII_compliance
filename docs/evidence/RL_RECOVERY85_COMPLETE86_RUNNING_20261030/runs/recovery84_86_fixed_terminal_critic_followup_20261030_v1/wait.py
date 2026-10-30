from pathlib import Path
import json,time,subprocess,sys,hashlib
D=Path(__file__).parent;B=D.parents[1]
def read(p):return json.loads(p.read_text())
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
try:
 plan=read(D/'PLAN.json');binding=read(D/'SOURCE_REVIEW.json')
 for r in binding['sources']:assert hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256']
 while True:
  ready=True;root=Path(plan['parent_run']);rev=Path(plan['parent_review'])
  checks=[(root/'ARCHIVE_REVIEW_FINISHED.json','completed'),(rev/'FINISHED.json','completed')];jobs=[plan['monitor']]+plan['learners']
  for p in [root/'ARCHIVE_REVIEW_FAILURE.json']+[root/m/'train/FAILURE.json' for m in ['impedance','admittance','vmc']]:assert not p.exists(),str(p)
  for m in plan['methods']:
   t=B/f'runs/{m}_recovery86_terminal_followup_20261029_v1';jobs.append(read(t/'LAUNCH.json'));checks.extend([(t/'FINISHED.json','completed'),(t/'SAVED_VALUES_REVIEW.json','passed')])
   for n in ['FAILURE.json','WAIT_FAILURE.json']:assert not (t/n).exists(),str(t/n)
  for p,k in checks:
   if not p.exists():ready=False
   else:assert read(p)[k]
  if ready and not any(live(j) for j in jobs):break
  assert time.time()<plan['original_deadline_unix'],'Original86 monitor+14400 deadline expired; no extension'
  time.sleep(5)
 subprocess.run([sys.executable,str(D/'audit.py')],check=True)
 assert read(D/'REVIEW.json')['passed'] and read(D/'SAVED_REVIEW.json')['passed']
 with (D/'FINISHED.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),automatic_training=False),f)
except BaseException as e:
 with (D/'FAILURE.json').open('x') as f:json.dump(dict(time=time.time(),error=repr(e)),f)
 raise
