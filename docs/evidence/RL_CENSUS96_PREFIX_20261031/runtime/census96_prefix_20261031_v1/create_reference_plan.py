from pathlib import Path
import json,time,hashlib,ast
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census96_fixed95_terminal_20261031_v1';T=B/'runtime/census95_continuation_20261031_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
full=read(B/'runs/parameter_census_cycle95_review_20261031_v1/REVIEW.json');assert full['passed'];oldroot=B/'runs/census95_fixed94_terminal_20261031_v1';prior=read(oldroot/'PLAN.json');methods={};inputs=[]
for m in ['impedance','admittance','vmc']:
 root=B/'runs/parameter_census_cycle95_20261031_v1'/m;cp=B/'runs/parameter_census_cycle95_archive_20261031_v1'/m/'cycle_00095.pt';old=prior['methods'][m];n=old['terminal_rows'];assert n==(2815 if m=='impedance' else 2814)
 e=dict(checkpoint=ref(cp),registration=ref(root/'REGISTRATION.json'),old_values=ref(oldroot/(m+'_values.npz')),old_review=ref(oldroot/(m+'_REVIEW.json')),transitions=ref(root/'train/transitions.jsonl'),episodes=ref(root/'train/episodes.jsonl'),terminal_rows=n+30,prediction_block_boundaries=[0,old['reference_old93_rows'],n,n+30]);assert e['checkpoint']['sha256']==full['methods'][m]['checkpoint_sha256'];methods[m]=e;inputs.extend(e[k] for k in ['checkpoint','registration','old_values','old_review','transitions','episodes'])
for n in ['REVIEW.json','FINISHED.json','health/DIAGNOSIS.json','PLOT_INSPECTION.json']:inputs.append(ref(B/'runs/parameter_census_cycle95_review_20261031_v1'/n))
inputs += [ref(oldroot/'PLAN.json'),ref(oldroot/'REVIEW.json'),ref(B/'runtime/census95_completion_20261031_v1/COMPLETE95_SCIENTIFIC_REVIEW.json')]
for p in D.glob('*.py'):ast.parse(p.read_text())
plan=dict(time=time.time(),deadline_unix=time.time()+1200,methods=methods,inputs=inputs,restore_runtime=str(T),runtime_hashes=read(T/'SOURCES.json')['files'],source_sha256=sha(D/'build_reference95.py'),scope='All8533 retained95 terminals including90new95,allfive/originalmasks. Preserve original<=93 and new94 CPU block shapes to reproduce saved complete95 predictions bitwise; add new95 third block. Strict full learner/Adam/replay/RNG unchanged,zerooptimizer/physics,no96 data or auxiliary weights.')
with (O/'REFERENCE_PLAN.json').open('x') as f:json.dump(plan,f,indent=2);f.write('\n')
print('All8533 full95 reference registered before forwards')
