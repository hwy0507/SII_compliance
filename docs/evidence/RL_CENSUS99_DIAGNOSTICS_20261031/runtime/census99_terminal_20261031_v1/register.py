from pathlib import Path
import sys,time,json
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census99_fixed98_terminal_20261031_v1';R=B/'runs/parameter_census_cycle99_20261031_v1';T=B/'runtime/census99_continuation_20261031_v1';N=B/'runs/census98_new_terminal_diagnosis_20261031_v1'
sys.path.insert(0,str(D));from terminal99 import read,put,sha
ref=lambda p:dict(path=str(p),sha256=sha(p))
old=read(B/'runs/census98_fixed97_terminal_20261031_v1/PLAN.json');diag=read(N/'DIAGNOSIS.json');methods={};inputs=[]
assert read(N/'reference98/REVIEW.json')['passed'] and diag['passed']
for m,e in old['methods'].items():
 rr=N/f'reference98/{m}_REVIEW.json';r=read(rr);reg=R/m/'REGISTRATION.json';p=read(reg);st=p['post_interruption_continuation'];assert r['checkpoint_sha256']==st['checkpoint']['sha256']
 known=list(e['known_rows']);largest=diag['methods'][m]['largest5'][0]
 known.append(dict(cycle=98,replay_index=largest['step']-1,kind='largest_new98_masked_residual_'+largest['condition']))
 if m=='vmc':
  q=diag['methods'][m]['short0600'];assert q['original_mask'][2]==0 and q['all5_sse']>1900 and not q['strict'];known.append(dict(cycle=98,replay_index=q['replay_index'],kind='new98_short0600_strict_loss_critic2_original_mask0_large_unmasked_residual'))
 methods[m]=dict(terminal_rows=r['terminal_rows'],prediction_block_boundaries=e['prediction_block_boundaries']+[r['terminal_rows']],parent_steps=st['parent_steps'],parent_sha256=st['checkpoint']['sha256'],baseline_values=r['values']['path'],baseline_sha256=r['values']['sha256'],baseline_review=str(rr),registration=str(reg),checkpoint=str(B/f'runs/parameter_census_cycle99_archive_20261031_v1/{m}/cycle_00099.pt'),known_rows=known)
 inputs.extend([ref(rr),r['values'],ref(reg)])
inputs.extend(ref(p) for p in [N/'reference98/REVIEW.json',N/'DIAGNOSIS.json',T/'SOURCES.json',T/'SCIENTIFIC_DECISION.json',B/'runtime/census98_completion_20261031_v1/COMPLETE98_SCIENTIFIC_REVIEW.json'])
assert sum(e['terminal_rows'] for e in methods.values())==8803
O.mkdir();put(O/'PLAN.json',dict(time=time.time(),methods=methods,inputs=inputs,source_hashes={p.name:sha(p) for p in D.glob('*.py')},runtime_hashes=read(T/'SOURCES.json')['files'],restore_runtime=str(T),run=str(R),complete_review=str(B/'runs/parameter_census_cycle99_review_20261031_v1'),original_monitor=read(R/'MONITOR_LAUNCH.json'),wait_deadline_unix=read(R/'LAUNCH.json')['time']+14400,analysis_budget_seconds=1200,baseline_prediction_key='initial_prediction',scope='All8803 full98 seen terminals, allfive/original masks and exact previous prediction blocks. All historical failures and98 largest residuals plus V short0600 mask0 case retained. Complete99 required. Zero training; not independent generalization.',automatic100=False))
print('All8803 terminal followup registered')
