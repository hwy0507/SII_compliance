"""VMC-distilled multiscale reservoir with an exact zero-load equilibrium.

The 48D public interface is retained. Only its six encoder-estimated wrench
channels drive this compliance reservoir. No pose/fixture bias or phase pulse
is permitted. Wrench history, not event time, supplies transient memory.
"""
import numpy as np


class OfficeVMCMemoryESN:
    kind='esn'
    contract='proprio48_office_vmc_memory_esn_v1'

    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            if str(z['contract'])!=self.contract:raise ValueError('Wrong contract')
            for key in ('win','w','leak','scale','weights'):
                setattr(self,key,z[key].copy())
            self.nonlinear=all(key in z.files for key in ('feature_scale','hidden_w','output_w'))
            self.axis_separable=bool(z['axis_separable']) if 'axis_separable' in z.files else False
            self.output_gain=float(z['output_gain']) if 'output_gain' in z.files else 1.
            if not 0<self.output_gain<=1:raise ValueError('Output gain must be in (0,1]')
            if self.nonlinear:
                for key in ('feature_scale','hidden_w','output_w'):
                    setattr(self,key,z[key].copy())
        self.reset()

    def reset(self):self.state=np.zeros(self.w.shape[0])

    def features(self,obs):
        obs=np.asarray(obs,dtype=float)
        if obs.shape!=(48,) or not np.isfinite(obs).all():raise ValueError('Expected finite proprio48')
        x=np.clip(obs[39:45]/self.scale,-12,12)
        self.state+=self.leak*(np.tanh(self.win@x+self.w@self.state)-self.state)
        signed=np.r_[x,self.state]
        return np.r_[signed,np.abs(signed)]

    def act(self,obs):
        features=self.features(obs)
        raw=features@self.weights
        if getattr(self,'nonlinear',False):
            raw+=np.tanh((features/self.feature_scale)@self.hidden_w.T)@self.output_w.T
        result=np.tanh(raw)
        result[0]=np.clip(np.linalg.norm(result[1:])/np.sqrt(6),0,1) if getattr(self,'axis_separable',False) else np.clip(raw[0],0,1)
        return result*getattr(self,'output_gain',1.)
