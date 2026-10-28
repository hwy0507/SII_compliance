from pathlib import Path
import json,hashlib,time,ast
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=Path(__file__).parent;condition='active_short_train_0600';records={}
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for c in [51,52]:
 run=B/f'runs/parameter_capacity_pool30_cycle{c}_20261026_v1/admittance/train';episode=run/f'cycle_{c:05d}'/condition
 roll=json.loads((episode/'rollout.json').read_text());terminal=json.loads((episode/'TERMINAL.json').read_text());source=(episode/'executed_evaluator.py.txt').read_text();ast.parse(source)
 assert "physical_valid=abort_reason is None and stats['max_external_penetration_m']<=.0002" in source
 assert "result['strict_success']=bool(result['task_success'] and result['physical_valid'])" in source
 value=roll['stats']['max_external_penetration_m'];expected=roll['abort_reason'] is None and value<=.0002
 assert expected==roll['physical_valid']==terminal['result']['physical_valid']
 assert roll['strict_success']==bool(roll['task_success'] and expected)
 rows=[json.loads(x) for x in (run/'transitions.jsonl').read_text().splitlines() if json.loads(x)['condition']==condition]
 assert len(rows)==1375 and sum(t['done'] for t in rows)==1 and rows[-1]['done']
 e=next(json.loads(x) for x in (run/'episodes.jsonl').read_text().splitlines() if json.loads(x)['condition']==condition)
 assert abs(sum(t['reward'] for t in rows)-e['reward'])<1e-8
 records[c]=dict(episode_reward=e['reward'],terminal_step=e['total_steps'],task=roll['task_success'],strict=roll['strict_success'],physical_valid=expected,external_penetration_m=value,external_penetration_mm=1000*value,gate_limit_mm=.2,margin_mm=.2-1000*value,worst_external_pair=roll['stats']['worst_external_pair'],terminal_reward=rows[-1]['reward'],terminal_terms=rows[-1]['reward_terms'],completion_time_s=terminal['completion_time_s'],model_sha256=sha(episode/'rollout.mjb'),inputs={n:dict(path=str(episode/n),sha256=sha(episode/n)) for n in ['rollout.json','TERMINAL.json','executed_evaluator.py.txt']})
assert records[51]['model_sha256']==records[52]['model_sha256'];assert records[51]['task'] and records[52]['task'];assert records[51]['strict'] and not records[52]['strict']
loss=json.loads((out/'REVIEW.json').read_text());event=next(r for r in loss['admittance52_all_terminal_neighborhoods'] if r['condition']==condition)
result=dict(time=time.time(),passed=True,condition=condition,cycles=records,model_unchanged=True,frozen_gate_unchanged=True,gate_arithmetic_verified=True,loss_neighborhood=event,episode_reward_delta=records[52]['episode_reward']-records[51]['episode_reward'],new_physics=0,optimizer_updates=0,causal_claim=False,limitation='Verifies recorded penetration/gate/terminal reward using saved rollout and executed evaluator. Does not independently reconstruct substep contact penetration. Temporal loss association is not replay-sample causality. No gate/reward/physics modification.')
(out/'GATE_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({c:{k:v for k,v in r.items() if k not in ['inputs','terminal_terms']} for c,r in records.items()},indent=2))
