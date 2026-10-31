from pathlib import Path
import json,time,hashlib,ast
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle97_20261031_v1';P=B/'runs/parameter_census_cycle96_review_20261031_v1';F=B/'runs/census96_new_terminal_diagnosis_20261031_v1/reference96'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
assert read(P/'REVIEW.json')['passed'] and read(F/'REVIEW.json')['passed'];methods=['impedance','admittance','vmc']
prior=[P/n for n in ['REVIEW.json','FINISHED.json','health/DIAGNOSIS.json','loss/REVIEW.json','PLOT_INSPECTION.json']]+[R/m/'REGISTRATION.json' for m in methods]
prior += [B/'runtime/census97_continuation_20261031_v1/STABILITY_WINDOW_INTENT.json',B/'runs/parameter_census94_96_reward_stability_20261031_v1/REVIEW.json',B/'runs/census_capacity6m_full96_20261031_v1/REVIEW.json',R/'MONITOR_LAUNCH.json',R/'LAUNCH.json',D/'capacity_contract.py']
amendments={m:read(R/m/'REGISTRATION.json')['conditional_terminal_amendment'] for m in methods}
put(D/'COMPARISON_PLAN.json',dict(time=time.time(),source_sha256=sha(D/'interpret97.py'),prior_inputs={str(p):sha(p) for p in prior},conditional_amendments=amendments,parent_cycle=96,new_cycle=97,conditions_per_method=30,methods=methods,scope='All90 complete96-to97 training comparison; same estimator/scientific settings, explicit append-only capacity4m->6m. Original health loss/conditional/actor separated; all failures retained. Descriptive,not causal or a substitute for original94-96 failure/prospective97-99 window.',optimizer_updates=0,new_physics=0))
pop={};inputs={}
for m in methods:
 f=F/(m+'_values.npz');pop[m]=dict(baseline_values=str(f),terminal_rows=read(F/(m+'_REVIEW.json'))['terminal_rows'])
 for p in [f,R/m/'REGISTRATION.json']:inputs[str(p)]=sha(p)
assert sum(x['terminal_rows'] for x in pop.values())==8623
put(D/'CACHE_POPULATION_PLAN.json',dict(time=time.time(),source_sha256=sha(D/'check_terminal_population.py'),inputs=inputs,methods=pop,restore_runtime=str(B/'runtime/census97_continuation_20261031_v1'),scope='First5000 actual97 prefix and full97 after original complete review; baseline all8623 full96 terminals. Online total count,not online per-stratum tensor observation.'))
monitor=read(R/'MONITOR_LAUNCH.json');s=Path('/proc',str(monitor['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==monitor['proc_start_ticks'];deadline=min(j['time'] for j in read(R/'LAUNCH.json')['jobs'])+14400;assert time.time()<deadline
sourcefiles=['interpret97.py','changed_cases.py','compare_wait.py','check_terminal_population.py','capacity_contract.py']
for n in sourcefiles:ast.parse((D/n).read_text())
put(D/'WAIT_PLAN.json',dict(time=time.time(),source_hashes={n:sha(D/n) for n in sourcefiles},comparison_plan_sha256=sha(D/'COMPARISON_PLAN.json'),cache_population_plan_sha256=sha(D/'CACHE_POPULATION_PLAN.json'),original_monitor=monitor,deadline=deadline,analysis_budget_seconds=600,scope='Single read-only waiter along original97 archive budget; no training/duplicate archive.'))
print('Full96->97 all90 and terminal population registered')
