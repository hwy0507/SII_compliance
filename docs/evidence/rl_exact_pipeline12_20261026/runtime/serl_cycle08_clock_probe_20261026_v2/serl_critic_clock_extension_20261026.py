"""Auxiliary critic-only clock branch preserving all existing SERL state.

Actor input remains canonical48. A zero clock branch enters the first critic
hidden layer without resizing its original GEMM. Eight new parameter/moment
leaves are zero; every original parameter, Adam counter/moment and RNG survives.
This changes the critic architecture, not an equivalent performance patch.
"""
import copy
from functools import partial
import numpy as np

def extend(wrapper):
 import jax
 import jax.numpy as jnp
 import flax.linen as nn
 from flax import serialization
 from serl_launcher.agents.continuous.sac import SACAgent
 from serl_launcher.networks.actor_critic_nets import Policy,Critic,ensemblize
 from serl_launcher.networks.mlp import MLP
 from serl_launcher.networks.lagrange import GeqLagrangeMultiplier
 from serl_launcher.common.common import default_init
 class Canonical48(nn.Module):
  @nn.compact
  def __call__(self, observations, train=False, stop_gradient=True):
   if observations.shape[-1]!=49:raise ValueError('Clock replay must have49 features')
   return observations[...,:48]
 class ClockMLP(nn.Module):
  @nn.compact
  def __call__(self,x,train=False):
   if x.shape[-1]!=56:raise ValueError('Expected49 observations and7 actions')
   clock=x[...,48:49];x=jnp.concatenate([x[...,:48],x[...,49:]],axis=-1)
   # Keep the original55-input Dense and all old parameter names/shapes.
   x=nn.Dense(256,kernel_init=default_init())(x)
   clock_kernel=self.param('clock_kernel',nn.initializers.zeros,(1,256))
   x=x+clock@clock_kernel
   x=jax.nn.tanh(nn.LayerNorm()(x))
   x=nn.Dense(256,kernel_init=default_init())(x)
   return jax.nn.tanh(nn.LayerNorm()(x))
 actor=Policy(encoder=Canonical48(),network=MLP(hidden_dims=[256,256],activations=jax.nn.tanh,use_layer_norm=True,activate_final=True),action_dim=7,tanh_squash_distribution=True,std_parameterization='exp',std_min=1e-5,std_max=5,name='actor')
 critic=ensemblize(partial(Critic,encoder=None,network=ClockMLP()),10)(name='critic')
 temp=GeqLagrangeMultiplier(init_value=1e-2,constraint_shape=(),constraint_type='geq',name='temperature')
 candidate=SACAgent.create(jax.random.PRNGKey(20261026),np.zeros(49,np.float32),np.zeros(7,np.float32),actor_def=actor,critic_def=critic,temperature_def=temp,discount=.9995,backup_entropy=False,critic_ensemble_size=10,critic_subsample_size=2)
 assert candidate.config==wrapper.agent.config
 original=jax.device_get(serialization.to_state_dict(wrapper.agent.state));template=jax.device_get(serialization.to_state_dict(candidate.state));paths=[]
 def merge(old,new,path=()):
  if isinstance(old,dict):
   assert set(old).issubset(new)
   result={key:merge(value,new[key],path+(str(key),)) for key,value in old.items()}
   for key in set(new)-set(old):
    assert key=='clock_kernel' and path[-2:]==('modules_critic','network') and new[key].shape==(10,1,256) and np.all(new[key]==0)
    result[key]=new[key];paths.append('/'.join(path+(key,)))
   return result
  assert np.asarray(old).shape==np.asarray(new).shape
  return copy.deepcopy(old)
 converted=merge(original,template);assert len(paths)==8
 candidate=candidate.replace(state=jax.device_put(serialization.from_state_dict(candidate.state,converted)))
 def strip(node):
  if isinstance(node,dict):
   if 'clock_kernel' in node:assert np.all(node['clock_kernel']==0)
   return {k:strip(v) for k,v in node.items() if k!='clock_kernel'}
  return node
 from validate_serl_state_20261026 import digest
 assert digest(strip(jax.device_get(serialization.to_state_dict(candidate.state))))==digest(original)
 return candidate,dict(added_paths=paths,original_full_agent_state_recoverable_exactly=True,new_weights_and_moments_zero=True,actor_features=48,critic_observation_features=49,original_gemm_shapes_retained=True,formal_weights_promoted=False)
