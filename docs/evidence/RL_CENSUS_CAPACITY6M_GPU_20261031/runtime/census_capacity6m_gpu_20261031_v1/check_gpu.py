"""Finite GPU comparison of old/new capacity using unchanged full95 learners.

Three disposable updates per method: old4m, new6m, repeated new6m. No physics,
formal updates, checkpoint writes or online dispatch.
"""
from pathlib import Path
import copy,gc,hashlib,importlib.util,json,os,sys,time,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census_capacity6m_gpu_20261031_v1'
P=B/'runtime/census_capacity6m_preparation_20261031_v1';OLD=B/'runtime/census96_continuation_20261031_v1'
sys.path[:0]=[str(P),str(OLD),str(B/'runtime/source_train17_clock/source/tools')]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(name,data):
 with (O/name).open('x') as f:json.dump(data,f,indent=2,allow_nan=False);f.write('\n')
def main():
 os.sched_setaffinity(0,{54});os.nice(15)
 import numpy as np
 import torch
 torch.set_num_threads(1);torch.cuda.set_device(0)
 from train_published_compliance_20261025 import Replay
 from parameter_replay_capacity4m_20261027 import replay_class as old_class
 from parameter_replay_capacity6m import replay_class,KEY,MARKER
 from persisted_history_critic import KEY as HK
 from persisted_violation_critic import KEY as VK,violation_replay_class
 from census_native import CensusCache,strict_restore
 from validate_published_finite_check_20261025 import digest
 spec=importlib.util.spec_from_file_location('original96_driver',OLD/'driver.py');driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
 plan=json.loads((O/'PLAN.json').read_text())
 for p,h in plan['sources'].items():assert sha(p)==h
 results={}
 for method,ref in plan['parents'].items():
  assert sha(ref['checkpoint']['path'])==ref['checkpoint']['sha256']
  ck=torch.load(ref['checkpoint']['path'],map_location='cpu',weights_only=False)
  p=json.loads(Path(ref['parent_registration']['path']).read_text())
  assert sha(ref['parent_registration']['path'])==ref['parent_registration']['sha256']
  assert ck['cycle']==95 and ck['boundary']=='complete_condition_cycle' and ck['protocol_sha256']==ref['parent_registration']['sha256']
  initial=ck['learner'];ld=digest(initial);s=ck['replay'];rd=digest(s)
  b=p['violation_critic_amendment']['binding'];dimension=b['action_dimension']
  old=violation_replay_class(old_class(Replay),b)(dimension,52,0);old.load_state_dict(s)
  stripped={k:v for k,v in s.items() if k not in (HK,VK)}
  new=violation_replay_class(replay_class(Replay,digest(stripped)),b)(dimension,52,0,capacity=6_000_000);new.load_state_dict(s)
  expected=dict(s,capacity=6_000_000,**{KEY:MARKER})
  assert digest(new.state_dict())==digest(expected)
  oldcache=CensusCache(old,'cuda:0');newcache=CensusCache(new,'cuda:0')
  assert np.array_equal(oldcache.terminal_indices,newcache.terminal_indices)
  assert torch.equal(oldcache.population,newcache.population)
  for k in oldcache.terminal:assert torch.equal(oldcache.terminal[k],newcache.terminal[k])
  # Check the complete retained device mirror, not only the sampled batch.
  for k,arr in old.arrays.items():
   assert torch.equal(oldcache.arrays[k][:old.size],newcache.arrays[k][:new.size])
   for lo in range(0,old.size,65536):
    hi=min(old.size,lo+65536);assert np.array_equal(newcache.arrays[k][lo:hi].cpu().numpy(),arr[lo:hi])
  learner=driver.restore_consumer(initial,p,'cuda:0')
  assert digest(learner.state_dict())==ld
  outcomes=[];batch_digest=None;sample_rng=None
  for tag,cache in [('old4m',oldcache),('new6m',newcache),('new6m_repeat',newcache)]:
   strict_restore(learner,initial,digest)
   cache.replay.rng.bit_generator.state=copy.deepcopy(s['rng'])
   learner.bind_cache(cache);batch=cache.sample(65536)
   bd=digest({k:v.cpu().numpy() for k,v in batch.items()});rng=digest(cache.replay.rng.bit_generator.state)
   if batch_digest is None:batch_digest=bd;sample_rng=rng
   assert bd==batch_digest and rng==sample_rng
   metrics=learner.update(batch);torch.cuda.synchronize()
   state=learner.state_dict();assert state['num_gradient_steps']==initial['num_gradient_steps']+1
   assert all(np.isfinite(float(v)) for v in metrics.values())
   outcomes.append(dict(tag=tag,batch_sha256=bd,sampled_rng_digest=rng,metrics=metrics,updated_full_state_digest=digest(state)))
   del batch,state
  assert all(x['metrics']==outcomes[0]['metrics'] and x['updated_full_state_digest']==outcomes[0]['updated_full_state_digest'] for x in outcomes)
  strict_restore(learner,initial,digest)
  old.rng.bit_generator.state=copy.deepcopy(s['rng']);new.rng.bit_generator.state=copy.deepcopy(s['rng'])
  assert digest(learner.state_dict())==ld and digest(old.state_dict())==rd and digest(new.state_dict())==digest(expected)
  assert digest(initial)==ld and digest(s)==rd and sha(ref['checkpoint']['path'])==ref['checkpoint']['sha256']
  result=dict(passed=True,rows=s['size'],terminals=len(oldcache.terminal_indices),gpu='cuda:0',
      outcomes=outcomes,complete_device_mirror_equal=True,all_terminal_values_and_strata_equal=True,
      full_learner_adam_rng_restored=True,full_old_new_replay_rng_restored=True,
      original_checkpoint_sha256=ref['checkpoint']['sha256'],initial_learner_digest=ld,
      peak_device_allocated_bytes=torch.cuda.max_memory_allocated(0),formal_updates=0,physics=0)
  results[method]=result;put(method+'_REVIEW.json',result);print(method,'GPU exact update and restore passed',flush=True)
  del learner,oldcache,newcache,old,new,ck,s,initial,stripped,expected;gc.collect();torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats(0)
 for p,h in plan['sources'].items():assert sha(p)==h
 put('REVIEW.json',dict(passed=True,time=time.time(),methods=results,disposable_optimizer_updates=9,
      formal_updates=0,physics_steps=0,weights_saved=False,online_deployment=False,
      parent_cycle=95,complete96_parent_tested=False,
      limitation='Exact GPU equivalence at retained full95 data only. No claim after new4m-crossing data; exact full96 recovery/finite97 registration and scientific review remain required.'))
 print('all GPU checks passed',flush=True)
if __name__=='__main__':
 try:main()
 except BaseException:
  put('FAILURE.json',dict(time=time.time(),traceback=traceback.format_exc()));raise
