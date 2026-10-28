"""Run the user's three historical scene families with the frozen new30 actor.

The original scene constructors/task supervisors are retained. The execution
boundary replaces every legacy action; no legacy controller correction reaches
the common filter. These are scene demonstrations, not the office test matrix.
"""
import argparse
import ast
from dataclasses import asdict
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT/'outputs/teacher_student_15h_20261012_v3'
RUNTIME = ROOT/'outputs/baseline_local_rl_20261009/runtime'
SCENES = ('corner', 'rod', 'ball')


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
    write(folder/'teacher.json', config)
    actor = teacher_module.ParameterTeacher(config)
    actions, observations, states, chains = [], [], [], []
    sensor = None
    peak_torque = np.zeros(7)
    contact_stats = {}
    sample_count = 0
    env_ref = None
    original_step = base.PandaWBCVelocityResidualEnv.step
    original_filter = VelocityResidualActionFilter.filter
    filter_config = None
    manifest = dict(status='running', scene=scene, started_utc=datetime.now(timezone.utc).isoformat(),
        teacher='new30 teacher_lhs_0; three actor classes AST-identical to collection source',
        teacher_config_sha256=sha(folder/'teacher.json'), actor_input='canonical48 proprioception; no contact oracle/clock/geometry',
        legacy_actions_discarded=True, task_supervisor='original scene script; not office-v7 test task',
        python=sys.executable, mujoco=mujoco.__version__, wrapper_sha256=sha(Path(__file__)),
        limitations='Historical video family/source matched by on-screen titles and scene layout. Full original per-video runtime metadata is unavailable; exact historical parameter/trajectory identity is not claimed.')
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
        nonlocal sensor, sample_count, env_ref
        env_ref = env
        m, d = env.model, env.data
        if sensor is None:
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
                sample_count += 1
                seen = set()
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
                    row['peak_force_n'] = max(row['peak_force_n'], float(np.linalg.norm(f[:3])))
                    row['max_penetration_m'] = max(row['max_penetration_m'], -float(c.dist))
                    row['last_s'] = float(d.time)
                    seen.add(name)
                for name in seen:
                    contact_stats[name]['duration_s'] += float(m.opt.timestep)
            # Panel's setter wraps callbacks with its own audit. Do not wrap
            # that audit twice when installing this additional observer.
            if hasattr(env, '_panel_observer'):
                env._panel_observer = observe
            else:
                env.substep_observer = observe
            mujoco.mj_saveModel(m, str(folder/'scene.mjb'), None)
            mujoco.mj_saveLastXML(str(folder/'scene.xml'), m)
            manifest.update(model_sha256=sha(folder/'scene.mjb'), physics_dt_s=float(m.opt.timestep),
                            safety_config=asdict(env.safety_config))
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
                '--simulation-time', '13', '--fps', '25', '--no-render']
        else:
            recipe = json.loads((ROOT/'configs'/('ball_source_demo.json' if scene=='ball' else 'workstation_source_demo.json')).read_text())
            flags = recipe['arguments']
            flags.update(dt=.00005, output=str(folder/'legacy'), menagerie=str(RUNTIME/'menagerie'))
            if scene == 'ball':
                flags['teacher_profile'] = 'none'
            else:
                # Reference video has local physical guards and no additional
                # workstation furniture; its title is the non-workstation branch.
                recipe['environment']['PANEL_CONFIG']['workstation'] = False
                recipe['environment']['CORE_VMC_CONFIG'] = {}
            for k, v in recipe['environment'].items():
                os.environ[k] = json.dumps(v) if isinstance(v, dict) else str(v)
            entry = ROOT/'scripts'/recipe['entrypoint']
            sys.argv = [str(entry)]
            for k,v in flags.items():
                if v is not None:
                    sys.argv += ['--'+k.replace('_','-'), str(v)]
            write(folder/'recipe.json', recipe)
        manifest.update(argv=sys.argv.copy(), entrypoint_sha256=sha(entry))
        write(folder/'execution.json', manifest)
        runpy.run_path(str(entry), run_name='__main__')
        replay = teacher_module.ParameterTeacher(config)
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
            np.savez_compressed(folder/'trajectory.npz', **{k:np.asarray([s[k] for s in states]) for k in states[0]},
                observation=np.asarray(observations), action=np.asarray(actions))
            np.savez_compressed(folder/'filter.npz', **{k:np.asarray([s[k] for s in chains]) for k in chains[0]})
            manifest.update(steps=len(states), physical_seconds=states[-1]['time'], substeps=sample_count,
                peak_torque_nm=peak_torque.tolist(), contacts=contact_stats, filter_config=asdict(filter_config),
                trajectory_sha256=sha(folder/'trajectory.npz'))
        files={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'scripts').glob('*.py')}
        files['tools/optimize_tool_contact_20261002.py']=sha(ROOT/'tools/optimize_tool_contact_20261002.py')
        write(folder/'SOURCE_HASHES.json', files)
        subprocess.run(['tar','-czf',str(folder/'source.tar.gz'),*files],cwd=ROOT,check=True)
        manifest['ended_utc']=datetime.now(timezone.utc).isoformat()
        write(folder/'execution.json', manifest)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--worker', choices=SCENES)
    p.add_argument('--scenes', nargs='+', choices=SCENES, default=SCENES)
    a=p.parse_args()
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


if __name__ == '__main__':
    main()
