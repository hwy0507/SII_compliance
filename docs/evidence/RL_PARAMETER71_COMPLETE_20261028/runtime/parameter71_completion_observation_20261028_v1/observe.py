from pathlib import Path
import json,time,hashlib,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runtime/parameter71_completion_observation_20261028_v1';O.mkdir(exist_ok=False)
os.sched_setaffinity(0,{53})
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,v:p.write_text(json.dumps(v,indent=2)+'\n')
s=read(B/'runtime/parameter71_followups_snapshot_20261028_v1/SNAPSHOT.json');run=B/'runs/parameter_capacity_pool30_cycle71_20261026_v1'
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 f=p.read_text().rsplit(')',1)[1].split();return f[19]==j['proc_start_ticks'] and f[0]!='Z'
ready={'archive':run/'ARCHIVE_REVIEW_FINISHED.json','loss71':B/'runs/parameter71_loss_20261028_v1/FINISHED.json','labels71':B/'runs/parameter_task_label_audit71_20261028_v1/FINISHED71.json','vmc71':B/'runs/vmc71_terminal_anchor_followup_20261028_v1/FINISHED.json','admittance71':B/'runs/admittance71_terminal_anchor_followup_20261028_v1/FINISHED.json','restore_only72':B/'runtime/prepare_parameter72_20261028_v1/parameter_FINISHED.json','window71_73':B/'runs/parameter_capacity71_73_reward_stability_20261028_v1/REVIEW.json'}
watch=list(s['learners'])+[s['archive_monitor']]+list(s['waiters'].values())+s['guard_processes'];assert all(live(j) for j in watch)
write(O/'PLAN.json',dict(time=time.time(),seconds=1800,interval_seconds=30,max_samples=61,identities=watch,source_sha256=sha(Path(__file__)),automatic_training=False,observer_only=True))
(O/'observe.py').write_bytes(Path(__file__).read_bytes());write(O/'LAUNCH.json',dict(pid=os.getpid(),proc_start_ticks=Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()[19]))
start=time.time()
try:
 for i in range(61):
  row=dict(index=i,time=time.time(),learners={},ready={k:p.exists() for k,p in ready.items()},waiters={},guard_live=all(live(j) for j in s['guard_processes']))
  for j in s['learners']:
   m=j['controller'];p=run/m/'train';row['learners'][m]=dict(live=live(j),progress=read(p/'PROGRESS.json'),finished=(p/'FINISHED.json').exists())
   assert row['learners'][m]['live'] or row['learners'][m]['finished']
   assert not (p/'FAILURE.json').exists()
  for key,j in s['waiters'].items():
   row['waiters'][key]=live(j);assert row['waiters'][key] or row['ready'][key],key
  assert live(s['archive_monitor']) or row['ready']['archive'];assert row['guard_live']
  failures=[str(p) for parent in [run,*(p.parent for p in ready.values()),Path('/tmp/sii_gpu_util_guard_20261028_v5')] for p in parent.glob('*FAILURE.json')];assert not failures,failures
  row['gpu']=json.loads(Path('/tmp/sii_gpu_util_guard_20261028_v5/samples.jsonl').read_text().splitlines()[-1]);assert time.time()-row['gpu']['time']<20
  with (O/'samples.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  print(json.dumps(dict(index=i,steps={m:r['progress']['steps'] for m,r in row['learners'].items()},gpu=[g['utilization'] for g in row['gpu']['gpus']],ready=row['ready'])),flush=True)
  if all(v for k,v in row['ready'].items() if k != 'window71_73'):break
  if i<60:time.sleep(30)
 write(O/'FINISHED.json',dict(completed=True,time=time.time(),duration=time.time()-start,samples=i+1,all_science_ready=all(v for k,v in row['ready'].items() if k != 'window71_73'),observer_only=True))
except BaseException as e:
 write(O/'OBSERVER_FAILURE.json',dict(time=time.time(),error=repr(e),does_not_authorize_scientific_restart=True));raise
