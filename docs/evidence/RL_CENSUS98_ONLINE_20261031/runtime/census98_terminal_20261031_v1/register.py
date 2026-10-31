from pathlib import Path
import sys,json,time,hashlib
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census98_fixed97_terminal_20261031_v1';R=B/'runs/parameter_census_cycle98_20261031_v1';T=B/'runtime/census98_continuation_20261031_v1';N=B/'runs/census97_new_terminal_diagnosis_20261031_v1'
sys.path.insert(0,str(D));from terminal98 import read,put,sha
ref=lambda p:dict(path=str(p),sha256=sha(p))
old=read(B/'runs/census97_fixed96_terminal_20261031_v1/PLAN.json');methods={};inputs=[]
assert read(N/'reference97/REVIEW.json')['passed'] and read(N/'DIAGNOSIS.json')['passed']
for m,e in old['methods'].items():
 rr=N/f'reference97/{m}_REVIEW.json';r=read(rr);reg=R/m/'REGISTRATION.json';p=read(reg);st=p['post_interruption_continuation'];assert r['checkpoint_sha256']==st['checkpoint']['sha256']
 known=list(e['known_rows'])
 if m=='impedance':known.append(dict(cycle=97,replay_index=4013182,kind='largest_new97_masked_residual_long0000'))
 if m=='admittance':known.append(dict(cycle=97,replay_index=4021249,kind='largest_new97_masked_residual_final_long0100'))
 if m=='vmc':known.append(dict(cycle=97,replay_index=4021832,kind='largest_new97_masked_residual_long0300'))
 methods[m]=dict(terminal_rows=r['terminal_rows'],prediction_block_boundaries=e['prediction_block_boundaries']+[r['terminal_rows']],parent_steps=st['parent_steps'],parent_sha256=st['checkpoint']['sha256'],baseline_values=r['values']['path'],baseline_sha256=r['values']['sha256'],baseline_review=str(rr),registration=str(reg),checkpoint=str(B/f'runs/parameter_census_cycle98_archive_20261031_v1/{m}/cycle_00098.pt'),known_rows=known)
 inputs.extend([ref(rr),r['values'],ref(reg)])
inputs.extend(ref(p) for p in [N/'reference97/REVIEW.json',N/'DIAGNOSIS.json',T/'SOURCES.json',T/'SCIENTIFIC_DECISION.json'])
assert sum(e['terminal_rows'] for e in methods.values())==8713
O.mkdir()
put(O/'PLAN.json',dict(time=time.time(),methods=methods,inputs=inputs,source_hashes={p.name:sha(p) for p in D.glob('*.py')},runtime_hashes=read(T/'SOURCES.json')['files'],restore_runtime=str(T),run=str(R),complete_review=str(B/'runs/parameter_census_cycle98_review_20261031_v1'),original_monitor=read(R/'MONITOR_LAUNCH.json'),wait_deadline_unix=read(R/'LAUNCH.json')['time']+14400,analysis_budget_seconds=1200,baseline_prediction_key='initial_prediction',scope='All8713 full97 seen terminals,allfive/original masks. Includes all old failures and97 largest residuals; needs complete98. Zero training; not independent generalization.',automatic99=False))
print('All8713 terminal followup registered')
