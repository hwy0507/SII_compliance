"""Register one finite history88 amendment and prepare real-state preflight."""
from pathlib import Path
import os,sys,json,time,copy,hashlib,ast
D=Path(__file__).parent;B=D.parents[1];I=B/'runtime/history87_critic_interface_20261030_v1';R=B/'runs/parameter_history_cycle88_20261030_v1';P=B/'runs/parameter_partial75_recovery_cycle87_20261029_v1';A=B/'runs/parameter_partial75_recovery_cycle87_archive_20261029_v1';V=B/'runs/parameter_partial75_recovery_cycle87_review_20261029_v1'
sys.path[:0]=[str(D),str(B/'runtime/source_train17_clock/source/tools')]
from driver import transform,validate_protocol,sha,read,put
ref=lambda p:dict(path=str(p),sha256=sha(p))
assert not R.exists()
for n in ['REVIEW.json','CACHE_SAVED_REVIEW.json','CONSUMER_REVIEW.json','FINISHED.json']:assert read(I/n)['passed']
assert read(V/'FINISHED.json')['completed'] and read(V/'REVIEW.json')['passed'] and read(P/'ARCHIVE_REVIEW_FINISHED.json')['completed']
for j in read(P/'LAUNCH.json')['jobs']:
 f=Path(f'/proc/{j["pid"]}/stat')
 if f.exists():v=f.read_text().rsplit(')',1)[1].split();assert v[19]!=j['proc_start_ticks'] or v[0]=='Z'
required=[V/'REVIEW.json',V/'health/DIAGNOSIS.json',B/'runs/parameter_recovery87_loss_20261029_v1/SAVED_REVIEW.json',B/'runs/parameter_recovery85_87_reward_stability_20261030_v1/REVIEW.json',B/'runs/parameter_recovery85_87_reward_stability_20261030_v1/SAVED_ARITHMETIC_REVIEW.json',B/'runs/parameter_recovery85_87_reward_stability_20261030_v1/PLOT_INSPECTION.json',B/'runs/recovery87_history_extension_20261030_v1/SAVED_REVIEW.json',B/'runs/recovery87_terminal_history_paired_fit_20261030_v1/REVIEW.json',B/'runs/recovery87_terminal_history_paired_fit_20261030_v1/SAVED_REVIEW.json',B/'runs/recovery87_terminal_history_paired_fit_20261030_v1/PLOT_INSPECTION.json',B/'runtime/half_std86_complete_history87_20261030_v1/HALF_STD_DECISION.json',B/'runtime/recovery87_completion_preparation_20261030_v1/DECISION87.json']
required += [I/n for n in ['PLAN.json','REVIEW.json','CACHE_SAVED_REVIEW.json','CONSUMER_REVIEW.json','FINISHED.json']]
for p in required:
 value=read(p)
 if 'passed' in value:assert value['passed']
 if 'actual_image_viewed' in value:assert value['actual_image_viewed']
methods={};hist=read(B/'runs/recovery87_history_extension_20261030_v1/REVIEW.json')
for m in ['impedance','admittance','vmc']:
 binding=read(I/(m+'_BINDING.json'));methods[m]=dict(version=1,kind='causal_history_critic_information_amendment',parent_cycle=87,first_cycle=88,binding=binding,sidecar=hist['methods'][m]['sidecar'],actor_information_dimension=49,critic_replay_dimension=51,feature_index=50,feature='p/(p+0.0002)',online_history='consume completed interval once before next observation and action',weights_from_offline_fit=False,optimizer_hyperparameters_changed=False,target_entropy_changed=False,new_weight_moments_zero=True,old_replay_rows_retained=True,clock_projection_and_target_pair_unchanged=True,physical_and_reward_contract_unchanged=True)
put(D/'AMENDMENT.json',dict(time=time.time(),methods=methods))
put(D/'SCIENTIFIC_DECISION.json',dict(time=time.time(),parent_cycle=87,new_cycle=88,new_cycles=1,maximum_new_actions_per_method=41250,architecture_changed=True,unchanged_automatic_continuation=False,automatic_followup=False,convergence_claim=False,direct34=False,evidence=[ref(p) for p in required],reason='Complete85-87 reward stability failed for all methods; late I/V loss rises and retained-terminal drift remain. Matched complete87 terminal fitting favored history for all15 critic endpoints but is in-sample, not proof of online benefit. Full exact-parent history51 migration, native interfaces, RNG/replay/Adam, projection and restore tests passed. Test this single causal history-critic information amendment in one bounded30-condition cycle, preserving all previous data, actor inputs, LR/reward/masks and physics. Offline fitted weights are not imported. Uniform half-std/entropy reduction is not supported and is not changed. This decision permits only one finite trial after integration preflight, not a convergence claim or automatic89.'))
R.mkdir();(B/'runs/parameter_history_cycle88_review_20261030_v1').mkdir();jobs=[]
for oldjob in read(P/'LAUNCH.json')['jobs']:
 m=oldjob['controller'];dest=R/m;dest.mkdir();(dest/'check').mkdir();parent=P/m/'REGISTRATION.json';p=read(parent);old=p['post_interruption_continuation'];trainer=P/m/'trainer_registered.py';cp=A/m/'cycle_00087.pt';assert sha(cp)==methods[m]['binding']['checkpoint_sha256']
 st=dict(old,parent_cycle=87,new_cycle=88,parent_registration=ref(parent),checkpoint=ref(cp),cycle_review=ref(V/'REVIEW.json'),health_review=ref(V/'health/DIAGNOSIS.json'),previous_driver=ref(B/'runtime/prepare_recovery87_20261030_v1/resume_recovery86.py'),driver_sha256=sha(D/'driver.py'),trainer_path=str(trainer),trainer_sha256=sha(trainer),patched_trainer_sha256=hashlib.sha256(transform(trainer.read_text()).encode()).hexdigest(),physical_semantics='One separately registered history51 information amendment from exact complete87. Retain all partial75 exposure and complete-cycle history, no old/new revision pooling or automatic89.')
 p['post_interruption_continuation']=st;p['history_critic_amendment']=methods[m];validate_protocol(st['parent_registration']['sha256'],p);put(dest/'REGISTRATION.json',p)
 cmd=list(oldjob['command']);cmd[1]=str(D/'driver.py')
 for flag,val in [('--registration',dest/'REGISTRATION.json'),('--resume',cp),('--output',dest/'train')]:cmd[cmd.index(flag)+1]=str(val)
 jobs.append(dict(controller=m,command=cmd))
put(R/'COMMANDS.json',dict(jobs=jobs,automatic_training=False))
files={p.name:sha(p) for p in D.glob('*.py')}
for p in D.glob('*.py'):ast.parse(p.read_text())
put(D/'SOURCES.json',dict(time=time.time(),files=files))
put(D/'PREFLIGHT_PLAN.json',dict(time=time.time(),sources=ref(D/'SOURCES.json'),cpu_allocation=[13,26,39],devices=['cuda:1','cuda:2','cuda:3'],disposable_native_updates=6,batch=65536,formal_updates=0,new_physics=0,budget_seconds=1800,require_metadata_rejection_tests=True,require_frozen_gate_and_health_integration=True,automatic_training=False))
print('Registered finite amendment; no physics dispatched')
