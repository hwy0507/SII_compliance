"""Isolated training-scene adapter around the unchanged office evaluator.

Only offline world generation, apparatus drives and ball launch coordinates
are adapted. Actor, task gates, actuator filter and physics audit stay shared.
"""
import argparse
import ast
import inspect
import json
import os
from pathlib import Path
import resource
import sys
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import numpy as np

from teacher_bank_design_20260930 import DT, DURATION, sha, write


def numbers(values):
    return ' '.join(f'{float(v):.12g}' for v in values)


def training_xml(xml, fixture):
    root=ET.fromstring(xml);world=root.find('worldbody')
    # Training primitives are independent of the frozen combined evaluation.
    for parent in root.iter():
        for element in list(parent):
            if element.get('name') in ('office_v5_pillar','office_v5_pillar_mount','office_v5_cup'):
                parent.remove(element)
    def named(tag,name):
        node=root.find(f".//{tag}[@name='{name}']")
        if node is None: raise ValueError(name)
        return node
    payload=named('geom','target_object_geom');payload.set('mass',str(fixture['payload_mass_kg']))
    face=named('geom','office_v5_corner_face')
    if fixture['category']=='passive_corner':
        face.set('euler',numbers([0,0,fixture['corner_yaw_rad']]))
        widths={'square_edge':[.012,.010,.020],'wide_edge':[.012,.016,.020],'thick_edge':[.018,.010,.028]}
        size=widths[fixture['object_shape']];yaw=fixture['corner_yaw_rad']
        extent_x=abs(np.cos(yaw))*size[0]+abs(np.sin(yaw))*size[1]
        raised='corner_bottom_z_m' in fixture
        center_z=fixture['corner_bottom_z_m']+size[2] if raised else fixture['corner_top_z_m']-size[2]
        face.set('pos',numbers([fixture['corner_right_x_m']-extent_x,fixture['corner_center_y_m'],center_z]))
        face.set('size',numbers(size))
        face.set('friction',numbers([fixture['corner_friction'],.01,.001]))
        # Connect the local apron to the support slab: an isolated floating box
        # is not a thick table corner. All pieces remain rigid world geoms.
        pos=np.fromstring(face.get('pos'),sep=' ');top=named('geom','office_v5_corner_top')
        top_pos=np.fromstring(top.get('pos'),sep=' ');top_size=np.fromstring(top.get('size'),sep=' ')
        end=top_pos[0]-top_size[0]+.004
        # Route the rigid connector around the initial gripper. A direct bridge
        # crossed the fingers before t=0; retain that failed fixture revision.
        route_y=-.08;half_width=.006
        pieces=(
            ('office_v5_corner_training_bridge',[pos[0],(pos[1]+route_y)/2,.510],
             [half_width,(route_y-pos[1])/2+half_width,half_width]),
            ('office_v5_corner_training_bridge_connector',[(pos[0]+end)/2,route_y,.510],
             [(end-pos[0])/2+half_width,half_width,half_width]))
        if raised:
            # Route behind the hand wing and outside the wrist's swept volume.
            # Keep the raised thick face physically joined to the lower support.
            route_y=-.480;bridge_z=pos[2];column_x=top_pos[0];low_z=.510
            top_join_y=top_pos[1]-top_size[1]+.020
            pieces=(
                ('office_v5_corner_training_bridge',[pos[0],(pos[1]+route_y)/2,bridge_z],
                 [half_width,(pos[1]-route_y)/2+half_width,half_width]),
                ('office_v5_corner_training_bridge_connector',[(pos[0]+column_x)/2,route_y,bridge_z],
                 [(column_x-pos[0])/2+half_width,half_width,half_width]),
                ('office_v5_corner_training_bridge_column',[column_x,route_y,(bridge_z+low_z)/2],
                 [half_width,half_width,(bridge_z-low_z)/2+half_width]),
                ('office_v5_corner_training_bridge_support_join',[column_x,(route_y+top_join_y)/2,low_z],
                 [half_width,(top_join_y-route_y)/2+half_width,half_width]))
        for name,center,size in pieces:
            if min(size)<=0:raise ValueError('Invalid routed corner bridge extent')
            ET.SubElement(world,'geom',name=name,type='box',pos=numbers(center),size=numbers(size),
                contype=face.get('contype','1'),conaffinity=face.get('conaffinity','1'),
                rgba='.50 .32 .18 1',friction=face.get('friction'),solref=face.get('solref','.002 1'))
    else:
        world.remove(face)  # table support remains; no passive obstacle in active primitives
    ball=named('body','office_v5_ball');ball_geom=named('geom','office_v5_ball_geom')
    if fixture['category']=='active_short':
        ball.set('pos',numbers(fixture['launch_position_m']))
        radius=fixture['ball_radius_m'];shape=fixture['object_shape']
        ball_geom.set('type',shape)
        ball_geom.set('size',numbers([radius] if shape=='sphere' else [radius,.75*radius,radius] if shape=='ellipsoid' else [.75*radius,.5*radius]))
        ball_geom.set('mass',str(fixture['ball_mass_kg']))
    else:
        ball.set('pos','1.7 -1.5 .3')
    # Place the chosen finite-mass apparatus using a PRECOMPUTED nominal path.
    # It never tracks actual robot position or changes direction during execution.
    rod=named('body','office_v5_push_rod');person=named('body','office_v5_person')
    if fixture['category']=='active_long':
        yaw=fixture['yaw_rad'];axis=np.array(fixture['axis']);target=np.array(fixture['target_nominal_m'])
        c,s=np.cos(yaw),np.sin(yaw);rotation=np.array([[c,-s,0],[s,c,0],[0,0,1]])
        if fixture['apparatus']=='rod':
            rod.set('euler',numbers([0,0,yaw]))
            rod.set('pos',numbers(target-axis*(fixture['stroke_m']+.045-.02)))
            geom=named('geom','office_v5_push_rod_geom')
            geom.set('mass',str(fixture['rod_mass_kg']))
            if fixture['object_shape']=='paddle':
                geom.attrib.pop('fromto',None);geom.set('type','box');geom.set('pos','.005 0 0')
                geom.set('size','.04 .035 .02')
            else: geom.set('size',str(fixture['rod_radius_m']))
            person.set('pos','2.5 1 -.35')
        else:
            # Tip position relative to torso origin with shoulder/elbow at zero.
            person.set('euler',numbers([0,0,yaw]))
            fingertip=np.array([-.035-.19-.19-.102,0,1.18-.10-.12-.005])
            person.set('pos',numbers(target+axis*(fixture['stroke_m']-.02)-rotation@fingertip))
            rod.set('pos','1.7 1.5 .3')
    else:
        rod.set('pos','1.7 1.5 .3');person.set('pos','2.5 1 -.35')
    return ET.tostring(root,encoding='unicode')


