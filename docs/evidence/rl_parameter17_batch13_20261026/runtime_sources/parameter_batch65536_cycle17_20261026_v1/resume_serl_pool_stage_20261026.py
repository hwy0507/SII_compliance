"""Finite official SERL continuation with thirty samplers sharing twelve CPUs.

Only sampler concurrency and CPU scheduling change. The official learner,
physical interpreter, complete checkpoint, batch and update ratio stay fixed.
More concurrent episodes change data arrival order; this is not a claim of
bitwise-equivalent training or established learning/performance improvement.
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
    parent = protocol['resume_parent_registration']
    if sha(parent['path']) != parent['sha256'] or checkpoint_digest != parent['sha256']:
        raise ValueError('Exact SERL parent registration required')
    previous = json.loads(Path(parent['path']).read_text())
    allowed = {'resume_parent_registration', 'reviewed_continuation_stage', 'stage_cycles', 'sampler_pool'}
    if ({k: v for k, v in previous.items() if k not in allowed} !=
            {k: v for k, v in protocol.items() if k not in allowed}):
        raise ValueError('Continuation changed a protected contract field')
    stage = protocol['reviewed_continuation_stage']
    if (previous['learner_batch_size'] != 32768 or protocol['learner_batch_size'] != 32768
            or protocol['learner_updates_per_transition'] != 1
            or protocol['critic_updates_per_outer_step'] != 8
            or protocol['actor_updates_per_outer_step'] != 1
            or stage['parent_cycle'] < 4 or stage['new_cycles'] not in (1, 2) or protocol['stage_cycles'] != stage['new_cycles']
            or stage['auxiliary_weights_imported'] is not False):
        raise ValueError('Unsupported official SERL continuation or budget')
    for name in ['cycle_review', 'health_review']:
        evidence = stage[name]
        if sha(evidence['path']) != evidence['sha256']:
            raise ValueError('Scientific review drift: ' + name)
    cycle = json.loads(Path(stage['cycle_review']['path']).read_text())
    health = json.loads(Path(stage['health_review']['path']).read_text())
    expected = stage['checkpoint']['sha256']
    if (not cycle['passed']
            or cycle['methods']['direct']['checkpoint_sha256'] != expected
            or health['checkpoint_sha256'] != expected
            or not health['network_optimizer_rng_unchanged']):
        raise ValueError('Reviews do not validate this exact parent checkpoint')



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
    if (str(args.resume.resolve()) != stage['checkpoint']['path']
            or sha(args.resume) != stage['checkpoint']['sha256']
            or sha(__file__) != stage['driver_sha256']):
        raise ValueError('Expected exact reviewed parent and registered driver')
    checkpoint = torch.load(args.resume, map_location='cpu', weights_only=False)
    validate(checkpoint['protocol_sha256'], protocol, sha(args.registration))
    if (checkpoint['cycle'] != stage['parent_cycle'] or checkpoint['boundary'] != 'complete_condition_cycle'
            or checkpoint['controller'] != 'direct' or checkpoint['seed'] != 20261026
            or checkpoint['learner']['algorithm'] != 'serl_state'):
        raise ValueError('Expected reviewed official SERL complete cycle')
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
        for name, value in [('learner_updates_per_transition', 2), ('critic_clock', True), ('learner_batch_size', 2048), ('stage_cycles', 99)]:
            bad = copy.deepcopy(protocol); bad[name] = value
            try:
                validate(checkpoint['protocol_sha256'], bad, sha(args.registration))
            except ValueError:
                continue
            raise AssertionError('Changed contract unexpectedly accepted')
        validate_mapping_guards(protocol, args)
        print(json.dumps(dict(passed=True, checkpoint_sha256=sha(args.resume),
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
            parent_checkpoint=stage['checkpoint'], protocol_sha256=sha(args.registration),
            batch_change=None, critic_actor_ratio=8, new_cycles=args.cycles,
            auxiliary_weights_imported=False, sampler_pool=protocol['sampler_pool']), f, indent=2)
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
            learner_source_changed=False, physics_source_changed=False), f, indent=2)
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
