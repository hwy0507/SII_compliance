"""Inference adapters for current 45D -> 7D MLP and ESN checkpoints."""
import json
from pathlib import Path
import numpy as np

class CurrentMLP:
    kind='mlp'
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            self.mean=z['mean'].copy();self.std=z['std'].copy();self.w0=z['0.weight'].copy();self.b0=z['0.bias'].copy();self.w1=z['2.weight'].copy();self.b1=z['2.bias'].copy();self.w2=z['4.weight'].copy();self.b2=z['4.bias'].copy()
    def reset(self):pass
    def act(self,obs):
        x=(np.asarray(obs,dtype=float)-self.mean)/self.std
        h=np.tanh(x@self.w0.T+self.b0);h=np.tanh(h@self.w1.T+self.b1);raw=h@self.w2.T+self.b2
        return np.r_[1/(1+np.exp(-np.clip(raw[0],-60,60))),np.tanh(raw[1:])]

class CurrentESN:
    kind='esn'
    def __init__(self,path):
        try:from esn128_action7_20260918 import ESN128Action7
        except ModuleNotFoundError:from .esn128_action7_20260918 import ESN128Action7
        self.obj=ESN128Action7.load(path)
    def reset(self):self.obj.reset()
    def act(self,obs):return self.obj.act(obs)

class Proprio48ESN:
    kind='esn'
    def __init__(self,path):
        try:from esn128_proprio48_action7_20260921 import ESN128Proprio48Action7
        except ModuleNotFoundError:from .esn128_proprio48_action7_20260921 import ESN128Proprio48Action7
        self.obj=ESN128Proprio48Action7.load(path)
    def reset(self):self.obj.reset()
    def act(self,obs):return self.obj.act(obs)

class LinearESN:
    kind='esn_linear'
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            self.mean=z['mean'].copy();self.std=z['std'].copy();self.win=z['win'].copy()
            self.w=z['w'].copy();self.leak=z['leak'].copy();self.weights=z['weights'].copy()
        self.reset()
    def reset(self):self.state=np.zeros(128)
    def act(self,obs):
        x=np.clip((np.asarray(obs,dtype=float)-self.mean)/self.std,-12,12)
        self.state+=self.leak*(np.tanh(self.win@np.r_[1.,x]+self.w@self.state)-self.state)
        raw=np.r_[x,self.state,1.]@self.weights
        result=np.tanh(raw);result[0]=1/(1+np.exp(-np.clip(raw[0],-60,60)))
        return result

def load_current(path):
    path=Path(path)
    with np.load(path,allow_pickle=False) as z: contract=str(z['contract'])
    if contract=='current_four_scene_action7_mlp_v1':return CurrentMLP(path)
    if contract=='proprio48_action7_mlp_v1':return CurrentMLP(path)
    if contract=='four_scene_contact45_action7_v1':return CurrentESN(path)
    if contract=='proprio48_esn128_action7_v1':return Proprio48ESN(path)
    if contract=='linear_esn_action7_v1':return LinearESN(path)
    if contract=='proprio48_linear_esn_action7_v1':return LinearESN(path)
    raise ValueError(f'Unsupported current checkpoint contract: {contract}')
