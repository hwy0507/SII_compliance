"""Physical apparatus acceptance test, not a student benchmark.

Robot is torque-controlled by existing WBC to hold a pose, NOT joint-locked.
World-only finite-force drives move the person/rod; the free ball gets an
initial velocity exactly once at reset. Actors never receive the schedule.
"""
import argparse,hashlib,json,os
from pathlib import Path
os.environ.setdefault('MUJOCO_GL','egl')
import mujoco
import numpy as np
from audit_office_complex_scene_v5_20260917 import make
from office_complex_scene_v5_20260917 import fixture_flags
from office_task_v4_20260917 import audit_initial,PickPlaceTask,contact_support,DEST
from run_contact_transfer_20260916 import clean
from haptic_vmc_teacher_20260916 import JointLoadObserver,equivalent_tool_wrench
from run_benchmark import body_jacobian,body_twist,so3_log


def smooth_profile(t,start,press,hold,retract):
    s=t-start
    u=np.clip(s/press,0,1) if s<press else 1. if s<press+hold else np.clip(1-(s-press-hold)/retract,0,1)
    return float(u*u*(3-2*u))


def run(a):
    if a.output.with_suffix('.json').exists():raise RuntimeError('Preserve existing results')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    flags=fixture_flags(a.seed,a.variant);flags['duration']=a.duration
    flags['nominal_speed']=.06;flags['ball_speed']=a.ball_speed
    env,task,spec=make(flags);m,d=env.model,env.data;m.opt.timestep=a.dt
    audit_initial(m,d)
    gid=lambda name:mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,name)
    bid=lambda name:mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,name)
    jid=lambda name:mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,name)
    robot=set(env._push_audit_robot_geom_ids)
    esn=None
    if a.esn_model:
        from contact_transfer_student_20260916 import TransferStudent
        esn=TransferStudent.load(a.esn_model)
        if esn.kind!='esn' or abs(esn.dt-.04)>1e-12:raise ValueError('Expected 25Hz ESN checkpoint')
    elif a.esn_mode=='control':raise ValueError('Control mode needs a checkpoint')
    load_observer=None;mass=None;release_truth=None;placement_hold=0.;max_lift=0.;task_events=[]
    target=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,'target_object_geom')
    if a.task=='pick_place':
        fingers=[];fdofs=[]
        for name in ('finger_joint1','finger_joint2'):
            j=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,name);fingers.append(m.jnt_qposadr[j]);fdofs.append(m.jnt_dofadr[j])
        task=PickPlaceTask(d.xpos[env._hand_id].copy(),fingers,fdofs,source=[.54,-.19,.425])
        env.reference=task;env.gripper_target_override=lambda unused,default:task.gripper_target()
        load_observer=JointLoadObserver(d.qvel.copy(),m.dof_frictionloss);mass=np.zeros((m.nv,m.nv))
    if esn and load_observer is None:
        load_observer=JointLoadObserver(d.qvel.copy(),m.dof_frictionloss);mass=np.zeros((m.nv,m.nv))
    ball=bid('office_v5_ball');ball_geom=gid('office_v5_ball_geom');ball_joint=jid('office_v5_ball_free')
    ball_dof=int(m.jnt_dofadr[ball_joint])
    # Initial condition only: after this point the ball is never actuated.
    if a.events in ('all','ball'):d.qvel[ball_dof+1]=a.ball_speed
    cup=bid('office_v5_cup');cup_base=gid('office_v5_cup_base');desk=gid('office_desk_top')
    cup_initial=d.xpos[cup].copy();initial_hand=d.xpos[env._hand_id].copy()
    joints={n:jid(n) for n in ('office_v5_person_root','office_v5_shoulder','office_v5_elbow','office_v5_push_rod_joint')}
    configs={
      'person':dict(start=3.,press=2.,hold=3.,retract=2.,stroke=a.person_stroke,force_limit=80.),
      'rod':dict(start=11.,press=1.5,hold=3.,retract=2.,stroke=a.rod_stroke,force_limit=14.)}
    stats=dict(max_penetration_m=0.,worst_pair=None,events={},cup_shift_m=0.,cup_tilt_deg=0.,
      max_hand_displacement_m=0.,peak_motor_torque_nm=0.,max_person_drive_n=0.,max_rod_drive_n=0.)
    last_ball_velocity=d.qvel[ball_dof:ball_dof+3].copy()
    ball_detail=[];next_ball_sample=0.
    incoming=None;last_robot_ball_contact=None;bounce_samples=[];first_ball_pos=None
    contact_keys=('ball','person_hand','rod','cup','office_v5_pillar')
    interval_peak=np.zeros(len(contact_keys));interval_impulse=np.zeros(len(contact_keys))
    def drive_joint(name,target,kp,kd,limit):
        j=joints[name];q=int(m.jnt_qposadr[j]);v=int(m.jnt_dofadr[j])
        force=float(np.clip(kp*(target-d.qpos[q])-kd*d.qvel[v]+d.qfrc_bias[v],-limit,limit))
        d.qfrc_applied[v]=force
        return force
    def world_step(unused):
        nonlocal incoming,last_ball_velocity,last_robot_ball_contact,first_ball_pos,next_ball_sample
        t=float(d.time)
        if load_observer:
            mujoco.mj_fullM(m,d,mass)
            load_observer.update(d.qvel.copy(),mass,d.qfrc_bias.copy(),d.qfrc_passive.copy(),d.qfrc_actuator.copy(),m.opt.timestep)
        c=configs['person'];target=c['stroke']*smooth_profile(t,c['start'],c['press'],c['hold'],c['retract']) if a.events in ('all','person') else 0.
        f=drive_joint('office_v5_person_root',target,1000.,180.,c['force_limit'])
        stats['max_person_drive_n']=max(stats['max_person_drive_n'],abs(f))
        drive_joint('office_v5_shoulder',0.,90.,15.,20.)
        drive_joint('office_v5_elbow',0.,65.,10.,12.)
        c=configs['rod'];target=c['stroke']*smooth_profile(t,c['start'],c['press'],c['hold'],c['retract']) if a.events in ('all','rod') else 0.
        f=drive_joint('office_v5_push_rod_joint',target,160.,12.,c['force_limit'])
        stats['max_rod_drive_n']=max(stats['max_rod_drive_n'],abs(f))
        resultant={};touch_ball=False
        for i in range(d.ncon):
            ct=d.contact[i];g1,g2=int(ct.geom1),int(ct.geom2)
            if m.geom_bodyid[g1]!=m.geom_bodyid[g2] and -ct.dist>stats['max_penetration_m']:
                stats['max_penetration_m']=-float(ct.dist)
                stats['worst_pair']=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g) or str(g) for g in (g1,g2)]
            if (g1 in robot)==(g2 in robot):continue
            other=g2 if g1 in robot else g1
            name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,other) or str(other)
            if not name.startswith('office_v5'):continue
            key='ball' if other==ball_geom else 'person_hand' if 'human_' in name else 'rod' if 'push_rod' in name else 'cup' if 'cup' in name else 'other_person_body' if any(s in name for s in ('person','arm')) else name
            f=np.zeros(6);mujoco.mj_contactForce(m,d,i,f)
            world=ct.frame.reshape(3,3).T@f[:3]*(1 if g2 in robot else -1)
            if np.linalg.norm(world)>.05:
                rg=g1 if g1 in robot else g2
                robot_part=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,int(m.geom_bodyid[rg])) or str(rg)
                rec=stats['events'].setdefault(key,dict(first_s=t,last_s=t,duration_s=0.,peak_n=0.,impulse_ns=0.,robot_parts=set()))
                rec['robot_parts'].add(robot_part)
                resultant[key]=resultant.get(key,np.zeros(3))+world
                if key=='ball':touch_ball=True
        for key,force in resultant.items():
            rec=stats['events'][key];mag=float(np.linalg.norm(force))
            rec['last_s']=t;rec['duration_s']+=m.opt.timestep;rec['peak_n']=max(rec['peak_n'],mag);rec['impulse_ns']+=mag*m.opt.timestep
            if key in contact_keys:
                k=contact_keys.index(key);interval_peak[k]=max(interval_peak[k],mag);interval_impulse[k]+=mag*m.opt.timestep
        velocity=d.qvel[ball_dof:ball_dof+3].copy()
        if touch_ball:
            if incoming is None:incoming=last_ball_velocity.copy();first_ball_pos=d.xpos[ball].copy()
            last_robot_ball_contact=t
        elif last_robot_ball_contact is not None and 0.<t-last_robot_ball_contact<.12:
            bounce_samples.append(velocity.copy())
        last_ball_velocity=velocity
        if t<.30 and (t>=next_ball_sample or touch_ball):
            ball_detail.append((t,d.qpos.copy(),velocity.copy(),touch_ball))
            next_ball_sample=t+.001
        stats['cup_shift_m']=max(stats['cup_shift_m'],float(np.linalg.norm((d.xpos[cup]-cup_initial)[:2])))
        stats['cup_tilt_deg']=max(stats['cup_tilt_deg'],float(np.rad2deg(np.arccos(np.clip(d.xmat[cup].reshape(3,3)[2,2],-1,1)))))
        stats['max_hand_displacement_m']=max(stats['max_hand_displacement_m'],float(np.linalg.norm(d.xpos[env._hand_id]-initial_hand)))
        stats['peak_motor_torque_nm']=max(stats['peak_motor_torque_nm'],float(abs(d.qfrc_actuator[:7]).max()))
    env.substep_observer=world_step
    records=[];video=None;frames=[];renderer=None
    if a.render:
        import imageio_ffmpeg
        from PIL import Image,ImageDraw,ImageFont
        m.vis.global_.offwidth=640;m.vis.global_.offheight=480
        renderer=mujoco.Renderer(m,height=480,width=640)
        overview=mujoco.MjvCamera();overview.lookat[:]=[.64,-.02,.45];overview.distance=2.5;overview.azimuth=135;overview.elevation=-20
        detail=mujoco.MjvCamera();detail.lookat[:]=[.60,-.18,.64];detail.distance=1.05;detail.azimuth=105;detail.elevation=-20
        video=imageio_ffmpeg.write_frames(str(a.output.with_suffix('.mp4')),(1280,520),fps=25,codec='libx264',pix_fmt_out='yuv420p',output_params=['-movflags','+faststart']);video.send(None)
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
    for _ in range(round(a.duration/.04)):
        if a.task=='pick_place':
            wrench=equivalent_tool_wrench(body_jacobian(m,d,env._hand_id),load_observer.filtered)
            before=task.index
            if task.update(d.qpos,d.qvel,d.xpos[env._hand_id],d.xmat[env._hand_id].reshape(3,3),body_twist(m,d,env._hand_id),wrench):
                task_events.append(dict(stage=task.names[task.index],time_s=float(d.time)))
            if before==5 and task.index==6:release_truth=contact_support(m,d,target,desk)
            task.advance_gripper()
        signal={};applied=np.zeros(7)
        if esn:
            position=d.xpos[env._hand_id].copy();rotation=d.xmat[env._hand_id].reshape(3,3).copy()
            twist=body_twist(m,d,env._hand_id);command=env._wbc_command(0.)
            error=np.r_[command.target_position_m-position,so3_log(command.target_rotation@rotation.T)]
            wrench=equivalent_tool_wrench(body_jacobian(m,d,env._hand_id),load_observer.filtered)
            observation=np.r_[d.qpos[:7],d.qvel[:7],command.task_twist_world,error,command.task_twist_world-twist,
                              load_observer.filtered,wrench[:3],task.path_direction]
            previous_state=esn.state.copy();predicted=esn.act(observation)
            if a.esn_mode=='control':applied=predicted.copy()
            signal=dict(neuron_time=float(d.time),neuron_qpos=d.qpos.copy(),observation=observation,
                        reservoir_state=esn.state.copy(),reservoir_delta=esn.state-previous_state,
                        esn_action=predicted,applied_action=applied.copy(),
                        prior_contact_peak=interval_peak.copy(),prior_contact_impulse=interval_impulse.copy())
        interval_peak[:]=0.;interval_impulse[:]=0.
        env.step(applied)
        max_lift=max(max_lift,float(d.xpos[env._target_body_id,2]-.425))
        if a.task=='pick_place':
            supported=contact_support(m,d,target,desk)
            near=np.linalg.norm(d.xpos[env._target_body_id,:2]-DEST[:2])<.025
            slow=np.linalg.norm(d.qvel[env._target_dof:env._target_dof+3])<.015
            placement_hold=placement_hold+.04 if task.index==7 and supported and near and slow else 0.
        records.append(dict(time=float(d.time),qpos=d.qpos.copy(),hand=d.xpos[env._hand_id].copy(),ball=d.xpos[ball].copy(),ball_velocity=d.qvel[ball_dof:ball_dof+3].copy(),cup=d.xpos[cup].copy(),stage=task.index,object_position=d.xpos[env._target_body_id].copy(),**signal))
        if renderer:
            renderer.update_scene(d,camera=overview);im1=Image.fromarray(renderer.render())
            renderer.update_scene(d,camera=detail);im2=Image.fromarray(renderer.render())
            im=Image.new('RGB',(1280,520),(15,22,30));im.paste(im1,(0,40));im.paste(im2,(640,40))
            ImageDraw.Draw(im).text((12,10),f'Office scene validation | {d.time:.2f}s | ball / human hand / rod | WBC {a.task}: {task.names[task.index]}',font=font,fill='white')
            video.send(np.asarray(im));frames.append(im)
        if stats['max_penetration_m']>.002:break
    if video:video.close()
    if frames:
        frames[0].save(a.output.with_suffix('.gif'),save_all=True,append_images=frames[1:],duration=40,loop=0)
        frames[0].save(a.output.with_suffix('.png'))
        for sec in (.12,5.,13.):
            frames[min(len(frames)-1,round(sec/.04))].save(a.output.parent/(a.output.name+f'_at_{sec:g}.png'))
    cup_supported=False
    for i in range(d.ncon):
        c=d.contact[i]
        if {int(c.geom1),int(c.geom2)}=={cup_base,desk}:
            f=np.zeros(6);mujoco.mj_contactForce(m,d,i,f);cup_supported=cup_supported or f[0]>.05
    bounce=bool(incoming is not None and incoming[1]>.05 and any(v[1]<-.05 for v in bounce_samples))
    separation=float(np.linalg.norm(d.xpos[ball]-first_ball_pos)) if first_ball_pos is not None else None
    required={'all':('ball','person_hand','rod'),'ball':('ball',),'person':('person_hand',),'rod':('rod',),'settle':()}[a.events]
    contact_ok=all(stats['events'].get(k,{}).get('duration_s',0)>(.0002 if k=='ball' else .4) for k in required)
    cup_valid=bool(cup_supported and np.linalg.norm(d.cvel[cup,3:])<.02 and stats['cup_shift_m']<.02 and stats['cup_tilt_deg']<10.)
    result=dict(purpose='scene_development_acceptance_no_policy_training',arguments=vars(a),fixture=flags,
      stats=stats,ball_initial_velocity=[0,a.ball_speed if a.events in ('all','ball') else 0,0],ball_actuated_after_reset=False,
      ball_incoming_velocity=incoming,ball_rebound=bounce,ball_final_separation_m=separation,
      cup_supported=cup_supported,cup_final_speed=float(np.linalg.norm(d.cvel[cup,3:])),
      initial_geometry_valid=True,physical_valid=stats['max_penetration_m']<.0002,
      contact_coverage_valid=contact_ok,cup_valid=cup_valid,passed=contact_ok and stats['max_penetration_m']<.0002 and cup_valid and (bounce if 'ball' in required else True),
      human_model='guided massive torso with shoulder/elbow hinges and compliant wrist; not free biped gait',
      controller='existing kinematic WBC pose hold, unlocked joints, zero learned residual',schedule=configs,
      source_sha256={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in
        ('office_complex_scene_v5_20260917.py','validate_office_apparatus_v5_20260917.py','audit_office_complex_scene_v5_20260917.py')})
    result['controller']='existing kinematic WBC '+a.task+', unlocked joints, zero learned residual'
    result['task_events']=task_events
    result['final_task_stage']=task.names[task.index]
    result['placement_complete']=bool(a.task=='pick_place' and placement_hold>=.5 and release_truth and max_lift>.10
       and np.linalg.norm(d.xpos[env._hand_id]-task.goals[-1])<.015 and sum(d.qpos[task.fingers])>.075)
    result['release_supported']=release_truth
    result['max_lift_m']=max_lift
    result['neural_logging']=dict(enabled=esn is not None,mode=a.esn_mode,model=str(a.esn_model) if a.esn_model else None,
        model_sha256=hashlib.sha256(a.esn_model.read_bytes()).hexdigest() if esn else None,
        reservoir_size=esn.reservoir if esn else None,policy_hz=25,
        state_semantics='post-update leaky reservoir state, before physics step; fixed unit ordering',
        contact_semantics='prior_contact_* covers the preceding physics interval; contact truth is diagnostics ONLY',
        contact_keys=contact_keys,force_truth_in_actor=False,weights_changed=False)
    if esn:result['controller']+=(' + ESN action residual' if a.esn_mode=='control' else ' (ESN shadow observer only)')
    a.output.with_suffix('.json').write_text(json.dumps(clean(result),indent=2,allow_nan=False))
    np.savez_compressed(a.output.with_suffix('.npz'),**{k:np.array([r[k] for r in records]) for k in records[0]})
    np.savez_compressed(a.output.parent/(a.output.name+'_ball_detail.npz'),
        time=np.array([r[0] for r in ball_detail]),qpos=np.array([r[1] for r in ball_detail]),
        velocity=np.array([r[2] for r in ball_detail]),contact=np.array([r[3] for r in ball_detail]))
    if a.render:
        mujoco.mj_saveLastXML(str(a.output.with_suffix('.xml')),m)
    if renderer:renderer.close()
    env.close();print(json.dumps(clean(result)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--render',action='store_true')
    p.add_argument('--events',choices=('settle','ball','person','rod','all'),default='all')
    p.add_argument('--task',choices=('hold','pick_place'),default='hold')
    p.add_argument('--seed',type=int,default=2026091751);p.add_argument('--variant',type=int,default=0)
    p.add_argument('--duration',type=float,default=21.);p.add_argument('--dt',type=float,default=.00005)
    p.add_argument('--ball-speed',type=float,default=1.7);p.add_argument('--person-stroke',type=float,default=.20)
    p.add_argument('--rod-stroke',type=float,default=.235)
    p.add_argument('--esn-model',type=Path)
    p.add_argument('--esn-mode',choices=('shadow','control'),default='shadow')
    run(p.parse_args())
