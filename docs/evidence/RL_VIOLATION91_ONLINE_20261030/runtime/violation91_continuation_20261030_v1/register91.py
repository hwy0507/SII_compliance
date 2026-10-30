"""Register one learned52 continuation from full90; retain all failure evidence."""
from pathlib import Path
import sys,json,time,hashlib,ast,subprocess
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_violation_cycle91_20261030_v1';OLD=B/'runs/parameter_violation_cycle90_20261030_v1';V=B/'runs/parameter_violation_cycle90_review_20261030_v1';C=B/'runtime/violation90_completion_20261030_v1';F=B/'runs/violation90_fixed87_terminal_followup_20261030_v1';S=B/'runs/parameter_violation90_92_reward_stability_20261030_v1'
sys.path[:0]=[str(D),str(B/'runtime/source_train17_clock/source/tools')]
from driver import read,sha,put,transform,validate_protocol
ref=lambda p:dict(path=str(p),sha256=sha(p))
assert not R.exists()
required=[V/n for n in ('REVIEW.json','FINISHED.json','health/DIAGNOSIS.json','loss/REVIEW.json','PLOT_INSPECTION.json')]+[C/n for n in ('INTERPRETATION.json','INTERPRETATION_SAVED_REVIEW.json','PLOT_INSPECTION.json','ABORT_REVIEW.json')]+[F/n for n in ('REVIEW.json','FINISHED.json','PLOT_INSPECTION.json')]+[S/'PLAN.json',B/'runtime/history89_completion_20261030_v1/EARLY_WINDOW_FAILURE.json',B/'runs/parameter_history88_90_reward_stability_20261030_v1/REVISION_BOUNDARY_90.json']
for p in required:
 x=read(p)
 if 'passed' in x:assert x['passed'],p
 if 'actual_visual_inspection' in x:assert x['actual_visual_inspection'],p
for folder in (V,C,F):
 for item in read(folder/'PLOT_INSPECTION.json')['plots']:assert item['inspected'] and sha(item['path'])==item['sha256']
assert read(V/'FINISHED.json')['completed']
for job in read(OLD/'LAUNCH.json')['jobs']:
 assert read(OLD/job['controller']/'train/FINISHED.json')['status']=='stopped_at_complete_cycle'
 p=Path('/proc',str(job['pid']),'stat')
 if p.exists():f=p.read_text().rsplit(')',1)[1].split();assert f[0]=='Z' or f[19]!=job['proc_start_ticks']
put(D/'SCIENTIFIC_DECISION.json',dict(time=time.time(),parent_cycle=90,new_cycle=91,new_cycles=1,maximum_new_actions_per_method=41250,critic_revision='raw_violation52',automatic_followup=False,offline_weights_promoted=False,optimizer_settings_changed=False,reward_physics_changed=False,direct34=False,architecture_final_acceptance=False,convergence_claim=False,evidence=[ref(p) for p in required],reason='Complete90 implementation/replay/reward and native frozen restore audits passed. First online52 cycle has lower critic tail means but I late spikes and actor drift. Fixed original87 terminal masked SSE improves I83.45% yet worsens A9.70%/V146.79%; all-row SSE decreases. Online labels improve A/V but I loses long0000 through a global object/corner penetration abort, whose external bit is0; preserve failure and original gates. This mixed evidence neither establishes convergence nor justifies promoting offline weights or changing physics/actor information. Register exactly one further same52 online cycle from all learned90 weights/Adam/replay/RNG, retaining the abort transition and unchanged objective/learning rates/UTD, to obtain the next comparable complete-cycle result and assess persistence of gains/regressions. Full91 must be reviewed before any92 decision. The90-92 statistics plan does not itself dispatch training. Frozen90 runs independently as prospectively fixed-policy evaluation.'))
R.mkdir();jobs=[]
for job in read(OLD/'COMMANDS.json')['jobs']:
 m=job['controller'];dest=R/m;dest.mkdir();(dest/'check').mkdir();p=read(OLD/m/'REGISTRATION.json');st=p['post_interruption_continuation'];cp=B/'runs/parameter_violation_cycle90_archive_20261030_v1'/m/'cycle_00090.pt';trainer=OLD/m/'trainer_registered.py';assert sha(cp)==read(V/'REVIEW.json')['methods'][m]['checkpoint_sha256']
 assert transform(trainer.read_text())==trainer.read_text()
 p['post_interruption_continuation']=dict(st,parent_cycle=90,new_cycle=91,parent_registration=ref(OLD/m/'REGISTRATION.json'),checkpoint=ref(cp),cycle_review=ref(V/'REVIEW.json'),health_review=ref(V/'health/DIAGNOSIS.json'),previous_driver=ref(B/'runtime/violation90_online_20261030_v1/driver.py'),driver_sha256=sha(D/'driver.py'),trainer_path=str(trainer),trainer_sha256=sha(trainer),patched_trainer_sha256=sha(trainer),loss_review=ref(V/'loss/REVIEW.json'),fixed_terminal_review=ref(F/'REVIEW.json'),training_pair_review=ref(C/'INTERPRETATION.json'),abort_review=ref(C/'ABORT_REVIEW.json'),scientific_decision=ref(D/'SCIENTIFIC_DECISION.json'),stability_plan=ref(S/'PLAN.json'),physical_semantics='One finite same52 continuation from exact complete90 including I safety abort. Preserve learned history and violation weights/Adam, all replay and RNG, original physics and failed windows; no automatic92.')
 validate_protocol(p['post_interruption_continuation']['parent_registration']['sha256'],p);put(dest/'REGISTRATION.json',p)
 cmd=list(job['command']);cmd[1]=str(D/'driver.py')
 for flag,value in [('--registration',dest/'REGISTRATION.json'),('--resume',cp),('--output',dest/'train')]:cmd[cmd.index(flag)+1]=str(value)
 jobs.append(dict(controller=m,command=cmd))
put(R/'COMMANDS.json',dict(jobs=jobs,automatic_training=False))
for p in D.glob('*.py'):ast.parse(p.read_text())
put(D/'SOURCES.json',dict(time=time.time(),files={p.name:sha(p) for p in D.glob('*.py')}))
put(D/'PREFLIGHT_PLAN.json',dict(time=time.time(),sources=ref(D/'SOURCES.json'),parent_cycle=90,new_cycle=91,disposable_native_updates=6,batch=65536,formal_updates=0,physical_steps=0,budget_seconds=1800,automatic_training=False))
repo=B/'repository/SII_compliance';put(D/'REMOTE_START.json',dict(time=time.time(),actual_query_fetch_read=True,**{n:subprocess.check_output(['git','rev-parse','origin/'+n],cwd=repo,text=True).strip() for n in ('main','baseline')}))
print('Finite91 registered; no physics launched')
