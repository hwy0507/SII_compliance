from pathlib import Path
import json,time,os
D=Path(__file__).parent;B=D.parents[1];os.sched_setaffinity(0,{54});read=lambda p:json.loads(Path(p).read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
identities=read(B/'runtime/recovery86_history_progress_20261030_v1/PLAN.json')['identities']
def state(j):
 for p in j['failure_paths']:assert not Path(p).exists(),p
 p=Path(f'/proc/{j["pid"]}/stat')
 if p.exists():
  s=p.read_text().rsplit(')',1)[1].split()
  if s[19]==str(j['proc_start_ticks']) and s[0]!='Z':return 'live'
 assert j['terminal_requirements'],j['name']
 for r in j['terminal_requirements']:assert read(r['path'])[r['key']]==r['value']
 return 'verified_terminal'
put(D/'WATCH_PLAN.json',dict(time=time.time(),identities=identities,budget_s=1800,interval_s=30,automatic_training=False));start=time.monotonic();rows=[]
try:
 with (D/'OBSERVATIONS.jsonl').open('x') as f:
  while True:
   states={j['name']:state(j) for j in identities};progress={m:read(B/f'runs/parameter_partial75_recovery_cycle86_20261029_v1/{m}/train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
   if rows:
    for m in progress:assert progress[m]['steps']>=rows[-1]['progress'][m]['steps']
   g=json.loads(Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()[-1]);assert time.time()-g['time']<20
   row=dict(time=time.time(),elapsed=time.monotonic()-start,states=states,progress=progress,gpu=g);rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
   ready=all(states[n]=='verified_terminal' for n in ['impedance','admittance','vmc','archive86','loss86','labels86','vmc_terminal86','admittance_terminal86','fixed2514_84_86','restore87_only'])
   if ready:break
   if time.monotonic()-start>=1800:
    put(D/'WATCH_TIMEOUT.json',dict(time=time.time(),scientific_failure=False,original_processes_not_restarted=True));break
   time.sleep(30)
 assert [json.loads(l) for l in (D/'OBSERVATIONS.jsonl').read_text().splitlines()]==rows
 put(D/'WATCH_FINISHED.json',dict(passed=True,time=time.time(),samples=len(rows),elapsed_s=rows[-1]['elapsed'],all_full86_and_restore87_ready=ready,automatic_training=False));print('Watch complete, ready=',ready)
except BaseException as e:put(D/'WATCH_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
