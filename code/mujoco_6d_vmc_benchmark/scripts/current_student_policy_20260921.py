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

class LoadGatedProprio48ESN:
    """Canonical ESN residual with a causal proprioceptive recovery gate.

    The reservoir always advances.  Only the submitted residual is gated, using
    the already-audited joint-load and estimated-wrench fields in canonical48D.
    No contact identity, task stage, event clock, geometry, or simulator truth
    is available to this policy.
    """
    kind='esn'
    contract='proprio48_esn128_action7_load_gated_v1'
    dt=.04
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            required=('mean','std','win','w','leak','input_mask','alpha','output_gain',
                      'fmean','fstd','w1','b1','w2','b2','gate_load_scale',
                      'gate_wrench_scale','gate_center','gate_width',
                      'gate_attack_tau','gate_release_tau')
            missing=[key for key in required if key not in z.files]
            if missing:raise ValueError(f'Missing load-gated ESN fields: {missing}')
            for key in required:
                value=z[key].copy()
                setattr(self,key,float(value) if value.shape==() else value)
        if min(self.gate_load_scale,self.gate_wrench_scale,self.gate_width,
               self.gate_attack_tau,self.gate_release_tau)<=0:
            raise ValueError('Load-gate scales, width, and time constants must be positive')
        self.reset()
    def reset(self):
        self.state=np.zeros(128);self.previous_action=np.zeros(7);self.load_gate=0.
    def act(self,obs):
        raw=np.asarray(obs,dtype=float)
        if raw.shape!=(48,) or not np.isfinite(raw).all():raise ValueError('Expected finite proprio48 observation')
        x=np.clip((raw-self.mean)/self.std,-12,12)*self.input_mask
        self.state+=self.leak*(np.tanh(self.win@np.r_[1.,x]+self.w@self.state)-self.state)
        features=(np.r_[x,self.state]-self.fmean)/self.fstd
        hidden=np.tanh(self.w1@features+self.b1)
        logits=self.w2@hidden+self.b2
        residual=np.tanh(logits);residual[0]=1/(1+np.exp(-np.clip(logits[0],-60,60)))
        residual*=self.output_gain
        load=np.linalg.norm(raw[32:39])/self.gate_load_scale
        wrench=np.linalg.norm(raw[39:45])/self.gate_wrench_scale
        evidence=float(np.hypot(load,wrench))
        target=1/(1+np.exp(-np.clip((evidence-self.gate_center)/self.gate_width,-60,60)))
        tau=self.gate_attack_tau if target>self.load_gate else self.gate_release_tau
        self.load_gate+=(1-np.exp(-self.dt/tau))*(target-self.load_gate)
        gated=residual*self.load_gate
        self.previous_action+=self.alpha*(gated-self.previous_action)
        return self.previous_action.copy()

class QuietCenteredProprio48ESN(LoadGatedProprio48ESN):
    """High-pass the reservoir readout only while proprioceptively unloaded.

    This keeps fast/multiscale ESN transients for impacts and brushes while a
    slow quiet-state baseline removes persistent off-distribution readout bias.
    The baseline freezes under estimated load, so sustained compliance is not
    erased merely because contact lasts longer than one policy step.
    """
    contract='proprio48_esn128_action7_quiet_centered_v1'
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            if 'centering_tau' not in z.files:raise ValueError('Missing centering_tau')
            self.centering_tau=float(z['centering_tau'])
        if self.centering_tau<=0:raise ValueError('centering_tau must be positive')
        super().__init__(path)
    def reset(self):
        super().reset();self.quiet_baseline=np.zeros(7)
    def act(self,obs):
        raw=np.asarray(obs,dtype=float)
        x=np.clip((raw-self.mean)/self.std,-12,12)*self.input_mask
        self.state+=self.leak*(np.tanh(self.win@np.r_[1.,x]+self.w@self.state)-self.state)
        features=(np.r_[x,self.state]-self.fmean)/self.fstd
        hidden=np.tanh(self.w1@features+self.b1);logits=self.w2@hidden+self.b2
        residual=np.tanh(logits);residual[0]=1/(1+np.exp(-np.clip(logits[0],-60,60)))
        residual*=self.output_gain
        load=np.linalg.norm(raw[32:39])/self.gate_load_scale
        wrench=np.linalg.norm(raw[39:45])/self.gate_wrench_scale
        evidence=float(np.hypot(load,wrench))
        loaded=1/(1+np.exp(-np.clip((evidence-self.gate_center)/self.gate_width,-60,60)))
        beta=(1-np.exp(-self.dt/self.centering_tau))*(1-loaded)
        self.quiet_baseline+=beta*(residual-self.quiet_baseline)
        centered=residual-self.quiet_baseline
        centered[0]=max(0.,centered[0])
        self.previous_action+=self.alpha*(centered-self.previous_action)
        return self.previous_action.copy()

