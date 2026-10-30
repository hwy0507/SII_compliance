"""Finite complete89 bit migration, original inverse, replay and native-update checks."""
from pathlib import Path
import os,sys,time,json,copy,gc,traceback,io,hashlib
D=Path(__file__).resolve().parent;B=D.parents[1]
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.sched_setaffinity(0,{12})
plan=json.loads((D/'PLAN.json').read_text());sys.path[:0]=[str(D),plan['restore_runtime'],str(B/'runtime/source_train17_clock/source/tools')]
import numpy as np
import torch
from published_compliance_learner_20261025 import PublishedLearner,OBSERVATION_SCALE
from published_pair_reduction_learner_20261026 import pair_class
from parameter_replay_capacity4m_20261027 import replay_class
from train_published_compliance_20261025 import Replay
from validate_published_finite_check_20261025 import digest
from persisted_history_critic import KEY as HISTORY_KEY,history_class,feature
from persisted_violation_critic import KEY,sha,bit,marker,violation_class,violation_replay_class,validate_observations
read=lambda p:json.loads(Path(p).read_text())
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
torch.set_num_threads(1);start=time.monotonic()
for n,h in plan['sources'].items():assert sha(D/n)==h
for n,h in plan['restore_sources'].items():assert sha(Path(plan['restore_runtime'])/n)==h
for x in plan['inputs']:assert sha(x['path'])==x['sha256']
def inverse(state):
 s=copy.deepcopy(state);s.pop(KEY)
 for k,v in list(s['agent'].items()):
  if k.startswith(('ensemble.','ensemble_targets.')) and k.endswith('.q_net.0.weight'):
   assert torch.count_nonzero(v[:,51])==0;s['agent'][k]=torch.cat((v[:,:51],v[:,52:]),1)
 for vals in s['q_optimizer']['state'].values():
  for k,v in list(vals.items()):
   if torch.is_tensor(v) and v.ndim==2 and v.shape[1] in (57,59):
    assert torch.count_nonzero(v[:,51])==0;vals[k]=torch.cat((v[:,:51],v[:,52:]),1)
 return s
def reject(fn,label,items):
 try:fn()
 except (ValueError,KeyError,RuntimeError,IndexError) as e:items.append(dict(case=label,error=str(e)))
 else:raise AssertionError('Accepted invalid '+label)
def make(cls,dim):return cls(B/'runtime/source_train17_clock',dimension=dim,direct=False,seed=20261025,device='cuda:1',algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True)
def fixture(dim,reduction):
 method='impedance' if dim==5 else 'admittance';hb=dict(method=method,checkpoint_sha256='0'*64,learner_digest='1'*64,replay_digest='2'*64,sidecar_sha256='3'*64,rows=256,action_dimension=dim)
 HC=history_class(pair_class(PublishedLearner,reduction),hb);old=make(HC,dim);old.load_state_dict(old.state_dict());rng=np.random.default_rng(420+dim)
 batch=dict(observations=rng.normal(0,.1,(256,51)).astype('f'),next_observations=rng.normal(0,.1,(256,51)).astype('f'),actions=rng.normal(0,.1,(256,dim)).astype('f'),rewards=rng.normal(0,.1,(256,1)).astype('f'),dones=(np.arange(256)%13==0).astype('f')[:,None],masks=np.ones((256,5),'f'))
 batch['observations'][:,49]=.9;batch['next_observations'][:,49]=.8
 for name in ('observations','next_observations'):batch[name][:,50]=np.linspace(0,.8,256,dtype='f')
 for _ in range(2):old.update(batch)
 state=old.state_dict();binding=dict(method=method,checkpoint_sha256='4'*64,learner_digest=digest(state),replay_digest='5'*64,sidecar_sha256='6'*64,bits_sha256='7'*64,rows=256,action_dimension=dim,history_binding=hb)
 new=make(violation_class(HC,binding),dim);new.migrate_parent(state);assert digest(inverse(new.state_dict()))==digest(state)
 bs={k:(np.column_stack((v,(v[:,50]>.5).astype('f'))) if k in ('observations','next_observations') else v) for k,v in batch.items()};initial=new.state_dict();metrics=[]
 for _ in range(2):metrics.append(new.update(bs))
 expected=new.state_dict();saved=io.BytesIO();torch.save(initial,saved);saved.seek(0);new.load_state_dict(torch.load(saved,weights_only=False))
 for i in range(2):assert new.update(bs)==metrics[i]
 assert digest(new.state_dict())==digest(expected) and any(torch.count_nonzero(q.q_net[0].weight[:,51])>0 for q in new.learner.agent.ensemble)
 online=list(new.learner.agent.ensemble.parameters());targets=list(new.learner.agent.ensemble_targets.parameters())
 with torch.no_grad():online[0][:,51].add_(.25)
 expected_target=[t.detach().clone().mul_(1-new.learner.polyak_factor).add_(p,alpha=new.learner.polyak_factor) for p,t in zip(online,targets)];new.learner.update_target_networks();assert all(torch.equal(t,e) for t,e in zip(targets,expected_target))
 obs=torch.as_tensor(bs['observations'],device=new.device);alt=obs.clone();alt[:,49:]=.123
 with torch.no_grad():assert digest(new.learner.agent.actor(obs))==digest(new.learner.agent.actor(alt))
 return dict(dimension=dim,native_calls=6,repeat_updates_exact=True,nonzero_bit_gradient=True,target_rebinding_exact=True,actor49_isolation_exact=True)
