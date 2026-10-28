from pathlib import Path
import json,hashlib,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=Path(__file__).parent;methods={}
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for m in ['impedance','admittance','vmc']:
 maps=[];refs={}
 for c in [64,65]:
  p=B/f'runs/parameter_capacity_pool30_cycle{c}_20261026_v1/{m}/train/episodes.jsonl';maps.append({e['condition']:e for e in map(json.loads,p.read_text().splitlines())});refs[str(p)]=sha(p)
 assert len(maps[0])==len(maps[1])==30 and set(maps[0])==set(maps[1]);changes=[];paired=[]
 for condition,new in maps[1].items():
  old=maps[0][condition];paired.append(dict(condition=condition,reward64=old['reward'],reward65=new['reward'],delta=new['reward']-old['reward']))
  if old['strict_success']==new['strict_success'] and old['abort_reason']==new['abort_reason']:continue
  cases=[]
  for c,e in zip([64,65],[old,new]):
   folder=Path(e['episode_path']);roll=json.loads((folder/'rollout.json').read_text());src=(folder/'executed_evaluator.py.txt').read_text();assert "physical_valid=abort_reason is None and stats['max_external_penetration_m']<=.0002" in src
   physical=roll['abort_reason'] is None and roll['stats']['max_external_penetration_m']<=.0002;assert physical==roll['physical_valid'];assert bool(roll['task_success'] and physical)==roll['strict_success']==e['strict_success']
   cases.append(dict(cycle=c,task=e['task_success'],strict=e['strict_success'],reward=e['reward'],step=e['total_steps'],actions=e['steps'],abort_reason=e['abort_reason'],global_penetration_mm=1000*roll['stats']['max_penetration_m'],worst_pair=roll['stats'].get('worst_pair'),penetration_mm=1000*roll['stats']['max_external_penetration_m'],physical_valid=physical,model_sha256=sha(folder/'rollout.mjb'),rollout=dict(path=str(folder/'rollout.json'),sha256=sha(folder/'rollout.json')),evaluator_sha256=sha(folder/'executed_evaluator.py.txt')))
  assert cases[0]['model_sha256']==cases[1]['model_sha256'];changes.append(dict(condition=condition,cases=cases))
 methods[m]=dict(changes=changes,all30_paired=paired,mean_reward_delta=sum(x['delta'] for x in paired)/30,inputs=refs)
report=dict(time=time.time(),passed=True,methods=methods,new_physics=0,optimizer_updates=0,gate_unchanged=True,causal_claim=False,limitation='All30 paired reward deltas retained, changed strict or abort labels checked against saved penetration and executed evaluator. No independent substep contact recomputation; does not establish replay sampling causality or modify original reward/gate.')
(out/'PAIRED_GATE_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({m:[x for x in r['changes'] if x['condition']=='active_short_train_0600'] for m,r in methods.items()},indent=2))