def adapted_run(module, method='vmc'):
    """Checked source adaptation; fail if upstream evaluator changes shape."""
    source=inspect.getsource(module.run)
    replacements={
        'd.qvel[ball_dof+1]=a.ball_speed':'d.qvel[ball_dof:ball_dof+3]=TRAIN_BALL_VELOCITY',
        "if t<.30 and (t>=next_ball_sample or touch_ball):":"if ball_launch_time_s <= t < ball_launch_time_s+.5 and (t>=next_ball_sample or touch_ball):",
        'incoming[1]>.05 and any(v[1]<-.05 for v in bounce_samples)':
            'np.dot(incoming, TRAIN_BALL_AXIS)>.05 and any(np.dot(v, TRAIN_BALL_AXIS)<-.05 for v in bounce_samples)',
        'metrics.sample()':'metrics.sample(); TRAIN_OBSERVER(m, d, env, task)',
    }
    for old,new in replacements.items():
        expected=2 if old.startswith('d.qvel') else 1
        if source.count(old)!=expected: raise RuntimeError('Evaluator adapter mismatch: '+old)
        source=source.replace(old,new)
    if method!='vmc':
        call='applied=teacher.act(wrench,.04) if'
        if source.count(call)!=1:raise RuntimeError('Teacher call adapter changed')
        source=source.replace(call,'applied=teacher.act(observation,.04) if')
    tree=ast.parse(source)
    class ConfigAdapter(ast.NodeTransformer):
        count=0
        def visit_Assign(self,node):
            if any(isinstance(t,ast.Name) and t.id=='configs' for t in node.targets):
                self.count+=1;node.value=ast.Name(id='TRAIN_CONFIGS',ctx=ast.Load())
            return self.generic_visit(node)
    adapter=ConfigAdapter();tree=adapter.visit(tree)
    if adapter.count!=1: raise RuntimeError('Expected one apparatus schedule')
    exec(compile(ast.fix_missing_locations(tree),module.__file__,'exec'),module.__dict__)


