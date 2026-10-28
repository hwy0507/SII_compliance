"""Resume four explicit completed training lineages without resetting learning.

Selection is recorded, never an automatic reward ranking. All sources must have
closed; fresh reward pilots are not misrepresented as four-family stages.
"""
import argparse
from pathlib import Path
import shutil

from rl_goal_stage_20261016 import (BENCH, read, write, digest, manifest,
    prepare_next, verify_inputs, completed_stage_checkpoints, job_parameter_source, require_stream_destination)
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
OCCUPANCY_PILOT = 'fresh_parameter_occupancy_pilot'
TRAINER = 'tools/train_v4_recovery_rl_20261016.py'
OCCUPANCY_HELPER = 'tools/goal_payload_occupancy_reward_20261016.py'
STORAGE_HELPER = 'tools/goal_prospective_storage_20261017.py'
# Reviewed archive-at-boundary migration. Do not ignore arbitrary trainer or
# storage changes merely because a registration calls them storage plumbing.
STORAGE_MIGRATION_HASHES = {
    TRAINER: 'c6f52e81bea7ef01fcea73b3d0c9d8bf30046df700bfd59c5e95edc21750550e',
    STORAGE_HELPER: '2c7f98aaf1c342763855be9698770dd8881ce079e898a802802917e342df1311',
}


def frozen(manifest_data):
    return {k: v for k, v in manifest_data.items() if k not in PLUMBING}


def regularization_origin(reg):
    if reg.get('experiment_kind') == ACTOR_PILOT:
        return dict(root=reg['run_root'],registration_sha256=digest(Path(reg['run_root'])/'REGISTRATION.json'))
    return reg.get('actor_regularization_origin')


def occupancy_origin(reg):
    if reg.get('experiment_kind') == OCCUPANCY_PILOT:
        return dict(root=reg['run_root'],registration_sha256=digest(Path(reg['run_root'])/'REGISTRATION.json'))
    return reg.get('payload_occupancy_origin')


