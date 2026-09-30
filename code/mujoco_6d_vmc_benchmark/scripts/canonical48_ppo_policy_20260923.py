"""Frozen SB3 PPO inference: canonical proprio48 -> bounded action7 only."""
from pathlib import Path
import gymnasium as gym
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv,VecNormalize


class _SpacesOnlyEnv(gym.Env):
    """Supplies normalization metadata; must never create or step physics."""
    observation_space=gym.spaces.Box(-np.inf,np.inf,shape=(48,),dtype=np.float32)
    action_space=gym.spaces.Box(np.array([0.,-1.,-1.,-1.,-1.,-1.,-1.],dtype=np.float32),
        np.ones(7,dtype=np.float32),dtype=np.float32)
    def reset(self,*args,**kwargs):raise RuntimeError('Inference adapter has no simulator/reset')
    def step(self,*args,**kwargs):raise RuntimeError('Inference adapter has no simulator/step')


class Canonical48PPO:
    kind='ppo_direct_action7'

    def __init__(self,checkpoint,normalizer):
        torch.set_num_threads(1)
        self.checkpoint=Path(checkpoint).resolve()
        self.normalizer_path=Path(normalizer).resolve()
        self.model=PPO.load(self.checkpoint,device='cpu')
        if self.model.observation_space.shape!=(48,) or self.model.action_space.shape!=(7,):
            raise ValueError('PPO checkpoint must implement48->7')
        expected=_SpacesOnlyEnv.action_space
        if not (np.array_equal(self.model.action_space.low,expected.low)
                and np.array_equal(self.model.action_space.high,expected.high)):
            raise ValueError('Incorrect slowdown/yield action limits')
        self.normalizer=VecNormalize.load(self.normalizer_path,DummyVecEnv([_SpacesOnlyEnv]))
        if self.normalizer.observation_space.shape!=(48,) or not self.normalizer.norm_obs:
            raise ValueError('Expected train-fitted48D VecNormalize')
        self.normalizer.training=False
        self.normalizer.norm_reward=False

    def reset(self):
        pass  # feedforward; normalizer remains frozen

    def act(self,observation):
        # Gym training and pilot evaluation cast the actor boundary tofloat32
        # before VecNormalize. Preserve that order before mean/variance/clip.
        observation=np.asarray(observation,dtype=np.float32)
        if observation.shape!=(48,) or not np.isfinite(observation).all():
            raise ValueError('Expected finite canonical48 observation')
        normalized=self.normalizer.normalize_obs(observation[None])[0]
        action,_=self.model.predict(normalized,deterministic=True)
        action=np.asarray(action,dtype=np.float32)
        if action.shape!=(7,) or not np.isfinite(action).all():
            raise ValueError('PPO returned invalid action')
        if np.any(action<self.model.action_space.low) or np.any(action>self.model.action_space.high):
            raise ValueError('PPO returned action outside trained Box')
        return action

    def close(self):
        self.normalizer.close()
