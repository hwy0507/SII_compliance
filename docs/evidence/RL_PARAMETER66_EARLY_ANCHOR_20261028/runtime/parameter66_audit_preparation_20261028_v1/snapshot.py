from pathlib import Path
import json,hashlib,time,math,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=B/'runtime/parameter66_verified_snapshot_1716_20261028_v1';out.mkdir();run=B/'runs/parameter_capacity_pool30_cycle66_20261026_v1'
def read(p):return json.loads(p.read_text())
def identity(j):
 s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert s[19]==j['proc_start_ticks'] and s[0]!='Z';return dict(pid=j['pid'],expected_start=j['proc_start_ticks'],actual_start=s[19],state=s[0],live=True)
learners=[]
for j in read(run/'LAUNCH.json')['jobs']:
 v=identity(j);p=run/j['controller']/'train';assert not(p/'FAILURE.json').exists();assert not(p/'FINISHED.json').exists();v.update(controller=j['controller'],progress=read(p/'PROGRESS.json'),finished=False,failure=False);learners.append(v)
watch={k:identity(read(p)) for k,p in [('archive',run/'MONITOR_LAUNCH.json'),('loss66',B/'runs/parameter66_loss_20261028_v1/LAUNCH.json'),('terminal66',B/'runs/vmc66_terminal_anchor_followup_20261028_v1/LAUNCH.json'),('labels66',B/'runs/parameter_task_label_audit66_20261028_v1/LAUNCH66.json'),('restore67',B/'runtime/prepare_parameter67_20261028_v1/parameter_LAUNCH.json'),('window65_67',B/'runs/parameter_capacity65_67_reward_stability_20261028_v1/LAUNCH.json')]}
for name,pid,t in [('guard',3256866,'37410686'),('guard0',3256867,'37410690'),('guard1',3256868,'37410690'),('guard2',3256869,'37410691'),('guard3',3256870,'37410693')]:watch[name]=identity(dict(pid=pid,proc_start_ticks=t))
assert not Path('/tmp/sii_gpu_util_guard_20261028_v5/STOP').exists();now=time.time();snap=dict(time=now,learners=learners,watchers=watch,gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu','--format=csv,noheader'],text=True),no_scientific_restart=True,goal_active=True);(out/'SNAPSHOT.json').write_text(json.dumps(snap,indent=2)+'\n')
# Current-turn retrospective, preserving actual sampling timestamps.
since=1793207511.;g=[]
with Path('/tmp/sii_gpu_util_guard_20261028_v5/samples.jsonl').open() as f:
 for line in f:
  x=json.loads(line)
  if since<=x['time']<=now:g.append(x)
assert len(g)>1;(out/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in g));stats={}
for i in range(4):
 v=[next(y['utilization'] for y in x['gpus'] if y['gpu']==i) for x in g];stats[str(i)]=dict(minimum=min(v),mean=math.fsum(v)/len(v),below50=sum(x<50 for x in v))
r=dict(samples=len(g),first_time=g[0]['time'],last_time=g[-1]['time'],max_gap_seconds=max(y['time']-x['time'] for x,y in zip(g,g[1:])),gpus=stats,synthetic_guard_included=True,per_instant_guarantee=False);(out/'GUARD_REVIEW.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(snapshot=snap,guard=r),indent=2))
