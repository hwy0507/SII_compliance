"""Physical apparatus acceptance test, not a student benchmark.

Robot is torque-controlled by existing WBC to hold a pose, NOT joint-locked.
World-only finite-force drives move the person/rod; the free ball gets an
initial velocity exactly once at reset. Actors never receive the schedule.
"""
import argparse,hashlib,json,os,subprocess
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
from physics_substep_metrics_20260923 import EpisodeMetrics


def is_external_contact(model, robot_geoms, target_body, g1, g2):
    """Robot/world contact, excluding intentional contact with grasped payload."""
    if (g1 in robot_geoms)==(g2 in robot_geoms):return False
    other=g2 if g1 in robot_geoms else g1
    return int(model.geom_bodyid[other])!=target_body


def canonical_observation(q, dq, command, error, twist, load, wrench, direction):
    observation=np.r_[q[:7],dq[:7],command,error,command-twist,load,wrench,direction]
    if observation.shape!=(48,) or not np.isfinite(observation).all():
        raise ValueError('Expected finite canonical proprio48 observation')
    return observation


def smooth_profile(t,start,press,hold,retract):
    s=t-start
    u=np.clip(s/press,0,1) if s<press else 1. if s<press+hold else np.clip(1-(s-press-hold)/retract,0,1)
    return float(u*u*(3-2*u))


def interaction_schedule(a):
    """World-side schedule; named protocols reject stale timing overrides."""
    configs = {
        'person': dict(start=getattr(a, 'person_start', 3.), press=2., hold=3.,
                       retract=2., stroke=a.person_stroke, force_limit=80.),
        'rod': dict(start=getattr(a, 'rod_start', 11.), press=1.5,
                    hold=getattr(a, 'rod_hold', 3.), retract=2.,
                    stroke=a.rod_stroke, force_limit=14.)}
    profile = getattr(a, 'interaction_schedule', 'legacy')
    if profile == 'sequential-r12-v1':
        if (configs['person']['start'], configs['rod']['start'], configs['rod']['hold']) != (3., 12., 6.):
            raise ValueError('sequential-r12-v1 requires --person-start 3 --rod-start 12 --rod-hold 6')
    elif profile != 'legacy':
        raise ValueError(f'Unknown interaction schedule: {profile}')
    return configs


def prepare_policy_state(esn, memory_ablation):
    if getattr(esn, 'kind', None) == 'mlp':
        return np.empty(0, dtype=float)
    if memory_ablation == 'reset_each_observation':
        obj = getattr(esn, 'obj', esn)
        contract = getattr(esn, 'contract', getattr(obj, 'contract', None))
        # Permit the current canonical 48D/action7 ESN alongside the legacy
        # office-memory checkpoint. The ablation is valid only for a stateful
        # 48D reservoir; legacy 45D policies remain rejected.
        legacy = contract == 'proprio48_office_vmc_memory_esn_v1'
        canonical = getattr(obj, 'input_dim', None) == 48 and hasattr(obj, 'state')
        if not (legacy or canonical):
            raise ValueError('Memory ablation requires a stateful 48D office ESN')
        esn.reset()
    elif memory_ablation != 'none':
        raise ValueError('Unknown memory ablation')
    return getattr(esn, 'obj', esn).state.copy()


