"""Audited primitive-v7 VMC-teacher rollout for source-domain collection.

All learned/teacher inputs are explicitly assembled before the simulator step.
No environment objects, world geometry, contact oracle or clock cross that API.
"""
import argparse
from dataclasses import asdict,replace
import hashlib
import json
import os
from pathlib import Path
os.environ.setdefault("MUJOCO_GL","egl")
os.environ.setdefault("OPENBLAS_NUM_THREADS","1")
os.environ.setdefault("OMP_NUM_THREADS","1")
import mujoco
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.optimize import least_squares
from audited_velocity_env import PandaWBCVelocityResidualEnv,VelocityResidualFixture,RL_DT
from wbc_velocity_residual_core import VelocityResidualSafetyConfig
from fixed_panda_wbc import FixedBasePandaWBC,FixedBasePandaWBCConfig
from run_benchmark import body_jacobian,body_twist,so3_log
from haptic_vmc_teacher_20260916 import JointLoadObserver,equivalent_tool_wrench
from contact_memory_vmc_20260916 import ContactMemoryVMC,ContactMemoryConfig
from low_force_vmc_20260917 import LowForceVMC
from primitive_contact_scene_v7_20260917 import SceneSpec,extend_xml,task_layout


STAGE_INDEX={"approach":0,"pregrasp":1,"loaded_lift":3,"carry":4,"recovery":5}


def clean(value):
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple,set)):return [clean(v) for v in value]
    if isinstance(value,np.ndarray):return clean(value.tolist())
    if isinstance(value,np.generic):return clean(value.item())
    if isinstance(value,Path):return str(value)
    if isinstance(value,float) and not np.isfinite(value):return None
    return value


class BlindTask:
    def __init__(self,initial,grasp,rotation,hand,fingers,finger_dofs,settle=False,extended=True):
        lifted=grasp+np.array([0,0,.2629])
        self.goals=[grasp+np.array([0,0,.175]),grasp+np.array([0,0,.1029]),
                    grasp+np.array([0,0,.1029]),lifted]
        self.names=["REACH / CONTACT RESPONSE","ALIGN TO GRASP","CLOSE GRIPPER","LOADED LIFT"]
        if extended:
            self.goals.extend([lifted+np.array([.085,.035,0.]),lifted])
            self.names.extend(["CARRY","RECOVERY"])
        if settle:self.goals=[initial.copy()];self.names=["STATIC SCENE CHECK"]
        self.index=0;self.ready=0;self.rotation=rotation;self.hand=hand
        self.gripper_command=.040
        self.fingers=fingers;self.finger_dofs=finger_dofs;self.previous_goal=initial.copy()
        self.path_direction=self.direction()

    def direction(self):
        v=self.goals[self.index]-self.previous_goal
        if np.linalg.norm(v)<1e-8:return np.array([0.,0.,1.])
        return v/np.linalg.norm(v)

    def update(self,qpos,qvel,position,rotation,twist):
        ready=np.linalg.norm(position-self.goals[self.index])<.012 and np.linalg.norm(so3_log(self.rotation@rotation.T))<.12 and np.linalg.norm(twist[:3])<.035
        if self.index==2:
            ready=ready and .015<sum(qpos[self.fingers])<.075 and np.linalg.norm(qvel[self.finger_dofs])<.003
        self.ready=self.ready+1 if ready else 0
        if self.ready>=5 and self.index<len(self.goals)-1:
            self.previous_goal=self.goals[self.index].copy();self.index+=1;self.ready=0
            self.path_direction=self.direction();return True
        return False

    def sample(self,_unused=None):return self.goals[self.index].copy(),self.rotation.copy(),np.zeros(3),np.zeros(3)
    def advance_gripper(self,dt):
        target=.040 if self.index<2 else 0.
        self.gripper_command+=float(np.clip(target-self.gripper_command,-.12*dt,.12*dt))

    def gripper_target(self,_unused=None):return self.gripper_command


