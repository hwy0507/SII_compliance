"""Prepare and register a single same-protocol cycle93 from fully reviewed92."""
from pathlib import Path
import ast,difflib,hashlib,json,re,sys,time
D=Path(__file__).resolve().parent;B=D.parents[1];P=B/'runtime/violation93_continuation_20261031_v1';Q=B/'runtime/violation93_review_20261031_v1';R=B/'runs/parameter_violation_cycle93_20261031_v1'
OLD=B/'runs/parameter_violation_cycle92_20261030_v1';V=B/'runs/parameter_violation_cycle92_review_20261030_v1';C=B/'runtime/violation92_completion_20261031_v1';F=B/'runs/violation92_fixed87_terminal_followup_20261030_v1';S=B/'runs/parameter_violation90_92_reward_stability_20261030_v1';T=B/'runs/violation92_terminal_census_20261031_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
assert not P.exists() and not Q.exists() and not R.exists()
required=[V/n for n in ['REVIEW.json','FINISHED.json','health/DIAGNOSIS.json','loss/REVIEW.json','PLOT_INSPECTION.json']]+[C/n for n in ['INTERPRETATION.json','INTERPRETATION_SAVED_REVIEW.json','PLOT_INSPECTION.json','CHANGED_CASES_REVIEW.json','TERMINAL_SAVED_REVIEW.json','ABORT_REVIEW.json']]+[F/n for n in ['REVIEW.json','FINISHED.json','PLOT_INSPECTION.json']]+[S/n for n in ['PLAN.json','REVIEW.json','SAVED_ARITHMETIC_REVIEW.json','PLOT_INSPECTION.json','EARLY_WINDOW_FAILURE_91.json']]+[T/n for n in ['PLAN.json','FINISHED.json','SAVED_REVIEW.json','PLOT_INSPECTION.json']]+[B/'runs/violation92_frozen_batch_diagnosis_20261031_v1'/n for n in ['SAVED_REVIEW.json','SPIKE_SOURCE_REVIEW.json','PLOT_INSPECTION.json']]
for p in required:
 x=read(p)
 if 'passed' in x:assert x['passed'],p
 if 'actual_visual_inspection' in x:
  assert x['actual_visual_inspection']
  for item in x['plots']:assert item['inspected'] and sha(item['path'])==item['sha256']
assert read(V/'FINISHED.json')['completed']
for j in read(OLD/'LAUNCH.json')['jobs']:
 assert read(OLD/j['controller']/'train/FINISHED.json')['status']=='stopped_at_complete_cycle'
 p=Path('/proc',str(j['pid']),'stat')
 if p.exists():
  f=p.read_text().rsplit(')',1)[1].split();assert f[0]=='Z' or f[19]!=j['proc_start_ticks']
P.mkdir();Q.mkdir();R.mkdir()
def shift(s):
 protected=['parameter_violation90_92_reward_stability_20261030_v1','[90,91,92]']
 for i,x in enumerate(protected):s=s.replace(x,f'KEEPWINDOW_{i}_END')
 mapping={'91':'92','92':'93','93':'94','00091':'00092','00092':'00093','00093':'00094'}
 s=re.sub(r'(?<!\d)(00091|00092|00093|91|92|93)(?!\d)',lambda m:mapping[m[0]],s)
 s=re.sub(r'(violation93[^\x27\x22\s/]*?)_20261030',r'\1_20261031',s)
 s=re.sub(r'(cycle93[^\x27\x22\s/]*?)_20261030',r'\1_20261031',s)
 for i,x in enumerate(protected):s=s.replace(f'KEEPWINDOW_{i}_END',x)
 return s
oldp=B/'runtime/violation92_continuation_20261030_v1';oldq=B/'runtime/violation92_review_20261030_v1';changed=[];unchanged=[]
for p in oldp.glob('*.py'):
 if p.name=='register92.py':continue
 data=p.read_text();new=shift(data) if p.name in ['driver.py','check_contract.py','run_preflight.py'] else data
 q=P/p.name;q.write_text(new);ast.parse(new)
 if new==data:unchanged.append(dict(parent=str(p),current=str(q),sha256=sha(q)))
 else:
  (P/(p.name+'.diff')).write_text(''.join(difflib.unified_diff(data.splitlines(True),new.splitlines(True),fromfile=str(p),tofile=str(q))));changed.append(dict(parent=ref(p),current=ref(q)))
for p in oldq.glob('*.py'):
 if p.name=='save92.py':continue
 data=p.read_text();new=shift(data) if p.name in ['launch92.py','archive92.py','review92.py','loss92.py','startup92.py','observe92.py'] else data
 q=Q/p.name.replace('92','93');q.write_text(new);ast.parse(new)
 if new==data:unchanged.append(dict(parent=str(p),current=str(q),sha256=sha(q)))
 else:
  (Q/(q.name+'.diff')).write_text(''.join(difflib.unified_diff(data.splitlines(True),new.splitlines(True),fromfile=str(p),tofile=str(q))));changed.append(dict(parent=ref(p),current=ref(q)))
