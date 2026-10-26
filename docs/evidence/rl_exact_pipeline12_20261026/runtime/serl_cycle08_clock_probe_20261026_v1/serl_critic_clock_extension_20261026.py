"""Auxiliary critic-only clock extension preserving all existing SERL state.

Actor input remains canonical48; only eight critic kernel/moment arrays gain
one zero row. Original weights, Adam moments/counters, target and RNG survive.
This changes the critic architecture, not an equivalent performance patch.
"""
import copy
from functools import partial
import numpy as np

def extend(wrapper):
 import jax
 import flax.linen as nn
 from flax import serialization
 from serl_launcher.agents.continuous.sac import SACAgent
 from serl_launcher.networks.actor_critic_nets import Policy,Critic,ensemblize
 from serl_launcher.networks.mlp import MLP
 from serl_launcher.networks.lagrange import GeqLagrangeMultiplier
 class Canonical48(nn.Module):
  @nn.compact
  def __call__(self, observations, train=False, stop_gradient=True):
   if observations.shape[-1]!=49:raise ValueError('Clock replay must have49 features')
   return observations[...,:48]
 actor=Policy(encoder=Canonical48(),network=MLP(hidden_dims=[256,256],activations=jax.nn.tanh,use_layer_norm=True,activate_final=True),action_dim=7,tanh_squash_distribution=True,std_parameterization='exp',std_min=1e-5,std_max=5,name='actor')
 critic=ensemblize(partial(Critic,encoder=None,network=MLP(hidden_dims=[256,256],activations=jax.nn.tanh,use_layer_norm=True,activate_final=True)),10)(name='critic')
 temp=GeqLagrangeMultiplier(init_value=1e-2,constraint_shape=(),constraint_type='geq',name='temperature')
 candidate=SACAgent.create(jax.random.PRNGKey(20261026),np.zeros(49,np.float32),np.zeros(7,np.float32),actor_def=actor,critic_def=critic,temperature_def=temp,discount=.9995,backup_entropy=False,critic_ensemble_size=10,critic_subsample_size=2)
 assert candidate.config==wrapper.agent.config
 original=jax.device_get(serialization.to_state_dict(wrapper.agent.state));converted=copy.deepcopy(original);paths=[]
 def pad(node,path=()):
  if isinstance(node,dict):
   for key,value in node.items():node[key]=pad(value,path+(str(key),))
  elif hasattr(node,'shape') and node.shape==(10,55,256):
   assert path[-4:]==('modules_critic','network','Dense_0','kernel')
   paths.append('/'.join(path));new=np.concatenate([node[:,:48],np.zeros((10,1,256),node.dtype),node[:,48:]],axis=1)
   assert np.array_equal(np.concatenate([new[:,:48],new[:,49:]],axis=1),node)
   return new
  return node
 converted=pad(converted);assert len(paths)==8
 candidate=candidate.replace(state=jax.device_put(serialization.from_state_dict(candidate.state,converted)))
 def unpad(node):
  if isinstance(node,dict):return {k:unpad(v) for k,v in node.items()}
  if hasattr(node,'shape') and node.shape==(10,56,256):
   assert np.all(node[:,48]==0)
   return np.concatenate([node[:,:48],node[:,49:]],axis=1)
  return node
 from validate_serl_state_20261026 import digest
 assert digest(unpad(jax.device_get(serialization.to_state_dict(candidate.state))))==digest(original)
 return candidate,dict(padded_paths=paths,original_full_agent_state_recoverable_exactly=True,new_weights_and_moments_zero=True,actor_features=48,critic_observation_features=49,formal_weights_promoted=False)
