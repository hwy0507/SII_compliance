"""One finite continuation92 from exact trained91; preserve learned52 and no automatic93."""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,os,sys,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;RUN=B/'runs/parameter_violation_cycle92_20261030_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def transform(source):
 # Same52 revision: exact actual91 trainer bytes, no numerical/source changes.
 for seam,count in [("learner.load_state_dict(checkpoint['learner'])",1),("replay.load_state_dict(checkpoint['replay'])",1),("violation_critic_amendment=protocol['violation_critic_amendment']",2),("learner.consume_interval(event['interval'], stream=slot)",1),("plateau_status([c for c in cycles if c['cycle'] >= 90])",1)]:
  if source.count(seam)!=count:raise ValueError('Exact91 trainer seam drift: '+seam)
 if 'require_online_launch' in source or 'migrate_parent(' in source:raise ValueError('Migration trainer forbidden for learned91')
 return source

def validate_protocol(parent_digest,p,current_digest=None):
 st=p['post_interruption_continuation'];previous=read(st['parent_registration']['path'])
 if sha(st['parent_registration']['path'])!=parent_digest or st['parent_registration']['sha256']!=parent_digest:raise ValueError('Exact trained91 registration required')
 if {k:v for k,v in p.items() if k!='post_interruption_continuation'}!={k:v for k,v in previous.items() if k!='post_interruption_continuation'}:raise ValueError('Scientific/historical contract changed')
 if (st['parent_cycle'],st['new_cycle'],st['new_cycles'],st['maximum_new_actions'],st['automatic_followup'],st['optimizer_settings_changed'],st['old_window_continuity_claim'],st['environment_state_saved'])!=(91,92,1,41250,False,False,False,False):raise ValueError('Finite92 budget contract drift')
 if sha(__file__)!=st['driver_sha256']:raise ValueError('Driver drift')
 for key in ('cycle_review','health_review','previous_driver','loss_review','fixed_terminal_review','training_pair_review','scientific_decision','stability_plan','old_window_failure','abort_review'):
  if sha(st[key]['path'])!=st[key]['sha256']:raise ValueError('Evidence drift: '+key)
 decision=read(st['scientific_decision']['path'])
 if (decision['parent_cycle'],decision['new_cycle'],decision['new_cycles'],decision['maximum_new_actions_per_method'],decision['automatic_followup'],decision['offline_weights_promoted'],decision['critic_revision'])!=(91,92,1,41250,False,False,'raw_violation52'):raise ValueError('Scientific decision drift')
 for item in decision['evidence']:
  if sha(item['path'])!=item['sha256']:raise ValueError('Decision evidence drift')
 spec=importlib.util.spec_from_file_location('validated_scientific91_driver',st['previous_driver']['path']);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 old=previous['post_interruption_continuation'];module.validate_protocol(old['parent_registration']['sha256'],previous)
 m=st['controller'];review=read(st['cycle_review']['path']);health=read(st['health_review']['path']);loss=read(st['loss_review']['path'])
 if not review['passed'] or not loss['passed'] or health['cycle']!=91 or health['optimizer_updates_performed']!=0:raise ValueError('Complete91 evidence missing')
 if review['methods'][m]['checkpoint_sha256']!=st['checkpoint']['sha256'] or health['methods'][m]['checkpoint_sha256']!=st['checkpoint']['sha256']:raise ValueError('Complete91 checkpoint binding mismatch')
 if loss['methods'][m]['rows']!=review['methods'][m]['new_transitions'] or not loss['methods'][m]['all_finite']:raise ValueError('Complete91 loss rows mismatch')
 if read(st['fixed_terminal_review']['path'])['methods'][m]['checkpoint_sha256']!=st['checkpoint']['sha256']:raise ValueError('Fixed-terminal parent mismatch')
 window=read(st['stability_plan']['path'])
 if window['cycles']!=[90,91,92] or window['relative_limit']!=.05 or window['near_zero_guard']!=1. or window['replicates']!=5000 or window['bootstrap_seed']!=2026102861 or window['automatic_training']:raise ValueError('Revision stability registration changed')
 if window['violation_amendment'][m]!=p['violation_critic_amendment'] or window['history_amendment'][m]!=p['history_critic_amendment']:raise ValueError('Window revision mismatch')
 return previous

