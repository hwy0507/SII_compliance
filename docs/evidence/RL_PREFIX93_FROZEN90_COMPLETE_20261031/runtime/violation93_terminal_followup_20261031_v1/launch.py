from pathlib import Path
import subprocess,json,time,hashlib,os
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_fixed92_terminal_followup_20261031_v1';read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
plan=read(O/'PLAN.json');assert read(O/'PREFLIGHT_REVIEW.json')['passed'];v=read(O/'VALIDATOR_REVIEW.json');assert v['passed'] and v['negative_count']==27
assert read(D/'SOURCE_REVIEW.json')['passed'];assert sha(D/'check93.py')==plan['source_hashes']['check93.py']
for n,h in plan['source_hashes'].items():assert sha(D/n)==h
j=plan['original_monitor'];s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['proc_start_ticks']
assert not (O/'PROCESS.json').exists() and not (O/'FINISHED.json').exists() and not (Path(plan['complete_review'])/'FINISHED.json').exists() and time.time()<plan['wait_deadline_unix']
put(O/'LAUNCH_REVIEW.json',dict(time=time.time(),passed=True,plan_sha256=sha(O/'PLAN.json'),validator_sha256=sha(O/'VALIDATOR_REVIEW.json'),validator_source_sha256=sha(D/'check93.py'),actual_original_monitor_live=True,only_one_waiter=True,automatic94=False))
with (O/'wait.log').open('xb') as log:p=subprocess.Popen([str(B/'env/bin/python'),str(D/'wait93.py')],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
s=Path('/proc',str(p.pid),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z';put(O/'PROCESS.json',dict(time=time.time(),pid=p.pid,start=s[19],source_sha256=sha(D/'wait93.py'),wait_deadline_unix=plan['wait_deadline_unix']))
print('Launched one fixed92 diagnostic waiter',p.pid)
