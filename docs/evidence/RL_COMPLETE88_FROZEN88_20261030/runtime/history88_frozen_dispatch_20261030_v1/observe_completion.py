from pathlib import Path
import json,time,os
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_history_cycle88_20261030_v2';T=B/'runs/history88_fixed87_terminal_followup_20261030_v1'
os.sched_setaffinity(0,{10})
read=lambda p:json.loads(p.read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
plan=read(D/'OBSERVATION_PLAN.json');end=plan['time']+plan['maximum_seconds'];samples=[]
while time.time()<end:
 states={}
 for j in plan['jobs']:
  m=j['controller'];f=R/m/'train/FINISHED.json'
  if f.exists():assert read(f)['status']=='stopped_at_complete_cycle';states[m]={'finished':True}
  else:
   fields=Path(f"/proc/{j['pid']}/stat").read_text().rsplit(')',1)[1].split();assert fields[0]!='Z' and fields[19]==j['proc_start_ticks'];assert not (R/m/'train/FAILURE.json').exists();states[m]=read(R/m/'train/PROGRESS.json')
 assert not (R/'ARCHIVE_REVIEW_FAILURE.json').exists()
 archive_done=(R/'ARCHIVE_REVIEW_FINISHED.json').exists()
 if not archive_done:
  j=plan['monitor'];fields=Path(f"/proc/{j['pid']}/stat").read_text().rsplit(')',1)[1].split();assert fields[0]!='Z' and fields[19]==j['proc_start_ticks']
 sample=dict(time=time.time(),states=states,archive_done=archive_done,fixed_terminal_done=(T/'FINISHED.json').exists())
 samples.append(sample)
 with (D/'COMPLETION_OBSERVATIONS.jsonl').open('a') as f:f.write(json.dumps(sample)+'\n')
 print(json.dumps(sample),flush=True)
 if archive_done:
  put(D/'OBSERVATION_FINISHED.json',dict(time=time.time(),complete88_review_available=True,samples=len(samples)));break
 time.sleep(30)
else:put(D/'OBSERVATION_TIMEOUT.json',dict(time=time.time(),original_jobs_not_stopped=True,scope='Observation budget only; revalidate original handles next, never automatically restart'))
