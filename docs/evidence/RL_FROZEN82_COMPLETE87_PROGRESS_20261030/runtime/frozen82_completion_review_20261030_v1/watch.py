from pathlib import Path
import json,time,os
D=Path(__file__).parent;B=D.parents[1];O=B/'runs/parameter82_frozen_full30_20261030_v1';read=lambda p:json.loads(Path(p).read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def state(j):
 for p in j['failure_paths']:assert not Path(p).exists(),p
 try:
  s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split()
  if s[19]==str(j['proc_start_ticks']) and s[0]!='Z':return 'live'
 except FileNotFoundError:pass
 assert j['terminal_requirements'],j['name']
 for q in j['terminal_requirements']:assert read(q['path'])[q['key']]==q['value']
 return 'verified_terminal'
os.sched_setaffinity(0,{12});plan=read(D/'PLAN.json');start=time.monotonic();rows=[]
try:
 with (D/'OBSERVATIONS.jsonl').open('x') as f:
  while True:
   states={j['name']:state(j) for j in plan['identities']};progress={m:read(B/f'runs/parameter_partial75_recovery_cycle87_20261029_v1/{m}/train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
   if rows:
    for m in progress:assert progress[m]['steps']>=rows[-1]['progress87'][m]['steps']
   g=json.loads(Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()[-1]);assert time.time()-g['time']<20
   ready=all(states[k]=='verified_terminal' for k in ['frozen82_impedance','frozen82_admittance','frozen82_vmc','frozen82_review','frozen55_82_compare','frozen82_saved'])
   row=dict(time=time.time(),elapsed=time.monotonic()-start,states=states,progress87=progress,frozen82_admittance=read(O/'admittance/PROGRESS.json'),gpu=g,all82_ready=ready);rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
   if ready:break
   if time.monotonic()-start>=plan['observer_budget_seconds']:break
   time.sleep(plan['interval_s'])
 assert [json.loads(l) for l in (D/'OBSERVATIONS.jsonl').read_text().splitlines()]==rows
 put(D/'WATCH_FINISHED.json',dict(passed=True,time=time.time(),all82_ready=ready,samples=len(rows),identities=len(plan['identities']),elapsed_s=rows[-1]['elapsed'],automatic_training=False,science_restarted=False))
 print('Watch completed. all82_ready=',ready)
except BaseException as e:put(D/'WATCH_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
