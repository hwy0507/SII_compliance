"""Single-environment PPO bridge to the unmodified canonical panel runner.

The runner executes in one synchronous worker thread. Its policy.act publishes
the exact 48-D observation and waits for the Gym caller's 7-D action. This keeps
reset, task transitions, event timing, observer, WBC and safety code in one
original implementation. No simulation worker processes or parallel envs.
"""
from __future__ import annotations

import contextlib
import gc
import hashlib
import json
import os
from pathlib import Path
import queue
import sys
import threading
import traceback
from types import SimpleNamespace

import gymnasium as gym
import numpy as np
import psutil


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_SHA256 = '8762b865a9bce8f3dd98e3495d71b3ad0e05d900c69e7e878b98b46fbff78847'
RUN_LOCK = threading.Lock()  # runner mutates process environment/module hooks
ACTION_LOW = np.array([0., -1., -1., -1., -1., -1., -1.], dtype=np.float32)
ACTION_HIGH = np.ones(7, dtype=np.float32)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    def encode(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, Path):
            return str(obj)
        raise TypeError(f'Cannot serialize {type(obj).__name__}')
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False, default=encode)+'\n')


def resource_check(max_rss_gib=7., min_available_gib=2.5):
    rss = psutil.Process().memory_info().rss/2**30
    available = psutil.virtual_memory().available/2**30
    if rss > max_rss_gib or available < min_available_gib:
        raise MemoryError(f'RL resource guard: RSS={rss:.2f}GiB, available={available:.2f}GiB')
    return dict(rss_gib=rss, available_gib=available)


def load_fixture_specs(assets):
    """First row by manifest order, never selected by candidate performance."""
    assets = Path(assets)
    manifest_path = assets/'manifest.json'
    if sha(manifest_path) != MANIFEST_SHA256:
        raise ValueError('Unexpected canonical teacher manifest hash')
    manifest = json.loads(manifest_path.read_text())
    if manifest['contract'] != 'proprio48_action7_6d_v1':
        raise ValueError('Expected canonical 48D bank')
    # Verify all three complete split identifiers, even though this minimal
    # pilot intentionally never opens held-out test episode data.
    intersections = {}
    for field in ('physical_fixture', 'fixture_hash', 'parameter_group', 'content_hash'):
        groups = {s:{r[field] for r in manifest['rows'] if r['split']==s}
                  for s in ('train', 'validation', 'test')}
        for a, b in (('train', 'validation'), ('train', 'test'), ('validation', 'test')):
            overlap = groups[a] & groups[b]
            if overlap:
                raise ValueError(f'Split leakage: {field} {a}/{b}')
            intersections[f'{field}:{a}/{b}'] = 0
    specs = {}
    for split, group, directory in (('train', 'rod', 'train_rod'),
                                     ('validation', 'front', 'validation_front')):
        row = next(r for r in manifest['rows'] if r['scene']=='push' and r['split']==split)
        if row['physical_fixture'] != group:
            raise ValueError('Frozen first-row fixture selection changed')
        folder = assets/directory
        command = json.loads((folder/'command.json').read_text())
        result = json.loads((folder/'rollout.json').read_text())
        search = json.loads((folder/'search_result.json').read_text())
        if search['group'] != group or result['arguments']['output']+'.json' != row['source_result']:
            raise ValueError('Teacher metadata does not match the selected manifest row')
        specs[split] = dict(row=row, command=command, arguments=result['arguments'],
            historical_scene=result['scene'], historical_panel=result['experiment_contract']['panel_config'],
            historical_physical_panels=result['panel_audit']['physical_panels'],
            focus=search['metrics']['focus'], original_checks=search['metrics']['checks'],
            original_reward='teacher search multiobjective score; no RL reward in canonical imitation dataset',
            source_hashes={n:sha(folder/n) for n in ('command.json', 'rollout.json', 'search_result.json')})
    return specs, intersections