class ImpactResponseProprio48ESN:
    """Pure ESN dual readout for route tracking and proprioceptive impacts.

    Both heads share one 128-unit reservoir.  A causal qvel transient selects
    the impact head for a short leaky interval; there is no VMC action, event
    time, contact truth, ball state, or geometry input.
    """
    kind='esn'; contract='proprio48_esn128_action7_impact_response_v1'; dt=.04
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            required=('mean','std','win','w','leak','input_mask','alpha','output_gain',
                      'fmean','fstd','w1','b1','route_w2','route_b2','impact_w2',
                      'impact_b2','impact_scale','impact_center','impact_width',
                      'impact_attack_tau','impact_release_tau','impact_hold_tau')
            missing=[key for key in required if key not in z.files]
            if missing:raise ValueError(f'Missing impact-response ESN fields: {missing}')
            for key in required:
                value=z[key].copy();setattr(self,key,float(value) if value.shape==() else value)
        self.reset()
    def reset(self):
        self.state=np.zeros(128);self.previous_action=np.zeros(7);self.previous_qvel=np.zeros(7);self.impact_gate=0.
    def act(self,obs):
        raw=np.asarray(obs,dtype=float)
        if raw.shape!=(48,) or not np.isfinite(raw).all():raise ValueError('Expected finite proprio48 observation')
        qvel=raw[7:14].copy();transient=float(np.linalg.norm(qvel-self.previous_qvel));self.previous_qvel=qvel
        x=np.clip((raw-self.mean)/self.std,-12,12)*self.input_mask
        self.state+=self.leak*(np.tanh(self.win@np.r_[1.,x]+self.w@self.state)-self.state)
        features=(np.r_[x,self.state]-self.fmean)/self.fstd
        hidden=np.tanh(self.w1@features+self.b1)
        route=self.route_w2@hidden+self.route_b2;impact=self.impact_w2@hidden+self.impact_b2
        route=np.tanh(route);route[0]=1/(1+np.exp(-np.clip((self.route_w2@hidden+self.route_b2)[0],-60,60)))
        impact=np.tanh(impact);impact[0]=1/(1+np.exp(-np.clip((self.impact_w2@hidden+self.impact_b2)[0],-60,60)))
        route*=self.output_gain;impact*=self.output_gain
        target=1/(1+np.exp(-np.clip((transient/self.impact_scale-self.impact_center)/self.impact_width,-60,60)))
        tau=self.impact_attack_tau if target>self.impact_gate else self.impact_release_tau
        self.impact_gate+=(1-np.exp(-self.dt/tau))*(target-self.impact_gate)
        self.impact_gate=np.clip(self.impact_gate,0.,1.)
        result=(1-self.impact_gate)*route+self.impact_gate*impact
        self.previous_action+=self.alpha*(result-self.previous_action)
        return self.previous_action.copy()

