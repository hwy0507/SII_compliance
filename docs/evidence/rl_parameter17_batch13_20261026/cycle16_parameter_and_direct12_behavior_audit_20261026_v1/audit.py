from pathlib import Path
import os,json,hashlib,time,collections
os.sched_setaffinity(0,{53})
import numpy as np
b=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=Path(__file__).parent
reg=json.loads((out/'REGISTRATION.json').read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def lines(p):
 with p.open() as f:return [json.loads(line) for line in f if line.endswith('\n')]
report=dict(new_optimizer_updates=0,new_physics=0,methods={},direct={},sources=[],limitations=['Paired conditions but evolving stochastic policies and histories; descriptive comparison, not isolated causal batch or target-horizon effect.','First160 Direct actions are matched duration, not matched states or action RNG. No physics or threshold change.'])
for ref in reg['reviews']:
 assert sha(ref['path'])==ref['sha256'] and json.loads(Path(ref['path']).read_text())['passed']
for method in ['impedance','admittance','vmc']:
 roots=[b/'runs'/name/method/'train' for name in ['parameter_batch65536_cycle15_20261026_v1','parameter_batch65536_cycle16_20261026_v1']]
 episodes=[{r['condition']:r for r in lines(root/'episodes.jsonl')} for root in roots];assert len(episodes[0])==len(episodes[1])==30 and episodes[0].keys()==episodes[1].keys()
 contexts=[]
 for root in roots:
  data=collections.defaultdict(list)
  for row in lines(root/'transitions.jsonl'):data[row['condition']].append(row['context'])
  contexts.append(data)
  for name in ['episodes.jsonl','transitions.jsonl']:report['sources'].append(dict(path=str(root/name),sha256=sha(root/name)))
 pairs=[]
 for name,old in episodes[0].items():
  new=episodes[1][name];values=[np.asarray(d[name],np.float64) for d in contexts];assert all(len(v)==1375 for v in values)
  pairs.append(dict(condition=name,category=old['category'],reward_before=old['reward'],reward_after=new['reward'],reward_delta=new['reward']-old['reward'],task_before=old['task_success'],task_after=new['task_success'],strict_before=old['strict_success'],strict_after=new['strict_success'],mean_authority=[float(v.mean()) for v in values],minimum_authority_fraction=[float(np.mean(v<=.200001)) for v in values]))
 categories={}
 for category in sorted({v['category'] for v in pairs}):
  rows=[v for v in pairs if v['category']==category]
  categories[category]=dict(conditions=len(rows),task_before=sum(v['task_before'] for v in rows),task_after=sum(v['task_after'] for v in rows),mean_reward_delta=float(np.mean([v['reward_delta'] for v in rows])),mean_authority_before=float(np.mean([v['mean_authority'][0] for v in rows])),mean_authority_after=float(np.mean([v['mean_authority'][1] for v in rows])))
 report['methods'][method]=dict(pairs=pairs,categories=categories,lost_task_conditions=[v['condition'] for v in pairs if v['task_before'] and not v['task_after']],gained_task_conditions=[v['condition'] for v in pairs if not v['task_before'] and v['task_after']],lost_strict_conditions=[v['condition'] for v in pairs if v['strict_before'] and not v['strict_after']],gained_strict_conditions=[v['condition'] for v in pairs if not v['strict_before'] and v['strict_after']])
roots=[b/'runs'/name/'direct' for name in ['serl_multistep_gather_cycle11_20261026_v1','serl_multistep_transfer_cycle12_20261026_v1']]
episodes=[{r['condition']:r for r in lines(root/'episodes.jsonl')} for root in roots];assert len(episodes[0])==len(episodes[1])==30 and episodes[0].keys()==episodes[1].keys();pairs=[]
for name,old in episodes[0].items():
 new=episodes[1][name];arrays=[]
 for e in [old,new]:
  path=Path(e['episode_path'])/'actor_intervals.jsonl';rows=lines(path);assert len(rows)==e['steps'];actions=np.asarray([v['action'] for v in rows],np.float64);assert actions.shape[1]==7 and len(actions)>=160 and np.isfinite(actions).all();arrays.append(actions);report['sources'].append(dict(path=str(path),sha256=sha(path)))
 pairs.append(dict(condition=name,actions_before=len(arrays[0]),actions_after=len(arrays[1]),task_before=old['task_success'],task_after=new['task_success'],final_stage_before=old['final_task_stage'],final_stage_after=new['final_task_stage'],abort_before=old['abort_reason'],abort_after=new['abort_reason'],first160_mean_actions=[a[:160].mean(axis=0).tolist() for a in arrays],whole_episode_mean_actions=[a.mean(axis=0).tolist() for a in arrays],first160_residual_saturation_fraction=[float(np.mean(abs(a[:160,1:])>.95)) for a in arrays]))
report['direct']=dict(pairs=pairs,first160_mean_actions=np.mean([v['first160_mean_actions'] for v in pairs],axis=0).tolist(),first160_residual_saturation_fraction=np.mean([v['first160_residual_saturation_fraction'] for v in pairs],axis=0).tolist(),stage_counts=[dict(collections.Counter(v[k] for v in pairs)) for k in ['final_stage_before','final_stage_after']],public_channel0_semantics='0 is nominal; larger slows WBC; no thresholds altered')
report.update(passed=True,time=time.time());(out/'REVIEW.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');print(json.dumps(dict(parameter={m:{'categories':v['categories'],'lost':v['lost_task_conditions'],'gained':v['gained_task_conditions']} for m,v in report['methods'].items()},direct={k:v for k,v in report['direct'].items() if k!='pairs'}),indent=2))
