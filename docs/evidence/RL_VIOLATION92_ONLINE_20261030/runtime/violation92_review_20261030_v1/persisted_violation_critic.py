"""Second causal critic amendment: preserve history51 and append raw violation bit.

Actor input remains49. Original history marker remains intact; this marker binds
exact complete89 state/raw history and explicitly records52-dimensional replay.
"""
import copy,types
import numpy as np
import torch
from torch import nn
from persisted_history_critic import KEY as HISTORY_KEY, marker as history_marker
from persisted_history_critic import actor_without_clock_or_history, project_with_history, sha
KEY='causal_external_penetration_violation_bit'

def bit(peak):
 value=np.asarray(peak,dtype=np.float64)
 if not np.isfinite(value).all() or np.any(value<0):raise ValueError('Finite nonnegative raw history required')
 return (value>0.0002).astype(np.float32)

def marker(binding):
 required={'method','checkpoint_sha256','learner_digest','replay_digest','sidecar_sha256','bits_sha256','rows','action_dimension','history_binding'}
 if set(binding)!=required or binding['method'] not in ('impedance','admittance','vmc'):raise ValueError('Exact complete89 binding required')
 for name in ('checkpoint_sha256','learner_digest','replay_digest','sidecar_sha256','bits_sha256'):
  value=binding[name]
  if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise ValueError('Invalid hash binding')
 if type(binding['rows']) is not int or not 0<binding['rows']<=4_000_000 or binding['action_dimension'] not in (5,7):raise ValueError('Invalid shape binding')
 old=history_marker(binding['history_binding'])
 if old['parent']['method']!=binding['method'] or old['parent']['action_dimension']!=binding['action_dimension']:raise ValueError('Original history binding mismatch')
 return dict(version=1,parent=copy.deepcopy(binding),observation_dimension=52,actor_dimension=49,clock_index=49,history_index=50,bit_index=51,feature='float(raw_preaction_cumulative_external_penetration_m >0.0002)',threshold_m=0.0002,new_weight_and_adam_moments='zero',old_fields='exact',original_history_marker_preserved=True,boundary='reset_all_streams_environment_not_restored')

def insert_zero(t):
 if t.ndim!=2 or t.shape[1] not in (56,58):raise ValueError('Expected history51 critic weight or moment')
 return torch.cat((t[:,:51],t.new_zeros((t.shape[0],1)),t[:,51:]),1)

def actor_without_critic_features(module,args):
 (value,)=args
 if value.shape[-1]!=52:raise ValueError('Bit learner actor entry requires52')
 return (value[...,:49],)

def project_with_bit(q,observation,alpha,gamma,log_volume,enabled=True):
 if observation.shape[-1]!=52:raise ValueError('Bit projection requires52')
 return project_with_history(q,observation[...,:51],alpha,gamma,log_volume,enabled)

def install_projection(wrapper):
 current=wrapper.learner.train.__func__
 if current.__globals__.get('_project_q') is not project_with_history:raise ValueError('Expected original history projection')
 adapted=types.FunctionType(current.__code__,dict(current.__globals__,_project_q=project_with_bit),current.__name__,current.__defaults__,current.__closure__)
 wrapper.learner.train=types.MethodType(adapted,wrapper.learner)

class PreservedHistoryLinear(nn.Linear):
 """Keep original history51 dot-product layout and add the bit contribution.

 A dense inserted zero column changed one-row CUDA reductions enough to perturb
 CHEQ uncertainty. This layout retains exact old inference at zero initialization.
 It represents the same real-arithmetic52-dimensional affine map; floating-point
 reductions after bit learning differ from the earlier dense offline diagnostic.
 """
 def forward(self,value):
  old_input=torch.cat((value[...,:51],value[...,52:]),dim=-1)
  old_weight=torch.cat((self.weight[:,:51],self.weight[:,52:]),dim=1)
  original=torch.nn.functional.linear(old_input,old_weight,self.bias)
  contribution=value[...,51:52]*self.weight[:,51]
  return original+contribution

