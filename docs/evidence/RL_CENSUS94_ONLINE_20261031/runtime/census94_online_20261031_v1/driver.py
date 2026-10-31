"""One finite conditional-terminal census online94, exact formal93 parent only."""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,os,sys,time,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle94_20261031_v1'
sys.path[:0]=[str(D),str(B/'runtime/source_train17_clock/source/tools'),str(B/'runtime/violation93_terminal_followup_20261031_v1')]
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def transform(source):
 changes=[("checkpoint = torch.load(args.resume, map_location=args.device, weights_only=False)","checkpoint = torch.load(args.resume, map_location='cpu', weights_only=False)"),
 ("learner.load_state_dict(checkpoint['learner'])","learner.migrate_parent(checkpoint['learner'])"),
 ('        replay = DeviceReplayCache(replay, learner.device)','        replay = DeviceReplayCache(replay, learner.device)\n        learner.bind_cache(replay)'),
 ("\n        violation_critic_amendment=protocol['violation_critic_amendment'],","\n        violation_critic_amendment=protocol['violation_critic_amendment'],\n        conditional_terminal_amendment=protocol['conditional_terminal_amendment'],"),
 ("\n            violation_critic_amendment=protocol['violation_critic_amendment'],","\n            violation_critic_amendment=protocol['violation_critic_amendment'],\n            conditional_terminal_amendment=protocol['conditional_terminal_amendment'],"),
 ("plateau_status([c for c in cycles if c['cycle'] >= 90])","plateau_status([c for c in cycles if c['cycle'] >= 94])"),
 ("                        replay.add(observations=previous['observation'], actions=previous['raw_action'],","                        if steps >= protocol['post_interruption_continuation']['parent_steps'] + 41250:\n                            raise ValueError('Finite94 new-transition budget exceeded')\n                        replay.add(observations=previous['observation'], actions=previous['raw_action'],")]
 for a,b in changes:
  if source.count(a)!=1:raise ValueError('Frozen93 trainer seam changed: '+a)
  source=source.replace(a,b)
 return source

def expected_protocol(m):
 from census_native import marker
 decision=read(D/'SCIENTIFIC_DECISION.json');e=decision['methods'][m];parent=read(e['parent_registration']['path'])
 if sha(e['parent_registration']['path'])!=e['parent_registration']['sha256']:raise ValueError('Formal93 registration drift')
 stage=dict(version=1,parent_cycle=93,new_cycle=94,new_cycles=1,controller=m,parent_registration=e['parent_registration'],checkpoint=e['checkpoint'],parent_steps=e['steps'],parent_updates=e['updates'],parent_history_digest=e['history_digest'],cycle_review=decision['cycle_review'],driver_sha256=sha(__file__),trainer_path=e['trainer']['path'],trainer_sha256=e['trainer']['sha256'],patched_trainer_sha256=hashlib.sha256(transform(Path(e['trainer']['path']).read_text()).encode()).hexdigest(),maximum_new_actions=41250,environment_state_saved=False,old_window_continuity_claim=False,automatic_followup=False,optimizer_settings_changed=False,scientific_decision=ref(D/'SCIENTIFIC_DECISION.json'))
 amendment=dict(version=1,first_cycle=94,kind='conditional_terminal_census',marker=marker(),source=ref(D/'census_native.py'),native_compatibility_review=decision['native_review'],frozen_census_review=decision['ablation_review'],health_metric='agent_train/original_sampled_q_loss',update_metric='agent_train/conditional_terminal_q_loss',same_expected_terminal_loss_and_gradient=True,equal_finite_Adam_trajectory_claim=False)
 return dict(parent,post_interruption_continuation=stage,conditional_terminal_amendment=amendment)

def validate_protocol(parent_digest,p,current_digest=None):
 m=p['post_interruption_continuation']['controller'];expected=expected_protocol(m)
 if p!=expected or parent_digest!=expected['post_interruption_continuation']['parent_registration']['sha256']:raise ValueError('Exact finite94 scientific contract required')
 d=read(D/'SCIENTIFIC_DECISION.json')
 if (d['parent_cycle'],d['new_cycle'],d['new_cycles'],d['maximum_new_actions_per_method'],d['automatic_followup'],d['offline_weights_promoted'],d['optimizer_settings_changed'],d['reward_physics_changed'])!=(93,94,1,41250,False,False,False,False):raise ValueError('Finite scientific decision changed')
 for item in d['evidence']:
  if sha(item['path'])!=item['sha256']:raise ValueError('Scientific decision evidence changed')
 for item in [d['cycle_review'],d['native_review'],d['ablation_review']]:
  if not read(item['path'])['passed']:raise ValueError('Required scientific review failed')
 return read(expected['post_interruption_continuation']['parent_registration']['path'])

