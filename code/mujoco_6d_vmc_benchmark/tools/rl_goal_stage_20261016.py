"""Finite four-family stages under the user's persistent RL training goal.

Immutable source snapshot, one simulator, independent hard-limited services.
This dispatcher never runs acceptance or declares the persistent goal complete.
"""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from rl_recovery_control_20261016 import active_workers, verify_checkpoint, dispatch_reason
from goal_compute_backend_20261016 import backend, environment, GPU_RESOURCES, gpu_snapshot, gpu_admission_reason

BENCH = Path(__file__).resolve().parents[1]
GIB = 1024 ** 3


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write(path, data):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    temp.replace(path)


def now():
    return datetime.now(timezone.utc).isoformat()


def manifest(folder):
    return {str(p.relative_to(folder)): digest(p) for p in sorted(folder.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}


def interaction_budget(reg):
    """Keep historical pilots fixed; larger four-family continuations are explicit."""
    kind = reg.get('experiment_kind')
    if kind == 'gpu_training_preflight':
        assert 'finite_continuation_budget' not in reg
        return 1375
    if kind in ('fresh_direct_tracking_pilot', 'fresh_parameter_tracking_pilot'):
        assert 'finite_continuation_budget' not in reg
        return 11000
    assert kind is None, 'Unknown experiment budget kind'
    if 'finite_continuation_budget' not in reg:
        return 11000
    budget = reg['finite_continuation_budget']
    assert type(budget) is int and budget in (11000, 22000, 33000, 44000)
    assert reg.get('previous_stage') or reg.get('selected_lineages'), 'Larger stages require exact completed lineage'
    assert len(reg['jobs']) == 4 and {j['controller'] for j in reg['jobs']} == {
        None, 'impedance', 'admittance', 'vmc'}
    assert reg['maximum_new_interactions'] == 4 * budget
    return budget


def validate_training_job(args, protocol, protocol_hash):
    reg = read(args.goal_registration)
    assert reg['schema'] == 'sii-rl-persistent-goal-stage-v1'
    assert reg['compute_host'] == platform.node() == 'airpig'
    assert reg['parent_root'] == str(args.root.resolve())
    assert reg['parent_protocol_sha256'] == protocol_hash
    assert reg['server_compute'] is False and reg['acceptance_allowed'] is False
    assert args.steps == reg['optimizer_schedule_steps'] == protocol['budgets']['rl_steps_per_family_seed']
    job = next(j for j in reg['jobs'] if j['output'] == str(args.output.resolve()))
    assert str(args.parameter_source.resolve()) == reg['parameter_source']
    for key, value in [('controller', args.controller), ('reward', args.reward),
                       ('reward_variant', args.reward_variant), ('hp', args.hyperparameter_id),
                       ('seed', args.seed), ('limit', args.stop_at_step)]:
        assert job[key] == value, key
    assert job['checkpoint'] == (str(args.resume_checkpoint.resolve()) if args.resume_checkpoint else None)
    budget = interaction_budget(reg)
    assert job['limit'] - job['inherited_steps'] == reg['new_interactions_per_family'] == budget
    assert 0 <= job['inherited_steps'] < job['limit'] <= reg['optimizer_schedule_steps']
    if budget == 1375:
        assert backend(reg) == 'cuda' and job['checkpoint']
    if backend(reg) == 'cuda':
        verify_inputs(reg)
        verify_preflight(reg)
    return reg, job


def prepare(parent, destination, checkpoint):
    assert platform.node() == 'airpig'
    assert not destination.exists(), 'Never reuse a stage directory'
    proto = read(parent / 'PROTOCOL.json')
    cp = verify_checkpoint(checkpoint)
    saved = read(checkpoint.parent / 'PROTOCOL.json')
    assert saved['protocol_sha256'] == digest(parent / 'PROTOCOL.json')
    assert saved['reward_variant'] == 'task_safety' and saved['controller'] is None
    assert saved['agent_config']['n_step'] == 1
    assert read(checkpoint.parent / 'execution.json')['status'] == 'complete'
    assert digest(parent / 'CONDITIONS.json') == proto['condition_file_sha256']
    destination.mkdir(parents=True)
    source = destination / 'source'
    ignore = shutil.ignore_patterns('__pycache__', '*.pyc', 'outputs', '.git')
    for folder in ('scripts', 'tools', 'assets'):
        shutil.copytree(BENCH / folder, source / folder, ignore=ignore)
    parameter = destination / 'parameter_n25'
    shutil.copytree(parent / 'parameter_fullrange', parameter, ignore=ignore)
    (parameter / 'official_parameter_agent.py').rename(parameter / 'official_parameter_agent_base.py')
    (parameter / 'official_parameter_agent.py').write_text(
        'from pathlib import Path\nfrom goal_rl_credit_adapter_20261016 import make_goal_adapter\n'
        'BATCH_SIZE=256\nOfficialParameterAgent=make_goal_adapter('
        'Path(__file__).with_name("official_parameter_agent_base.py"),'
        + repr(str(checkpoint)) + ')\n')
    started = datetime.now(timezone.utc)
    jobs = []
    for old in proto['jobs']:
        direct = old['controller'] is None
        inherited = cp['step'] if direct else 0
        jobs.append(dict(name=old['name'], controller=old['controller'], reward=old['reward'],
            reward_variant=old['reward_variant'], hp=old['hp'], seed=proto['budgets']['training_seeds'][0],
            inherited_steps=inherited, limit=inherited + 11000, checkpoint=str(checkpoint) if direct else None,
            credit_migration=direct, output=str(destination / old['name']),
            unit='sii-rl-goal-' + hashlib.sha256(str(destination / old['name']).encode()).hexdigest()[:12]))
    reg = dict(schema='sii-rl-persistent-goal-stage-v1', registered_utc=started.isoformat(),
        authorization='2026-10-16 user explicitly enabled Goal: keep advancing RL training to convergence and autonomously repair problems',
        authorization_start_utc='2026-10-16T04:52:18+00:00',
        goal_scope='All four RL families, validated training convergence then common final testing; this stage is not completion',
        parent_root=str(parent), parent_protocol_sha256=digest(parent / 'PROTOCOL.json'),
        parent_checkpoint_hashes=cp['hashes'], run_root=str(destination), source=str(source),
        parameter_source=str(parameter), source_manifest=manifest(source), parameter_manifest=manifest(parameter),
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=BENCH, text=True).strip(),
        source_worktree_state='Source snapshot includes the new goal-stage implementation; content manifests are authoritative',
        compute_host='airpig', server_compute=False, python=str(BENCH.parents[2] / '.venv-sii-local-rl/bin/python'),
        runtime=proto['runtime'], source_base_commit=proto['source_base_commit'],
        dispatch_deadline_utc=(started + timedelta(hours=24)).isoformat(),
        deadline_basis='Agent-selected 24h fail-safe for this finite stage under the new persistent goal, not extension of the historical run',
        optimizer_schedule_steps=1000000, new_interactions_per_family=11000, maximum_new_interactions=44000,
        resources=dict(simulators=1, cpu='1', numerical_threads=1, memory_max=3*GIB,
                       swap_max=0, admission_reserve=768*1024**2),
        minimum_free_disk=50*GIB, stop_file=str(destination / 'STOP_REQUESTED'),
        dispatch_lock=str(BENCH / 'outputs/.v4_recovery_dispatch.lock'),
        coordinator_unit='sii-rl-goal-stage-' + hashlib.sha256(str(destination).encode()).hexdigest()[:12],
        jobs=jobs, n_step=25, utd=1, acceptance_allowed=False,
        credit_migration='Direct retains weights, optimizer, RNG, normalizers and raw replay. Only n_step changes 1->25; derived sampled returns are rebuilt, raw rewards stay unchanged. Other families start fresh.',
        limitations='Uncorrected multi-step off-policy bias; no matched fresh 1-step control in this stage; inherited/fresh exposures differ and must be reported.',
        evidence_basis='Historical online n25 phase never launched. Current n1 checkpoint terminal targets mostly fit while nonterminal Q and behavior returns diverge; that is a hypothesis, not proof of a bug.',
        training_convergence=dict(minimum_completed_episodes=96, window_episodes=32,
            adjacent_window_relative_mean_change_max=.05, last_window_return_cv_max=.25,
            required_task_and_strict_rate_each_last_window=.9,
            condition_coverage='Each of the last two windows must contain all 32 training identities; all failures retained',
            interpretation='Prospective training-screen criterion only; never replaces final acceptance or independent audit'))
    write(destination / 'REGISTRATION.json', reg)
    return reg


