"""Run the user's three historical scene families with the frozen new30 actor.

The original scene constructors/task supervisors are retained. The execution
boundary replaces every legacy action; no legacy controller correction reaches
the common filter. These are scene demonstrations, not the office test matrix.
"""
import argparse
import ast
from dataclasses import asdict, replace
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT/'outputs/teacher_student_15h_20261012_v3'
RUNTIME = ROOT/'outputs/baseline_local_rl_20261009/runtime'
SCENES = ('corner', 'rod', 'ball')
COMMON_LINEAR_YIELD_MPS = .32


def make_actor(config, checkpoint=None):
    """Use the same canonical observations for teacher and diagnostic students."""
    if checkpoint is None:
        from optimize_tool_contact_20261002 import ParameterTeacher
        return ParameterTeacher(config)
    from current_student_policy_20260921 import load_current

    class StudentAdapter:
        def __init__(self):
            self.policy = load_current(checkpoint)
            self.policy.reset()

        def observe(self, observation):
            self.observation = observation.copy()

        def act(self, wrench, dt=.04):
            if dt != .04:
                raise ValueError('Frozen student actor clock must be 0.04 seconds')
            return self.policy.act(self.observation)

    return StudentAdapter()


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def write(p, value):
    p.write_text(json.dumps(value, indent=2, allow_nan=False,
                           default=lambda v: v.tolist())+'\n')


def verify_actor():
    for name, cls in [('tools/optimize_tool_contact_20261002.py', 'ParameterTeacher'),
                      ('scripts/vmc_teacher_stable_readout_20260930.py', 'StableReadoutTeacher'),
                      ('scripts/run_vmc_6d_constrained_push_20260918.py', 'SixDVirtualDynamics')]:
        def node(path):
            return ast.dump(next(n for n in ast.parse(path.read_text()).body
                                 if isinstance(n, ast.ClassDef) and n.name == cls))
        assert node(ROOT/name) == node(PARENT/'source'/name), cls