def validate_parent(ck,p):
 from compare93 import validate_complete93
 from census_native import KEY
 from validate_published_finite_check_20261025 import digest
 st=p['post_interruption_continuation'];old=read(st['parent_registration']['path']);validate_complete93(ck,old)
 if KEY in ck['learner'] or 'conditional_terminal_amendment' in ck:raise ValueError('Only unchanged formal93 may migrate')
 if ck['steps']!=st['parent_steps'] or ck['learner']['num_gradient_steps']!=st['parent_updates'] or digest(ck['cycles'])!=st['parent_history_digest']:raise ValueError('Formal93 counters/history changed')
 if ck['protocol_sha256']!=st['parent_registration']['sha256'] or ck['steps']+41250>4000000:raise ValueError('Parent identity/capacity mismatch')

def validate_checkpoint(ck,p,complete=False):
 from persisted_history_critic import KEY as HK,marker as hm
 from persisted_violation_critic import KEY as VK,marker as vm
 from parameter_replay_capacity_20261026 import MARKER as CAP2
 from parameter_replay_capacity4m_20261027 import MARKER as CAP4
 from census_native import KEY,marker
 from validate_published_finite_check_20261025 import digest
 st=p['post_interruption_continuation'];h=p['history_critic_amendment'];v=p['violation_critic_amendment'];m=st['controller'];n=ck['steps']
 if ck['controller']!=m or ck['seed']!=20261025 or ck['cycle']!=94 or ck['environment_state_saved'] is not False:raise ValueError('Wrong94 checkpoint identity')
 if ck['protocol_sha256']!=sha(R/m/'REGISTRATION.json') or ck['conditional_terminal_amendment']!=p['conditional_terminal_amendment']:raise ValueError('Estimator registration missing or changed')
 if ck['recovery_continuation']!=st or ck['interruption_recovery']!=p['interrupted_episode_recovery'] or ck['history_critic_amendment']!=h or ck['violation_critic_amendment']!=v:raise ValueError('Historical metadata changed')
 if not st['parent_steps']<n<=st['parent_steps']+41250 or ck['learner']['num_gradient_steps']!=st['parent_updates']+n-st['parent_steps']:raise ValueError('Transition/update budget mismatch')
 if ck['learner'].get(KEY)!=marker():raise ValueError('Persisted census rule missing')
 for k in ['learner','replay']:
  if ck[k].get(HK)!=hm(h['binding']) or ck[k].get(VK)!=vm(v['binding']):raise ValueError('History/rawbit marker changed')
 r=ck['replay']
 if r['capacity']!=4000000 or r['size']!=n or r['cursor']!=n or r['replay_capacity_extension']!=CAP2 or r['replay_capacity_followup']!=CAP4:raise ValueError('Append-only replay changed')
 if any(r['arrays'][k].shape!=(n,52) for k in ['observations','next_observations']):raise ValueError('Full52 replay required')
 full=ck['boundary']=='complete_condition_cycle';history=ck['cycles'][:-1] if full else ck['cycles']
 if digest(history)!=st['parent_history_digest'] or any(c['cycle']==75 for c in ck['cycles']):raise ValueError('Historical cycle records changed')
 if full and ck['cycles'][-1]['cycle']!=94:raise ValueError('Wrong final cycle record')
 if complete and not full:raise ValueError('Complete94 required')

def classes(p):
 from violation_pipeline import classes as old_classes
 from census_native import census_class
 base,replay=old_classes(p);return census_class(base),replay

def restore_consumer(state,p,device):
 from census_native import strict_restore
 from validate_published_finite_check_20261025 import digest
 cls,_=classes(p);l=cls(Path(p['runtime']),dimension=p['violation_critic_amendment']['binding']['action_dimension'],direct=False,seed=20261025,device=device,algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True);strict_restore(l,state,digest);return l

def verify_initial(learner,replay,ck,out):
 from census_native import KEY,marker
 from validate_published_finite_check_20261025 import digest
 state=learner.state_dict();plain=dict(state);assert plain.pop(KEY)==marker();assert digest(plain)==digest(ck['learner']) and digest(replay.state_dict())==digest(ck['replay'])
 put(out/'INITIAL_STATE_REVIEW.json',dict(passed=True,time=time.time(),full_trained93_learner_and_replay_exact_except_added_estimator_marker=True,learner_digest=digest(state),parent_learner_digest=digest(ck['learner']),replay_digest=digest(ck['replay']),new_physics=0,optimizer_updates=0))

