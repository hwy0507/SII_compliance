from pathlib import Path
import sys,time,copy
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle100_20261031_v1'
sys.path.insert(0,str(D));from driver import read,ref,put
W=B/'runs/parameter_census100_102_reward_stability_20261031_v1';sys.path.insert(0,str(W));from binding_rules import locked,protocol,validate_registration
plan=locked(W);methods={}
assert plan['previous97_99_failed_report']==read(D/'STABILITY_WINDOW_INTENT.json')['previous97_99_failed_report']
assert not (R/'LAUNCH.json').exists()
for m in ['impedance','admittance','vmc']:
 p=read(R/m/'REGISTRATION.json');protocol(p,m,100,plan)
 parent=read(p['post_interruption_continuation']['parent_registration']['path'])
 assert p['replay_capacity_third_stage']==parent['replay_capacity_third_stage']==plan['third_capacity_stage'][m]
 assert p==read(plan['protocol100'][m]['path']) and not (R/m/'train').exists()
 rejected=[]
 for key in ['replay_capacity_third_stage','conditional_terminal_amendment','reward','history_critic_amendment','violation_critic_amendment']:
  bad=copy.deepcopy(p);bad[key]={}
  try:protocol(bad,m,100,plan)
  except (ValueError,KeyError,AssertionError):rejected.append(key)
  else:raise AssertionError('Mutated scientific window accepted')
 methods[m]=dict(registration=ref(R/m/'REGISTRATION.json'),unchanged_science=True,inherited_third_capacity_stage_exact=True,rejected=rejected)
from bind_inputs import build
for inputs in [{},{'impedance:100':{}}]:
 try:validate_registration(W,build(inputs))
 except (ValueError,KeyError,AssertionError):pass
 else:raise AssertionError('Incomplete window accepted')
put(D/'WINDOW100_102_PROTOCOL_REVIEW.json',dict(passed=True,time=time.time(),methods=methods,prospective_intent=plan['intent'],source=ref(W/'binding_rules.py'),cycles=[100,101,102],statistics_run=False,missing_future_inputs_rejected=True,original_failed_window=plan['previous97_99_failed_report'],scope='Pre100 nonoverlapping prospective100-102; original failures retained. No101/102 launch authorization.'))