def completed_stage_checkpoints(reg, state):
    """Only exact closed final checkpoints of all four registered jobs qualify."""
    assert state['status'] == 'finite_stage_complete' and state.get('active') is None
    names = {job['name'] for job in reg['jobs']}
    assert len(reg['jobs']) == 4 and len(names) == 4
    assert {job['controller'] for job in reg['jobs']} == {None, 'impedance', 'admittance', 'vmc'}
    assert len(state['jobs']) == 4 and {row['job'] for row in state['jobs']} == names
    checkpoints = {}
    for job in reg['jobs']:
        row = next(row for row in state['jobs'] if row['job'] == job['name'])
        assert row['returncode'] == 0 and row['stop_reason'] == 'step_budget'
        output = Path(job['output'])
        execution = read(output / 'execution.json')
        assert execution['status'] == 'complete' and execution['stop_reason'] == 'step_budget'
        assert execution['rows'] and all('ended_utc' in r for r in execution['rows'])
        cp = verify_checkpoint(Path(execution['checkpoint_rows'][-1]['path']))
        assert Path(cp['path']).parent == output
        assert cp['step'] == execution['steps'] == row['steps']
        assert cp == row['checkpoint'], 'Coordinator and trainer checkpoint disagree'
        assert job['inherited_steps'] < cp['step'] <= job['limit']
        assert job['limit'] - cp['step'] < 1375, 'Unexpected unfinished step budget'
        spec = read(output / 'PROTOCOL.json')
        assert spec['protocol_sha256'] == reg['parent_protocol_sha256']
        assert spec['goal_registration_sha256'] == digest(Path(reg['run_root']) / 'REGISTRATION.json')
        assert spec['agent_config']['n_step'] == 25 and spec['utd'] == 1
        assert spec['controller'] == job['controller'] and spec['seed'] == job['seed']
        assert spec['reward_variant'] == job['reward_variant'] and spec['hyperparameter_id'] == job['hp']
        checkpoints[job['name']] = cp
    return checkpoints