def controller_contract(method):
    contracts={
        'vmc':dict(controller='VMC stable-readout teacher',input_contract='canonical48D; estimated wrench[39:45] only',
                   control_location='action7 residual upstream of shared action filter and motor servo'),
        'admittance':dict(controller='Cartesian admittance shifted-reference baseline',
                   input_contract='canonical48D; arm encoders, nominal twist, pose error, estimated joint load; robot FK/J',
                   control_location='M-D-K shifted WBC reference mapped to action7 residual, shared filter and motor servo'),
        'impedance':dict(controller='Cartesian impedance moving-reference baseline',
                   input_contract='canonical48D actor interface; robot pose/twist/J and nominal WBC command at servo',
                   control_location='Cartesian spring/damper torque backend through shared motor limiter; action7 is zero'),
    }
    if method not in contracts:raise ValueError(method)
    return dict(method=method,**contracts[method])


def direct_arm_mapping(model):
    """Verify ctrl[0:7] maps 1:1 to the recorded qfrc_actuator[0:7].

    MuJoCo enums joint transmission/fixed gain/no bias/no dynamics are zero.
    Additional generalized actuator contributions are still caught by the
    actual physical trace comparison below; they are not assumed absent.
    """
    if model.nu<7:raise AssertionError('Missing seven arm actuators')
    joints=np.asarray(model.actuator_trnid[:7,0],int)
    if np.any(joints<0) or not np.array_equal(model.jnt_dofadr[joints],np.arange(7)):
        raise AssertionError('Arm actuator to generalized-DOF mapping changed')
    for key in ('actuator_trntype','actuator_gaintype','actuator_biastype','actuator_dyntype'):
        if np.any(np.asarray(getattr(model,key))[:7]!=0):raise AssertionError('Non-direct arm '+key)
    expected=np.zeros((7,6));expected[:,0]=1.
    np.testing.assert_allclose(model.actuator_gear[:7],expected,rtol=0,atol=0)
    np.testing.assert_allclose(model.actuator_gainprm[:7,0],1.,rtol=0,atol=0)
    return dict(actuator_indices=list(range(7)),generalized_dof_indices=list(range(7)),
                joint_indices=joints.tolist(),transmission='verified direct unit-gear fixed-unit-gain torque actuators')


def audit_impedance_execution(servo, physics):
    """Connect limiter output at servo START to completed physical intervals.

    EpisodeMetrics timestamps are post-mj_step END times, while torque is the
    retained force evaluation within that step. Use [end-dt,end], not end
    alone: a sample ending at the next servo boundary belongs to the previous
    held command. This is valid only after direct_arm_mapping verification.
    """
    starts=np.asarray(servo['time'],float);period=np.asarray(servo['dt'],float)
    requested=np.asarray(servo['applied_torque'],float)
    end=np.asarray(physics['time'],float);dt=np.asarray(physics['dt'],float)
    actual=np.asarray(physics['qfrc_actuator'])
    if starts.ndim!=1 or len(starts)==0 or period.shape!=starts.shape or requested.shape!=(len(starts),7):
        raise AssertionError('Invalid servo execution shape')
    if end.ndim!=1 or len(end)==0 or dt.shape!=end.shape or actual.shape!=(len(end),7):
        raise AssertionError('Invalid physical execution shape')
    if not all(np.isfinite(v).all() for v in (starts,period,requested,end,dt,actual)):
        raise AssertionError('Nonfinite executed torque evidence')
    if np.any(period<=0) or np.any(dt<=0) or np.any(np.diff(starts)<=0) or np.any(np.diff(end)<=0):
        raise AssertionError('Invalid execution time ordering')
    tol=1e-8
    np.testing.assert_allclose(starts[1:],starts[:-1]+period[:-1],rtol=0,atol=tol)
    begin=end-dt
    np.testing.assert_allclose(begin[1:],end[:-1],rtol=0,atol=tol)
    np.testing.assert_allclose(begin[0],starts[0],rtol=0,atol=tol)
    np.testing.assert_allclose(end[-1],starts[-1]+period[-1],rtol=0,atol=tol)
    index=np.searchsorted(starts,begin+tol,side='right')-1
    if np.any(index<0) or np.any(begin<starts[index]-tol) or np.any(end>starts[index]+period[index]+tol):
        raise AssertionError('Physical sample crosses a servo hold boundary')
    counts=np.bincount(index,minlength=len(starts))
    if np.any(counts==0):raise AssertionError('Servo command has no executed physical evidence')
    # Metric raw vectors are float32. Compare after the declared storage
    # rounding, not a tolerance silently broad enough to hide torque errors.
    expected=requested[index].astype(actual.dtype)
    np.testing.assert_allclose(actual,expected,rtol=0,atol=1e-6)
    error=float(np.max(np.abs(actual.astype(float)-expected.astype(float))))
    return dict(max_abs_nm=error,servo_commands=len(starts),physical_samples=len(end),
                samples_per_hold_min=int(counts.min()),samples_per_hold_max=int(counts.max()),
                time_mapping='physical [end-dt,end] lies within servo [start,start+period]; qfrc_actuator[:7]',
                comparison='limiter output cast to physical metric storage dtype, absolute tolerance 1e-6 Nm')