class GatedProprio48ESN:
    """Two readout experts selected only from the frozen reservoir history."""
    kind='esn'
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            required=('mean','std','win','w','leak','input_mask','alpha','output_gain',
                      'fmean','fstd','w1','b1','yield_w2','yield_b2',
                      'clearance_w2','clearance_b2','gate_w','gate_b')
            missing=[key for key in required if key not in z.files]
            if missing:raise ValueError(f'Missing gated ESN fields: {missing}')
            for key in required:
                value=z[key].copy()
                setattr(self,key,float(value) if value.shape==() else value)
        self.reset()
    def reset(self):self.state=np.zeros(128);self.previous_action=np.zeros(7)
    def act(self,obs):
        x=np.asarray(obs,dtype=float)
        if x.shape!=(48,) or not np.isfinite(x).all():raise ValueError('Expected finite proprio48 observation')
        x=np.clip((x-self.mean)/self.std,-12,12)*self.input_mask
        self.state+=self.leak*(np.tanh(self.win@np.r_[1.,x]+self.w@self.state)-self.state)
        features=(np.r_[x,self.state]-self.fmean)/self.fstd
        hidden=np.tanh(self.w1@features+self.b1)
        gate=1/(1+np.exp(-np.clip(hidden@self.gate_w+self.gate_b,-60,60)))
        logits=(1-gate)*(self.yield_w2@hidden+self.yield_b2)+gate*(self.clearance_w2@hidden+self.clearance_b2)
        result=np.tanh(logits);result[0]=1/(1+np.exp(-np.clip(logits[0],-60,60)))
        result*=self.output_gain;self.previous_action+=self.alpha*(result-self.previous_action)
        return self.previous_action.copy()

class GatedMLPProprio48ESN:
    """Two frozen experts with a small nonlinear reservoir-state gate."""
    kind='esn'
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            required=('mean','std','win','w','leak','input_mask','alpha','output_gain',
                      'fmean','fstd','w1','b1','yield_w2','yield_b2',
                      'clearance_w2','clearance_b2','gate_w1','gate_b1','gate_w2','gate_b2')
            missing=[key for key in required if key not in z.files]
            if missing:raise ValueError(f'Missing gated MLP ESN fields: {missing}')
            for key in required:
                value=z[key].copy()
                setattr(self,key,float(value) if value.shape==() else value)
        self.reset()
    def reset(self):self.state=np.zeros(128);self.previous_action=np.zeros(7)
    def act(self,obs):
        x=np.asarray(obs,dtype=float)
        if x.shape!=(48,) or not np.isfinite(x).all():raise ValueError('Expected finite proprio48 observation')
        x=np.clip((x-self.mean)/self.std,-12,12)*self.input_mask
        self.state+=self.leak*(np.tanh(self.win@np.r_[1.,x]+self.w@self.state)-self.state)
        features=(np.r_[x,self.state]-self.fmean)/self.fstd
        hidden=np.tanh(self.w1@features+self.b1)
        gate_hidden=np.tanh(self.gate_w1@hidden+self.gate_b1)
        gate=1/(1+np.exp(-np.clip(self.gate_w2@gate_hidden+self.gate_b2,-60,60)))
        logits=(1-gate)*(self.yield_w2@hidden+self.yield_b2)+gate*(self.clearance_w2@hidden+self.clearance_b2)
        result=np.tanh(logits);result[0]=1/(1+np.exp(-np.clip(logits[0],-60,60)))
        result*=self.output_gain;self.previous_action+=self.alpha*(result-self.previous_action)
        return self.previous_action.copy()

