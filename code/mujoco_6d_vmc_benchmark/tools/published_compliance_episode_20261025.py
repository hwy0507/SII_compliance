"""Source-built office episode with canonical48 IPC and reward-only telemetry.

Execute one episode per process: controller monkeypatches cannot leak between
episodes. Original task success, safety aborts, physics, and public filters stay
in the shared evaluator. New source-built worlds are explicitly distinct from
the unavailable historical frozen MJB. This is an adapter, not a new simulator.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np


def encode(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)


def write(path, value):
    Path(path).write_text(json.dumps(value, default=encode, indent=2, allow_nan=False)+'\n')


def run(args):
    root, out = args.runtime.resolve(), args.output.resolve()
    if out.exists():
        raise FileExistsError('Preserve earlier attempts; choose a new episode path')
    metadata = json.loads((root/'RUNTIME.json').read_text())
    for filename, subdir in [('SOURCE_HASHES.json', 'source'), ('PARAMETER_HASHES.json', 'parameter')]:
        for name, digest in json.loads((root/filename).read_text()).items():
            if hashlib.sha256((root/subdir/name).read_bytes()).hexdigest() != digest:
                raise ValueError('Runtime source drift: '+name)
    os.environ['MUJOCO_MENAGERIE_PATH'] = metadata['menagerie']
    for name, digest in json.loads((root/'ROBOT_ASSET_HASHES.json').read_text()).items():
        if hashlib.sha256((Path(metadata['menagerie'])/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Robot asset drift: '+name)
    # Physics-only runs require no OpenGL/EGL library or display service.
    os.environ.setdefault('MUJOCO_GL', 'disable')
    sys.path[:0] = [str(root/'source/tools'), str(root/'source/scripts'), str(root/'parameter')]
    import mujoco
    import validate_office_apparatus_v5_20260917 as evaluator
    import audit_office_complex_scene_v5_20260917 as geometry
    from payload_reward_potential_20261014 import payload_potential
    from spt_rl_reward_20261025 import contact_integrals
    from baseline_repair_reward_clock_20261009 import slew_cost_rows
    if mujoco.__version__ != metadata['mujoco_version']:
        raise ValueError('MuJoCo runtime version drift')
    out.mkdir(parents=True)
    fixture = json.loads(args.fixture.read_text()) if args.fixture else None
    if fixture is not None:
        if args.reference_plan is None:
            raise ValueError('All disturbed conditions require the same frozen nominal reference plan')
        from planned_hand_corner_20261002 import PlannedCornerTask
        import planned_hand_corner_20261002 as planner
        frozen_plan = json.loads(args.reference_plan.read_text())
        routes = {int(k): [(np.asarray(p['hand']), np.asarray(p['rotation'])) for p in route]
                  for k, route in frozen_plan['routes'].items()}

        def common_plan(env, base, blind_edge=False, allow_lateral_rejoin=False):
            # Apparatus/obstacle geometry is not fed back into planning. The
            # planned task/gates are unchanged; all methods face the same
            # blocked nominal trajectory and physical contact resolution.
            base.destination = np.asarray(frozen_plan['destination']).copy()
            task = PlannedCornerTask(base, routes)
            task.allow_lateral_rejoin = allow_lateral_rejoin
            return task, dict(frozen_plan, common_reference_plan_sha256=hashlib.sha256(
                args.reference_plan.read_bytes()).hexdigest(), replan_for_fixture=False)

        planner.build_plan = common_plan
    if args.nominal_reference:
        if fixture or args.ipc or args.controller != 'direct':
            raise ValueError('Nominal reference is a separate zero-policy construction run')
        import xml.etree.ElementTree as ET
        original_xml = geometry.extend_complex_xml

        def reference_xml(*a, **kw):
            tree = ET.fromstring(original_xml(*a, **kw))
            for parent in tree.iter():
                for node in list(parent):
                    if node.get('name') in ('office_v5_pillar', 'office_v5_pillar_mount',
                                           'office_v5_cup', 'office_v5_corner_face'):
                        parent.remove(node)
            for name, position in [('office_v5_ball', '1.7 -1.5 .3'),
                                   ('office_v5_push_rod', '1.7 1.5 .3'),
                                   ('office_v5_person', '2.5 1 -.35')]:
                tree.find(f".//body[@name='{name}']").set('pos', position)
            return ET.tostring(tree, encoding='unicode')

        geometry.extend_complex_xml = reference_xml
    if fixture is not None:
        from teacher_bank_rollout_20260930 import training_xml
        original_xml = geometry.extend_complex_xml
        geometry.extend_complex_xml = lambda *a, **kw: training_xml(original_xml(*a, **kw), fixture)
    source = inspect.getsource(evaluator.run)
    original_source = source
    state = dict(rows=[], previous_tau=None, placement_hold_s=0., terminal_time_s=0.)
    channel = sys.stdout

    def send(value):
        print(json.dumps(value, default=encode, allow_nan=False), file=channel, flush=True)

    def potential(env):
        return payload_potential(env.data.xpos[env._hand_id],
                                 env.data.xpos[env._target_body_id], env.reference.destination)

    def sample(env, stats, human_force):
        # Live physical-step actuator force and coincident contact telemetry.
        state['rows'].append((float(env.model.opt.timestep), env.data.qfrc_actuator[:7].copy(),
                              float(human_force), float(stats['max_external_penetration_m'])))

    def interval(env):
        rows = state['rows']
        if not rows:
            return None
        dt = np.array([r[0] for r in rows])
        tau = np.array([r[1] for r in rows])
        forces = np.array([r[2] for r in rows])
        limits = np.asarray(env.torque_limits)[:7]
        previous = tau[0] if state['previous_tau'] is None else state['previous_tau']
        slew = float(slew_cost_rows(tau, env.safety_config.maximum_torque_rate_nmps, previous).sum())
        state['previous_tau'] = tau[-1].copy()
        result = dict(elapsed_s=float(dt.sum()), peak_torque_ratio=float(np.max(abs(tau)/limits)),
                      peak_torque_nm_per_joint=np.max(abs(tau), axis=0),
                      external_penetration_peak_m=max(r[3] for r in rows), torque_slew_cost=slew,
                      spt_contact=contact_integrals(dt, tau, limits, forces),
                      payload_potential=potential(env), substeps=len(rows))
        state['rows'] = []
        return result

    class Policy:
        label = 'published-baseline source-runtime '+args.controller

        def __init__(self, env):
            self.env = env
            self.observation = None
            self.actions = 0
            self.controller = None
            self.dimension = 7
            self.journal = (out/'actor_intervals.jsonl').open('x', buffering=1)
            if args.controller != 'direct':
                from controllers import ParameterController
                prior = json.loads((root/'parameter/PRIORS.json').read_text())['methods'][args.controller]
                self.dimension = prior['action_dimension']
                self.controller = ParameterController(env, args.controller, prior)
            state['policy'] = self

        def act(self, observation):
            if observation.shape != (48,) or not np.isfinite(observation).all():
                raise ValueError('Invalid canonical48')
            self.observation = observation.copy()
            iv = interval(self.env)
            if args.ipc:
                send(dict(kind='observation', observation=observation, interval=iv,
                          payload_potential=potential(self.env), action_dimension=self.dimension))
                line = sys.stdin.readline()
                if not line:
                    raise RuntimeError('Learner action pipe closed')
                action = np.asarray(json.loads(line)['action'], float)
            else:
                action = np.zeros(self.dimension)
            if action.shape != (self.dimension,) or not np.isfinite(action).all() or np.max(abs(action)) > 1.000001:
                raise ValueError('Invalid normalized action')
            if self.controller is None and action[0] < 0:
                raise ValueError('Direct authority action must be in [0, 1]')
            executed = self.controller.act(observation, action) if self.controller else action
            self.journal.write(json.dumps(dict(observation=observation, action=action,
                executed_action=executed, interval=iv, payload_potential=potential(self.env)),
                default=encode, allow_nan=False)+'\n')
            self.actions += 1
            return executed

        def finish(self, folder):
            state['terminal_interval'] = interval(self.env)
            state['terminal_potential'] = potential(self.env)
            self.journal.close()
            if self.controller:
                self.controller.save(folder)
            return dict(actor_input='canonical48', action_dimension=self.dimension, actions=self.actions,
                        controller=args.controller, reward_truth_in_actor=False)

    def placement(hold, timestamp):
        state['placement_hold_s'] = float(hold)
        state['terminal_time_s'] = float(timestamp)

    replacements = [
        ('    abort_reason=None\n    for step_index',
         '    external_policy=PUBLISHED_POLICY(env)\n    abort_reason=None\n    for step_index'),
        ('        interval_peak[:]=0.;interval_impulse[:]=0.\n        env.step(applied)',
         '        applied=np.asarray(external_policy.act(observation.copy()),dtype=float)\n'
         '        signal.update(applied_action=applied.copy())\n'
         '        interval_peak[:]=0.;interval_impulse[:]=0.\n        env.step(applied)'),
        ("        records.append(dict(time=float(d.time),qpos=d.qpos.copy()",
         "        PUBLISHED_PLACEMENT(placement_hold,d.time)\n        records.append(dict(time=float(d.time),qpos=d.qpos.copy()"),
        ("    result['metrics']=metrics.save(",
         "    result['baseline_policy']=external_policy.finish(a.output.parent)\n    result['metrics']=metrics.save("),
        ('        resultant={};touch_ball=False;', '        human_force_sum=0.\n        resultant={};touch_ball=False;'),
        ('            world=ct.frame.reshape(3,3).T@f[:3]*(1 if g2 in robot else -1)',
         "            if key in ('person_hand','other_person_body'):human_force_sum+=float(np.linalg.norm(f[:3]))\n"
         '            world=ct.frame.reshape(3,3).T@f[:3]*(1 if g2 in robot else -1)'),
        ('        metrics.sample()', '        metrics.sample();PUBLISHED_SAMPLE(env,stats,human_force_sum)'),
    ]
    if fixture:
        replacements += [
            ('    configs = interaction_schedule(a)', '    configs = PUBLISHED_SCHEDULE'),
            ('d.qvel[ball_dof+1]=a.ball_speed', 'd.qvel[ball_dof:ball_dof+3]=PUBLISHED_BALL_VELOCITY'),
            ('incoming[1]>.05 and any(v[1]<-.05 for v in bounce_samples)',
             'np.dot(incoming,PUBLISHED_BALL_AXIS)>.05 and any(np.dot(v,PUBLISHED_BALL_AXIS)<-.05 for v in bounce_samples)'),
        ]
        evaluator.PUBLISHED_BALL_AXIS = np.asarray(fixture['axis'])
        evaluator.PUBLISHED_BALL_VELOCITY = evaluator.PUBLISHED_BALL_AXIS*fixture['ball_speed_mps']
        evaluator.PUBLISHED_SCHEDULE = {kind: dict(start=fixture['start_s'], press=fixture['press_s'],
            hold=fixture['hold_s'], retract=fixture['retract_s'], stroke=fixture['stroke_m'],
            force_limit=fixture['drive_limit_n']) for kind in ('person', 'rod')}
    for old, new in replacements:
        expected = 2 if old == 'd.qvel[ball_dof+1]=a.ball_speed' else 1
        if source.count(old) != expected:
            raise ValueError('Evaluator seam changed: '+old)
        source = source.replace(old, new)
    evaluator.PUBLISHED_POLICY = Policy
    evaluator.PUBLISHED_SAMPLE = sample
    evaluator.PUBLISHED_PLACEMENT = placement
    exec(compile(source, str(out/'executed_evaluator.py.txt'), 'exec'), evaluator.__dict__)
    (out/'executed_evaluator.py.txt').write_text(source)
    flags = dict(output=out/'rollout', render=False, events='settle', task='pick_place',
                 corner_placement=True, planned_hand_corner=True, allow_lateral_rejoin=True,
                 combined_thick_corner_pillar_v4=True, seed=2026091751, variant=0,
                 duration=55., dt=.00005, ball_speed=1.7, ball_launch_time_s=2.,
                 person_stroke=.20, rod_stroke=.235, esn_model=None, esn_mode='shadow', teacher='none',
                 physics_probe_s=args.probe_seconds)
    if fixture:
        flags.update(seed=fixture['seed'], ball_speed=fixture['ball_speed_mps'],
                     ball_launch_time_s=fixture['start_s'], person_stroke=fixture['stroke_m'],
                     rod_stroke=fixture['stroke_m'], events={'passive_corner': 'settle',
                     'active_short': 'ball', 'active_long': fixture['apparatus']}[fixture['category']])
    write(out/'ADAPTER.json', dict(runtime=str(root), fixture=fixture, arguments=flags,
        adapter_file_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        reference_plan=str(args.reference_plan) if args.reference_plan else None,
        reference_plan_sha256=hashlib.sha256(args.reference_plan.read_bytes()).hexdigest() if args.reference_plan else None,
        original_evaluator_function_sha256=hashlib.sha256(original_source.encode()).hexdigest(),
        executed_evaluator_function_sha256=hashlib.sha256(source.encode()).hexdigest(),
        historical_model=False, nominal_reference_only=args.nominal_reference,
        scope='source-built new cohort preflight', actor_truth=False))
    try:
        with (out/'evaluator.log').open('x') as log, contextlib.redirect_stdout(log):
            evaluator.run(SimpleNamespace(**flags))
        result = json.loads((out/'rollout.json').read_text())
        # Final stable run must include the final horizon, rather than an early
        # transient placement. Samples are on the original 40 ms gate clock.
        completion = None
        if result['task_success']:
            completion = state['terminal_time_s']-state['placement_hold_s']+13*.04
        telemetry = dict(completion_time_s=completion,
            completion_definition='final_stable_placement_certification',
            placement_hold_s=state['placement_hold_s'], terminal_time_s=state['terminal_time_s'],
            model_sha256=hashlib.sha256((out/'rollout.mjb').read_bytes()).hexdigest(),
            result={k: result[k] for k in ('task_success', 'strict_success', 'abort_reason',
                    'full_task_horizon_completed', 'physical_valid', 'final_task_stage')},
            interval=state.get('terminal_interval'), payload_potential=state.get('terminal_potential'))
        write(out/'TERMINAL.json', telemetry)
        send(dict(kind='terminal', **telemetry,
                  observation=state['policy'].observation,
                  terminal_observation_valid=False, bootstrap_mask=0.))
    except BaseException as error:
        write(out/'FAILURE.json', dict(type=type(error).__name__, error=str(error)))
        send(dict(kind='error', error=repr(error)))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fixture', type=Path)
    parser.add_argument('--reference-plan', type=Path)
    parser.add_argument('--controller', choices=('direct', 'impedance', 'admittance', 'vmc'), default='direct')
    parser.add_argument('--ipc', action='store_true')
    parser.add_argument('--probe-seconds', type=float)
    parser.add_argument('--nominal-reference', action='store_true',
        help='Separate disturbance-free zero-policy reference for apparatus placement; never a task benchmark result')
    run(parser.parse_args())
