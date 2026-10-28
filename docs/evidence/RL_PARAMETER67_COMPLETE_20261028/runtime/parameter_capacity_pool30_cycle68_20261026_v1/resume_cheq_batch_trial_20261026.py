"""Explicit one-cycle batch-size trial with otherwise exact CHEQ continuation.

The frozen trainer is loaded unchanged. Its protocol gate is replaced only by
the narrow validator below, with a hashed driver receipt. No actor, optimizer,
RNG, replay, physics, objective or UTD changes are made by this wrapper.
"""
import argparse
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
        raise ValueError('Exact parent registration required')
    previous = json.loads(Path(parent['path']).read_text())
    allowed = {'resume_parent_registration', 'workload_trial', 'learner_batch_size'}
    if ({k: v for k, v in previous.items() if k not in allowed} !=
            {k: v for k, v in protocol.items() if k not in allowed}):
        raise ValueError('Batch trial changed protected contract')
    trial = protocol['workload_trial']
    if (previous['learner_batch_size'] != 256 or protocol['learner_batch_size'] != 32768 or
            protocol['learner_updates_per_transition'] != 1 or trial['cycles'] != 1 or
            trial['parent_cycle'] != 4 or trial['weight_promotion_from_probe'] is not False):
        raise ValueError('Unexpected batch trial or budget')
    for evidence in ['cycle_review', 'throughput_registration']:
        row = trial[evidence]
        if sha(row['path']) != row['sha256']:
            raise ValueError('Trial evidence drift')


def main(args):
    import torch
    protocol = json.loads(args.registration.read_text())
    trial = protocol['workload_trial']
    expected = trial['checkpoints'][args.controller]
    if sha(args.resume) != expected['sha256'] or str(args.resume.resolve()) != expected['path']:
        raise ValueError('Exact reviewed checkpoint required')
    checkpoint = torch.load(args.resume, map_location='cpu', weights_only=False)
    validate(checkpoint['protocol_sha256'], protocol, sha(args.registration))
    if (checkpoint['cycle'] != 4 or checkpoint['boundary'] != 'complete_condition_cycle' or
            checkpoint['controller'] != args.controller or checkpoint['seed'] != 20261025 or
            checkpoint['learner']['algorithm'] != 'cheq'):
        raise ValueError('Only reviewed complete parameter CHEQ boundary supported')
    if sha(__file__) != trial['driver_sha256']:
        raise ValueError('Driver drift')
    root = args.runtime.resolve()
    trainer = root/'source/tools/train_published_compliance_20261025.py'
    source = json.loads((root/'SOURCE_HASHES.json').read_text())
    for name, digest in source.items():
        if sha(root/'source'/name) != digest:
            raise ValueError('Frozen source drift: '+name)
    if args.check_only:
        # A reward or UTD change must not pass this batch-only gate.
        import copy
        for key, value in [('learner_updates_per_transition', 2), ('critic_clock', False)]:
            bad = copy.deepcopy(protocol); bad[key] = value
            try:
                validate(checkpoint['protocol_sha256'], bad, sha(args.registration))
            except ValueError:
                continue
            raise AssertionError('Rejected-contract check unexpectedly passed')
        print(json.dumps(dict(controller=args.controller, passed=True,
                             checkpoint_sha256=sha(args.resume))))
        return
    del checkpoint
    args.algorithm, args.seed, args.cycles = 'cheq', 20261025, 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    receipt = args.output.parent/'BATCH_TRIAL_EXECUTION.json'
    if receipt.exists():
        raise FileExistsError(receipt)
    receipt.write_text(json.dumps(dict(time=time.time(), driver_sha256=sha(__file__),
        frozen_trainer_sha256=sha(trainer), protocol_sha256=sha(args.registration),
        parent_checkpoint=expected, changed_batch=[256, 32768], utd=1, cycles=1,
        method=args.controller, no_auxiliary_weights=True), indent=2)+'\n')
    sys.path.insert(0, str(root/'source/tools'))
    spec = importlib.util.spec_from_file_location('frozen_cheq_batch_trial', trainer)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.validate_resume_protocol = validate
    module.main(args)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['runtime', 'registration', 'resume', 'output']:
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--controller', choices=['impedance', 'admittance', 'vmc'], required=True)
    p.add_argument('--cpus', required=True)
    p.add_argument('--workers', type=int, default=12)
    p.add_argument('--device', required=True)
    p.add_argument('--check-only', action='store_true')
    main(p.parse_args())
