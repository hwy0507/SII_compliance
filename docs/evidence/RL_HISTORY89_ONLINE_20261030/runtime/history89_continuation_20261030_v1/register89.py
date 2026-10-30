"""Explicit one-cycle budget decision after complete88 review, not automatic continuation."""
from pathlib import Path
import json,time,sys,hashlib,ast
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_history_cycle89_20261030_v1';P=B/'runs/parameter_history_cycle88_20261030_v2';A=B/'runs/parameter_history_cycle88_archive_20261030_v2';V=B/'runs/parameter_history_cycle88_review_20261030_v2';T=B/'runs/history88_fixed87_terminal_followup_20261030_v1';C=B/'runtime/history88_completion_20261030_v1'
sys.path[:0]=[str(D),str(B/'runtime/source_train17_clock/source/tools')]
from driver import read,sha,put,transform,validate_protocol
ref=lambda p:dict(path=str(p),sha256=sha(p))
assert not R.exists()
required=[V/'REVIEW.json',V/'FINISHED.json',V/'health/DIAGNOSIS.json',V/'loss/REVIEW.json',V/'PLOT_INSPECTION.json',T/'REVIEW.json',T/'FINISHED.json',T/'PLOT_INSPECTION.json',C/'INTERPRETATION.json',C/'PLOT_INSPECTION.json',B/'runs/parameter_history88_90_reward_stability_20261030_v1/PLAN.json']
for p in required:
 x=read(p)
 if 'passed' in x:assert x['passed']
 if 'actual_visual_inspection' in x:assert x['actual_visual_inspection']
assert read(V/'FINISHED.json')['completed']
for j in read(P/'LAUNCH.json')['jobs']:
 assert read(P/j['controller']/'train/FINISHED.json')['status']=='stopped_at_complete_cycle'
 q=Path(f'/proc/{j["pid"]}/stat')
 if q.exists():f=q.read_text().rsplit(')',1)[1].split();assert f[19]!=j['proc_start_ticks'] or f[0]=='Z'
put(D/'SCIENTIFIC_DECISION.json',dict(time=time.time(),parent_cycle=88,new_cycle=89,new_cycles=1,maximum_new_actions_per_method=41250,architecture_changed=False,continued_history_amendment=True,optimizer_settings_changed=False,reward_physics_changed=False,automatic_followup=False,convergence_claim=False,direct34=False,evidence=[ref(p) for p in required],reason='Complete88 all90 full55s/noabort and exact replay/reward review passed. Q loss first-to-last1000 falls for all3; Task/Strict I18/17,A16/16,V17/17 and returns improve versus87. Preserve Ashort0900 carry regression and Icritic3/Acritics2,3 fixed87 mask-in fitting regressions. Learned history needs a second finite same-revision learning cycle, not an immediate further architecture/entropy change supported only by one cycle. Continue exact full88 learner/replay/Adam/RNG in one41250-action cycle per method, preserving all settings and original history marker. This is a separately reviewed finite budget decision, not automatic89/90 or a convergence conclusion. Original88-90 prospective stability protocol remains unchanged; frozen88 continues independently.'))
R.mkdir();jobs=[]
for oldjob in read(P/'LAUNCH.json')['jobs']:
 m=oldjob['controller'];dest=R/m;dest.mkdir();(dest/'check').mkdir();parent=P/m/'REGISTRATION.json';p=read(parent);old=p['post_interruption_continuation'];trainer=Path(old['trainer_path']);cp=A/m/'cycle_00088.pt'
 assert sha(cp)==read(V/'REVIEW.json')['methods'][m]['checkpoint_sha256']
 st=dict(old,parent_cycle=88,new_cycle=89,parent_registration=ref(parent),checkpoint=ref(cp),cycle_review=ref(V/'REVIEW.json'),health_review=ref(V/'health/DIAGNOSIS.json'),previous_driver=ref(Path(oldjob['command'][1])),driver_sha256=sha(D/'driver.py'),trainer_path=str(trainer),trainer_sha256=sha(trainer),patched_trainer_sha256=hashlib.sha256(transform(trainer.read_text()).encode()).hexdigest(),loss_review=ref(V/'loss/REVIEW.json'),fixed_terminal_review=ref(T/'REVIEW.json'),training_pair_review=ref(C/'INTERPRETATION.json'),scientific_decision=ref(D/'SCIENTIFIC_DECISION.json'),physical_semantics='One explicitly reviewed finite89 budget from exact complete88. Restore learned51-state directly, preserve original history amendment, full replay/Adam/RNG and all historical failures. No automatic90 or old-revision stability pooling.')
 p['post_interruption_continuation']=st;validate_protocol(st['parent_registration']['sha256'],p);put(dest/'REGISTRATION.json',p)
 cmd=list(oldjob['command']);cmd[1]=str(D/'driver.py')
 for flag,val in [('--registration',dest/'REGISTRATION.json'),('--resume',cp),('--output',dest/'train')]:cmd[cmd.index(flag)+1]=str(val)
 jobs.append(dict(controller=m,command=cmd))
put(R/'COMMANDS.json',dict(jobs=jobs,automatic_training=False))
for p in D.glob('*.py'):ast.parse(p.read_text())
put(D/'SOURCES.json',dict(time=time.time(),files={p.name:sha(p) for p in D.glob('*.py')}))
put(D/'PREFLIGHT_PLAN.json',dict(time=time.time(),sources=ref(D/'SOURCES.json'),parent_cycle=88,new_cycle=89,disposable_native_updates=6,batch=65536,formal_updates=0,physical_steps=0,budget_seconds=1800,requires_full_state_and_replay_exact=True,requires_protocol_and_actual_parent_negative_guards=True,automatic_training=False))
print('Finite89 registered after complete88 evidence; no new physics yet')
