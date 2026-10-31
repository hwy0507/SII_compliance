from pathlib import Path
import json,time,hashlib,ast
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle96_20261031_v1';Q=B/'runtime/census96_consumer_repair_20261031_v1';P=B/'runs/parameter_census_cycle95_review_20261031_v1';F=B/'runs/census96_fixed95_terminal_20261031_v1/reference95'
rd=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
assert rd(P/'REVIEW.json')['passed'] and rd(F/'REVIEW.json')['passed']
prior=[P/n for n in ['REVIEW.json','FINISHED.json','health/DIAGNOSIS.json','loss/REVIEW.json','PLOT_INSPECTION.json']]
prior.extend(R/m/'REGISTRATION.json' for m in ['impedance','admittance','vmc'])
prior += [B/'runtime/census94_online_20261031_v1/STABILITY_WINDOW_INTENT.json',B/'runtime/census95_completion_20261031_v1/EARLY_WINDOW94_95_REVIEW.json',Q/'REPAIR_PLAN.json',Q/'ARCHIVE_REPAIR_LAUNCH.json']
methods=['impedance','admittance','vmc'];amendments={m:rd(R/m/'REGISTRATION.json')['conditional_terminal_amendment'] for m in methods}
for m in methods:assert amendments[m]['first_cycle']==94
put(D/'COMPARISON_PLAN.json',dict(time=time.time(),source_sha256=sha(D/'interpret96.py'),prior_inputs={str(p):sha(p) for p in prior},conditional_amendments=amendments,parent_cycle=95,new_cycle=96,conditions_per_method=30,methods=methods,scope='All90 complete95-to96 training comparison,same census estimator; original sampled loss/conditional/actor separated,all regressions retained. Descriptive,not causal/not fixed94–96 stability proof; A94->95 necessary-condition failure preserved.',optimizer_updates=0,new_physics=0))
pop={};inputs={}
for m in methods:
 f=F/(m+'_values.npz');pop[m]=dict(baseline_values=str(f),terminal_rows=rd(F/(m+'_REVIEW.json'))['terminal_rows'])
 for p in [f,R/m/'REGISTRATION.json']:inputs[str(p)]=sha(p)
assert sum(x['terminal_rows'] for x in pop.values())==8533
put(D/'CACHE_POPULATION_PLAN.json',dict(time=time.time(),source_sha256=sha(D/'check_terminal_population.py'),inputs=inputs,methods=pop,restore_runtime=str(B/'runtime/census96_continuation_20261031_v1'),scope='First5000 actual96 prefix and full96 after original complete review; baseline all8533 full95 terminals. Online total count,not online per-stratum tensor observation.'))
monitor=rd(Q/'ARCHIVE_REPAIR_LAUNCH.json');s=Path('/proc',str(monitor['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==monitor['proc_start_ticks'];deadline=rd(Q/'REPAIR_PLAN.json')['original_archive_deadline_unix'];assert time.time()<deadline
sourcefiles=['interpret96.py','changed_cases.py','compare_wait.py','check_terminal_population.py']
for n in sourcefiles:ast.parse((D/n).read_text())
put(D/'WAIT_PLAN.json',dict(time=time.time(),source_hashes={n:sha(D/n) for n in sourcefiles},comparison_plan_sha256=sha(D/'COMPARISON_PLAN.json'),cache_population_plan_sha256=sha(D/'CACHE_POPULATION_PLAN.json'),original_monitor=monitor,deadline=deadline,analysis_budget_seconds=600,scope='Single read-only waiter follows corrected archive with unchanged original96 deadline; complete population audit follows all90 comparison,zero training.'))
print('All90 comparison and complete population registered; no physics/training launched')