def rollout(root, request, folder):
    resource.setrlimit(resource.RLIMIT_AS,(3*1024**3,3*1024**3))
    sys.path.insert(0,str(root/'source/scripts'))
    import mujoco
    if mujoco.__version__!='3.11.0':raise RuntimeError('Pinned MuJoCo 3.11.0 required')
    import audit_office_complex_scene_v5_20260917 as geometry
    import validate_office_apparatus_v5_20260917 as evaluator
    import run_vmc_6d_constrained_push_20260918 as vmc
    from vmc_teacher_stable_readout_20260930 import StableReadoutTeacher
    from wbc_velocity_residual_core import VelocityResidualActionFilter
    fixture=request['fixture'];config=request['teacher'];method=request.get('method','vmc')
    records=[];chain=[];env_ref=[];actors=[]
    original_xml=geometry.extend_complex_xml
    geometry.extend_complex_xml=lambda *args,**kwargs:training_xml(original_xml(*args,**kwargs),fixture)
    original_make=evaluator.make
    def make(flags):
        result=original_make(flags);env_ref.append(result[0]);return result
    evaluator.make=make
    class RecordedTeacher(StableReadoutTeacher):
        def __init__(self,unused):
            if unused:raise ValueError('Unexpected evaluator parameters')
            super().__init__(**config)
        def act(self,wrench,dt=.04):
            action=super().act(wrench,dt)
            records.append(dict(request=action.copy(),wrench=np.array(wrench),offset=self.offset.copy(),
                                velocity=self.velocity.copy(),filtered_wrench=self.filtered.copy()))
            return action
    def factory(unused):
        if method=='vmc':actor=RecordedTeacher(unused)
        else:
            from teacher_bank_classical_20260930 import configure_environment
            actor=configure_environment(env_ref[0],config,method,records)
        actors.append(actor)
        return actor
    vmc.SixDVirtualDynamics=factory
    original_filter=VelocityResidualActionFilter.filter
    def record_filter(self,action,dt):
        out=original_filter(self,action,dt)
        limits=np.array([self.config.maximum_linear_yield_mps]*3+[self.config.maximum_angular_yield_radps]*3)
        normalized=np.r_[(1-out.wbc_scale)/(1-self.config.minimum_wbc_scale),out.cartesian_yield_twist/limits]
        chain.append(dict(request=np.array(action),filtered_action=normalized,yield_twist=out.cartesian_yield_twist.copy(),
                          wbc_scale=out.wbc_scale,filter_dt=dt))
        return out
    VelocityResidualActionFilter.filter=record_filter
    evaluator.TRAIN_BALL_AXIS=np.array(fixture['axis'])
    evaluator.TRAIN_BALL_VELOCITY=evaluator.TRAIN_BALL_AXIS*fixture['ball_speed_mps']
    evaluator.TRAIN_CONFIGS={kind:dict(start=fixture['start_s'],press=fixture['press_s'],hold=fixture['hold_s'],
        retract=fixture['retract_s'],stroke=fixture['stroke_m'],force_limit=fixture['drive_limit_n']) for kind in ('person','rod')}
    from teacher_bank_exposure_20260930 import TrainingExposure
    exposure=TrainingExposure(fixture);evaluator.TRAIN_OBSERVER=exposure
    adapted_run(evaluator,method)
    events={'passive_corner':'settle','active_short':'ball','active_long':fixture['apparatus']}[fixture['category']]
    args=SimpleNamespace(output=folder/'rollout',render=False,events=events,task='pick_place',corner_placement=True,
        combined_thick_corner_pillar_v4=True,seed=fixture['seed'],variant=0,duration=DURATION,dt=DT,
        ball_speed=fixture['ball_speed_mps'],ball_launch_time_s=fixture['start_s'],
        person_stroke=fixture['stroke_m'],rod_stroke=fixture['stroke_m'],esn_model=None,esn_mode='shadow',teacher='vmc6d')
    write(folder/'command.json',dict(arguments={k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()},
        training_adapter_source_sha256=sha(__file__),python=sys.version,mujoco=mujoco.__version__,numpy=np.__version__,
        fixture=fixture,teacher=config,evaluator_entrypoint_alias='vmc6d (factory replaced for declared method)',
        **controller_contract(method)))
    try:
        evaluator.run(args)
    finally:
        for name,rows in [('teacher_internal',records),('execution_chain',chain)]:
            if rows:np.savez_compressed(folder/(name+'.npz'),**{k:np.asarray([r[k] for r in rows]) for k in rows[0]})
        exposure.save(folder)
        for actor in actors:
            servo=getattr(actor,'servo_records',None)
            if servo:np.savez_compressed(folder/'impedance_servo.npz',**{k:np.asarray([r[k] for r in servo]) for k in servo[0]})
            if hasattr(actor,'close'):actor.close()
    # Keep frozen evaluator output intact; adapter semantics are explicitly separate.
    write(folder/'training_scene.json',evaluator.clean(dict(fixture=fixture,method=method,
        controller_metadata=getattr(actors[0],'metadata',{'method':'vmc','input':'estimated wrench only'}),
        ball_initial_velocity=evaluator.TRAIN_BALL_VELOCITY.tolist(),
        rebound_axis=evaluator.TRAIN_BALL_AXIS.tolist(),applicability='source-domain training, not frozen formal evaluation',
        actuator_config=vars(env_ref[0].safety_config) if hasattr(env_ref[0],'safety_config') else None)))
    audit(root,request,folder)