def prepare_next(previous, destination, gpu_preflight=False, interactions_per_family=11000):
    """Prepare one finite continuation; never dispatch or restart a fresh model."""
    assert platform.node() == 'airpig'
    assert not destination.exists(), 'Never reuse a stage directory'
    assert type(interactions_per_family) is int and interactions_per_family in (11000, 22000, 33000, 44000)
    assert not gpu_preflight or interactions_per_family == 11000, 'GPU preflight budget remains 1375'
    old = read(previous / 'REGISTRATION.json')
    verify_inputs(old)
    state = read(previous / 'execution.json')
    assert state['registration_sha256'] == digest(previous / 'REGISTRATION.json')
    checkpoints = completed_stage_checkpoints(old, state)
    # Default11k; explicit continuation may cover one32-condition cycle.
    # GPU validation stays1375; optimizer schedule and rewards stay unchanged.
    if old.get('experiment_kind') == 'gpu_training_preflight':
        if not gpu_preflight:
            validate_gpu_training_closure(old, state)
    else:
        assert old['new_interactions_per_family'] == interaction_budget(old)
    assert old['optimizer_schedule_steps'] == 1000000
    if gpu_preflight:
        assert (backend(old) == 'cpu' and not old.get('experiment_kind')) or (
            backend(old) == 'cuda' and old.get('experiment_kind') == 'gpu_training_preflight')
    budget = 1375 if gpu_preflight else interactions_per_family
    assert all(cp['step'] + budget <= 1000000 for cp in checkpoints.values()), 'Final remainder requires explicit registration'
    destination.mkdir(parents=True)
    ignore = shutil.ignore_patterns('__pycache__', '*.pyc')
    source = destination / 'source'
    parameter = destination / 'parameter_n25'
    shutil.copytree(old['source'], source, ignore=ignore)
    shutil.copytree(old['parameter_source'], parameter, ignore=ignore)
    # Ordinary continuation keeps the trainer; explicit GPU validation replaces
    # its backend plumbing only. Physics/worker/parameter snapshots stay frozen.
    for name in ('rl_goal_stage_20261016.py', 'probe_goal_credit_20261016.py', 'goal_compute_backend_20261016.py'):
        shutil.copy2(BENCH / 'tools' / name, source / 'tools' / name)
    if gpu_preflight:
        shutil.copy2(BENCH/'tools/train_v4_recovery_rl_20261016.py', source/'tools/train_v4_recovery_rl_20261016.py')
        shutil.copy2(BENCH/'tools/goal_tracking_reward_20261016.py', source/'tools/goal_tracking_reward_20261016.py')
    started = datetime.now(timezone.utc)
    reg = dict(old)
    reg.pop('selected_lineages', None)
    reg.pop('selection_basis', None)
    reg.pop('parent_checkpoint_hashes', None)
    reg.pop('experiment_kind', None)
    reg.pop('finite_continuation_budget', None)
    if not gpu_preflight and budget != 11000:
        reg['finite_continuation_budget'] = budget
    jobs = []
    for job in old['jobs']:
        cp = checkpoints[job['name']]
        output = destination / job['name']
        jobs.append(dict(job, inherited_steps=cp['step'], limit=cp['step']+budget,
            checkpoint=cp['path'], checkpoint_hashes=cp['hashes'], credit_migration=False,
            backend_migration=gpu_preflight and backend(old) == 'cpu',
            parent_execution_sha256=digest(Path(job['output']) / 'execution.json'),
            output=str(output), unit='sii-rl-goal-'+hashlib.sha256(str(output).encode()).hexdigest()[:12]))
    reg.update(registered_utc=started.isoformat(), run_root=str(destination), source=str(source),
        parameter_source=str(parameter), source_manifest=manifest(source), parameter_manifest=manifest(parameter),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=BENCH,text=True).strip(),
        source_worktree_state='Parent frozen source retained; dispatcher, backend guard and replay preflight copied from current worktree. Content manifests authoritative.',
        previous_stage=dict(root=str(previous),registration_sha256=digest(previous/'REGISTRATION.json'),
            execution_sha256=digest(previous/'execution.json')),
        dispatch_deadline_utc=(started+timedelta(hours=24)).isoformat(),
        stop_file=str(destination/'STOP_REQUESTED'),jobs=jobs,
        coordinator_unit='sii-rl-goal-stage-'+hashlib.sha256(str(destination).encode()).hexdigest()[:12],
        preflight_required_jobs=[job['name'] for job in jobs],
        new_interactions_per_family=budget, maximum_new_interactions=4*budget,
        credit_migration='None: all four families resume their own exact n25 checkpoints with raw replay, optimizer, normalizers and RNG.',
        evidence_basis='Exact continuation of a completed finite stage; no new treatment and no convergence claim.')
    if gpu_preflight:
        reg.update(experiment_kind='gpu_training_preflight',
            resources=dict(old['resources'], **GPU_RESOURCES),
            source_worktree_state='Parent physics/worker/parameter retained. Trainer, dispatcher, backend guard and replay preflight updated for explicit CPU-to-CUDA migration.',
            evidence_basis='Local disposable fixed-batch CPU/CUDA probe passed. Four-family one-full-episode stage validates actual training loop; no full-loop speedup claim yet.',
            backend_migration='Portable weights, optimizer, RNG, normalizers and replay retained. CUDA floating point differs; no bitwise trajectory-equivalence claim.')
    elif old.get('experiment_kind') == 'gpu_training_preflight':
        reg['gpu_training_validation'] = dict(root=str(previous),
            registration_sha256=digest(previous/'REGISTRATION.json'), execution_sha256=digest(previous/'execution.json'))
    write(destination/'REGISTRATION.json',reg)
    return reg