class TableCornerTask(BlindTask):
    """Under-table grasp, diagonal apron contact, slide-over and placement."""

    def __init__(self,initial,grasp,rotation,hand,fingers,finger_dofs,settle=False):
        super().__init__(initial,grasp,rotation,hand,fingers,finger_dofs,settle=settle,extended=False)
        if settle:
            return
        under=grasp+np.array([.015,0.,.135])
        # Stay below the tabletop underside while moving into the hanging
        # apron.  This prevents link 6 from striking the tabletop first and
        # makes the intended lower-face contact visible from the side camera.
        contact=grasp+np.array([.140,0.,.125])
        slide=grasp+np.array([.150,0.,.365])
        # The grasped block center sits about 108 mm below the hand.  A hand
        # target at z=.83 therefore places the block at z≈.722, immediately
        # above the tabletop surface z=.695 before physical settling.
        place=np.array([.84,0.,.83])
        retreat=np.array([.68,0.,.84])
        self.goals=[grasp+np.array([0,0,.175]),grasp+np.array([0,0,.1029]),
                    grasp+np.array([0,0,.1029]),under,contact,slide,place,place,retreat]
        self.names=["REACH BELOW TABLE","ALIGN TO GRASP","CLOSE GRIPPER",
                    "LOADED LIFT BELOW APRON","APRON CONTACT","SLIDE OVER EDGE",
                    "PLACE ON TABLE","RELEASE / SETTLE","RETREAT"]

    def advance_gripper(self,dt):
        target=.040 if self.index<2 or self.index>=7 else 0.
        self.gripper_command+=float(np.clip(target-self.gripper_command,-.12*dt,.12*dt))

    def update(self,qpos,qvel,position,rotation,twist):
        ready=np.linalg.norm(position-self.goals[self.index])<.012 and np.linalg.norm(so3_log(self.rotation@rotation.T))<.12 and np.linalg.norm(twist[:3])<.035
        if self.index==2:
            ready=ready and .015<sum(qpos[self.fingers])<.075 and np.linalg.norm(qvel[self.finger_dofs])<.003
        if self.index==7:
            ready=ready and sum(qpos[self.fingers])>.065 and np.linalg.norm(qvel[self.finger_dofs])<.004
        self.ready=self.ready+1 if ready else 0
        if self.ready>=5 and self.index<len(self.goals)-1:
            self.previous_goal=self.goals[self.index].copy();self.index+=1;self.ready=0
            self.path_direction=self.direction();return True
        return False


class ScaledReferenceWBC(FixedBasePandaWBC):
    def command(self,*args,feedback_scale=1.,**kwargs):
        # Slowdown must scale a bounded command, not disappear inside its
        # speed saturation when the arm is far from the task goal.
        command=super().command(*args,feedback_scale=1.,**kwargs)
        return replace(command,joint_velocity_radps=command.joint_velocity_radps*feedback_scale,
                       task_twist_world=command.task_twist_world*feedback_scale)