def main(args):
 import torch
 from census_native import CensusCache,KEY,marker
 from validate_published_finite_check_20261025 import digest
 from parameter_shared_sampler_pool_20261026 import validate_pool,sampler_affinity
 torch.set_num_threads(1);p=read(args.registration);st=p['post_interruption_continuation'];root=Path(p['runtime'])
 for n,h in read(D/'SOURCES.json')['files'].items():
  if sha(D/n)!=h:raise ValueError('Registered source changed: '+n)
 if args.runtime.resolve()!=root or sha(root/'RUNTIME.json')!=p['runtime_sha256']:raise ValueError('Frozen runtime mismatch')
 for n,h in read(root/'SOURCE_HASHES.json').items():
  if sha(root/'source'/n)!=h:raise ValueError('Frozen physics/source changed')
 if args.resume.resolve()!=Path(st['checkpoint']['path']) or sha(args.resume)!=st['checkpoint']['sha256']:raise ValueError('Formal93 archive required')
 validate_protocol(st['parent_registration']['sha256'],p);cpus=list(map(int,args.cpus.split(',')));validate_pool(p,args,cpus)
 ck=torch.load(args.resume,map_location='cpu',weights_only=False);validate_parent(ck,p);cls,replay_cls=classes(p);source=Path(st['trainer_path']).read_text()
 if sha(st['trainer_path'])!=st['trainer_sha256']:raise ValueError('Parent trainer changed')
 modified=transform(source);assert hashlib.sha256(modified.encode()).hexdigest()==st['patched_trainer_sha256']
 if args.check_only:
  os.sched_setaffinity(0,{cpus[0]});l=cls(root,dimension=p['violation_critic_amendment']['binding']['action_dimension'],direct=False,seed=20261025,device=args.device,algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True);l.migrate_parent(ck['learner']);r=replay_cls(l.dimension if hasattr(l,'dimension') else p['violation_critic_amendment']['binding']['action_dimension'],52,20261078);r.load_state_dict(ck['replay']);out=args.output.parent/'check';out.mkdir();verify_initial(l,r,ck,out)
  initial=l.state_dict();rr=copy.deepcopy(r.rng.bit_generator.state);cache=CensusCache(r,args.device);l.bind_cache(cache);batch=cache.sample(65536);a=l.update(batch);after=digest(l.state_dict());l.load_state_dict(initial);l.bind_cache(cache);b=l.update(batch);assert a==b and digest(l.state_dict())==after;l.load_state_dict(initial);r.rng.bit_generator.state=rr;assert digest(l.state_dict())==digest(initial) and digest(r.state_dict())==digest(ck['replay'])
  consumer=restore_consumer(initial,p,args.device);assert digest(consumer.state_dict())==digest(initial);assert sha(args.resume)==st['checkpoint']['sha256']
  put(args.output.parent/'CHECK_ONLY_REVIEW.json',dict(passed=True,time=time.time(),checkpoint_sha256=st['checkpoint']['sha256'],registration_sha256=sha(args.registration),actual_native_batch=65536,disposable_restored_clone_updates=2,repeat_native_update_full_state_exact=True,original_state_restored=True,consumer_full_state_exact=True,estimator_marker=marker(),metrics=a,new_physics=0,actual_formal_updates=0));return
 gate=read(R/'PRELAUNCH_REVIEW.json');assert gate['passed'] and gate['registration_hashes'][args.controller]==sha(args.registration);assert read(args.output.parent/'CHECK_ONLY_REVIEW.json')['passed']
 if time.time()>read(D/'SCIENTIFIC_DECISION.json')['launch_deadline_unix']:raise ValueError('Finite launch window expired')
 trainer=root/'source/tools/train_published_compliance_20261025.py';spec=importlib.util.spec_from_file_location('census94_trainer',trainer);module=importlib.util.module_from_spec(spec);exec(compile(modified,str(trainer),'exec'),module.__dict__)
 def stage_check(checkpoint,stage,cycle_budget,rates):
  validate_parent(checkpoint,p);assert stage==p['completed_stage_continuation'] and cycle_budget==1;_,expected=module.registered_stage_actor_rates(stage);assert len(rates)==len(expected) and all(abs(a-b)<1e-12 for a,b in zip(rates,expected))
 import published_replay_device_cache_20261025 as cm
 cm.DeviceReplayCache=CensusCache
 module.Replay=replay_cls;module.PublishedLearner=cls;module.validate_resume_protocol=validate_protocol;module.validate_completed_stage_checkpoint=stage_check;module._parameter_sampler_affinity=sampler_affinity;module._validate_parameter_sampler_pool=validate_pool;module._verify_initial_state=verify_initial
 args.algorithm='cheq';args.seed=20261025;args.cycles=1;(args.output.parent/'trainer_registered.py').write_text(modified)
 put(args.output.parent/'CENSUS_EXECUTION.json',dict(time=time.time(),pid=os.getpid(),registration_sha256=sha(args.registration),driver_sha256=sha(__file__),trainer_sha256=st['patched_trainer_sha256'],cycle=94,automatic_followup=False,maximum_new_actions=41250))
 del ck;module.main(args)
if __name__=='__main__':
 parser=argparse.ArgumentParser()
 for n in ['runtime','registration','resume','output']:parser.add_argument('--'+n,type=Path,required=True)
 parser.add_argument('--controller',required=True,choices=['impedance','admittance','vmc']);parser.add_argument('--device',required=True);parser.add_argument('--cpus',required=True);parser.add_argument('--workers',type=int,default=30);parser.add_argument('--check-only',action='store_true');args=parser.parse_args()
 try:main(args)
 except BaseException:
  put(args.output.parent/('CHECK_ONLY_FAILURE.json' if args.check_only else 'DRIVER_FAILURE.json'),dict(time=time.time(),traceback=traceback.format_exc()));raise