def validate_gpu_training_closure(reg, state):
    assert reg['experiment_kind'] == 'gpu_training_preflight' and backend(reg) == 'cuda'
    completed_stage_checkpoints(reg, state)
    for job in reg['jobs']:
        training = read(Path(job['output'])/'execution.json')
        info = training['compute_runtime']
        assert info['learning_backend'] == 'cuda' and info['platforms'] == ['gpu']
        assert info['cpu_affinity'] == [int(reg['resources']['cpu'])]
        assert len(training['rows']) == 1 and training['rows'][0]['result']['full_task_horizon_completed']
        assert training['steps']-job['inherited_steps'] == 1375
        resources = training['resource_snapshot']
        assert resources['memory_events']['oom'] == resources['memory_events']['oom_kill'] == 0
        assert resources['memory_swap_current'] == 0
        assert resources['memory_peak'] <= 3*GIB


def verify_inputs(reg):
    assert platform.node() == reg['compute_host'] == 'airpig'
    assert digest(Path(reg['parent_root']) / 'PROTOCOL.json') == reg['parent_protocol_sha256']
    assert manifest(Path(reg['source'])) == reg['source_manifest'], 'Frozen source changed'
    assert manifest(Path(reg['parameter_source'])) == reg['parameter_manifest'], 'Parameter source changed'
    backend(reg)
    if reg.get('selected_lineages'):
        from goal_selected_continuation_20261016 import verify_selected_lineages
        verify_selected_lineages(reg)
    if backend(reg) == 'cuda' and reg.get('experiment_kind') != 'gpu_training_preflight':
        validated = reg['gpu_training_validation']; previous = Path(validated['root'])
        assert digest(previous/'REGISTRATION.json') == validated['registration_sha256']
        assert digest(previous/'execution.json') == validated['execution_sha256']
        validate_gpu_training_closure(read(previous/'REGISTRATION.json'), read(previous/'execution.json'))
    if reg.get('previous_stage'):
        previous = reg['previous_stage']
        root = Path(previous['root'])
        assert digest(root/'REGISTRATION.json') == previous['registration_sha256']
        assert digest(root/'execution.json') == previous['execution_sha256']
        for job in reg['jobs']:
            cp = Path(job['checkpoint'])
            assert digest(cp.parent/'execution.json') == job['parent_execution_sha256']
            assert verify_checkpoint(cp)['hashes'] == job['checkpoint_hashes']


