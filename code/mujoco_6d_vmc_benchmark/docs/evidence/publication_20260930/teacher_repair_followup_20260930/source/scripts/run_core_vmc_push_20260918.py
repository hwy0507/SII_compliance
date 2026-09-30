"""Original virtual M-D-K dynamics only; persistent apparatus, fixed task.

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


class CoreTeacher:
    def __init__(self,config):
        self.config=config
        options=dict(stiffness=config.stiffness,damping=config.damping,**PARAMETERS)
        self.filter_tau=float(options.pop('filter_tau',.06))
        self.rotation=virtual_frame(options.pop('axis_rotation_rpy',[0.,0.,0.]))
        k=options.pop('stiffness_xyz',None);b=options.pop('damping_xyz',None)
        fixed=HapticVMCConfig(**options)
        self.base=HapticVMC(fixed) if k is None else DiagonalVirtualDynamics(fixed,k,b)
        self.filtered_force=np.zeros(3)
        self.slide=0.

    def act(self,force,position_error,velocity,path_direction,dt=.04):
        self.filtered_force+=(1.-np.exp(-dt/max(self.filter_tau,1e-6)))*(np.asarray(force)-self.filtered_force)
        action=self.base.act(self.rotation.T@self.filtered_force,dt)
        action[1:4]=np.clip(self.rotation@action[1:4],-1.,1.)
        return action


def main():
    source=Path(__file__).with_name('run_primitive_teacher_v7_20260917.py')
    spec=importlib.util.spec_from_file_location('primitive_v7_core',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.ContactMemoryVMC=CoreTeacher
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
    original_run=module.run
    def audited_run(args):
        if args.scene!='push' or args.teacher_profile!='memory' or args.model:
            raise ValueError('This experiment requires the unlearned core VMC push teacher')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        config=HapticVMCConfig(stiffness=args.stiffness,damping=args.damping,
                              **{k:v for k,v in PARAMETERS.items() if k not in ('filter_tau','stiffness_xyz','damping_xyz','axis_rotation_rpy')})
        files=[Path(__file__),source,source.with_name('haptic_vmc_teacher_20260916.py'),
               source.with_name('audited_velocity_env.py')]
        metadata=dict(family='original_virtual_mass_spring_damper',config=asdict(config),
                      diagonal_parameters={k:PARAMETERS[k]for k in ('stiffness_xyz','damping_xyz','axis_rotation_rpy')if k in PARAMETERS},
                      filter_tau=PARAMETERS.get('filter_tau',.06),
                      source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in files},
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
