"""Independent saved-state inverse audit plus actual52-column device cache."""
from pathlib import Path
import os,sys,copy,json,time,hashlib,gc,traceback
D=Path(__file__).parent;B=D.parents[1];I=B/'runtime/history89_violation_interface_20261030_v2';O=B/'runs/history89_violation_interface_snapshots_20261030_v1'
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.sched_setaffinity(0,{11})
sys.path[:0]=[str(D),str(B/'runtime/history88_frozen_preparation_20261030_v1'),str(B/'runtime/source_train17_clock/source/tools')]
import numpy as np
import torch
from persisted_violation_critic import KEY,sha,violation_replay_class,bit,marker
from train_published_compliance_20261025 import Replay
from parameter_replay_capacity4m_20261027 import replay_class
from published_replay_device_cache_20261025 import DeviceReplayCache
from published_exact_pipeline_20261026 import cache_class
from validate_published_finite_check_20261025 import digest
read=lambda p:json.loads(Path(p).read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
start=time.monotonic();torch.set_num_threads(1);plan=read(D/'CACHE_PLAN.json');assert sha(__file__)==plan['sources']['check_cache_and_saved.py'];
for name,h in plan['sources'].items():assert sha(D/name)==h
for name,h in plan['restore_sources'].items():assert sha(Path(plan['restore_runtime'])/name)==h
for x in plan['inputs']:assert sha(x['path'])==x['sha256']
O.mkdir();review=read(I/'REVIEW.json');assert review['passed'];hist=read(B/'runs/history89_raw_history_extension_20261030_v1/REVIEW.json');results={}
try:
 for method in plan['methods']:
  assert time.monotonic()-start<plan['budget_seconds'];binding=read(I/(method+'_BINDING.json'));meta=hist['methods'][method];cp=Path(meta['checkpoint89']['path']);assert sha(cp)==binding['checkpoint_sha256'];old=torch.load(cp,map_location='cpu',weights_only=False);ls=torch.load(I/(method+'_migrated_learner.pt'),map_location='cpu',weights_only=False);assert ls[KEY]==marker(binding)
  # Independent inverse: remove column51 by index selection, verify every old
  # state field including all Adam moments/counters and every RNG value.
  restored=copy.deepcopy(ls);restored.pop(KEY);removed=0
  for k,t in restored['agent'].items():
   if k in old['learner']['agent'] and t.shape!=old['learner']['agent'][k].shape:
    assert k.startswith(('ensemble.','ensemble_targets.')) and k.endswith('.q_net.0.weight');assert torch.count_nonzero(t[:,51])==0
    idx=torch.tensor([i for i in range(t.shape[1]) if i!=51]);restored['agent'][k]=t.index_select(1,idx);removed+=1
  assert removed==10
  for pid,values in restored['q_optimizer']['state'].items():
   for k,t in values.items():
    parent=old['learner']['q_optimizer']['state'][pid][k]
    if torch.is_tensor(t) and t.shape!=parent.shape:
     assert t.ndim==2 and t.shape[1]==parent.shape[1]+1 and torch.count_nonzero(t[:,51])==0
     values[k]=t.index_select(1,torch.tensor([i for i in range(t.shape[1]) if i!=51]))
  assert digest(restored)==digest(old['learner'])==binding['learner_digest']
  cls=violation_replay_class(replay_class(Replay),binding);rp=cls(binding['action_dimension'],52,7);rp.migrate_parent(old['replay'],meta['sidecar']['path'],meta['bits']['path']);initial=rp.state_dict();initial_digest=digest(initial)
  inverse_replay={k:v for k,v in initial.items() if k!=KEY};inverse_replay['arrays']={k:(v[:,:51] if k in ('observations','next_observations') else v) for k,v in initial['arrays'].items()};assert digest(inverse_replay)==digest(old['replay'])==binding['replay_digest']
  snapshot=O/(method+'.pt');payload=dict(kind='interface_only_no_online_approval',learner=ls,replay=initial,parent_checkpoint=meta['checkpoint89'],parent_cycle=89,online_steps=0,optimizer_updates=0,environment_state_saved=False)
  torch.save(payload,snapshot);del payload;loaded=torch.load(snapshot,map_location='cpu',weights_only=False);assert digest(loaded['learner'])==digest(ls) and digest(loaded['replay'])==initial_digest
  rp.load_state_dict(loaded['replay']);assert digest(rp.state_dict())==initial_digest
  cache=cache_class(DeviceReplayCache)(rp,'cuda:2');assert cache.arrays['observations'].shape==(4_000_000,52)
  sampled=cache.sample(65536);sampled_rng=digest(rp.rng.bit_generator.state);rp.load_state_dict(initial);expected=rp.sample(65536);assert digest(expected)==digest(sampled) and digest(rp.rng.bit_generator.state)==sampled_rng
  # Appending one disposable synthetic row must consume precisely the original
  # Bernoulli mask draw, not change the retained prefix, and refresh GPU row.
  n=rp.size;test_rng=np.random.default_rng();test_rng.bit_generator.state=copy.deepcopy(rp.rng.bit_generator.state);expected_mask=test_rng.binomial(1,.8,5)
  row={k:np.array(v[0],copy=True) for k,v in loaded['replay']['arrays'].items() if k!='masks'};cache.add(**row)
  for k,v in rp.arrays.items():assert np.array_equal(v[n],cache.arrays[k][n].cpu().numpy())
  assert np.array_equal(rp.arrays['masks'][n],expected_mask) and digest(rp.rng.bit_generator.state)==digest(test_rng.bit_generator.state)
  assert digest({k:v[:n] for k,v in rp.arrays.items()})==digest(loaded['replay']['arrays']);cache.load_state_dict(loaded['replay']);assert digest(cache.state_dict())==initial_digest
  # First32 all masks zero forces exact-cache fallback; a small deterministic
  # sampling sequence then forces rejection and retry before a valid batch.
  class ScriptedRNG:
   def __init__(self):self.calls=0
   def integers(self,size,size_kw=None,**kw):
    count=kw.get('size',size_kw)
    self.calls+=1
    return np.zeros(count,dtype=int) if self.calls==1 else np.r_[np.zeros(32,dtype=int),np.ones(count-32,dtype=int)]
  class Fixture:
   def __init__(self):self.size=2;self.rng=None;self.arrays={'masks':np.array([[0]*5,[1]*5],dtype='f'),'observations':np.zeros((2,52),'f')}
  # Use a positional upper bound and keyword size as NumPy does.
  class Fixed:
   def __init__(self):self.calls=0
   def integers(self,high,*,size):
    self.calls+=1;return np.zeros(size,dtype=int) if self.calls==1 else np.r_[np.zeros(32,dtype=int),np.ones(size-32,dtype=int)]
  f=Fixture();f.rng=Fixed();fc=cache_class(DeviceReplayCache)(f,'cuda:2');fv=fc.sample(64);assert f.rng.calls==2 and torch.equal(fv['masks'][:32],torch.zeros((32,5),device='cuda:2')) and torch.equal(fv['masks'][32:],torch.ones((32,5),device='cuda:2'))
  # Independently scalar-check transformed histories from saved full replay.
  peaks=np.load(meta['sidecar']['path'],mmap_mode='r');indices=np.unique(np.r_[np.linspace(0,n-1,4096,dtype=int),np.flatnonzero(old['replay']['arrays']['dones'][:,0]==1)])
  for i in indices:
   for c,k in enumerate(('observations','next_observations')):
    p=float(peaks[i,c]);assert loaded['replay']['arrays'][k][i,51]==np.float32(p>0.0002)
  assert sha(cp)==binding['checkpoint_sha256'];result=dict(passed=True,rows=n,independent_inverse_all_learner_fields_exact=True,full_saved_replay_roundtrip_exact=True,actual_gpu_cache_next65536_and_rng_exact=True,synthetic_append_mask_and_gpu_row_exact=True,all_retained_prefix_rows_exact=True,cache_rejection_and_fallback_calls=2,scalar_bit_checks=2*len(indices),snapshot=dict(path=str(snapshot),sha256=sha(snapshot),bytes=snapshot.stat().st_size),snapshot_kind='interface_only_no_online_approval',new_physics=0,optimizer_updates=0,original_checkpoint_unchanged=True)
  results[method]=result;put(D/(method+'_CACHE_SAVED_REVIEW.json'),result);print('CACHE_SAVED',method,n,flush=True)
  del old,ls,restored,loaded,rp,cache,initial,inverse_replay,expected,sampled,peaks;gc.collect();torch.cuda.empty_cache()
 put(D/'CACHE_SAVED_REVIEW.json',dict(passed=True,methods=results,elapsed_s=time.monotonic()-start,new_physics=0,optimizer_updates=0))
except BaseException as e:
 put(D/('CACHE_FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(e),traceback=traceback.format_exc()));raise
