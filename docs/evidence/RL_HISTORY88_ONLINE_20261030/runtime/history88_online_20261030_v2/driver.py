"""One registered history-critic cycle from exact complete87; no followup."""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,os,sys,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;I=B/'runtime/history87_critic_interface_20261030_v1';RUN=B/'runs/parameter_history_cycle88_20261030_v2'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def transform(source):
 from persisted_history_critic import transform_trainer
 source=transform_trainer(source)
 edits={"        learner.load_state_dict(checkpoint['learner'])":"        learner.migrate_parent(checkpoint['learner'])", "        replay.load_state_dict(checkpoint['replay'])":"        replay.migrate_parent(checkpoint['replay'], protocol['history_critic_amendment']['sidecar']['path'])", "            environment_state_saved=False,":"            history_critic_amendment=protocol['history_critic_amendment'],\n            environment_state_saved=False,", "        replay_device_cache=bool(cache_enabled),":"        history_critic_amendment=protocol['history_critic_amendment'],\n        registered_trainer_sha256=protocol['post_interruption_continuation']['patched_trainer_sha256'],\n        replay_device_cache=bool(cache_enabled),", "plateau=plateau_status(cycles)":"plateau=plateau_status([c for c in cycles if c['cycle'] >= 88])"}
 for old,new in edits.items():
  if source.count(old)!=1:raise ValueError('History trainer seam changed: '+old)
  source=source.replace(old,new)
 return source

def validate_protocol(parent_digest,p,current_digest=None):
 st=p['post_interruption_continuation'];h=p['history_critic_amendment'];previous=read(st['parent_registration']['path'])
 if sha(st['parent_registration']['path'])!=parent_digest or st['parent_registration']['sha256']!=parent_digest:raise ValueError('Exact complete87 registration required')
 if {k:v for k,v in p.items() if k not in ('post_interruption_continuation','history_critic_amendment')}!={k:v for k,v in previous.items() if k!='post_interruption_continuation'}:raise ValueError('Unregistered scientific or historical contract change')
 if (st['parent_cycle'],st['new_cycle'],st['new_cycles'],st['maximum_new_actions'],st['automatic_followup'],st['optimizer_settings_changed'],st['old_window_continuity_claim'],st['environment_state_saved'])!=(87,88,1,41250,False,False,False,False):raise ValueError('Finite history88 continuation contract changed')
 if h!=read(D/'AMENDMENT.json')['methods'][st['controller']]:raise ValueError('History architecture binding changed')
 if sha(__file__)!=st['driver_sha256']:raise ValueError('Driver drift')
 for key in ('cycle_review','health_review','previous_driver'):
  if sha(st[key]['path'])!=st[key]['sha256']:raise ValueError('Parent review/driver drift')
 old=previous['post_interruption_continuation']
 spec=importlib.util.spec_from_file_location('validated_formal87_driver',st['previous_driver']['path']);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 module.validate_protocol(old['parent_registration']['sha256'],previous,st['parent_registration']['sha256'])
 review=read(st['cycle_review']['path']);health=read(st['health_review']['path']);m=st['controller']
 if not review['passed'] or review['methods'][m]['checkpoint_sha256']!=st['checkpoint']['sha256'] or health['methods'][m]['checkpoint_sha256']!=st['checkpoint']['sha256']:raise ValueError('Complete87 reviews do not bind checkpoint')
 if st['checkpoint']['sha256']!=h['binding']['checkpoint_sha256']:raise ValueError('Migration parent mismatch')
 return previous

def validate_parent(ck,p):
 st=p['post_interruption_continuation'];previous=read(st['parent_registration']['path']);binding=p['history_critic_amendment']['binding']
 if ck['cycle']!=87 or ck['boundary']!='complete_condition_cycle' or ck['environment_state_saved'] or ck['seed']!=20261025 or ck['steps']!=binding['rows'] or ck['controller']!=binding['method'] or ck['recovery_continuation']!=previous['post_interruption_continuation'] or ck['interruption_recovery']!=previous['interrupted_episode_recovery'] or ck['cycles'][-1]['cycle']!=87 or any(c['cycle']==75 for c in ck['cycles']):raise ValueError('Exact complete87 boundary required')

