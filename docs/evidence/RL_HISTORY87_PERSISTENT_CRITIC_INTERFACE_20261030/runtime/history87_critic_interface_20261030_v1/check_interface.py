from pathlib import Path
import os,sys,time,json,copy,gc,traceback,io,hashlib
D=Path(__file__).parent;B=D.parents[1]
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
os.sched_setaffinity(0,{53})
sys.path[:0]=[str(D),str(B/'runtime/parameter86_half_std_paired_20261030_v3'),str(B/'runtime/source_train17_clock/source/tools')]
import numpy as np
import torch
from published_compliance_learner_20261025 import PublishedLearner,OBSERVATION_SCALE
from published_pair_reduction_learner_20261026 import pair_class
from parameter_replay_capacity4m_20261027 import replay_class
from train_published_compliance_20261025 import Replay
from validate_published_finite_check_20261025 import digest
from persisted_history_critic import KEY,sha,marker,feature,history_class,history_replay_class,transform_trainer
from published_exact_pipeline_20261026 import cache_class
from published_replay_device_cache_20261025 import DeviceReplayCache
read=lambda p:json.loads(Path(p).read_text())
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
torch.set_num_threads(1);start=time.monotonic();plan=read(D/'PLAN.json')
for n,h in plan['sources'].items():assert sha(D/n)==h

def inverse(state):
 s=copy.deepcopy(state);s.pop(KEY)
 for k,v in s['agent'].items():
  if k.startswith(('ensemble.','ensemble_targets.')) and k.endswith('.q_net.0.weight'):
   assert torch.count_nonzero(v[:,50])==0;s['agent'][k]=torch.cat((v[:,:50],v[:,51:]),1)
 for vals in s['q_optimizer']['state'].values():
  for k,v in vals.items():
   if torch.is_tensor(v) and v.ndim==2 and v.shape[1] in (56,58):
    assert torch.count_nonzero(v[:,50])==0;vals[k]=torch.cat((v[:,:50],v[:,51:]),1)
 return s

def reject(fn,label,items):
 try:fn()
 except (ValueError,KeyError,RuntimeError,IndexError) as e:items.append(dict(case=label,error=str(e)))
 else:raise AssertionError('Accepted invalid '+label)

def make(cls,dim,device='cuda:1'):
 return cls(B/'runtime/source_train17_clock',dimension=dim,direct=False,seed=20261025,device=device,algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True)

def fixture_checks(dim,reduction):
 base=pair_class(PublishedLearner,reduction);old=make(base,dim);s=old.state_dict();old.load_state_dict(s)
 rng=np.random.default_rng(100+dim);batch=dict(observations=rng.normal(0,.1,(256,50)).astype('f'),next_observations=rng.normal(0,.1,(256,50)).astype('f'),actions=rng.normal(0,.1,(256,dim)).astype('f'),rewards=rng.normal(0,.1,(256,1)).astype('f'),dones=(np.arange(256)%13==0).astype('f')[:,None],masks=np.ones((256,5),'f'))
 batch['observations'][:,49]=.9;batch['next_observations'][:,49]=.8
 # Populate real upstream Adam state, both cadence phases and alpha.
 for _ in range(2):old.update(batch)
 s=old.state_dict();binding=dict(method='impedance' if dim==5 else 'admittance',checkpoint_sha256='0'*64,learner_digest=digest(s),replay_digest='1'*64,sidecar_sha256='2'*64,rows=256,action_dimension=dim)
 cls=history_class(base,binding);new=make(cls,dim);new.migrate_parent(s);assert digest(inverse(new.state_dict()))==digest(s)
 bs={k:(np.column_stack((v,np.linspace(0,.7,256,dtype='f'))) if k in ('observations','next_observations') else v) for k,v in batch.items()}
 initial=new.state_dict();metrics=[]
 for _ in range(2):metrics.append(new.update(bs))
 expected=new.state_dict();saved=io.BytesIO();torch.save(initial,saved);saved.seek(0);new.load_state_dict(torch.load(saved,weights_only=False))
 for i in range(2):assert new.update(bs)==metrics[i]
 assert digest(new.state_dict())==digest(expected)
 assert any(torch.count_nonzero(q.q_net[0].weight[:,50])>0 for q in new.learner.agent.ensemble)
 # Exercise actual target object references after two restores.
 online=list(new.learner.agent.ensemble.parameters());target=list(new.learner.agent.ensemble_targets.parameters())
 with torch.no_grad():online[0][:,50].add_(.25)
 expected_target=[t.detach().clone().mul_(1-new.learner.polyak_factor).add_(p,alpha=new.learner.polyak_factor) for p,t in zip(online,target)]
 new.learner.update_target_networks()
 assert all(torch.equal(t,e) for t,e in zip(target,expected_target))
 # Actor excludes clock/history even after new critic weights become nonzero.
 obs=torch.as_tensor(bs['observations'],device=new.device);alt=obs.clone();alt[:,49:]=.123
 with torch.no_grad():
  a=new.learner.agent.actor(obs);b=new.learner.agent.actor(alt)
  assert digest(a)==digest(b)
 return dict(dimension=dim,native_calls=6,repeat_updates_exact=True,nonzero_history_gradient=True,target_rebinding_exact=True,actor_isolation_exact=True)

