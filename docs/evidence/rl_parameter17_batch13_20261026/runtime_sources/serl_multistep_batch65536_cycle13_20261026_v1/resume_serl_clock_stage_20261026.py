"""One formal SERL cycle with validated critic-clock state/replay migration.

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
    from resume_serl_pool_stage_20261026 import validate as validate_parent
    from serl_clock_state_adapter_20261026 import MARKER
    stage = protocol['critic_clock_stage']
    if protocol.get('critic_clock') is not True or stage['marker'] != MARKER:
        raise ValueError('Explicit critic-only clock contract required')
    if protocol['stage_cycles'] != 1 or stage['auxiliary_weights_imported'] is not False:
        raise ValueError('Only one registered clock cycle and no auxiliary weights')
    for key in ('preparation_review', 'probe_review'):
        ref = stage[key]
        if sha(ref['path']) != ref['sha256']:
            raise ValueError('Clock scientific evidence drift')
    prep = json.loads(Path(stage['preparation_review']['path']).read_text())
    probe = json.loads(Path(stage['probe_review']['path']).read_text())
    if (not prep['passed'] or not probe['passed']
            or prep['checkpoint_sha256'] != protocol['reviewed_continuation_stage']['checkpoint']['sha256']
            or prep['prepared_checkpoint_sha256'] != stage['prepared_checkpoint']['sha256']
            or not prep['original_full_learner_recovered_exactly']
            or not prep['old_replay_recovered_exactly']):
        raise ValueError('Clock migration not validated against formal parent')
    # Delegate all unchanged official learner, physical and sampler contracts.
    legacy = copy.deepcopy(protocol)
    legacy.pop('critic_clock_stage')
    legacy['critic_clock'] = False
    validate_parent(checkpoint_digest, legacy, current_digest)



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
    return source.replace(guard, '    _validate_sampler_pool(protocol, args, cpus)').replace(
        cpu, 'str(_sampler_affinity(cpus, slot))')


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
    migration = protocol['critic_clock_stage']
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
    from serl_clock_state_adapter_20261026 import MARKER
    if checkpoint['learner'].get('critic_clock_extension') != MARKER:
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
    if args.check_only:
        from serl_clock_state_adapter_20261026 import SerlClockLearner
        from validate_serl_state_20261026 import digest
        learner = SerlClockLearner(root, upstream=args.serl_upstream,
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
        validate_mapping_guards(protocol, args)
        print(json.dumps(dict(passed=True, checkpoint_sha256=sha(args.resume),
            full_prepared_state_unchanged=True,
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
            critic_clock_stage=migration, protocol_sha256=sha(args.registration),
            batch_change=None, critic_actor_ratio=8, new_cycles=args.cycles,
            auxiliary_weights_imported=False, sampler_pool=protocol['sampler_pool']), f, indent=2)
    from serl_clock_state_adapter_20261026 import SerlClockLearner
    module.PublishedLearner = SerlClockLearner
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
            changes=['sampler-count guard', 'shared physical CPU-set affinity'],
            learner_source_changed=True, physics_source_changed=False,
            critic_clock_stage=migration), f, indent=2)
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
