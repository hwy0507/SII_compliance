from pathlib import Path
import copy,json,time
from capacity_contract import verify_science
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle100_20261031_v1';results={}
for m in ['impedance','admittance','vmc']:
 p=json.loads((R/m/'REGISTRATION.json').read_text());old=json.loads(Path(p['post_interruption_continuation']['parent_registration']['path']).read_text());assert verify_science(p,old);rejected=[]
 for case in ['changed_physics','missing_condition','wrong_capacity','missing_third_stage','wrong_capacity_parent','changed_estimator']:
  bad=copy.deepcopy(p)
  if case=='changed_physics':bad['physics_dt_s']=.0001
  elif case=='missing_condition':bad['conditions'].pop()
  elif case=='wrong_capacity':bad['replay_capacity_third_stage']['marker']['capacity']=4000000
  elif case=='missing_third_stage':bad.pop('replay_capacity_third_stage')
  elif case=='wrong_capacity_parent':bad['replay_capacity_third_stage']['entry_checkpoint']['sha256']='0'*64
  elif case=='changed_estimator':bad['conditional_terminal_amendment']['marker']['version']=100
  try:verify_science(bad,old)
  except (ValueError,AssertionError,KeyError):rejected.append(case)
  else:raise AssertionError('Changed scientific contract accepted: '+case)
 results[m]=dict(unchanged_inherited_capacity_accepted=True,rejected=rejected)
with (D/'CAPACITY_COMPARISON_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),methods=results,negative_count=18,physics_steps=0,optimizer_updates=0),f,indent=2);f.write('\n')
print('Unchanged6m comparison accepted;18 unintended changes rejected')
