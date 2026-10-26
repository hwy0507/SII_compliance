"""Finite matched SERL critic-clock diagnostic; no physics or promoted weights."""
import argparse,copy,hashlib,json,os,sys,time
from pathlib import Path
import numpy as np
import torch

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,d):
 temp=p.with_suffix('.tmp');temp.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');temp.replace(p)
def main(args):
 reg=json.loads(args.registration.read_text());os.sched_setaffinity(0,{0});torch.set_num_threads(1)
 assert reg['outer_updates_per_arm']==2000 and reg['record_every']==100 and reg['auxiliary_weights_promoted'] is False
 for name,h in reg['source_hashes'].items():assert sha(Path(__file__).with_name(name))==h
 for item in [reg['checkpoint'],reg['review'],reg['clock']]:assert sha(item['path'])==item['sha256']
 sys.path.insert(0,reg['adapter_runtime'])
 from serl_state_adapter_20261026 import SerlStateLearner
 from validate_serl_state_20261026 import digest
 from serl_critic_clock_extension_20261026 import extend
 args.output.mkdir(exist_ok=False)
 ck=torch.load(reg['checkpoint']['path'],weights_only=False,map_location='cpu');assert ck['cycle']==8 and ck['boundary']=='complete_condition_cycle'
 review=json.loads(Path(reg['review']['path']).read_text());assert review['passed'] and review['methods']['direct']['checkpoint_sha256']==reg['checkpoint']['sha256']
 initial=ck['learner'];parent_digest=digest(initial);arrays=ck['replay']['arrays'];replay_digest=digest(ck['replay']);clock=np.load(reg['clock']['path']);assert clock.shape==(ck['replay']['size'],2)
 terminals=np.flatnonzero(arrays['dones'][:,0]);sample=np.random.default_rng(reg['seed']).choice(np.flatnonzero(arrays['dones'][:,0]==0),4096,replace=False)
 results=[];initial_reference=None
 for name in ['critic_clock','original']:
  a=SerlStateLearner(Path(reg['runtime']),upstream=Path(reg['upstream']),upstream_manifest=Path(reg['upstream_manifest']),dimension=7,direct=True,seed=reg['seed'],device='cuda:0');a.load_state_dict(copy.deepcopy(initial));assert digest(a.state_dict())==parent_digest
  receipt=None
  def batch(ids,clock_enabled=None):
   selected={k:v[ids] for k,v in arrays.items()}
   if (name=='critic_clock') if clock_enabled is None else clock_enabled:
    selected['observations']=np.concatenate([selected['observations'],clock[ids,0:1]],axis=1)
    selected['next_observations']=np.concatenate([selected['next_observations'],clock[ids,1:2]],axis=1)
   return selected
  jax=a.jax
  if name=='critic_clock':
   old=a.agent;candidate,receipt=extend(a);base=a.batch(batch(sample[:256],False));extended=a.batch(batch(sample[:256],True));key=jax.random.PRNGKey(261)
   before=np.asarray(old.forward_critic(base['observations'],base['actions'],rng=key));after=np.asarray(candidate.forward_critic(extended['observations'],extended['actions'],rng=key))
   np.testing.assert_allclose(before,after,rtol=2e-6,atol=1e-4)
   for argmax in [True,False]:
    kw=dict(argmax=argmax) if argmax else dict(seed=jax.random.PRNGKey(12))
    np.testing.assert_array_equal(np.asarray(old.sample_actions(base['observations'],**kw)),np.asarray(candidate.sample_actions(extended['observations'],**kw)))
   alternate=extended['observations'].at[:,-1].set(0.)
   np.testing.assert_array_equal(np.asarray(candidate.sample_actions(alternate,argmax=True)),np.asarray(candidate.sample_actions(extended['observations'],argmax=True)))
   a.agent=candidate;receipt.update(initial_critic_max_abs_difference=float(np.max(abs(before-after))),initial_actor_exact=True,actor_invariant_to_clock=True)
   write(args.output/'CLOCK_GATE.json',dict(passed=True,**receipt,new_optimizer_updates=0))
  def diagnose():
   t=a.batch(batch(terminals));q=np.asarray(a.agent.forward_critic(t['observations'],t['actions'],rng=jax.random.PRNGKey(261)));error=abs(q-np.asarray(t['rewards'])[None])
   s=a.batch(batch(sample));key,ak=jax.random.split(jax.random.PRNGKey(262));actions,logp=a.agent._compute_next_actions(s,ak);tq=a.agent.forward_target_critic(s['next_observations'],actions,rng=key);target=s['rewards']+.9995*s['masks']*tq[jax.numpy.array([7,3])].min(axis=0);pred=np.asarray(a.agent.forward_critic(s['observations'],s['actions'],rng=key))
   return dict(terminal_mae=float(error.mean()),terminal_p95=float(np.percentile(error,95)),terminal_max=float(error.max()),replay_q_mean=float(pred.mean()),replay_q_abs_p95=float(np.percentile(abs(pred),95)),replay_q_min=float(pred.min()),replay_q_max=float(pred.max()),td_mae=float(abs(pred-np.asarray(target)[None]).mean()),temperature=float(a.agent.forward_temperature()))
  entry=dict(arm=name,initial=diagnose(),curve=[],extension=receipt)
  rng=np.random.default_rng(reg['seed']);start=time.time()
  for update in range(reg['outer_updates_per_arm']):
   ids=rng.integers(ck['replay']['size'],size=32768);metrics=a.update(batch(ids))
   if (update+1)%reg['record_every']==0:
    row=dict(outer_updates=update+1,critic_updates=8*(update+1),metrics=metrics,diagnostic=diagnose(),time=time.time());entry['curve'].append(row);write(args.output/'PROGRESS.json',dict(arm=name,**row))
  assert a.learner.num_gradient_steps-initial['num_gradient_steps']==16000
  entry.update(final=diagnose(),elapsed_s=time.time()-start,sampling_rng_sha256=digest(rng.bit_generator.state),parent_unchanged=True);results.append(entry);write(args.output/(name+'.json'),entry)
 assert results[0]['sampling_rng_sha256']==results[1]['sampling_rng_sha256'] and digest(initial)==parent_digest and digest(ck['replay'])==replay_digest
 write(args.output/'FINISHED.json',dict(passed=True,results=results,checkpoint_sha256=reg['checkpoint']['sha256'],registration_sha256=sha(args.registration),new_physics=0,auxiliary_critic_updates=32000,auxiliary_actor_updates=4000,auxiliary_weights_saved=False,parent_unchanged=True,limitations=['Critic architecture adaptation; no online task or convergence conclusion.','All old weights, target, Adam moments/counters and RNG retained; eight new clock parameter/moment leaves are zero.','Same official10-critic/random2-target/no-entropy-backup/8-to-1 optimizer; canonical48 actor.','Replay clocks reconstructed solely from recorded condition action counts, not future rewards.']))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--registration',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 try:main(a)
 except BaseException as e:
  a.output.mkdir(exist_ok=True);write(a.output/'FAILURE.json',dict(error=repr(e)));raise
