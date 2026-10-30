from pathlib import Path
import json,hashlib,math,time
D=Path(__file__).resolve().parent;B=D.parents[1];S=B/'runs/parameter_violation90_92_reward_stability_20261030_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(S/'PLAN.json');assert plan['cycles']==[90,91,92] and plan['relative_limit']==.05 and plan['near_zero_guard']==1 and plan['replicates']==5000 and plan['bootstrap_seed']==2026102861
assert sha(S/'audit.py')==plan['source_sha256'] and sha(S/'review_saved.py')==plan['review_source_sha256']
r=read(D/'INTERPRETATION.json');assert r['passed'] and read(D/'INTERPRETATION_SAVED_REVIEW.json')['passed'];results={}
for m,v in r['methods'].items():
 rows=v['rows'];assert len(rows)==30;means=[math.fsum(x['reward'+str(c)] for x in rows)/30 for c in (90,91)]
 for c in (90,91):
  p=read(B/f'runs/parameter_violation_cycle{c}_20261030_v1'/m/'REGISTRATION.json');assert p['history_critic_amendment']==plan['history_amendment'][m] and p['violation_critic_amendment']==plan['violation_amendment'][m]
 near=any(abs(x)<plan['near_zero_guard'] for x in means);relative=None if near else abs(means[1]-means[0])/abs(means[0]);violates=relative is not None and relative>plan['relative_limit']
 results[m]=dict(cycles=[90,91],means=means,near_zero_guard_triggered=near,adjacent_relative_change=relative,necessary_five_percent_condition_violated=violates,complete_window_passed=False,reason='Observed first adjacency already exceeds original5percent; future92 cannot repair it' if violates else 'Near-zero guard prevents relative stability check' if near else 'This adjacency does not violate5percent; complete92 endpoint and second adjacency still required')
output=dict(time=time.time(),passed=True,original_plan_sha256=sha(S/'PLAN.json'),interpretation_sha256=sha(D/'INTERPRETATION.json'),methods=results,full_window_statistics_evaluated=False,bootstrap_performed=False,convergence_claim=False,automatic92=False,scope='Necessary condition only for original registered90-92; does not replace full-window audit or loss-health judgment; all30 outcomes and aborts retained')
with (D/'ADJACENT90_91_REVIEW.json').open('x') as out:json.dump(output,out,indent=2);out.write('\n')
print(json.dumps(results,indent=2))