def validate_parent(ck,p):
 from persisted_history_critic import KEY as HK,marker as hm
 from persisted_violation_critic import KEY as VK,marker as vm
 from parameter_replay_capacity_20261026 import MARKER as OLD_CAP
 from parameter_replay_capacity4m_20261027 import MARKER as CAP
 st=p['post_interruption_continuation'];previous=read(st['parent_registration']['path']);review=read(st['cycle_review']['path'])['methods'][st['controller']];v=p['violation_critic_amendment'];h=p['history_critic_amendment'];n=review['steps']
 if ck['protocol_sha256']!=st['parent_registration']['sha256'] or ck['controller']!=st['controller'] or ck['controller']!=v['binding']['method'] or ck['seed']!=20261025:raise ValueError('Exact trained91 identity required')
 if ck['cycle']!=91 or ck['boundary']!='complete_condition_cycle' or ck['environment_state_saved'] or ck['steps']!=n:raise ValueError('Complete trained91 boundary required')
 parent_review=read(previous['post_interruption_continuation']['cycle_review']['path'])['methods'][st['controller']]
 if n!=parent_review['steps']+review['new_transitions'] or not 0<review['new_transitions']<=41250:raise ValueError('Actual complete91 rows from exact complete90 including abort required')
 if ck['cycles'][-1]['cycle']!=91 or any(c['cycle']==75 for c in ck['cycles']):raise ValueError('Historical complete cycles changed')
 if ck['recovery_continuation']!=previous['post_interruption_continuation'] or ck['interruption_recovery']!=p['interrupted_episode_recovery']:raise ValueError('Recovery metadata drift')
 if ck['history_critic_amendment']!=h or ck['violation_critic_amendment']!=v:raise ValueError('Trained architecture amendments changed')
 for key in ('learner','replay'):
  if ck[key].get(HK)!=hm(h['binding']) or ck[key].get(VK)!=vm(v['binding']):raise ValueError('Both learned architecture markers required')
 replay=ck['replay']
 if replay['size']!=n or replay['cursor']!=n or replay['capacity']!=4_000_000 or replay['replay_capacity_extension']!=OLD_CAP or replay['replay_capacity_followup']!=CAP:raise ValueError('Append-only replay metadata changed')
 if any(replay['arrays'][k].shape!=(n,52) for k in ('observations','next_observations')):raise ValueError('Full learned52 replay required')
 if ck['learner']['num_gradient_steps']!=review['updates']:raise ValueError('Trained optimizer counter changed')

