"""Arithmetic necessary-condition check for locked94–96 window, not full statistics."""
from pathlib import Path
import sys,json,hashlib,time,math
D=Path(__file__).resolve().parent;B=D.parents[1];W=B/'runs/parameter_census94_96_reward_stability_20261031_v1';sys.path.insert(0,str(W));from binding_rules import locked,ref,read
p=locked(W);methods={};inputs=[]
for m in ['impedance','admittance','vmc']:
 means=[]
 for c in [94,95]:
  rv=B/f'runs/parameter_census_cycle{c}_review_20261031_v1/REVIEW.json';rr=read(rv);assert rr['passed'];ep=B/f'runs/parameter_census_cycle{c}_20261031_v1/{m}/train/episodes.jsonl';es=[json.loads(x) for x in ep.read_text().splitlines()];assert len(es)==30 and len({e['condition'] for e in es})==30 and all(e['cycle']==c for e in es)
  mean=math.fsum(e['reward'] for e in es)/30;assert math.isclose(mean,rr['methods'][m]['reward_mean'],abs_tol=1e-12);means.append(mean);inputs.extend([ref(rv),ref(ep)])
 near=any(abs(x)<p['near_zero_guard'] for x in means);relative=None if near else abs(means[1]-means[0])/abs(means[0]);methods[m]=dict(means94_95=means,near_zero_guard_triggered=near,adjacent_relative_change=relative,necessary_five_percent_condition_fails=near or relative>p['relative_limit'],full_window_pass_claim=False)
assert not (W/'REGISTRATION.json').exists() and not (W/'REVIEW.json').exists()
x=dict(passed=True,time=time.time(),methods=methods,plan=ref(W/'PLAN.json'),inputs=inputs,fixed_window=[94,95,96],bootstrap_run=False,complete96_missing=True,full_window_pass_claim=False,scope='Independent scalar sums on complete94/95 original30 episode logs. Existing94->95 adjacent5% necessary condition only, not full94–96 statistics or health acceptance; original window/source unchanged.')
with (D/'EARLY_WINDOW94_95_REVIEW.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(methods,indent=2))
