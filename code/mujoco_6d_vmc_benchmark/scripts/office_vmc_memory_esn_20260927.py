"""VMC-distilled multiscale reservoir with an exact zero-load equilibrium.

The 48D public interface is retained. Encoder-estimated wrench and optional
products with existing reference-relative motion drive the reservoir. No
world-pose/fixture bias or phase pulse is permitted. Wrench history, not event
time, supplies transient memory; context alone cannot produce an action.
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
            self.absolute_inputs=bool(z['absolute_inputs']) if 'absolute_inputs' in z.files else False
            self.context_inputs=bool(z['context_inputs']) if 'context_inputs' in z.files else False
            self.position_context=bool(z['position_context']) if 'position_context' in z.files else False
            self.context_dimension=12 if self.position_context else 9
            self.context_gate_w=z['context_gate_w'].copy() if 'context_gate_w' in z.files else None
            if self.context_gate_w is not None:
                if not self.context_inputs or self.context_gate_w.shape!=(self.w.shape[0],self.context_dimension) or not np.isfinite(self.context_gate_w).all():
                    raise ValueError('Invalid context-conditioned reservoir leak')
            if self.position_context and not self.context_inputs:raise ValueError('Position context requires context inputs')
            if self.context_inputs and not self.absolute_inputs:raise ValueError('Context reservoir requires magnitude channels')
            if self.context_inputs and np.any(self.weights[-self.context_dimension:]!=0):raise ValueError('Direct context-only action is forbidden')
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
        drive=np.r_[x,np.abs(x)] if getattr(self,'absolute_inputs',False) else x
        cross=None
        if getattr(self,'context_inputs',False):
            context=np.clip(np.r_[obs[14:17]/.06,obs[26:29]/.06,obs[45:48]],-4,4)
            if getattr(self,'position_context',False):context=np.r_[context,np.clip(obs[20:23]/.08,-4,4)]
            # Derived products let the reservoir remember load conditional on
            # commanded/measured motion. They vanish when estimated load does.
            cross=np.outer(drive,context).ravel();drive=np.r_[drive,cross]
        leak=self.leak
        if getattr(self,'context_gate_w',None) is not None:
            # A fixed random contextual gate changes each neuron's memory
            # rate, not its equilibrium. With no load and zero initial state,
            # arbitrary motion context still cannot create a reservoir state.
            gate=.05+1.95/(1+np.exp(-np.clip(self.context_gate_w@context+np.log(.95),-40,40)))
            leak=np.minimum(1.,leak*gate)
        self.state+=leak*(np.tanh(self.win@drive+self.w@self.state)-self.state)
        signed=np.r_[x,self.state]
        base=np.r_[signed,np.abs(signed)]
        return np.r_[base,cross,context] if cross is not None else base

    def act(self,obs):
        features=self.features(obs)
        raw=features@self.weights
        if getattr(self,'nonlinear',False):
            scaled=features/self.feature_scale
            if getattr(self,'context_inputs',False):
                n=self.context_dimension
                context=scaled[-n:]@self.hidden_w[:,-n:].T
                load=scaled[:-n]@self.hidden_w[:,:-n].T
                hidden=np.tanh(load+context)-np.tanh(context)
            else:hidden=np.tanh(scaled@self.hidden_w.T)
            raw+=hidden@self.output_w.T
        result=np.tanh(raw)
        result[0]=np.clip(np.linalg.norm(result[1:])/np.sqrt(6),0,1) if getattr(self,'axis_separable',False) else np.clip(raw[0],0,1)
        return result*getattr(self,'output_gain',1.)
