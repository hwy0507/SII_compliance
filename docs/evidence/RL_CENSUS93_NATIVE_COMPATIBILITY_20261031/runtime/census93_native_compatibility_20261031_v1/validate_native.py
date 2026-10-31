"""Finite disposable full-native compatibility: exact parent93, no physics."""
from pathlib import Path
import os,sys,time,json,copy,hashlib,traceback,gc,types
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census93_native_compatibility_20261031_v1'
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def main(m):
 import numpy as np
 import torch
 p=rd(O/'PLAN.json');e=p['methods'][m];out=O/m;out.mkdir();t=time.monotonic();os.sched_setaffinity(0,{e['cpu']});torch.set_num_threads(1)
 for path,h in p['dependencies'].items():assert sha(path)==h,path
 for name,h in rd(O/'SOURCE_LOCK.json').items():assert sha(D/name)==h,name
 sys.path[:0]=[str(D),str(B/'runtime/violation93_continuation_20261031_v1'),str(B/'runtime/source_train17_clock/source/tools'),str(B/'runtime/violation90_frozen_preparation_20261030_v1'),str(B/'runtime/violation93_terminal_followup_20261031_v1'),str(B/'runtime/violation93_terminal_census_ablation_20261031_v1')]
 from violation_pipeline import classes
 from compare93 import validate_complete93
 from frozen_helpers import capture_rng,restore_rng
 from validate_published_finite_check_20261025 import digest
 from published_exact_pipeline_20261026 import cache_class,accepted
 from published_replay_device_cache_20261025 import DeviceReplayCache
 from census_native import CensusCache,census_class,KEY,marker,native_source,install,losses,strict_restore
 from conditional import weights
 cp=Path(e['checkpoint']);assert sha(cp)==e['checkpoint_sha256'];ck=torch.load(cp,map_location='cpu',weights_only=False);reg=rd(e['registration']);validate_complete93(ck,reg);original_hash=digest(ck);base,replay_cls=classes(reg);candidate_cls=census_class(base)
 kwargs=dict(dimension=reg['violation_critic_amendment']['binding']['action_dimension'],direct=False,seed=ck['seed'],device=e['device'],algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True)
 learner=candidate_cls(B/'runtime/source_train17_clock',**kwargs);learner.migrate_parent(ck['learner']);expected=dict(ck['learner'],**{KEY:marker()});assert digest(learner.state_dict())==digest(expected)
 replay=replay_cls(kwargs['dimension'],52,20261078);replay.load_state_dict(ck['replay']);assert digest(replay.state_dict())==digest(ck['replay']);cache=CensusCache(replay,e['device']);learner.bind_cache(cache);receipt=learner.census_receipt
 def terminal_exact():
  idx=np.flatnonzero(replay.arrays['dones'][:replay.size,0]==1);np.testing.assert_array_equal(idx,cache.terminal_indices)
  for k,v in cache.terminal.items():np.testing.assert_array_equal(v.cpu().numpy(),replay.arrays[k][idx])
  masks=replay.arrays['masks'][idx];codes=(masks.astype(np.int64)*[1,2,4,8,16]).sum(1);np.testing.assert_array_equal(cache.population.cpu().numpy(),np.bincount(codes,minlength=32))
 terminal_exact();initial_terminal=len(cache.terminal_indices);assert cache.scanned_rows_total==replay.size
 # Guard checks: each invalid input is rejected without learner updates.
 rejected=[]
 def reject(name,fn):
  try:fn()
  except ValueError:rejected.append(name)
  else:raise AssertionError('Accepted invalid '+name)
 reject('missing_estimator_marker',lambda:learner.load_state_dict(ck['learner']))
 bad=copy.deepcopy(expected);bad[KEY]['version']=2;reject('changed_estimator_marker',lambda:learner.load_state_dict(bad));del bad
 reject('double_migration',lambda:learner.migrate_parent(expected));reject('double_bind',lambda:learner.bind_cache(cache))
 learner.load_state_dict(expected);reject('unbound_update',lambda:learner.update({}));learner.bind_cache(cache)
 old=base(B/'runtime/source_train17_clock',**kwargs);reject('old_loader_marker_drop_detected',lambda:strict_restore(old,expected,digest));del old
 learner.load_state_dict(expected);learner.bind_cache(cache)
 original_size=replay.size;replay.size-=1;replay.cursor-=1;reject('truncated_cache',cache.refresh);replay.size=original_size;replay.cursor=original_size
 oldarray=replay.arrays['dones'];replay.arrays['dones']=oldarray.view();reject('replaced_storage',cache.refresh);replay.arrays['dones']=oldarray
 rowid=int(cache.terminal_indices[-1]);row={k:v[rowid].copy() for k,v in replay.arrays.items() if k!='masks'};badrow=dict(row,dones=np.array([.5],np.float32));before=digest(replay.rng.bit_generator.state);reject('nonbinary_append_done',lambda:cache.add(**badrow));assert digest(replay.rng.bit_generator.state)==before and replay.size==original_size
 # Direct numerical check at exact native initial batch: independent NumPy weights,
 # same float32 sum order, every critic gradient checked against reference.
 saved_rng=capture_rng(learner);saved_rr=copy.deepcopy(replay.rng.bit_generator.state);batch=cache.sample(65536);data=types.SimpleNamespace(**batch);agent=learner.learner.agent
 with torch.no_grad():
  pair=np.random.choice(5,2,replace=False);act,lp=agent.get_action_and_log_prob(observation=data.next_observations);g=learner.learner.train.__func__.__globals__;a=agent.get_q_value(state=data.next_observations,action=act,q_net=pair[0],target=True);b=agent.get_q_value(state=data.next_observations,action=act,q_net=pair[1],target=True);q=g['_project_q'](g['_reduce_pair'](a,b,g['_mean_pair']),data.next_observations,learner.learner.alpha,learner.learner.gamma,g['_log_volume'],True);target=data.rewards.flatten()+(1-data.dones.flatten())*.9995*(q-learner.learner.alpha*lp).flatten()
 qv=[agent.get_q_value(state=data.observations,action=data.actions,q_net=j,target=False).flatten() for j in range(5)];actual=losses(learner.learner,data,qv,target,cache)
 w,den,_,_=weights(cache.terminal['masks'].cpu().numpy(),data.masks.cpu().numpy(),data.dones.flatten().cpu().numpy());reference=[]
 for j in range(5):
  qterm=agent.get_q_value(state=cache.terminal['observations'],action=cache.terminal['actions'],q_net=j,target=False).flatten();nt=((qv[j]-target)**2*data.masks[:,j]*(1-data.dones.flatten())).sum()/float(den[j]);ref=nt+((qterm-cache.terminal['rewards'].flatten())**2*torch.tensor(w[:,j],dtype=torch.float32,device=learner.device)).sum();reference.append(ref)
 np.testing.assert_allclose([float(v.detach()) for v in actual],[float(v.detach()) for v in reference],rtol=2e-6,atol=1e-7)
 params=tuple(x for q in agent.ensemble for x in q.parameters());ga=torch.autograd.grad(sum(actual),params,retain_graph=True);gr=torch.autograd.grad(sum(reference),params);maxgrad=max(float((a-b).abs().max()) for a,b in zip(ga,gr));assert all(torch.allclose(a,b,rtol=2e-5,atol=2e-6) for a,b in zip(ga,gr))
 del qv,actual,reference,ga,gr,batch,data,target;restore_rng(learner,saved_rng);replay.rng.bit_generator.state=saved_rr
 # An appended historical terminal/nonterminal is a compatibility fixture, not new physics.
 ntid=int(np.flatnonzero(ck['replay']['arrays']['dones'][:,0]==0)[-1]);fixture=[rowid,ntid,rowid,ntid,ntid,rowid,ntid,rowid]
 def reset(candidate):
  cache.load_state_dict(ck['replay'])
  if candidate:
   learner.load_state_dict(expected);learner.bind_cache(cache);return learner
  control=base(B/'runtime/source_train17_clock',**kwargs);control.load_state_dict(ck['learner']);native_source(control);return control
 def run(label,candidate,restart=False):
  l=reset(candidate);records=[];rng_records=[];draws=[];start_steps=l.learner.num_gradient_steps;start_actor=digest(l.learner.agent.actor.state_dict());start_target=digest([q.state_dict() for q in l.learner.agent.ensemble_targets]);start_alpha=digest(l.learner.a_optimizer.state_dict());restart_ref=None
  for step in range(8):
   assert time.monotonic()-t<p['budget_seconds_per_method']
   rid=fixture[step];r={k:v[rid].copy() for k,v in ck['replay']['arrays'].items() if k!='masks'};cache.add(**r);terminal_exact()
   # Independently reconstruct accepted uniform draw from a copied NumPy generator.
   gen=np.random.default_rng();gen.bit_generator.state=copy.deepcopy(replay.rng.bit_generator.state)
   while True:
    idx=gen.integers(replay.size,size=65536)
    if np.all(replay.arrays['masks'][idx].sum(0)>0):break
   batch=cache.sample(65536)
   assert digest(replay.rng.bit_generator.state)==digest(gen.bit_generator.state)
   for k,v in batch.items():np.testing.assert_array_equal(v.cpu().numpy(),replay.arrays[k][idx])
   draws.append(digest(idx));metrics=l.update(batch);records.append(metrics);rng_records.append(dict(learner=digest(capture_rng(l)),replay=digest(replay.rng.bit_generator.state)))
   if step==3 and restart:
    state=l.state_dict();rs=copy.deepcopy(cache.state_dict());payload=dict(learner=state,replay=rs);f=out/'restart_fixture.pt';torch.save(payload,f);loaded=torch.load(f,map_location='cpu',weights_only=False);assert digest(loaded)==digest(payload)
    strict_restore(l,loaded['learner'],digest);cache.load_state_dict(loaded['replay']);l.bind_cache(cache);terminal_exact();restart_ref=dict(path=str(f),bytes=f.stat().st_size,sha256=sha(f));del state,rs,payload,loaded;gc.collect()
   (O/(m+'_PROGRESS.json')).write_text(json.dumps(dict(time=time.time(),arm=label,step=step+1,metrics=metrics))+'\n')
  assert l.learner.num_gradient_steps==start_steps+8
  assert digest(l.learner.agent.actor.state_dict())!=start_actor and digest([q.state_dict() for q in l.learner.agent.ensemble_targets])!=start_target and digest(l.learner.a_optimizer.state_dict())!=start_alpha
  result=dict(metrics=records,rng=rng_records,draws=draws,state=digest(l.state_dict()),replay=digest(cache.state_dict()),updates=8,terminal_count=len(cache.terminal_indices),actor_target_temperature_updated=True,restart=restart_ref)
  if not candidate:del l;gc.collect()
  return result
 results={}
 for label,candidate,restart in [('native_control',False,False),('candidate',True,False),('candidate_repeat',True,False),('candidate_restart',True,True)]:results[label]=run(label,candidate,restart)
 for key in ['metrics','rng','draws','state','replay']:
  assert results['candidate'][key]==results['candidate_repeat'][key]==results['candidate_restart'][key],key
 for key in ['rng','draws','replay']:assert results['native_control'][key]==results['candidate'][key],key
 assert results['candidate']['terminal_count']==initial_terminal+4
 # Refresh with no new terminals must not rescan the historical population.
 scans=cache.scanned_rows_total;cache.refresh();assert cache.scanned_rows_total==scans
 learner.load_state_dict(expected);cache.load_state_dict(ck['replay']);learner.bind_cache(cache);terminal_exact();assert digest(learner.state_dict())==digest(expected) and digest(replay.state_dict())==digest(ck['replay']);assert digest(ck)==original_hash and sha(cp)==e['checkpoint_sha256']
 put(out/'REVIEW.json',dict(passed=True,time=time.time(),method=m,source_receipt=receipt,negative_guards=rejected,independent_loss_and_gradient_check=True,gradient_max_abs_error=maxgrad,full_learner_Adam_RNG_migration_exact=True,original_checkpoint_unchanged=True,initial_terminal_rows=initial_terminal,arms=results,disposable_updates=32,formal_updates=0,new_physics=0,offline_weights_promoted=False,elapsed_s=time.monotonic()-t))
 print(json.dumps(dict(passed=True,method=m,updates=32,elapsed_s=time.monotonic()-t)),flush=True)
if __name__=='__main__':
 m=sys.argv[1]
 try:main(m)
 except BaseException:put(O/(m+'_FAILURE.json'),dict(time=time.time(),traceback=traceback.format_exc()));raise