try:
 fixtures=[fixture_checks(5,'minimum'),fixture_checks(7,'mean')];put(D/'FIXTURE_REVIEW.json',dict(passed=True,fixtures=fixtures,random_fixture_updates=12,physics=0));gc.collect();torch.cuda.empty_cache()
 hist=read(B/'runs/recovery87_history_extension_20261030_v1/REVIEW.json');results={}
 for method in plan['methods']:
  assert time.monotonic()-start<plan['budget_seconds'];meta=hist['methods'][method];cp=Path(meta['checkpoint87']['path']);assert sha(cp)==meta['checkpoint87']['sha256'];ck=torch.load(cp,map_location='cpu',weights_only=False);assert ck['cycle']==87 and ck['boundary']=='complete_condition_cycle';state=ck['learner'];rs=ck['replay'];dim=rs['arrays']['actions'].shape[1]
  binding=dict(method=method,checkpoint_sha256=sha(cp),learner_digest=digest(state),replay_digest=digest(rs),sidecar_sha256=meta['sidecar']['sha256'],rows=rs['size'],action_dimension=dim);put(D/(method+'_BINDING.json'),binding)
  base=pair_class(PublishedLearner,'minimum' if method=='impedance' else 'mean');old=make(base,dim);old.load_state_dict(state);assert digest(old.state_dict())==binding['learner_digest']
  cls=history_class(base,binding);new=make(cls,dim);new.migrate_parent(state);initial=new.state_dict();assert digest(inverse(initial))==binding['learner_digest']
  samples=np.unique(np.r_[np.linspace(0,rs['size']-1,4096,dtype=int),np.flatnonzero(rs['arrays']['dones'][:,0]==1)]);peaks=np.load(meta['sidecar']['path'],mmap_mode='r');obs=torch.as_tensor(rs['arrays']['observations'][samples],device=new.device);act=torch.as_tensor(rs['arrays']['actions'][samples],device=new.device);obs1=torch.cat((obs,torch.as_tensor(feature(peaks[samples,0])[:,None],device=new.device)),1)
  errors={}
  with torch.no_grad():
   for name in ('ensemble','ensemble_targets'):
    q0=torch.stack([q(obs,act) for q in getattr(old.learner.agent,name)]);q1=torch.stack([q(obs1,act) for q in getattr(new.learner.agent,name)]);errors[name]=float((q0-q1).abs().max());assert errors[name]<=plan['initial_q_atol']
  # Native CHEQ draws/actions/mixing, including multiple episode streams.
  raws=[rs['arrays']['observations'][int(i),:48]*OBSERVATION_SCALE for i in samples[:4]]
  outputs=[]
  for learner,st in [(old,state),(new,initial)]:
   learner.load_state_dict(st);out=[]
   for stream in (0,3):learner.reset_episode(stream)
   for j in range(4):
    for stream in (0,3):
     if learner is new:learner.consume_interval(None if j==0 else dict(external_penetration_peak_m=j*.0001),stream)
     o,a,m,c=learner.act(raws[j],step=ck['steps']+j,stream=stream);out.append((o[:50],a,m,c))
   outputs.append(out)
  assert digest(outputs[0])==digest(outputs[1]);assert digest(inverse(new.state_dict()))==digest(old.state_dict())
  bads=[];reject(lambda:new.load_state_dict(state),'unmarked old load',bads)
  bad=copy.deepcopy(initial);bad[KEY]['clock_index']=50;reject(lambda:new.load_state_dict(bad),'changed clock index',bads)
  bad=copy.deepcopy(state);bad['num_gradient_steps']+=1;reject(lambda:new.migrate_parent(bad),'wrong learner parent',bads)
  reject(lambda:new.consume_interval(None,0),'missing completed interval',bads)
  reject(lambda:new.observation(raws[0],stream=0),'unconsumed interval',bads)
  reject(lambda:new.consume_interval(dict(external_penetration_peak_m=.0001),0),'decreasing peak',bads)
  new.consume_interval(dict(external_penetration_peak_m=.0004),0);terminal=new.terminal_observation(np.r_[outputs[1][-2][0],np.float32(.6)],0);assert terminal[50]==feature(.0004) and terminal[49]==np.float32((1375-4)/1375)
  reject(lambda:new.consume_interval(dict(external_penetration_peak_m=.0004),0),'duplicate interval',bads)
  for val in (-1.,float('nan'),float('inf')):reject(lambda val=val:feature(val),'invalid peak '+str(val),bads)
  new.load_state_dict(initial);assert new.history_peaks=={0:0.} and new.history_intervals=={0:0} and new.episode_actions=={0:0};assert digest(new.state_dict())==digest(initial)
  snapshot=D/(method+'_migrated_learner.pt');torch.save(initial,snapshot);new.load_state_dict(torch.load(snapshot,map_location='cpu',weights_only=False));assert digest(new.state_dict())==digest(initial)
  # Preserve every retained array, every old marker, and the next native sample.
  R4=replay_class(Replay);HR=history_replay_class(R4,binding);rp=HR(dim,51,20261078);rp.migrate_parent(rs,meta['sidecar']['path']);migrated=rp.state_dict()
  original={k:v for k,v in migrated.items() if k!=KEY};original['arrays']={k:(v[:,:50] if k in ('observations','next_observations') else v) for k,v in migrated['arrays'].items()};assert digest(original)==binding['replay_digest']
  for col,name in enumerate(('observations','next_observations')):assert np.array_equal(migrated['arrays'][name][:,50],feature(peaks[:,col]))
  expected_rng=np.random.default_rng();expected_rng.bit_generator.state=copy.deepcopy(rs['rng'])
  while True:
   index=expected_rng.integers(rs['size'],size=65536)
   if np.all(rs['arrays']['masks'][index].sum(0)>0):break
  sample=rp.sample(65536)
  for k,v in sample.items():assert np.array_equal(v[:,:50] if k in ('observations','next_observations') else v,rs['arrays'][k][index])
  for col,name in enumerate(('observations','next_observations')):assert np.array_equal(sample[name][:,50],feature(peaks[index,col]))
  assert digest(rp.rng.bit_generator.state)==digest(expected_rng.bit_generator.state)
  rp.load_state_dict(migrated);assert digest(rp.state_dict())==digest(migrated)
  bad=dict(migrated);bad.pop(KEY);reject(lambda:rp.load_state_dict(bad),'unmarked replay',bads)
  bad=dict(migrated);bad[KEY]=dict(migrated[KEY],history_index=49);reject(lambda:rp.load_state_dict(bad),'changed replay marker',bads)
  bad=dict(rs,size=rs['size']-1);reject(lambda:rp.migrate_parent(bad,meta['sidecar']['path']),'wrong replay parent',bads)
  reject(lambda:rp.migrate_parent(rs,D/'PLAN.json'),'wrong sidecar',bads)
  reject(lambda:HR(dim,50,0),'wrong replay width',bads)
  assert digest(state)==binding['learner_digest'] and digest(rs)==binding['replay_digest'] and sha(cp)==binding['checkpoint_sha256']
  result=dict(passed=True,binding=binding,initial_q_max_errors=errors,prediction_rows=len(samples),old_full_learner_inverse_exact=True,new_weight_moment_zero=True,actor_native_actions_context_rng_exact=True,all_old_replay_fields_exact=True,all_added_history_features_exact=True,next65536_sample_and_rng_exact=True,learner_serialization_roundtrip_exact=True,replay_roundtrip_exact=True,all_streams_reset=True,negative_rejections=bads,terminal_clock_history_exact=True,original_checkpoint_unchanged=True,migrated_learner_snapshot=dict(path=str(snapshot),sha256=sha(snapshot)),actual_parent_optimizer_updates=0,new_physics=0)
  put(D/(method+'_REVIEW.json'),result);results[method]=result;print('PASSED',method,'rows',rs['size'],'rejects',len(bads),flush=True)
  del ck,state,rs,old,new,rp,migrated,original,initial,obs,obs1,act,peaks,sample;gc.collect();torch.cuda.empty_cache()
 source=(B/'runs/parameter_partial75_recovery_cycle87_20261029_v1/impedance/trainer_registered.py').read_text();transformed=transform_trainer(source);assert transformed.replace("                    learner.consume_interval(event['interval'], stream=slot)\n",'')==source
 (D/'trainer_history_event_candidate.py').write_text(transformed)
 put(D/'REVIEW.json',dict(passed=True,elapsed_s=time.monotonic()-start,methods=results,fixtures=fixtures,all_full87_migrations_passed=True,trainer_single_event_seam_exact=True,finite_online_registration=False,training88=False,new_physics=0,actual_parent_optimizer_updates=0))
except BaseException as e:
 put(D/('FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(e),traceback=traceback.format_exc(),elapsed_s=time.monotonic()-start));raise
