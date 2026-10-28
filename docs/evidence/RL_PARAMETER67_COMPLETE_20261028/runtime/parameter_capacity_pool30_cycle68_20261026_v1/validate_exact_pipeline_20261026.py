"""Finite matched full-state equivalence and throughput test; no weights promoted."""
import argparse,copy,hashlib,json,os,sys,time
from pathlib import Path
import numpy as np
import torch

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def main(args):
 reg=json.loads(args.registration.read_text());m=args.controller
 for n,h in reg['source_hashes'].items():assert sha(Path(__file__).with_name(n))==h
 os.sched_setaffinity(0,{reg['cpus'][m]});os.nice(10);torch.set_num_threads(1)
 root=Path(reg['runtime']);assert sha(root/'RUNTIME.json')==reg['runtime_sha256']
 for n,h in reg['runtime_sources'].items():assert sha(root/n)==h
 sys.path.insert(0,str(root/'source/tools'))
 from published_compliance_learner_20261025 import PublishedLearner
 from published_replay_device_cache_20261025 import DeviceReplayCache
 from train_published_compliance_20261025 import Replay
 from published_projected_terminal_learner_20261026 import projected_class
 from published_exact_pipeline_20261026 import cache_class,install_foreach,accepted
 from validate_published_finite_check_20261025 import digest
 item=reg['checkpoints'][m];assert sha(item['path'])==item['sha256']
 ck=torch.load(item['path'],weights_only=False,map_location='cpu');state=ck['learner'];arrays=ck['replay']['arrays']
 assert state['terminal_loss_weight']==128 and state['finite_target_projection']['upper_only']
 args.output.mkdir(exist_ok=False);parent=digest(state);original_replay=digest(ck['replay'])
 # Forced inconclusive and rejecting prefixes exercise both fallback branches.
 rng=np.random.default_rng(20261026);checks=0
 for mode in ['random','prefix_zero','last_critic_zero','one_late_positive']:
  masks=rng.binomial(1,.8,(512,5)).astype(np.float32)
  if mode=='prefix_zero':masks[:32]=0
  if mode=='last_critic_zero':masks[:,4]=0
  if mode=='one_late_positive':masks[:,4]=0;masks[63,4]=1
  ids=np.arange(128)
  assert accepted(masks,ids)==(not np.any(masks[ids].sum(axis=0)==0));checks+=1
 learner=projected_class(PublishedLearner)(root,dimension=arrays['actions'].shape[1],direct=False,seed=20261025,device=args.device,algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True)
 original_update=learner.learner.update_target_networks
 replay=Replay(arrays['actions'].shape[1],50,20261026);replay.load_state_dict(copy.deepcopy(ck['replay']))
 slow=DeviceReplayCache(replay,args.device);fast=cache_class(DeviceReplayCache)(replay,args.device)
 results=[];reference=None;initial_batch=None
 for repeat in range(2):
  # Reversed order in the second repeat reduces simple warmup/order bias.
  names=['original','cache_only','cache_and_foreach']
  if repeat:names=names[::-1]
  for name in names:
   learner.load_state_dict(copy.deepcopy(state));learner.learner.update_target_networks=original_update
   for p in learner.learner.agent.parameters():p.grad=None
   assert digest(learner.state_dict())==parent
   replay.rng=np.random.default_rng(reg['seed'])
   patch=install_foreach(learner) if name=='cache_and_foreach' else None
   cache=slow if name=='original' else fast
   for update in range(reg['warmup_updates']):
    batch=cache.sample(32768)
    if update==0:
     batch_digest=digest(batch)
     if initial_batch is None:initial_batch=batch_digest
     else:assert initial_batch==batch_digest
    learner.update(batch)
   torch.cuda.synchronize(learner.device);start=time.perf_counter()
   for update in range(reg['timed_updates']):learner.update(cache.sample(32768))
   torch.cuda.synchronize(learner.device);elapsed=time.perf_counter()-start
   final=digest(learner.state_dict());sampling=digest(replay.rng.bit_generator.state)
   if reference is None:reference=(final,sampling)
   equal=(final,sampling)==reference
   row=dict(repeat=repeat,arm=name,elapsed_s=elapsed,updates_per_s=reg['timed_updates']/elapsed,final_state_sha256=final,sampling_rng_sha256=sampling,full_state_identical=equal,patch=patch)
   results.append(row);write(args.output/'PROGRESS.json',dict(results=results))
   if not equal:raise AssertionError('Candidate final state or sample stream differs: '+name)
 assert digest(state)==parent and digest(ck['replay'])==original_replay
 retained=replay.state_dict();retained['rng']=copy.deepcopy(ck['replay']['rng']);assert digest(retained)==original_replay
 result=dict(passed=True,controller=m,checkpoint_sha256=item['sha256'],registration_sha256=sha(args.registration),results=results,mask_acceptance_edge_cases=checks,parent_unchanged=True,replay_unchanged=True,new_physics=0,auxiliary_weights_saved=False,auxiliary_updates=6*(reg['warmup_updates']+reg['timed_updates']),limitations=['Shared GPU with formal learner; two reversed repeats are finite microbenchmark, not online speedup.','No sampler scheduling, policy timing, update ratio or batch changes.'])
 write(args.output/'FINISHED.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--registration',type=Path,required=True);p.add_argument('--controller',required=True);p.add_argument('--device',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 try:main(a)
 except BaseException as e:
  a.output.mkdir(exist_ok=True);write(a.output/'FAILURE.json',dict(error=repr(e)));raise
