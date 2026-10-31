from pathlib import Path
import sys,time,copy
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle97_20261031_v1'
sys.path.insert(0,str(D));from driver import read,ref,put
W=B/'runs/parameter_census94_96_reward_stability_20261031_v1';sys.path.insert(0,str(W));from binding_rules import locked,protocol
from parameter_replay_capacity6m import MARKER
oldplan=locked(W);intent=read(D/'STABILITY_WINDOW_INTENT.json');assert intent['cycles']==[97,98,99] and not intent['automatic_training']
for key,value in [('bootstrap_seed',2026102861),('replicates',5000),('near_zero_guard',1.),('relative_limit',.05)]:assert intent[key]==value==oldplan[key]
methods={}
for m in ['impedance','admittance','vmc']:
 p=read(R/m/'REGISTRATION.json');st=protocol(p,m,97,oldplan);cap=p['replay_capacity_third_stage'];assert cap['marker']==MARKER and cap['parent_cycle']==96 and cap['first_cycle']==97
 assert intent['amendments'][m]==p['conditional_terminal_amendment'] and intent['third_capacity_stage'][m]==cap
 assert not (R/m/'train').exists()
 methods[m]=dict(registration=ref(R/m/'REGISTRATION.json'),original_science_unchanged=True,capacity6m_explicit=True)
assert read(W/'REVIEW.json')['methods']['admittance']['descriptive_five_percent_check'] is False
put(D/'WINDOW97_PROTOCOL_REVIEW.json',dict(passed=True,time=time.time(),methods=methods,prospective_intent=ref(D/'STABILITY_WINDOW_INTENT.json'),original94_96_failed_window=ref(W/'REVIEW.json'),scientific_protocol_checker=ref(W/'binding_rules.py'),physics_steps=0,optimizer_updates=0,scope='Prospective97-99 intent before first97 launch; unchanged statistical rules; complete input binder/statistics still pending. Only97 dispatched separately, no automatic98/99.'))