class HierarchicalMarginProprio48ESN:
    """R15 two-expert base plus a reservoir-state margin selector."""
    kind='esn'
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            required=('mean','std','win','w','leak','input_mask','alpha','output_gain',
                      'fmean','fstd','w1','b1','base_yield_w2','base_yield_b2',
                      'base_clearance_w2','base_clearance_b2','base_gate_w1','base_gate_b1',
                      'base_gate_w2','base_gate_b2','margin_w2','margin_b2',
                      'selector_w1','selector_b1','selector_w2','selector_b2')
            missing=[key for key in required if key not in z.files]
            if missing:raise ValueError(f'Missing hierarchical ESN fields: {missing}')
            for key in required:
                value=z[key].copy()
                setattr(self,key,float(value) if value.shape==() else value)
        self.reset()
    def reset(self):
        self.state=np.zeros(128);self.previous_action=np.zeros(7)
        self.selector_positive_steps=0;self.selector_latched=False
        self.selector_pulse_remaining=0;self.selector_pulse_used=False
    def act(self,obs):
        x=np.asarray(obs,dtype=float)
        if x.shape!=(48,) or not np.isfinite(x).all():raise ValueError('Expected finite proprio48 observation')
        x=np.clip((x-self.mean)/self.std,-12,12)*self.input_mask
        self.state+=self.leak*(np.tanh(self.win@np.r_[1.,x]+self.w@self.state)-self.state)
        features=(np.r_[x,self.state]-self.fmean)/self.fstd
        hidden=np.tanh(self.w1@features+self.b1)
        base_gate_hidden=np.tanh(self.base_gate_w1@hidden+self.base_gate_b1)
        base_gate=1/(1+np.exp(-np.clip(self.base_gate_w2@base_gate_hidden+self.base_gate_b2,-60,60)))
        base_logits=(1-base_gate)*(self.base_yield_w2@hidden+self.base_yield_b2)+base_gate*(self.base_clearance_w2@hidden+self.base_clearance_b2)
        selector_hidden=np.tanh(self.selector_w1@hidden+self.selector_b1)
        selector=1/(1+np.exp(-np.clip(self.selector_w2@selector_hidden+self.selector_b2,-60,60)))
        channel_floor=None
        if hasattr(self,'selector_pulse_steps'):
            positive=selector>=0.5
            self.selector_positive_steps=self.selector_positive_steps+1 if positive else 0
            if not self.selector_pulse_used and self.selector_positive_steps>=self.selector_confirm_steps:
                self.selector_pulse_remaining=self.selector_pulse_steps;self.selector_pulse_used=True
            pulse_active=self.selector_pulse_remaining>0
            if hasattr(self,'selector_slowdown_floor'):
                # The reservoir selector supplies timing only.  Keep the complete
                # validated base readout and alter only its normalized slowdown
                # request during the pre-contact pulse.
                selector=0.0
                channel_floor=(0,self.selector_slowdown_floor) if pulse_active else None
            elif hasattr(self,'selector_vertical_floor'):
                selector=0.0
                channel_floor=(3,self.selector_vertical_floor) if pulse_active else None
            else:selector=float(pulse_active)*getattr(self,'selector_pulse_scale',1.0)
            self.selector_pulse_remaining=max(0,self.selector_pulse_remaining-1)
        elif hasattr(self,'selector_confirm_steps'):
            self.selector_positive_steps=self.selector_positive_steps+1 if selector>=0.5 else 0
            if getattr(self,'selector_latch_enabled',False):
                self.selector_latched=self.selector_latched or self.selector_positive_steps>=self.selector_confirm_steps
                selector=float(self.selector_latched)
            else:selector=float(self.selector_positive_steps>=self.selector_confirm_steps)
        elif getattr(self,'hard_selector',False):selector=float(selector>=0.5)
        logits=(1-selector)*base_logits+selector*(self.margin_w2@hidden+self.margin_b2)
        result=np.tanh(logits);result[0]=1/(1+np.exp(-np.clip(logits[0],-60,60)))
        result*=self.output_gain
        if channel_floor is not None:
            index,floor=channel_floor;result[index]=max(result[index],floor)
        self.previous_action+=self.alpha*(result-self.previous_action)
        return self.previous_action.copy()

class HardHierarchicalMarginProprio48ESN(HierarchicalMarginProprio48ESN):
    """Hierarchical policy with a binary selector and the same action filter."""
    def __init__(self,path):
        super().__init__(path);self.hard_selector=True

class DebouncedHierarchicalMarginProprio48ESN(HierarchicalMarginProprio48ESN):
    """Binary hierarchical selector requiring sustained reservoir evidence."""
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            if 'selector_confirm_steps' not in z.files:raise ValueError('Missing selector_confirm_steps')
            confirm=int(z['selector_confirm_steps'])
        if confirm<1:raise ValueError('selector_confirm_steps must be positive')
        super().__init__(path);self.selector_confirm_steps=confirm;self.reset()

class LatchedHierarchicalMarginProprio48ESN(HierarchicalMarginProprio48ESN):
    """Sustained-evidence selector that latches the margin expert per episode."""
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            if 'selector_confirm_steps' not in z.files:raise ValueError('Missing selector_confirm_steps')
            confirm=int(z['selector_confirm_steps'])
        if confirm<1:raise ValueError('selector_confirm_steps must be positive')
        super().__init__(path);self.selector_confirm_steps=confirm;self.selector_latch_enabled=True;self.reset()

