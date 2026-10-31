from pathlib import Path
import sys,time,os,ast,difflib,json,hashlib
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle97_20261031_v1';OLD=B/'runtime/census96_continuation_20261031_v1'
sys.path[:0]=[str(D),str(B/'runtime/source_train17_clock/source/tools')]
from driver import read,sha,ref,put,expected_protocol,transform,parent_driver
from validate_published_finite_check_20261025 import digest
from persisted_history_critic import KEY as HK
from persisted_violation_critic import KEY as VK
import torch
os.sched_setaffinity(0,{54});torch.set_num_threads(1)
V=B/'runs/parameter_census_cycle96_review_20261031_v1';C=B/'runtime/census96_completion_20261031_v1';N=B/'runs/census96_new_terminal_diagnosis_20261031_v1';G=B/'runs/census_capacity6m_full96_20261031_v1';W=B/'runs/parameter_census94_96_reward_stability_20261031_v1'
evidence=[V/x for x in ['REVIEW.json','FINISHED.json','loss/REVIEW.json','health/DIAGNOSIS.json','PLOT_INSPECTION.json']]+[C/x for x in ['COMPLETE96_SCIENTIFIC_REVIEW.json','NEXT_FINITE_DECISION.json','WINDOW_BOOTSTRAP_SCALAR_REVIEW.json']]+[N/x for x in ['reference96/REVIEW.json','DIAGNOSIS.json','PLOT_INSPECTION.json']]+[G/'REVIEW.json',G/'PLAN.json',W/'REVIEW.json',W/'SOURCE_LOCK.json',OLD/'driver.py',OLD/'SOURCES.json',B/'runs/census_capacity6m_preparation_20261031_v1/REVIEW.json']
assert read(G/'REVIEW.json')['passed'] and read(N/'DIAGNOSIS.json')['passed'];full=read(V/'REVIEW.json');assert full['passed'];methods={}
for n,h in read(OLD/'SOURCES.json')['files'].items():assert sha(OLD/n)==h
for m in ['impedance','admittance','vmc']:
 cp=B/f'runs/parameter_census_cycle96_archive_20261031_v1/{m}/cycle_00096.pt';reg=B/f'runs/parameter_census_cycle96_20261031_v1/{m}/REGISTRATION.json';p=read(reg);ck=torch.load(cp,map_location='cpu',weights_only=False,mmap=True);parent_driver().validate_checkpoint(ck,p,complete=True)
 assert sha(cp)==full['methods'][m]['checkpoint_sha256']==read(G/'REVIEW.json')['methods'][m]['original_checkpoint_sha256'];assert ck['steps']<4000000<ck['steps']+41250<6000000
 stripped={k:v for k,v in ck['replay'].items() if k not in (HK,VK)}
 methods[m]=dict(parent_registration=ref(reg),checkpoint=ref(cp),steps=ck['steps'],updates=ck['learner']['num_gradient_steps'],history_digest=digest(ck['cycles']),stripped_replay_digest=digest(stripped),trainer=ref(B/f'runs/parameter_census_cycle96_20261031_v1/{m}/trainer_registered.py'));del ck,stripped
p=dict(time=time.time(),parent_cycle=96,new_cycle=97,new_cycles=1,maximum_new_actions_per_method=41250,automatic_followup=False,offline_weights_promoted=False,optimizer_settings_changed=False,reward_physics_changed=False,direct34=False,convergence_claim=False,launch_deadline_unix=time.time()+4*3600,methods=methods,evidence=[ref(f) for f in evidence],cycle_review=ref(V/'REVIEW.json'),complete_scientific_review=ref(C/'COMPLETE96_SCIENTIFIC_REVIEW.json'),terminal_review=ref(N/'DIAGNOSIS.json'),reason='Original94-96 A/V stability fails; V original loss spike and actor drift remain. New96 terminals/short0600 inspected: A late terminal only one subsequent transition, V strict penetration failure with critic1 masked out; no sampled-batch causal inference. All8623 full96 reference verified. One finite97 exact complete96 state, unchanged reward/physics/optimizer/census/masks; append-only4m->6m required to preserve all old rows. Full96 GPU next-update equivalence passed, no auxiliary weights. Preserve all prior failures, no automatic98/Direct34.')
put(D/'SCIENTIFIC_DECISION.json',p);jobs=[];source_reviews=[]
for i,m in enumerate(methods,1):
 (R/m).mkdir();reg=expected_protocol(m);put(R/m/'REGISTRATION.json',reg);old=Path(methods[m]['trainer']['path']).read_text();new=transform(old);ast.parse(new);delta=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='actual96',tofile='registered97'));(D/(m+'_trainer.diff')).write_text(delta)
 strippednew=new.replace('Finite97 new-transition budget exceeded','Finite96 new-transition budget exceeded')
 for indent in (8,12):strippednew=strippednew.replace('\n'+' '*indent+"replay_capacity_third_stage=protocol['replay_capacity_third_stage'],",'')
 assert strippednew==old
 first={'impedance':13,'admittance':26,'vmc':39}[m];jobs.append(dict(controller=m,command=[str(B/'env/bin/python'),str(D/'driver.py'),'--runtime',reg['runtime'],'--registration',str(R/m/'REGISTRATION.json'),'--resume',methods[m]['checkpoint']['path'],'--output',str(R/m/'train'),'--controller',m,'--cpus',','.join(map(str,range(first,first+13))),'--workers','30','--device','cuda:'+str(i)]));source_reviews.append(dict(method=m,trainer_delta_only_label_and_two_metadata_fields=True,parent=methods[m]['trainer'],registered_sha256=hashlib.sha256(new.encode()).hexdigest()))
put(R/'COMMANDS.json',dict(jobs=jobs));put(D/'PREFLIGHT_PLAN.json',dict(time=time.time(),budget_seconds=1800,maximum_disposable_updates=6,formal_updates=0,new_physics=0,scope='Finite97 real driver6m restore and twice repeated native65536; no weights retained; separate launch gate'))
put(D/'SOURCE_REVIEW.json',dict(passed=True,methods=source_reviews,census_source_byte_exact=sha(D/'census_native.py')==sha(OLD/'census_native.py'),capacity_module_byte_exact=sha(D/'parameter_replay_capacity6m.py')==sha(B/'runtime/census_capacity6m_preparation_20261031_v1/parameter_replay_capacity6m.py'),gamma_consumers_corrected_to_original_9995=True))
put(D/'STABILITY_WINDOW_INTENT.json',dict(time=time.time(),cycles=[97,98,99],bootstrap_seed=2026102861,replicates=5000,near_zero_guard=1.,relative_limit=.05,automatic_training=False,amendments={m:read(R/m/'REGISTRATION.json')['conditional_terminal_amendment'] for m in methods},third_capacity_stage={m:read(R/m/'REGISTRATION.json')['replay_capacity_third_stage'] for m in methods},original94_96_window=ref(W/'REVIEW.json'),scope='Fixed prospective97-99 reward description, before first97 launch; same5%/nearzero1/bootstrap rules, original failures retained. No reward-only convergence; original sampled loss/actor and final evaluation still required. Only97 currently authorized by finite decision.'))
put(D/'OBSERVATION_PLAN.json',dict(time=time.time(),startup_wait_seconds=2400,observe_seconds=120,interval_seconds=5,source_sha256=sha(D/'observe97.py')))
for f in D.glob('*.py'):ast.parse(f.read_text())
put(D/'SOURCES.json',dict(files={f.name:sha(f) for f in sorted(D.glob('*.py'))}));print('Finite97 registered; no online dispatch',flush=True)
