"""One reviewed finite SERL continuation with explicit append-only2m replay.

All old network/Adam/RNG/replay/history are retained. Actor canonical48,
official10 critics/random2 target/no entropy backup/8-to-1 are unchanged.
"""
import argparse
import copy
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate(checkpoint_digest, protocol, current_digest):
    from serl_multistep_state_adapter_20261026 import MARKER
    parent = protocol['resume_parent_registration']
    if sha(parent['path']) != parent['sha256'] or checkpoint_digest != parent['sha256']:
        raise ValueError('Exact current formal parent registration required')
    previous = json.loads(Path(parent['path']).read_text())
    allowed = {'resume_parent_registration','reviewed_continuation_stage','gather_stage','learner_batch_size','batch_size_stage','replay_capacity_stage'}
    if ({k:v for k,v in previous.items() if k not in allowed} !=
            {k:v for k,v in protocol.items() if k not in allowed}):
        raise ValueError('Protected SERL contract changed')
    validate_capacity(protocol, previous)
    stage = protocol['gather_stage']
    continuation = protocol['reviewed_continuation_stage']
    if (stage['marker'] != MARKER or stage['auxiliary_weights_imported'] is not False
            or continuation['parent_cycle'] < 13 or continuation['parent_cycle'] != previous['reviewed_continuation_stage']['parent_cycle'] + 1 or continuation['new_cycles'] != 1
            or protocol['stage_cycles'] != 1 or continuation['auxiliary_weights_imported'] is not False
            or stage['prepared_checkpoint'] != continuation['checkpoint']):
        raise ValueError('One registered multistep cycle from latest complete formal parent required')
    trial = protocol['batch_size_stage']
    if (previous['learner_batch_size'] != 65536 or protocol['learner_batch_size'] != 65536
            or trial != previous['batch_size_stage'] or trial['parent_cycle'] != 12
            or trial['batch_size'] != 65536 or trial['new_cycles'] != 1
            or trial['auxiliary_weights_imported'] is not False):
        raise ValueError('Expected unchanged inherited batch65536 stage')
    historical_entry = previous
    seen = set()
    while historical_entry['reviewed_continuation_stage']['parent_cycle'] != 12:
        ref = historical_entry['resume_parent_registration']
        if ref['path'] in seen or sha(ref['path']) != ref['sha256']:
            raise ValueError('Historical continuation registration cycle or hash drift')
        seen.add(ref['path'])
        earlier = json.loads(Path(ref['path']).read_text())
        if earlier['reviewed_continuation_stage']['parent_cycle'] != historical_entry['reviewed_continuation_stage']['parent_cycle'] - 1:
            raise ValueError('Noncontiguous formal continuation lineage')
        historical_entry = earlier
    if historical_entry['batch_size_stage'] != trial:
        raise ValueError('Historical batch trial changed')
    ref = historical_entry['resume_parent_registration']
    if sha(ref['path']) != ref['sha256']:raise ValueError('Original formal12 registration drift')
    original12 = json.loads(Path(ref['path']).read_text())
    for name in ['probe_review','independent_review']:
        ref = trial[name]
        if sha(ref['path']) != ref['sha256']:raise ValueError('Batch evidence drift')
    probe = json.loads(Path(trial['probe_review']['path']).read_text())
    independent = json.loads(Path(trial['independent_review']['path']).read_text())
    if (not probe['passed'] or not independent['passed'] or probe['weights_saved']
            or independent['report_sha256'] != trial['probe_review']['sha256']
            or probe['checkpoint'] != original12['reviewed_continuation_stage']['checkpoint']
            or trial['checkpoint'] != historical_entry['reviewed_continuation_stage']['checkpoint']):
        raise ValueError('Batch evidence must bind original11 probe and original12 migration parents')
    historical_ref = original12['resume_parent_registration']
    if sha(historical_ref['path']) != historical_ref['sha256']:
        raise ValueError('Historical transfer registration drift')
    historical = json.loads(Path(historical_ref['path']).read_text())
    for key in ['equivalence_review','update_gate']:
        ref=stage[key]
        if sha(ref['path']) != ref['sha256']:raise ValueError('Gather evidence drift')
    ref = stage['transfer_review']
    if sha(ref['path']) != ref['sha256']:
        raise ValueError('Transfer evidence drift')
    transfer = json.loads(Path(ref['path']).read_text())
    if (not transfer['passed'] or not transfer['batch_pytree_exact']
            or not transfer['full_next_update_state_metrics_exact'] or transfer['weights_saved']
            or transfer['checkpoint_sha256'] != historical['reviewed_continuation_stage']['checkpoint']['sha256']):
        raise ValueError('Transfer equivalence must bind to the original formal10 probe parent')
    for key in ['cycle_review','health_review']:
        ref=continuation[key]
        if sha(ref['path']) != ref['sha256']:raise ValueError('Current formal parent evidence drift')
    eq=json.loads(Path(stage['equivalence_review']['path']).read_text())
    gate=json.loads(Path(stage['update_gate']['path']).read_text())
    review=json.loads(Path(continuation['cycle_review']['path']).read_text())
    health=json.loads(Path(continuation['health_review']['path']).read_text())
    if (not eq['passed'] or not gate['passed'] or not gate['full_next_update_state_metrics_rng_exact']
            or not review['passed'] or not health['network_optimizer_rng_unchanged']
            or review['methods']['direct']['checkpoint_sha256'] != continuation['checkpoint']['sha256']
            or health['checkpoint_sha256'] != continuation['checkpoint']['sha256']):
        raise ValueError('Unverified exact parent or gather equivalence')



