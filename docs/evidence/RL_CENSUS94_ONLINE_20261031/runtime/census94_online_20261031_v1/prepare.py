from pathlib import Path
import sys,time,json,hashlib,copy,difflib,ast,os
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle94_20261031_v1'
sys.path[:0]=[str(D),str(B/'runtime/source_train17_clock/source/tools')]
import torch
from validate_published_finite_check_20261025 import digest
from driver import sha,ref,put,expected_protocol,transform
os.sched_setaffinity(0,{11});torch.set_num_threads(1)
evidence=[B/'runs/parameter_violation_cycle93_review_20261031_v1'/n for n in ['REVIEW.json','FINISHED.json','loss/REVIEW.json','health/DIAGNOSIS.json','PLOT_INSPECTION.json']]
evidence += [B/'runs/census93_native_compatibility_20261031_v2'/n for n in ['SAVED_REVIEW.json','FINISHED.json','CACHE_EDGE_REVIEW.json','ADAM_ALIAS_REVIEW.json','LOSS_EDGE_REVIEW.json','EXECUTION_REVIEW.json']]
evidence += [B/'runs/violation93_terminal_census_ablation_20261031_v1'/n for n in ['SAVED_REVIEW.json','MATH_PREFLIGHT.json','FINISHED.json','PLOT_INSPECTION.json']]
evidence += [B/'repository/RL_CENSUS93_NATIVE_COMPATIBILITY_20261031/PUBLICATION.json',B/'runtime/host_recovery_census93_20261031_v1/COLD_RESTORE_REVIEW.json']
full=json.loads((B/'runs/parameter_violation_cycle93_review_20261031_v1/REVIEW.json').read_text());assert full['passed']
methods={}
for m in ['impedance','admittance','vmc']:
 cp=B/'runs/parameter_violation_cycle93_archive_20261031_v1'/m/'cycle_00093.pt';ck=torch.load(cp,map_location='cpu',weights_only=False,mmap=True);assert sha(cp)==full['methods'][m]['checkpoint_sha256'];methods[m]=dict(parent_registration=ref(B/'runs/parameter_violation_cycle93_20261031_v1'/m/'REGISTRATION.json'),checkpoint=ref(cp),steps=ck['steps'],updates=ck['learner']['num_gradient_steps'],history_digest=digest(ck['cycles']),trainer=ref(B/'runs/parameter_violation_cycle93_20261031_v1'/m/'trainer_registered.py'));del ck
p=dict(time=time.time(),parent_cycle=93,new_cycle=94,new_cycles=1,maximum_new_actions_per_method=41250,automatic_followup=False,offline_weights_promoted=False,optimizer_settings_changed=False,reward_physics_changed=False,direct34=False,convergence_claim=False,launch_deadline_unix=time.time()+4*3600,methods=methods,evidence=[ref(f) for f in evidence],cycle_review=ref(evidence[0]),native_review=ref(B/'runs/census93_native_compatibility_20261031_v2/SAVED_REVIEW.json'),ablation_review=ref(B/'runs/violation93_terminal_census_ablation_20261031_v1/SAVED_REVIEW.json'),reason='Full93 remains nonconverged with original loss spikes and adjacent reward changes. Conditional terminal census reduces full terminal masked SSE and original sampled mean losses in finite critic controls, but I maximum/new93 and V unmasked regressions remain. Full-native source/gradient/sampler/actor-target-temperature/growing-cache/save-reload compatibility now passes all3; original Adam/RNG/full formal93 preserved. Register exactly one online94 to test with changing policy/targets and new physical data, preserve all failures, record original sampled loss separately, no offline weights or actor information changes. Review complete94 before any95. This first estimator cycle cannot prove three-cycle stability.')
put(D/'SCIENTIFIC_DECISION.json',p);jobs=[]
for i,m in enumerate(methods,1):
 (R/m).mkdir();reg=expected_protocol(m);put(R/m/'REGISTRATION.json',reg);old=Path(methods[m]['trainer']['path']).read_text();new=transform(old);(D/(m+'_trainer.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='actual93',tofile='registered94')));first={'impedance':13,'admittance':26,'vmc':39}[m];jobs.append(dict(controller=m,command=[str(B/'env/bin/python'),str(D/'driver.py'),'--runtime',reg['runtime'],'--registration',str(R/m/'REGISTRATION.json'),'--resume',methods[m]['checkpoint']['path'],'--output',str(R/m/'train'),'--controller',m,'--cpus',','.join(map(str,range(first,first+13))),'--workers','30','--device','cuda:'+str(i)]))
put(R/'COMMANDS.json',dict(jobs=jobs));put(D/'PREFLIGHT_PLAN.json',dict(time=time.time(),budget_seconds=1800,maximum_disposable_updates=6,formal_updates=0,new_physics=0,scope='Exact93 migration, registration negatives, native65536 repeated update, strict consumer restore; online requires separate gate'))
print('Registered finite94 from formal93; no physics launched',flush=True)
