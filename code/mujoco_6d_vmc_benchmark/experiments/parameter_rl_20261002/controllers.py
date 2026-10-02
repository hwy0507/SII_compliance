"""BO-derived, scene-independent online parameter controllers.

The tank limits positive changes in the controller's local stored-energy model.
Moving nominal references, readout gains, discrete saturation and robot dynamics
are outside that guarantee; this is not a global passivity/stability proof.
"""
import json,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
HERE=Path(__file__).resolve().parent
VENDOR=HERE/'vendor'
sys.path.insert(0,str(VENDOR))
from stiffness_training_core import action_to_kappa,StiffnessActionConfig
from teacher_bank_classical_20260930 import physical_vectors
from admittance_reference_core_20260923 import rotation_offset_and_jacobian
from run_panel_admittance_reference_20260923 import ReferenceAdmittance
from run_panel_impedance_reference_20260923 import MovingEquilibrium,ReferenceImpedanceConfig,clip_norm
from vmc_teacher_stable_readout_20260930 import StableReadoutTeacher

def vectors(method,theta):
 if method=='vmc':
  scale=np.r_[theta[0],theta[0],theta[1],np.repeat(theta[2],3)]
  k=np.array([400,400,1200,10,8,12])*scale
  d=np.array([28,28,55,2.8,2.4,3])*np.sqrt(scale)*np.r_[np.repeat(theta[3],3),np.repeat(theta[4],3)]
  return np.array([.5,.5,.8,.06,.06,.08]),k,d
 keys=['stiffness','rot_stiffness','mass','inertia','zeta','rot_zeta','vertical_stiffness_ratio'] if method=='admittance' else ['stiffness','rot_stiffness','zeta','rot_zeta','vertical_stiffness_ratio']
 cfg=dict(zip(keys,map(float,theta)))
 if method=='impedance':cfg.update(mass=.5,inertia=.06)
 return physical_vectors(cfg)

class ParameterShield:
 def __init__(self,method,prior):
  self.method=method;self.prior=prior;self.center=np.asarray(prior['center']);self.theta=self.center.copy();self.bounds=np.asarray(prior['bounds']);self.energy=.8;self.minimum=.08;self.maximum=1.2;self.records=[]
 def energy_at(self,theta,offset,velocity):
  mass,k,_=vectors(self.method,theta)
  if self.method=='vmc':
   sigma=np.array([30,30,45,3,3,3]);u=k*offset/sigma
   potential=np.sum(sigma*sigma/k*(np.logaddexp(u,-u)-np.log(2.)))
  else:potential=.5*np.sum(k*offset*offset)
  kinetic=0. if self.method=='impedance' else .5*np.sum(mass*velocity*velocity)
  return float(potential+kinetic)
 def update(self,action,offset,velocity,dt=.04):
  action=np.asarray(action,float);offset=np.asarray(offset,float);velocity=np.asarray(velocity,float);n=len(self.center)
  if offset.shape!=(6,) or velocity.shape!=(6,) or not np.isfinite(offset).all() or not np.isfinite(velocity).all() or dt<=0:raise ValueError('Finite six-dimensional storage state and positive dt required')
  if action.shape!=(n,) or not np.isfinite(action).all() or np.max(abs(action))>1.000001:raise ValueError('Finite bounded parameter action required')
  proposed=[]
  # Reuse the repository's validated six-vector log map in padded blocks.
  for start in range(0,n,6):
   count=min(6,n-start);pad=6-count
   fill=lambda x:tuple(np.r_[x,np.ones(pad)])
   cfg=StiffnessActionConfig(base_kappa=fill(self.center[start:start+count]),minimum_kappa=fill(self.bounds[start:start+count,0]),maximum_kappa=fill(self.bounds[start:start+count,1]),action_log_span=self.prior['action_log_span'],update_hz=1/dt,max_log_rate_per_s=self.prior['max_log_rate_per_s'])
   proposed.extend(action_to_kappa(np.r_[action[start:start+count],np.zeros(pad)],fill(self.theta[start:start+count]),cfg)[:count])
  target=np.asarray(proposed);old=self.theta.copy();before=self.energy;_,_,damping=vectors(self.method,old)
  # Relative virtual damping is a local accounting model, not measured robot dissipation.
  recharge=min(self.maximum-self.energy,.2*float(np.sum(damping*velocity*velocity))*dt)
  self.energy+=recharge;available=self.energy-self.minimum;u0=self.energy_at(old,offset,velocity)
  def candidate(alpha):return np.exp(np.log(old)+alpha*(np.log(target)-np.log(old)))
  def cost(alpha):return self.energy_at(candidate(alpha),offset,velocity)-u0
  requested=cost(1.);alpha=1.
  if requested>available:
   lo,hi=0.,1.
   for _ in range(45):
    mid=(lo+hi)/2
    if cost(mid)<=available:lo=mid
    else:hi=mid
   alpha=lo
  self.theta=candidate(alpha);change=self.energy_at(self.theta,offset,velocity)-u0
  debit=max(change,0.);credit=min(max(-change,0.),self.maximum-(self.energy-debit));self.energy=self.energy-debit+credit
  if self.energy<self.minimum-1e-10 or self.energy>self.maximum+1e-10:raise RuntimeError('Parameter energy budget violated')
  row=dict(raw_action=action.tolist(),previous_parameters=old.tolist(),requested_parameters=target.tolist(),applied_parameters=self.theta.tolist(),energy_before_j=before,recharge_j=recharge,requested_storage_change_j=requested,applied_storage_change_j=change,debit_j=debit,credit_j=credit,energy_after_j=self.energy,energy_scale=alpha,offset=offset.tolist(),velocity=velocity.tolist())
  self.records.append(row);return self.theta