def validate_capacity(protocol, previous):
    from serl_replay_capacity_20261027 import MARKER
    stage = protocol['replay_capacity_stage']
    required = {'marker', 'parent_cycle', 'old_capacity', 'new_capacity',
                'entry_checkpoint', 'entry_replay_digest', 'helper_sha256',
                'replay_preparation_review', 'driver_preparation_review',
                'auxiliary_weights_imported'}
    if (set(stage) != required or stage['marker'] != MARKER
            or stage['parent_cycle'] != 23 or stage['old_capacity'] != 1_000_000
            or stage['new_capacity'] != 2_000_000 or stage['auxiliary_weights_imported'] is not False
            or stage['helper_sha256'] != sha(Path(__file__).with_name('serl_replay_capacity_20261027.py'))
            or len(stage['entry_replay_digest']) != 64):
        raise ValueError('Exact registered SERL capacity extension required')
    inherited = 'replay_capacity_stage' in previous
    if inherited:
        if stage != previous['replay_capacity_stage']:
            raise ValueError('Historical SERL capacity entry changed')
    elif (protocol['reviewed_continuation_stage']['parent_cycle'] != 23
            or stage['entry_checkpoint'] != protocol['reviewed_continuation_stage']['checkpoint']):
        raise ValueError('Capacity entry requires exact complete23 parent')
    for key in ['entry_checkpoint', 'replay_preparation_review', 'driver_preparation_review']:
        ref = stage[key]
        if sha(ref['path']) != ref['sha256']:
            raise ValueError('Capacity evidence drift: '+key)
    replay = json.loads(Path(stage['replay_preparation_review']['path']).read_text())
    driver = json.loads(Path(stage['driver_preparation_review']['path']).read_text())
    if (not replay['passed'] or replay['new_physics'] != 0 or replay['learner_updates'] != 0
            or replay['weights_saved'] or replay['formal_deployment']
            or not driver['passed'] or not driver['full_next_update_state_metrics_rng_exact']
            or not driver['expanded_restore_next_batch_exact'] or driver['weights_saved']
            or driver['new_physics'] != 0 or driver['outer_updates_per_arm'] != 1
            or driver['helper_sha256'] != stage['helper_sha256']
            or driver['driver_sha256'] != sha(__file__)
            or driver['replay_preparation_sha256'] != stage['replay_preparation_review']['sha256']):
        raise ValueError('Capacity preparation incomplete or changed')
    if not inherited and driver['checkpoint'] != previous['reviewed_continuation_stage']['checkpoint']:
        raise ValueError('Capacity driver preparation must cover complete22 predecessor')


