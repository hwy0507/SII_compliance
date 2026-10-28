"""Resume pinned official SERL with one reviewed batch-only online trial.

All network, optimizer, replay and RNG state is restored by the frozen trainer.
Only the registered batch size changes; critic:actor ratio and objective stay
fixed. A larger batch changes gradient statistics and is not an equivalent
performance optimization. No auxiliary weights may be used.
"""
import argparse
import copy
import hashlib
import importlib.util
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
    allowed = {'resume_parent_registration', 'learner_batch_size', 'reviewed_batch_stage', 'stage_cycles'}
    if ({k: v for k, v in previous.items() if k not in allowed} !=
            {k: v for k, v in protocol.items() if k not in allowed}):
        raise ValueError('Batch-only continuation changed a protected contract field')
    stage = protocol['reviewed_batch_stage']
    if (previous['learner_batch_size'] != 2048 or protocol['learner_batch_size'] != 32768
            or protocol['learner_updates_per_transition'] != 1
            or protocol['critic_updates_per_outer_step'] != 8
            or protocol['actor_updates_per_outer_step'] != 1
            or stage['parent_cycle'] != 1 or stage['new_cycles'] != 1 or protocol['stage_cycles'] != 1
            or stage['auxiliary_weights_imported'] is not False):
        raise ValueError('Unsupported official SERL batch trial or budget')
    for name in ['cycle_review', 'throughput_review']:
        evidence = stage[name]
        if sha(evidence['path']) != evidence['sha256']:
            raise ValueError('Scientific review drift: ' + name)


def main(args):
    import torch
    protocol = json.loads(args.registration.read_text())
    stage = protocol['reviewed_batch_stage']
    if (str(args.resume.resolve()) != stage['checkpoint']['path']
            or sha(args.resume) != stage['checkpoint']['sha256']
            or sha(__file__) != stage['driver_sha256']):
        raise ValueError('Expected exact reviewed parent and registered driver')
    checkpoint = torch.load(args.resume, map_location='cpu', weights_only=False)
    validate(checkpoint['protocol_sha256'], protocol, sha(args.registration))
    if (checkpoint['cycle'] != 1 or checkpoint['boundary'] != 'complete_condition_cycle'
            or checkpoint['controller'] != 'direct' or checkpoint['seed'] != 20261026
            or checkpoint['learner']['algorithm'] != 'serl_state'):
        raise ValueError('Expected official SERL complete cycle1')
    adapter = Path(protocol['source_adapter'])
    for name, expected in protocol['source_adapter_hashes'].items():
        if sha(adapter/name) != expected:
            raise ValueError('Frozen SERL adapter source drift: ' + name)
    root = args.runtime.resolve()
    for name, expected in json.loads((root/'SOURCE_HASHES.json').read_text()).items():
        if sha(root/'source'/name) != expected:
            raise ValueError('Frozen physical source drift: ' + name)
    if args.check_only:
        for name, value in [('learner_updates_per_transition', 2), ('critic_clock', True)]:
            bad = copy.deepcopy(protocol); bad[name] = value
            try:
                validate(checkpoint['protocol_sha256'], bad, sha(args.registration))
            except ValueError:
                continue
            raise AssertionError('Changed contract unexpectedly accepted')
        print(json.dumps(dict(passed=True, checkpoint_sha256=sha(args.resume))))
        return
    del checkpoint
    args.controller, args.algorithm, args.seed = 'direct', 'serl_state', 20261026
    args.cycles = 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    receipt = args.output.parent/'BATCH_STAGE_EXECUTION.json'
    with receipt.open('x') as f:
        json.dump(dict(time=time.time(), driver_sha256=sha(__file__),
            parent_checkpoint=stage['checkpoint'], protocol_sha256=sha(args.registration),
            batch_change=[2048, 32768], critic_actor_ratio=8, new_cycles=1,
            auxiliary_weights_imported=False), f, indent=2)
    sys.path.insert(0, str(root/'source/tools'))
    sys.path.insert(0, str(adapter))
    spec = importlib.util.spec_from_file_location('frozen_serl_batch_stage', adapter/'train_serl_state_20261026.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.validate_resume_protocol = validate
    module.main(args)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['runtime', 'registration', 'resume', 'output', 'serl-upstream', 'serl-manifest', 'sampler-python']:
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--device', default='cuda:0')
    p.add_argument('--cpus', required=True)
    p.add_argument('--workers', type=int, default=12)
    p.add_argument('--check-only', action='store_true')
    main(p.parse_args())
