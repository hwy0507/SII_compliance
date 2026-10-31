from pathlib import Path
import json,time,ast
from terminal94 import B,D,O,sha,read,put
O.mkdir();T=B/'runtime/census94_online_20261031_v1';RUN=B/'runs/parameter_census_cycle94_20261031_v1';F=B/'runs/violation93_potential_ablation_20261031_v1';parent=read(B/'runs/parameter_violation_cycle93_review_20261031_v1/REVIEW.json');methods={};inputs=[]
for m in ['impedance','admittance','vmc']:
 e=parent['methods'][m];v=F/(m+'_values.npz');r=F/(m+'_REVIEW.json');reg=RUN/m/'REGISTRATION.json';known=[]
 if m=='impedance':known=[dict(cycle=c,replay_index=i,kind=k) for c,i,k in [(79,3264118,'historical_abort'),(90,3726050,'historical_abort'),(92,3804982,'historical_abort'),(93,3851694,'full55s_placement_failure_spike')]]
 methods[m]=dict(terminal_rows=2785 if m=='impedance' else 2784,parent_steps=e['steps'],parent_sha256=e['checkpoint_sha256'],baseline_values=str(v),baseline_sha256=sha(v),baseline_review=str(r),registration=str(reg),checkpoint=str(B/'runs/parameter_census_cycle94_archive_20261031_v1'/m/'cycle_00094.pt'),known_rows=known)
 for f in [v,r,reg]:inputs.append(dict(path=str(f),sha256=sha(f)))
for f in [F/'SAVED_REVIEW.json',T/'SCIENTIFIC_DECISION.json',T/'CONTRACT_REVIEW.json',T/'CPU_CONSUMER_REVIEW.json',B/'runs/parameter_violation_cycle93_review_20261031_v1/REVIEW.json']:
 inputs.append(dict(path=str(f),sha256=sha(f)))
monitor=read(RUN/'MONITOR_LAUNCH.json');print(monitor)
for n in ['terminal94.py','wait_terminal94.py']:ast.parse((D/n).read_text())
# Original archive started with the original learner batch, whose launch timestamp is explicit.
launch=read(RUN/'LAUNCH.json');print({k:v for k,v in launch.items() if k!='jobs'})
put(O/'PLAN.json',dict(time=time.time(),methods=methods,inputs=inputs,source_hashes={n:sha(D/n) for n in ['terminal94.py','wait_terminal94.py']},runtime_hashes=read(T/'SOURCES.json')['files'],restore_runtime=str(T),run=str(RUN),complete_review=str(B/'runs/parameter_census_cycle94_review_20261031_v1'),original_monitor=monitor,wait_deadline_unix=monitor['time']+14400,analysis_budget_seconds=1200,baseline_prediction_key='initial_prediction',scope='All8353 full93 terminals, all five critics and original masks; all old/new93 and known failures retained; full94 required, strict census-aware CPU restoration, zero updates or physics; not held-out test/convergence gate',automatic95=False))