def capacity_replay(base, protocol, checkpoint):
    from serl_multistep_state_adapter_20261026 import replay_class
    from serl_multistep_replay_gather_20261026 import optimized_class
    from serl_replay_capacity_20261027 import replay_class as expand, MARKER
    from validate_serl_state_20261026 import digest
    raw = checkpoint['replay']
    stage = protocol['replay_capacity_stage']
    entry = checkpoint['cycle'] == stage['parent_cycle']
    if raw['size'] != raw['cursor'] or raw['size'] != checkpoint['steps']:
        raise ValueError('Append-only complete replay required')
    if entry:
        if ('replay_capacity_extension' in raw or raw['capacity'] != 1_000_000
                or raw['size'] >= 1_000_000 or digest(raw) != stage['entry_replay_digest']):
            raise ValueError('Exact original complete23 replay required')
    elif raw.get('replay_capacity_extension') != MARKER or raw['capacity'] != 2_000_000:
        raise ValueError('Persisted2m replay marker required after migration')
    return expand(optimized_class(replay_class(base)), stage['entry_replay_digest'] if entry else None)


def check_replay_restore(raw_base, expanded_class, checkpoint, learner):
    from serl_multistep_state_adapter_20261026 import replay_class, SerlMultistepLearner
    from serl_multistep_replay_gather_20261026 import optimized_class
    from serl_replay_capacity_20261027 import MARKER
    from validate_serl_state_20261026 import digest
    raw = checkpoint['replay']
    entry = 'replay_capacity_extension' not in raw
    original_class = optimized_class(replay_class(raw_base)) if entry else expanded_class
    original = original_class(7, 49, 20261079)
    candidate = expanded_class(7, 49, 20261079)
    original.load_state_dict(raw)
    candidate.load_state_dict(raw)
    def normalized(value):
        if entry:
            value = dict(value)
            if value.pop('replay_capacity_extension') != MARKER:
                raise ValueError('Capacity marker changed')
            value['capacity'] = 1_000_000
        return value
    assert digest(normalized(candidate.state_dict())) == digest(original.state_dict()) == digest(raw)
    first, second = original.sample(65536), candidate.sample(65536)
    assert digest(first) == digest(second)
    assert digest(SerlMultistepLearner.batch(learner, first)) == digest(learner.batch(second))
    assert digest(original.rng.bit_generator.state) == digest(candidate.rng.bit_generator.state)
    saved = candidate.state_dict()
    restored = expanded_class(7, 49, 1)
    restored.load_state_dict(saved)
    assert digest(restored.state_dict()) == digest(saved)
    assert digest(restored.sample(65536)) == digest(candidate.sample(65536))
    assert digest(restored.rng.bit_generator.state) == digest(candidate.rng.bit_generator.state)
    assert digest(learner.state_dict()) == digest(checkpoint['learner'])
    return dict(full_replay_state_and_next_sample_exact=True,
                expanded_restore_next_batch_exact=True, capacity=2_000_000, entry_migration=entry)


def sampler_affinity(cpus, slot):
    if not 0 <= slot < 30 or cpus != list(range(13)):
        raise ValueError('Expected registered Direct slot and CPU allocation')
    return ','.join(str(cpu) for cpu in cpus[1:])


def validate_sampler_pool(protocol, args, cpus):
    expected = dict(kind='shared_physical_cpu_set', workers=30,
        learner_cpu=0, physical_cpus=list(range(1, 13)))
    if (protocol.get('sampler_pool') != expected or args.workers != 30
            or cpus != list(range(13)) or len(protocol['conditions']) != 30):
        raise ValueError('Expected exactly thirty samplers on the registered twelve physical CPUs')