def materialize_npz(archive, keys=None):
    """Read each compressed column once, before row-wise controller replay.

    NpzFile.__getitem__ decompresses the entire column on EVERY access; a row
    view also keeps that whole column alive. Never form rows from NpzFile.
    """
    names=tuple(archive.files if keys is None else keys)
    if len(set(names))!=len(names):raise ValueError('Duplicate requested NPZ column')
    return {name:archive[name] for name in names}


def column_rows(columns):
    """Yield views into one materialized column set, without retaining rows."""
    if not columns:raise ValueError('Empty replay columns')
    lengths={len(value) for value in columns.values()}
    if len(lengths)!=1:raise ValueError('Replay column lengths differ')
    for index in range(next(iter(lengths))):
        yield {key:value[index] for key,value in columns.items()}


def audit_observation_alignment(data):
    """Bind 48D encoder fields to saved pre/post-action robot state and time.

    First pre-action velocity has no preceding saved post-state; its provenance
    is explicitly outside this check. Wrench/observer/FK reconstruction is also
    outside this kinematic association check.
    """
    obs=np.asarray(data['observation']);count=len(obs)
    for name in ('neuron_qpos','qpos','qvel'):
        value=np.asarray(data[name])
        if value.ndim!=2 or value.shape[0]!=count or value.shape[1]<7 or not np.isfinite(value).all():
            raise AssertionError('Invalid state alignment evidence: '+name)
    for name in ('neuron_time','time'):
        value=np.asarray(data[name])
        if value.shape!=(count,) or not np.isfinite(value).all():
            raise AssertionError('Invalid state alignment time: '+name)
    if obs.shape!=(count,48) or not np.isfinite(obs).all():raise AssertionError('Invalid observation alignment shape')
    np.testing.assert_allclose(data['neuron_time'],np.arange(count)*.04,rtol=0,atol=1e-7)
    np.testing.assert_allclose(data['time'],(np.arange(count)+1)*.04,rtol=0,atol=1e-7)
    pairs=[(obs[:,:7],data['neuron_qpos'][:,:7])]
    if count>1:
        pairs.extend([(data['neuron_qpos'][1:,:7],data['qpos'][:-1,:7]),
                      (obs[1:,7:14],data['qvel'][:-1,:7])])
    maximum=0.
    for left,right in pairs:
        np.testing.assert_allclose(left,right,rtol=0,atol=1e-12)
        maximum=max(maximum,float(np.max(np.abs(left-right))) if left.size else 0.)
    return dict(max_abs=maximum,actions=count,
        scope='encoder q matches pre-action neuron_qpos; consecutive arm q/dq and 25Hz timestamps match saved post-state',
        first_pre_action_velocity_independently_verified=False,
        observer_wrench_and_kinematics_independently_reconstructed=False)


