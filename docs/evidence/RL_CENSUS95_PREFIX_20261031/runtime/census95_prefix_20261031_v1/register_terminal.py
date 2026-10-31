from pathlib import Path
import json,time,ast
from terminal95 import B,D,O,sha,read,put
T=B/'runtime/census95_continuation_20261031_v1';RUN=B/'runs/parameter_census_cycle95_20261031_v1';F=O/'reference94';parent=read(B/'runs/parameter_census_cycle94_review_20261031_v1/REVIEW.json');reference=read(F/'REVIEW.json');assert reference['passed'];methods={};inputs=[]
for m in ['impedance','admittance','vmc']:
 e=parent['methods'][m];v=F/(m+'_values.npz');r=F/(m+'_REVIEW.json');reg=RUN/m/'REGISTRATION.json';known=[]
 if m=='impedance':known=[dict(cycle=c,replay_index=i,kind=k) for c,i,k in [(79,3264118,'historical_abort'),(90,3726050,'historical_abort'),(92,3804982,'historical_abort'),(93,3851694,'full55s_placement_failure_spike')]]
 methods[m]=dict(terminal_rows=2815 if m=='impedance' else 2814,reference_old93_rows=2785 if m=='impedance' else 2784,parent_steps=e['steps'],parent_sha256=e['checkpoint_sha256'],baseline_values=str(v),baseline_sha256=sha(v),baseline_review=str(r),registration=str(reg),checkpoint=str(B/'runs/parameter_census_cycle95_archive_20261031_v1'/m/'cycle_00095.pt'),known_rows=known)
 for f in [v,r,reg]:inputs.append(dict(path=str(f),sha256=sha(f)))
for f in [O/'REFERENCE_PLAN.json',F/'REVIEW.json',D/'build_reference94.py',T/'SCIENTIFIC_DECISION.json',T/'CONTRACT_REVIEW.json',T/'CPU_CONSUMER_REVIEW.json',B/'runs/parameter_census_cycle94_review_20261031_v1/REVIEW.json',B/'runtime/census94_completion_20261031_v1/COMPLETE94_SCIENTIFIC_REVIEW.json']:
 inputs.append(dict(path=str(f),sha256=sha(f)))
monitor=read(RUN/'MONITOR_LAUNCH.json');s=Path('/proc',str(monitor['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==monitor['proc_start_ticks']
for n in ['terminal95.py','wait_terminal95.py']:ast.parse((D/n).read_text())
put(O/'PLAN.json',dict(time=time.time(),methods=methods,inputs=inputs,source_hashes={n:sha(D/n) for n in ['terminal95.py','wait_terminal95.py']},runtime_hashes=read(T/'SOURCES.json')['files'],restore_runtime=str(T),run=str(RUN),complete_review=str(B/'runs/parameter_census_cycle95_review_20261031_v1'),original_monitor=monitor,wait_deadline_unix=monitor['time']+14400,analysis_budget_seconds=1200,baseline_prediction_key='initial_prediction',scope='All8443 full94 terminals,allfive/originalmasks;old<=93/new94,known79/90/92 aborts and93 spike retained; full95 required. CPU block sizes match full94 reference. Zero updates/physics,not heldout or convergence gate.',automatic96=False))
print('Registered all8443 fixed94 comparison, waiting for actual complete95')