def transform_main(source):
    guard = """    if len(set(cpus)) != len(cpus) or args.workers > len(cpus)-1:
        raise ValueError('Reserve one distinct learner CPU plus one per sampler')"""
    cpu = 'str(cpus[slot+1])'
    if source.count(guard) != 1 or source.count(cpu) != 1:
        raise ValueError('Frozen sampler scheduling seam changed')
    seam = 'replay.add(observations=previous'
    if source.count(seam) != 1:raise ValueError('Replay stream seam drift')
    old_batch_guard = 'if not 256 <= batch_size <= 32768 or not 1 <= utd <= 8:'
    if source.count(old_batch_guard) != 1:
        raise ValueError('Frozen batch guard seam changed')
    source = source.replace(old_batch_guard, 'if batch_size != 65536 or utd != 1:')
    return source.replace(guard, '    _validate_sampler_pool(protocol, args, cpus)').replace(
        cpu, 'str(_sampler_affinity(cpus, slot))').replace(seam, 'replay.add(stream=slot, observations=previous')


def validate_mapping_guards(protocol, args):
    mapping = [sampler_affinity(list(range(13)), i) for i in range(30)]
    assert len(mapping) == 30
    assert all(set(int(v) for v in mask.split(',')) == set(range(1, 13)) for mask in mapping)
    for workers in (0, 12, 31):
        bad = copy.copy(args); bad.workers = workers
        try:
            validate_sampler_pool(protocol, bad, list(range(13)))
        except ValueError:
            continue
        raise AssertionError('Unregistered worker count accepted')
    for cpus in (list(range(12)), [0]*13, list(range(13, 26))):
        try:
            validate_sampler_pool(protocol, args, cpus)
        except ValueError:
            continue
        raise AssertionError('Changed CPU allocation accepted')


