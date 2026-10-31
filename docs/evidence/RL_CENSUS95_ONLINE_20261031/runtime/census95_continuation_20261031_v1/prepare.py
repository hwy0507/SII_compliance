from pathlib import Path
import sys,time,json,hashlib,difflib,ast,os,subprocess,socket
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle95_20261031_v1';O=B/'runtime/census94_online_20261031_v1'
sys.path[:0]=[str(D),str(B/'runtime/source_train17_clock/source/tools')]
import torch
from validate_published_finite_check_20261025 import digest
from driver import sha,ref,put,read,expected_protocol,transform,parent_driver
os.sched_setaffinity(0,{11});torch.set_num_threads(1)
prior=B/'runtime/census94_completion_20261031_v1';fullroot=B/'runs/parameter_census_cycle94_review_20261031_v1'
evidence=[fullroot/n for n in ['REVIEW.json','FINISHED.json','loss/REVIEW.json','health/DIAGNOSIS.json','PLOT_INSPECTION.json']]
evidence += [prior/n for n in ['COMPLETE94_SCIENTIFIC_REVIEW.json','NEXT_FINITE_DECISION.json','FULL_LOSS_SAVED_REVIEW.json']]
evidence += [B/'runs/census94_fixed93_terminal_20261031_v1'/n for n in ['REVIEW.json','FINISHED.json','PLOT_INSPECTION.json']]
evidence += [B/'runtime/census94_comparison_20261031_v1'/n for n in ['CACHE_POPULATION_FULL_REVIEW.json','INTERPRETATION.json','CHANGED_CASES_REVIEW.json','PLOT_INSPECTION.json']]
evidence += [B/'repository/RL_COMPLETE94_20261031/PUBLICATION.json',O/'driver.py',O/'SOURCES.json',O/'SCIENTIFIC_DECISION.json',O/'STABILITY_WINDOW_INTENT.json']
full=read(fullroot/'REVIEW.json');assert full['passed'];assert read(prior/'COMPLETE94_SCIENTIFIC_REVIEW.json')['passed'];methods={}
for n,h in read(O/'SOURCES.json')['files'].items():assert sha(O/n)==h
for m in ['impedance','admittance','vmc']:
 cp=B/'runs/parameter_census_cycle94_archive_20261031_v1'/m/'cycle_00094.pt';oldreg=B/'runs/parameter_census_cycle94_20261031_v1'/m/'REGISTRATION.json';p=read(oldreg);ck=torch.load(cp,map_location='cpu',weights_only=False,mmap=True);parent_driver().validate_checkpoint(ck,p,complete=True)
 assert sha(cp)==full['methods'][m]['checkpoint_sha256'];assert ck['steps']+2*41250<=4000000
 methods[m]=dict(parent_registration=ref(oldreg),checkpoint=ref(cp),steps=ck['steps'],updates=ck['learner']['num_gradient_steps'],history_digest=digest(ck['cycles']),trainer=ref(B/'runs/parameter_census_cycle94_20261031_v1'/m/'trainer_registered.py'));del ck
p=dict(time=time.time(),parent_cycle=94,new_cycle=95,new_cycles=1,maximum_new_actions_per_method=41250,automatic_followup=False,offline_weights_promoted=False,optimizer_settings_changed=False,reward_physics_changed=False,direct34=False,convergence_claim=False,launch_deadline_unix=time.time()+4*3600,methods=methods,evidence=[ref(f) for f in evidence],cycle_review=ref(fullroot/'REVIEW.json'),complete_scientific_review=ref(prior/'COMPLETE94_SCIENTIFIC_REVIEW.json'),terminal_review=ref(B/'runs/census94_fixed93_terminal_20261031_v1/REVIEW.json'),reason='Full94 original losses decrease and all8353 fixed93 masked terminal SSE improves, but I/A original spikes, actor drift, A short0200 loss and per-row/unmasked regressions remain. Continue exactly one cycle95 with unchanged census estimator and all scientific settings, full trained94 learner/Adam/replay/RNG. Preserve94–96 fixed-window intent and all old failures; no95 success/stability or automatic96 claim. No auxiliary weights. Existing capacity fits95 and96 without changing retention.')
put(D/'SCIENTIFIC_DECISION.json',p);jobs=[];sources=[]
for i,m in enumerate(methods,1):
 (R/m).mkdir();reg=expected_protocol(m);put(R/m/'REGISTRATION.json',reg);old=Path(methods[m]['trainer']['path']).read_text();new=transform(old);assert new.replace("learner.load_state_dict(checkpoint['learner'])","learner.migrate_parent(checkpoint['learner'])").replace('Finite95 new-transition budget exceeded','Finite94 new-transition budget exceeded')==old
 ast.parse(new);(D/(m+'_trainer.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='actual94',tofile='registered95')));first={'impedance':13,'admittance':26,'vmc':39}[m];jobs.append(dict(controller=m,command=[str(B/'env/bin/python'),str(D/'driver.py'),'--runtime',reg['runtime'],'--registration',str(R/m/'REGISTRATION.json'),'--resume',methods[m]['checkpoint']['path'],'--output',str(R/m/'train'),'--controller',m,'--cpus',','.join(map(str,range(first,first+13))),'--workers','30','--device','cuda:'+str(i)]));sources.append(dict(method=m,parent_trainer=methods[m]['trainer'],patched_trainer_sha256=hashlib.sha256(new.encode()).hexdigest(),only_restore_call_and_error_cycle_label_changed=True,census_amendment_identical=reg['conditional_terminal_amendment']==read(methods[m]['parent_registration']['path'])['conditional_terminal_amendment']))
put(R/'COMMANDS.json',dict(jobs=jobs));put(D/'PREFLIGHT_PLAN.json',dict(time=time.time(),budget_seconds=1800,maximum_disposable_updates=6,formal_updates=0,new_physics=0,scope='Exact complete94 census restore, registration negatives, native65536 repeated update and restored state, strict CPU consumer; separate launch gate required'))
put(D/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),methods=sources,census_source_identical_to94=sha(D/'census_native.py')==sha(O/'census_native.py'),parent94_registered_sources_all_verified=True,original_scientific_settings_unchanged=True))
for f in D.glob('*.py'):ast.parse(f.read_text())
put(D/'OBSERVATION_PLAN.json',dict(time=time.time(),startup_wait_seconds=2400,observe_seconds=120,interval_seconds=5,source_sha256=sha(D/'observe95.py')))
put(D/'SOURCES.json',dict(files={f.name:sha(f) for f in sorted(D.glob('*.py'))}))
print('Registered finite95 from exact complete94, no physics launched',flush=True)
