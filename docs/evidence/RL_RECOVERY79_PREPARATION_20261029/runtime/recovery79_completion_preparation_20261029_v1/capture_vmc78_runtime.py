from pathlib import Path
import json,time,hashlib,math
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;RUN=B/'runs/parameter_partial75_recovery_cycle78_20261029_v1';P=RUN/'vmc/train'
read=lambda p:json.loads(p.read_text())
def ref(p):
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return dict(path=str(p),sha256=h)
j=next(x for x in read(RUN/'LAUNCH.json')['jobs'] if x['controller']=='vmc');p=Path(f'/proc/{j["pid"]}/stat')
if p.exists():
 f=p.read_text().rsplit(')',1)[1].split();assert f[19]!=j['proc_start_ticks'] or f[0]=='Z'
finish=read(P/'FINISHED.json');assert finish['status']=='stopped_at_complete_cycle'
es=[json.loads(l) for l in (P/'episodes.jsonl').read_text().splitlines()];assert len(es)==30 and {e['condition'] for e in es}=={c['id'] for c in read(P.parent/'REGISTRATION.json')['conditions']}
assert all(e['cycle']==78 and math.isfinite(e['reward']) and e['full_task_horizon_completed'] and e['abort_reason'] is None for e in es)
assert sum(e['steps'] for e in es)==41250
r=dict(time=time.time(),method='vmc',cycle=78,runtime_only=True,full_checkpoint_review_pending=True,finish=finish,episodes=30,added_steps=41250,reward_mean=math.fsum(e['reward'] for e in es)/30,task=sum(e['task_success'] for e in es),strict=sum(e['strict_success'] for e in es),full_horizon=30,aborts=[],inputs={n:ref(P/n) for n in ['FINISHED.json','episodes.jsonl']},source=ref(Path(__file__)),convergence_claim=False,new_physics=0,optimizer_updates=0)
(D/'VMC78_RUNTIME_FINISHED.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
