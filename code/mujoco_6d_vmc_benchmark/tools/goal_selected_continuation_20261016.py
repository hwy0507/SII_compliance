"""Resume four explicit completed training lineages without resetting learning.

Selection is recorded, never an automatic reward ranking. All sources must have
closed; fresh reward pilots are not misrepresented as four-family stages.
"""
import argparse
from pathlib import Path
import shutil

from rl_goal_stage_20261016 import (BENCH, read, write, digest, manifest,
    prepare_next, verify_inputs, completed_stage_checkpoints, job_parameter_source)
from rl_recovery_control_20261016 import verify_checkpoint

FAMILIES = {None, 'impedance', 'admittance', 'vmc'}
# Only dispatch/preflight tooling may differ. Every other frozen source and the
# shared parameter implementation must agree. A job-specific loss adapter must
# match its explicitly selected parent; the trainer migration is pinned below.
PLUMBING = {'tools/' + name for name in (
    'rl_goal_stage_20261016.py', 'probe_goal_credit_20261016.py',
    'goal_compute_backend_20261016.py', 'goal_tracking_pilot_20261016.py',
    'goal_selected_continuation_20261016.py', 'goal_actor_regularization_pilot_20261016.py',
    'goal_actor_regularization_20261016.py')}
JOB_FIELDS = ('controller', 'seed', 'reward', 'reward_variant', 'hp')
ACTOR_PILOT = 'resumed_actor_regularization_pilot'
TRAINER = 'tools/train_v4_recovery_rl_20261016.py'


def frozen(manifest_data):
    return {k: v for k, v in manifest_data.items() if k not in PLUMBING}


def regularization_origin(reg):
    if reg.get('experiment_kind') == ACTOR_PILOT:
        return dict(root=reg['run_root'],registration_sha256=digest(Path(reg['run_root'])/'REGISTRATION.json'))
    return reg.get('actor_regularization_origin')


def training_source(reg):
    """Normalize only the pinned loss-migration plumbing, never physics/reward."""
    data=dict(reg['source_manifest'])
    origin=regularization_origin(reg)
    if origin:
        root=Path(origin['root'])
        assert digest(root/'REGISTRATION.json')==origin['registration_sha256']
        pilot=read(root/'REGISTRATION.json')
        from goal_actor_regularization_pilot_20261016 import validate_pair
        validate_pair(pilot)
        assert data[TRAINER]==pilot['source_manifest'][TRAINER], 'Unregistered trainer change'
        parent=read(Path(pilot['pilot_predecessor']['root'])/'REGISTRATION.json')
        data[TRAINER]=parent['source_manifest'][TRAINER]
    return frozen(data)


