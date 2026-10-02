"""One original video fixture per process, common baseline injection and audit.
No scene clock, obstacle geometry, teacher action or contact truth enters policy.
"""
import argparse,contextlib,hashlib,json,os,runpy,sys,time,traceback
from pathlib import Path
import numpy as np
ROOT=Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002')
SCENE=ROOT/'source_scene_20260918/scripts'

def clean(x):
 if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 if isinstance(x,np.ndarray):return x.tolist()
 if isinstance(x,np.generic):return x.item()
 if isinstance(x,Path):return str(x)
 return x

def execute(request,channel):
 fixture=request['fixture'];out=Path(request['output']);out.mkdir(parents=True,exist_ok=False)
 (out/'request.json').write_text(json.dumps(request,indent=2))
 os.environ.update({k:str(v) for k,v in fixture['environment'].items()})
 os.environ.update(MUJOCO_GL='egl',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
 sys.path.insert(0,str(SCENE))
 import mujoco
 import audited_velocity_env as module
 from haptic_vmc_teacher_20260916 import JointLoadObserver,equivalent_tool_wrench
 from run_benchmark import body_jacobian,body_twist,so3_log
 if mujoco.__version__!='3.11.0':raise RuntimeError('Frozen MuJoCo 3.11.0 required')
 method=request['method'];cfg=request.get('parameters',{});state={};records=[];raw=[];render_states=[]
 original_torque=module.safe_velocity_tracking_torque
 protocol_out=channel
 def send(value):
  if method=='rl':print(json.dumps(clean(value),allow_nan=False),file=protocol_out,flush=True)
 def receive():
  line=sys.stdin.readline()
  if not line:raise RuntimeError('RL action pipe closed')
  v=json.loads(line)
  if v.get('stop'):raise InterruptedError('checkpoint boundary cancellation')
  a=np.asarray(v['action'],float)
  if a.shape!=(7,) or not np.isfinite(a).all() or np.max(np.abs(a))>1.000001:raise ValueError('invalid action')
  return np.clip(a,-1,1)
 class BaselineEnv(module.PandaWBCVelocityResidualEnv):
  def __init__(self,*a,**kw):
   self._baseline_observer=None;self._baseline_callback=None;self._baseline_initialized=False
   self.interval=None;self.pending=None;self.offset=np.zeros(6);self.velocity=np.zeros(6)
   self.total_dt=0.;self.total_e2=0.;self.peak_tau=0.;self.peak_speed=0.;self.max_pen=0.;self.contact_duration=0.;self.intended_contact_duration=0.;self.pairs={};self.steps=0;self.initial_object=None
   super().__init__(*a,**kw);state['env']=self
  @property
  def substep_observer(self):return self._observe
  @substep_observer.setter
  def substep_observer(self,v):self._baseline_callback=v
  def _initialize(self):
   if self._baseline_initialized:return
   m,d=self.model,self.data
   self._baseline_observer=JointLoadObserver(d.qvel.copy(),m.dof_frictionloss)
   self._baseline_mass=np.zeros((m.nv,m.nv));self.scratch=mujoco.MjData(m);self.jp=np.zeros((3,m.nv));self.jr=np.zeros((3,m.nv))
   self.initial_object=d.xpos[self._target_body_id].copy()
   mujoco.mj_saveModel(m,str(out/'model.mjb'),None)
   (out/'model.xml').write_text(self.model_xml if isinstance(getattr(self,'model_xml',None),str) else '<!-- use model.mjb for exact reconstruction -->')
   self._baseline_initialized=True
  def _observe(self,t):
   if self._baseline_callback:self._baseline_callback(t)
   if not self._baseline_initialized or self.interval is None or request.get('disable_metrics',False):return
   m,d=self.model,self.data;dt=float(m.opt.timestep)
   mujoco.mj_fullM(m,d,self._baseline_mass)
   self._baseline_observer.update(d.qvel.copy(),self._baseline_mass,d.qfrc_bias.copy(),d.qfrc_passive.copy(),d.qfrc_actuator.copy(),dt)
   s=self.scratch;s.qpos[:]=d.qpos;s.qvel[:]=d.qvel;s.mocap_pos[:]=d.mocap_pos;s.mocap_quat[:]=d.mocap_quat
   mujoco.mj_kinematics(m,s);mujoco.mj_comPos(m,s);mujoco.mj_jacBody(m,s,self.jp,self.jr,self._hand_id)
   error=s.xpos[self._hand_id]-self._baseline_target;e2=float(error@error);speed=float(np.linalg.norm(self.jp@s.qvel));tau=np.abs(d.qfrc_actuator[:7]);iv=self.interval
   iv['elapsed_s']+=dt;iv['error_integral']+=dt*e2;iv['bounded_error_integral']+=dt*e2/(.12**2+e2);iv['peak_torque_nm_per_joint']=np.maximum(iv['peak_torque_nm_per_joint'],tau);iv['max_position_error_m']=max(iv['max_position_error_m'],np.sqrt(e2));iv['substeps']+=1
   iv['peak_torque_ratio']=max(iv['peak_torque_ratio'],float(np.max(tau/np.asarray(self.torque_limits)[:7])))
   self.total_dt+=dt;self.total_e2+=dt*e2;self.peak_tau=max(self.peak_tau,float(tau.max()));self.peak_speed=max(self.peak_speed,speed)
   robot=self._push_audit_robot_geom_ids;touch=False;intended=False
   for ci in range(d.ncon):
    c=d.contact[ci];g1,g2=int(c.geom1),int(c.geom2)
    if (g1 in robot)==(g2 in robot):continue
    other=g2 if g1 in robot else g1
    if int(m.geom_bodyid[other])==self._target_body_id:continue
    self.max_pen=max(self.max_pen,-float(c.dist))
    f=np.zeros(6);mujoco.mj_contactForce(m,d,ci,f);force=float(np.linalg.norm(f[:3]))
    if force>.05:
     touch=True;other_name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,other) or '';prefix={'ball':'primitive_free_ball','push':'push_rod','corner':'primitive_corner','table_corner':'table_side'}[fixture['scene']];intended=intended or other_name.startswith(prefix);names=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g) or str(g) for g in (g1,g2)];key='|'.join(sorted(names));p=self.pairs.setdefault(key,dict(first_s=float(d.time),last_s=0.,duration_s=0.,peak_n=0.,impulse_ns=0.));p['duration_s']+=dt if p['last_s']!=float(d.time) else 0.;p['last_s']=float(d.time);p['peak_n']=max(p['peak_n'],force);p['impulse_ns']+=force*dt
   if touch:self.contact_duration+=dt
   if intended:self.intended_contact_duration+=dt
   if request.get('save_substeps',False) and (not render_states or d.time-render_states[-1][0]>=.01-1e-8):render_states.append((float(d.time),d.qpos.copy(),d.qvel.copy(),d.ctrl.copy()))
   if request.get('save_substeps',False):raw.append(np.r_[d.time,dt,error,tau,speed,self.max_pen])
  def observation(self):
   d=self.data;m=self.model;command=self._wbc_command(self.step_count*.04);tw=body_twist(m,d,self._hand_id);error=np.r_[command.target_position_m-d.xpos[self._hand_id],so3_log(command.target_rotation@d.xmat[self._hand_id].reshape(3,3).T)]
   wrench=equivalent_tool_wrench(body_jacobian(m,d,self._hand_id),self._baseline_observer.filtered)
   direction=np.asarray(getattr(self.reference,'path_direction',command.task_twist_world[:3]),float).copy()
   if np.linalg.norm(direction)<1e-8:direction=error[:3].copy()
   direction/=max(np.linalg.norm(direction),1e-9)
   obs=np.r_[d.qpos[:7],d.qvel[:7],command.task_twist_world,error,command.task_twist_world-tw,self._baseline_observer.filtered,wrench,direction]
   if obs.shape!=(48,) or not np.isfinite(obs).all():raise ValueError('proprio48 contract')
   return obs
  def potential(self):
   if hasattr(self.reference,'index'):
    i=int(self.reference.index);n=len(self.reference.goals);err=np.linalg.norm(self.data.xpos[self._hand_id]-self.reference.goals[i]);return float((i+1/(1+err/.04))/n)
   # Legacy task exposes a moving reference, not waypoint stage; avoid fabricated stage labels.
   return float(np.clip((self.data.xpos[self._target_body_id,2]-self.initial_object[2])/.30,0,1))
  def step(self,unused_teacher_action):
   self._initialize();obs=self.observation();phi=self.potential()
   send(dict(kind='observation',observation=obs,interval=self.pending,potential=phi))
   if method=='rl':action=receive()
   elif method=='admittance':
    mass=np.r_[np.full(3,cfg.get('mass',.55)),np.full(3,cfg.get('inertia',.065))];k=np.r_[np.full(3,cfg.get('stiffness',95.)),np.full(3,cfg.get('rot_stiffness',4.))];damp=2*cfg.get('zeta',1.2)*np.sqrt(mass*k);bounds=np.array([30,30,30,3,3,3]);force=bounds*np.tanh(obs[39:45]/bounds)
    for _ in range(20):
     self.velocity=np.clip(self.velocity+.002*(force-damp*self.velocity-k*self.offset)/mass,-np.array([.16]*3+[.6]*3),np.array([.16]*3+[.6]*3));self.offset=np.clip(self.offset+.002*self.velocity,-np.array([.08]*3+[.25]*3),np.array([.08]*3+[.25]*3))
    action=np.r_[0,self.velocity[:3]/self.safety_config.maximum_linear_yield_mps,self.velocity[3:]/self.safety_config.maximum_angular_yield_radps];action=np.clip(action,-1,1)
   elif method=='original':action=np.asarray(unused_teacher_action,float).copy()
   else:action=np.zeros(7)
   self._baseline_target=self._wbc_command(self.step_count*.04).target_position_m.copy()
   self.interval=dict(elapsed_s=0.,error_integral=0.,bounded_error_integral=0.,peak_torque_ratio=0.,peak_torque_nm_per_joint=np.zeros(7),max_position_error_m=0.,substeps=0)
   result=super().step(action)
   self.pending=clean(self.interval);self.pending['potential']=self.potential();self.pending['time_s']=float(self.data.time)
   records.append(dict(time=float(self.data.time),observation=obs,action=action,position=self.data.xpos[self._hand_id].copy(),target=self._baseline_target.copy(),object_position=self.data.xpos[self._target_body_id].copy(),qpos=self.data.qpos.copy(),qvel=self.data.qvel.copy(),ctrl=self.data.ctrl.copy(),potential=phi,interval=clean(self.interval)))
   self.steps+=1
   return result
  def close(self):
   if self._baseline_initialized:
    state['final_obs']=self.observation();state['pending']=self.pending
   super().close()
 def torque(bias_torque,measured_joint_velocity,joint_velocity_command,previous_torque,dt,config,torque_limits=None):
  e=state['env'];m,d=e.model,e.data;c=e._wbc_command(e.step_count*.04);J=body_jacobian(m,d,e._hand_id);err=np.r_[c.target_position_m-d.xpos[e._hand_id],so3_log(c.target_rotation@d.xmat[e._hand_id].reshape(3,3).T)];tw=c.task_twist_world-body_twist(m,d,e._hand_id);k=np.r_[np.full(3,cfg.get('stiffness',600.)),np.full(3,cfg.get('rot_stiffness',30.))];mass=np.r_[np.full(3,cfg.get('mass',1.)),np.full(3,cfg.get('inertia',.08))];damp=2*cfg.get('zeta',1.2)*np.sqrt(mass*k);null=np.eye(7)-J.T@np.linalg.pinv(J.T);residual=J.T@(k*err+damp*tw)-null@(2*np.asarray(measured_joint_velocity));equivalent=np.asarray(measured_joint_velocity)+residual/np.asarray(config.velocity_gain_nm_per_radps)
  return original_torque(bias_torque,measured_joint_velocity,equivalent,previous_torque,dt,config,torque_limits=torque_limits)
 module.PandaWBCVelocityResidualEnv=BaselineEnv
 if method=='impedance':module.safe_velocity_tracking_torque=torque
 if fixture['scene']!='table_corner':
  import dataset_primitive_initialization_20260918 as init
  module.PandaWBCVelocityResidualEnv=init.InitialStateEnv
 flags=dict(fixture['flags']);flags['output']=str(out/'original.gif' if fixture['scene']=='table_corner' else out/'original')
 if request.get('duration') is not None:flags['simulation_time' if fixture['scene']=='table_corner' else 'duration']=request['duration']
 if fixture['scene']=='table_corner':flags['trace_output']=str(out/'legacy.npz')
 entry=SCENE/fixture['entry'];sys.argv=[str(entry)]
 for k,v in flags.items():
  if v is None or v is False:continue
  sys.argv+=['--'+k.replace('_','-')]
  if v is not True:sys.argv.append(str(v))
 started=time.monotonic()
 with (out/'run.log').open('w') as log,contextlib.redirect_stdout(log):runpy.run_path(str(entry),run_name='__main__')
 e=state['env'];source=json.loads((out/'original.json').read_text());duration=float(records[-1]['time']) if records else 0
 physical=bool(e.max_pen<=.0002 and np.isfinite(e.peak_tau))
 task=bool(source.get('success',False)) if fixture['scene']!='table_corner' else bool(source.get('object_grasped_and_lifted') and source.get('object_placed_on_table') and source.get('final_gripper_command_m',0)>.025)
 summary=dict(method=method,fixture_id=fixture['id'],scene=fixture['scene'],physical_hash=fixture.get('physical_hash'),model_sha256=hashlib.sha256((out/'model.mjb').read_bytes()).hexdigest(),task_success=task,physical_valid=physical,contact_exposed=e.intended_contact_duration>0.,intended_contact_duration_s=e.intended_contact_duration,all_external_contact_duration_s=e.contact_duration,strict_success=task and physical and e.intended_contact_duration>0.,duration_s=duration,wall_s=time.monotonic()-started,rmse_m=float(np.sqrt(e.total_e2/max(e.total_dt,1e-12))),peak_torque_nm=e.peak_tau,peak_speed_mps=e.peak_speed,max_external_penetration_m=e.max_pen,contacts=e.pairs,original_result=str(out/'original.json'),steps=e.steps,controller_parameters=cfg,worker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),legacy_runner_controller_labels_are_not_executed_baseline=True,observation_contract='proprio48 q7,dq7,nominal6,pose6,twist_error6,estimated_load7,estimated_wrench6,path3',action_contract='native normalized action7; fixture safety limits unchanged; actual actions in control.npz',safety_config=clean(vars(e.safety_config)),simulation_timestep_s=float(e.model.opt.timestep) if e.model is not None else source.get('simulation_timestep_s',source.get('simulation_numerics',{}).get('timestep_s')),training_only=fixture.get('split')=='train',task_definition='legacy table requires measured lift, placement and released gripper; primitives retain original success; contact separately reported')
 np.savez_compressed(out/'control.npz',**{k:np.asarray([r[k] for r in records]) for k in records[0] if k!='interval'})
 (out/'intervals.json').write_text(json.dumps([r['interval'] for r in records]))
 if render_states:np.savez_compressed(out/'render_states.npz',time=np.array([r[0] for r in render_states]),qpos=np.array([r[1] for r in render_states]),qvel=np.array([r[2] for r in render_states]),ctrl=np.array([r[3] for r in render_states]))
 if raw:np.savez_compressed(out/'substeps.npz',values=np.asarray(raw,dtype=np.float64),columns=np.array(['time','dt','error_x','error_y','error_z']+[f'torque_{j}' for j in range(7)]+['speed','max_penetration']))
 (out/'result.json').write_text(json.dumps(clean(summary),indent=2,allow_nan=False))
 send(dict(kind='terminal',observation=state['final_obs'],interval=state['pending'],result=summary))
 if method!='rl':print(json.dumps(summary),file=protocol_out,flush=True)
 return summary

def main():
 p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);a=p.parse_args();request=json.loads(a.request.read_text())
 try:execute(request,sys.stdout)
 except BaseException:
  error=traceback.format_exc();Path(request['output']).mkdir(parents=True,exist_ok=True);(Path(request['output'])/'ERROR.txt').write_text(error)
  print(json.dumps(dict(kind='error',error=error)),flush=True);raise
if __name__=='__main__':main()
