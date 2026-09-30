"""6-D VMC teacher in a physically constrained push corridor.

All control parameters are fixed for an episode. No contact state machine,
surface search, time gate, or obstacle-state input is added to the controller.
The common approach-plane/loaded-lift task is frozen from the prior protocol.
"""
import ast
from dataclasses import asdict,replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import numpy as np
import mujoco
from haptic_vmc_teacher_20260916 import HapticVMC, HapticVMCConfig


PARAMETERS=json.loads(os.environ.get('CORE_VMC_CONFIG','{}'))


def virtual_frame(rpy):
    """Fixed virtual-spring principal axes; R K R^T and R D R^T are SPD."""
    roll,pitch,yaw=np.asarray(rpy,dtype=float)
    cr,sr=np.cos(roll),np.sin(roll);cp,sp=np.cos(pitch),np.sin(pitch);cy,sy=np.cos(yaw),np.sin(yaw)
    rx=np.array([[1,0,0],[0,cr,-sr],[0,sr,cr]])
    ry=np.array([[cp,0,sp],[0,1,0],[-sp,0,cp]])
    rz=np.array([[cy,-sy,0],[sy,cy,0],[0,0,1]])
    return rz@ry@rx


class DiagonalVirtualDynamics(HapticVMC):
    """Same equation/integrator/limits, with positive diagonal K and D."""
    def __init__(self,config,stiffness_xyz,damping_xyz):
        super().__init__(config)
        self.k=np.asarray(stiffness_xyz,dtype=float)
        self.b=np.asarray(damping_xyz,dtype=float)
        if self.k.shape!=(3,)or self.b.shape!=(3,)or not np.all(self.k>0)or not np.all(self.b>0):
            raise ValueError('Positive diagonal K,D required')

    def act(self,estimated_force_world,dt):
        c=self.config;force=np.asarray(estimated_force_world,dtype=float)
        if force.shape!=(3,)or not np.isfinite(force).all()or not 0<dt<=.04:raise ValueError('Invalid input')
        norm=np.linalg.norm(force)
        force=force*max(0.,1.-c.force_deadband/max(norm,1e-12))
        force*=min(1.,c.force_limit/max(np.linalg.norm(force),1e-12))
        for _ in range(20):
            acceleration=(force-self.b*self.velocity-self.k*self.offset)/c.mass
            self.velocity+=acceleration*dt/20
            self.velocity*=min(1.,c.velocity_limit/max(np.linalg.norm(self.velocity),1e-12))
            self.offset+=self.velocity*dt/20
            if np.linalg.norm(self.offset)>c.offset_limit:
                n=self.offset/np.linalg.norm(self.offset);self.offset=n*c.offset_limit
                self.velocity-=max(0.,np.dot(self.velocity,n))*n
        action=np.zeros(7)
        action[1:4]=np.clip((self.velocity+c.offset_tracking_gain*self.offset)/c.action_velocity_limit,-1,1)
        return action