def create_environment(a):
    along=getattr(a,"along",None)
    if along is None:along=0.
    stage_push_target={"approach":np.array([.54,0.]),"pregrasp":np.array([.54,0.]),
                       "loaded_lift":np.array([.54,0.]),"carry":np.array([.625,.035]),
                       "recovery":np.array([.600,.020])}[a.event_stage]
    push_target_x=stage_push_target[0] if a.push_target_x is None else a.push_target_x
    push_target_y=stage_push_target[1] if a.push_target_y is None else a.push_target_y
    stage_ball_target={"approach":np.array([.54,0.,.62]),"pregrasp":np.array([.54,0.,.53]),
                       "loaded_lift":np.array([.54,0.,.60]),"carry":np.array([.625,.035,.688]),
                       "recovery":np.array([.600,.020,.688])}[a.event_stage]
    ball_target_x=stage_ball_target[0] if a.ball_target_x is None else a.ball_target_x
    ball_target_y=stage_ball_target[1] if a.ball_target_y is None else a.ball_target_y
    ball_target_z=stage_ball_target[2] if a.ball_target_z is None else a.ball_target_z
    spec=SceneSpec(kind=a.scene,yaw=a.yaw,shift=a.shift,along=along,width=a.width,cup_mass=a.cup_mass,
                   ball_mass=a.ball_mass,ball_speed=a.ball_speed,ball_angle=a.ball_angle,
                   ball_height_offset=a.ball_height_offset,ball_vertical_speed=a.ball_vertical_speed,
                   ball_target_x=ball_target_x,ball_target_y=ball_target_y,ball_target_z=ball_target_z,
                   ball_radius=a.ball_radius,ball_shell=a.ball_shell,ball_contact_time=a.ball_contact_time,
                   ball_contact_damping=a.ball_contact_damping,
                   push_angle=a.push_angle,
                   push_height=a.push_height,push_stroke=a.push_stroke,corner_height=a.corner_height,
                   push_target_x=push_target_x,push_target_y=push_target_y,
                   corner_friction=a.corner_friction,payload_mass=a.payload_mass,seed=a.seed)
    os.environ.update(THICK_TABLE_SCENE="1",EXTRACTION_TABLE="1",PUSH_FULL_RIGID_CONTACTS="1",
        HAPTIC_BALL_FULL_CONTACTS="1",TARGET_TABLE_AFFINITY="63",PUSH_ROD_SCENE="1" if a.scene in ("push","complex") else "0",
        PUSH_ROD_CENTER_X=".54",PUSH_ROD_CENTER_Z=str(a.push_height),PUSH_ROD_DRIVER_KP="160",
        PUSH_ROD_DRIVER_FORCE_LIMIT_N=str(a.push_force),PUSH_ROD_JOINT_DAMPING="20",
        PUSH_ROD_SOLREF_TIME_S=".0015",PUSH_ROD_SOLIMP_MIN=".95",PUSH_ROD_SOLIMP_MAX=".995",
        PUSH_ROD_SOLIMP_WIDTH_M=".0002",PUSH_ROD_CONTACT_PRIORITY="2",PUSH_ROD_START_S="1000000",
        PUSH_ROD_PRESS_S=str(a.push_press),PUSH_ROD_HOLD_S=str(a.push_hold),
        PUSH_ROD_RETRACT_S=str(a.push_retract),PUSH_ROD_STROKE_M=str(a.push_stroke))
    env=PandaWBCVelocityResidualEnv(menagerie=a.menagerie,fan_ye_model_npz=None,fan_ye_train_summary_json=None,
        observation_mode="direct_esn",fixtures=(VelocityResidualFixture(.1,.53,1.8,contact_time_constant_s=.001),),
        rod_enabled=False,robot="fr3",wbc_backend="paper_mpc",execution_mode="twist",seed=a.seed,
        safety_config=VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32),grasp_retention_mode="off",
        simulation_time_s=a.duration,scene_transform=lambda xml:extend_xml(xml,spec))
    env.reset(seed=a.seed,options={"fixture_index":0})
    m,d=env.model,env.data;m.opt.timestep=a.dt;m.opt.solver=mujoco.mjtSolver.mjSOL_NEWTON
    if a.scene=="ball":m.opt.timestep=min(a.dt,max(.000025,a.ball_contact_time/40.))
    elif a.scene=="push":m.opt.timestep=min(a.dt,.00005)
    # Legacy keyframe has only the arm/finger coordinates. New free bodies
    # must start at their compiled physical placement, not padded zero pose.
    for j in range(m.njnt):
        if m.jnt_type[j]==mujoco.mjtJoint.mjJNT_FREE:
            adr=m.jnt_qposadr[j];d.qpos[adr:adr+7]=m.qpos0[adr:adr+7]
    m.opt.iterations=1000;m.opt.tolerance=1e-10;m.opt.ccd_iterations=1000;m.opt.ccd_tolerance=1e-10
    m.opt.disableflags=int(m.opt.disableflags)|int(mujoco.mjtDisableBit.mjDSBL_NATIVECCD)
    initial,goal=task_layout(spec);rotation=np.diag([-1.,1.,-1.])
    scratch=mujoco.MjData(m);scratch.qpos[:]=d.qpos;seedq=d.qpos[:7].copy()
    def residual(q):
        scratch.qpos[:7]=q;mujoco.mj_forward(m,scratch)
        return np.r_[scratch.xpos[env._hand_id]-initial,.08*(scratch.xmat[env._hand_id].reshape(3,3)-rotation).ravel(),.0001*(q-seedq)]
    ik=least_squares(residual,seedq,max_nfev=800,bounds=(m.jnt_range[:7,0],m.jnt_range[:7,1]))
    if np.linalg.norm(residual(ik.x)[:3])>.002:raise RuntimeError("Initial pose IK failed")
    d.qpos[:7]=ik.x;d.qvel[:7]=0.
    target_q=env._target_qpos;d.qpos[target_q:target_q+7]=np.r_[goal,1,0,0,0]
    fingers=[];fdofs=[]
    for n in ("finger_joint1","finger_joint2"):
        j=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,n)
        fingers.append(m.jnt_qposadr[j]);fdofs.append(m.jnt_dofadr[j]);d.qpos[m.jnt_qposadr[j]]=.04
    if a.scene in ("ball","complex"):
        j=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,"primitive_free_ball_joint")
        d.qvel[m.jnt_dofadr[j]:m.jnt_dofadr[j]+6]=0.
        m.body_gravcomp[m.jnt_bodyid[j]]=1.
    mujoco.mj_forward(m,d)
    for i in range(d.ncon):
        c=d.contact[i];names=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,int(g)) or "" for g in (c.geom1,c.geom2)]
        primary=any(n.startswith(("primitive_corner","primitive_table_corner","office_cup","office_pillar","push_rod_geom")) for n in names)
        arm=any(int(g) in env._push_audit_robot_geom_ids for g in (c.geom1,c.geom2))
        if primary and arm and c.dist<-.00001:raise ValueError(f"Initial robot/obstacle overlap: {names}, {c.dist}")
    env.previous_torque=d.qfrc_bias[:7].copy()
    task=(TableCornerTask(initial,goal,rotation,env._hand_id,fingers,fdofs,a.settle_only)
          if a.scene=="table_corner" else
          BlindTask(initial,goal,rotation,env._hand_id,fingers,fdofs,a.settle_only,extended=a.scene!="corner"))
    env.reference=task;env.gripper_target_override=lambda unused,default:task.gripper_target()
    env.fixed_wbc=ScaledReferenceWBC(m,env._hand_id,ik.x,FixedBasePandaWBCConfig(
        position_feedback_gain=2.5*12/13,orientation_feedback_gain=2.3,max_linear_speed_mps=getattr(a,"nominal_speed",.08),
        max_angular_speed_radps=.5,nullspace_posture_gain=.1))
    return env,task,spec


