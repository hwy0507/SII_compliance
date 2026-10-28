from pathlib import Path
import json,time,hashlib,subprocess,socket
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
O=B/'runtime/parameter70_followups_snapshot_20261028_v1';O.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,v:p.write_text(json.dumps(v,indent=2)+'\n')
def identity(j):
 p=Path(f'/proc/{j["pid"]}/stat');s=p.read_text().rsplit(')',1)[1].split()
 assert s[19]==j['proc_start_ticks'] and s[0]!='Z'
 return dict(pid=j['pid'],proc_start_ticks=s[19],state=s[0],cmdline=Path(f'/proc/{j["pid"]}/cmdline').read_bytes().replace(b'\0',b' ').decode())
root=B/'runs/parameter_capacity_pool30_cycle70_20261026_v1'
snap=dict(time=time.time(),compute_host=socket.gethostname(),learners=[],waiters={},source_bindings_verified=[],convergence_claim=False)
for j in read(root/'LAUNCH.json')['jobs']:
 d=identity(j);d['controller']=j['controller'];d['progress']=read(root/j['controller']/'train/PROGRESS.json')
 d['sampler_count']=len(Path(f'/proc/{j["pid"]}/task/{j["pid"]}/children').read_text().split());assert d['sampler_count']==30
 assert not (root/j['controller']/'train/FAILURE.json').exists();snap['learners'].append(d)
snap['archive_monitor']=identity(read(root/'MONITOR_LAUNCH.json'))
assert not (root/'ARCHIVE_REVIEW_FINISHED.json').exists() and not (root/'ARCHIVE_REVIEW_FAILURE.json').exists()
for key,folder,receipt,plan in [
 ('loss70','runs/parameter70_loss_20261028_v1','LAUNCH.json','PLAN.json'),
 ('window68_70','runs/parameter_capacity68_70_reward_stability_20261028_v1','LAUNCH.json','PLAN.json'),
 ('labels70','runs/parameter_task_label_audit70_20261028_v1','LAUNCH70.json','PLAN70.json'),
 ('vmc70','runs/vmc70_terminal_anchor_followup_20261028_v1','LAUNCH.json','PLAN.json'),
 ('admittance70','runs/admittance70_terminal_anchor_followup_20261028_v1','LAUNCH.json','PLAN.json'),
 ('restore_only71','runtime/prepare_parameter71_20261028_v1','parameter_LAUNCH.json','REGISTRATION.json')]:
 f=B/folder;j=read(f/receipt);p=read(f/plan);d=identity(j)
 expected=j.get('plan_sha256',j.get('registration_sha256'));assert sha(f/plan)==expected
 d['registration_sha256']=expected;snap['waiters'][key]=d
 assert not list(f.glob('*FAILURE.json'))
 if key in ['vmc70','admittance70']:
  for n,h in p['sources'].items():assert sha(f/n)==h
  for v in p['inputs'].values():assert sha(Path(v['path']))==v['sha256']
  assert sha(Path(p['parent_run'])/'LAUNCH.json')==p['parent_launch_sha256']
  snap['source_bindings_verified'].append(key)
assert sha(B/'runs/parameter_capacity68_70_reward_stability_20261028_v1/PLAN.json')=='e3a50567b669cb5a8a37ca9aefbca4efcb84ae39d4549af2fc720a99420e95bf'
snap['cycle71_training_launched']=(B/'runs/parameter_capacity_pool30_cycle71_20261026_v1/LAUNCH.json').exists();assert not snap['cycle71_training_launched']
g=Path('/tmp/sii_gpu_util_guard_20261028_v5')
snap['guard_processes']=[identity(dict(pid=p,proc_start_ticks=t)) for p,t in [(3256866,'37410686'),(3256867,'37410690'),(3256868,'37410690'),(3256869,'37410691'),(3256870,'37410693')]]
assert not (g/'STOP').exists() and not (g/'FAILURE.json').exists()
start=read(B/'runtime/parameter69_completion_observation_20261028_v1/FINAL_SNAPSHOT.json')['time']
raw=[l for l in (g/'samples.jsonl').read_bytes().splitlines(keepends=True) if l.endswith(b'\n') and json.loads(l)['time']>=start]
(O/'gpu_samples.jsonl').write_bytes(b''.join(raw));samples=[json.loads(l) for l in raw];assert len(samples)>10
snap['guard_window']=dict(start=samples[0]['time'],end=samples[-1]['time'],samples=len(samples),max_gap=max(b['time']-a['time'] for a,b in zip(samples,samples[1:])),synthetic_guard_included=True,instantaneous_guarantee=False)
snap['guard_stats']=[]
for i in range(4):
 values=[s['gpus'][i]['utilization'] for s in samples]
 snap['guard_stats'].append(dict(gpu=i,minimum=min(values),mean=sum(values)/len(values),below50=sum(v<50 for v in values)))
snap['current_gpus']=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used','--format=csv,noheader,nounits'],text=True)
write(O/'SNAPSHOT.json',snap);print(json.dumps(snap,indent=2))