def verify_preflight(reg):
    if reg.get('experiment_kind') in ('fresh_direct_tracking_pilot', 'fresh_parameter_tracking_pilot'):
        from goal_tracking_pilot_20261016 import verify_pilot_preflight
        return verify_pilot_preflight(reg)
    root = Path(reg['run_root'])
    digest_reg = digest(root/'REGISTRATION.json')
    preflight = read(root/'CREDIT_PREFLIGHT.json')
    assert preflight['status'] == 'passed' and preflight['registration_sha256'] == digest_reg
    if reg.get('preflight_required_jobs'):
        assert set(preflight['jobs']) == set(reg['preflight_required_jobs'])
        for name in reg['preflight_required_jobs']:
            receipt = root/f'CREDIT_PREFLIGHT_{name}.json'
            result = read(receipt)
            job = next(j for j in reg['jobs'] if j['name'] == name)
            assert preflight['jobs'][name] == digest(receipt)
            assert result['status'] == 'passed' and result['registration_sha256'] == digest_reg
            assert result['job'] == name and result['checkpoint'] == job['checkpoint']
            assert result['checkpoint_hashes'] == job['checkpoint_hashes']
            assert result['checkpoint_hashes_unchanged'] and result['inherited_steps'] == job['inherited_steps']
            assert result['actual_n_step'] == 25 and result['restored_raw_replay_count'] == job['inherited_steps']
            assert result['finite_update_metrics'] and result['terminal_windows_match'] and result['no_cross_episode_bootstrap']
            if backend(reg) == 'cuda':
                assert result['compute_runtime']['learning_backend'] == 'cuda'
                assert result['compute_runtime']['platforms'] == ['gpu']
    return preflight