def audit_exposure_physics_binding(exposure,physics,fixture):
    """Prevent a valid early-window exposure file standing in for a full run."""
    pt=np.asarray(physics['time'],float);pdt=np.asarray(physics['dt'],float)
    et=np.asarray(exposure['time'],float);ee=np.asarray(exposure['interval_end'],float);edt=np.asarray(exposure['dt'],float)
    if (pt.ndim!=1 or not len(pt) or pdt.shape!=pt.shape or et.ndim!=1 or not len(et)
            or ee.shape!=et.shape or edt.shape!=et.shape):raise AssertionError('Invalid exposure/physics binding shape')
    if not all(np.isfinite(v).all() for v in (pt,pdt,et,ee,edt)):raise AssertionError('Nonfinite exposure/physics binding')
    begin=pt-pdt;tol=1e-8
    np.testing.assert_allclose(et[0],begin[0],rtol=0,atol=tol)
    np.testing.assert_allclose(ee[-1],pt[-1],rtol=0,atol=tol)
    np.testing.assert_allclose(float(exposure['terminal_time_s']),pt[-1],rtol=0,atol=tol)
    indices=np.searchsorted(begin,et-tol)
    ends=np.r_[indices[1:],len(pt)]
    if np.any(indices>=len(pt)) or np.any(ends<=indices):raise AssertionError('Exposure buckets do not cover physics')
    np.testing.assert_allclose(begin[indices],et,rtol=0,atol=tol)
    np.testing.assert_allclose(pt[ends-1],ee,rtol=0,atol=tol)
    np.testing.assert_allclose(np.add.reduceat(pdt,indices),edt,rtol=0,atol=tol)
    person_exact=False
    if fixture['category']=='active_long' and fixture.get('apparatus')=='person' and int(exposure['schema'])>=2:
        raw=np.asarray(exposure['person_physics'])
        if raw.shape!=(len(pt),6) or not np.isfinite(raw).all():raise AssertionError('Person raw count differs from physical trace')
        np.testing.assert_allclose(raw[:,0],begin,rtol=0,atol=tol)
        np.testing.assert_allclose(raw[:,1],pdt,rtol=0,atol=1e-12)
        person_exact=True
    return dict(physical_samples=len(pt),exposure_buckets=len(et),duration_s=float(pdt.sum()),
        person_every_physical_step_verified=person_exact,
        scope='exposure interval endpoints and dt sums match physical trace; schema2 person raw times/dt match every substep')