def training_source(reg):
    """Compare frozen sources through exact registered optional-code migrations.

    This normalizes implementation availability, never a job's reward setting.
    The selected parent protocol and each reward field are checked separately.
    """
    data=dict(reg['source_manifest'])
    occupancy=occupancy_origin(reg)
    if occupancy:
        root=Path(occupancy['root'])
        assert digest(root/'REGISTRATION.json')==occupancy['registration_sha256']
        pilot=read(root/'REGISTRATION.json')
        from goal_tracking_pilot_20261016 import validate_pair
        validate_pair(pilot)
        assert pilot['experiment_kind']==OCCUPANCY_PILOT
        if pilot.get('storage_predecessor'):
            from goal_prospective_storage_20261017 import validate as validate_storage
            validate_storage(root)
            predecessor=pilot['storage_predecessor'];old_root=Path(predecessor['root'])
            assert digest(old_root/'REGISTRATION.json')==predecessor['registration_sha256'], 'Storage predecessor changed'
            old=read(old_root/'REGISTRATION.json');validate_pair(old)
            assert old['experiment_kind']==OCCUPANCY_PILOT and not old.get('storage_predecessor')
            assert pilot['pilot_predecessor']==old['pilot_predecessor'], 'Storage migration changed training ancestry'
            assert pilot['parameter_manifest']==old['parameter_manifest'], 'Storage migration changed parameter implementation'
            for key,expected in STORAGE_MIGRATION_HASHES.items():
                assert pilot['source_manifest'][key]==data[key]==expected, 'Unregistered storage implementation change'
                if key in old['source_manifest']:
                    data[key]=old['source_manifest'][key]
                else:
                    data.pop(key)
            assert frozen(data)==frozen(old['source_manifest']), 'Storage migration changed other frozen source'
            pilot=old
        pred=pilot['pilot_predecessor'];parent_root=Path(pred['root'])
        assert digest(parent_root/'REGISTRATION.json')==pred['registration_sha256']
        parent=read(parent_root/'REGISTRATION.json')
        for key in (TRAINER,OCCUPANCY_HELPER):
            assert data[key]==pilot['source_manifest'][key], 'Unregistered occupancy implementation change'
            if key in parent['source_manifest']:
                data[key]=parent['source_manifest'][key]
            else:
                data.pop(key)
        assert frozen(data)==frozen(parent['source_manifest']), 'Occupancy migration changed other frozen source'
        normalized=training_source(parent)
        actor=regularization_origin(reg)
        if actor:
            actor_root=Path(actor['root'])
            assert digest(actor_root/'REGISTRATION.json')==actor['registration_sha256']
            # Both registered optional paths must share the same frozen base.
            assert training_source(read(actor_root/'REGISTRATION.json'))==normalized
        return normalized
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
    elif reg.get('experiment_kind') in ('fresh_direct_tracking_pilot', 'fresh_parameter_tracking_pilot', OCCUPANCY_PILOT):
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
        assert spec.get('payload_occupancy_guidance') == job.get('payload_occupancy_guidance')
        if regularization_origin(reg):
            assert spec['agent_config']['actor_bc_alpha']==job.get('actor_bc_alpha',0.)
        result[job['name']] = dict(job=job, checkpoint=cp,
            execution_sha256=digest(output/'execution.json'), protocol_sha256=digest(output/'PROTOCOL.json'),
            parameter_source=job_parameter_source(reg,job),
            parameter_manifest=manifest(Path(job_parameter_source(reg,job))),
            regularization_origin=regularization_origin(reg),occupancy_origin=occupancy_origin(reg))
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
        assert job.get('payload_occupancy_guidance') == old.get('payload_occupancy_guidance'), 'Selected occupancy reward changed'
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
    occupancy_origins=[item['occupancy_origin'] for item in chosen.values() if item['occupancy_origin']]
    if not occupancy_origins and base_reg.get('payload_occupancy_origin'):
        # Retain already registered optional-code availability when all chosen
        # models use older objectives; each selected job still clears its field.
        occupancy_origins=[base_reg['payload_occupancy_origin']]
    assert not occupancy_origins or all(origin==occupancy_origins[0] for origin in occupancy_origins), 'Mixed occupancy origins require a new explicit protocol'
    storage_parents = [parent for parent in [base_reg, *(value[0] for value in cache.values())]
                       if parent.get('working_set_policy')]
    if storage_parents:
        from goal_prospective_storage_20261017 import SCHEMA
        require_stream_destination(destination)
        for parent in storage_parents:
            assert parent['working_set_policy'] == SCHEMA
            assert parent['storage_resources'] == dict(cpu=6,memory_max_bytes=1024**3,swap_max_bytes=0)
            assert all(parent['source_manifest'].get(key)==value for key,value in STORAGE_MIGRATION_HASHES.items())
    reg = prepare_next(base, destination, interactions_per_family=interactions_per_family,
                       _defer_storage_seal=True)
    reg.pop('previous_stage')
    reg.update(selected_lineages=lineages, selection_basis=selection['decision'],
        evidence_basis='Explicit four-method checkpoint selection from closed sources; preserved objectives, replay, optimizer, normalizers and RNG. No convergence claim.')
    if origins:
        reg['actor_regularization_origin']=origins[0]
        pilot=read(Path(origins[0]['root'])/'REGISTRATION.json')
        shutil.copy2(Path(pilot['source'])/TRAINER,Path(reg['source'])/TRAINER)
    if occupancy_origins:
        reg['payload_occupancy_origin']=occupancy_origins[0]
        pilot=read(Path(occupancy_origins[0]['root'])/'REGISTRATION.json')
        for key in (TRAINER,OCCUPANCY_HELPER):
            shutil.copy2(Path(pilot['source'])/key,Path(reg['source'])/key)
        if pilot.get('storage_predecessor'):
            # Preserve the exact optional trainer dependency in the new source
            # snapshot. Only the new stage is enrolled below; old runs stay intact.
            shutil.copy2(Path(pilot['source'])/STORAGE_HELPER,Path(reg['source'])/STORAGE_HELPER)
    for job in reg['jobs']:
        item = chosen[job['name']]
        old, cp = item['job'], item['checkpoint']
        job.update({key: old[key] for key in JOB_FIELDS})
        job.pop('tracking_guidance', None)
        if old.get('tracking_guidance') is not None:
            job['tracking_guidance'] = old['tracking_guidance']
        job.pop('payload_occupancy_guidance',None)
        if old.get('payload_occupancy_guidance') is not None:
            job['payload_occupancy_guidance']=old['payload_occupancy_guidance']
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
    if storage_parents:
        # Enroll only this new, still-unlaunched stage. Never reuse a parent's
        # seal or roundtrip preflight, which bind different outputs and hashes.
        assert all(reg['source_manifest'].get(key)==value for key,value in STORAGE_MIGRATION_HASHES.items())
        reg.update(working_set_policy=SCHEMA,storage_resources=dict(storage_parents[0]['storage_resources']))
    write(destination/'REGISTRATION.json', reg)
    if reg.get('working_set_policy'):
        from goal_prospective_storage_20261017 import seal
        seal(destination)
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
