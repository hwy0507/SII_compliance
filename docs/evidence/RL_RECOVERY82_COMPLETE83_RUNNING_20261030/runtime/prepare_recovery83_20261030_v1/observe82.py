from pathlib import Path
import json,time,os,hashlib
D=Path(__file__).parent;B=D.parents[1];R=B/'runs/parameter_partial75_recovery_cycle82_20261029_v1';os.sched_setaffinity(0,{54})
def read(p):return json.loads(p.read_text())
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
refs=[R/'LAUNCH.json',R/'MONITOR_LAUNCH.json']+[B/f'runs/{n}/LAUNCH.json' for n in ['parameter_recovery82_loss_20261029_v1','parameter_recovery82_task_labels_20261029_v1','vmc_recovery82_terminal_followup_20261029_v1','admittance_recovery82_terminal_followup_20261029_v1','parameter_recovery82_84_reward_stability_20261030_v1']]
jobs=read(R/'LAUNCH.json')['jobs'];identities=list(jobs)+[read(p) for p in refs[1:]]+[read(D/'LAUNCH.json')]+[dict(pid=pid,proc_start_ticks=start) for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]]
put(D/'OBSERVATION_PLAN.json',dict(time=time.time(),samples=16,interval_seconds=20,identities=identities,refs=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in refs],automatic_training=False))
start=time.monotonic();rows=[]
try:
 with (D/'OBSERVATIONS.jsonl').open('x') as log:
  for n in range(16):
   if n:time.sleep(max(0,start+20*n-time.monotonic()))
   assert all(live(j) for j in identities),'Original process identity changed'
   progress={j['controller']:read(R/j['controller']/'train/PROGRESS.json') for j in jobs}
   for m in progress:
    assert not (R/m/'train/FAILURE.json').exists()
    if rows:assert progress[m]['steps']>=rows[-1]['progress'][m]['steps']
   g=json.loads(Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()[-1]);assert time.time()-g['time']<20
   row=dict(time=time.time(),elapsed=time.monotonic()-start,identities_live=True,progress=progress,gpu=g);rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
 saved=[json.loads(l) for l in (D/'OBSERVATIONS.jsonl').read_text().splitlines()];assert saved==rows and len(saved)==16
 put(D/'OBSERVATION_FINISHED.json',dict(passed=True,time=time.time(),samples=16,elapsed=rows[-1]['elapsed'],all_original_identities_preserved=True,all_saved_rows_independently_read_back=True,new_physics=0,optimizer_updates=0))
 print(json.dumps(dict(passed=True,elapsed=rows[-1]['elapsed'],steps={m:v['steps'] for m,v in rows[-1]['progress'].items()})))
except BaseException as e:put(D/'OBSERVATION_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