def verify_initial(learner,replay,ck,out):
 import numpy as np,torch
 from validate_published_finite_check_20261025 import digest
 from persisted_history_critic import KEY,feature
 m=ck['controller'];binding=read(I/(m+'_BINDING.json'));ls=learner.state_dict();expected=torch.load(I/(m+'_migrated_learner.pt'),map_location='cpu',weights_only=False);assert digest(ls)==digest(expected)
 rs=replay.state_dict();plain={k:v for k,v in rs.items() if k!=KEY};plain['arrays']={k:(v[:,:50] if k in ('observations','next_observations') else v) for k,v in rs['arrays'].items()};assert digest(plain)==binding['replay_digest']==digest(ck['replay']);peaks=np.load(read(D/'AMENDMENT.json')['methods'][m]['sidecar']['path'],mmap_mode='r')
 for c,k in enumerate(('observations','next_observations')):assert np.array_equal(rs['arrays'][k][:,50],feature(peaks[:,c]))
 put(out/'INITIAL_STATE_REVIEW.json',dict(passed=True,time=time.time(),learner_digest=digest(ls),replay_digest=digest(rs),original_replay_digest=binding['replay_digest'],old87_state_exact_except_registered_zero_column_migration=True,all_history_rows_verified=True,history_digest=digest(ck['cycles']),new_physics=0,optimizer_updates=0))

def validate_actor_rates(actual, expected):
 import math
 if len(actual)!=len(expected) or any(not math.isfinite(a) or abs(a-e)>=1e-12 for a,e in zip(actual,expected)):
  raise ValueError('Actual actor learning rates differ from registered values')