try:
 fixtures=[fixture(5,'minimum'),fixture(7,'mean')];put(D/'FIXTURE_REVIEW.json',dict(passed=True,fixtures=fixtures,random_fixture_updates=12,physics=0));gc.collect();torch.cuda.empty_cache()
 history=read(B/'runs/history89_raw_history_extension_20261030_v1/REVIEW.json');results={}
 for method,meta in history['methods'].items():
  assert time.monotonic()-start<plan['budget_seconds'];cp=Path(meta['checkpoint89']['path']);assert sha(cp)==meta['checkpoint89']['sha256'];ck=torch.load(cp,map_location='cpu',weights_only=False);assert ck['cycle']==89 and ck['boundary']=='complete_condition_cycle';state=ck['learner'];rs=ck['replay'];dim=rs['arrays']['actions'].shape[1];hb=state[HISTORY_KEY]['parent'];assert rs[HISTORY_KEY]==state[HISTORY_KEY]
  binding=dict(method=method,checkpoint_sha256=sha(cp),learner_digest=digest(state),replay_digest=digest(rs),sidecar_sha256=meta['sidecar']['sha256'],bits_sha256=meta['bits']['sha256'],rows=rs['size'],action_dimension=dim,history_binding=hb);put(D/(method+'_BINDING.json'),binding)
  HC=history_class(pair_class(PublishedLearner,'minimum' if method=='impedance' else 'mean'),hb);old=make(HC,dim);old.load_state_dict(state);assert digest(old.state_dict())==binding['learner_digest']
  new=make(violation_class(HC,binding),dim);new.migrate_parent(state);initial=new.state_dict();assert digest(inverse(initial))==binding['learner_digest']
  samples=np.unique(np.r_[np.linspace(0,rs['size']-1,4096,dtype=int),np.flatnonzero(rs['arrays']['dones'][:,0]==1)]);peaks=np.load(meta['sidecar']['path'],mmap_mode='r');obs=torch.as_tensor(rs['arrays']['observations'][samples],device=new.device);act=torch.as_tensor(rs['arrays']['actions'][samples],device=new.device);obs1=torch.cat((obs,torch.as_tensor(bit(peaks[samples,0])[:,None],device=new.device)),1);errors={}
  with torch.no_grad():
   for name in ('ensemble','ensemble_targets'):
    q0=torch.stack([q(obs,act) for q in getattr(old.learner.agent,name)]);q1=torch.stack([q(obs1,act) for q in getattr(new.learner.agent,name)]);errors[name]=float((q0-q1).abs().max());assert errors[name]<=plan['initial_q_atol']
  raws=[rs['arrays']['observations'][int(i),:48]*OBSERVATION_SCALE for i in samples[:4]];outputs=[]
  for learner,st in [(old,state),(new,initial)]:
   learner.load_state_dict(st);out=[]
   for stream in (0,3):learner.reset_episode(stream)
   for j in range(4):
    for stream in (0,3):
     learner.consume_interval(None if j==0 else dict(external_penetration_peak_m=j*.0001),stream)
     o,a,m,c=learner.act(raws[j],step=ck['steps']+j,stream=stream);out.append((o[:51],a,m,c))
   outputs.append(out)
  assert digest(outputs[0])==digest(outputs[1]);assert digest(inverse(new.state_dict()))==digest(old.state_dict())
  bads=[];reject(lambda:new.load_state_dict(state),'unmarked history51 load',bads)
  bad=copy.deepcopy(initial);bad[KEY]['bit_index']=50;reject(lambda:new.load_state_dict(bad),'changed bit index',bads)
  bad=copy.deepcopy(state);bad['num_gradient_steps']+=1;reject(lambda:new.migrate_parent(bad),'wrong learner parent',bads)
  reject(lambda:new.consume_interval(None,0),'missing interval',bads);reject(lambda:new.observation(raws[0],stream=0),'unconsumed interval',bads);reject(lambda:new.consume_interval(dict(external_penetration_peak_m=.0001),0),'decreasing peak',bads)
  new.consume_interval(dict(external_penetration_peak_m=.0004),0);terminal=new.terminal_observation(np.r_[outputs[1][-2][0],np.float32(1)],0);assert terminal[51]==1 and terminal[50]==feature(.0004) and terminal[49]==np.float32((1375-4)/1375)
  reject(lambda:new.consume_interval(dict(external_penetration_peak_m=.0004),0),'duplicate interval',bads)
  for val in (-1.,float('nan'),float('inf')):reject(lambda val=val:bit(val),'invalid peak '+str(val),bads)
  assert bit(.0002)==0 and bit(np.nextafter(np.float64(.0002),np.inf))==1
  for val in (0,1):validate_observations(np.r_[np.zeros(50),.5,val])
  for h,b in ((.4,1),(.6,0),(.5,.2)):
   reject(lambda h=h,b=b:validate_observations(np.r_[np.zeros(50),h,b]),'inconsistent history/bit',bads)
  new.load_state_dict(initial);assert new.history_peaks=={0:0.} and new.history_intervals=={0:0} and new.episode_actions=={0:0};assert digest(new.state_dict())==digest(initial)
  snapshot=D/(method+'_migrated_learner.pt');torch.save(initial,snapshot);new.load_state_dict(torch.load(snapshot,map_location='cpu',weights_only=False));assert digest(new.state_dict())==digest(initial)
  BR=violation_replay_class(replay_class(Replay),binding);rp=BR(dim,52,20261090);rp.migrate_parent(rs,meta['sidecar']['path'],meta['bits']['path']);migrated=rp.state_dict();original={k:v for k,v in migrated.items() if k!=KEY};original['arrays']={k:(v[:,:51] if k in ('observations','next_observations') else v) for k,v in migrated['arrays'].items()};assert digest(original)==binding['replay_digest']
  for col,name in enumerate(('observations','next_observations')):np.testing.assert_array_equal(migrated['arrays'][name][:,51],bit(peaks[:,col]))
  expected_rng=np.random.default_rng();expected_rng.bit_generator.state=copy.deepcopy(rs['rng'])
  while True:
   index=expected_rng.integers(rs['size'],size=65536)
   if np.all(rs['arrays']['masks'][index].sum(0)>0):break
  sample=rp.sample(65536)
  for k,v in sample.items():np.testing.assert_array_equal(v[:,:51] if k in ('observations','next_observations') else v,rs['arrays'][k][index])
  for col,name in enumerate(('observations','next_observations')):np.testing.assert_array_equal(sample[name][:,51],bit(peaks[index,col]))
  assert digest(rp.rng.bit_generator.state)==digest(expected_rng.bit_generator.state);rp.load_state_dict(migrated);assert digest(rp.state_dict())==digest(migrated)
  bad=dict(migrated);bad.pop(KEY);reject(lambda:rp.load_state_dict(bad),'unmarked replay',bads)
  bad=dict(migrated);bad.pop(HISTORY_KEY);reject(lambda:rp.load_state_dict(bad),'lost original history marker',bads)
  bad=dict(rs,size=rs['size']-1);reject(lambda:rp.migrate_parent(bad,meta['sidecar']['path'],meta['bits']['path']),'wrong replay parent',bads)
  reject(lambda:rp.migrate_parent(rs,D/'PLAN.json',meta['bits']['path']),'wrong raw sidecar',bads);reject(lambda:rp.migrate_parent(rs,meta['sidecar']['path'],D/'PLAN.json'),'wrong bits sidecar',bads);reject(lambda:BR(dim,51,0),'wrong replay width',bads)
  assert digest(state)==binding['learner_digest'] and digest(rs)==binding['replay_digest'] and sha(cp)==binding['checkpoint_sha256']
  result=dict(passed=True,binding=binding,initial_q_max_errors=errors,prediction_rows=len(samples),old_full_learner_inverse_exact=True,new_weight_moment_zero=True,actor_native_actions_context_rng_exact=True,all_old_replay_fields_exact=True,all_added_raw_bit_features_exact=True,next65536_sample_and_rng_exact=True,learner_serialization_roundtrip_exact=True,replay_roundtrip_exact=True,all_streams_reset=True,negative_rejections=bads,terminal_clock_history_bit_exact=True,original_checkpoint_unchanged=True,migrated_learner_snapshot=dict(path=str(snapshot),sha256=sha(snapshot)),actual_parent_optimizer_updates=0,new_physics=0)
  put(D/(method+'_REVIEW.json'),result);results[method]=result;print('PASSED',method,'rows',rs['size'],'rejects',len(bads),flush=True)
  del ck,state,rs,old,new,rp,migrated,original,initial,obs,obs1,act,peaks,sample;gc.collect();torch.cuda.empty_cache()
 put(D/'REVIEW.json',dict(passed=True,elapsed_s=time.monotonic()-start,methods=results,fixtures=fixtures,all_full89_migrations_passed=True,finite_online_registration=False,training90=False,new_physics=0,actual_parent_optimizer_updates=0,limits='Initial migration/native fixture checks only; full serialized replay GPU-cache and complete1375-step frozen consumer interfaces remain to verify before training90.'))
except BaseException as e:put(D/('FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(e),traceback=traceback.format_exc(),elapsed_s=time.monotonic()-start));raise
