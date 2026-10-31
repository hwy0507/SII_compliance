from pathlib import Path
import sys,time,copy
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle99_20261031_v1'
sys.path.insert(0,str(D));from driver import read,ref,put
W=B/'runs/parameter_census97_99_reward_stability_20261031_v1';sys.path.insert(0,str(W));from binding_rules import locked,protocol
plan=locked(W);methods={}
for m in ['impedance','admittance','vmc']:
 p=read(R/m/'REGISTRATION.json');protocol(p,m,99,plan)
 parent=read(p['post_interruption_continuation']['parent_registration']['path'])
 assert p['replay_capacity_third_stage']==parent['replay_capacity_third_stage']==plan['third_capacity_stage'][m]
 assert not (R/m/'train').exists()
 rejected=[]
 for key in ['replay_capacity_third_stage','conditional_terminal_amendment','reward']:
  bad=copy.deepcopy(p);bad[key]={}
  try:protocol(bad,m,99,plan)
  except (ValueError,KeyError,AssertionError):rejected.append(key)
  else:raise AssertionError('Mutated scientific window accepted')
 methods[m]=dict(registration=ref(R/m/'REGISTRATION.json'),unchanged_science=True,inherited_third_capacity_stage_exact=True,rejected=rejected)
put(D/'WINDOW97_99_PROTOCOL_REVIEW.json',dict(passed=True,time=time.time(),methods=methods,original_prospective_intent=plan['intent'],source=ref(W/'binding_rules.py'),cycles=[97,98,99],statistics_run=False,scope='Finite99 conforms to original pre97 prospective97-99. Original94-96 failures retained, no automatic100.'))