def worker(out, scene):
    import numpy as np
    import mujoco
    sys.path.insert(0, str(ROOT/'scripts'))
    import optimize_tool_contact_20261002 as teacher_module
    import audited_velocity_env as base
    from haptic_vmc_teacher_20260916 import JointLoadObserver, equivalent_tool_wrench
    from run_benchmark import body_jacobian, body_twist, so3_log
    from wbc_velocity_residual_core import VelocityResidualActionFilter
    assert mujoco.__version__ == '3.11.0'
    verify_actor()
    folder = out/scene
    folder.mkdir(exist_ok=False)
    config = json.loads((PARENT/'TEACHER_CHOICE.json').read_text())['selected']['config']
    override=os.environ.get('VMC_TEACHER_CONFIG')
    if override:
        config=json.loads(Path(override).read_text())
    write(folder/'teacher.json', config)
    checkpoint_source = os.environ.get('VMC_STUDENT_CHECKPOINT')
    checkpoint = None
    if checkpoint_source:
        if os.environ.get('VMC_COLLECTION_PLAN'):
            raise ValueError('A student diagnostic may not enter teacher collection')
        checkpoint = folder/'student_checkpoint.npz'
        shutil.copyfile(Path(checkpoint_source).resolve(), checkpoint)
    actor = make_actor(config, checkpoint)
    actions, observations, states, chains = [], [], [], []
    sensor = None
    peak_torque = np.zeros(7)
    contact_stats = {}
    sample_count = 0
    substeps = None
    env_ref = None
    original_step = base.PandaWBCVelocityResidualEnv.step
    original_filter = VelocityResidualActionFilter.filter
    filter_config = None
    manifest = dict(status='running', scene=scene, started_utc=datetime.now(timezone.utc).isoformat(),
        teacher=(('development VMC configuration' if override else 'new30 teacher_lhs_0')+'; three actor classes AST-identical to collection source' if checkpoint is None else 'not a teacher: frozen student diagnostic'),
        controller_role='teacher' if checkpoint is None else 'student_diagnostic',
        student_checkpoint_sha256=sha(checkpoint) if checkpoint else None,
        action_contract=dict(linear_yield_mps=COMMON_LINEAR_YIELD_MPS, angular_yield_radps=.6,
                             actor_dt_s=.04, label='unfiltered normalized requested action'),
        teacher_override_source=(str(Path(override).resolve()) if override else None),
        teacher_config_sha256=sha(folder/'teacher.json'), actor_input='canonical48 proprioception; no contact oracle/clock/geometry',
        legacy_actions_discarded=True, task_supervisor='original scene script; not office-v7 test task',
        python=sys.executable, mujoco=mujoco.__version__, wrapper_sha256=sha(Path(__file__)),
        limitations='Historical video family/source matched by on-screen titles and scene layout. Full original per-video runtime metadata is unavailable; exact historical parameter/trajectory identity is not claimed.')
    manifest['experiment_environment'] = {k:v for k,v in os.environ.items() if k.startswith(
        ('VMC_', 'PLACE_', 'PLACEMENT_', 'UPRIGHT_', 'LIFT_BOARD_', 'INIT_JOINT_',
         'GRASP_', 'GRIPPER_', 'WBC_', 'PREGRASP_'))}
    plan_path = os.environ.get('VMC_COLLECTION_PLAN')
    plan = None
    if plan_path:
        from collect_special_scene_actions_20261028 import validate
        plan_path = Path(plan_path).resolve()
        plan = validate(plan_path)
        identity = os.environ['VMC_COLLECTION_ID']
        entry = next(e for e in plan['episodes'] if e['id'] == identity)
        if Path(entry['folder']).resolve() != folder or entry['scene'] != scene:
            raise ValueError('Collection identity/path/scene mismatch')
        if manifest['teacher_config_sha256'] != plan['teacher_config_sha256']:
            raise ValueError('Teacher changed after collection registration')
        if plan.get('action_contract') != manifest['action_contract']:
            raise ValueError('Collection must explicitly register the common action contract; old mixed-scale plans are not reusable')
        if any(os.environ.get(k) != str(v) for k,v in entry['scene_parameters'].items()):
            raise ValueError('Scene parameters differ from collection plan')
        if os.environ.get('VMC_SCENE_SEED') != str(entry['seed']):
            raise ValueError('Seed differs from collection plan')
        if datetime.fromisoformat(plan['registered_utc']) >= datetime.fromisoformat(manifest['started_utc']):
            raise ValueError('Collection plan must predate execution')
        manifest.update(collection_plan_sha256=sha(plan_path), collection_identity=identity,
                        collection_split=entry['split'], collection_scene_parameters=entry['scene_parameters'])
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    manifest['resources']={name:((cg/name).read_text().strip() if (cg/name).exists() else None) for name in
                           ('memory.max','memory.swap.max','cpu.max')}
    manifest['resources']['cgroup']=str(cg)
    write(folder/'execution.json', manifest)

    def filter_capture(self, action, dt):
        nonlocal filter_config
        result = original_filter(self, action, dt)
        filter_config = self.config
        chains.append(dict(request=np.asarray(action).copy(), dt=float(dt),
            twist=result.cartesian_yield_twist.copy(), scale=float(result.wbc_scale),
            clipped=result.raw_action_clipped.copy()))
        return result

    def controlled_step(env, ignored_legacy_action):
        nonlocal sensor, sample_count, env_ref, substeps
        env_ref = env
        m, d = env.model, env.data
        if sensor is None:
            # The corner constructor historically inherited the 0.16 default,
            # while rod/ball and frozen office evaluation use 0.32. Correct
            # the action conversion before the first physical policy step;
            # keep geometry, task gates and all other safety settings intact.
            manifest['constructor_linear_yield_mps'] = env.safety_config.maximum_linear_yield_mps
            assert env.action_filter.config is env.safety_config
            env.safety_config = replace(env.safety_config, maximum_linear_yield_mps=COMMON_LINEAR_YIELD_MPS)
            env.action_filter.config = env.safety_config
            assert env.safety_config.maximum_angular_yield_radps == .6
            substeps=np.empty((int(np.ceil(env.simulation_time_s/m.opt.timestep))+100,18),dtype=np.float64)
            sensor = JointLoadObserver(d.qvel.copy(), m.dof_frictionloss)
            mass = np.zeros((m.nv, m.nv))
            old_observer = env.substep_observer
            robot = set(env._push_audit_robot_geom_ids)
            names = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, i) or '' for i in range(m.ngeom)]
            def observe(t):
                nonlocal sample_count
                if old_observer is not None:
                    old_observer(t)
                mujoco.mj_fullM(m, d, mass)
                sensor.update(d.qvel.copy(), mass, d.qfrc_bias.copy(), d.qfrc_passive.copy(),
                              d.qfrc_actuator.copy(), m.opt.timestep)
                peak_torque[:] = np.maximum(peak_torque, np.abs(d.qfrc_actuator[:7]))
                seen = set()
                seen_body = set()
                external_penetration=0.;disturbance_force=0.
                for i in range(d.ncon):
                    c = d.contact[i]
                    g1, g2 = int(c.geom1), int(c.geom2)
                    if (g1 in robot) == (g2 in robot):
                        continue
                    other = g2 if g1 in robot else g1
                    if int(m.geom_bodyid[other]) == env._target_body_id:
                        continue
                    name = names[other]
                    row = contact_stats.setdefault(name, dict(first_s=float(d.time), last_s=float(d.time),
                        duration_s=0., peak_force_n=0., max_penetration_m=0.))
                    f = np.zeros(6)
                    mujoco.mj_contactForce(m, d, i, f)
                    external_penetration=max(external_penetration,-float(c.dist))
                    if name=='push_rod_geom' or name.startswith('primitive_free_ball'):
                        disturbance_force+=float(np.linalg.norm(f[:3]))
                    row['peak_force_n'] = max(row['peak_force_n'], float(np.linalg.norm(f[:3])))
                    row['max_penetration_m'] = max(row['max_penetration_m'], -float(c.dist))
                    row['last_s'] = float(d.time)
                    seen.add(name)
                    if np.linalg.norm(f[:3]) > .05:
                        robot_g=g1 if g1 in robot else g2
                        body=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,int(m.geom_bodyid[robot_g]))
                        body_row=row.setdefault('per_body',{}).setdefault(body,dict(first_s=float(d.time),last_s=float(d.time),duration_s=0.,peak_force_n=0.))
                        body_row['last_s']=float(d.time)
                        body_row['peak_force_n']=max(body_row['peak_force_n'],float(np.linalg.norm(f[:3])))
                        seen_body.add((name,body))
                for name in seen:
                    contact_stats[name]['duration_s'] += float(m.opt.timestep)
                for name,body in seen_body:
                    contact_stats[name]['per_body'][body]['duration_s'] += float(m.opt.timestep)
                if sample_count>=len(substeps):
                    raise RuntimeError('Substep telemetry exceeded registered physical duration')
                substeps[sample_count]=np.r_[d.time,d.qfrc_actuator[:7],d.qvel[:7],external_penetration,disturbance_force,m.opt.timestep]
                sample_count+=1
            # Panel's setter wraps callbacks with its own audit. Do not wrap
            # that audit twice when installing this additional observer.
            if hasattr(env, '_panel_observer'):
                env._panel_observer = observe
            else:
                env.substep_observer = observe
            mujoco.mj_saveModel(m, str(folder/'scene.mjb'), None)
            mujoco.mj_saveLastXML(str(folder/'scene.xml'), m)
            push_joint = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, 'push_rod_slide')
            manifest.update(model_sha256=sha(folder/'scene.mjb'), physics_dt_s=float(m.opt.timestep),
                            safety_config=asdict(env.safety_config),
                            actuator_torque_limits_nm=np.abs(m.actuator_ctrlrange[:7,1]).tolist(),
                            push_rod_qpos_index=(int(m.jnt_qposadr[push_joint]) if push_joint >= 0 else None),
                            push_rod_stroke_m=(float(os.environ.get('PUSH_ROD_STROKE_M', '0'))
                                               if scene == 'rod' else None))
            write(folder/'execution.json', manifest)
        command = env._wbc_command(env.step_count*.04)
        position = d.xpos[env._hand_id].copy()
        rotation = d.xmat[env._hand_id].reshape(3,3).copy()
        twist = body_twist(m, d, env._hand_id)
        error = np.r_[command.target_position_m-position, so3_log(command.target_rotation@rotation.T)]
        direction = getattr(env.reference, 'path_direction', None)
        if direction is None:
            direction = command.task_twist_world[:3].copy()
            direction /= max(float(np.linalg.norm(direction)), 1e-12)
        wrench = equivalent_tool_wrench(body_jacobian(m,d,env._hand_id),sensor.filtered)
        obs = np.r_[d.qpos[:7], d.qvel[:7], command.task_twist_world, error,
                    command.task_twist_world-twist, sensor.filtered, wrench, direction]
        assert obs.shape == (48,) and np.isfinite(obs).all()
        actor.observe(obs)
        action = actor.act(wrench, .04)
        observations.append(obs.copy())
        actions.append(action.copy())
        result = original_step(env, action)
        states.append(dict(time=float(d.time), qpos=d.qpos.copy(), qvel=d.qvel.copy(),
            ctrl=d.ctrl.copy(), mocap_pos=d.mocap_pos.copy(), mocap_quat=d.mocap_quat.copy()))
        if len(states)%25 == 0:
            write(folder/'progress.json', dict(time_s=float(d.time), steps=len(states), substeps=sample_count))
        return result

    base.PandaWBCVelocityResidualEnv.step = controlled_step
    VelocityResidualActionFilter.filter = filter_capture
    try:
        if scene == 'corner':
            # Select the nominal legacy branch so all old VMC-specific gain,
            # oracle and hand-crafted residual schedules remain inactive.
            entry = ROOT/'scripts/render_compliance_audited.py'
            os.environ.update(CORNER_AUDIT_TIMESTEP_S='.00005', ALLOW_TEACHER_DISTURBANCE_GAIN_SCHEDULE='0')
            sys.argv = [str(entry), '--menagerie', str(RUNTIME/'menagerie'), '--esn', str(folder/'unused.npz'),
                '--output', str(folder/'legacy'), '--scenario', 'corner', '--controller', 'paper_mpc',
                '--simulation-time', '13', '--fps', '25', '--no-render',
                '--seed', os.environ.get('VMC_SCENE_SEED','20264031')]
        else:
            recipe = json.loads((ROOT/'configs'/('ball_source_demo.json' if scene=='ball' else 'workstation_source_demo.json')).read_text())
            flags = recipe['arguments']
            flags.update(dt=.00005, output=str(folder/'legacy'), menagerie=str(RUNTIME/'menagerie'))
            flags['seed'] = int(os.environ.get('VMC_SCENE_SEED',flags.get('seed',800)))
            if scene == 'ball':
                flags['teacher_profile'] = 'none'
                for key,variable in [('ball_speed','VMC_BALL_SPEED_MPS'),('shift','VMC_BALL_SHIFT_M'),
                                     ('ball_height_offset','VMC_BALL_HEIGHT_OFFSET_M')]:
                    if variable in os.environ: flags[key]=float(os.environ[variable])
            else:
                # Reference video has local physical guards and no additional
                # workstation furniture; its title is the non-workstation branch.
                recipe['environment']['PANEL_CONFIG']['workstation'] = False
                recipe['environment']['CORE_VMC_CONFIG'] = {}
            if scene == 'rod':
                # run_primitive_teacher_v7 writes these values into the
                # audited environment when it builds the physical push rod;
                # setting only outer environment variables would be silently
                # overwritten by the recipe arguments.
                # Fixed scene drive; behavior is measured independently and
                # must finish before withdrawal STARTS. No success is assumed.
                rod_press = float(os.environ.get('VMC_ROD_PRESS_S', '0.36'))
                rod_hold = float(os.environ.get('VMC_ROD_HOLD_S', '2.00'))
                rod_retract = float(os.environ.get('VMC_ROD_RETRACT_S', '0.36'))
                rod_stroke = float(os.environ.get('VMC_ROD_STROKE_M', '0.20'))
                rod_force = float(os.environ.get('VMC_ROD_PUSH_FORCE_N', '30.0'))
                flags.update(push_press=rod_press, push_hold=rod_hold, push_retract=rod_retract,
                             push_stroke=rod_stroke, push_force=rod_force,
                             event_stage=os.environ.get('VMC_ROD_EVENT_STAGE',flags['event_stage']),
                             event_delay=float(os.environ.get('VMC_ROD_EVENT_DELAY_S', '.8')),
                             push_height=float(os.environ.get('VMC_ROD_HEIGHT_M', '.65')),
                             push_target_x=float(os.environ.get('VMC_ROD_TARGET_X_M', '.57')),
                             duration=float(os.environ.get('VMC_SCENE_DURATION_S', '24')))
            for k, v in recipe['environment'].items():
                os.environ[k] = json.dumps(v) if isinstance(v, dict) else str(v)
            if scene == 'rod':
                # The reference clip used a persistent rod, which only proves
                # contact/hold. The collection contract requires the physical
                # rod to reach its full stroke, remain there long enough to
                # displace the hand, and retract only after the hand has
                # crossed and rejoined the nominal path. This is the existing
                # audited press-hold-retract apparatus in audited_velocity_env;
                # it is a scene drive, never an actor input.
                os.environ.update(
                    PUSH_ROD_SCENE='1',
                    PUSH_ROD_PRESS_S=str(rod_press),
                    PUSH_ROD_HOLD_S=str(rod_hold),
                    PUSH_ROD_RETRACT_S=str(rod_retract),
                    PUSH_ROD_STROKE_M=str(rod_stroke),
                )
                manifest['rod_behavior_contract'] = dict(
                    mode='full_stroke_press_hold_retract',
                    stroke_m=rod_stroke, press_s=rod_press, hold_s=rod_hold, retract_s=rod_retract,
                    drive_force_limit_n=rod_force,
                    start_source='legacy.json fixture_trigger_time_s; never a hard-coded assumed time',
                    required_order='hand contact -> yield -> geometric pass -> persistent rejoin < retract_start',
                    actor_inputs='canonical48 only; rod state/contact/release time excluded',
                )
            entry = ROOT/'scripts'/recipe['entrypoint']
            sys.argv = [str(entry)]
            for k,v in flags.items():
                if v is not None:
                    sys.argv += ['--'+k.replace('_','-'), str(v)]
            write(folder/'recipe.json', recipe)
        manifest.update(argv=sys.argv.copy(), entrypoint_sha256=sha(entry))
        write(folder/'execution.json', manifest)
        runpy.run_path(str(entry), run_name='__main__')
        replay = make_actor(config, checkpoint)
        pred = []
        for obs in observations:
            replay.observe(obs)
            pred.append(replay.act(obs[39:45], .04))
        np.testing.assert_allclose(pred, actions, atol=0, rtol=0)
        np.testing.assert_array_equal([v['request'] for v in chains], actions)
        filt = VelocityResidualActionFilter(filter_config)
        for c in chains:
            # Bypass capture while auditing; otherwise replay appends to the
            # same live list being iterated and falsely reports a mismatch.
            v = original_filter(filt, c['request'], c['dt'])
            np.testing.assert_array_equal(v.cartesian_yield_twist, c['twist'])
            assert v.wbc_scale == c['scale']
        manifest.update(status='complete', actor_replay_max_abs=0., filter_replay_max_abs=0.)
    except BaseException as exc:
        manifest.update(status='failed_preserved', error=repr(exc))
        raise
    finally:
        base.PandaWBCVelocityResidualEnv.step = original_step
        VelocityResidualActionFilter.filter = original_filter
        if states:
            raw=substeps[:sample_count]
            np.savez_compressed(folder/'substeps.npz',time=raw[:,0],torque=raw[:,1:8],joint_velocity=raw[:,8:15],
                                external_penetration_m=raw[:,15],disturbance_force_n=raw[:,16],dt=raw[:,17])
            manifest['substeps_sha256']=sha(folder/'substeps.npz')
            np.savez_compressed(folder/'trajectory.npz', **{k:np.asarray([s[k] for s in states]) for k in states[0]},
                observation=np.asarray(observations), action=np.asarray(actions))
            np.savez_compressed(folder/'filter.npz', **{k:np.asarray([s[k] for s in chains]) for k in chains[0]})
            manifest.update(steps=len(states), physical_seconds=states[-1]['time'], substeps=sample_count,
                peak_torque_nm=peak_torque.tolist(), contacts=contact_stats, filter_config=asdict(filter_config),
                trajectory_sha256=sha(folder/'trajectory.npz'))
        files={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'scripts').glob('*.py')}
        files['tools/optimize_tool_contact_20261002.py']=sha(ROOT/'tools/optimize_tool_contact_20261002.py')
        files['tools/collect_special_scene_actions_20261028.py']=sha(ROOT/'tools/collect_special_scene_actions_20261028.py')
        files[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
        if files[str(Path(__file__).relative_to(ROOT))]!=manifest['wrapper_sha256']:
            manifest.update(status='failed_preserved',error='Wrapper source changed during run')
        if plan is not None and sha(plan_path) != manifest['collection_plan_sha256']:
            manifest.update(status='failed_preserved',error='Collection plan changed during run')
        if checkpoint and sha(checkpoint) != manifest['student_checkpoint_sha256']:
            manifest.update(status='failed_preserved',error='Diagnostic checkpoint changed during run')
        write(folder/'SOURCE_HASHES.json', files)
        subprocess.run(['tar','-czf',str(folder/'source.tar.gz'),*files],cwd=ROOT,check=True)
        manifest['ended_utc']=datetime.now(timezone.utc).isoformat()
        manifest['resources'].update({name:(cg/name).read_text().strip() for name in
                                     ('memory.peak','memory.events','memory.swap.current')})
        write(folder/'execution.json', manifest)
    if manifest['status'] != 'complete':
        raise RuntimeError(manifest.get('error', 'Incomplete worker execution'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--worker', choices=SCENES)
    p.add_argument('--scenes', nargs='+', choices=SCENES, default=SCENES)
    a=p.parse_args()
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=(cg/'memory.max').read_text().strip()
    if memory == 'max' or int(memory)>3*1024**3 or (cg/'memory.swap.max').read_text().strip()!='0':
        raise RuntimeError('Actual cgroup MemoryMax<=3GiB and MemorySwapMax=0 required')
    out=a.output.resolve()
    if a.worker:
        worker(out,a.worker)
        return
    out.mkdir(parents=True,exist_ok=False)
    lock=(ROOT/'outputs/.local-rl-compute.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    rows=[]
    for scene in a.scenes:
        command=[sys.executable,str(Path(__file__).resolve()),'--output',str(out),'--worker',scene]
        with (out/(scene+'.log')).open('x') as f:
            rc=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT).returncode
        rows.append(dict(scene=scene,returncode=rc))
        write(out/'execution.json',dict(status='running',rows=rows))
    write(out/'execution.json',dict(status='complete' if all(r['returncode']==0 for r in rows) else 'failures_preserved',rows=rows))
    if any(r['returncode']!=0 for r in rows):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
