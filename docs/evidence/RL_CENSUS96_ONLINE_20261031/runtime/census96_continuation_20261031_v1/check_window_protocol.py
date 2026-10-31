from pathlib import Path
import sys,json,time
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/parameter_census94_96_reward_stability_20261031_v1';R=B/'runs/parameter_census_cycle96_20261031_v1'
sys.path.insert(0,str(O));from binding_rules import locked,protocol,read,ref
plan=locked(O);methods={}
for m in ['impedance','admittance','vmc']:
 p=R/m/'REGISTRATION.json';st=protocol(read(p),m,96,plan);methods[m]=dict(registration=ref(p),fixed94_96_scientific_protocol_passed=True,parent_cycle=st['parent_cycle'],new_cycle=st['new_cycle'])
assert not (O/'REGISTRATION.json').exists() and not (O/'REVIEW.json').exists()
result=dict(passed=True,time=time.time(),methods=methods,prepared_window_plan=ref(O/'PLAN.json'),prepared_window_lock=ref(O/'SOURCE_LOCK.json'),protocol_checker=ref(O/'binding_rules.py'),complete96_inputs_bound=False,window_statistics_performed=False,physics_steps=0,optimizer_updates=0,scope='Only actual96 scientific registrations checked against unchanged locked94–96 window. Full checkpoint/episodes/loss/inspection input binding still requires completed95/96; no statistics or convergence inference.')
with (D/'WINDOW96_PROTOCOL_REVIEW.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print('Actual96 registrations match locked94–96 scientific window; full inputs/statistics pending')
