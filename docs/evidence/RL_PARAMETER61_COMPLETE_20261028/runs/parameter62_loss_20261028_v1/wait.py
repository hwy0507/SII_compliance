from pathlib import Path
import json,os,time,subprocess
OUT=Path(__file__).resolve().parent
os.sched_setaffinity(0,{54})
plan=json.loads((OUT/'PLAN.json').read_text());deadline=time.monotonic()+7200
def live(j):
 try:
  f=Path(f"/proc/{j['pid']}/stat").read_text().split(') ')[1].split();return f[19]==j['proc_start_ticks'] and f[0]!='Z'
 except FileNotFoundError:return False
try:
 while True:
  ready=True
  for j in plan['jobs']:
   p=Path(plan['parent_run'])/j['controller']/'train'
   assert not (p/'FAILURE.json').exists()
   if not (p/'FINISHED.json').exists():
    assert live(j),'Original learner disappeared before FINISHED';ready=False
   elif live(j):ready=False
   else:assert json.loads((p/'FINISHED.json').read_text())['status']=='stopped_at_complete_cycle'
  if ready:break
  assert time.monotonic()<deadline,'Fixed full62 loss observation expired'
  time.sleep(5)
 for name in ['audit.py','paired_gate.py']:subprocess.run([plan['python'],str(OUT/name)],check=True)
 (OUT/'FINISHED.json').write_text(json.dumps(dict(time=time.time(),completed=True)))
except BaseException as error:
 (OUT/'FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(error))));raise