class PulsedHierarchicalMarginProprio48ESN(HierarchicalMarginProprio48ESN):
    """Reservoir-triggered, one-shot margin pulse with episode-local memory."""
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            required=('selector_confirm_steps','selector_pulse_steps')
            missing=[key for key in required if key not in z.files]
            if missing:raise ValueError(f'Missing pulse selector fields: {missing}')
            confirm=int(z['selector_confirm_steps']);pulse=int(z['selector_pulse_steps'])
            scale=float(z['selector_pulse_scale']) if 'selector_pulse_scale' in z.files else 1.0
        if confirm<1 or pulse<1 or not 0<scale<=1:raise ValueError('invalid selector confirm/pulse/scale')
        super().__init__(path);self.selector_confirm_steps=confirm;self.selector_pulse_steps=pulse
        self.selector_pulse_scale=scale;self.reset()

class SlowdownPulsedHierarchicalMarginProprio48ESN(HierarchicalMarginProprio48ESN):
    """Reservoir-timed pulse that changes only the base policy slowdown."""
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            required=('selector_confirm_steps','selector_pulse_steps','selector_slowdown_floor')
            missing=[key for key in required if key not in z.files]
            if missing:raise ValueError(f'Missing slowdown pulse fields: {missing}')
            confirm=int(z['selector_confirm_steps']);pulse=int(z['selector_pulse_steps'])
            floor=float(z['selector_slowdown_floor'])
        if confirm<1 or pulse<1 or not 0<floor<=1:raise ValueError('invalid selector confirm/pulse/slowdown floor')
        super().__init__(path);self.selector_confirm_steps=confirm;self.selector_pulse_steps=pulse
        self.selector_slowdown_floor=floor;self.reset()

class VerticalPulsedHierarchicalMarginProprio48ESN(HierarchicalMarginProprio48ESN):
    """Reservoir-timed pulse that changes only upward translational yield."""
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            required=('selector_confirm_steps','selector_pulse_steps','selector_vertical_floor')
            missing=[key for key in required if key not in z.files]
            if missing:raise ValueError(f'Missing vertical pulse fields: {missing}')
            confirm=int(z['selector_confirm_steps']);pulse=int(z['selector_pulse_steps'])
            floor=float(z['selector_vertical_floor'])
        if confirm<1 or pulse<1 or not 0<floor<=1:raise ValueError('invalid selector confirm/pulse/vertical floor')
        super().__init__(path);self.selector_confirm_steps=confirm;self.selector_pulse_steps=pulse
        self.selector_vertical_floor=floor;self.reset()