def run(a):
    a.output.parent.mkdir(parents=True,exist_ok=True)
    env,task,spec=create_environment(a);m,d=env.model,env.data
    tangent_speed=a.tangent_speed
    if tangent_speed is None:tangent_speed=0. if a.scene in ("ball","push") else .065
    teacher_config=ContactMemoryConfig(stiffness=a.stiffness,damping=a.damping,
        force_on=a.force_on,tangent_speed=tangent_speed,contact_tau=a.contact_tau,
        release_tau=a.release_tau,memory_tau=a.memory_tau)
    teacher=(LowForceVMC(teacher_config,force_target=a.force_target,normal_gain=a.normal_gain)
             if a.teacher_profile=="low_force" else ContactMemoryVMC(teacher_config))
    policy=None
    if a.model:
        from current_student_policy_20260921 import load_current
        policy=load_current(a.model)
    observer=JointLoadObserver(d.qvel.copy(),m.dof_frictionloss);mass=np.zeros((m.nv,m.nv))
    robot=set(env._push_audit_robot_geom_ids)
    objects={g for g in range(m.ngeom) if (mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g) or "").startswith(("primitive_corner","primitive_table_corner","primitive_free_ball","office_cup","office_pillar"))}
    if env._push_rod_geom_id>=0:objects.add(env._push_rod_geom_id)
    audit=dict(peak_force_n=0.,all_external_peak_force_n=0.,peak_body_resultant_n=0.,max_penetration_m=0.,
        all_external_max_penetration_m=0.,grasp_penetration_m=0.,duration_s=0.,first_s=None,last_s=None,
        first_stage=None,first_stage_name=None,first_payload_held=None,contact_path_direction=None,pairs=set(),robot_geoms=set(),
        robot_bodies=set(),force=np.zeros(3),impulse_vector_ns=np.zeros(3),contact_impulse_ns=0.,
        ball_core_min_distance_m=float("inf"),
        other_contacts=set())
    teacher_force_sensor=np.zeros(3)
    def sensor_and_audit(_unused):
        nonlocal cup_shift,cup_tilt
        mujoco.mj_fullM(m,d,mass)
        observer.update(d.qvel.copy(),mass,d.qfrc_bias.copy(),d.qfrc_passive.copy(),d.qfrc_actuator.copy(),m.opt.timestep)
        force=np.zeros(3);all_external_force=np.zeros(3);touch=False;body_forces={}
        for i in range(d.ncon):
            c=d.contact[i];g1,g2=int(c.geom1),int(c.geom2)
            if (g1 in robot)!=(g2 in robot):
                other=g2 if g1 in robot else g1
                # Privileged teacher load channel excludes the known grasp
                # target's intentional grip/support forces. Students never
                # receive this body-identity separation or the ideal force.
                if m.geom_bodyid[other]!=env._target_body_id:
                    f_sensor=np.zeros(6);mujoco.mj_contactForce(m,d,i,f_sensor)
                    world_force=(c.frame.reshape(3,3).T@f_sensor[:3])*(1 if g2 in robot else -1)
                    all_external_force+=world_force
                    body=int(m.geom_bodyid[g2 if g2 in robot else g1])
                    body_forces[body]=body_forces.get(body,np.zeros(3))+world_force
                    audit["all_external_max_penetration_m"]=max(audit["all_external_max_penetration_m"],-float(c.dist))
                else:audit["grasp_penetration_m"]=max(audit["grasp_penetration_m"],-float(c.dist))
                if other not in objects and m.geom_bodyid[other]!=env._target_body_id:
                    audit["other_contacts"].add(mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,other) or str(other))
            if (g1 in robot and g2 in objects) or (g2 in robot and g1 in objects):
                f=np.zeros(6);mujoco.mj_contactForce(m,d,i,f)
                force+=(c.frame.reshape(3,3).T@f[:3])*(1 if g1 in objects else -1)
                audit["max_penetration_m"]=max(audit["max_penetration_m"],-float(c.dist))
                obstacle_name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g2 if g1 in robot else g1) or ""
                if obstacle_name.startswith("primitive_free_ball") and obstacle_name!="primitive_free_ball_visual":
                    audit["ball_core_min_distance_m"]=min(audit["ball_core_min_distance_m"],float(c.dist))
                if np.linalg.norm(f[:3])>.05:
                    touch=True;audit["pairs"].add((mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g1) or str(g1),mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g2) or str(g2)))
                    robot_geom=g1 if g1 in robot else g2
                    audit["robot_geoms"].add(mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,robot_geom) or str(robot_geom))
                    robot_body=int(m.geom_bodyid[robot_geom])
                    audit["robot_bodies"].add(mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,robot_body) or str(robot_body))
        audit["force"]=force;audit["peak_force_n"]=max(audit["peak_force_n"],float(np.linalg.norm(force)))
        audit["impulse_vector_ns"]+=force*m.opt.timestep
        audit["contact_impulse_ns"]+=float(np.linalg.norm(force))*m.opt.timestep
        audit["all_external_peak_force_n"]=max(audit["all_external_peak_force_n"],float(np.linalg.norm(all_external_force)))
        audit["peak_body_resultant_n"]=max(audit["peak_body_resultant_n"],max((float(np.linalg.norm(f)) for f in body_forces.values()),default=0.))
        teacher_force_sensor[:]+=(1.-np.exp(-m.opt.timestep/.04))*(all_external_force-teacher_force_sensor)
        if cup>=0:
            cup_shift=max(cup_shift,float(np.linalg.norm((d.xpos[cup]-cup_initial)[:2])))
            cup_tilt=max(cup_tilt,float(np.arccos(np.clip(d.xmat[cup].reshape(3,3)[2,2],-1,1))))
        if touch:
            audit["duration_s"]+=m.opt.timestep;audit["last_s"]=float(d.time)
            if audit["first_s"] is None:
                audit["first_s"]=float(d.time);audit["first_stage"]=int(task.index)
                audit["first_stage_name"]=task.names[task.index]
                audit["contact_path_direction"]=task.path_direction.copy()
                object_distance=float(np.linalg.norm(d.xpos[env._target_body_id]-d.xpos[env._hand_id]))
                audit["first_payload_held"]=bool(task.index>=2 and object_distance<.13 and sum(d.qpos[task.fingers])<.075)
    env.substep_observer=sensor_and_audit
    cup=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,"office_cup")
    cup_initial=d.xpos[cup].copy() if cup>=0 else None
    cup_shift=0.;cup_tilt=0.;frames=[];records=[];events=[];invalid=False
    requested_stage=STAGE_INDEX[a.event_stage]
    fixture_triggered=False;fixture_trigger_time=None;ball_launched=False
    ball_joint=-1;ball_dof=-1;ball_qpos=-1;ball_body=-1;ball_launch_state=None
    if a.scene=="ball":
        ball_joint=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,"primitive_free_ball_joint")
        ball_dof=int(m.jnt_dofadr[ball_joint]);ball_qpos=int(m.jnt_qposadr[ball_joint]);ball_body=int(m.jnt_bodyid[ball_joint])
    if a.render:
        m.vis.global_.offwidth=640;m.vis.global_.offheight=480
        renderer=mujoco.Renderer(m,height=480,width=640)
        cam=mujoco.MjvCamera();cam.type=mujoco.mjtCamera.mjCAMERA_FREE
        cam.lookat[:]=[.44,0.,.34];cam.distance=1.6;cam.azimuth=135;cam.elevation=-28
        close_cam=mujoco.MjvCamera();close_cam.type=mujoco.mjtCamera.mjCAMERA_FREE
        if a.scene=="table_corner":
            cam.lookat[:]=[.50,0.,.48];cam.distance=1.55;cam.azimuth=135;cam.elevation=-22
            close_cam.lookat[:]=[.70,0.,.64];close_cam.distance=.82;close_cam.azimuth=90;close_cam.elevation=-8
        elif a.scene=="push":
            # Oblique side view: the rod axis, contact patch, normal yielding
            # and tangential slip all remain visible in the same panel.
            close_cam.lookat[:]=[.55,-.01,.56];close_cam.distance=.78;close_cam.azimuth=140;close_cam.elevation=-12
        else:
            close_cam.lookat[:]=[.54,.025,.54];close_cam.distance=.90;close_cam.azimuth=90;close_cam.elevation=-60
        font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",17)
    for step in range(round(a.duration/RL_DT)):
        position=d.xpos[env._hand_id].copy();rotation=d.xmat[env._hand_id].reshape(3,3).copy()
        twist=body_twist(m,d,env._hand_id)
        if not fixture_triggered and task.index>=requested_stage:
            fixture_triggered=True;fixture_trigger_time=float(d.time+a.event_delay)
            if a.scene=="push":os.environ["PUSH_ROD_START_S"]=str(fixture_trigger_time)
        phase_locked=False
        if fixture_triggered and task.index==requested_stage:
            if a.scene=="ball":
                phase_locked=audit["first_s"] is None or d.time<audit["first_s"]+.60
            # Do not lock push progression to the scripted rod schedule.  The
            # rod still needs an external start time to create the disturbance,
            # but neither the VMC action nor the task state machine may wait for
            # the known retract time.  Progress under a sustained push must be
            # earned from the robot's own pose/twist/force response.
        if not phase_locked and task.update(d.qpos,d.qvel,position,rotation,twist):
            events.append(dict(t=float(d.time),stage=task.index))
            if not fixture_triggered and task.index>=requested_stage:
                fixture_triggered=True;fixture_trigger_time=float(d.time+a.event_delay)
                if a.scene=="push":os.environ["PUSH_ROD_START_S"]=str(fixture_trigger_time)
        if a.scene=="ball" and fixture_triggered and not ball_launched and d.time+1e-12>=fixture_trigger_time:
            direction=np.array([np.sin(a.ball_angle),np.cos(a.ball_angle),0.])
            travel_y=.32
            flight_time=travel_y/(a.ball_speed*np.cos(a.ball_angle))
            target=position+np.array([a.shift,0.,a.ball_height_offset])
            proposed_launch_z=target[2]-a.ball_vertical_speed*flight_time+4.905*flight_time**2
            launch_z=max(.455,proposed_launch_z)
            actual_vertical_speed=(target[2]-launch_z+4.905*flight_time**2)/flight_time
            launch=np.array([target[0]-np.tan(a.ball_angle)*travel_y,
                             target[1]-travel_y,
                             launch_z])
            d.qpos[ball_qpos:ball_qpos+7]=np.r_[launch,1.,0.,0.,0.]
            d.qvel[ball_dof:ball_dof+3]=a.ball_speed*direction
            d.qvel[ball_dof+2]=actual_vertical_speed
            m.body_gravcomp[ball_body]=0.;mujoco.mj_forward(m,d);ball_launched=True
            ball_launch_state=dict(time_s=float(d.time),launch_position_m=launch,
                                   target_position_m=target,launch_velocity_mps=d.qvel[ball_dof:ball_dof+3].copy(),
                                   requested_vertical_speed_mps=a.ball_vertical_speed,
                                   launch_height_clamped_for_table_clearance=bool(launch_z>proposed_launch_z+1e-12),
                                   target_was_actual_hand_position=True)
        task.advance_gripper(RL_DT)
        command=env._wbc_command(0.);error=np.r_[command.target_position_m-position,so3_log(command.target_rotation@rotation.T)]
        wrench=equivalent_tool_wrench(body_jacobian(m,d,env._hand_id),observer.filtered)
        observation=np.r_[d.qpos[:7],d.qvel[:7],command.task_twist_world,error,command.task_twist_world-twist,observer.filtered,wrench[:3],task.path_direction]
        teacher_force=teacher_force_sensor.copy() if a.teacher_force_source=="ideal" else wrench[:3]
        if (policy is None or a.mixture>0) and a.teacher_profile!="none":
            if a.teacher_profile=="low_force":
                expert=teacher.act(teacher_force,error[:3],twist[:3],task.path_direction,RL_DT,
                                   nominal_velocity=command.task_twist_world[:3])
            else:
                expert=teacher.act(teacher_force,error[:3],twist[:3],task.path_direction,RL_DT)
        else:
            expert=np.zeros(7)
        if policy is None:action=expert
        elif a.mixture>0:action=a.mixture*expert+(1.-a.mixture)*policy.act(observation)
        else:action=policy.act(observation)
        if a.settle_only:action=np.zeros(7)
        env.step(action)
        if cup>=0:
            cup_shift=max(cup_shift,float(np.linalg.norm((d.xpos[cup]-cup_initial)[:2])))
            cup_tilt=max(cup_tilt,float(np.arccos(np.clip(d.xmat[cup].reshape(3,3)[2,2],-1,1))))
        records.append(dict(time=float(d.time),observation=observation,teacher_action=expert,action=action,teacher_force=teacher_force,
            stage=task.index,position=d.xpos[env._hand_id].copy(),target=task.goals[task.index].copy(),
            force=audit["force"].copy(),twist=body_twist(m,d,env._hand_id),object_position=d.xpos[env._target_body_id].copy(),
            torque=d.qfrc_actuator[:7].copy(),cup_shift=cup_shift,cup_tilt=cup_tilt,slide_memory=teacher.slide))
        records[-1]["cup_position"]=d.xpos[cup].copy() if cup>=0 else np.zeros(3)
        records[-1]["ball_position"]=(d.xpos[ball_body].copy() if ball_body>=0 else np.zeros(3))
        records[-1]["ball_velocity"]=(d.cvel[ball_body,3:6].copy() if ball_body>=0 else np.zeros(3))
        if a.render:
            renderer.update_scene(d,camera=cam);overview=Image.fromarray(renderer.render())
            renderer.update_scene(d,camera=close_cam);detail=Image.fromarray(renderer.render())
            im=Image.new("RGB",(1280,532),(15,22,30));im.paste(overview,(0,52));im.paste(detail,(640,52));draw=ImageDraw.Draw(im)
            draw.text((12,5),f'{a.scene} | {"VMC teacher" if policy is None else policy.kind.upper()} | force feedback only',font=font,fill="white")
            recent_contact=audit["last_s"] is not None and d.time-audit["last_s"]<=RL_DT
            draw.text((12,28),f'{d.time:.2f}s  {task.names[task.index]}  {"CONTACT" if recent_contact else ""}  force now={np.linalg.norm(audit["force"]):.2f} N',font=font,fill=(255,195,90) if recent_contact else (170,220,210));frames.append(im)
        if audit["max_penetration_m"]>.002:invalid=True;break
    arr={k:np.asarray([r[k] for r in records]) for k in records[0]}
    error=np.linalg.norm(arr["position"]-arr["target"],axis=1)
    impact_metrics=dict(max_lateral_displacement_m=0.,max_total_displacement_m=0.,
                        recovery_time_s=None,contact_impulse_ns=float(np.linalg.norm(audit["impulse_vector_ns"])),
                        accumulated_contact_impulse_ns=float(audit["contact_impulse_ns"]))
    if a.scene=="ball":
        minimum=float(audit["ball_core_min_distance_m"])
        audit["ball_shell_compression_m"]=(max(0.,float(a.ball_shell)-minimum) if np.isfinite(minimum) else 0.)
        audit["rigid_core_overlap_m"]=(max(0.,-minimum) if np.isfinite(minimum) else 0.)
    if audit["first_s"] is not None:
        start=int(np.searchsorted(arr["time"],audit["first_s"],side="left"))
        contact_stage=int(arr["stage"][start])
        stage_changes=np.flatnonzero(arr["stage"][start:]!=contact_stage)
        stop=(start+int(stage_changes[0])) if len(stage_changes) else int(np.searchsorted(arr["time"],audit["first_s"]+6.,side="right"))
        stop=max(stop,start+1);anchor=arr["position"][start].copy()
        direction=np.asarray(audit["contact_path_direction"],dtype=float);direction/=max(np.linalg.norm(direction),1e-9)
        delta=arr["position"][start:stop]-anchor
        lateral=delta-np.outer(delta@direction,direction)
        lateral_norm=np.linalg.norm(lateral,axis=1);total_norm=np.linalg.norm(delta,axis=1)
        peak=int(np.argmax(lateral_norm));peak_value=float(lateral_norm[peak])
        impact_metrics["max_lateral_displacement_m"]=peak_value
        impact_metrics["max_total_displacement_m"]=float(np.max(total_norm))
        # "Recovered" means re-entering a 10-mm path corridor, not returning
        # to the exact sub-millimetre contact sample while the nominal task is
        # itself moving.  Three consecutive 25-Hz samples are required.
        threshold=max(.010,.3*peak_value)
        for j in range(peak+1,len(lateral_norm)-2):
            if np.all(lateral_norm[j:j+3]<=threshold):
                impact_metrics["recovery_time_s"]=float(arr["time"][start+j]-arr["time"][start+peak]);break
    push_metrics=dict(contact_sample_fraction=0.,normal_yield_m=0.,tangential_travel_m=0.,
                      path_progress_m=0.,stage_advanced_during_contact=False,
                      error_reduction_during_contact_m=0.)
    if a.scene=="push" and audit["first_s"] is not None:
        contact_norm=np.linalg.norm(arr["force"],axis=1)
        contact_samples=np.flatnonzero(contact_norm>.05)
        if len(contact_samples):
            first,last=int(contact_samples[0]),int(contact_samples[-1])
            span=np.arange(first,last+1)
            push_metrics["contact_sample_fraction"]=float(np.mean(contact_norm[span]>.05))
            anchor=arr["position"][first].copy()
            delta=arr["position"][span]-anchor
            push_direction=np.array([np.sin(a.push_angle),-np.cos(a.push_angle),0.])
            normal_projection=delta@push_direction
            tangent_delta=delta-np.outer(normal_projection,push_direction)
            path_direction=np.asarray(audit["contact_path_direction"],dtype=float)
            path_direction/=max(np.linalg.norm(path_direction),1e-9)
            push_metrics["normal_yield_m"]=float(max(0.,np.max(normal_projection)))
            push_metrics["tangential_travel_m"]=float(np.max(np.linalg.norm(tangent_delta,axis=1)))
            push_metrics["path_progress_m"]=float(max(0.,np.max(delta@path_direction)))
            push_metrics["stage_advanced_during_contact"]=bool(np.max(arr["stage"][span])>arr["stage"][first])
            path_error=np.linalg.norm(arr["position"][span]-arr["target"][span],axis=1)
            peak_error=int(np.argmax(path_error))
            if peak_error+1<len(path_error):
                push_metrics["error_reduction_during_contact_m"]=float(max(0.,path_error[peak_error]-np.min(path_error[peak_error:])))
    lift=float(arr["object_position"][-1,2]-.425)
    motion=float(np.max(np.linalg.norm(np.diff(arr["object_position"][-10:],axis=0)/RL_DT,axis=1))) if len(records)>1 else float("inf")
    payload_top_support=False
    for i in range(d.ncon):
        c=d.contact[i];names={mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,int(g)) or "" for g in (c.geom1,c.geom2)}
        if "target_object_geom" in names and "primitive_table_corner_top" in names:
            payload_top_support=True;break
    upstream_contact=bool(set(audit.get("robot_bodies",set())) & {"fr3_link0","fr3_link1","fr3_link2","fr3_link3","fr3_link4"})
    success=bool(lift>.10 and motion<.02 and np.mean(error[-10:])<.015 and not invalid and not upstream_contact and task.index==len(task.goals)-1)
    if a.scene=="table_corner":success=success and payload_top_support
    cup_support=False
    if cup>=0:
        cup_body=int(mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,"office_cup"))
        for i in range(d.ncon):
            c=d.contact[i];names=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,int(g)) or "" for g in (c.geom1,c.geom2)]
            if any("office_cup" in n for n in names) and any("office_desk_top" in n for n in names):
                cup_support=True;break
    cup_stable=(cup<0 or (cup_support and np.linalg.norm(d.cvel[cup,3:6])<.02))
    if cup>=0:success=success and cup_shift<.02 and cup_tilt<np.deg2rad(10) and cup_stable
    result=dict(scene=asdict(spec),controller="vmc" if policy is None else policy.kind,success=success,
        grasp_lift_success=lift>.10 and motion<.02,cup_safe=cup<0 or (cup_shift<.02 and cup_tilt<np.deg2rad(10) and cup_stable),cup_stable=cup_stable,cup_support_contact=cup_support,
        real_contact=audit["duration_s"]>(1e-6 if a.scene=="ball" else .001),invalid_physics=invalid,upstream_contact=upstream_contact,contact=audit,events=events,
        requested_event_stage=a.event_stage,requested_event_stage_index=requested_stage,
        fixture_triggered=fixture_triggered,fixture_trigger_time_s=fixture_trigger_time,
        ball_launched=ball_launched,ball_launch_state=ball_launch_state,
        final_stage=task.index,endpoint_error_m=float(np.mean(error[-10:])),lift_m=lift,cup_shift_m=cup_shift,cup_tilt_deg=float(np.rad2deg(cup_tilt)),
        impact_metrics=impact_metrics,push_metrics=push_metrics,payload_top_support=payload_top_support,
        peak_torque_nm=env.peak_torque,speed_p95_mps=float(np.percentile(np.linalg.norm(arr["twist"][:,:3],axis=1),95)),
        duration_s=float(d.time),arguments=vars(a),teacher_config={**asdict(teacher.config),
            "profile":a.teacher_profile,"force_target":a.force_target,"normal_gain":a.normal_gain},contract="contact45_v2",
        cup_initial_position=cup_initial,
        simulation_timestep_s=float(m.opt.timestep),student_mixture=a.mixture,
        teacher_called=((policy is None and a.teacher_profile!="none") or a.mixture>0),
        inputs="q7,qdot7,nominal_twist6,pose_error6,twist_error6,estimated_joint_load7,estimated_force3,commanded_path_direction3",
        source_sha256={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in [Path(__file__).name,"primitive_contact_scene_v7_20260917.py","contact_memory_vmc_20260916.py"]})
    np.savez_compressed(a.output.with_suffix(".npz"),**arr)
    a.output.with_suffix(".json").write_text(json.dumps(clean(result),indent=2,allow_nan=False))
    if frames:
        frames[0].save(a.output.with_suffix(".gif"),save_all=True,append_images=frames[1:],duration=40,loop=0,optimize=False)
        frames[0].save(a.output.with_suffix(".png"));renderer.close()
    print(json.dumps(clean({k:v for k,v in result.items() if k not in ("arguments","source_sha256")})),flush=True)
    env.close()


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scene",choices=("ball","push","corner","table_corner","empty"),required=True)
    p.add_argument("--output",type=Path,required=True);p.add_argument("--menagerie",type=Path,default=Path("../mujoco_menagerie"))
    p.add_argument("--model",type=Path);p.add_argument("--duration",type=float,default=18.)
    p.add_argument("--nominal-speed",type=float,default=.08)
    p.add_argument("--mixture",type=float,default=0.)
    p.add_argument("--seed",type=int,default=0);p.add_argument("--yaw",type=float,default=0.)
    p.add_argument("--shift",type=float,default=0.);p.add_argument("--width",type=float,default=.050)
    p.add_argument("--along",type=float)
    p.add_argument("--cup-mass",type=float,default=.30);p.add_argument("--ball-mass",type=float,default=.20)
    p.add_argument("--ball-speed",type=float,default=1.5);p.add_argument("--ball-angle",type=float,default=0.)
    p.add_argument("--ball-height-offset",type=float,default=0.);p.add_argument("--ball-vertical-speed",type=float,default=1.3)
    p.add_argument("--ball-radius",type=float,default=.060);p.add_argument("--ball-shell",type=float,default=.005)
    p.add_argument("--ball-contact-time",type=float,default=.008)
    p.add_argument("--ball-contact-damping",type=float,default=.75)
    p.add_argument("--ball-target-x",type=float);p.add_argument("--ball-target-y",type=float);p.add_argument("--ball-target-z",type=float)
    p.add_argument("--push-hold",type=float,default=3.);p.add_argument("--push-angle",type=float,default=0.)
    p.add_argument("--push-height",type=float,default=.56);p.add_argument("--push-force",type=float,default=15.)
    p.add_argument("--push-target-x",type=float);p.add_argument("--push-target-y",type=float)
    p.add_argument("--push-stroke",type=float,default=.12);p.add_argument("--push-press",type=float,default=1.4)
    p.add_argument("--push-retract",type=float,default=1.2)
    p.add_argument("--corner-height",type=float,default=.70);p.add_argument("--corner-friction",type=float,default=.20)
    p.add_argument("--payload-mass",type=float,default=.08)
    p.add_argument("--event-stage",choices=tuple(STAGE_INDEX),default="approach")
    p.add_argument("--event-delay",type=float,default=.30)
    p.add_argument("--stiffness",type=float,default=110.);p.add_argument("--tangent-speed",type=float)
    p.add_argument("--damping",type=float,default=32.);p.add_argument("--force-on",type=float,default=.5)
    p.add_argument("--contact-tau",type=float,default=.12);p.add_argument("--release-tau",type=float,default=.45)
    p.add_argument("--memory-tau",type=float,default=1.2)
    p.add_argument("--teacher-force-source",choices=("ideal","estimated"),default="ideal")
    p.add_argument("--teacher-profile",choices=("none","memory","low_force"),default="memory")
    p.add_argument("--force-target",type=float,default=1.0)
    p.add_argument("--normal-gain",type=float,default=.02)
    p.add_argument("--dt",type=float,default=.0001);p.add_argument("--settle-only",action="store_true");p.add_argument("--render",action="store_true")
    args=p.parse_args()
    if not 0.<=args.mixture<=1.:raise ValueError("Mixture must be in [0,1]")
    run(args)