def run(a):
    configs = interaction_schedule(a)
    planned_corner = bool(getattr(a, 'planned_hand_corner', False))
    if planned_corner and not (a.task == 'pick_place' and a.corner_placement and a.combined_thick_corner_pillar_v4):
        raise ValueError('Planned hand corner requires combined-v4 corner pick_place')
    path_plan = None
    unexpected_edge = bool(getattr(a, 'unexpected_edge', False))
    if unexpected_edge and not planned_corner:
        raise ValueError('Unexpected edge requires the planned hand-corner task')
    if a.output.with_suffix('.json').exists():raise RuntimeError('Preserve existing results')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    probe=getattr(a,'physics_probe_s',None)
    if probe is not None and (probe<=0 or probe>a.duration or abs(probe/.04-round(probe/.04))>1e-8):
        raise ValueError('Physics probe must be a positive whole number of policy periods within duration')
    planned_steps=round((a.duration if probe is None else probe)/.04)
    flags=fixture_flags(a.seed,a.variant,
                        interaction_demo=bool(getattr(a,'interaction_demo',False)),
                        corner_placement=bool(getattr(a,'corner_placement',False)),
                        combined_demo=bool(getattr(a,'combined_demo',False)),
                        combined_contact_v2=bool(getattr(a,'combined_contact_v2',False)),
                        relaxed_pillar=bool(getattr(a,'relaxed_pillar',False)),
                        combined_thick_corner_pillar_v1=bool(getattr(a,'combined_thick_corner_pillar_v1',False)),
                        combined_thick_corner_pillar_v2=bool(getattr(a,'combined_thick_corner_pillar_v2',False)),
                        combined_thick_corner_pillar_v3=bool(getattr(a,'combined_thick_corner_pillar_v3',False)),
                        combined_thick_corner_pillar_v4=bool(getattr(a,'combined_thick_corner_pillar_v4',False)))
    if unexpected_edge:flags['unexpected_edge']=True
    flags['duration']=a.duration
    flags['nominal_speed']=.06;flags['ball_speed']=a.ball_speed
    env,task,spec=make(flags);m,d=env.model,env.data;m.opt.timestep=a.dt
    refinement=getattr(a,'impact_refinement_dt',None)
    refine_until=getattr(a,'impact_refinement_until',.2)
    if refinement is not None:
        if not 0<refinement<a.dt or abs(refine_until/.004-round(refine_until/.004))>1e-8 or not 0<refine_until<a.duration:
            raise ValueError('Refinement requires a smaller step and a servo-aligned time boundary')
        if any(abs(.004/dt-round(.004/dt))>1e-8 for dt in (refinement,a.dt)):
            raise ValueError('Physics timesteps must divide the 4ms servo period')
        original_physics=env._physics_step
        def refined_physics(t):
            m.opt.timestep=refinement if t<refine_until-1e-10 else a.dt
            return original_physics(t)
        env._physics_step=refined_physics;m.opt.timestep=refinement
    audit_initial(m,d)
    gid=lambda name:mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,name)
    bid=lambda name:mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,name)
    jid=lambda name:mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,name)
    robot=set(env._push_audit_robot_geom_ids)
    esn=None;policy_contract=None;policy_observation_dim=None
    if a.esn_model:
        with np.load(a.esn_model,allow_pickle=False) as checkpoint:
            policy_contract=str(checkpoint['contract'].item()) if 'contract' in checkpoint.files else 'legacy_contact45'
        if policy_contract.startswith('proprio48_'):
            from current_student_policy_20260921 import load_current
            esn=load_current(a.esn_model);policy_observation_dim=48
        else:
            from contact_transfer_student_20260916 import TransferStudent
            esn=TransferStudent.load(a.esn_model);policy_observation_dim=45
            if abs(esn.dt-.04)>1e-12:raise ValueError('Expected 25Hz legacy ESN checkpoint')
        # Permit the explicitly paired canonical48D MLP control in the same
        # frozen physical evaluator.  Its actor contract is still 48D->7D;
        # this branch changes no world, gate, actuator, or observation field.
        if esn.kind not in ('esn','esn_linear','mlp'):raise ValueError('Expected canonical ESN/MLP checkpoint')
    elif a.esn_mode=='control':raise ValueError('Control mode needs a checkpoint')
    memory_ablation=getattr(a,'memory_ablation','none')
    if memory_ablation != 'none':
        stateful_canonical = esn is not None and policy_contract.startswith('proprio48_')
        if not (stateful_canonical or policy_contract == 'proprio48_office_vmc_memory_esn_v1'):
            raise ValueError('Memory ablation requires a stateful 48D office ESN')
    load_observer=None;mass=None;release_truth=None;placement_hold=0.;max_lift=0.;task_events=[]
    observer_kwargs=dict(friction_velocity_scale=getattr(a,'observer_friction_velocity_scale',.005))
    target_geom=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,'target_object_geom')
    target_body=int(m.geom_bodyid[target_geom])
    desk=gid('office_desk_top')
    corner_top=gid('office_v5_corner_top')
    corner_contact_geoms={g for g in (corner_top,gid('office_v5_corner_face'),gid('office_v5_corner_bridge')) if g>=0}
    if bool(getattr(a,'corner_placement',False)):
        if corner_top<0:raise ValueError('Corner placement requested but corner top is absent')
        # Place the cube on the front portion of the thick corner top.  The
        # center remains over the support slab (x=.588..712, y=.110..300,
        # z=.575 top surface) while the approach stays in front of the
        # vertical face (y>=.205), so the end effector can reach it without
        # pushing through the corner.
        destination=np.array([.565 if (bool(getattr(a,'combined_demo',False)) or bool(getattr(a,'combined_contact_v2',False))) else .582,
                              -.302+.018*float(a.variant),.545])
        support_geoms=(corner_top,)
    else:
        destination=DEST.copy()
        support_geoms=(desk,)
    if getattr(a,'disable_selector_pulse',False):
        if esn is None or not hasattr(esn,'selector_pulse_steps'):
            raise ValueError('Pulse ablation requires a pulsed ESN')
        esn.selector_pulse_used=True
    if a.task=='pick_place':
        fingers=[];fdofs=[]
        for name in ('finger_joint1','finger_joint2'):
            j=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,name);fingers.append(m.jnt_qposadr[j]);fdofs.append(m.jnt_dofadr[j])
        task=PickPlaceTask(d.xpos[env._hand_id].copy(),fingers,fdofs,
                           source=[.54,-.19,.425],destination=destination,
                           support_geoms=support_geoms,
                           lift_height=.24,
                           # The former corner waypoint [x, y-.60, z+.175]
                           # demanded z=.775 m and was outside the measured
                           # WBC reach envelope.  Use a conservative, already
                           # reachable staging point before the final
                           # above-corner placement goal.  This changes only
                           # the development route; geometry, support gate,
                           # actor inputs and limits remain frozen.
                           carry_waypoint=(np.array([.560,
                                                     -.330,
                                                     .670])
                                           if bool(getattr(a,'combined_demo',False)) or bool(getattr(a,'combined_thick_corner_pillar_v1',False)) or bool(getattr(a,'combined_thick_corner_pillar_v2',False)) or bool(getattr(a,'combined_thick_corner_pillar_v3',False)) or bool(getattr(a,'combined_thick_corner_pillar_v4',False)) else
                                           np.array([.560,
                                                     -.330,
                                                     .670])
                                           if bool(getattr(a,'corner_placement',False)) else None))
        if bool(getattr(a,'combined_contact_v2',False)):
            # The generic task retreats to its carry waypoint.  In the
            # combined fixture that would make a pillar placed on the retreat
            # path also disturb the payload before release.  Use a distinct,
            # reachable post-release retreat target so the same physical
            # pillar brush remains causal but cannot invalidate placement.
            # This target is a commanded task reference only; no scene truth
            # or schedule field is exposed to the actor.
            task.goals[-1]=np.array([.690,-.330+.018*float(a.variant),.700])
        if planned_corner:
            from planned_hand_corner_20261002 import build_plan
            task,path_plan=build_plan(env,task,blind_edge=unexpected_edge,
                                     allow_lateral_rejoin=bool(getattr(a,'allow_lateral_rejoin',False)))
            a.output.with_suffix('.plan.json').write_text(json.dumps(path_plan,indent=2))
        env.reference=task;env.gripper_target_override=lambda unused,default:task.gripper_target()
        load_observer=JointLoadObserver(d.qvel.copy(),m.dof_frictionloss,**observer_kwargs);mass=np.zeros((m.nv,m.nv))
    if esn and load_observer is None:
        load_observer=JointLoadObserver(d.qvel.copy(),m.dof_frictionloss,**observer_kwargs);mass=np.zeros((m.nv,m.nv))
    teacher=None
    hybrid_teacher=None
    hybrid_blend=float(getattr(a,'hybrid_vmc_blend',0.0))
    if hybrid_blend:
        if esn is None or a.esn_mode!='control' or not 0.0 <= hybrid_blend <= 1.0:
            raise ValueError('hybrid-vmc-blend requires ESN control and a weight in [0,1]')
        from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics
        hybrid_teacher=SixDVirtualDynamics({})
    if getattr(a,'teacher','none')!='none':
        if esn or hybrid_teacher:raise ValueError('Teacher collection and ESN execution must be separate')
        if a.teacher=='vmc6d':
            from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics
            teacher=SixDVirtualDynamics({})
        else:
            from contact_memory_vmc_20260916 import ContactMemoryVMC
            teacher=ContactMemoryVMC()
        if load_observer is None:
            load_observer=JointLoadObserver(d.qvel.copy(),m.dof_frictionloss,**observer_kwargs);mass=np.zeros((m.nv,m.nv))
    capacity=None if refinement is None else int(np.ceil(refine_until/refinement)+np.ceil((a.duration-refine_until)/a.dt))+32
    metrics=EpisodeMetrics(env,capacity=capacity)
    mujoco.mj_saveModel(m,str(a.output.with_suffix('.mjb')),None)
    mujoco.mj_saveLastXML(str(a.output.with_suffix('.xml')),m)
    ball=bid('office_v5_ball');ball_geom=gid('office_v5_ball_geom');ball_joint=jid('office_v5_ball_free')
    ball_qpos_adr=int(m.jnt_qposadr[ball_joint])
    ball_dof=int(m.jnt_dofadr[ball_joint])
    # Initial condition only: after this point the ball is never actuated.
    ball_launch_time_s = float(getattr(a, 'ball_launch_time_s', 0.0))
    if not np.isfinite(ball_launch_time_s) or ball_launch_time_s < 0.0:
        raise ValueError('ball-launch-time-s must be finite and non-negative')
    ball_launched = False
    ball_hold_qpos = d.qpos[ball_qpos_adr:ball_qpos_adr + 7].copy() if ball_launch_time_s > 0.0 else None
    if a.events in ('all','ball') and ball_launch_time_s <= 0.0:
        d.qvel[ball_dof+1]=a.ball_speed
        ball_launched = True
    cup=bid('office_v5_cup');cup_base=gid('office_v5_cup_base')
    cup_initial=d.xpos[cup].copy() if cup>=0 else np.zeros(3);initial_hand=d.xpos[env._hand_id].copy()
    joints={n:jid(n) for n in ('office_v5_person_root','office_v5_shoulder','office_v5_elbow','office_v5_push_rod_joint')}
    stats=dict(max_penetration_m=0.,worst_pair=None,max_external_penetration_m=0.,worst_external_pair=None,
      events={},contact_diagnostics={'rod_longest_run': None, 'corner_target_by_stage': {}},cup_shift_m=0.,cup_tilt_deg=0.,
      max_hand_displacement_m=0.,peak_motor_torque_nm=0.,max_person_drive_n=0.,max_rod_drive_n=0.)
    edge_geom=gid('office_v5_unexpected_edge')
    if unexpected_edge:
        stats['unexpected_edge']=dict(first_s=None,last_s=None,duration_s=0.,peak_n=0.,impulse_ns=0.,
                                      max_penetration_m=0.,by_stage={})
    last_ball_velocity=d.qvel[ball_dof:ball_dof+3].copy()
    ball_detail=[];next_ball_sample=0.
    incoming=None;last_robot_ball_contact=None;bounce_samples=[];first_ball_pos=None
    impact_slow_frames=[];impact_next=max(0.,ball_launch_time_s-.25)
    impact_renderer=None;impact_overview=None;impact_detail=None
    contact_keys=('ball','person_hand','rod','cup','office_v5_pillar')
    interval_peak=np.zeros(len(contact_keys));interval_impulse=np.zeros(len(contact_keys))
    rod_run=None
    def drive_joint(name,target,kp,kd,limit):
        j=joints[name];q=int(m.jnt_qposadr[j]);v=int(m.jnt_dofadr[j])
        force=float(np.clip(kp*(target-d.qpos[q])-kd*d.qvel[v]+d.qfrc_bias[v],-limit,limit))
        d.qfrc_applied[v]=force
        return force
    def world_step(unused):
        nonlocal incoming,last_ball_velocity,last_robot_ball_contact,first_ball_pos,next_ball_sample,ball_launched,impact_next,rod_run
        t=float(d.time)
        if a.events in ('all','ball') and not ball_launched and t < ball_launch_time_s:
            # Display-only delayed launch: hold the free ball at its reset pose
            # until the scheduled demonstration impulse. Formal evaluations
            # use the default launch time zero and never enter this branch.
            d.qpos[ball_qpos_adr:ball_qpos_adr + 7] = ball_hold_qpos
            d.qvel[ball_dof:ball_dof + 6] = 0.0
        if a.events in ('all','ball') and not ball_launched and t >= ball_launch_time_s:
            # Presentation-only delayed launch is opt-in. The default remains
            # the frozen reset impulse at t=0 used by every formal evaluation.
            d.qvel[ball_dof+1]=a.ball_speed
            ball_launched = True
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
        resultant={};touch_ball=False;corner_target_force=0.;edge_force=0.
        for i in range(d.ncon):
            ct=d.contact[i];g1,g2=int(ct.geom1),int(ct.geom2)
            if unexpected_edge and edge_geom in (g1,g2) and (g2 if g1==edge_geom else g1) in (robot|{target_geom}):
                edge_wrench=np.zeros(6);mujoco.mj_contactForce(m,d,i,edge_wrench)
                edge_force+=float(np.linalg.norm(edge_wrench[:3]))
                stats['unexpected_edge']['max_penetration_m']=max(stats['unexpected_edge']['max_penetration_m'],-float(ct.dist))
            if target_geom in (g1,g2) and (g2 if g1==target_geom else g1) in corner_contact_geoms:
                corner_wrench=np.zeros(6);mujoco.mj_contactForce(m,d,i,corner_wrench)
                corner_target_force+=float(np.linalg.norm(corner_wrench[:3]))
            if m.geom_bodyid[g1]!=m.geom_bodyid[g2] and -ct.dist>stats['max_penetration_m']:
                stats['max_penetration_m']=-float(ct.dist)
                stats['worst_pair']=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g) or str(g) for g in (g1,g2)]
            if (g1 in robot)==(g2 in robot):continue
            other=g2 if g1 in robot else g1
            if is_external_contact(m,robot,target_body,g1,g2) and -ct.dist>stats['max_external_penetration_m']:
                stats['max_external_penetration_m']=-float(ct.dist)
                stats['worst_external_pair']=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g) or str(g) for g in (g1,g2)]
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
        if unexpected_edge and edge_force>.05:
            rec=stats['unexpected_edge']
            if rec['first_s'] is None:rec['first_s']=t
            rec['last_s']=t;rec['duration_s']+=m.opt.timestep
            rec['peak_n']=max(rec['peak_n'],edge_force);rec['impulse_ns']+=edge_force*m.opt.timestep
            stage_name=task.names[task.index]
            rec['by_stage'][stage_name]=rec['by_stage'].get(stage_name,0.)+m.opt.timestep
        diagnostics=stats['contact_diagnostics']
        if corner_target_force>.05:
            stage_name=task.names[task.index]
            rec=diagnostics['corner_target_by_stage'].setdefault(stage_name,dict(first_s=t,last_s=t,duration_s=0.,peak_n=0.))
            rec['last_s']=t;rec['duration_s']+=m.opt.timestep
            rec['peak_n']=max(rec['peak_n'],corner_target_force)
        if 'rod' in resultant:
            hand_xy=d.xpos[env._hand_id,:2].copy()
            if rod_run is None:
                rod_run=dict(first_s=t,last_s=t,duration_s=0.,start_xy=hand_xy,last_xy=hand_xy)
            rod_run['last_s']=t;rod_run['duration_s']+=m.opt.timestep;rod_run['last_xy']=hand_xy
        elif rod_run is not None:
            candidate=dict(first_s=rod_run['first_s'],last_s=rod_run['last_s'],duration_s=rod_run['duration_s'],
                           hand_xy_displacement_m=float(np.linalg.norm(rod_run['last_xy']-rod_run['start_xy'])))
            longest=diagnostics['rod_longest_run']
            if longest is None or candidate['duration_s']>longest['duration_s']:
                diagnostics['rod_longest_run']=candidate
            rod_run=None
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
        if cup>=0:
            stats['cup_shift_m']=max(stats['cup_shift_m'],float(np.linalg.norm((d.xpos[cup]-cup_initial)[:2])))
            stats['cup_tilt_deg']=max(stats['cup_tilt_deg'],float(np.rad2deg(np.arccos(np.clip(d.xmat[cup].reshape(3,3)[2,2],-1,1)))))
        stats['max_hand_displacement_m']=max(stats['max_hand_displacement_m'],float(np.linalg.norm(d.xpos[env._hand_id]-initial_hand)))
        stats['peak_motor_torque_nm']=max(stats['peak_motor_torque_nm'],float(abs(d.qfrc_actuator[:7]).max()))
        metrics.sample()
        if impact_renderer is not None and float(d.time) <= ball_launch_time_s+.65 and float(d.time)+1e-12 >= impact_next:
            impact_renderer.update_scene(d,camera=impact_overview);slow1=Image.fromarray(impact_renderer.render())
            impact_renderer.update_scene(d,camera=impact_detail);slow2=Image.fromarray(impact_renderer.render())
            frame=Image.new('RGB',(1280,520),(15,22,30));frame.paste(slow1,(0,40));frame.paste(slow2,(640,40))
            ImageDraw.Draw(frame).text((12,10),f'Impact slow motion | t={d.time:.4f}s | ball / end-effector',font=font,fill='white')
            impact_slow_frames.append(frame);impact_next+=.01
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
        if getattr(a,'impact_slowmo',False):
            impact_renderer=mujoco.Renderer(m,height=480,width=640)
            impact_overview=overview;impact_detail=detail
    abort_reason=None
    for step_index in range(planned_steps):
        if a.task=='pick_place':
            wrench=equivalent_tool_wrench(body_jacobian(m,d,env._hand_id),load_observer.filtered)
            before=task.index
            if bool(getattr(a,'corner_placement',False)) and not planned_corner and task.index==5:
                # Corner-only release: the payload may be released once the
                # known support geom is carrying it and its translational
                # speed is low.  This is evaluator bookkeeping; no contact
                # truth is added to the actor observation.
                task.corner_release_ok=(contact_support(m,d,target_geom,task.support_geoms)
                                         and np.linalg.norm(d.cvel[env._target_body_id,3:])<.02)
            if task.update(d.qpos,d.qvel,d.xpos[env._hand_id],d.xmat[env._hand_id].reshape(3,3),body_twist(m,d,env._hand_id),wrench):
                task_events.append(dict(stage=task.names[task.index],time_s=float(d.time)))
            if before==5 and task.index==6:release_truth=contact_support(m,d,target_geom,task.support_geoms)
            task.advance_gripper()
        signal={};applied=np.zeros(7)
        if load_observer:
            position=d.xpos[env._hand_id].copy();rotation=d.xmat[env._hand_id].reshape(3,3).copy()
            twist=body_twist(m,d,env._hand_id);command=env._wbc_command(0.)
            error=np.r_[command.target_position_m-position,so3_log(command.target_rotation@rotation.T)]
            wrench=equivalent_tool_wrench(body_jacobian(m,d,env._hand_id),load_observer.filtered)
            observation=canonical_observation(d.qpos,d.qvel,command.task_twist_world,error,twist,
                                              load_observer.filtered,wrench,task.path_direction)
            signal=dict(neuron_time=float(d.time),neuron_qpos=d.qpos.copy(),observation=observation,
                        applied_action=applied.copy(),prior_contact_peak=interval_peak.copy(),
                        prior_contact_impulse=interval_impulse.copy(),
                        task_ready_s=float(task.ready) if hasattr(task,'ready') else 0.,
                        task_position_error_m=float(np.linalg.norm(error[:3])),
                        task_rotation_error_rad=float(np.linalg.norm(error[3:])),
                        task_speed_mps=float(np.linalg.norm(twist[:3])),
                        task_carry_load=float(task.carry_load) if getattr(task,'carry_load',None) is not None else np.nan)
        if esn:
            if policy_observation_dim==45:observation=np.r_[observation[:39],observation[39:42],observation[45:]]
            if observation.shape!=(policy_observation_dim,):raise ValueError(f'Expected {policy_observation_dim}D observation, got {observation.shape}')
            policy_state=getattr(esn,'obj',esn)
            previous_state=prepare_policy_state(esn,memory_ablation)
            pulse_remaining_before=int(getattr(esn,'selector_pulse_remaining',0));pulse_used_before=bool(getattr(esn,'selector_pulse_used',False))
            predicted=esn.act(observation)
            pulse_active=bool(pulse_remaining_before>0 or (not pulse_used_before and getattr(esn,'selector_pulse_used',False)))
            if a.esn_mode=='control':applied=predicted.copy()
            current_state = policy_state.state.copy() if hasattr(policy_state, 'state') else np.empty(0, dtype=float)
            signal.update(dict(neuron_time=float(d.time),neuron_qpos=d.qpos.copy(),observation=observation,
                        reservoir_state=current_state,reservoir_delta=current_state-previous_state,
                        esn_action=predicted,applied_action=applied.copy(),
                        selector_pulse_active=pulse_active,
                        prior_contact_peak=interval_peak.copy(),prior_contact_impulse=interval_impulse.copy()))
            if hybrid_teacher is not None:
                teacher_action=hybrid_teacher.act(wrench,.04)
                applied=(1.0-hybrid_blend)*teacher_action+hybrid_blend*predicted
                signal.update(hybrid_teacher_action=teacher_action.copy(),hybrid_blend=hybrid_blend,
                             applied_action=applied.copy())
        if teacher:
            applied=teacher.act(wrench,.04) if a.teacher=='vmc6d' else teacher.act(wrench[:3],error[:3],twist[:3],task.path_direction,.04)
            signal.update(teacher_action=applied.copy(),applied_action=applied.copy())
        interval_peak[:]=0.;interval_impulse[:]=0.
        env.step(applied)
        max_lift=max(max_lift,float(d.xpos[env._target_body_id,2]-.425))
        if a.task=='pick_place':
            supported=contact_support(m,d,target_geom,task.support_geoms)
            near=np.linalg.norm(d.xpos[env._target_body_id,:2]-task.destination[:2])<.025
            slow=np.linalg.norm(d.qvel[env._target_dof:env._target_dof+3])<.015
            if planned_corner:
                released=sum(d.qpos[task.fingers])>.075 and not contact_support(m,d,target_geom,robot)
                height_ok=abs(d.xpos[env._target_body_id,2]-task.destination[2])<.015
                angular_slow=np.linalg.norm(d.qvel[env._target_dof+3:env._target_dof+6])<.15
                placement_hold=placement_hold+.04 if supported and near and slow and released and height_ok and angular_slow else 0.
            else:
                placement_hold=placement_hold+.04 if task.index==7 and supported and near and slow else 0.
        records.append(dict(time=float(d.time),qpos=d.qpos.copy(),qvel=d.qvel.copy(),ctrl=d.ctrl.copy(),
                            mocap_pos=d.mocap_pos.copy(),mocap_quat=d.mocap_quat.copy(),
                            hand=d.xpos[env._hand_id].copy(),ball=d.xpos[ball].copy(),ball_velocity=d.qvel[ball_dof:ball_dof+3].copy(),cup=d.xpos[cup].copy() if cup>=0 else np.zeros(3),stage=task.index,object_position=d.xpos[env._target_body_id].copy(),**signal))
        if step_index%25==0:
            progress=dict(time_s=float(d.time),stage=task.names[task.index],position_error_m=signal.get('task_position_error_m'),
                          external_penetration_mm=1000*stats['max_external_penetration_m'])
            a.output.with_suffix('.progress.json').write_text(json.dumps(progress,allow_nan=False))
        if renderer:
            renderer.update_scene(d,camera=overview);im1=Image.fromarray(renderer.render())
            renderer.update_scene(d,camera=detail);im2=Image.fromarray(renderer.render())
            im=Image.new('RGB',(1280,520),(15,22,30));im.paste(im1,(0,40));im.paste(im2,(640,40))
            ImageDraw.Draw(im).text((12,10),f'Office scene validation | {d.time:.2f}s | ball / human hand / rod | WBC {a.task}: {task.names[task.index]}',font=font,fill='white')
            video.send(np.asarray(im));frames.append(im)
        if not np.isfinite(np.r_[d.qpos,d.qvel,d.qacc]).all():abort_reason='nonfinite_physics';break
        if stats['max_penetration_m']>.002:abort_reason='global_penetration_exceeded_2mm';break
    if video:video.close()
    if frames:
        frames[0].save(a.output.with_suffix('.gif'),save_all=True,append_images=frames[1:],duration=40,loop=0)
        frames[0].save(a.output.with_suffix('.png'))
        for sec in (.12,5.,13.):
            frames[min(len(frames)-1,round(sec/.04))].save(a.output.parent/(a.output.name+f'_at_{sec:g}.png'))
    if impact_slow_frames:
        slow_gif=a.output.parent/(a.output.name+'_impact_slowmo.gif')
        slow_mp4=a.output.parent/(a.output.name+'_impact_slowmo.mp4')
        impact_slow_frames[0].save(slow_gif,save_all=True,append_images=impact_slow_frames[1:],duration=40,loop=0)
        import imageio_ffmpeg
        command=[imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','1280x520','-framerate','25',
                 '-i','pipe:0','-an','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(slow_mp4)]
        process=subprocess.Popen(command,stdin=subprocess.PIPE)
        for frame in impact_slow_frames:process.stdin.write(frame.tobytes())
        process.stdin.close()
        if process.wait()!=0:raise RuntimeError('Impact slow-motion encoding failed')
    cup_supported=False
    for i in range(d.ncon):
        c=d.contact[i]
        if cup_base>=0 and {int(c.geom1),int(c.geom2)}=={cup_base,desk}:
            f=np.zeros(6);mujoco.mj_contactForce(m,d,i,f);cup_supported=cup_supported or f[0]>.05
    bounce=bool(incoming is not None and incoming[1]>.05 and any(v[1]<-.05 for v in bounce_samples))
    separation=float(np.linalg.norm(d.xpos[ball]-first_ball_pos)) if first_ball_pos is not None else None
    required={'all':('ball','person_hand','rod'),'ball':('ball',),'person':('person_hand',),'rod':('rod',),'settle':()}[a.events]
    if bool(getattr(a,'combined_contact_v2',False)) and a.events=='all':
        # The registered combined fixture has an explicit, stricter exposure
        # contract: the cup and pillar must each receive a real force-bearing
        # brush.  Formal penetration and task gates remain unchanged.
        required=('ball','person_hand','rod','cup','office_v5_pillar')
    if (bool(getattr(a,'combined_thick_corner_pillar_v1',False)) or bool(getattr(a,'combined_thick_corner_pillar_v2',False)) or bool(getattr(a,'combined_thick_corner_pillar_v3',False)) or bool(getattr(a,'combined_thick_corner_pillar_v4',False))) and a.events=='all':
        # Single-obstacle successor to combined-demo: the cup is omitted;
        # pillar, ball, hand and sustained rod contact remain auditable.
        required=('ball','person_hand','rod','office_v5_pillar')
    contact_ok=all(stats['events'].get(k,{}).get('duration_s',0)>(.0002 if k=='ball' else .4) for k in required)
    cup_valid=(True if cup<0 else bool(cup_supported and np.linalg.norm(d.cvel[cup,3:])<.02 and stats['cup_shift_m']<.02 and stats['cup_tilt_deg']<10.))
    result=dict(purpose='frozen_policy_office_complex_evaluation' if esn else 'scene_development_acceptance_no_policy_training',arguments=vars(a),fixture=flags,
      stats=stats,ball_initial_velocity=[0,a.ball_speed if a.events in ('all','ball') else 0,0],
      ball_launch_time_s=ball_launch_time_s,ball_actuated_after_reset=bool(ball_launch_time_s > 0.0),
      ball_incoming_velocity=incoming,ball_rebound=bounce,ball_final_separation_m=separation,
      cup_supported=cup_supported,cup_present=bool(cup>=0),cup_final_speed=float(np.linalg.norm(d.cvel[cup,3:])) if cup>=0 else None,
      placement_destination=task.destination if a.task=='pick_place' else None,
      placement_support_geoms=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g) for g in (task.support_geoms if a.task=='pick_place' else ())],
      initial_geometry_valid=True,physical_valid=abort_reason is None and stats['max_external_penetration_m']<=.0002,
      legacy_global_penetration_valid=stats['max_penetration_m']<=.0002,
      abort_reason=abort_reason,execution_complete=abort_reason is None and len(records)==planned_steps,
      full_task_horizon_completed=probe is None and abort_reason is None and len(records)==planned_steps,
      contact_coverage_valid=contact_ok,contact_required=list(required),cup_valid=cup_valid,passed=abort_reason is None and contact_ok and stats['max_external_penetration_m']<=.0002 and cup_valid and (bounce if 'ball' in required else True),
      human_model='guided massive torso with shoulder/elbow hinges and compliant wrist; not free biped gait',
      controller='existing kinematic WBC pose hold, unlocked joints, zero learned residual',schedule=configs,
      interaction_schedule=getattr(a,'interaction_schedule','legacy'),
      source_sha256={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in
        ('office_complex_scene_v5_20260917.py','validate_office_apparatus_v5_20260917.py','audit_office_complex_scene_v5_20260917.py')})
    result['controller']='existing kinematic WBC '+a.task+', unlocked joints, zero learned residual'
    if rod_run is not None:
        candidate=dict(first_s=rod_run['first_s'],last_s=rod_run['last_s'],duration_s=rod_run['duration_s'],
                       hand_xy_displacement_m=float(np.linalg.norm(rod_run['last_xy']-rod_run['start_xy'])))
        longest=stats['contact_diagnostics']['rod_longest_run']
        if longest is None or candidate['duration_s']>longest['duration_s']:
            stats['contact_diagnostics']['rod_longest_run']=candidate
    result['task_events']=task_events
    result['physics_resolution']=dict(base_dt_s=a.dt,initial_refinement_dt_s=refinement,
        refinement_until_s=refine_until if refinement is not None else None,
        actor_schedule_input=False,metric_weighting='physical time',
        note=('New planned-hand-corner task/reference and placement success protocol; materials and actuator limits unchanged'
              if planned_corner else 'Numerical resolution schedule only; world impulses, drives, materials and task gates unchanged'))
    result['final_task_stage']=task.names[task.index]
    result['observer_settings']=dict(**observer_kwargs,filter_tau_s=.04,truth_in_observer=False)
    result['placement_complete']=bool(a.task=='pick_place' and placement_hold>=.5 and release_truth and max_lift>.10
       and np.linalg.norm(d.xpos[env._hand_id]-task.goals[-1])<.015 and sum(d.qpos[task.fingers])>.075)
    if planned_corner:
        result['placement_complete']=bool(placement_hold>=.5 and max_lift>.10)
    result['task_success']=bool(result['full_task_horizon_completed'] and result['placement_complete']) if a.task=='pick_place' else result['full_task_horizon_completed']
    if probe is not None:result['purpose']='short_horizon_physics_probe_not_task_evaluation'
    result['strict_success']=bool(result['task_success'] and result['passed'])
    if planned_corner:
        result['legacy_strict_success']=result['strict_success']
        result['strict_success']=bool(result['task_success'] and result['physical_valid'])
        result['success_definition']='planned-hand-corner-v1: released payload supported in 25mm XY/15mm Z target region, linear speed <15mm/s and angular speed <0.15rad/s for final 0.5s; full horizon and lift >0.1m; contact coverage is diagnostic only'
        result['path_plan']=path_plan
        result['placement_hold_s']=placement_hold
        result['object_final_position']=d.xpos[env._target_body_id].copy()
        result['placement_error_xy_m']=float(np.linalg.norm(d.xpos[env._target_body_id,:2]-task.destination[:2]))
        result['source_sha256']['planned_hand_corner_20261002.py']=hashlib.sha256(Path(__file__).with_name('planned_hand_corner_20261002.py').read_bytes()).hexdigest()
    if unexpected_edge:
        result['unexpected_edge_safe']=bool(stats['unexpected_edge']['max_penetration_m']<=.0002)
        result['strict_success']=bool(result['strict_success'] and result['unexpected_edge_safe'])
        result['unknown_obstacle_protocol']='prior-map-omission-edge-v1; fixed physical lip, no online sensing/replanning'
    result['release_supported']=release_truth
    result['max_lift_m']=max_lift
    result['neural_logging']=dict(enabled=esn is not None,mode=a.esn_mode,model=str(a.esn_model) if a.esn_model else None,
        model_sha256=hashlib.sha256(a.esn_model.read_bytes()).hexdigest() if esn else None,
        hybrid_vmc_blend=hybrid_blend,
        policy_contract=policy_contract,observation_dim=policy_observation_dim,
        memory_ablation=memory_ablation,
        reservoir_size=(int(getattr(getattr(esn,'obj',esn),'state').size)
                        if esn is not None and hasattr(getattr(esn,'obj',esn),'state') else 0),policy_hz=25,
        state_semantics='post-update leaky reservoir state, before physics step; fixed unit ordering',
        contact_semantics='prior_contact_* covers the preceding physics interval; contact truth is diagnostics ONLY',
        contact_keys=contact_keys,force_truth_in_actor=False,weights_changed=False)
    if policy_contract and policy_contract.startswith('proprio48_'):
        policy_source=Path(__file__).with_name('current_student_policy_20260921.py')
        result['source_sha256'][policy_source.name]=hashlib.sha256(policy_source.read_bytes()).hexdigest()
        if policy_contract=='proprio48_office_vmc_memory_esn_v1':
            policy_source=Path(__file__).with_name('office_vmc_memory_esn_20260927.py')
            result['source_sha256'][policy_source.name]=hashlib.sha256(policy_source.read_bytes()).hexdigest()
    if esn:result['controller']+=(' + ESN action residual' if a.esn_mode=='control' else ' (ESN shadow observer only)')
    if hybrid_teacher:result['controller']+=f' + proprioceptive VMC blend ({hybrid_blend:.3f} ESN weight)'
    if teacher:
        result['controller']='existing kinematic WBC '+a.task+' + '+a.teacher+' encoder-wrench VMC teacher'
        result['teacher_parameters']={k:v for k,v in vars(teacher).items() if isinstance(v,(float,int,str,np.ndarray))}
    result['metrics']=metrics.save(a.output.parent/(a.output.name+'_metrics'))
    result['model_sha256']=hashlib.sha256(a.output.with_suffix('.mjb').read_bytes()).hexdigest()
    for name in ('office_task_v4_20260917.py','run_contact_transfer_20260916.py','audited_velocity_env.py',
                 'wbc_velocity_residual_core.py','fixed_panda_wbc.py','haptic_vmc_teacher_20260916.py',
                 'physics_substep_metrics_20260923.py','run_benchmark.py'):
        result['source_sha256'][name]=hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
    if teacher:
        for name in ('run_vmc_6d_constrained_push_20260918.py','contact_memory_vmc_20260916.py'):
            result['source_sha256'][name]=hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
    a.output.with_suffix('.json').write_text(json.dumps(clean(result),indent=2,allow_nan=False))
    np.savez_compressed(a.output.with_suffix('.npz'),**{k:np.array([r[k] for r in records]) for k in records[0]})
    np.savez_compressed(a.output.parent/(a.output.name+'_ball_detail.npz'),
        time=np.array([r[0] for r in ball_detail]),qpos=np.array([r[1] for r in ball_detail]),
        velocity=np.array([r[2] for r in ball_detail]),contact=np.array([r[3] for r in ball_detail]))
    if a.render:
        mujoco.mj_saveLastXML(str(a.output.with_suffix('.xml')),m)
    if impact_renderer:impact_renderer.close()
    if renderer:renderer.close()
    env.close();print(json.dumps(clean(result)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--render',action='store_true')
    p.add_argument('--impact-slowmo',action='store_true',help='Save a separate 4x playback slow-motion impact clip')
    p.add_argument('--events',choices=('settle','ball','person','rod','all'),default='all')
    p.add_argument('--task',choices=('hold','pick_place'),default='hold')
    p.add_argument('--corner-placement',action='store_true',
                   help='Development-only: place the payload on office_v5_corner_top')
    p.add_argument('--planned-hand-corner',action='store_true',
                   help='New task protocol: static-map planned route to hand-side corner; released placement is task success, contact coverage diagnostic only')
    p.add_argument('--unexpected-edge',action='store_true',help='Independent fixture: a supported physical lip absent from the prior planning map')
    p.add_argument('--allow-lateral-rejoin',action='store_true',help='Proprioceptive waypoint-plane progress permits contact detours; same for every method')
    p.add_argument('--interaction-demo',action='store_true',
                   help='Development-only: move cup/pillar onto the corner approach for physical contact')
    p.add_argument('--combined-demo',action='store_true',
                   help='Development-only: combined cup/pillar contact plus corner placement route')
    p.add_argument('--combined-contact-v2',action='store_true',
                   help='Registered combined fixture with cup/pillar on the audited carry/retreat path')
    p.add_argument('--combined-thick-corner-pillar-v1',action='store_true',
                   help='Development fixture: delayed ball, one pillar, sustained rod rub and thick-corner placement')
    p.add_argument('--combined-thick-corner-pillar-v2',action='store_true',
                   help='Independent development fixture: visible pillar and corner moved into the measured lift corridor')
    p.add_argument('--combined-thick-corner-pillar-v3',action='store_true',
                   help='Independent development fixture: local thick-corner face contacts the payload during lift')
    p.add_argument('--combined-thick-corner-pillar-v4',action='store_true',
                   help='Independent development fixture: unobstructed ball lane with a lift-side corner face')
    p.add_argument('--relaxed-pillar',action='store_true',
                   help='Development-only: reduce pillar radius/friction/compliance for a registered diagnostic')
    p.add_argument('--seed',type=int,default=2026091751);p.add_argument('--variant',type=int,default=0)
    p.add_argument('--duration',type=float,default=21.);p.add_argument('--dt',type=float,default=.00005)
    p.add_argument('--ball-speed',type=float,default=1.7);p.add_argument('--ball-launch-time-s',type=float,default=0.0,
                   help='Display-only delayed ball launch. Keep at zero for frozen formal evaluation.')
    p.add_argument('--person-stroke',type=float,default=.20)
    p.add_argument('--rod-stroke',type=float,default=.235)
    p.add_argument('--esn-model',type=Path)
    p.add_argument('--esn-mode',choices=('shadow','control'),default='shadow')
    p.add_argument('--hybrid-vmc-blend',type=float,default=0.0,
                   help='Development-only convex blend weight for ESN and proprioceptive VMC action; no new observation fields')
    p.add_argument('--memory-ablation',choices=('none','reset_each_observation'),default='none',
                   help='Diagnostic only: remove inter-observation reservoir history, preserving weights and current input')
    p.add_argument('--disable-selector-pulse',action='store_true',help='Diagnostic ablation only; preserve checkpoint weights')
    p.add_argument('--teacher',choices=('none','vmc6d','memory'),default='none',help='Development-only encoder-wrench teacher collection')
    p.add_argument('--physics-probe-s',type=float,help='Diagnostic-only early horizon; never eligible for task success')
    p.add_argument('--impact-refinement-dt',type=float,help='Shared fine physics step for initial impulse, no actor input')
    p.add_argument('--impact-refinement-until',type=float,default=.2)
    p.add_argument('--person-start',type=float,default=3.)
    p.add_argument('--interaction-schedule',choices=('legacy','sequential-r12-v1'),default='legacy',
                   help='World-only protocol label and timing guard; sequential-r12-v1 requires explicit starts 3/12 and rod hold 6')
    p.add_argument('--rod-start',type=float,default=11.)
    p.add_argument('--rod-hold',type=float,default=3.)
    p.add_argument('--observer-friction-velocity-scale',type=float,default=.005)
    run(p.parse_args())
