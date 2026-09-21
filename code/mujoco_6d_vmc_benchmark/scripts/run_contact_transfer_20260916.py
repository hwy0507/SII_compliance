"""Blind contact transfer: primitives for training, office objects for test.

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
from office_contact_scene_20260916 import SceneSpec,extend_xml,task_layout


def clean(value):
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple,set)):return [clean(v) for v in value]
    if isinstance(value,np.ndarray):return clean(value.tolist())
    if isinstance(value,np.generic):return clean(value.item())
    if isinstance(value,Path):return str(value)
    if isinstance(value,float) and not np.isfinite(value):return None
    return value


class BlindTask:
    def __init__(self,initial,grasp,rotation,hand,fingers,finger_dofs,settle=False):
        self.goals=[grasp+np.array([0,0,.175]),grasp+np.array([0,0,.1029]),
                    grasp+np.array([0,0,.1029]),grasp+np.array([0,0,.2629])]
        self.names=["REACH / CONTACT RESPONSE","ALIGN TO GRASP","CLOSE GRIPPER","LIFT / HOLD"]
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
    spec=SceneSpec(kind=a.scene,yaw=a.yaw,shift=a.shift,along=along,width=a.width,cup_mass=a.cup_mass,
                   ball_mass=a.ball_mass,ball_speed=a.ball_speed,seed=a.seed)
    os.environ.update(THICK_TABLE_SCENE="1",EXTRACTION_TABLE="1",PUSH_FULL_RIGID_CONTACTS="1",
        HAPTIC_BALL_FULL_CONTACTS="1",TARGET_TABLE_AFFINITY="63",PUSH_ROD_SCENE="1" if a.scene in ("push","complex") else "0",
        PUSH_ROD_CENTER_X=".54",PUSH_ROD_CENTER_Z=".56",PUSH_ROD_DRIVER_KP="160",
        PUSH_ROD_DRIVER_FORCE_LIMIT_N="15",PUSH_ROD_JOINT_DAMPING="20",
        PUSH_ROD_SOLREF_TIME_S=".0028",PUSH_ROD_SOLIMP_MIN=".90",PUSH_ROD_SOLIMP_MAX=".99",
        PUSH_ROD_SOLIMP_WIDTH_M=".001",PUSH_ROD_CONTACT_PRIORITY="2",PUSH_ROD_START_S=".3",
        PUSH_ROD_PRESS_S="1.4",PUSH_ROD_HOLD_S=str(a.push_hold),PUSH_ROD_RETRACT_S="1.2",PUSH_ROD_STROKE_M=".12")
    env=PandaWBCVelocityResidualEnv(menagerie=a.menagerie,fan_ye_model_npz=None,fan_ye_train_summary_json=None,
        observation_mode="direct_esn",fixtures=(VelocityResidualFixture(.1,.53,1.8,contact_time_constant_s=.001),),
        rod_enabled=False,robot="fr3",wbc_backend="paper_mpc",execution_mode="twist",seed=a.seed,
        safety_config=VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32),grasp_retention_mode="off",
        simulation_time_s=a.duration,scene_transform=lambda xml:extend_xml(xml,spec))
    env.reset(seed=a.seed,options={"fixture_index":0})
    m,d=env.model,env.data;m.opt.timestep=a.dt;m.opt.solver=mujoco.mjtSolver.mjSOL_NEWTON
    if a.scene in ("ball","complex"):m.opt.timestep=min(a.dt,.00005)
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
        d.qvel[m.jnt_dofadr[j]+1]=a.ball_speed
        d.qvel[m.jnt_dofadr[j]+2]=1.3
    mujoco.mj_forward(m,d)
    for i in range(d.ncon):
        c=d.contact[i];names=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,int(g)) or "" for g in (c.geom1,c.geom2)]
        primary=any(n.startswith(("primitive_corner","office_cup","office_pillar","push_rod_geom")) for n in names)
        arm=any(int(g) in env._push_audit_robot_geom_ids for g in (c.geom1,c.geom2))
        if primary and arm and c.dist<-.00001:raise ValueError(f"Initial robot/obstacle overlap: {names}, {c.dist}")
    env.previous_torque=d.qfrc_bias[:7].copy()
    task=BlindTask(initial,goal,rotation,env._hand_id,fingers,fdofs,a.settle_only)
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
    teacher_config=ContactMemoryConfig(stiffness=a.stiffness,tangent_speed=tangent_speed)
    teacher=(LowForceVMC(teacher_config,force_target=a.force_target,normal_gain=a.normal_gain)
             if a.teacher_profile=="low_force" else ContactMemoryVMC(teacher_config))
    policy=None
    if a.model:
        from contact_transfer_student_20260916 import TransferStudent
        policy=TransferStudent.load(a.model)
    observer=JointLoadObserver(d.qvel.copy(),m.dof_frictionloss);mass=np.zeros((m.nv,m.nv))
    robot=set(env._push_audit_robot_geom_ids)
    objects={g for g in range(m.ngeom) if (mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g) or "").startswith(("primitive_corner","primitive_free_ball","office_cup","office_pillar"))}
    if env._push_rod_geom_id>=0:objects.add(env._push_rod_geom_id)
    audit=dict(peak_force_n=0.,all_external_peak_force_n=0.,peak_body_resultant_n=0.,max_penetration_m=0.,
        all_external_max_penetration_m=0.,grasp_penetration_m=0.,duration_s=0.,first_s=None,last_s=None,pairs=set(),force=np.zeros(3),other_contacts=set())
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
                if np.linalg.norm(f[:3])>.05:
                    touch=True;audit["pairs"].add((mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g1) or str(g1),mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g2) or str(g2)))
        audit["force"]=force;audit["peak_force_n"]=max(audit["peak_force_n"],float(np.linalg.norm(force)))
        audit["all_external_peak_force_n"]=max(audit["all_external_peak_force_n"],float(np.linalg.norm(all_external_force)))
        audit["peak_body_resultant_n"]=max(audit["peak_body_resultant_n"],max((float(np.linalg.norm(f)) for f in body_forces.values()),default=0.))
        teacher_force_sensor[:]+=(1.-np.exp(-m.opt.timestep/.04))*(all_external_force-teacher_force_sensor)
        if cup>=0:
            cup_shift=max(cup_shift,float(np.linalg.norm((d.xpos[cup]-cup_initial)[:2])))
            cup_tilt=max(cup_tilt,float(np.arccos(np.clip(d.xmat[cup].reshape(3,3)[2,2],-1,1))))
        if touch:
            audit["duration_s"]+=m.opt.timestep;audit["last_s"]=float(d.time)
            if audit["first_s"] is None:audit["first_s"]=float(d.time)
    env.substep_observer=sensor_and_audit
    cup=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,"office_cup")
    cup_initial=d.xpos[cup].copy() if cup>=0 else None
    cup_shift=0.;cup_tilt=0.;frames=[];records=[];events=[];invalid=False
    if a.render:
        m.vis.global_.offwidth=640;m.vis.global_.offheight=480
        renderer=mujoco.Renderer(m,height=480,width=640)
        cam=mujoco.MjvCamera();cam.type=mujoco.mjtCamera.mjCAMERA_FREE
        cam.lookat[:]=[.44,0.,.34];cam.distance=1.6;cam.azimuth=135;cam.elevation=-28
        close_cam=mujoco.MjvCamera();close_cam.type=mujoco.mjtCamera.mjCAMERA_FREE
        close_cam.lookat[:]=[.54,.025,.54];close_cam.distance=.90;close_cam.azimuth=90;close_cam.elevation=-60
        font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",17)
    for step in range(round(a.duration/RL_DT)):
        position=d.xpos[env._hand_id].copy();rotation=d.xmat[env._hand_id].reshape(3,3).copy()
        twist=body_twist(m,d,env._hand_id)
        if task.update(d.qpos,d.qvel,position,rotation,twist):events.append(dict(t=float(d.time),stage=task.index))
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
    lift=float(arr["object_position"][-1,2]-.425)
    motion=float(np.max(np.linalg.norm(np.diff(arr["object_position"][-10:],axis=0)/RL_DT,axis=1))) if len(records)>1 else float("inf")
    success=bool(lift>.10 and motion<.02 and np.mean(error[-10:])<.015 and not invalid)
    cup_stable=(cup<0 or (.395<float(d.xpos[cup,2])<.41 and np.linalg.norm(d.cvel[cup,3:6])<.02))
    if cup>=0:success=success and cup_shift<.02 and cup_tilt<np.deg2rad(10) and cup_stable
    result=dict(scene=asdict(spec),controller="vmc" if policy is None else policy.kind,success=success,
        grasp_lift_success=lift>.10 and motion<.02,cup_safe=cup<0 or (cup_shift<.02 and cup_tilt<np.deg2rad(10) and cup_stable),cup_stable=cup_stable,
        real_contact=audit["duration_s"]>.001,invalid_physics=invalid,contact=audit,events=events,
        final_stage=task.index,endpoint_error_m=float(np.mean(error[-10:])),lift_m=lift,cup_shift_m=cup_shift,cup_tilt_deg=float(np.rad2deg(cup_tilt)),
        peak_torque_nm=env.peak_torque,speed_p95_mps=float(np.percentile(np.linalg.norm(arr["twist"][:,:3],axis=1),95)),
        duration_s=float(d.time),arguments=vars(a),teacher_config={**asdict(teacher.config),
            "profile":a.teacher_profile,"force_target":a.force_target,"normal_gain":a.normal_gain},contract="contact45_v2",
        cup_initial_position=cup_initial,
        simulation_timestep_s=float(m.opt.timestep),student_mixture=a.mixture,
        teacher_called=((policy is None and a.teacher_profile!="none") or a.mixture>0),
        inputs="q7,qdot7,nominal_twist6,pose_error6,twist_error6,estimated_joint_load7,estimated_force3,commanded_path_direction3",
        source_sha256={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in [Path(__file__).name,"office_contact_scene_20260916.py","contact_memory_vmc_20260916.py"]})
    np.savez_compressed(a.output.with_suffix(".npz"),**arr)
    a.output.with_suffix(".json").write_text(json.dumps(clean(result),indent=2,allow_nan=False))
    if frames:
        frames[0].save(a.output.with_suffix(".gif"),save_all=True,append_images=frames[1:],duration=40,loop=0,optimize=False)
        frames[0].save(a.output.with_suffix(".png"));renderer.close()
    print(json.dumps(clean({k:v for k,v in result.items() if k not in ("arguments","source_sha256")})),flush=True)
    env.close()


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scene",choices=("ball","push","corner","cup","pillar","cup_pillar","complex","empty"),required=True)
    p.add_argument("--output",type=Path,required=True);p.add_argument("--menagerie",type=Path,default=Path("../mujoco_menagerie"))
    p.add_argument("--model",type=Path);p.add_argument("--duration",type=float,default=18.)
    p.add_argument("--nominal-speed",type=float,default=.08)
    p.add_argument("--mixture",type=float,default=0.)
    p.add_argument("--seed",type=int,default=0);p.add_argument("--yaw",type=float,default=0.)
    p.add_argument("--shift",type=float,default=0.);p.add_argument("--width",type=float,default=.050)
    p.add_argument("--along",type=float)
    p.add_argument("--cup-mass",type=float,default=.30);p.add_argument("--ball-mass",type=float,default=.20)
    p.add_argument("--ball-speed",type=float,default=1.5);p.add_argument("--push-hold",type=float,default=3.)
    p.add_argument("--stiffness",type=float,default=110.);p.add_argument("--tangent-speed",type=float)
    p.add_argument("--teacher-force-source",choices=("ideal","estimated"),default="ideal")
    p.add_argument("--teacher-profile",choices=("none","memory","low_force"),default="memory")
    p.add_argument("--force-target",type=float,default=1.0)
    p.add_argument("--normal-gain",type=float,default=.02)
    p.add_argument("--dt",type=float,default=.0001);p.add_argument("--settle-only",action="store_true");p.add_argument("--render",action="store_true")
    args=p.parse_args()
    if not 0.<=args.mixture<=1.:raise ValueError("Mixture must be in [0,1]")
    if args.scene in ("cup","pillar","cup_pillar","complex") and args.model is not None:
        # Experiment preflight only; this never changes a policy action.
        # Do not spend a novel-object test on an unfrozen/failed source fit.
        frozen=args.model.resolve().parent.parent/"selection_frozen.json"
        if not frozen.exists():raise RuntimeError("Office evaluation requires frozen source-only selection")
        selection=json.loads(frozen.read_text())["selected"]
        if args.mixture!=0 or any(v["score"][0]<8 for v in selection.values()):
            raise RuntimeError("Office test sealed: both students must pass at least 8 source validation cases, with zero teacher mixture")
    run(args)