def seal_preflight(root):
    reg = read(root/'REGISTRATION.json')
    verify_inputs(reg)
    assert not (root/'CREDIT_PREFLIGHT.json').exists()
    assert reg.get('preflight_required_jobs')
    receipts = {}
    for name in reg['preflight_required_jobs']:
        path = root/f'CREDIT_PREFLIGHT_{name}.json'
        result = read(path)
        job = next(j for j in reg['jobs'] if j['name'] == name)
        assert result['status'] == 'passed' and result['registration_sha256'] == digest(root/'REGISTRATION.json')
        assert result['job'] == name and result['checkpoint'] == job['checkpoint']
        assert result['checkpoint_hashes'] == job['checkpoint_hashes'] and result['checkpoint_hashes_unchanged']
        assert result['inherited_steps'] == job['inherited_steps']
        assert result['actual_n_step'] == 25 and result['restored_raw_replay_count'] == job['inherited_steps']
        assert result['finite_update_metrics'] and result['terminal_windows_match'] and result['no_cross_episode_bootstrap']
        if backend(reg) == 'cuda':
            assert result['compute_runtime']['learning_backend'] == 'cuda'
            assert result['compute_runtime']['platforms'] == ['gpu']
        receipts[name] = digest(path)
    write(root/'CREDIT_PREFLIGHT.json',dict(status='passed',registration_sha256=digest(root/'REGISTRATION.json'),
        jobs=receipts,simulation=False,gradient_updates=len(receipts),model_saved=False))
    verify_preflight(reg)


def worker_command(reg, job):
    runtime = Path(reg['runtime'])
    env = dict(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1',
        JAX_PLATFORMS='cpu', SII_RL_UTD='1', XLA_PYTHON_CLIENT_PREALLOCATE='false',
        SII_REWARD_PAYLOAD_TELEMETRY='1', SII_LOCAL_RUNTIME=str(runtime),
        MUJOCO_MENAGERIE_PATH=str(runtime / 'menagerie'))
    env.update(environment(reg))
    cmd = ['systemd-run', '--user', '--wait', '--pipe', '--unit=' + job['unit'],
        '--property=MemoryMax=3G', '--property=MemorySwapMax=0', '--property=CPUQuota=100%',
        '--property=CPUAffinity=1', '--property=TasksMax=256', '--working-directory=' + reg['source']]
    cmd += ['--setenv=' + k + '=' + v for k, v in env.items()]
    cmd += [reg['python'], str(Path(reg['source']) / 'tools/train_v4_recovery_rl_20261016.py'),
        '--root', reg['parent_root'], '--output', job['output'], '--parameter-source', reg['parameter_source'],
        '--seed', str(job['seed']), '--steps', str(reg['optimizer_schedule_steps']), '--stop-at-step', str(job['limit']),
        '--reward', job['reward'], '--reward-variant', job['reward_variant'], '--hyperparameter-id', job['hp'],
        '--goal-registration', str(Path(reg['run_root']) / 'REGISTRATION.json')]
    if job['controller']:
        cmd += ['--controller', job['controller']]
    if job['checkpoint']:
        cmd += ['--resume-checkpoint', job['checkpoint']]
    return cmd


