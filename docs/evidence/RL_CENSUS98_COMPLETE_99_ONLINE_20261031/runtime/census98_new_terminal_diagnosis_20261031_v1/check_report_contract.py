from pathlib import Path
import json,copy,time,hashlib,ast
from fixed_report_contract import check_fixed_report
D=Path(__file__).resolve().parent;B=D.parents[1];F=B/'runs/census97_fixed96_terminal_20261031_v1';V=B/'runs/parameter_census_cycle97_review_20261031_v1';O=B/'runs/census98_new_terminal_diagnosis_20261031_v1';rd=lambda p:json.loads(p.read_text());aggregate=rd(F/'REVIEW.json');full=rd(V/'REVIEW.json');results={}
for m in ['impedance','admittance','vmc']:
 original=rd(F/(m+'_REVIEW.json'));values=F/(m+'_values.npz');expected=full['methods'][m]['checkpoint_sha256'];assert 'passed' not in original and check_fixed_report(aggregate,original,m,expected,values);rejections=[]
 for label in ['root_failed','root_missing_passed','row_mismatch','wrong_checkpoint','state_changed','arithmetic_unverified','values_hash_changed','method_missing','state_marker_missing']:
  a=copy.deepcopy(aggregate);r=copy.deepcopy(original)
  if label=='root_failed':a['passed']=False
  elif label=='root_missing_passed':a.pop('passed')
  elif label=='row_mismatch':r['regression_rows']+=1
  elif label=='wrong_checkpoint':r['checkpoint_sha256']='0'*64;a['methods'][m]=r
  elif label=='state_changed':r['full_learner_optimizer_replay_rng_unchanged']=False;a['methods'][m]=r
  elif label=='arithmetic_unverified':r['saved_scalar_arithmetic_verified']=False;a['methods'][m]=r
  elif label=='values_hash_changed':r['values_sha256']='0'*64;a['methods'][m]=r
  elif label=='method_missing':a['methods'].pop(m)
  elif label=='state_marker_missing':r.pop('full_learner_optimizer_replay_rng_unchanged');a['methods'][m]=r
  try:check_fixed_report(a,r,m,expected,values)
  except (KeyError,AssertionError):rejections.append(label)
  else:raise AssertionError('Invalid fixed-terminal report accepted: '+label)
 results[m]=dict(actual_complete97_schema_accepted=True,per_method_passed_field_absent=True,checkpoint_sha256=expected,rejected=rejections)
s=(D/'wait_diagnosis.py').read_text();tree=ast.parse(s);fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='bind');calls=[x for x in ast.walk(fn) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='check_fixed_report'];assert len(calls)==1
with (O/'REPORT_CONTRACT_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),methods=results,negative_count=27,actual_binder_calls_checked_contract=True,source_sha256=hashlib.sha256((D/'fixed_report_contract.py').read_bytes()).hexdigest(),scope='Actual prior complete97 fixed-report schema accepted;27 in-memory corruptions rejected. No fake98 outputs or neural inference.',physics_steps=0,optimizer_updates=0),f,indent=2);f.write('\n')
print('Actual three97 reports accepted,27 corruption rejections')
