"""Preserve audited complete recovery78 state; prepare one finite79 with interrupted75 history retained."""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,os,sys,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
def transform(source):
 seam="        steps, cycles, start_cycle = checkpoint['steps'], checkpoint['cycles'], checkpoint['cycle']+1"
 assert source.count(seam)==1
 source=source.replace(seam,seam+"\n        _verify_initial_state(learner, replay, checkpoint, out.parent)")
 seam='            environment_state_saved=False,';assert source.count(seam)==1
 source=source.replace(seam,"            interruption_recovery=protocol['interrupted_episode_recovery'],\n"+seam)
 seam='        completed_stage_continuation=stage,';assert source.count(seam)==1
 source=source.replace(seam,seam+"\n        interruption_recovery=protocol['interrupted_episode_recovery'],")
 source=source.replace("            environment_state_saved=False,", "            recovery_continuation=protocol['post_interruption_continuation'],\n            environment_state_saved=False,")
 source=source.replace("        completed_stage_continuation=stage,", "        completed_stage_continuation=stage,\n        recovery_continuation=protocol['post_interruption_continuation'],")
 return source

def validate_protocol(checkpoint_digest,protocol,current_digest):
 st=protocol['post_interruption_continuation'];prior=st['parent_registration'];previous=read(prior['path'])
 if sha(prior['path'])!=prior['sha256'] or checkpoint_digest!=prior['sha256']:raise ValueError('Exact recovery78 registration required')
 if {k:v for k,v in protocol.items() if k!='post_interruption_continuation'}!={k:v for k,v in previous.items() if k!='post_interruption_continuation'}:raise ValueError('Scientific or historical recovery protocol changed')
 if (st['parent_cycle']!=78 or st['new_cycle']!=79 or st['new_cycles']!=1 or st['maximum_new_actions']!=41250 or st['environment_state_saved'] or st['old_window_continuity_claim'] or st['automatic_followup'] or st['optimizer_settings_changed']):raise ValueError('Invalid complete recovery continuation semantics')
 for key in ['cycle_review','health_review']:
  if sha(st[key]['path'])!=st[key]['sha256']:raise ValueError('Complete78 review binding changed')
 review=read(st['cycle_review']['path']);health=read(st['health_review']['path']);m=st['controller']
 if not review['passed'] or review['methods'][m]['checkpoint_sha256']!=st['checkpoint']['sha256'] or health['methods'][m]['checkpoint_sha256']!=st['checkpoint']['sha256']:raise ValueError('Evidence must cover exact complete78 checkpoint')
 if sha(st['recovery_driver']['path'])!=st['recovery_driver']['sha256']:raise ValueError('Original recovery driver changed')
 prior_stage=previous['post_interruption_continuation'];prior_driver=st['previous_driver']
 if sha(prior_driver['path'])!=prior_driver['sha256'] or prior_driver['sha256']!=prior_stage['driver_sha256']:raise ValueError('Previous continuation driver changed')
 spec=importlib.util.spec_from_file_location('validated_previous_recovery78',prior_driver['path']);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 module.validate_protocol(prior_stage['parent_registration']['sha256'],previous,prior['sha256'])
 return previous

def validate_parent(ck,st):
 review=read(st['cycle_review']['path'])['methods'][st['controller']]
 previous=read(st['parent_registration']['path'])
 if (ck['cycle']!=78 or ck['boundary']!='complete_condition_cycle' or ck['environment_state_saved'] or ck['steps']!=review['steps'] or ck['seed']!=20261025 or any(c['cycle']==75 for c in ck['cycles']) or ck['cycles'][-1]['cycle']!=78 or ck['interruption_recovery']!=previous['interrupted_episode_recovery'] or ck.get('recovery_continuation')!=previous['post_interruption_continuation']):raise ValueError('Not the exact complete recovery78 boundary')

def verify_initial_state(learner,replay,checkpoint,out):
 from validate_published_finite_check_20261025 import digest
 ld,rd=digest(learner.state_dict()),digest(replay.state_dict())
 assert ld==digest(checkpoint['learner']) and rd==digest(checkpoint['replay'])
 write(out/'INITIAL_STATE_REVIEW.json',dict(passed=True,time=time.time(),steps=checkpoint['steps'],learner_digest=ld,replay_digest=rd,history_digest=digest(checkpoint['cycles']),optimizer_updates=0,new_physics=0,all_complete78_and_partial75_rows_retained=True))