class ParameterController:
 def __init__(self,env,method,prior):
  self.env=env;self.method=method;self.prior=prior;self.shield=ParameterShield(method,prior);self.actions=[];self.servo=[];self.last_servo_time=None;self.last_error=np.zeros(6);self.last_relative_velocity=np.zeros(6)
  theta=self.shield.theta;mass,k,d=vectors(method,theta)
  if method=='admittance':
   cfg=SimpleNamespace(stiffness=k[0],rot_stiffness=k[3],mass=mass[0],inertia=mass[3],zeta=1.)
   self.actor=ReferenceAdmittance(cfg,env,.04)
   self.legacy_joint_reference=hasattr(env.fixed_wbc,'waypoints')
  elif method=='vmc':
   self.actor=StableReadoutTeacher(options=dict(stiffness_6d=k,damping_6d=d),velocity_weight=theta[5])
  elif method=='impedance':
   self.actor=MovingEquilibrium(ReferenceImpedanceConfig(stiffness=k[0],rot_stiffness=k[3],mass=.5,inertia=.06,zeta=1.))
   import audited_velocity_env as backend
   from run_benchmark import body_jacobian,body_twist
   self.original_torque=backend.safe_velocity_tracking_torque
   def torque(bias_torque,measured_joint_velocity,joint_velocity_command,previous_torque,dt,config,torque_limits=None):
    e=self.env;data=e.data;command=e._wbc_command(e.step_count*.04);now=float(data.time)
    if self.last_servo_time!=now:
     self.last_error,self.last_nominal=self.actor.update(data.xpos[e._hand_id].copy(),data.xmat[e._hand_id].reshape(3,3).copy(),command.task_twist_world.copy(),dt);self.last_servo_time=now
    measured=body_twist(e.model,data,e._hand_id);self.last_relative_velocity=measured-self.last_nominal
    wrench=self.actor.wrench(self.last_error,self.last_nominal,measured);J=body_jacobian(e.model,data,e._hand_id);residual=J.T@wrench
    equivalent=np.asarray(measured_joint_velocity)+residual/np.asarray(config.velocity_gain_nm_per_radps)
    applied,scale=self.original_torque(bias_torque,measured_joint_velocity,equivalent,previous_torque,dt,config,torque_limits=torque_limits)
    self.servo.append(np.r_[now,self.last_error,wrench,residual,applied,float(scale)])
    return applied,scale
   backend.safe_velocity_tracking_torque=torque
  else:raise ValueError(method)
  self.apply(theta)
 def apply(self,theta):
  mass,k,d=vectors(self.method,theta)
  if self.method=='admittance':self.actor.state.mass=mass;self.actor.state.k=k;self.actor.state.d=d
  elif self.method=='vmc':self.actor.mass=mass;self.actor.k=k;self.actor.b=d;self.actor.velocity_weight=float(theta[5]);self.actor.offset_gain=float(theta[6])
  else:self.actor.k=k;self.actor.damping=d
 def storage_state(self):
  if self.method=='admittance':return self.actor.state.offset.copy(),self.actor.state.velocity.copy()
  if self.method=='vmc':return self.actor.offset.copy(),self.actor.velocity.copy()
  if self.actor.position is None:return np.zeros(6),np.zeros(6)
  from scipy.spatial.transform import Rotation
  e=self.env;d=e.data;err=np.r_[clip_norm(self.actor.position-d.xpos[e._hand_id],.04),clip_norm(Rotation.from_matrix(self.actor.rotation@d.xmat[e._hand_id].reshape(3,3).T).as_rotvec(),.20)]
  return err,self.last_relative_velocity.copy()
 def act(self,obs,action):
  offset,velocity=self.storage_state();theta=self.shield.update(action,offset,velocity);self.apply(theta)
  if self.method=='impedance':out=np.zeros(7)
  elif self.method=='admittance':
   if self.legacy_joint_reference:
    # Joint-waypoint MPC ignores Cartesian target arguments; preserve its
    # nominal command and map virtual reference displacement into twist.
    # Same fixed map is used in BO-derived fixed and learned comparisons.
    self.actor.state.advance(np.asarray(obs)[39:45],.04)
    residual=self.actor.state.virtual_twist()+np.array([5.,5.,5.,3.,3.,3.])*self.actor.state.offset
    out=np.r_[0.,np.clip(residual/self.actor.action_units,-1.,1.)]
   else:out=self.actor.act(obs)
  else:out=self.actor.act(np.asarray(obs)[39:45],.04)
  self.actions.append(np.asarray(out).copy());return out
 def save(self,out):
  (out/'parameter_trace.json').write_text(json.dumps(self.shield.records,allow_nan=False))
  np.savez_compressed(out/'parameter_actions.npz',raw_action=np.asarray([r['raw_action'] for r in self.shield.records]),parameters=np.asarray([r['applied_parameters'] for r in self.shield.records]),executed_action=np.asarray(self.actions),tank=np.asarray([r['energy_after_j'] for r in self.shield.records]),energy_scale=np.asarray([r['energy_scale'] for r in self.shield.records]))
  if self.servo:np.savez_compressed(out/'impedance_servo.npz',values=np.asarray(self.servo),columns=np.asarray(['time']+[f'error_{i}' for i in range(6)]+[f'wrench_{i}' for i in range(6)]+[f'residual_tau_{i}' for i in range(7)]+[f'applied_tau_{i}' for i in range(7)]+['feasible_scale']))
  return dict(controller=self.method,parameter_dimension=self.prior['action_dimension'],parameter_keys=self.prior['keys'],prior=self.prior['center'],updates=len(self.shield.records),minimum_tank_j=min(r['energy_after_j'] for r in self.shield.records),limited_updates=sum(r['energy_scale']<.999999 for r in self.shield.records),reference_mapping=('joint-WBC offset-to-twist gains [5,5,5,3,3,3]' if self.method=='admittance' and self.legacy_joint_reference else 'original BO controller reference mapping'),safety_scope='Rate/bounds and positive change of local storage model. Damping recharge is relative virtual damping. No global robot passivity claim; reference motion and VMC readout gain are outside storage model.')
