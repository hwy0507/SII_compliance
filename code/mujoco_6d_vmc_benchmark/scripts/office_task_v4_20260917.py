"""Office pick/carry/place development benchmark, separate from retired pilots.

Scene geometry is used by simulator/auditor only. The actor receives contact45.
Release is gated by causal load transfer plus known commanded placement pose;
physics truth independently checks support BEFORE opening and AFTER retreat.
Nominal controller is kinematic WBC, not claimed to be the paper MPC planner.
"""
import argparse
from dataclasses import replace
import hashlib,json,os
from pathlib import Path
os.environ.setdefault('MUJOCO_GL','egl')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import xml.etree.ElementTree as ET
import mujoco
import numpy as np
from scipy.optimize import least_squares
from office_contact_scene_20260916 import extend_xml,SceneSpec,geom,numbers
from run_contact_transfer_20260916 import create_environment as legacy_environment, clean
import run_contact_transfer_20260916 as legacy
from haptic_vmc_teacher_20260916 import JointLoadObserver,equivalent_tool_wrench
from contact_transfer_student_20260916 import TransferStudent
from contact_memory_vmc_20260916 import ContactMemoryVMC
from run_benchmark import body_jacobian,body_twist,so3_log

DT=.04
SOURCE=np.array([.54,-.20,.425]);DEST=np.array([.54,.23,.425])


def layout_xml(xml,spec,obstacles,human_push=False,hand_contact_time=.004):
    root=ET.fromstring(extend_xml(xml,replace(spec,kind='empty')))
    world=root.find('worldbody')
    if obstacles:
        # Explicit, disjoint placements. A compound hollow cup stays dynamic.
        cup_source=ET.fromstring(extend_xml(xml,replace(spec,kind='cup')))
        cup=cup_source.find(".//body[@name='office_cup']")
        cup.set('pos',numbers([.465,-.045,.4005]));world.append(cup)
        geom(world,'office_pillar','cylinder',[.610,.075,.585],[.035,.185],[.32,.35,.38,1])
        geom(world,'office_pillar_mount','cylinder',[.610,.075,.407],[.045,.007],[.22,.24,.27,1])
        # Near x face .695 shared exactly; vertical top equals top underside.
        geom(world,'office_corner_face','box',[.705,.215,.535],[.010,.085,.135],[.50,.32,.18,1])
        geom(world,'office_corner_top','box',[.7575,.215,.69],[.0625,.085,.02],[.57,.37,.20,1])
    if human_push:
        body=ET.SubElement(world,'body',name='office_hand',pos=numbers([.33,0.,.60]))
        ET.SubElement(body,'joint',name='office_hand_slide',type='slide',axis='1 0 0',range='0 .20',damping='2')
        geom(body,'office_hand_geom','capsule',[0,0,0],[.025], [.65,.44,.32,1],
             fromto='0 -.04 0 0 .04 0',mass='.4',solref=f'{hand_contact_time} 1',solimp='.95 .99 .0001 .5 2')
    return ET.tostring(root,encoding='unicode')


def make_environment(a):
    # Adapter is process-local and restored immediately after construction.
    original_xml,original_layout=legacy.extend_xml,legacy.task_layout
    legacy.extend_xml=lambda xml,spec:layout_xml(xml,spec,a.obstacles,a.human_push,a.hand_contact_time)
    legacy.task_layout=lambda spec:(SOURCE+np.array([0,0,.195]),SOURCE.copy())
    try:env,_,spec=legacy_environment(a)
    finally:legacy.extend_xml,legacy.task_layout=original_xml,original_layout
    return env


def audit_initial(m,d):
    failures=[]
    for i in range(d.ncon):
        c=d.contact[i];g1,g2=int(c.geom1),int(c.geom2)
        b1,b2=int(m.geom_bodyid[g1]),int(m.geom_bodyid[g2])
        if b1==b2:continue
        if c.dist < -.00001:
            names=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g) or str(g) for g in (g1,g2)]
            failures.append(dict(pair=names,depth_mm=-float(c.dist)*1000))
    if failures:raise ValueError('Initial rigid body intersections: '+json.dumps(failures))


def contact_support(m,d,target,desk):
    for i in range(d.ncon):
        c=d.contact[i]
        if {int(c.geom1),int(c.geom2)}=={target,desk}:
            f=np.zeros(6);mujoco.mj_contactForce(m,d,i,f)
            if f[0]>.05:return True
    return False