def expand(wrapper):
 agent=wrapper.learner.agent;hooks=agent.actor._forward_pre_hooks
 if len(hooks)!=1 or next(iter(hooks.values())) is not actor_without_clock_or_history:raise ValueError('Expected original history actor isolation')
 if agent.actor.latent_pi[0].in_features!=49 or wrapper.learner.q_optimizer.state:raise ValueError('Fresh architecture before restore required')
 devices=[wrapper.device.index] if wrapper.device.type=='cuda' else []
 with torch.random.fork_rng(devices=devices):
  for ensemble in (agent.ensemble,agent.ensemble_targets):
   for q in ensemble:
    old=q.q_net[0]
    if not isinstance(old,nn.Linear) or old.in_features!=51+wrapper.spaces.action_space.shape[0]:raise ValueError('Expected history51 critic')
    new=PreservedHistoryLinear(old.in_features+1,old.out_features,bias=old.bias is not None,device=old.weight.device,dtype=old.weight.dtype)
    with torch.no_grad():
     new.weight.copy_(insert_zero(old.weight))
     if old.bias is not None:new.bias.copy_(old.bias)
    q.q_net[0]=new
 wrapper.learner.q_optimizer=torch.optim.Adam(agent.ensemble.parameters(),**wrapper.learner.q_optimizer.defaults)
 agent.ensemble_targets.requires_grad_(False);hooks.pop(next(iter(hooks)));agent.actor.register_forward_pre_hook(actor_without_critic_features);wrapper.replay_observation_dimension=52

def migrated_state(state,binding,wrapper):
 from validate_published_finite_check_20261025 import digest
 if KEY in state or state.get(HISTORY_KEY)!=history_marker(binding['history_binding']) or digest(state)!=binding['learner_digest']:raise ValueError('Only bound complete89 history learner may migrate')
 value=copy.deepcopy(state);count=0
 for name,tensor in list(value['agent'].items()):
  if name.startswith(('ensemble.','ensemble_targets.')) and name.endswith('.q_net.0.weight'):
   value['agent'][name]=insert_zero(tensor);count+=1
 if count!=10:raise ValueError('Expected five online and five target critics')
 named=list(wrapper.learner.agent.ensemble.named_parameters());opt=value['q_optimizer'];ids=[p for group in opt['param_groups'] for p in group['params']]
 if len(ids)!=len(named):raise ValueError('Optimizer parameter ordering mismatch')
 for pid,(name,param) in zip(ids,named,strict=True):
  if name.endswith('.q_net.0.weight'):
   for key,tensor in list(opt['state'].get(pid,{}).items()):
    if torch.is_tensor(tensor) and tensor.ndim!=0:
     if tensor.shape!=(param.shape[0],param.shape[1]-1):raise ValueError('Unexpected Adam moment shape')
     opt['state'][pid][key]=insert_zero(tensor)
 value[KEY]=marker(binding);return value

def violation_class(history_base,binding):
 binding=copy.deepcopy(binding);expected=marker(binding)
 class ViolationLearner(history_base):
  def __init__(self,*args,**kwargs):
   super().__init__(*args,**kwargs);expand(self)
  def observation(self,raw,stream=0):
   value=super().observation(raw,stream=stream)
   return np.r_[value,bit(self.history_peaks[stream])].astype(np.float32)
  def terminal_observation(self,previous,stream=0):
   value=np.asarray(previous,np.float32)
   if value.shape!=(52,):raise ValueError('Expected52-dimensional previous observation')
   return np.r_[super().terminal_observation(value[:51],stream=stream),bit(self.history_peaks[stream])].astype(np.float32)
  def load_state_dict(self,state):
   if state.get(KEY)!=expected:raise ValueError('Exact bit marker required')
   plain=dict(state);plain.pop(KEY);super().load_state_dict(plain);install_projection(self)
  def migrate_parent(self,state):self.load_state_dict(migrated_state(state,binding,self))
  def state_dict(self):return dict(super().state_dict(),**{KEY:copy.deepcopy(expected)})
 return ViolationLearner

