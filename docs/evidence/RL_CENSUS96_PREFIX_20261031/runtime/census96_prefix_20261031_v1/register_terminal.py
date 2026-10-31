from pathlib import Path
import json,time,ast
from terminal96 import B,D,O,sha,read,put
T=B/'runtime/census96_continuation_20261031_v1';RUN=B/'runs/parameter_census_cycle96_20261031_v1';F=O/'reference95';parent=read(B/'runs/parameter_census_cycle95_review_20261031_v1/REVIEW.json');reference=read(F/'REVIEW.json');assert reference['passed'];methods={};inputs=[]
for m in ['impedance','admittance','vmc']:
 e=parent['methods'][m];v=F/(m+'_values.npz');r=F/(m+'_REVIEW.json');reg=RUN/m/'REGISTRATION.json';known=[]
 if m=='impedance':known=[dict(cycle=c,replay_index=i,kind=k) for c,i,k in [(79,3264118,'historical_abort'),(90,3726050,'historical_abort'),(92,3804982,'historical_abort'),(93,3851694,'full55s_placement_failure_spike')]]
 methods[m]=dict(terminal_rows=2845 if m=='impedance' else 2844,prediction_block_boundaries=read(O/'REFERENCE_PLAN.json')['methods'][m]['prediction_block_boundaries'],parent_steps=e['steps'],parent_sha256=e['checkpoint_sha256'],baseline_values=str(v),baseline_sha256=sha(v),baseline_review=str(r),registration=str(reg),checkpoint=str(B/'runs/parameter_census_cycle96_archive_20261031_v1'/m/'cycle_00096.pt'),known_rows=known)
 for f in [v,r,reg]:inputs.append(dict(path=str(f),sha256=sha(f)))
for f in [O/'REFERENCE_PLAN.json',F/'REVIEW.json',D/'build_reference95.py',T/'SCIENTIFIC_DECISION.json',T/'CONTRACT_REVIEW.json',T/'CPU_CONSUMER_REVIEW.json',B/'runs/parameter_census_cycle95_review_20261031_v1/REVIEW.json',B/'runtime/census95_completion_20261031_v1/COMPLETE95_SCIENTIFIC_REVIEW.json']:
 inputs.append(dict(path=str(f),sha256=sha(f)))
repair=B/'runtime/census96_consumer_repair_20261031_v1';monitor=read(repair/'ARCHIVE_REPAIR_LAUNCH.json');s=Path('/proc',str(monitor['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==monitor['proc_start_ticks']
for n in ['terminal96.py','wait_terminal96.py']:ast.parse((D/n).read_text())
put(O/'PLAN.json',dict(time=time.time(),methods=methods,inputs=inputs,source_hashes={n:sha(D/n) for n in ['terminal96.py','wait_terminal96.py']},runtime_hashes=read(T/'SOURCES.json')['files'],restore_runtime=str(T),run=str(RUN),complete_review=str(B/'runs/parameter_census_cycle96_review_20261031_v1'),original_monitor=monitor,wait_deadline_unix=read(repair/'REPAIR_PLAN.json')['original_archive_deadline_unix'],analysis_budget_seconds=1200,baseline_prediction_key='initial_prediction',scope='All8533 full95 terminals,allfive/originalmasks;old<=94/new95,known79/90/92 aborts and93 spike retained; full96 required. CPU block sizes match full95 reference. Zero updates/physics,not heldout or convergence gate.',automatic97=False))
print('Registered all8533 fixed95 comparison, waiting for actual complete96')
