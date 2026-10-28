from pathlib import Path
import json,time,hashlib,subprocess,math,socket
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runtime/parameter71_followups_snapshot_20261028_v1';O.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();write=lambda p,v:p.write_text(json.dumps(v,indent=2)+'\n')
p=B/'runs/parameter71_first5000_20261028_v1';assert read(p/'SAVED_REVIEW.json')['passed']
write(p/'PLOT_INSPECTION.json',dict(time=time.time(),actual_image_viewed=True,plot_sha256=sha(p/'loss.png'),axes_and_data_readable=True,observations='All5000 raw samples and1000moving means visible in six panels. I critic rises mid-prefix then returns lower; actor slightly rises. A critic roughly flat but slightly higher final1000, finite spikes retained. V critic initial burst then lower mean with persistent finite spikes, actor slightly declines. MaxI15.8374/A19.4732/V24.3393 retained. Only early71 prefix, not complete cycle or convergence.',convergence_claim=False))
def identity(j):
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z'
 return dict(pid=j['pid'],proc_start_ticks=f[19],state=f[0],cmdline=Path(f'/proc/{j["pid"]}/cmdline').read_bytes().replace(b'\0',b' ').decode())
root=B/'runs/parameter_capacity_pool30_cycle71_20261026_v1';snap=dict(time=time.time(),compute_host=socket.gethostname(),learners=[],waiters={},convergence_claim=False)
for j in read(root/'LAUNCH.json')['jobs']:
 d=identity(j);d.update(controller=j['controller'],progress=read(root/j['controller']/'train/PROGRESS.json'),sampler_count=len(Path(f'/proc/{j["pid"]}/task/{j["pid"]}/children').read_text().split()));assert d['sampler_count']==30;assert not (root/j['controller']/'train/FAILURE.json').exists();snap['learners'].append(d)
snap['archive_monitor']=identity(read(root/'MONITOR_LAUNCH.json'));assert not (root/'ARCHIVE_REVIEW_FINISHED.json').exists() and not (root/'ARCHIVE_REVIEW_FAILURE.json').exists()
for key,folder,receipt,plan in [('loss71','runs/parameter71_loss_20261028_v1','LAUNCH.json','PLAN.json'),('window71_73','runs/parameter_capacity71_73_reward_stability_20261028_v1','LAUNCH.json','PLAN.json'),('labels71','runs/parameter_task_label_audit71_20261028_v1','LAUNCH71.json','PLAN71.json'),('vmc71','runs/vmc71_terminal_anchor_followup_20261028_v1','LAUNCH.json','PLAN.json'),('admittance71','runs/admittance71_terminal_anchor_followup_20261028_v1','LAUNCH.json','PLAN.json'),('restore_only72','runtime/prepare_parameter72_20261028_v1','parameter_LAUNCH.json','REGISTRATION.json')]:
 f=B/folder;j=read(f/receipt);d=identity(j);h=j.get('plan_sha256',j.get('registration_sha256'));assert sha(f/plan)==h;d['registration_sha256']=h;snap['waiters'][key]=d;assert not list(f.glob('*FAILURE.json'))
 if key in ['vmc71','admittance71']:
  p=read(f/plan)
  for n,h in p['sources'].items():assert sha(f/n)==h
  for x in p['inputs'].values():assert sha(Path(x['path']))==x['sha256']
assert sha(B/'runs/parameter_capacity71_73_reward_stability_20261028_v1/PLAN.json')=='c160b5d6032abaea7ea81c1fb0a2a8151f4fd929d81044a830740343fc572bdf'
snap['cycle72_training_launched']=(B/'runs/parameter_capacity_pool30_cycle72_20261026_v1/LAUNCH.json').exists();assert not snap['cycle72_training_launched']
g=Path('/tmp/sii_gpu_util_guard_20261028_v5');snap['guard_processes']=[identity(dict(pid=p,proc_start_ticks=t)) for p,t in [(3256866,'37410686'),(3256867,'37410690'),(3256868,'37410690'),(3256869,'37410691'),(3256870,'37410693')]]
assert not (g/'STOP').exists() and not (g/'FAILURE.json').exists();start=read(B/'runtime/parameter70_completion_observation_20261028_v1/FINAL_SNAPSHOT.json')['time']
raw=[l for l in (g/'samples.jsonl').read_bytes().splitlines(keepends=True) if l.endswith(b'\n') and json.loads(l)['time']>=start];(O/'gpu_samples.jsonl').write_bytes(b''.join(raw));rows=[json.loads(l) for l in raw];assert len(rows)>10
snap['guard_window']=dict(start=rows[0]['time'],end=rows[-1]['time'],samples=len(rows),max_gap=max(b['time']-a['time'] for a,b in zip(rows,rows[1:])),synthetic_guard_included=True,instantaneous_guarantee=False)
snap['guard_stats']=[]
for i in range(4):
 v=[next(g['utilization'] for g in row['gpus'] if g['gpu']==i) for row in rows];snap['guard_stats'].append(dict(gpu=i,minimum=min(v),mean=math.fsum(v)/len(v),below50=sum(x<50 for x in v)))
snap['current_gpus']=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used','--format=csv,noheader,nounits'],text=True)
write(O/'SNAPSHOT.json',snap);print(json.dumps({k:v for k,v in snap.items() if k not in ['learners','waiters','guard_processes','archive_monitor']},indent=2));print('steps',[j['progress']['steps'] for j in snap['learners']])
