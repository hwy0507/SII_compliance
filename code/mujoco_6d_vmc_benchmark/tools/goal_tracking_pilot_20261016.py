"""Finite fresh Direct or impedance reward comparison after a four-family stage.

Preparation and discarded-update preflight may run while the predecessor trains.
Launch/run require its four jobs to have closed successfully and the global lock.
Two pilot arms never count as four-family training or final acceptance.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

from rl_goal_stage_20261016 import (BENCH, read, write, digest, manifest, verify_inputs,
    completed_stage_checkpoints, validate_gpu_training_closure)
from rl_recovery_control_20261016 import verify_checkpoint
from goal_tracking_reward_20261016 import CONFIG, PARAMETER_CONFIG, tracking_terms
from goal_compute_backend_20261016 import backend, runtime_info, GPU_RESOURCES


def pair_settings(controller):
    if controller is None:
        return dict(prefix='direct', reward='office_task', variant='task_safety',
                    hp='direct_explore', config=CONFIG, kind='fresh_direct_tracking_pilot')
    assert controller == 'impedance', 'Only the evidenced impedance treatment is registered'
    return dict(prefix='impedance', reward='metric', variant='payload_shaping',
                hp='parameter_balanced', config=PARAMETER_CONFIG, kind='fresh_parameter_tracking_pilot')


def validate_pair(reg):
    assert len(reg['jobs']) == 2 and reg['maximum_new_interactions'] == 22000
    control, treatment = reg['jobs']
    settings = pair_settings(control['controller'])
    assert reg['experiment_kind'] == settings['kind']
    assert control['name'] == settings['prefix']+'_control' and treatment['name'] == settings['prefix']+'_tracking'
    for job in reg['jobs']:
        assert job['checkpoint'] is None and job['inherited_steps'] == 0 and job['limit'] == 11000
        assert job['controller'] == control['controller'] and job['reward'] == settings['reward']
        assert job['reward_variant'] == settings['variant'] and job['hp'] == settings['hp']
        assert not job['credit_migration']
    excluded = {'name','output','unit','tracking_guidance'}
    assert {k:v for k,v in control.items() if k not in excluded} == {
        k:v for k,v in treatment.items() if k not in excluded}, 'Only tracking reward may differ'
    assert control.get('tracking_guidance') is None and treatment['tracking_guidance'] == settings['config']
    assert reg['new_interactions_per_family'] == 11000 and reg['optimizer_schedule_steps'] == 1000000


def require_predecessor_complete(reg):
    validate_pair(reg)
    predecessor = reg['pilot_predecessor']; root = Path(predecessor['root'])
    assert digest(root/'REGISTRATION.json') == predecessor['registration_sha256']
    old = read(root/'REGISTRATION.json'); state = read(root/'execution.json')
    assert state['registration_sha256'] == predecessor['registration_sha256']
    verify_inputs(old)
    return completed_stage_checkpoints(old, state)


def prepare(previous, destination, checkpoint, reward_receipt, controller=None):
    assert not destination.exists(), 'Preserve every pilot attempt'
    old = read(previous/'REGISTRATION.json'); verify_inputs(old)
    assert len(old['jobs']) == 4 and not old.get('experiment_kind')
    cp = verify_checkpoint(checkpoint)
    receipt = read(reward_receipt)
    settings = pair_settings(controller)
    assert receipt['protocol_snapshot']['controller'] == controller
    assert receipt['protocol_snapshot']['reward_variant'] == settings['variant']
    if controller:
        assert receipt['protocol_snapshot']['reward']['error_weight'] == PARAMETER_CONFIG['base_error_weight']
    assert receipt['protocol_sha256'] == digest(checkpoint.parent/'PROTOCOL.json')
    parent_job = next(j for j in old['jobs'] if j['controller'] == controller)
    assert checkpoint.parent == Path(parent_job['output'])
    # Use one complete recorded training episode for a discarded-update preflight.
    row = next(r for r in receipt['execution_snapshot']['rows'] if 'ended_utc' in r)
    assert row['step_after'] <= cp['step']
    destination.mkdir(parents=True)
    ignore = shutil.ignore_patterns('__pycache__','*.pyc')
    source = destination/'source'; parameter = destination/'parameter_n25'
    shutil.copytree(old['source'], source, ignore=ignore)
    shutil.copytree(old['parameter_source'], parameter, ignore=ignore)
    for name in ('rl_goal_stage_20261016.py','train_v4_recovery_rl_20261016.py',
                 'goal_tracking_reward_20261016.py','goal_tracking_pilot_20261016.py',
                 'goal_compute_backend_20261016.py'):
        shutil.copy2(BENCH/'tools'/name, source/'tools'/name)
    jobs = []
    for name in (settings['prefix']+'_control',settings['prefix']+'_tracking'):
        output = destination/name
        job = dict(name=name,controller=controller,reward=settings['reward'],reward_variant=settings['variant'],
            hp=settings['hp'],seed=parent_job['seed'],inherited_steps=0,limit=11000,
            checkpoint=None,credit_migration=False,output=str(output),
            unit='sii-rl-goal-'+hashlib.sha256(str(output).encode()).hexdigest()[:12])
        if name.endswith('_tracking'): job['tracking_guidance'] = dict(settings['config'])
        jobs.append(job)
    reg = dict(old)
    for key in ('parent_checkpoint_hashes','previous_stage','preflight_required_jobs'):
        reg.pop(key, None)
    started = datetime.now(timezone.utc)
    reg.update(experiment_kind=settings['kind'], registered_utc=started.isoformat(),
        run_root=str(destination),source=str(source),parameter_source=str(parameter),
        source_manifest=manifest(source),parameter_manifest=manifest(parameter),jobs=jobs,
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=BENCH,text=True).strip(),
        source_worktree_state='Frozen predecessor physics/worker/parameter retained; only trainer, tracking component and dispatch tools replaced. Manifests authoritative.',
        maximum_new_interactions=22000,dispatch_deadline_utc=(started+timedelta(hours=24)).isoformat(),
        stop_file=str(destination/'STOP_REQUESTED'),
        coordinator_unit='sii-rl-goal-stage-'+hashlib.sha256(str(destination).encode()).hexdigest()[:12],
        pilot_predecessor=dict(root=str(previous),registration_sha256=digest(previous/'REGISTRATION.json')),
        pilot_probe=dict(checkpoint=str(checkpoint),hashes=cp['hashes'],reward_receipt=str(reward_receipt),
                         reward_receipt_sha256=digest(reward_receipt),episode=row['episode']),
        credit_migration='None: both arms fresh model/optimizer/replay/normalizers/RNG; same seed and warmup.',
        evidence_basis=('Recorded Direct safe failures have equal discounted base return despite different tracking cost.' if controller is None else
            'Eight closed impedance failures remain at carry waypoint20; discounted tracking cost around0.09 versus torque1.6-2.8. Test tenfold tracking weight4->40 with one added weight36 component; no gate or physical change.'),
        limitations='Single seed, eight full-horizon episodes per arm at most; pilot feasibility only, not convergence or four-family completion. Historical training is not the matched control.',
        comparison='Report every Task/Strict result, stage reached and physical tracking cost on matched train identities; do not compare different-objective reward totals as improvement.')
    validate_pair(reg); write(destination/'REGISTRATION.json',reg)
    return reg


def verify_pilot_preflight(reg):
    validate_pair(reg)
    root = Path(reg['run_root']); result = read(root/'CREDIT_PREFLIGHT.json')
    assert result['status'] == 'passed' and result['registration_sha256'] == digest(root/'REGISTRATION.json')
    assert result['initial_networks_equal'] and result['checkpoint_hashes_unchanged']
    assert result['gradient_updates'] == 2 and not result['model_saved'] and not result['simulation']
    assert result['source_checkpoint'] == reg['pilot_probe']['checkpoint']
    assert result['source_checkpoint_hashes'] == reg['pilot_probe']['hashes']
    assert result['reward_receipt_sha256'] == reg['pilot_probe']['reward_receipt_sha256']
    assert set(result['arms']) == {j['name'] for j in reg['jobs']}
    if backend(reg) == 'cuda':
        assert result['compute_runtime']['learning_backend'] == 'cuda'
        assert result['compute_runtime']['platforms'] == ['gpu']
    for job in reg['jobs']:
        arm = result['arms'][job['name']]
        assert arm['fresh_before'] and arm['n_step'] == 25 and arm['finite_update']
        assert arm['terminal_window_checked'] and arm['guidance'] == job.get('tracking_guidance')
    return result


def prepare_gpu_pilot(cpu_pilot, validation, destination):
    """New fresh pair only after actual four-family CUDA full-loop validation.

    Preserve the original CPU experiment and all historical model checkpoints.
    The new pair needs its own CUDA discarded-update preflight before launch.
    """
    assert not destination.exists(), 'Preserve every pilot attempt'
    old = read(cpu_pilot/'REGISTRATION.json')
    verify_inputs(old); validate_pair(old); verify_pilot_preflight(old)
    assert backend(old) == 'cpu'
    assert not (cpu_pilot/'LAUNCH.json').exists() and not (cpu_pilot/'execution.json').exists(), \
        'Only an unlaunched CPU pilot can be superseded by this fresh GPU pair'
    require_predecessor_complete(old)
    gpu = read(validation/'REGISTRATION.json'); state = read(validation/'execution.json')
    verify_inputs(gpu); validate_gpu_training_closure(gpu,state)
    assert state['registration_sha256'] == digest(validation/'REGISTRATION.json')
    for key in ('parent_root','parent_protocol_sha256','runtime','python','compute_host','dispatch_lock'):
        assert old[key] == gpu[key], 'CUDA validation must use the same frozen task/runtime'
    assert old['parameter_manifest'] == gpu['parameter_manifest']
    # Dispatch and learning plumbing may differ; physical worker/scripts/assets
    # must match the validation used to authorize these full training loops.
    physical = lambda files: {k:v for k,v in files.items() if
        k.startswith(('scripts/','assets/')) or k == 'tools/baseline_repair_worker_20261008.py'}
    assert physical(old['source_manifest']) == physical(gpu['source_manifest'])
    destination.mkdir(parents=True)
    ignore=shutil.ignore_patterns('__pycache__','*.pyc')
    source=destination/'source'; parameter=destination/'parameter_n25'
    shutil.copytree(old['source'],source,ignore=ignore)
    shutil.copytree(old['parameter_source'],parameter,ignore=ignore)
    # Only this preparation entry point is added; retain the paired trainer and
    # reward implementation that already passed the original CPU preflight.
    shutil.copy2(BENCH/'tools/goal_tracking_pilot_20261016.py',source/'tools/goal_tracking_pilot_20261016.py')
    started=datetime.now(timezone.utc)
    jobs=[]
    for job in old['jobs']:
        output=destination/job['name']
        jobs.append(dict(job,output=str(output),
            unit='sii-rl-goal-'+hashlib.sha256(str(output).encode()).hexdigest()[:12]))
    reg=dict(old,run_root=str(destination),source=str(source),parameter_source=str(parameter),
        source_manifest=manifest(source),parameter_manifest=manifest(parameter),jobs=jobs,
        registered_utc=started.isoformat(),dispatch_deadline_utc=(started+timedelta(hours=24)).isoformat(),
        stop_file=str(destination/'STOP_REQUESTED'),
        coordinator_unit='sii-rl-goal-stage-'+hashlib.sha256(str(destination).encode()).hexdigest()[:12],
        resources=dict(old['resources'],**GPU_RESOURCES),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=BENCH,text=True).strip(),
        source_worktree_state='Original fresh CPU pair source retained except GPU-pair preparation entry point; content manifests authoritative.',
        gpu_training_validation=dict(root=str(validation),registration_sha256=digest(validation/'REGISTRATION.json'),
            execution_sha256=digest(validation/'execution.json')),
        derived_from_cpu_pilot=dict(root=str(cpu_pilot),registration_sha256=digest(cpu_pilot/'REGISTRATION.json'),
            cpu_preflight_sha256=digest(cpu_pilot/'CREDIT_PREFLIGHT.json')),
        backend_migration='None: both arms initialize fresh on CUDA; historical checkpoint is diagnostic replay only. CPU pair remains unlaunched.')
    validate_pair(reg); verify_inputs(reg)
    write(destination/'REGISTRATION.json',reg)
    return reg


def preflight(root):
    reg = read(root/'REGISTRATION.json'); verify_inputs(reg); validate_pair(reg)
    out = root/'CREDIT_PREFLIGHT.json'; assert not out.exists()
    probe = reg['pilot_probe']; cp = Path(probe['checkpoint'])
    assert verify_checkpoint(cp)['hashes'] == probe['hashes']
    assert digest(probe['reward_receipt']) == probe['reward_receipt_sha256']
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::')[1].lstrip('/')
    assert int((cg/'memory.max').read_text()) <= 2*1024**3 and (cg/'memory.swap.max').read_text().strip() == '0'
    result = dict(status='running',registration_sha256=digest(root/'REGISTRATION.json'),
        simulation=False,gradient_updates=0,model_saved=False,arms={},
        source_checkpoint=str(cp),source_checkpoint_hashes=probe['hashes'],
        reward_receipt_sha256=probe['reward_receipt_sha256'])
    write(out,result)
    try:
        if backend(reg) == 'cuda':
            result['compute_runtime'] = runtime_info(reg, expected_cpu=6)
        import numpy as np
        from flax import serialization
        sys.path.insert(0,reg['parameter_source'])
        from official_parameter_agent import OfficialParameterAgent
        from multistep_rl_replay_20261009 import MultiStepReplay
        from baseline_repair_rl_diagnostics_20261008 import flatten_metrics
        receipt = read(probe['reward_receipt'])
        row = next(r for r in receipt['execution_snapshot']['rows'] if r['episode'] == probe['episode'])
        logs = receipt['closed_log_entries'][str(row['episode'])]
        assert len(logs) == row['steps']
        with np.load(cp/'office_replay.npz',allow_pickle=False) as data:
            raw = {key:data[key][row['step_before']:row['step_after']].copy() for key in data.files}
        np.testing.assert_allclose(raw['reward'],[e['terms']['final_reward'] for e in logs],rtol=1e-6,atol=1e-6)
        assert raw['terminated'][-1] and not raw['terminated'][:-1].any() and not raw['truncated'].any()
        hp = read(Path(reg['parent_root'])/'PROTOCOL.json')['rl_hyperparameters'][reg['jobs'][0]['hp']]
        dimension = receipt['protocol_snapshot']['agent_config']['action_dimension']
        initial_hashes = []
        for job in reg['jobs']:
            agent = OfficialParameterAgent(seed=job['seed'],total_steps=1000000,utd=1,gamma=.9995,
                entropy_coef=hp['entropy_coef'],initial_temperature=hp['initial_temperature'],action_dimension=dimension)
            assert agent.interactions == agent.updates == agent.reward_samples == 0
            initial_hashes.append({name:hashlib.sha256(serialization.to_bytes(getattr(agent.raw_agent,name))).hexdigest()
                for name in ('_actor','_critic','_target_critic','_temperature')})
            replay = MultiStepReplay(len(logs),dimension,job['seed']+53,n_step=25,gamma=.9995)
            previous_time = 0.
            for i, entry in enumerate(logs):
                terms = entry['terms']; reward = float(raw['reward'][i]); elapsed = terms['elapsed_s']
                if job.get('tracking_guidance'):
                    reward += sum(tracking_terms(terms['bounded_error_cost'],elapsed-previous_time,elapsed,
                        terminated=terms['terminated'],success=terms['success'],config=job['tracking_guidance']).values())
                agent.sample_action(raw['observation'][i],training=True)
                agent.consume_transition(reward,bool(raw['terminated'][i]))
                transition = {k:v[i] for k,v in raw.items()}; transition['reward'] = reward
                replay.add(**transition); previous_time = elapsed
            start = len(logs)-25
            terminal = replay.at(np.arange(start,len(logs)))
            expected = [sum(.9995**j*float(replay.data['reward'][i+j]) for j in range(len(logs)-i))
                        for i in range(start,len(logs))]
            np.testing.assert_allclose(terminal['reward'],expected,rtol=2e-6,atol=2e-6)
            assert terminal['terminated'].all()
            metrics = flatten_metrics(agent.update(replay.sample(256)))
            assert agent.updates == 1 and all(np.isfinite(v) for v in metrics.values())
            result['gradient_updates'] += 1
            result['arms'][job['name']] = dict(fresh_before=True,n_step=agent.config['n_step'],
                guidance=job.get('tracking_guidance'),finite_update=True,terminal_window_checked=True,
                diagnostic_replay_count=replay.count,metrics=metrics,initial_network_hashes=initial_hashes[-1])
            del agent, replay
        result.update(initial_networks_equal=initial_hashes[0]==initial_hashes[1],
            checkpoint_hashes_unchanged=all(digest(cp/k)==v for k,v in probe['hashes'].items()),status='passed')
        assert result['initial_networks_equal'] and result['checkpoint_hashes_unchanged']
    except BaseException as exc:
        result.update(status='failed_preserved',error=repr(exc)); raise
    finally:
        result.update(peak_memory_bytes=int((cg/'memory.peak').read_text()),memory_events=(cg/'memory.events').read_text())
        write(out,result)
    verify_pilot_preflight(reg)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','prepare-gpu','preflight','check-ready'))
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--previous-stage',type=Path)
    p.add_argument('--checkpoint',type=Path)
    p.add_argument('--reward-receipt',type=Path)
    p.add_argument('--controller',choices=('impedance',))
    p.add_argument('--cpu-pilot',type=Path)
    p.add_argument('--gpu-validation',type=Path)
    a = p.parse_args()
    if a.mode == 'prepare':
        prepare(a.previous_stage.resolve(),a.root.resolve(),a.checkpoint.resolve(),a.reward_receipt.resolve(),a.controller)
    elif a.mode == 'prepare-gpu':
        prepare_gpu_pilot(a.cpu_pilot.resolve(),a.gpu_validation.resolve(),a.root.resolve())
    elif a.mode == 'preflight': preflight(a.root.resolve())
    else: require_predecessor_complete(read(a.root.resolve()/'REGISTRATION.json'))