put(D/'ADAPTATION_REVIEW.json',dict(time=time.time(),passed=True,changed=changed,numerical_dependencies_unchanged=unchanged,retained_original90_92_window=True,new_physics=0,formal_updates=0))
put(P/'SCIENTIFIC_DECISION.json',dict(time=time.time(),parent_cycle=92,new_cycle=93,new_cycles=1,maximum_new_actions_per_method=41250,critic_revision='raw_violation52',automatic_followup=False,offline_weights_promoted=False,optimizer_settings_changed=False,reward_physics_changed=False,direct34=False,architecture_final_acceptance=False,convergence_claim=False,original90_92_IA_failed=True,evidence=[ref(p) for p in required],reason='Complete92 and all8263 terminal census reviewed. I cycle90/92 safety-abort terminals contribute76.3184% of terminal masked SSE; older79 contributes0.2162%, but current cross-row differences do not prove learning trajectory or irreducibility. Frozen native batches reproduce two I spikes from90 with no updates; A/V historical spikes remain unresolved. Full92 retained all replay/learned52/Adam/RNG exactly; original90-92 I/A reward failure and V reward-only pass retained. Register one unchanged online93 to test whether continued native learning improves these specific seen rare failures while monitoring all fixed92 terminals, full losses/actor drift and actual30 conditions per method. No rows excluded, no special sampling, no offline weights, no new information/LR/reward changes. This is one bounded continuation, not an automatic sequence or occupancy job; review full93 before any94. If rare terminal errors persist/worsen, reassess learning interference/representation rather than blindly continue. Frozen90 continues independently.'))
sys.path[:0]=[str(P),str(B/'runtime/source_train17_clock/source/tools')]
from driver import transform,validate_protocol
jobs=[]
for job in read(OLD/'COMMANDS.json')['jobs']:
 m=job['controller'];dest=R/m;dest.mkdir();(dest/'check').mkdir();p=read(OLD/m/'REGISTRATION.json');st=p['post_interruption_continuation'];cp=B/'runs/parameter_violation_cycle92_archive_20261030_v1'/m/'cycle_00092.pt';trainer=OLD/m/'trainer_registered.py'
 assert sha(cp)==read(V/'REVIEW.json')['methods'][m]['checkpoint_sha256'];assert transform(trainer.read_text())==trainer.read_text()
 p['post_interruption_continuation']=dict(st,parent_cycle=92,new_cycle=93,parent_registration=ref(OLD/m/'REGISTRATION.json'),checkpoint=ref(cp),cycle_review=ref(V/'REVIEW.json'),health_review=ref(V/'health/DIAGNOSIS.json'),previous_driver=ref(oldp/'driver.py'),driver_sha256=sha(P/'driver.py'),trainer_path=str(trainer),trainer_sha256=sha(trainer),patched_trainer_sha256=sha(trainer),loss_review=ref(V/'loss/REVIEW.json'),fixed_terminal_review=ref(F/'REVIEW.json'),training_pair_review=ref(C/'INTERPRETATION.json'),abort_review=ref(C/'ABORT_REVIEW.json'),scientific_decision=ref(P/'SCIENTIFIC_DECISION.json'),stability_plan=ref(S/'PLAN.json'),fixed92_terminal_census=ref(T/'SAVED_REVIEW.json'),physical_semantics='One finite unchanged52 continuation from complete92; preserve all old failures including79/90/92, learned weights/Adam/RNG, full replay, original failed windows and physics. Fixed92 all-terminal census is a diagnostic reference; no automatic94.')
 validate_protocol(p['post_interruption_continuation']['parent_registration']['sha256'],p);put(dest/'REGISTRATION.json',p)
 cmd=list(job['command']);cmd[1]=str(P/'driver.py')
 for flag,value in [('--registration',dest/'REGISTRATION.json'),('--resume',cp),('--output',dest/'train')]:cmd[cmd.index(flag)+1]=str(value)
 jobs.append(dict(controller=m,command=cmd))
put(R/'COMMANDS.json',dict(jobs=jobs,automatic_training=False))
for folder in [P,Q]:put(folder/'SOURCES.json',dict(time=time.time(),files={p.name:sha(p) for p in folder.glob('*.py')}))
put(P/'PREFLIGHT_PLAN.json',dict(time=time.time(),sources=ref(P/'SOURCES.json'),parent_cycle=92,new_cycle=93,disposable_native_updates=6,batch=65536,formal_updates=0,physical_steps=0,budget_seconds=1800,automatic_training=False))
oldobs=read(oldq/'OBSERVATION_PLAN.json');oldobs.update(time=time.time(),source_sha256=sha(Q/'observe93.py'));put(Q/'OBSERVATION_PLAN.json',oldobs)
put(P/'REMOTE_START.json',read(D/'REMOTE_START.json'))
print('Finite93 registered; no physical training launched. Exact92 trainer retained.')
