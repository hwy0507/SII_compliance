from pathlib import Path
import sys,os,json,hashlib,time,copy
O=Path(__file__).parent;B=O.parents[1]
plan=json.loads((O/'PLAN.json').read_text());os.sched_setaffinity(0,{52});os.nice(15)
import torch,numpy as np
torch.set_num_threads(1)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(n,d):(O/n).write_text(json.dumps(d,indent=2)+'\n')
try:
 assert sha(plan['checkpoint'])==plan['checkpoint_sha256']
 assert sha(O/'serl_replay_take_gather_20261027.py')==plan['candidate_sha256']
 reg=json.loads(Path(plan['parent_registration']).read_text());root=Path(reg['runtime']);rt=Path(plan['runtime'])
 sys.path[:0]=[str(O),str(rt),reg['source_adapter'],str(root/'source/tools')]
 from validate_serl_state_20261026 import digest
 from train_serl_state_20261026 import Replay
 from serl_multistep_state_adapter_20261026 import SerlMultistepLearner
 from serl_multistep_batch_transfer_20261026 import transfer_class
 from resume_serl_capacity_reviewed_continuation_20261027 import capacity_replay
 from resume_serl_interrupted25_20261027 import quarantine_replay
 from serl_replay_take_gather_20261027 import take_class
 ck=torch.load(plan['checkpoint'],map_location='cpu',weights_only=False);before=digest(ck)
 base=capacity_replay(Replay,reg,ck)
 # Startup snapshot includes old quarantined0-29 and new online30-59 queues.
 old_pending={k:v for k,v in ck['replay']['multistep_target_extension']['pending'].items() if k<30}
 assert sum(map(len,old_pending.values()))==930
 guarded=quarantine_replay(base,old_pending);candidate=take_class(guarded,plan['sample_source_sha256'])
 a,b=guarded(7,49,1),candidate(7,49,2);a.load_state_dict(ck['replay']);b.load_state_dict(ck['replay'])
 assert digest(a.state_dict())==digest(b.state_dict())==digest(ck['replay'])
 for _ in range(plan['sample_checks']):
  x,y=a.sample(65536),b.sample(65536)
  assert digest(x)==digest(y);assert digest(a.rng.bit_generator.state)==digest(b.rng.bit_generator.state)
 saved=b.state_dict();restored=candidate(7,49,3);restored.load_state_dict(saved)
 assert digest(restored.state_dict())==digest(saved)
 assert digest(restored.sample(65536))==digest(b.sample(65536))
 args=dict(upstream=B/'runtime/serl_upstream_1fa2af7',upstream_manifest=B/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json',dimension=7,direct=True,seed=20261026,device='cuda:0')
 cls=transfer_class(SerlMultistepLearner);left=cls(root,**args);right=cls(root,**args)
 left.load_state_dict(ck['learner']);right.load_state_dict(ck['learner'])
 assert digest(left.state_dict())==digest(right.state_dict())==digest(ck['learner'])
 assert digest(left.batch(x))==digest(right.batch(y))
 t=time.monotonic();lm=left.update(x);rm=right.update(y)
 assert digest(lm)==digest(rm),'metrics mismatch'
 ld,rd=digest(left.state_dict()),digest(right.state_dict());assert ld==rd,'updated learner/network/Adam/RNG mismatch'
 assert left.state_dict()['num_gradient_steps']==ck['learner']['num_gradient_steps']+8
 assert right.state_dict()['outer_updates']==ck['learner']['outer_updates']+1
 assert digest(ck)==before and sha(plan['checkpoint'])==plan['checkpoint_sha256']
 # Reject mismatched parent source and impossible mature endpoint; no silent clipping of corrupt indices.
 try:take_class(guarded,'0'*64)
 except ValueError:pass
 else:raise AssertionError('Wrong parent sampler source accepted')
 b.target_endpoints[b.ready_array[:len(b.ready)]]=-1
 try:b.sample(65536)
 except ValueError:pass
 else:raise AssertionError('Invalid endpoint silently clipped')
 report={'passed':True,'time':time.time(),'plan_sha256':sha(O/'PLAN.json'),'candidate_sha256':sha(O/'serl_replay_take_gather_20261027.py'),'gate_sha256':sha(__file__),'checkpoint_sha256':plan['checkpoint_sha256'],'sample_checks':3,'all_sample_fields_and_rng_exact':True,'serialized_replay_and_restore_exact':True,'full_batch_pytree_exact':True,'full_next_update_state_metrics_rng_exact':True,'after_update_learner_digest':ld,'old_pending_quarantined':930,'negative_guards':2,'outer_updates_per_arm':1,'total_critic_updates':16,'total_actor_updates':2,'new_physics':0,'weights_saved':False,'formal_deployment':False,'update_and_compare_seconds_including_compilation':time.monotonic()-t,'limitation':'Same saved startup parent, one update per arm; does not claim all future random sequences or real end-to-end speedup. Running official recovery26 unchanged.'}
 write('REVIEW.json',report);print(json.dumps(report,indent=2),flush=True)
except BaseException as e:
 write('FAILURE.json',{'time':time.time(),'error':repr(e)});raise