class SixDVirtualDynamics:
    """Six independent saturated spring-damper channels in a rotated frame.

    This is the paper-style extension of the previous translational proxy:
    ``M xdd + D xd + sat_K(x) = w_ext`` for translation and rotation,
    integrated causally from the encoder-derived six-dimensional wrench.
    ``axis_rotation_rpy`` rotates both the force and moment principal axes;
    it is a fixed controller parameter, never a scene/event input.
    """
    def __init__(self, options):
        self.k=np.asarray(options.get('stiffness_6d', [400., 400., 1200., 10., 8., 12.]), dtype=float)
        self.b=np.asarray(options.get('damping_6d', [28., 28., 55., 2.8, 2.4, 3.0]), dtype=float)
        self.mass=np.asarray(options.get('mass_6d', [0.5, 0.5, 0.8, 0.06, 0.06, 0.08]), dtype=float)
        self.sigma=np.asarray(options.get('wrench_limit_6d', [30., 30., 45., 3., 3., 3.]), dtype=float)
        self.deadband=np.asarray(options.get('deadband_6d', [0.2, 0.2, 0.2, 0.03, 0.03, 0.03]), dtype=float)
        self.vmax=np.asarray(options.get('velocity_limit_6d', [0.12, 0.12, 0.16, .55, .55, .65]), dtype=float)
        self.xmax=np.asarray(options.get('offset_limit_6d', [.18, .18, .18, .35, .35, .35]), dtype=float)
        self.action_limits=np.asarray(options.get('action_limit_6d', [.16, .16, .20, .60, .60, .60]), dtype=float)
        self.offset_gain=float(options.get('offset_tracking_gain_6d', 1.6))
        self.filter_tau=float(options.get('filter_tau', .04))
        self.rotation=virtual_frame(options.get('axis_rotation_rpy', [0., 0., 0.]))
        self.R6=np.zeros((6,6));self.R6[:3,:3]=self.rotation;self.R6[3:,3:]=self.rotation
        values=np.r_[self.k,self.b,self.mass,self.sigma,self.deadband,self.vmax,self.xmax,self.action_limits,self.offset_gain,self.filter_tau]
        if values.shape!=(50,) or not np.all(np.isfinite(values)) or np.any(values<=0):
            raise ValueError('6-D VMC parameters must be finite and positive')
        self.offset=np.zeros(6);self.velocity=np.zeros(6);self.filtered=np.zeros(6)

    def reset(self):
        self.offset.fill(0.);self.velocity.fill(0.);self.filtered.fill(0.)

    def act(self, wrench_world, dt=.04):
        wrench=np.asarray(wrench_world,dtype=float)
        if wrench.shape!=(6,) or not np.all(np.isfinite(wrench)) or not 0<dt<=.04:
            raise ValueError('expected a finite six-dimensional wrench')
        self.filtered+=(1.-np.exp(-dt/self.filter_tau))*(wrench-self.filtered)
        w=self.R6.T@self.filtered
        w=np.sign(w)*np.maximum(np.abs(w)-self.deadband,0.)
        w=self.sigma*np.tanh(w/self.sigma)
        for _ in range(20):
            spring=self.sigma*np.tanh(self.k*self.offset/self.sigma)
            acc=(w-self.b*self.velocity-spring)/self.mass
            self.velocity=np.clip(self.velocity+acc*(dt/20.),-self.vmax,self.vmax)
            self.offset=np.clip(self.offset+self.velocity*(dt/20.),-self.xmax,self.xmax)
        residual=self.velocity+self.offset_gain*self.offset
        action=np.zeros(7);action[1:]=np.clip(self.R6@residual/self.action_limits,-1.,1.)
        # Proprioceptive slowdown is a causal function of the same six residuals.
        action[0]=float(np.clip(np.linalg.norm(action[1:])/np.sqrt(6.),0.,1.))
        return action


class CoreTeacher:
    def __init__(self,config):
        self.config=config
        options=dict(**PARAMETERS)
        options.setdefault('stiffness_6d', [config.stiffness]*3+[config.stiffness*.08]*3)
        options.setdefault('damping_6d', [config.damping]*3+[config.damping*.08]*3)
        self.base=SixDVirtualDynamics(options)
        self.slide=0.

    def act(self,wrench,position_error,velocity,path_direction,dt=.04):
        return self.base.act(wrench,dt)