def audit(root,request,folder,output_path=None):
    output_path=Path(output_path) if output_path is not None else folder/'audit.json'
    sys.path.insert(0,str(root/'source/scripts'))
    from vmc_teacher_stable_readout_20260930 import StableReadoutTeacher
    from wbc_velocity_residual_core import VelocityResidualActionFilter,VelocityResidualSafetyConfig,TORQUE_LIMITS_NM
    result=json.loads((folder/'rollout.json').read_text());fixture=request['fixture']
    method=request.get('method','vmc')
    actor=StableReadoutTeacher(**request['teacher']) if method=='vmc' else None
    safety=VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32)
    filt=VelocityResidualActionFilter(safety);label_filter=VelocityResidualActionFilter(safety);maximum=0.
    replay_scope='VMC state, action and shared filter'
    impedance_execution=None
    servo_columns=None
    with np.load(folder/'rollout.npz') as data_archive,np.load(folder/'teacher_internal.npz') as internal_archive,np.load(folder/'execution_chain.npz') as chain_archive:
        data=materialize_npz(data_archive,('observation','applied_action','neuron_qpos','qpos','qvel','neuron_time','time'))
        observation_alignment=audit_observation_alignment(data)
        internal=materialize_npz(internal_archive)
        chain=materialize_npz(chain_archive)
        observations=data['observation'];count=len(observations)
        if observations.shape!=(count,48) or count!=len(internal['request']) or count!=len(chain['request']):raise AssertionError('Contract/length mismatch')
        for arrays in (internal,chain):
            for key in arrays:
                if not np.isfinite(arrays[key]).all():raise AssertionError('Nonfinite '+key)
        if not np.isfinite(observations).all():raise AssertionError('Nonfinite actor observation')
        if not np.isfinite(data['applied_action']).all():raise AssertionError('Nonfinite applied action')
        if method!='vmc':
            from teacher_bank_classical_20260930 import replay_admittance,replay_impedance
            rows=column_rows(internal)
            if method=='admittance':replay=replay_admittance(request['teacher'],rows)
            else:
                with np.load(folder/'impedance_servo.npz') as servo:
                    servo_columns=materialize_npz(servo)
                    for k,value in servo_columns.items():
                        if not np.isfinite(value).all():raise AssertionError('Nonfinite servo '+k)
                    replay=replay_impedance(request['teacher'],column_rows(servo_columns),safety)
            maximum=replay['max_abs'];replay_scope=replay['scope']
        for i,obs in enumerate(observations):
            action=actor.act(obs[39:45]) if actor else internal['request'][i]
            out=filt.filter(action,.04)
            limits=np.array([safety.maximum_linear_yield_mps]*3+[safety.maximum_angular_yield_radps]*3)
            label=np.r_[(1-out.wbc_scale)/(1-safety.minimum_wbc_scale),out.cartesian_yield_twist/limits]
            second=label_filter.filter(chain['filtered_action'][i],.04)
            pairs=[(action,internal['request'][i]),(action,data['applied_action'][i]),(action,chain['request'][i]),
                   (out.cartesian_yield_twist,chain['yield_twist'][i]),(out.wbc_scale,chain['wbc_scale'][i]),
                   (label,chain['filtered_action'][i]),(chain['filter_dt'][i],.04),
                   (second.cartesian_yield_twist,out.cartesian_yield_twist),(second.wbc_scale,out.wbc_scale)]
            if actor:pairs.extend([(actor.offset,internal['offset'][i]),(actor.velocity,internal['velocity'][i]),(actor.filtered,internal['filtered_wrench'][i])])
            for left,right in pairs:
                if np.shape(left)!=np.shape(right):raise AssertionError('Replay shape mismatch')
                maximum=max(maximum,float(np.max(np.abs(np.asarray(left)-right))))
        if maximum>1e-10:raise AssertionError('Teacher/filter replay mismatch')
        delta_rms=float(np.sqrt(np.mean(np.diff(internal['request'][:,1:],axis=0)**2))) if count>1 else 0.
    with np.load(folder/'rollout_metrics/substep_metrics.npz') as physics_archive:
        data=materialize_npz(physics_archive,('dt','time','error','qfrc_actuator','twist'))
        if method=='impedance':
            import mujoco
            mapping=direct_arm_mapping(mujoco.MjModel.from_binary_path(str(folder/'rollout.mjb')))
            impedance_execution=dict(mapping=mapping,**audit_impedance_execution(servo_columns,data))
        for key in ('dt','time','error','qfrc_actuator','twist'):
            if not np.isfinite(data[key]).all():raise AssertionError('Nonfinite physical '+key)
        dt=data['dt'].astype(float);error=data['error'].astype(float);torque=data['qfrc_actuator'].astype(float)
        times=data['time'].astype(float)
        executed_duration=count*.04
        if len(dt)!=round(executed_duration/DT) or np.any(dt<=0) or abs(dt.sum()-executed_duration)>1e-6:raise AssertionError('Incomplete physics evidence for executed actions')
        if count!=round(DURATION/.04) and not result.get('abort_reason'):raise AssertionError('Unexplained truncated episode')
        if np.any(np.diff(times)<=0):raise AssertionError('Nonmonotone physics time')
        np.testing.assert_allclose(dt,DT,rtol=0,atol=1e-12)
        np.testing.assert_allclose(times,np.cumsum(dt),rtol=0,atol=1e-7)
        if error.shape!=(len(dt),3) or torque.shape!=(len(dt),7) or data['twist'].shape!=(len(dt),6):raise AssertionError('Physical shape mismatch')
        speed=np.linalg.norm(data['twist'][:,:3].astype(float),axis=1)
        rmse=float(np.sqrt(np.sum(error**2*dt[:,None])/dt.sum()));peak=float(abs(torque).max());vpeak=float(speed.max())
        ratio=float(np.max(abs(torque)/TORQUE_LIMITS_NM))
        # Motor command is held between 4-ms servo updates; do not divide jumps by physics dt.
        rate_ratio=float(np.max(abs(np.diff(torque,axis=0))/(np.asarray(safety.maximum_torque_rate_nmps)*.004)))
        measured=[rmse,peak,vpeak];reported=[result['metrics'][k] for k in ('position_rmse_3d_m','generalized_actuator_torque_peak_nm','linear_speed_peak_mps')]
        np.testing.assert_allclose(measured,reported,rtol=2e-7,atol=1e-8)
        substeps=len(dt)
        with np.load(folder/'exposure.npz') as exposure_archive:
            binding=audit_exposure_physics_binding(exposure_archive,data,fixture)
    from teacher_bank_exposure_20260930 import audit_saved
    exposure=audit_saved(folder/'exposure.npz',fixture)
    contact=result['contact_coverage_valid'] and exposure['passed']
    reasons=[]
    if result.get('abort_reason'):reasons.append('physics_abort:'+str(result['abort_reason']))
    for passed,reason in ((result['task_success'],'task_failed'),(result['strict_success'],'evaluator_strict_failed'),
        (contact,'required_contact_missing'),(ratio<=1+1e-6,'torque_amplitude'),(rate_ratio<=1+1e-3,'torque_slew'),
        (count==round(DURATION/.04),'incomplete_horizon')):
        if not passed:reasons.append(reason)
    completed=next((e['time_s'] for e in result['task_events'] if 'retreat' in e['stage'].lower()),DURATION)
    score=rmse/.05+.3*ratio+.1*completed/DURATION
    result=dict(eligible=not reasons,failure_reasons=reasons,task=result['task_success'],strict=result['strict_success'],
        contact=contact,rmse_m=rmse,peak_torque_nm=peak,peak_speed_mps=vpeak,torque_ratio=ratio,
        torque_slew_ratio=rate_ratio,completion_proxy_retreat_s=completed,action_delta_rms=delta_rms,
        score=score,constraint=-1. if not reasons else float(len(reasons)),replay_max_abs=maximum,replay_scope=replay_scope,
        method=method,exposure=exposure,
        esn_label_eligible=(not reasons and method=='vmc' and fixture['split']=='train'),
        impedance_execution=impedance_execution,controller_contract=controller_contract(method),
        observation_alignment=observation_alignment,exposure_physics_binding=binding,
        substeps=substeps,penetration_mm=result['stats']['max_external_penetration_m']*1000,
        fixture_id=fixture['id'],split=fixture['split'],model_sha256=sha(folder/'rollout.mjb'),
        note='VMC filtered action7 replays shared filter; classical trajectories are baseline evidence, not VMC action labels. Full learner closed-loop validation still required.',
        audit_source_sha256=sha(__file__),raw_folder=str(folder.resolve()),
        files_sha256={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file()
            and p.name not in ('run.log','execution.json','audit.json') and p.resolve()!=output_path.resolve()})
    write(output_path,result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--request',type=Path,required=True)
    args=parser.parse_args();request=json.loads(args.request.read_text())
    rollout(args.root.resolve(),request,args.request.parent.resolve())