def validate_observations(value):
 if value.shape[-1]!=52 or not np.isfinite(value).all():raise ValueError('Finite52-dimensional observations required')
 h=value[...,50];b=value[...,51]
 if np.any((h<0)|(h>=1)) or np.any((b!=0)&(b!=1)):raise ValueError('Invalid history/bit domain')
 # At rounded history==0.5 either bit is allowed; raw threshold remains authoritative.
 if np.any((h<.5)&(b!=0)) or np.any((h>.5)&(b!=1)):raise ValueError('Bit inconsistent with continuous history')

def violation_replay_class(base,binding):
 binding=copy.deepcopy(binding);expected=marker(binding);old_marker=history_marker(binding['history_binding'])
 class ViolationReplay(base):
  def __init__(self,dimension,observation_dim,seed,capacity=4_000_000):
   if dimension!=binding['action_dimension'] or observation_dim!=52:raise ValueError('Bound52 replay dimensions required')
   super().__init__(dimension,observation_dim,seed,capacity=capacity)
  def state_dict(self):return dict(super().state_dict(),**{HISTORY_KEY:copy.deepcopy(old_marker),KEY:copy.deepcopy(expected)})
  def load_state_dict(self,state):
   if state.get(KEY)!=expected or state.get(HISTORY_KEY)!=old_marker:raise ValueError('Both history and bit markers required')
   a=state['arrays'];validate_observations(a['observations']);validate_observations(a['next_observations'])
   if np.any(a['next_observations'][:,50:]<a['observations'][:,50:]):raise ValueError('Causal history/bit decreased within transition')
   plain=dict(state);plain.pop(KEY);plain.pop(HISTORY_KEY);super().load_state_dict(plain)
  def migrate_parent(self,state,sidecar_path,bits_path):
   from validate_published_finite_check_20261025 import digest
   if KEY in state or state.get(HISTORY_KEY)!=old_marker or digest(state)!=binding['replay_digest']:raise ValueError('Exact original history replay required')
   if sha(sidecar_path)!=binding['sidecar_sha256'] or sha(bits_path)!=binding['bits_sha256']:raise ValueError('Bound raw history and bit files required')
   raw=np.load(sidecar_path,mmap_mode='r',allow_pickle=False);bits=np.load(bits_path,mmap_mode='r',allow_pickle=False)
   if raw.shape!=(binding['rows'],2) or raw.dtype!=np.float64 or bits.shape!=raw.shape or bits.dtype!=np.uint8 or state['size']!=binding['rows']:raise ValueError('Raw history/bit shape mismatch')
   if np.any(raw[:,1]<raw[:,0]) or not np.array_equal(bits,bit(raw).astype(np.uint8)):raise ValueError('Invalid raw history/bit mapping')
   arrays=dict(state['arrays'])
   for col,name in enumerate(('observations','next_observations')):
    if arrays[name].shape!=(state['size'],51):raise ValueError('Original51 replay expected')
    from persisted_history_critic import feature
    if not np.array_equal(arrays[name][:,50],feature(raw[:,col])):raise ValueError('Original continuous history mismatch')
    arrays[name]=np.column_stack((arrays[name],bits[:,col].astype(np.float32)))
   self.load_state_dict(dict(state,arrays=arrays,**{KEY:copy.deepcopy(expected)}))
  def add(self,**row):
   for name in ('observations','next_observations'):
    value=np.asarray(row[name])
    if value.shape!=(52,):raise ValueError('One52-dimensional transition required')
    validate_observations(value)
   if np.any(np.asarray(row['next_observations'])[50:]<np.asarray(row['observations'])[50:]):raise ValueError('Online history/bit decreased')
   super().add(**row)
 return ViolationReplay