def closed_source(root):
    root = Path(root).resolve()
    reg = read(root/'REGISTRATION.json')
    assert reg['run_root'] == str(root)
    verify_inputs(reg)
    state = read(root/'execution.json')
    assert state['registration_sha256'] == digest(root/'REGISTRATION.json')
    assert state['status'] == 'finite_stage_complete' and state.get('active') is None
    if reg.get('experiment_kind') == ACTOR_PILOT:
        from goal_actor_regularization_pilot_20261016 import require_predecessor_complete
        require_predecessor_complete(reg)
        checked = {}
    elif reg.get('experiment_kind') in ('fresh_direct_tracking_pilot', 'fresh_parameter_tracking_pilot'):
        from goal_tracking_pilot_20261016 import validate_pair
        validate_pair(reg)
        checked = {}
    else:
        checked = completed_stage_checkpoints(reg, state)
    assert len(state['jobs']) == len(reg['jobs'])
    assert {r['job'] for r in state['jobs']} == {j['name'] for j in reg['jobs']}
    result = {}
    for job in reg['jobs']:
        output = Path(job['output'])
        entry = next(r for r in state['jobs'] if r['job'] == job['name'])
        execution = read(output/'execution.json')
        assert entry['returncode'] == 0 and entry['stop_reason'] == 'step_budget'
        assert execution['status'] == 'complete' and execution['stop_reason'] == 'step_budget'
        assert execution['rows'] and all(r.get('ended_utc') for r in execution['rows'])
        cp = checked.get(job['name']) or verify_checkpoint(Path(execution['checkpoint_rows'][-1]['path']))
        assert Path(cp['path']).parent == output
        assert cp == entry['checkpoint'] and cp['step'] == execution['steps'] == entry['steps']
        assert job['inherited_steps'] < cp['step'] <= job['limit']
        assert job['limit']-cp['step'] < 1375
        spec = read(output/'PROTOCOL.json')
        assert spec['goal_registration_sha256'] == digest(root/'REGISTRATION.json')
        assert spec['protocol_sha256'] == reg['parent_protocol_sha256']
        assert spec['agent_config']['n_step'] == 25 and spec['utd'] == 1
        for key, field in (('controller','controller'),('seed','seed'),
                           ('reward_variant','reward_variant'),('hyperparameter_id','hp')):
            assert spec[key] == job[field]
        assert spec['reward']['mode'] == job['reward']
        assert spec.get('tracking_guidance') == job.get('tracking_guidance')
        if regularization_origin(reg):
            assert spec['agent_config']['actor_bc_alpha']==job.get('actor_bc_alpha',0.)
        result[job['name']] = dict(job=job, checkpoint=cp,
            execution_sha256=digest(output/'execution.json'), protocol_sha256=digest(output/'PROTOCOL.json'),
            parameter_source=job_parameter_source(reg,job),
            parameter_manifest=manifest(Path(job_parameter_source(reg,job))),
            regularization_origin=regularization_origin(reg))
    return reg, result


def compatible(current, parent):
    for key in ('parent_root','parent_protocol_sha256','runtime','python','compute_host',
                'optimizer_schedule_steps','resources','training_convergence'):
        assert current[key] == parent[key], f'Incompatible lineage {key}'
    assert current['parameter_manifest'] == parent['parameter_manifest'], 'Parameter implementation differs'
    assert training_source(current) == training_source(parent), 'Frozen training source differs'


def verify_selected_lineages(reg):
    assert not reg.get('previous_stage'), 'Selection and single-stage lineage are mutually exclusive'
    assert len(reg['jobs']) == 4 and {j['controller'] for j in reg['jobs']} == FAMILIES
    assert len({j['name'] for j in reg['jobs']}) == 4
    assert set(reg['selected_lineages']) == {j['name'] for j in reg['jobs']}
    assert reg.get('selection_basis'), 'A recorded decision is required'
    cache = {}
    for job in reg['jobs']:
        lineage = reg['selected_lineages'][job['name']]
        root = Path(lineage['root']).resolve()
        assert str(root) != reg['run_root'] and lineage.get('rationale')
        assert digest(root/'REGISTRATION.json') == lineage['registration_sha256']
        assert digest(root/'execution.json') == lineage['execution_sha256']
        if root not in cache:
            cache[root] = closed_source(root)
        parent, candidates = cache[root]
        compatible(reg, parent)
        selected = candidates[lineage['job']]
        old, cp = selected['job'], selected['checkpoint']
        assert all(job[k] == old[k] for k in JOB_FIELDS), 'Selected training objective/identity changed'
        assert job.get('tracking_guidance') == old.get('tracking_guidance'), 'Selected reward changed'
        assert manifest(Path(job_parameter_source(reg,job)))==selected['parameter_manifest'], 'Selected agent implementation changed'
        assert job.get('actor_bc_alpha',0.)==old.get('actor_bc_alpha',0.)
        assert not job.get('actor_regularization_migration'), 'A selected checkpoint is already migrated'
        assert job['checkpoint'] == cp['path'] and job['checkpoint_hashes'] == cp['hashes']
        assert job['inherited_steps'] == cp['step']
        assert job['parent_execution_sha256'] == selected['execution_sha256']
        assert lineage['protocol_sha256'] == selected['protocol_sha256']
        assert not job['credit_migration'] and not job.get('backend_migration')