def main():
    source=Path(__file__).with_name('run_primitive_teacher_v7_20260917.py')
    spec=importlib.util.spec_from_file_location('primitive_v7_core',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.ContactMemoryVMC=CoreTeacher
    # Extend the validated primitive scene with fixed front/back guard plates.
    # They are physical MuJoCo geoms, not policy inputs or scripted events.
    original_extend=module.extend_xml
    def constrained_extend(xml,spec):
        import xml.etree.ElementTree as ET
        out=original_extend(xml,spec)
        if spec.kind!='push' or os.environ.get('CONSTRAINED_PUSH_CORRIDOR','1')!='1':
            return out
        root=ET.fromstring(out);world=root.find('worldbody')
        def add(name,pos,size,color):
            ET.SubElement(world,'geom',dict(name=name,type='box',pos=' '.join(f'{v:.9g}' for v in pos),
                size=' '.join(f'{v:.9g}' for v in size),rgba=' '.join(f'{v:.9g}' for v in color),
                contype='32',conaffinity='63',friction='.45 .01 .001',solref='.004 .9',
                solimp='.92 .98 .002 .5 2',priority='3'))
        # The hand/pusher corridor is open in x, but bounded in +/-y.
        # Keep the plates out of the nominal pre-grasp link sweep while still
        # closing the forward/backward hand corridor at the push height.
        # End-effector front/back corridor: x is the robot-facing travel axis
        # in this scene. The previous y-separated plates looked like left /
        # right walls in the camera and did not constrain the intended motion.
        # Low solid barriers define the x-direction corridor without putting
        # a tall wall through the upstream FR3 link sweep.  The rod itself is
        # kept at the end-effector height below, so contact is with the hand.
        # Tight x-direction tunnel.  A full-width wall is physically wrong
        # for this FR3 posture because wrist/link7 occupies the same x-z
        # corridor as the hand during approach.  Instead each x stopper is a
        # narrow, padded side rail placed at the hand's negative-y rim.  Its
        # 16-mm y span overlaps hand_collision but stays outside link7's
        # measured y envelope, so it is a real end-effector bumper rather
        # than a collision-mask exception or a scripted gate.
        # The forward bumper is kept outside the wrist sweep; the rear rail
        # is the actual anti-retreat constraint for this protocol.
        fx=float(os.environ.get('GUARD_FRONT_X','.700'))
        bx=float(os.environ.get('GUARD_BACK_X','.500'))
        gy=float(os.environ.get('GUARD_CENTER_Y','-.065'))
        hy=float(os.environ.get('GUARD_HALF_Y','.004'))
        gz=float(os.environ.get('GUARD_Z','.585'))
        hz=float(os.environ.get('GUARD_HALF_Z','.025'))
        hx=float(os.environ.get('GUARD_HALF_X','.018'))
        add('push_front_guard',[fx,gy,gz],[hx,hy,hz],[.18,.28,.42,1.])
        add('push_back_guard',[bx,gy,gz],[hx,hy,hz],[.18,.28,.42,1.])
        return ET.tostring(root,encoding='unicode')
    module.extend_xml=constrained_extend
    original_update=module.BlindTask.update
    def passage_update(self,qpos,qvel,position,rotation,twist):
        delta=position-self.goals[self.index]
        margin=float(os.environ.get('APPROACH_PASSAGE_MARGIN','.008'))
        if (self.index==0 and delta@self.path_direction>margin
                and np.linalg.norm(delta)<.12 and np.linalg.norm(twist[:3])<.18):
            self.previous_goal=self.goals[0].copy();self.index=1;self.ready=0
            self.path_direction=self.direction();return True
        return original_update(self,qpos,qvel,position,rotation,twist)
    module.BlindTask.update=passage_update
    original_environment=module.create_environment
    def environment(args):
        env,task,scene=original_environment(args)
        if os.environ.get('PRINT_BODIES')=='1':
            for name in ('hand','fr3_link5','fr3_link6','fr3_link7'):
                bid=mujoco.mj_name2id(env.model,mujoco.mjtObj.mjOBJ_BODY,name)
                if bid>=0:
                    print('BODY_INIT',name,env.data.xpos[bid].tolist(),flush=True)
        if os.environ.get('PRINT_GEOMS')=='1':
            selected={'hand','fr3_link5','fr3_link6','fr3_link7','left_finger','right_finger','finger_left','finger_right','gripper'}
            for gid in range(env.model.ngeom):
                bid=int(env.model.geom_bodyid[gid])
                body=mujoco.mj_id2name(env.model,mujoco.mjtObj.mjOBJ_BODY,bid) or ''
                if body not in selected:
                    continue
                name=mujoco.mj_id2name(env.model,mujoco.mjtObj.mjOBJ_GEOM,gid) or f'geom_{gid}'
                kind=int(env.model.geom_type[gid])
                size=env.model.geom_size[gid].copy()
                pos=env.data.geom_xpos[gid].copy()
                mat=env.data.geom_xmat[gid].reshape(3,3).copy()
                # Conservative world-axis half extents for box / sphere /
                # capsule-like geoms.  This is used only for geometry audit.
                if kind==int(mujoco.mjtGeom.mjGEOM_BOX):
                    half=np.abs(mat)@size
                elif kind==int(mujoco.mjtGeom.mjGEOM_SPHERE):
                    half=np.repeat(size[0],3)
                else:
                    radius=float(size[0]);half=np.repeat(radius,3)
                    if kind in (int(mujoco.mjtGeom.mjGEOM_CAPSULE),int(mujoco.mjtGeom.mjGEOM_CYLINDER)):
                        half+=np.abs(mat[:,2])*float(size[1])
                print('GEOM_INIT',json.dumps(dict(name=name,body=body,type=kind,
                    size=size.tolist(),position=pos.tolist(),aabb_min=(pos-half).tolist(),
                    aabb_max=(pos+half).tolist())),flush=True)
        if args.scene=='push' and not args.settle_only:
            task.goals=task.goals[:4];task.names=task.names[:4]
            if 'PUSH_LIFT_GOAL_Z' in os.environ:
                task.goals[3]=task.goals[3].copy()
                task.goals[3][2]=float(os.environ['PUSH_LIFT_GOAL_Z'])
            lift_scale=float(os.environ.get('PUSH_LIFT_NOMINAL_SCALE','1'))
            if not 0<lift_scale<=1:raise ValueError('Lift nominal scale must be in (0,1]')
            if lift_scale!=1.:
                original_command=env._wbc_command
                def lift_command(*values,**kwargs):
                    command=original_command(*values,**kwargs)
                    if task.index>=3:
                        return replace(command,joint_velocity_radps=command.joint_velocity_radps*lift_scale,
                                       task_twist_world=command.task_twist_world*lift_scale)
                    return command
                env._wbc_command=lift_command
        return env,task,scene
    module.create_environment=environment
    # Recompile only the primitive runner's ``run`` function after replacing
    # its 3-D teacher call with the 6-D wrench call below.  The module-level
    # environment wrapper above remains in effect.
    text=source.read_text()
    text=text.replace('teacher_force=teacher_force_sensor.copy() if a.teacher_force_source=="ideal" else wrench[:3]',
        'teacher_force=(np.r_[teacher_force_sensor, np.zeros(3)] if a.teacher_force_source=="ideal" else wrench.copy())')
    text=text.replace('expert=teacher.act(teacher_force,error[:3],twist[:3],task.path_direction,RL_DT)',
        'expert=teacher.act(teacher_force,error,twist,task.path_direction,RL_DT)')
    text=text.replace('estimated_force3', 'estimated_wrench6')
    text=text.replace('("primitive_corner","primitive_table_corner","office_cup","office_pillar","push_rod_geom")',
        '("primitive_corner","primitive_table_corner","office_cup","office_pillar","push_rod_geom","push_front_guard","push_back_guard")')
    text=text.replace('("primitive_corner","primitive_table_corner","primitive_free_ball","office_cup","office_pillar")',
        '("primitive_corner","primitive_table_corner","primitive_free_ball","office_cup","office_pillar","push_front_guard","push_back_guard")')
    parsed=ast.parse(text)
    run_node=next(n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    exec(compile(ast.Module(body=[run_node],type_ignores=[]),str(source),'exec'),module.__dict__)
    original_run=module.run
    def audited_run(args):
        if args.scene!='push' or args.teacher_profile!='memory' or args.model:
            raise ValueError('This experiment requires the unlearned core VMC push teacher')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        config=dict(stiffness=args.stiffness,damping=args.damping,**PARAMETERS)
        files=[Path(__file__),source,source.with_name('haptic_vmc_teacher_20260916.py'),
               source.with_name('audited_velocity_env.py')]
        metadata=dict(family='six_d_saturated_virtual_model_controller',config=config,
                      diagonal_parameters={k:PARAMETERS[k]for k in ('stiffness_6d','damping_6d','mass_6d','wrench_limit_6d','axis_rotation_rpy')if k in PARAMETERS},
                      filter_tau=PARAMETERS.get('filter_tau',.06),
                      source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in files},
                      constrained_corridor=True,front_guard_x_m=float(os.environ.get('GUARD_FRONT_X','.700')),
                      back_guard_x_m=float(os.environ.get('GUARD_BACK_X','.500')),
                      guard_center_y_m=float(os.environ.get('GUARD_CENTER_Y','-.065')),
                      guard_half_y_m=float(os.environ.get('GUARD_HALF_Y','.040')),
                      guard_z_m=float(os.environ.get('GUARD_Z','.585')),
                      guard_half_z_m=float(os.environ.get('GUARD_HALF_Z','.025')),
                      new_contact_rules=False,persistent=args.push_hold>args.duration,
                      approach_passage_margin_m=float(os.environ.get('APPROACH_PASSAGE_MARGIN','.008')),
                      lift_goal_z_m=float(os.environ.get('PUSH_LIFT_GOAL_Z','.6879')),
                      lift_nominal_scale=float(os.environ.get('PUSH_LIFT_NOMINAL_SCALE','1')),
                      force_source=args.teacher_force_source)
        args.output.with_name('core_config.json').write_text(json.dumps(metadata,indent=2))
        original_run(args)
        path=args.output.with_suffix('.json');result=json.loads(path.read_text())
        result['core_vmc']=metadata;path.write_text(json.dumps(result,indent=2))
    module.run=audited_run
    tree=ast.parse(source.read_text())
    exec(compile(ast.Module(body=tree.body[-1].body,type_ignores=[]),str(source),'exec'),module.__dict__)


if __name__=='__main__':main()