class PickPlaceTask:
    def __init__(self,initial,fingers,fdofs,source=None):
        source=SOURCE if source is None else np.asarray(source,dtype=float)
        pickup=source+np.array([0,0,.1029])
        above=source+np.array([0,0,.175])
        carry=DEST+np.array([0,0,.175])
        placement=DEST+np.array([0,0,.0959])
        lift=source+np.array([0,0,.24])
        self.goals=[above,pickup,pickup,lift,carry,placement,placement,carry]
        self.names=['approach','align','grasp','lift','carry','load_transfer','release','retreat']
        self.index=0;self.ready=0.;self.rotation=np.diag([-1.,1.,-1.])
        self.previous_goal=initial.copy();self.path_direction=self.direction()
        self.fingers=fingers;self.fdofs=fdofs;self.gripper=.04
        self.carry_load=None;self.release_load_change=None

    def direction(self):
        v=self.goals[self.index]-self.previous_goal
        return v/max(np.linalg.norm(v),1e-8) if np.linalg.norm(v)>1e-8 else np.array([0.,0.,1.])

    def update(self,q,dq,pos,rot,twist,wrench):
        ready=np.linalg.norm(pos-self.goals[self.index])<.012 and np.linalg.norm(so3_log(self.rotation@rot.T))<.12 and np.linalg.norm(twist[:3])<.025
        if self.index==2:
            ready=ready and .015<sum(q[self.fingers])<.075 and np.linalg.norm(dq[self.fdofs])<.004
        if self.index in (3,4) and np.linalg.norm(twist[:3])<.03:
            self.carry_load=float(wrench[2]) if self.carry_load is None else .95*self.carry_load+.05*float(wrench[2])
        if self.index==5:
            self.release_load_change=float(wrench[2])-(self.carry_load or 0.)
            ready=ready and self.carry_load is not None and self.release_load_change>.4
        if self.index==6:ready=ready and sum(q[self.fingers])>.075
        self.ready=self.ready+DT if ready else 0.
        if self.ready>=.20-1e-9 and self.index<7:
            self.previous_goal=self.goals[self.index].copy();self.index+=1;self.ready=0.;self.path_direction=self.direction()
            return True
        return False

    def sample(self,unused=None):return self.goals[self.index].copy(),self.rotation.copy(),np.zeros(3),np.zeros(3)
    def advance_gripper(self):
        target=.04 if self.index<2 or self.index>=6 else 0.
        self.gripper+=np.clip(target-self.gripper,-.12*DT,.12*DT)
    def gripper_target(self,unused=None):return self.gripper


