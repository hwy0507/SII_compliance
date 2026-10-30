from pathlib import Path
import json,time,hashlib,os
from decision80 import B,D,OUT,read,sha,ref
G=Path('/tmp/sii_gpu_util_guard_20261030_v7')
jobs=[]
def add(name,j,terminal=None):
 p=Path(f'/proc/{j["pid"]}');f=(p/'stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z';jobs.append(dict(name=name,pid=j['pid'],proc_start_ticks=j['proc_start_ticks'],cmdline_sha256=sha(p/'cmdline'),terminal=str(terminal) if terminal else None))
for j in read(OUT/'LAUNCH.json')['jobs']:add(j['controller'],j,OUT/j['controller']/'train/FINISHED.json')
for name in ['MONITOR','STARTUP']:
 j=read(OUT/(name+'_LAUNCH.json'));term=OUT/('ARCHIVE_REVIEW_FINISHED.json' if name=='MONITOR' else 'startup/REVIEW.json');p=Path(f'/proc/{j["pid"]}/stat')
 if p.exists() and p.read_text().rsplit(')',1)[1].split()[0]!='Z':add(name,j,term)
 else:assert term.exists() and read(term).get('passed',read(term).get('completed',False))
for name,root in [('loss',B/'runs/parameter_recovery80_loss_20261029_v1'),('labels',B/'runs/parameter_recovery80_task_labels_20261029_v1'),('vmc_terminal',B/'runs/vmc_recovery80_terminal_followup_20261029_v1'),('admittance_terminal',B/'runs/admittance_recovery80_terminal_followup_20261029_v1'),('window79_81',B/'runs/parameter_recovery79_81_reward_stability_20261030_v1')]:add(name,read(root/'LAUNCH.json'),root/'FINISHED.json')
for name,pid,start in [('guard',97370,'570509460'),('worker0',97399,'570509475'),('worker1',97400,'570509475'),('worker2',97401,'570509475'),('worker3',97402,'570509475')]:add(name,dict(pid=pid,proc_start_ticks=start))
plan=dict(time=time.time(),duration_seconds=180,period_seconds=30,jobs=jobs,sources=read(D/'LAUNCH_SOURCE_REVIEW.json')['files'],automatic_training=False)
with (D/'OBSERVATION_PLAN.json').open('x') as f:json.dump(plan,f,indent=2);f.write('\n')
t0=time.monotonic();rows=[]
try:
 while True:
  statuses=[]
  for j in jobs:
   p=Path(f'/proc/{j["pid"]}');live=False
   if p.exists():
    z=(p/'stat').read_text().rsplit(')',1)[1].split();live=z[19]==j['proc_start_ticks'] and z[0]!='Z'
   if live:assert sha(p/'cmdline')==j['cmdline_sha256']
   else:assert j['terminal'] and Path(j['terminal']).exists() and any(read(j['terminal']).get(k) for k in ['passed','completed','status'])
   statuses.append(dict(name=j['name'],pid=j['pid'],proc_start_ticks=j['proc_start_ticks'],status='live' if live else 'terminal_receipt'))
  for x in plan['sources']:assert sha(x['path'])==x['sha256']
  for m in ['impedance','admittance','vmc']:assert not (OUT/m/'DRIVER_FAILURE.json').exists() and not (OUT/m/'train/FAILURE.json').exists()
  assert not (OUT/'ARCHIVE_REVIEW_FAILURE.json').exists()
  g=json.loads((G/'samples.jsonl').read_text().splitlines()[-1]);assert time.time()-g['time']<20
  progress={m:read(OUT/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
  row=dict(time=time.time(),elapsed=time.monotonic()-t0,identities=statuses,parameter=progress,gpu=g)
  with (D/'OBSERVATIONS.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  rows.append(row);print(json.dumps(dict(sample=len(rows),elapsed=row['elapsed'],steps={m:v['steps'] for m,v in progress.items()},gpu=[v['utilization'] for v in g['gpus']])),flush=True)
  if row['elapsed']>=180:break
  time.sleep(30)
 saved=[json.loads(l) for l in (D/'OBSERVATIONS.jsonl').read_text().splitlines()];assert saved==rows
 for m in ['impedance','admittance','vmc']:assert all(a['parameter'][m]['steps']<=z['parameter'][m]['steps'] for a,z in zip(saved,saved[1:]))
 result=dict(passed=True,time=time.time(),samples=len(rows),elapsed=rows[-1]['elapsed'],identities=len(jobs),saved_rows_verified=True,first_steps={m:v['steps'] for m,v in rows[0]['parameter'].items()},last_steps={m:v['steps'] for m,v in rows[-1]['parameter'].items()},scientific_restart=False,goal='active')
 with (D/'OBSERVATION_FINISHED.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
except BaseException as e:
 (D/'OBSERVATION_FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)),indent=2)+'\n');raise
