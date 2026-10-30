"""Independent scalar arithmetic of the existing fixed88-90 report."""
from pathlib import Path
import hashlib,json,math,os,time
os.sched_setaffinity(0,{54})
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def near(a,b):assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),(a,b)
reg=read(ROOT/'REGISTRATION.json');report=read(ROOT/'REVIEW.json')
assert report['passed'] and reg['cycles']==[88,89,90]
assert reg['relative_limit']==.05 and reg['near_zero_guard']==1 and reg['bootstrap_replicates']==5000
assert sha(ROOT/'reward_stability.png')==report['plot_sha256']
results={}
for method,record in report['methods'].items():
    means=[];maps=[]
    for cycle,summary in zip(reg['cycles'],record['cycles']):
        refs=reg['inputs'][f'{method}:{cycle}']
        for ref in refs.values():assert sha(Path(ref['path']))==ref['sha256']
        episodes=[json.loads(s) for s in Path(refs['episodes']['path']).read_text().splitlines()]
        assert len(episodes)==30 and len({e['condition'] for e in episodes})==30
        mean=math.fsum(e['reward'] for e in episodes)/30;means.append(mean)
        near(mean,summary['reward_mean'])
        assert sum(e['task_success'] for e in episodes)==summary['task']
        assert sum(e['strict_success'] for e in episodes)==summary['strict']
        assert sum(e['full_task_horizon_completed'] for e in episodes)==summary['full_horizon']
        logs=[json.loads(s) for s in Path(refs['optimizer']['path']).read_text().splitlines()]
        assert len(logs)==sum(e['steps'] for e in episodes)
        for log in logs:
            assert all(math.isfinite(v) for v in log.values() if isinstance(v,(int,float)))
        q=[x['agent_train/q_loss'] for x in logs]
        near(math.fsum(q)/len(q),summary['q_loss_mean'])
        near(math.fsum(q[:1000])/1000,summary['q_loss_first1000'])
        near(math.fsum(q[-1000:])/1000,summary['q_loss_last1000'])
        assert max(q)==summary['q_loss_maximum']
        maps.append({e['condition']:e['reward'] for e in episodes})
    zero=any(abs(m)<1 for m in means);assert zero==record['near_zero_guard_triggered']
    adjacent=[abs(means[i+1]-means[i])/abs(means[i]) for i in range(2)] if not zero else None
    endpoint=abs(means[2]-means[0])/abs(means[0]) if not zero else None
    if zero:assert record['adjacent_relative_mean_changes'] is None and record['endpoint_relative_mean_change'] is None
    else:
        for a,b in zip(adjacent,record['adjacent_relative_mean_changes']):near(a,b)
        near(endpoint,record['endpoint_relative_mean_change'])
    passed=not zero and max(adjacent+[endpoint])<=.05
    assert passed==record['descriptive_five_percent_check']
    assert len(record['paired_conditions'])==30
    for pair in record['paired_conditions']:
        assert pair['rewards']==[m[pair['condition']] for m in maps]
    deltas=[maps[2][k]-maps[0][k] for k in sorted(maps[0])]
    near(math.fsum(deltas)/30,record['paired88_to90_mean_delta'])
    near((means[2]-means[0])/2,record['slope'])
    assert sum(x>0 for x in deltas)==record['improved_conditions']
    assert sum(x<0 for x in deltas)==record['worsened_conditions']
    results[method]=dict(means=means,adjacent_relative=adjacent,endpoint_relative=endpoint,five_percent_passed=passed)
(ROOT/'SAVED_ARITHMETIC_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),methods=results,
    review_sha256=sha(ROOT/'REVIEW.json'),source_sha256=sha(Path(__file__)),bootstrap_reruns=0,
    bootstrap_intervals_independently_recomputed=False,original_aborts_and_actual_lengths_retained=True,
    plot_inspected=False,convergence_claim=False),indent=2)+'\n')
print(json.dumps(results,indent=2))