class Dual64Proprio48ESN:
    """Shared 128-unit reservoir with two 64-unit proprioceptive readouts."""
    kind='esn'; contract='proprio48_esn_dual64_action7_v1'; dt=.04
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            required=('mean','std','win','w','leak','input_mask','alpha','output_gain',
                      'fmean','fstd','route_w1','route_b1','route_w2','route_b2',
                      'impact_w1','impact_b1','impact_w2','impact_b2',
                      'transient_center','transient_width','attack_tau','release_tau')
            missing=[key for key in required if key not in z.files]
            if missing:raise ValueError(f'Missing dual64 ESN fields: {missing}')
            for key in required:
                value=z[key].copy();setattr(self,key,float(value) if value.shape==() else value)
        if self.transient_center<0 or self.transient_width<=0 or self.attack_tau<=0 or self.release_tau<=0:
            raise ValueError('Invalid dual64 transient gate parameters')
        self.obj=self;self.reset()
    def reset(self):
        self.state=np.zeros(128);self.previous_action=np.zeros(7);self.previous_qvel=np.zeros(7);self.transient_gate=0.
    @staticmethod
    def _activate(raw):
        result=np.tanh(raw);result[0]=1/(1+np.exp(-np.clip(raw[0],-60,60)));return result
    def act(self,observation):
        raw=np.asarray(observation,dtype=float)
        if raw.shape!=(48,) or not np.isfinite(raw).all():raise ValueError('Expected finite proprio48 observation')
        qvel=raw[7:14].copy();transient=float(np.linalg.norm(qvel-self.previous_qvel));self.previous_qvel=qvel
        x=np.clip((raw-self.mean)/self.std,-12,12)*self.input_mask
        self.state+=self.leak*(np.tanh(self.win@np.r_[1.,x]+self.w@self.state)-self.state)
        features=(np.r_[x,self.state]-self.fmean)/self.fstd
        route_hidden=np.tanh(self.route_w1@features+self.route_b1)
        impact_hidden=np.tanh(self.impact_w1@features+self.impact_b1)
        route=self._activate(self.route_w2@route_hidden+self.route_b2)*self.output_gain
        impact=self._activate(self.impact_w2@impact_hidden+self.impact_b2)*self.output_gain
        target=1/(1+np.exp(-np.clip((transient-self.transient_center)/self.transient_width,-60,60)))
        tau=self.attack_tau if target>self.transient_gate else self.release_tau
        self.transient_gate+=(1-np.exp(-self.dt/tau))*(target-self.transient_gate)
        self.transient_gate=float(np.clip(self.transient_gate,0.,1.))
        result=(1-self.transient_gate)*route+self.transient_gate*impact
        self.previous_action+=self.alpha*(result-self.previous_action)
        return self.previous_action.copy()

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
    if contract=='proprio48_context_network_v1':
        from office_context_network_20261003 import OfficeContextNetwork
        return OfficeContextNetwork(path)
    if contract=='proprio48_office_mlp_rnn_v1':
        from office_mlp_rnn_20261002 import OfficeMLPRNN
        return OfficeMLPRNN(path)
    if (contract=='proprio48_office_vmc_memory_esn_v1' or
        contract.startswith('VMC_teacher_ESN_state_delta_residual_20261007_v1') or
        contract.startswith('VMC_teacher_ESN_state_delta_readout_20261007_v1')):
        from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN
        return OfficeVMCMemoryESN(path)
    if contract=='current_four_scene_action7_mlp_v1':return CurrentMLP(path)
    if contract=='proprio48_action7_mlp_v1':return CurrentMLP(path)
    if contract=='four_scene_contact45_action7_v1':return CurrentESN(path)
    if contract=='proprio48_esn128_action7_v1':return Proprio48ESN(path)
    if contract=='proprio48_esn128_action7_load_gated_v1':return LoadGatedProprio48ESN(path)
    if contract=='proprio48_esn128_action7_quiet_centered_v1':return QuietCenteredProprio48ESN(path)
    if contract=='proprio48_esn128_action7_impact_response_v1':return ImpactResponseProprio48ESN(path)
    if contract=='proprio48_esn_dual64_action7_v1':return Dual64Proprio48ESN(path)
    if contract=='proprio48_esn128_action7_gated_v1':return GatedProprio48ESN(path)
    if contract=='proprio48_esn128_action7_gated_mlp_v1':return GatedMLPProprio48ESN(path)
    if contract=='proprio48_esn128_action7_hierarchical_margin_v1':return HierarchicalMarginProprio48ESN(path)
    if contract=='proprio48_esn128_action7_hierarchical_margin_hard_v1':return HardHierarchicalMarginProprio48ESN(path)
    if contract=='proprio48_esn128_action7_hierarchical_margin_debounced_v1':return DebouncedHierarchicalMarginProprio48ESN(path)
    if contract=='proprio48_esn128_action7_hierarchical_margin_latched_v1':return LatchedHierarchicalMarginProprio48ESN(path)
    if contract=='proprio48_esn128_action7_hierarchical_margin_pulsed_v1':return PulsedHierarchicalMarginProprio48ESN(path)
    if contract=='proprio48_esn128_action7_hierarchical_margin_slowdown_pulsed_v1':return SlowdownPulsedHierarchicalMarginProprio48ESN(path)
    if contract=='proprio48_esn128_action7_hierarchical_margin_vertical_pulsed_v1':return VerticalPulsedHierarchicalMarginProprio48ESN(path)
    if contract=='linear_esn_action7_v1':return LinearESN(path)
    if contract=='proprio48_linear_esn_action7_v1':return LinearESN(path)
    raise ValueError(f'Unsupported current checkpoint contract: {contract}')
