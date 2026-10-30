from pathlib import Path
import json,time,hashlib,math
D=Path(__file__).parent;B=D.parents[1]
read=lambda p:json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
plan=read(D/'PLAN.json');result={}
for v in plan['inputs'].values():
 if 'sha256' in v:assert sha(v['path'])==v['sha256']
for c in [78,79,80]:
 case=Path(plan['inputs'][f'{c}:TERMINAL.json']['path']).parent;terminal=read(case/'TERMINAL.json');roll=read(case/'rollout.json')
 es=[json.loads(l) for l in Path(plan['inputs'][f'{c}:episodes']['path']).read_text().splitlines()];matches=[x for x in es if x['cycle']==c and x['condition']==plan['condition']];assert len(matches)==1;e=matches[0]
 rows=[json.loads(l) for l in (case/'actor_intervals.jsonl').read_text().splitlines()];assert len(rows)==e['steps'] and rows[0]['interval'] is None
 for k in ['task_success','strict_success','abort_reason','full_task_horizon_completed']:assert e[k]==terminal['result'][k]
 intervals=[v['interval'] for v in rows[1:]]+[terminal['interval']];substeps=sum(v['substeps'] for v in intervals);seconds=math.fsum(v['elapsed_s'] for v in intervals)
 assert substeps==800*e['steps'] and math.isclose(seconds,e['steps']*.04,abs_tol=1e-8) and math.isclose(seconds,terminal['terminal_time_s'],abs_tol=1e-7)
 assert e['model_sha256']==sha(case/'rollout.mjb')
 result[str(c)]=dict(episode=e,actual_time_s=terminal['terminal_time_s'],recorded_interval_substeps=substeps,all_intervals_include_terminal=True,recorded_global_penetration_m=roll['stats']['max_penetration_m'],worst_pair=roll['stats']['worst_pair'],terminal_sha256=sha(case/'TERMINAL.json'),model_sha256=sha(case/'rollout.mjb'),executed_evaluator_sha256=sha(case/'executed_evaluator.py.txt'))
assert len({v['model_sha256'] for v in result.values()})==len({v['executed_evaluator_sha256'] for v in result.values()})==1
assert result['79']['episode']['abort_reason']=='global_penetration_exceeded_2mm' and not result['79']['episode']['physical_valid']
assert result['80']['episode']['task_success'] and result['80']['episode']['strict_success'] and result['80']['episode']['steps']==1375 and result['80']['recorded_global_penetration_m']<.002
for c in [78,79,80]:
 p=D/f'episode{c}.json'
 with p.open('x') as f:json.dump(result[str(c)]['episode'],f,indent=2);f.write('\n')
r=dict(passed=True,time=time.time(),cycles=result,original79_failure_preserved=True,source_sha256=sha(__file__),new_physics=0,new_updates=0,independent_raw_substep_reconstruction=False,root_cause_established=False,convergence_claim=False,scope=plan['scope'])
with (D/'REVIEW.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps({k:{n:v for n,v in x.items() if n not in ['episode','terminal_sha256','model_sha256','executed_evaluator_sha256']} for k,x in result.items()},indent=2))
