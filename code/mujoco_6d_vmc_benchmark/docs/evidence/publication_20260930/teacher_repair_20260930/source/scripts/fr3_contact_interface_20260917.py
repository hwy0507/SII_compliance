"""Portable proprioceptive observer and fail-closed action boundary.

No MuJoCo import, acceleration, contact truth, obstacle geometry or event clock.
Torque conventions: tau is TOTAL measured generalized actuator torque; bias
is C(q,dq)dq+g(q), passive is a calibrated internal passive-torque model.
These are NOT libfranka commanded-torque conventions (gravity handled there).
"""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class SensorConfig:
    period_s: float = .001
    filter_tau_s: float = .020
    velocity_noise_std: float = .001
    torque_noise_std: float = .03
    torque_bias_std: float = .02
    seed: int = 0


class SampledMomentumObserver:
    """Causal momentum residual, sampled independently of physics dt.

    p=M dq; p_dot=tau+passive-bias+M_dot dq+tau_ext.
    Backward-Euler residual observer:
      r_k=(tau_o*r_{k-1}+p_k-p_{k-1}-dt*u_k)/(tau_o+dt).
    The momentum increment is filtered; encoder acceleration is not required.
    Internal friction compensation remains a model assumption to calibrate.
    """
    def __init__(self, velocity, frictionloss, config=SensorConfig()):
        self.config=config
        if config.period_s<=0 or config.filter_tau_s<=0:raise ValueError('Invalid sample period')
        self.rng=np.random.default_rng(config.seed)
        self.bias=self.rng.normal(0,config.torque_bias_std,7)
        self.friction=np.asarray(frictionloss,dtype=float)[:7].copy()
        self.filtered=np.zeros(7);self.raw_residual=np.zeros(7)
        self.elapsed=0.;self.previous_m=None;self.previous_p=None
        self.previous_velocity=np.asarray(velocity,dtype=float)[:7].copy()
        self.samples=0

    def update(self, velocity, mass_matrix, bias, passive, actuator_torque, dt):
        if not np.isfinite(dt) or dt<=0:raise ValueError('Invalid dt')
        self.elapsed+=dt
        if self.elapsed+1e-12<self.config.period_s:return self.filtered.copy()
        elapsed=self.elapsed;self.elapsed=0.;c=self.config
        v=np.asarray(velocity,dtype=float)[:7]+self.rng.normal(0,c.velocity_noise_std,7)
        m=np.asarray(mass_matrix,dtype=float)[:7,:7]
        motor=np.asarray(actuator_torque,dtype=float)[:7]+self.bias+self.rng.normal(0,c.torque_noise_std,7)
        internal=np.asarray(passive,dtype=float)[:7]-np.asarray(bias,dtype=float)[:7]
        if not all(np.isfinite(x).all() for x in (v,m,motor,internal)):raise ValueError('Nonfinite sensor packet')
        p=m@v
        if self.previous_m is not None:
            mdot_v=((m-self.previous_m)/elapsed)@(.5*(v+self.previous_velocity))
            u=motor+internal+mdot_v
            self.raw_residual=(c.filter_tau_s*self.raw_residual+p-self.previous_p-elapsed*u)/(c.filter_tau_s+elapsed)
            motion=np.tanh(v/.005)
            compensated=self.raw_residual+self.friction*motion
            uncertainty=self.friction*(1.-abs(motion))
            self.filtered=np.sign(compensated)*np.maximum(abs(compensated)-uncertainty,0.)
        self.previous_m=m.copy();self.previous_p=p.copy();self.previous_velocity=v.copy();self.samples+=1
        return self.filtered.copy()


@dataclass(frozen=True)
class ActionBoundaryConfig:
    policy_period_s: float = .010
    stale_after_s: float = .030
    max_linear_speed_mps: float = .12
    max_linear_acceleration_mps2: float = .8


class ActionBoundary:
    """Transport-agnostic velocity boundary; not a robot hardware driver.

    Stale/invalid packets latch a stop request for the robot's verified
    controller. Returning zero here cannot prove the physical arm has stopped.
    """
    def __init__(self, config=ActionBoundaryConfig()):
        self.config=config;self.previous=np.zeros(3);self.stop_requested=False

    def step(self, nominal_velocity, action, age_s, dt):
        c=self.config
        action=np.asarray(action);nominal=np.asarray(nominal_velocity)
        if (action.shape!=(7,) or nominal.shape!=(3,) or not np.isfinite(action).all()
            or not np.isfinite(nominal).all() or not np.isfinite(age_s) or age_s<0
            or age_s>c.stale_after_s or not np.isfinite(dt) or dt<=0 or dt>.01):
            self.stop_requested=True
        if self.stop_requested:return np.zeros(3)
        action=np.clip(action,-1,1)
        desired=(1.-.8*max(0.,action[0]))*nominal+.32*action[1:4]
        desired*=min(1.,c.max_linear_speed_mps/max(np.linalg.norm(desired),1e-12))
        delta=desired-self.previous
        delta*=min(1.,c.max_linear_acceleration_mps2*dt/max(np.linalg.norm(delta),1e-12))
        self.previous+=delta
        return self.previous.copy()
