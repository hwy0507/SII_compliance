from pathlib import Path
import json,time,hashlib,ast
D=Path(__file__).resolve().parent;B=D.parents[1]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
H=B/'runs/history89_raw_history_extension_20261030_v1';F=B/'runs/history89_violation_bit_paired_fit_20261030_v1'
assert read(H/'RUN_FINISHED.json')['passed'] and read(H/'FINISHED.json')['passed'] and read(F/'SAVED_REVIEW.json')['passed']
previous=read(F/'PLAN.json');inputs=[H/n for n in ('PLAN.json','REVIEW.json','SAVED_REVIEW.json','FINISHED.json')]+[F/n for n in ('PLAN.json','SAVED_REVIEW.json','PLOT_INSPECTION.json')]+[B/'runtime/history89_violation_bit_review_20261030_v1/SCIENTIFIC_DECISION.json']
inputs.append(D/'NUMERICAL_LAYOUT_CORRECTION.json')
for n in ('persisted_violation_critic.py','check_interface.py','register.py'):ast.parse((D/n).read_text())
plan=dict(time=time.time(),methods=['impedance','admittance','vmc'],cpu=12,device='cuda:1',budget_seconds=1800,initial_q_atol=1e-4,sources={n:sha(D/n) for n in ('persisted_violation_critic.py','check_interface.py','register.py')},restore_runtime=previous['restore_runtime'],restore_sources=previous['restore_sources'],inputs=[dict(path=str(p),sha256=sha(p)) for p in inputs],parent_cycle=89,old_dimensions=51,new_dimensions=52,actor_dimension=49,history_index=50,bit_index=51,feature='float(raw causal external penetration >0.0002m)',no_fitted_weights_imported=True,actual_parent_optimizer_updates=0,random_fixture_native_updates=12,physics_steps=0,training90=False,scope='Actual complete89 learner/replay inverse migration checks, all raw bits, next65536 sampling/RNG, native actions/contexts, serialization of learner and random fixture updates. No full replay disk/cache or complete frozen trajectory consumer check yet.')
with (D/'PLAN.json').open('x') as f:json.dump(plan,f,indent=2);f.write('\n')
print(sha(D/'PLAN.json'))