def run(root):
    reg = read(root / 'REGISTRATION.json')
    if reg.get('experiment_kind') in ('fresh_direct_tracking_pilot', 'fresh_parameter_tracking_pilot'):
        from goal_tracking_pilot_20261016 import require_predecessor_complete
        require_predecessor_complete(reg)
    assert not (root / 'execution.json').exists(), 'Never retry in-place'
    assert len(list(Path('/proc').glob('[0-9]*'))) > 20, 'Host /proc required'
    verify_inputs(reg)
    verify_preflight(reg)
    with Path(reg['dispatch_lock']).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = dict(status='running', started_utc=now(), jobs=[], active=None,
                     registration_sha256=digest(root / 'REGISTRATION.json'), goal_complete=False)
        def save():
            state['updated_utc'] = now()
            write(root / 'execution.json', state)
        save()
        try:
            for job in reg['jobs']:
                verify_inputs(reg)
                available = next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()
                                 if x.startswith('MemAvailable:'))
                reason = dispatch_reason(datetime.fromisoformat(reg['dispatch_deadline_utc']),
                    datetime.now(timezone.utc), available, active_workers())
                if Path(reg['stop_file']).exists():
                    reason = 'cooperative_stop'
                if shutil.disk_usage(root).free < reg['minimum_free_disk']:
                    reason = 'disk_reserve'
                if backend(reg) == 'cuda' and not reason:
                    reason = gpu_admission_reason(reg, gpu_snapshot())
                if reason:
                    state.update(status='stopped_before_dispatch', reason=reason)
                    break
                if job['checkpoint']:
                    verify_checkpoint(Path(job['checkpoint']))
                assert not Path(job['output']).exists()
                command = worker_command(reg, job)
                receipt = dict(job=job['name'], command=command, started_utc=now(), available_bytes=available)
                state['jobs'].append(receipt)
                state['active'] = dict(job=job['name'], unit=job['unit'], output=job['output'])
                save()
                with (root / (job['name'] + '.log')).open('x') as log:
                    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
                receipt.update(returncode=result.returncode, ended_utc=now())
                state['active'] = None
                save()
                assert result.returncode == 0, 'Worker failed; preserve receipt and inspect before new stage'
                training = read(Path(job['output']) / 'execution.json')
                assert training['status'] == 'complete'
                cp = verify_checkpoint(Path(training['checkpoint_rows'][-1]['path']))
                receipt.update(steps=training['steps'], checkpoint=cp, stop_reason=training['stop_reason'],
                    completed_episodes=len([r for r in training['rows'] if 'ended_utc' in r]),
                    task=sum(r.get('result', {}).get('task_success', False) for r in training['rows']),
                    strict=sum(r.get('result', {}).get('strict_success', False) for r in training['rows']))
                if training['stop_reason'] != 'step_budget':
                    state.update(status='stopped_at_episode_boundary', reason=training['stop_reason'])
                    break
                save()
            else:
                state.update(status='finite_stage_complete', convergence_demonstrated=False)
        except BaseException as exc:
            state.update(status='failed_preserved', error=repr(exc))
            raise
        finally:
            state['ended_utc'] = now()
            save()


def launch(root):
    reg = read(root / 'REGISTRATION.json')
    if reg.get('experiment_kind') in ('fresh_direct_tracking_pilot', 'fresh_parameter_tracking_pilot'):
        from goal_tracking_pilot_20261016 import require_predecessor_complete
        require_predecessor_complete(reg)
    verify_inputs(reg)
    verify_preflight(reg)
    assert not (root / 'LAUNCH.json').exists() and not (root / 'execution.json').exists()
    assert not active_workers(), 'Another RL worker is active'
    assert Path(reg['python']).is_file()
    cmd = ['systemd-run', '--user', '--unit=' + reg['coordinator_unit'],
        '--property=MemoryMax=256M', '--property=MemorySwapMax=0', '--property=TasksMax=64',
        '--working-directory=' + reg['source'], reg['python'],
        str(Path(reg['source']) / 'tools/rl_goal_stage_20261016.py'), 'run', '--root', str(root)]
    write(root / 'LAUNCH.json', dict(command=cmd, started_utc=now()))
    subprocess.run(cmd, check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'prepare-next', 'prepare-gpu-preflight', 'seal-preflight', 'launch', 'run'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--parent', type=Path)
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--previous-stage', type=Path)
    parser.add_argument('--interactions-per-family', type=int, default=11000,
                        choices=(11000, 22000, 33000, 44000),
                        help='Explicit finite prepare-next budget; defaults to11000. No change to existing registrations.')
    args = parser.parse_args()
    if args.mode != 'prepare-next' and args.interactions_per_family != 11000:
        parser.error('--interactions-per-family applies only to prepare-next')
    if args.mode == 'prepare':
        print(json.dumps(prepare(args.parent.resolve(), args.root.resolve(), args.checkpoint.resolve()), indent=2))
    elif args.mode in ('prepare-next', 'prepare-gpu-preflight'):
        print(json.dumps(prepare_next(args.previous_stage.resolve(), args.root.resolve(),
                                     gpu_preflight=args.mode == 'prepare-gpu-preflight',
                                     interactions_per_family=args.interactions_per_family), indent=2))
    elif args.mode == 'seal-preflight':
        seal_preflight(args.root.resolve())
    elif args.mode == 'launch':
        launch(args.root.resolve())
    else:
        run(args.root.resolve())