def runtime_argv(spec, output, menagerie, duration=None):
    arguments = dict(spec['arguments'])
    arguments.update(output=str(output), menagerie=str(Path(menagerie).resolve()),
                     model='canonical48_ppo_in_memory', mixture=0., render=False,
                     teacher_force_source='estimated', teacher_profile='memory')
    if duration is not None:
        arguments['duration'] = duration
    argv = []
    for key, value in arguments.items():
        if value is None or value is False:
            continue
        flag = '--'+key.replace('_', '-')
        argv.extend([flag] if value is True else [flag, str(value)])
    return argv


class EpisodeCancelled(BaseException):
    pass


class QueuePolicy:
    kind = 'ppo_canonical48_action7_development'

    def __init__(self, publish, receive, state, direct_action=None):
        self.publish, self.receive, self.state = publish, receive, state
        self.direct_action = direct_action
        self.observations, self.actions, self.phases = [], [], []

    def act(self, observation):
        obs = np.asarray(observation, dtype=np.float64).copy()
        if obs.shape != (48,) or not np.all(np.isfinite(obs)):
            raise ValueError(f'Canonical actor contract requires finite 48D, got {obs.shape}')
        resource_check()
        # This metadata is available to the reward logger only, never appended
        # to actor/critic observation. The actor receives exactly obs below.
        phase = int(self.state['task'].index)
        if self.direct_action is None:
            self.publish.put(('observation', obs, phase))
            action = self.receive.get()
            if action is None:
                raise EpisodeCancelled()
        else:
            action = self.direct_action(obs.copy())
        action = np.asarray(action, dtype=np.float64)
        if action.shape != (7,) or not np.all(np.isfinite(action)):
            raise ValueError('Expected finite 7D action')
        if np.any(action < ACTION_LOW) or np.any(action > ACTION_HIGH):
            raise ValueError('Action outside canonical slowdown[0,1]/yield[-1,1] limits')
        self.observations.append(obs)
        self.actions.append(action.copy())
        self.phases.append(phase)
        return action