def run(a):
    if a.output.with_suffix('.json').exists():raise ValueError('Output exists')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    env=make_environment(a);m,d=env.model,env.data
    audit_initial(m,d)
    fingers=[];fdofs=[]
    for n in ('finger_joint1','finger_joint2'):
        j=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,n);fingers.append(m.jnt_qposadr[j]);fdofs.append(m.jnt_dofadr[j])
    task=PickPlaceTask(d.xpos[env._hand_id].copy(),fingers,fdofs)
    env.reference=task;env.gripper_target_override=lambda unused,default:task.gripper_target()
    target=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,'target_object_geom')
    desk=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,'office_desk_top')
    cup=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,'office_cup')
    cup_base=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,'office_cup_base')
    cup_initial=d.xpos[cup].copy() if cup>=0 else np.zeros(3)
    observer=JointLoadObserver(d.qvel.copy(),m.dof_frictionloss);mass=np.zeros((m.nv,m.nv))
    policy=TransferStudent.load(a.model) if a.model else None
    teacher=ContactMemoryVMC() if a.method=='vmc' else None
    robot=set(env._push_audit_robot_geom_ids)
    stats=dict(max_penetration_m=0.,peak_force_n=0.,cup_shift_m=0.,cup_tilt_deg=0.,events={},peak_torque_per_joint=np.zeros(7))
    push_joint=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,'office_hand_slide')
    force_sensor=np.zeros(3);last_force=np.zeros(3)
    def sensor(unused):
        if push_joint>=0:
            # World-side finite-force apparatus; its event clock never enters
            # task progress or actor observations. No reset/teleport at impact.
            elapsed=float(d.time)-9.
            fraction=np.clip(elapsed,0.,1.) if elapsed<1. else 1. if elapsed<5. else np.clip(6.-elapsed,0.,1.)
            target_position=.18*fraction*fraction*(3.-2.*fraction)
            qa=int(m.jnt_qposadr[push_joint]);da=int(m.jnt_dofadr[push_joint])
            # Apply a bounded actuator-equivalent force to the OBSTACLE rail
            # only. Robot motion remains entirely contact-mediated.
            d.qfrc_applied[da]=np.clip(120*(target_position-d.qpos[qa])-8*d.qvel[da],-12,12)
        mujoco.mj_fullM(m,d,mass)
        observer.update(d.qvel.copy(),mass,d.qfrc_bias.copy(),d.qfrc_passive.copy(),d.qfrc_actuator.copy(),m.opt.timestep)
        force=np.zeros(3);by_object={}
        stats['peak_torque_per_joint']=np.maximum(stats['peak_torque_per_joint'],abs(d.qfrc_actuator[:7]))
        for i in range(d.ncon):
            c=d.contact[i];g1,g2=int(c.geom1),int(c.geom2)
            if m.geom_bodyid[g1]!=m.geom_bodyid[g2]:stats['max_penetration_m']=max(stats['max_penetration_m'],-float(c.dist))
            if (g1 in robot)==(g2 in robot):continue
            other=g2 if g1 in robot else g1
            if other==target:continue
            f=np.zeros(6);mujoco.mj_contactForce(m,d,i,f)
            world=c.frame.reshape(3,3).T@f[:3]*(1 if g2 in robot else -1)
            force+=world
            name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,other) or str(other)
            key='cup' if 'cup' in name else 'pillar' if 'pillar' in name else 'corner' if 'corner' in name else 'human_push' if 'office_hand' in name else name
            by_object[key]=by_object.get(key,np.zeros(3))+world
        for key,f in by_object.items():
            mag=float(np.linalg.norm(f))
            if mag>.05:
                rec=stats['events'].setdefault(key,dict(first_s=float(d.time),last_s=float(d.time),duration_s=0.,peak_n=0.,impulse_ns=0.))
                rec['last_s']=float(d.time);rec['duration_s']+=m.opt.timestep;rec['peak_n']=max(rec['peak_n'],mag);rec['impulse_ns']+=mag*m.opt.timestep
        last_force[:]=force;stats['peak_force_n']=max(stats['peak_force_n'],float(np.linalg.norm(force)))
        force_sensor[:]+=(1-np.exp(-m.opt.timestep/.04))*(force-force_sensor)
        if cup>=0:
            stats['cup_shift_m']=max(stats['cup_shift_m'],float(np.linalg.norm((d.xpos[cup]-cup_initial)[:2])))
            stats['cup_tilt_deg']=max(stats['cup_tilt_deg'],float(np.rad2deg(np.arccos(np.clip(d.xmat[cup].reshape(3,3)[2,2],-1,1)))))
    env.substep_observer=sensor
    records=[];events=[];release_truth=None;max_lift=0.;support_hold=0.;placement_time=None
    renderer=None;frames=[]
    if a.render:
        from PIL import Image,ImageDraw
        m.vis.global_.offwidth=960;m.vis.global_.offheight=640
        renderer=mujoco.Renderer(m,height=640,width=960)
        cam=mujoco.MjvCamera();cam.lookat[:]=[.52,.04,.44];cam.distance=1.5;cam.azimuth=140;cam.elevation=-30
    for step in range(round(a.duration/DT)):
        pos=d.xpos[env._hand_id].copy();rot=d.xmat[env._hand_id].reshape(3,3).copy();twist=body_twist(m,d,env._hand_id)
        wrench=equivalent_tool_wrench(body_jacobian(m,d,env._hand_id),observer.filtered)
        previous=task.index
        if task.update(d.qpos[:],d.qvel[:],pos,rot,twist,wrench):events.append(dict(stage=task.names[task.index],time_s=float(d.time)))
        if previous==5 and task.index==6:release_truth=contact_support(m,d,target,desk)
        task.advance_gripper()
        command=env._wbc_command(0.)
        error=np.r_[command.target_position_m-pos,so3_log(command.target_rotation@rot.T)]
        observation=np.r_[d.qpos[:7],d.qvel[:7],command.task_twist_world,error,command.task_twist_world-twist,observer.filtered,wrench[:3],task.path_direction]
        action=policy.act(observation) if policy else teacher.act(force_sensor,error[:3],twist[:3],task.path_direction,DT) if teacher else np.zeros(7)
        env.step(action)
        obj=d.xpos[env._target_body_id].copy();max_lift=max(max_lift,float(obj[2]-SOURCE[2]))
        supported=contact_support(m,d,target,desk)
        settled=supported and np.linalg.norm(d.qvel[env._target_dof:env._target_dof+3])<.015 if hasattr(env,'_target_dof') else supported and np.linalg.norm(d.cvel[env._target_body_id,3:])<.015
        support_hold=support_hold+DT if task.index==7 and settled and np.linalg.norm(obj[:2]-DEST[:2])<.025 else 0.
        if support_hold>=.5 and placement_time is None:placement_time=float(d.time)
        records.append(dict(time=d.time,stage=task.index,position=d.xpos[env._hand_id].copy(),target=task.goals[task.index].copy(),
            object_position=obj,observation=observation,action=action,force=last_force.copy(),torque=d.qfrc_actuator[:7].copy(),
            twist=body_twist(m,d,env._hand_id),cup_position=d.xpos[cup].copy() if cup>=0 else np.zeros(3),
            gripper=task.gripper,load_change=task.release_load_change or 0.,support=supported,qpos=d.qpos.copy()))
        if renderer and step%2==0:
            renderer.update_scene(d,camera=cam);im=Image.fromarray(renderer.render());draw=ImageDraw.Draw(im)
            draw.text((15,15),f'{a.method.upper()} | development | {d.time:.2f}s | {task.names[task.index]}',fill='white')
            frames.append(im)
        if stats['max_penetration_m']>.002:break
    cup_safe=cup<0 or (stats['cup_shift_m']<.02 and stats['cup_tilt_deg']<10 and contact_support(m,d,cup_base,desk)
                       and np.linalg.norm(d.cvel[cup,3:])<.02)
    physical=stats['max_penetration_m']<.0002
    retreat_ok=(np.linalg.norm(d.xpos[env._hand_id]-task.goals[-1])<.015
                and sum(d.qpos[fingers])>.075 and np.linalg.norm(body_twist(m,d,env._hand_id)[:3])<.025)
    done=task.index==7 and support_hold>=.5 and max_lift>.10 and bool(release_truth) and retreat_ok
    result=dict(method=a.method,controller_class=type(env.fixed_wbc).__name__,purpose='development_only',
        success=bool(done and cup_safe and physical),placement_complete=bool(done),cup_safe=bool(cup_safe),physical_valid=physical,
        final_stage=task.names[task.index],release_supported=release_truth,retreat_complete=bool(retreat_ok),release_signal='causal proprioceptive load transfer + known target pose',
        teacher_force_privileged=a.method=='vmc',student_called=policy is not None,events=events,contact=stats,
        object_final=d.xpos[env._target_body_id].copy(),placement_error_m=float(np.linalg.norm(d.xpos[env._target_body_id][:2]-DEST[:2])),
        max_lift_m=max_lift,support_hold_s=support_hold,placement_time_s=placement_time,initial_overlap_audit_passed=True,arguments=vars(a),
        source_sha256={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in
            ('office_task_v4_20260917.py','run_contact_transfer_20260916.py','office_contact_scene_20260916.py','contact_transfer_student_20260916.py')},
        model_sha256=hashlib.sha256(a.model.read_bytes()).hexdigest() if a.model else None)
    a.output.with_suffix('.json').write_text(json.dumps(clean(result),indent=2,allow_nan=False))
    np.savez_compressed(a.output.with_suffix('.npz'),**{k:np.array([r[k] for r in records]) for k in records[0]})
    if frames:
        frames[0].save(a.output.with_suffix('.gif'),save_all=True,append_images=frames[1:],duration=80,loop=0)
        frames[0].save(a.output.with_suffix('.png'))
        import subprocess,imageio_ffmpeg
        command=[imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','960x640','-framerate','12.5',
                 '-i','pipe:0','-an','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(a.output.with_suffix('.mp4'))]
        process=subprocess.Popen(command,stdin=subprocess.PIPE)
        for frame in frames:process.stdin.write(frame.tobytes())
        process.stdin.close()
        if process.wait()!=0:raise RuntimeError('Video encoding failed')
    if renderer:renderer.close()
    env.close();print(json.dumps(clean(result)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--method',choices=('wbc','vmc','mlp','esn'),default='wbc')
    p.add_argument('--model',type=Path);p.add_argument('--obstacles',action='store_true');p.add_argument('--render',action='store_true')
    p.add_argument('--human-push',action='store_true')
    p.add_argument('--hand-contact-time',type=float,default=.004)
    p.add_argument('--duration',type=float,default=50.);p.add_argument('--nominal-speed',type=float,default=.06)
    a=p.parse_args()
    for k,v in dict(scene='empty',seed=171001,yaw=0.,shift=0.,along=0.,width=.05,cup_mass=.3,ball_mass=.2,ball_speed=1.5,
        push_hold=4.,menagerie=Path('../mujoco_menagerie'),dt=.0001,settle_only=False).items():setattr(a,k,v)
    if (a.method in ('mlp','esn'))!=(a.model is not None):raise ValueError('Model required exactly for students')
    run(a)
