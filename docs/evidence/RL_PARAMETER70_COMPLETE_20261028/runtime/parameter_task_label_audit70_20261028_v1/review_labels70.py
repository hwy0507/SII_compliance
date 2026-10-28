"""Independent full69->70 saved label/count/reward cross-check; no training."""
from pathlib import Path
import json,math,hashlib,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
def read(p):return json.loads(p.read_text())
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
root=B/'runs/parameter_task_label_audit70_20261028_v1';loss=B/'runs/parameter70_loss_20261028_v1'
assert read(root/'FINISHED70.json')['completed'] and read(loss/'SAVED_REVIEW.json')['passed']
labels=read(root/'COMPLETE69_70.json');paired=read(loss/'PAIRED_GATE_REVIEW.json');lr=read(loss/'REVIEW.json')
assert labels['passed'] and labels['saved_rollouts_checked']==180 and paired['passed']
summary={}
for m,v in labels['methods'].items():
    rows=v['all30'];assert len(rows)==30
    pairs={x['condition']:x for x in paired['methods'][m]['all30_paired']};assert set(pairs)=={x['condition'] for x in rows}
    counts={}
    for i,cycle in enumerate([69,70]):
        r=next(x for x in lr['methods'][m]['reward_history'] if x['cycle']==cycle)
        assert math.isclose(math.fsum(x['cases'][i]['reward'] for x in rows)/30,r['reward_mean'],rel_tol=1e-12,abs_tol=1e-12)
        counts[str(cycle)]={key:sum(x['cases'][i][key] for x in rows) for key in ['task','strict','physical_valid']}
        assert counts[str(cycle)]==v['counts'][str(cycle)]
        assert all(counts[str(cycle)][k]==r[k] for k in ['task','strict'])
        for x in rows:assert x['cases'][i]['reward']==pairs[x['condition']][f'reward{cycle}']
    changed={x['condition'] for x in rows if 'strict' in x['changed_fields'] or 'abort_reason' in x['changed_fields']}
    assert changed=={x['condition'] for x in paired['methods'][m]['changes']}
    taskonly=[x for x in rows if 'task' in x['changed_fields'] and 'strict' not in x['changed_fields']]
    assert taskonly==v['task_only_changes']
    summary[m]=dict(counts=counts,changes=[dict(condition=x['condition'],fields=x['changed_fields'],cases=[{k:c[k] for k in ['cycle','task','strict','physical_valid','penetration_mm','reward']} for c in x['cases']]) for x in rows if x['changed_fields']],task_only_changes=[x['condition'] for x in taskonly])
result=dict(passed=True,time=time.time(),all90_reward_pairs_and_counts_match=True,strict_abort_changes_match_original=True,methods=summary,source=ref(root/'COMPLETE69_70.json'),reviewer_source=ref(Path(__file__)),new_physics=0,optimizer_updates=0)
out=root/'COMPLETE69_70_SAVED_REVIEW.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(summary,indent=2))
