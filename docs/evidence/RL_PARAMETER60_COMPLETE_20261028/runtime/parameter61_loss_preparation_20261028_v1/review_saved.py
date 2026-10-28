"""Independently verify saved complete61 loss and paired statistics."""
from pathlib import Path
import hashlib, json, math, os, time
os.sched_setaffinity(0, {54})
OUT=Path(__file__).resolve().parent
B=OUT.parents[1]
def read(p): return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def finite(value):
    if isinstance(value,dict): return all(finite(v) for v in value.values())
    if isinstance(value,list): return all(finite(v) for v in value)
    if isinstance(value,(int,float)): return math.isfinite(value)
    return True
def near(a,b): assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),(a,b)
r=read(OUT/'REVIEW.json'); paired=read(OUT/'PAIRED_GATE_REVIEW.json')
assert read(OUT/'FINISHED.json')['completed'] and paired['passed']
assert sha(OUT/'loss.png')==r['plot_sha256']
methods={}
for m,report in r['methods'].items():
    for source in report['inputs'].values(): assert sha(Path(source['path']))==source['sha256']
    root=B/f'runs/parameter_capacity_pool30_cycle61_20261026_v1/{m}/train'
    logs=[json.loads(s) for s in (root/'optimizer.jsonl').read_text().splitlines()]
    episodes=[json.loads(s) for s in (root/'episodes.jsonl').read_text().splitlines()]
    assert len(episodes)==30 and len({e['condition'] for e in episodes})==30
    assert len(logs)==sum(e['steps'] for e in episodes) and all(finite(x) for x in logs)
    assert all(x['step']==logs[0]['step']+i for i,x in enumerate(logs))
    for k,s in report['loss'].items():
        values=[x[k] for x in logs]
        assert len(values)==s['count'] and min(values)==s['minimum'] and max(values)==s['maximum']
        near(math.fsum(values)/len(values),s['mean'])
        near(math.fsum(values[:1000])/1000,s['first1000']); near(math.fsum(values[-1000:])/1000,s['last1000'])
    assert report['full_horizon']==sum(e['full_task_horizon_completed'] for e in episodes)
    assert report['aborts']==[e for e in episodes if e['abort_reason']]
    for h in report['reward_history']:
        p=B/f"runs/parameter_capacity_pool30_cycle{h['cycle']}_20261026_v1/{m}/train/episodes.jsonl"
        es=[json.loads(s) for s in p.read_text().splitlines()]
        assert len(es)==30
        near(math.fsum(e['reward'] for e in es)/30,h['reward_mean'])
        assert sum(e['task_success'] for e in es)==h['task'] and sum(e['strict_success'] for e in es)==h['strict']
    pr=paired['methods'][m]
    for path,h in pr['inputs'].items(): assert sha(Path(path))==h
    maps=[]
    for c in [60,61]:
        p=B/f'runs/parameter_capacity_pool30_cycle{c}_20261026_v1/{m}/train/episodes.jsonl'
        maps.append({e['condition']:e for e in map(json.loads,p.read_text().splitlines())})
    assert len(pr['all30_paired'])==30 and {x['condition'] for x in pr['all30_paired']}==set(maps[0])==set(maps[1])
    for v in pr['all30_paired']:
        assert v['reward60']==maps[0][v['condition']]['reward'] and v['reward61']==maps[1][v['condition']]['reward']
        near(v['reward61']-v['reward60'],v['delta'])
    near(math.fsum(v['delta'] for v in pr['all30_paired'])/30,pr['mean_reward_delta'])
    expected={k for k in maps[0] if any(maps[0][k][field]!=maps[1][k][field] for field in ['strict_success','abort_reason'])}
    assert {v['condition'] for v in pr['changes']}==expected
    for change in pr['changes']:
        for case in change['cases']:
            p=Path(case['rollout']['path']);folder=p.parent;roll=read(p)
            assert sha(p)==case['rollout']['sha256'] and sha(folder/'rollout.mjb')==case['model_sha256']
            assert sha(folder/'executed_evaluator.py.txt')==case['evaluator_sha256']
            assert "physical_valid=abort_reason is None and stats['max_external_penetration_m']<=.0002" in (folder/'executed_evaluator.py.txt').read_text()
            physical=roll['abort_reason'] is None and roll['stats']['max_external_penetration_m']<=.0002
            assert physical==case['physical_valid'] and bool(roll['task_success'] and physical)==case['strict']
            near(1000*roll['stats']['max_external_penetration_m'],case['penetration_mm'])
    methods[m]=dict(count=len(logs),all_numeric_fields_finite=True,independent_arithmetic=True,
        full_horizon=report['full_horizon'],abort_count=len(report['aborts']),paired_sources_and_model_evaluator_hashes_verified=True)
(OUT/'SAVED_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),plot_inspected=False,
    source_sha256=sha(Path(__file__)),methods=methods,convergence_claim=False,new_physics=0,optimizer_updates=0),indent=2)+'\n')
print(json.dumps(methods,indent=2))