def run_episode(spec, menagerie, output, publish, receive, duration=None, direct_action=None):
    """Hook only policy loading and state capture; execute original runner main."""
    import current_student_policy_20260921 as loader
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=False)
    state = {}
    policy = QueuePolicy(publish, receive, state, direct_action)
    source = ROOT/'scripts/run_panel_push_20260920.py'
    text = source.read_text()
    marker = '    run=module.run\n'
    if text.count(marker) != 1:
        raise RuntimeError('Canonical panel controller hook contract changed')
    text = text.replace(marker, '    _install_rl(module)\n'+marker)

    def install(module):
        create = module.create_environment
        def capture(args):
            env, task, scene = create(args)
            if env.execution_mode != 'twist' or env.observation_mode != 'direct_esn':
                raise ValueError('Unsupported canonical execution backend')
            if not np.isclose(module.RL_DT, .04):
                raise ValueError('Unexpected canonical action period')
            state.update(env=env, task=task)
            save_json(output.parent/'execution_contract.json', dict(
                robot=env.robot, execution=env.execution_mode, observation='proprio48_action7_6d_v1',
                wbc_type=type(env.fixed_wbc).__name__, wbc_source=env.fixed_wbc.source_name,
                nominal_wbc_config=vars(env.fixed_wbc.config), safety_config=vars(env.safety_config),
                simulation_dt_s=float(env.model.opt.timestep), action_period_s=module.RL_DT,
                input_order='q7,qdot7,nominal_twist6,pose_error6,twist_error6,estimated_joint_load7,estimated_wrench6,path_direction3',
                actor_privileged_fields=[], teacher_called=False))
            return env, task, scene
        module.create_environment = capture
        loader.load_current = lambda _: policy

    if not RUN_LOCK.acquire(blocking=False):
        raise RuntimeError('Only one canonical simulator may run in this process')
    previous_env, previous_argv, previous_load = dict(os.environ), sys.argv, loader.load_current
    try:
        configured = spec['command']['environment']
        # Do not inherit server cache paths or any earlier trial's apparatus
        # environment. The fixture settings here are the archived command.
        for key in list(os.environ):
            if key.startswith(('PUSH_', 'PANEL_', 'CORE_VMC_', 'UNIFIED_', 'VMC_MODEL_CACHE_')):
                os.environ.pop(key)
        for key in ('PANEL_CONFIG', 'CORE_VMC_CONFIG', 'PANELS_ENABLED'):
            os.environ[key] = configured[key]
        panel_config = json.loads(os.environ['PANEL_CONFIG'])
        panel_config['rod_height_m'] = spec['historical_scene']['push_height']
        os.environ['PANEL_CONFIG'] = json.dumps(panel_config)
        os.environ.update(UNIFIED_6D_TEACHER='1',
            PRIMITIVE_RUNNER_PATH=str(ROOT/'scripts/run_primitive_teacher_v7_20260917.py'),
            SKIP_MODEL_ARCHIVE='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
        argv = runtime_argv(spec, output, menagerie, duration)
        save_json(output.parent/'rl_episode_command.json', dict(argv=argv, source_row=spec['row'],
            environment={key:os.environ[key] for key in ('PANEL_CONFIG','CORE_VMC_CONFIG',
                                                       'PANELS_ENABLED','UNIFIED_6D_TEACHER','PRIMITIVE_RUNNER_PATH')},
            actor_inputs='canonical48 only; audit and task-phase metadata never concatenated'))
        namespace = dict(__name__='canonical48_rl_runtime', __file__=str(source), _install_rl=install)
        sys.argv = [str(source), *argv]
        with (output.parent/'runner.log').open('w') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            exec(compile(text, str(source), 'exec'), namespace)
            namespace['main']()
        result = json.loads(output.with_suffix('.json').read_text())
        scene_differences = {key:dict(historical=value, current=result['scene'].get(key))
            for key,value in spec['historical_scene'].items() if result['scene'].get(key) != value}
        panels_match = result['panel_audit']['physical_panels'] == spec['historical_physical_panels']
        save_json(output.parent/'historical_config_audit.json', dict(
            scene_differences=scene_differences, physical_panels_equal=panels_match,
            explicit_default_restoration={'rod_height_m':panel_config['rod_height_m']},
            historical_runtime_byte_equivalence_proven=False,
            scope='Current canonical48/action7 runtime with reconstructed manifest fixture'))
        if scene_differences or not panels_match:
            raise ValueError('Reconstructed scene/panel differs from historical fixture')
        if result['teacher_called'] or result['contract'] != 'proprio48_action7_6d_v1':
            raise ValueError('Incorrect canonical episode contract')
        publish.put(('terminal', result, int(result['final_stage'])))
    except EpisodeCancelled:
        save_json(output.parent/'partial_episode.json', dict(status='budget/reset interruption',
            samples=len(policy.actions), source_row=spec['row'], scored_as_completed=False))
    except BaseException as error:
        failure = dict(error=repr(error), traceback=traceback.format_exc(), samples=len(policy.actions),
                       source_row=spec['row'])
        save_json(output.parent/'failure.json', failure)
        publish.put(('error', failure, None))
    finally:
        np.savez_compressed(output.parent/'actor_trace.npz', observation=np.asarray(policy.observations),
                            action=np.asarray(policy.actions), phase_reward_metadata=np.asarray(policy.phases))
        if 'env' in state and state['env'].model is not None:
            state['env'].close()
        loader.load_current = previous_load
        sys.argv = previous_argv
        os.environ.clear(); os.environ.update(previous_env)
        state.clear()
        RUN_LOCK.release()
        gc.collect()


def reward_from_transition(observation, action, previous_action, phase_delta=0, terminal=None):
    """Reward shaping uses causal actor observations, action and task progress.

    Terminal task/safety labels are reward-only supervision. There is no oracle
    contact impulse/position in the actor or value network input.
    """
    obs = np.asarray(observation)
    terms = dict(position=-.04*4.*float(np.linalg.norm(obs[20:23])),
                 rotation=-.04*.15*float(np.linalg.norm(obs[23:26])),
                 estimated_force=-.04*.002*float(np.linalg.norm(obs[39:42])),
                 action=-.04*.05*float(np.dot(action, action)),
                 action_change=-.04*.01*float(np.sum((action-previous_action)**2)),
                 progress=.5*max(phase_delta, 0), terminal=0.)
    if terminal is not None:
        terms['terminal'] = 5.*bool(terminal.get('success')) - 5.*bool(terminal.get('invalid_physics'))
    return sum(terms.values()), terms


def evaluation_summary(result, spec):
    contacts = result['panel_audit']['contacts']
    focus = contacts[spec['focus']]
    external = [v for k,v in contacts.items() if k != 'target_object_geom']
    penetration = max(v['max_penetration_m'] for v in external)
    focus_contact = focus['duration_s'] > .001
    # The validation front fixture has NO rod stroke. A rod-release gate
    # would be the wrong task; record the original checks but don't reuse its
    # historical accepted label as new experimental success.
    passed = bool(result['success'] and not result['invalid_physics'] and
                  not result.get('upstream_contact', False) and focus_contact and penetration <= .0002)
    return dict(source_id=spec['row']['id'], split=spec['row']['split'],
        physical_fixture=spec['row']['physical_fixture'], focus=spec['focus'],
        task_success=result['success'], development_gate=passed,
        gate_definition='task success AND no invalid/upstream AND correct focus contact AND all external penetration<=0.2mm',
        original_teacher_checks=spec['original_checks'], original_teacher_gate_reused=False,
        max_external_penetration_m=penetration, focus_contact=focus_contact,
        peak_external_resultant_force_n=max(v['peak_resultant_force_n'] for v in external),
        peak_torque_nm=result['peak_torque_nm'], speed_p95_mps=result['speed_p95_mps'],
        endpoint_error_m=result['endpoint_error_m'], final_stage=result['final_stage'],
        publication_ready=False)


class Canonical48Env(gym.Env):
    metadata = {'render_modes': []}

    def __init__(self, spec, menagerie, output_root, duration=None):
        super().__init__()
        self.spec, self.menagerie = spec, menagerie
        self.output_root = Path(output_root)
        self.duration = duration
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, shape=(48,), dtype=np.float32)
        self.action_space = gym.spaces.Box(ACTION_LOW, ACTION_HIGH, dtype=np.float32)
        self.worker = None
        self.episode_index = 0
        self.last_result = None

    def _next(self):
        while True:
            try:
                event = self.publish.get(timeout=5.)
                break
            except queue.Empty:
                if not self.worker.is_alive():
                    raise RuntimeError('Canonical runner exited before publishing an event')
        if event[0] == 'error':
            self.worker.join()
            raise RuntimeError(event[1]['traceback'])
        return event

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.close()
        resource_check()
        self.publish, self.receive = queue.Queue(), queue.Queue()
        output = self.output_root/f'episode_{self.episode_index:05d}'/'rollout'
        self.episode_index += 1
        self.worker = threading.Thread(target=run_episode,
            args=(self.spec, self.menagerie, output, self.publish, self.receive, self.duration), daemon=True)
        self.worker.start()
        event, observation, phase = self._next()
        if event != 'observation':
            raise RuntimeError('Canonical reset did not reach the actor boundary')
        self.obs, self.phase = observation, phase
        self.previous_action = np.zeros(7)
        self.last_result = None
        return self.obs.astype(np.float32), {}

    def step(self, action):
        action = np.asarray(action, dtype=np.float64)
        if action.shape != (7,) or not np.isfinite(action).all():
            raise ValueError('Nonfinite/invalid action')
        action = np.clip(action, ACTION_LOW, ACTION_HIGH)
        self.receive.put(action)
        event, value, phase = self._next()
        done = event == 'terminal'
        if done:
            self.worker.join()
            self.last_result = value
            # No invented terminal observation: use the last actor observation
            # and terminate (no bootstrap from an audit-only state).
            observation = self.obs
        else:
            observation = value
        reward, terms = reward_from_transition(observation, action, self.previous_action,
                                               phase-self.phase, value if done else None)
        self.obs, self.phase, self.previous_action = observation, phase, action.copy()
        info = {'reward_terms':terms}
        if done:
            info['evaluation'] = evaluation_summary(value, self.spec)
        return self.obs.astype(np.float32), float(reward), done, False, info

    def close(self):
        if self.worker is not None and self.worker.is_alive():
            self.receive.put(None)
            self.worker.join(timeout=60.)
            if self.worker.is_alive():
                raise RuntimeError('Canonical worker did not stop safely')
        self.worker = None
