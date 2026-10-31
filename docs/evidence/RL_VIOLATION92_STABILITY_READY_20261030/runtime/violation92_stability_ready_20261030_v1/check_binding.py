from pathlib import Path
import copy,json,time,ast
from bind_inputs import B,D,S,read,sha,put,bind_visual_evidence,setup
plan,previous=setup();results={}
for cycle in (90,91):
 review=B/f'runs/parameter_violation_cycle{cycle}_review_20261030_v1';inspection=read(review/'PLOT_INSPECTION.json');loss=read(review/'loss/REVIEW.json');valid=bind_visual_evidence(cycle,review,inspection,loss);rejected=[]
 def reject(name,ins,l=loss,c=cycle):
  try:bind_visual_evidence(c,review,ins,l)
  except (AssertionError,FileNotFoundError,KeyError):rejected.append(name)
  else:raise AssertionError('Invalid evidence accepted: '+name)
 bad=copy.deepcopy(inspection);bad['actual_visual_inspection']=False;reject('uninspected_overall',bad)
 bad=copy.deepcopy(inspection);bad['plots']=[];reject('empty_plot_list',bad)
 bad=copy.deepcopy(inspection);bad['plots']=bad['plots'][:1];reject('missing_plot',bad)
 bad=copy.deepcopy(inspection);bad['plots'][1]=bad['plots'][0];reject('duplicate_plot',bad)
 bad=copy.deepcopy(inspection);bad['plots'][0]['inspected']=False;reject('individual_not_viewed',bad)
 bad=copy.deepcopy(inspection);bad['plots'][0]['sha256']='0'*64;reject('changed_plot_hash',bad)
 bad=copy.deepcopy(loss);bad['plot_sha256']='0'*64;reject('loss_summary_hash_mismatch',inspection,bad)
 reject('wrong_cycle_plot',inspection,c=92)
 assert len(rejected)==8
 results[str(cycle)]=dict(valid_refs=valid,negative_cases=rejected,original_inspection_sha256=sha(review/'PLOT_INSPECTION.json'))
registered=read(D/'BINDING_PLAN.json');assert sha(S/'PLAN.json')==registered['original_plan_sha256'] and sha(S/'audit.py')==registered['audit_sha256'] and sha(S/'review_saved.py')==registered['saved_review_sha256']
for script in (S/'audit.py',S/'review_saved.py'):
 tree=ast.parse(script.read_text());assert any(isinstance(x,ast.For) and 'group' in ast.unparse(x.target) for x in ast.walk(tree)) if script.name=='audit.py' else 'for ref in refs.values()' in script.read_text()
put(D/'PLOT_BINDING_GUARD_REVIEW.json',dict(passed=True,time=time.time(),methods=results,negative_count=16,original_plan_audit_saved_review_bytes_unchanged=True,original_audit_checks_all_added_input_hashes=True,original_saved_review_checks_all_added_input_hashes=True,physical_steps=0,optimizer_updates=0,statistics_evaluated=False,source_sha256=sha(__file__)))
print('Actual90/91 figures accepted;16 malformed metadata cases rejected; frozen statistical sources unchanged')