def prepare_selected(base, selection, destination, interactions_per_family=11000):
    """Prepare only; caller still needs four replay preflights and normal launch."""
    base, destination = Path(base).resolve(), Path(destination).resolve()
    assert not destination.exists()
    base_reg, _ = closed_source(base)
    assert len(base_reg['jobs']) == 4 and {j['controller'] for j in base_reg['jobs']} == FAMILIES
    assert selection.get('decision') and set(selection['methods']) == {j['name'] for j in base_reg['jobs']}
    chosen, lineages, cache = {}, {}, {}
    # Validate every source before creating any destination. Running pilot arms
    # are not accepted merely because one side has already completed.
    for base_job in base_reg['jobs']:
        choice = selection['methods'][base_job['name']]
        assert choice.get('rationale')
        root = Path(choice['root']).resolve()
        if root not in cache:
            cache[root] = closed_source(root)
        parent, candidates = cache[root]
        compatible(base_reg, parent)
        item = candidates[choice['job']]
        assert item['job']['controller'] == base_job['controller']
        assert item['job']['seed'] == base_job['seed']
        assert item['checkpoint']['step']+interactions_per_family <= 1000000
        chosen[base_job['name']] = item
        lineages[base_job['name']] = dict(root=str(root),job=choice['job'],rationale=choice['rationale'],
            registration_sha256=digest(root/'REGISTRATION.json'),execution_sha256=digest(root/'execution.json'),
            protocol_sha256=item['protocol_sha256'])
    origins=[item['regularization_origin'] for item in chosen.values() if item['regularization_origin']]
    assert not origins or all(origin==origins[0] for origin in origins), 'Mixed migration origins require a new explicit protocol'
    reg = prepare_next(base, destination, interactions_per_family=interactions_per_family)
    reg.pop('previous_stage')
    reg.update(selected_lineages=lineages, selection_basis=selection['decision'],
        evidence_basis='Explicit four-method checkpoint selection from closed sources; preserved objectives, replay, optimizer, normalizers and RNG. No convergence claim.')
    if origins:
        reg['actor_regularization_origin']=origins[0]
        pilot=read(Path(origins[0]['root'])/'REGISTRATION.json')
        shutil.copy2(Path(pilot['source'])/TRAINER,Path(reg['source'])/TRAINER)
    for job in reg['jobs']:
        item = chosen[job['name']]
        old, cp = item['job'], item['checkpoint']
        job.update({key: old[key] for key in JOB_FIELDS})
        job.pop('tracking_guidance', None)
        if old.get('tracking_guidance') is not None:
            job['tracking_guidance'] = old['tracking_guidance']
        job.pop('parameter_source',None);job.pop('parameter_manifest',None)
        if item['parameter_manifest']!=reg['parameter_manifest']:
            parameter=destination/'selected_parameter_by_job'/job['name']
            shutil.copytree(item['parameter_source'],parameter,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            job.update(parameter_source=str(parameter),parameter_manifest=item['parameter_manifest'])
        if reg.get('actor_regularization_origin'):
            job.update(actor_bc_alpha=old.get('actor_bc_alpha',0.),actor_regularization_migration=False)
        job.update(checkpoint=cp['path'],checkpoint_hashes=cp['hashes'],inherited_steps=cp['step'],
            limit=cp['step']+interactions_per_family,parent_execution_sha256=item['execution_sha256'],
            credit_migration=False,backend_migration=False)
    # A four-family base can predate the pilot tooling. Selected ancestors are
    # validated at runtime, so their dispatch validator must travel with us too.
    for name in ('goal_selected_continuation_20261016.py','goal_tracking_pilot_20261016.py',
                 'goal_actor_regularization_pilot_20261016.py','goal_actor_regularization_20261016.py'):
        shutil.copy2(BENCH/'tools'/name,Path(reg['source'])/'tools'/name)
    reg['source_manifest'] = manifest(Path(reg['source']))
    write(destination/'REGISTRATION.json', reg)
    verify_inputs(reg)
    return reg


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,required=True)
    parser.add_argument('--selection',type=Path,required=True)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--interactions-per-family',type=int,choices=(11000,22000,33000,44000),default=11000)
    args = parser.parse_args()
    result = prepare_selected(args.base,read(args.selection),args.root,args.interactions_per_family)
    print(result['run_root'])