def main(args):
    import torch
    protocol = json.loads(args.registration.read_text())
    stage = protocol['reviewed_continuation_stage']
    migration = protocol['gather_stage']
    if (str(args.resume.resolve()) != migration['prepared_checkpoint']['path']
            or sha(args.resume) != migration['prepared_checkpoint']['sha256']
            or sha(__file__) != stage['driver_sha256']):
        raise ValueError('Expected exact reviewed parent and registered driver')
    checkpoint = torch.load(args.resume, map_location='cpu', weights_only=False)
    validate(checkpoint['protocol_sha256'], protocol, sha(args.registration))
    if (checkpoint['cycle'] != stage['parent_cycle'] or checkpoint['boundary'] != 'complete_condition_cycle'
            or checkpoint['controller'] != 'direct' or checkpoint['seed'] != 20261026
            or checkpoint['learner']['algorithm'] != 'serl_state'):
        raise ValueError('Expected reviewed official SERL complete cycle')
    for name, expected in migration['source_hashes'].items():
        if sha(Path(__file__).with_name(name)) != expected:
            raise ValueError('Clock implementation drift: '+name)
    from serl_multistep_state_adapter_20261026 import MARKER
    if checkpoint['learner'].get('multistep_target_extension') != MARKER:
        raise ValueError('Missing persistent critic clock marker')
    adapter = Path(protocol['source_adapter'])
    for name, expected in protocol['source_adapter_hashes'].items():
        if sha(adapter/name) != expected:
            raise ValueError('Frozen SERL adapter source drift: ' + name)
    root = args.runtime.resolve()
    for name, expected in json.loads((root/'SOURCE_HASHES.json').read_text()).items():
        if sha(root/'source'/name) != expected:
            raise ValueError('Frozen physical source drift: ' + name)
    validate_sampler_pool(protocol, args, [int(v) for v in args.cpus.split(',')])
    sys.path.insert(0, str(root/'source/tools'))
    sys.path.insert(0, str(adapter))
    spec = importlib.util.spec_from_file_location('frozen_serl_pool_stage', adapter/'train_serl_state_20261026.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    base_main = inspect.getsource(module.main)
    candidate = transform_main(base_main)
    candidate_digest = hashlib.sha256(candidate.encode()).hexdigest()
    if candidate_digest != stage['patched_main_sha256']:
        raise ValueError('Patched scheduling source differs from registration')
    compile(candidate, '<registered_sii_serl_shared_sampler_affinity>', 'exec')
    expanded_class = capacity_replay(module.Replay, protocol, checkpoint)
    if args.check_only:
        from serl_multistep_state_adapter_20261026 import SerlMultistepLearner, replay_class
        from validate_serl_state_20261026 import digest
        from serl_multistep_batch_transfer_20261026 import transfer_class
        learner = transfer_class(SerlMultistepLearner)(root, upstream=args.serl_upstream,
            upstream_manifest=args.serl_manifest, dimension=7, direct=True,
            seed=20261026, device=args.device)
        learner.load_state_dict(checkpoint['learner'])
        if digest(learner.state_dict()) != digest(checkpoint['learner']):
            raise ValueError('Fresh loader did not preserve the full prepared state')
        for name, value in [('learner_updates_per_transition', 2), ('critic_clock', False), ('learner_batch_size', 2048), ('stage_cycles', 99)]:
            bad = copy.deepcopy(protocol); bad[name] = value
            try:
                validate(checkpoint['protocol_sha256'], bad, sha(args.registration))
            except ValueError:
                continue
            raise AssertionError('Changed contract unexpectedly accepted')
        replay_checks = check_replay_restore(module.Replay, expanded_class, checkpoint, learner)
        for key, value in [('new_capacity', 1_000_000), ('parent_cycle', 22), ('entry_replay_digest', 'bad')]:
            bad = copy.deepcopy(protocol); bad['replay_capacity_stage'][key] = value
            try:
                validate(checkpoint['protocol_sha256'], bad, sha(args.registration))
            except ValueError:
                continue
            raise AssertionError('Altered capacity contract accepted')
        validate_mapping_guards(protocol, args)
        print(json.dumps(dict(passed=True, checkpoint_sha256=sha(args.resume),
            full_prepared_state_unchanged=True, **replay_checks,
            candidate_main_sha256=candidate_digest,
            slot_cpu_sets=[sampler_affinity(list(range(13)), i) for i in range(30)])))
        return
    del checkpoint
    args.controller, args.algorithm, args.seed = 'direct', 'serl_state', 20261026
    args.cycles = stage['new_cycles']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    receipt = args.output.parent/'SAMPLER_STAGE_EXECUTION.json'
    with receipt.open('x') as f:
        json.dump(dict(time=time.time(), driver_sha256=sha(__file__),
            parent_checkpoint=stage['checkpoint'], prepared_checkpoint=migration['prepared_checkpoint'],
            multistep_stage=migration, protocol_sha256=sha(args.registration),
            batch_change=dict(previous=65536,current=65536), critic_actor_ratio=8, new_cycles=args.cycles,
            auxiliary_weights_imported=False, sampler_pool=protocol['sampler_pool'],
            replay_capacity_stage=protocol['replay_capacity_stage']), f, indent=2)
    from serl_multistep_state_adapter_20261026 import SerlMultistepLearner, replay_class
    from serl_multistep_batch_transfer_20261026 import transfer_class
    module.PublishedLearner = transfer_class(SerlMultistepLearner)
    from serl_multistep_replay_gather_20261026 import optimized_class
    module.Replay = expanded_class
    module.validate_resume_protocol = validate
    namespace = module.__dict__
    namespace['_validate_sampler_pool'] = validate_sampler_pool
    namespace['_sampler_affinity'] = sampler_affinity
    exec(compile(candidate, '<registered_sii_serl_shared_sampler_affinity>', 'exec'), namespace)
    with (args.output.parent/'SAMPLER_MAIN.py.txt').open('x') as f:
        f.write(candidate)
    with (args.output.parent/'SAMPLER_PATCH.json').open('x') as f:
        json.dump(dict(base_trainer_sha256=sha(adapter/'train_serl_state_20261026.py'),
            base_main_sha256=hashlib.sha256(base_main.encode()).hexdigest(),
            candidate_main_sha256=hashlib.sha256(candidate.encode()).hexdigest(),
            changes=['sampler-count guard', 'shared physical CPU-set affinity', 'explicit replay stream id', 'registered batch65536 guard'],
            learner_source_changed=True, physics_source_changed=False,
            multistep_stage=migration), f, indent=2)
    module.main(args)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['runtime', 'registration', 'resume', 'output', 'serl-upstream', 'serl-manifest', 'sampler-python']:
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--device', default='cuda:0')
    p.add_argument('--cpus', required=True)
    p.add_argument('--workers', type=int, default=30)
    p.add_argument('--check-only', action='store_true')
    main(p.parse_args())