def main(args):
 import torch,numpy as np
 torch.set_num_threads(1);p=read(args.registration);st=p['post_interruption_continuation'];h=p['history_critic_amendment'];root=Path(p['runtime']);assert args.runtime.resolve()==root and sha(root/'RUNTIME.json')==p['runtime_sha256']
 assert args.resume.resolve()==Path(st['checkpoint']['path']) and sha(args.resume)==st['checkpoint']['sha256']
 for n,d in read(D/'SOURCES.json')['files'].items():assert sha(D/n)==d,n
 for n,d in read(root/'SOURCE_HASHES.json').items():assert sha(root/'source'/n)==d,n
 sys.path[:0]=[str(D),str(root/'source/tools')]
 from persisted_history_critic import history_class,history_replay_class
 from published_compliance_learner_20261025 import PublishedLearner
 from published_pair_reduction_learner_20261026 import pair_class
 from parameter_replay_capacity4m_20261027 import replay_class
 from train_published_compliance_20261025 import Replay
 from parameter_shared_sampler_pool_20261026 import validate_pool,sampler_affinity
 from published_exact_pipeline_20261026 import cache_class
 from validate_published_finite_check_20261025 import digest
 ck=torch.load(args.resume,map_location='cpu',weights_only=False);validate_protocol(ck['protocol_sha256'],p);validate_parent(ck,p)
 cpus=list(map(int,args.cpus.split(',')));validate_pool(p,args,cpus)
 cls=history_class(pair_class(PublishedLearner,'minimum' if args.controller=='impedance' else 'mean'),h['binding']);replay_cls=history_replay_class(replay_class(Replay),h['binding'])
 source=Path(st['trainer_path']).read_text();assert sha(st['trainer_path'])==st['trainer_sha256'];modified=transform(source);assert hashlib.sha256(modified.encode()).hexdigest()==st['patched_trainer_sha256']
 if args.check_only:
  os.sched_setaffinity(0,{cpus[0]});learner=cls(root,dimension=h['binding']['action_dimension'],direct=False,seed=20261025,device=args.device,algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True);learner.migrate_parent(ck['learner']);replay=replay_cls(h['binding']['action_dimension'],51,20261078);replay.migrate_parent(ck['replay'],h['sidecar']['path']);verify_initial(learner,replay,ck,args.output.parent/'check')
  from train_published_compliance_20261025 import registered_stage_actor_rates
  _, expected_rates=registered_stage_actor_rates(p['completed_stage_continuation'])
  validate_actor_rates([g['lr'] for g in learner.learner.actor_optimizer.param_groups],expected_rates)
  from published_replay_device_cache_20261025 import DeviceReplayCache
  initial=learner.state_dict();replay_initial=copy.deepcopy(replay.rng.bit_generator.state);cache=cache_class(DeviceReplayCache)(replay,args.device);batch=cache.sample(65536);metrics=learner.update(batch);expected=digest(learner.state_dict());learner.load_state_dict(initial);metrics2=learner.update(batch);assert metrics==metrics2 and digest(learner.state_dict())==expected;learner.load_state_dict(initial);replay.rng.bit_generator.state=replay_initial;assert digest(learner.state_dict())==digest(initial)
  put(args.output.parent/'CHECK_ONLY_REVIEW.json',dict(passed=True,time=time.time(),checkpoint_sha256=sha(args.resume),registration_sha256=sha(args.registration),actual_native_batch=65536,disposable_migrated_clone_updates=2,repeat_native_update_full_state_exact=True,original_state_restored=True,clone_weights_promoted=False,new_physics=0,actual_formal_updates=0));return
 gate=read(RUN/'PRELAUNCH_REVIEW.json');assert gate['passed'] and gate['registration_hashes'][args.controller]==sha(args.registration);assert read(args.output.parent/'CHECK_ONLY_REVIEW.json')['passed']
 trainer=root/'source/tools/train_published_compliance_20261025.py';spec=importlib.util.spec_from_file_location('history88_trainer',trainer);module=importlib.util.module_from_spec(spec);exec(compile(modified,str(trainer),'exec'),module.__dict__)
 def stage_check(checkpoint,stage,cycle_budget,rates):
  validate_parent(checkpoint,p);assert stage==p['completed_stage_continuation'] and cycle_budget==1;_,expected=module.registered_stage_actor_rates(stage);validate_actor_rates(rates,expected)
 import published_replay_device_cache_20261025 as cm
 cm.DeviceReplayCache=cache_class(cm.DeviceReplayCache)
 module.Replay=replay_cls;module.PublishedLearner=cls;module.validate_resume_protocol=validate_protocol;module.validate_completed_stage_checkpoint=stage_check;module._parameter_sampler_affinity=sampler_affinity;module._validate_parameter_sampler_pool=validate_pool;module._verify_initial_state=verify_initial
 args.algorithm='cheq';args.seed=20261025;args.cycles=1;(args.output.parent/'trainer_registered.py').write_text(modified)
 put(args.output.parent/'HISTORY_EXECUTION.json',dict(time=time.time(),pid=os.getpid(),registration_sha256=sha(args.registration),driver_sha256=sha(__file__),trainer_sha256=hashlib.sha256(modified.encode()).hexdigest(),cycle=88,automatic_followup=False,maximum_new_actions=41250))
 del ck;module.main(args)
if __name__=='__main__':
 parser=argparse.ArgumentParser()
 for n in ['runtime','registration','resume','output']:parser.add_argument('--'+n,type=Path,required=True)
 parser.add_argument('--controller',choices=['impedance','admittance','vmc'],required=True);parser.add_argument('--cpus',required=True);parser.add_argument('--workers',type=int,default=30);parser.add_argument('--device',required=True);parser.add_argument('--check-only',action='store_true');args=parser.parse_args()
 try:main(args)
 except BaseException as e:
  if args.output.parent.exists():put(args.output.parent/('CHECK_ONLY_FAILURE.json' if args.check_only else 'DRIVER_FAILURE.json'),dict(time=time.time(),error=repr(e)))
  raise