def verify_initial(learner,replay,ck,out):
 from validate_published_finite_check_20261025 import digest
 ls=learner.state_dict();rs=replay.state_dict()
 assert digest(ls)==digest(ck['learner']) and digest(rs)==digest(ck['replay'])
 put(out/'INITIAL_STATE_REVIEW.json',dict(passed=True,time=time.time(),learner_digest=digest(ls),replay_digest=digest(rs),full_trained91_learner_and_replay_exact=True,learned_history_weights_and_adam_retained=True,learned_violation_weights_and_adam_retained=True,history_digest=digest(ck['cycles']),new_physics=0,optimizer_updates=0))

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
 from violation_pipeline import classes
 from published_compliance_learner_20261025 import PublishedLearner
 from published_pair_reduction_learner_20261026 import pair_class
 from parameter_replay_capacity4m_20261027 import replay_class
 from train_published_compliance_20261025 import Replay
 from parameter_shared_sampler_pool_20261026 import validate_pool,sampler_affinity
 from published_exact_pipeline_20261026 import cache_class
 from validate_published_finite_check_20261025 import digest
 ck=torch.load(args.resume,map_location='cpu',weights_only=False);validate_protocol(ck['protocol_sha256'],p);validate_parent(ck,p)
 cpus=list(map(int,args.cpus.split(',')));validate_pool(p,args,cpus)
 cls,replay_cls=classes(p)
 source=Path(st['trainer_path']).read_text();assert sha(st['trainer_path'])==st['trainer_sha256'];modified=transform(source);assert hashlib.sha256(modified.encode()).hexdigest()==st['patched_trainer_sha256']
 if args.check_only:
  os.sched_setaffinity(0,{cpus[0]});learner=cls(root,dimension=h['binding']['action_dimension'],direct=False,seed=20261025,device=args.device,algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True);learner.load_state_dict(ck['learner']);replay=replay_cls(h['binding']['action_dimension'],52,20261078);replay.load_state_dict(ck['replay']);verify_initial(learner,replay,ck,args.output.parent/'check')
  from train_published_compliance_20261025 import registered_stage_actor_rates
  _, expected_rates=registered_stage_actor_rates(p['completed_stage_continuation'])
  validate_actor_rates([g['lr'] for g in learner.learner.actor_optimizer.param_groups],expected_rates)
  from published_replay_device_cache_20261025 import DeviceReplayCache
  initial=learner.state_dict();replay_initial=copy.deepcopy(replay.rng.bit_generator.state);cache=cache_class(DeviceReplayCache)(replay,args.device);batch=cache.sample(65536);metrics=learner.update(batch);expected=digest(learner.state_dict());learner.load_state_dict(initial);metrics2=learner.update(batch);assert metrics==metrics2 and digest(learner.state_dict())==expected;learner.load_state_dict(initial);replay.rng.bit_generator.state=replay_initial;assert digest(learner.state_dict())==digest(initial)
  assert digest(replay.state_dict())==digest(ck['replay']) and sha(args.resume)==st['checkpoint']['sha256']
  put(args.output.parent/'CHECK_ONLY_REVIEW.json',dict(passed=True,time=time.time(),checkpoint_sha256=sha(args.resume),registration_sha256=sha(args.registration),actual_native_batch=65536,disposable_restored_clone_updates=2,repeat_native_update_full_state_exact=True,original_state_restored=True,clone_weights_promoted=False,new_physics=0,actual_formal_updates=0));return
 gate=read(RUN/'PRELAUNCH_REVIEW.json');assert gate['passed'] and gate['registration_hashes'][args.controller]==sha(args.registration);assert read(args.output.parent/'CHECK_ONLY_REVIEW.json')['passed']
 trainer=root/'source/tools/train_published_compliance_20261025.py';spec=importlib.util.spec_from_file_location('violation92_trainer',trainer);module=importlib.util.module_from_spec(spec);exec(compile(modified,str(trainer),'exec'),module.__dict__)
 def stage_check(checkpoint,stage,cycle_budget,rates):
  validate_parent(checkpoint,p);assert stage==p['completed_stage_continuation'] and cycle_budget==1;_,expected=module.registered_stage_actor_rates(stage);validate_actor_rates(rates,expected)
 import published_replay_device_cache_20261025 as cm
 cm.DeviceReplayCache=cache_class(cm.DeviceReplayCache)
 module.Replay=replay_cls;module.PublishedLearner=cls;module.validate_resume_protocol=validate_protocol;module.validate_completed_stage_checkpoint=stage_check;module._parameter_sampler_affinity=sampler_affinity;module._validate_parameter_sampler_pool=validate_pool;module._verify_initial_state=verify_initial
 args.algorithm='cheq';args.seed=20261025;args.cycles=1;(args.output.parent/'trainer_registered.py').write_text(modified)
 put(args.output.parent/'VIOLATION_EXECUTION.json',dict(time=time.time(),pid=os.getpid(),registration_sha256=sha(args.registration),driver_sha256=sha(__file__),trainer_sha256=hashlib.sha256(modified.encode()).hexdigest(),cycle=92,automatic_followup=False,maximum_new_actions=41250))
 del ck;module.main(args)
if __name__=='__main__':
 parser=argparse.ArgumentParser()
 for n in ['runtime','registration','resume','output']:parser.add_argument('--'+n,type=Path,required=True)
 parser.add_argument('--controller',choices=['impedance','admittance','vmc'],required=True);parser.add_argument('--cpus',required=True);parser.add_argument('--workers',type=int,default=30);parser.add_argument('--device',required=True);parser.add_argument('--check-only',action='store_true');args=parser.parse_args()
 try:main(args)
 except BaseException as e:
  if args.output.parent.exists():put(args.output.parent/('CHECK_ONLY_FAILURE.json' if args.check_only else 'DRIVER_FAILURE.json'),dict(time=time.time(),error=repr(e)))
  raise