def main(args):
 import torch,numpy as np
 torch.set_num_threads(1)
 p=read(args.registration);st=p['post_interruption_continuation'];root=args.runtime.resolve();rt=Path(st['original_runtime'])
 assert str(root)==p['runtime'] and sha(root/'RUNTIME.json')==p['runtime_sha256']
 assert sha(__file__)==st['driver_sha256'] and str(args.resume.resolve())==st['checkpoint']['path'] and sha(args.resume)==st['checkpoint']['sha256']
 for n,h in st['source_hashes'].items():assert sha(rt/n)==h,n
 for n,h in read(root/'SOURCE_HASHES.json').items():assert sha(root/'source'/n)==h,n
 sys.path[:0]=[str(rt),str(root/'source/tools')]
 from validate_published_finite_check_20261025 import digest
 from published_compliance_learner_20261025 import PublishedLearner
 from published_pair_reduction_learner_20261026 import pair_class,marker
 from published_exact_pipeline_20261026 import cache_class
 from parameter_replay_capacity4m_20261027 import replay_class
 from train_published_compliance_20261025 import Replay
 from parameter_shared_sampler_pool_20261026 import validate_pool,sampler_affinity
 import resume_cheq_capacity4m_pool30_20261027 as old
 ck=torch.load(args.resume,map_location='cpu',weights_only=False);previous=validate_protocol(ck['protocol_sha256'],p,sha(args.registration));validate_parent(ck,st)
 assert ck['controller']==args.controller and ck['replay']['capacity']==4000000
 recovery_spec=importlib.util.spec_from_file_location('validated_original_recovery',st['recovery_driver']['path']);recovery_module=importlib.util.module_from_spec(recovery_spec);recovery_spec.loader.exec_module(recovery_module)
 base75=recovery_module.validate_protocol(previous['interrupted_episode_recovery']['parent_registration']['sha256'],{k:v for k,v in previous.items() if k!='post_interruption_continuation'},sha(st['parent_registration']['path']))
 old.validate(base75['resume_parent_registration']['sha256'],base75,sha(previous['interrupted_episode_recovery']['parent_registration']['path']))
 cpus=list(map(int,args.cpus.split(',')));assert len(cpus)==13 and args.workers==30;validate_pool(p,args,cpus)
 reduction=previous['batch_size_stage']['reduction'];cls=pair_class(PublishedLearner,reduction);Replay4m=replay_class(Replay,previous['replay_capacity_followup_stage']['entry_replay_digest'])
 assert ck['learner']['target_pair_reduction']==marker(reduction) and ck['learner']['terminal_loss_weight']==128
 source=Path(st['trainer_path']).read_text();assert sha(st['trainer_path'])==st['trainer_sha256'];modified=transform(source);assert hashlib.sha256(modified.encode()).hexdigest()==st['patched_trainer_sha256']
 if args.check_only:
  os.sched_setaffinity(0,{cpus[0]});learner=cls(root,dimension=ck['replay']['arrays']['actions'].shape[1],direct=False,seed=20261025,device='cpu',algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True);learner.load_state_dict(ck['learner']);assert digest(learner.state_dict())==digest(ck['learner'])
  replay=Replay4m(ck['replay']['arrays']['actions'].shape[1],50,20261078);replay.load_state_dict(ck['replay']);assert digest(replay.state_dict())==digest(ck['replay'])
  plain=dict(ck['replay']);plain.pop('replay_capacity_extension');plain.pop('replay_capacity_followup');ordinary=Replay(ck['replay']['arrays']['actions'].shape[1],50,20261078,capacity=4000000);ordinary.load_state_dict(plain)
  assert digest(replay.sample(65536))==digest(ordinary.sample(65536));assert digest(replay.rng.bit_generator.state)==digest(ordinary.rng.bit_generator.state)
  rejects=0
  for key,val in [('learner_batch_size',256),('learner_updates_per_transition',2),('critic_clock',False)]:
   bad=copy.deepcopy(p);bad[key]=val
   try:validate_protocol(ck['protocol_sha256'],bad,'')
   except ValueError:rejects+=1
   else:raise AssertionError('Scientific contract mutation accepted')
  for key,val in [('new_cycle',78),('new_cycles',2),('old_window_continuity_claim',True),('environment_state_saved',True),('optimizer_settings_changed',True),('automatic_followup',True)]:
   bad=copy.deepcopy(p);bad['post_interruption_continuation'][key]=val
   try:validate_protocol(ck['protocol_sha256'],bad,'')
   except ValueError:rejects+=1
   else:raise AssertionError('Recovery mutation accepted')
  write(args.output.parent/'CHECK_ONLY_REVIEW.json',dict(passed=True,time=time.time(),controller=args.controller,checkpoint_sha256=sha(args.resume),full_learner_state_exact=True,full_replay_and_next65536_exact=True,learner_digest=digest(ck['learner']),replay_digest=digest(ck['replay']),history_digest=digest(ck['cycles']),negative_rejections=rejects,new_physics=0,optimizer_updates=0));print(args.controller,'exact complete78 check-only passed',flush=True);return
 check=read(args.output.parent/'CHECK_ONLY_REVIEW.json');assert check['passed'] and check['checkpoint_sha256']==sha(args.resume)
 gate=read(args.output.parent.parent/'PRELAUNCH_REVIEW.json');assert gate['passed'] and gate['registration_hashes'][args.controller]==sha(args.registration)
 trainer=root/'source/tools/train_published_compliance_20261025.py';spec=importlib.util.spec_from_file_location('frozen_recovery78_continuation',trainer);module=importlib.util.module_from_spec(spec);exec(compile(modified,str(trainer),'exec'),module.__dict__)
 def validate_recovery_stage(checkpoint,stage,cycle_budget,actual_rates):
  validate_parent(checkpoint,st);assert stage==previous['completed_stage_continuation'] and cycle_budget==1
  _,expected=module.registered_stage_actor_rates(stage);assert len(actual_rates)==len(expected) and all(np.isfinite(a) and abs(a-e)<1e-12 for a,e in zip(actual_rates,expected))
  assert stage['actor_learning_rate_factor'] is None and stage.get('bellman_target_count') is None and checkpoint['learner'].get('bellman_target_count',2)==2
 import published_replay_device_cache_20261025 as cache_module
 cache_module.DeviceReplayCache=cache_class(cache_module.DeviceReplayCache)
 module.Replay=Replay4m;module.PublishedLearner=cls;module.validate_resume_protocol=validate_protocol;module.validate_completed_stage_checkpoint=validate_recovery_stage
 module._parameter_sampler_affinity=sampler_affinity;module._validate_parameter_sampler_pool=validate_pool;module._verify_initial_state=verify_initial_state
 args.algorithm='cheq';args.seed=20261025;args.cycles=1
 (args.output.parent/'trainer_registered.py').write_text(modified)
 write(args.output.parent/'RECOVERY_EXECUTION.json',dict(time=time.time(),pid=os.getpid(),checkpoint=st['checkpoint'],registration_sha256=sha(args.registration),driver_sha256=sha(__file__),new_cycle=79,maximum_new_actions=41250,cycle75_complete=False,old_window_continuity_claim=False,automatic_followup=False))
 del ck
 module.main(args)
if __name__=='__main__':
 parser=argparse.ArgumentParser()
 for n in ['runtime','registration','resume','output']:parser.add_argument('--'+n,type=Path,required=True)
 parser.add_argument('--controller',choices=['impedance','admittance','vmc'],required=True);parser.add_argument('--cpus',required=True);parser.add_argument('--workers',type=int,default=30);parser.add_argument('--device',required=True);parser.add_argument('--check-only',action='store_true')
 a=parser.parse_args()
 try:main(a)
 except BaseException as e:
  if a.output.parent.exists():write(a.output.parent/('CHECK_ONLY_FAILURE.json' if a.check_only else 'DRIVER_FAILURE.json'),dict(time=time.time(),error=repr(e)))
  raise
