"""One complete online cycle testing terminal-weighted CHEQ critic regression.

Starts from reviewed formal cycle9, retaining every learner/Adam/replay/RNG
state. Auxiliary probe weights are never loaded. Only critic loss weighting
changes; sampling, batch, actor objective, targets and physical execution stay.
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
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def validate(checkpoint_digest, protocol, current_digest):
    parent = protocol['resume_parent_registration']
    if sha(parent['path']) != parent['sha256'] or checkpoint_digest != parent['sha256']:
        raise ValueError('Exact parent registration required')
    previous = json.loads(Path(parent['path']).read_text())
    allowed = {'resume_parent_registration', 'completed_stage_continuation', 'terminal_weight_stage'}
    if ({k:v for k,v in previous.items() if k not in allowed} !=
            {k:v for k,v in protocol.items() if k not in allowed}):
        raise ValueError('Protected contract changed')
    trial = protocol['terminal_weight_stage']
    stage = protocol['completed_stage_continuation']
    if (trial['parent_cycle'] != 9 or trial['new_cycles'] != 1 or trial['weight'] != 128
            or trial['auxiliary_weights_imported'] is not False or stage['new_cycles'] != 1
            or stage['parent_cycle'] != 9 or stage['actor_learning_rate_factor'] is not None
            or protocol['learner_batch_size'] != 32768 or protocol['learner_updates_per_transition'] != 1
            or stage.get('bellman_target_count') is not None):
        raise ValueError('Expected one cycle, weight128 and original workload/actor/targets')
    for name in ('cycle_review', 'health_review', 'probe_review'):
        ref = trial[name]
        if sha(ref['path']) != ref['sha256']:
            raise ValueError('Scientific evidence drift: '+name)
    method = trial['controller']
    cycle = json.loads(Path(trial['cycle_review']['path']).read_text())
    health = json.loads(Path(trial['health_review']['path']).read_text())
    probe = json.loads(Path(trial['probe_review']['path']).read_text())
    if (not cycle['passed'] or not probe['passed'] or any(
            d['methods'][method]['checkpoint_sha256'] != trial['checkpoint']['sha256']
            for d in (cycle, health, probe))):
        raise ValueError('Evidence does not cover this exact checkpoint')


def main(args):
    import torch
    p = json.loads(args.registration.read_text())
    trial = p['terminal_weight_stage']
    if (str(args.resume.resolve()) != trial['checkpoint']['path']
            or sha(args.resume) != trial['checkpoint']['sha256']
            or args.controller != trial['controller'] or sha(__file__) != trial['driver_sha256']):
        raise ValueError('Exact reviewed formal checkpoint and driver required')
    helper = Path(__file__).with_name('published_terminal_loss_weight_20261026.py')
    if sha(helper) != trial['helper_sha256']:
        raise ValueError('Weighting implementation drift')
    if sha(Path(__file__).with_name('validate_published_finite_check_20261025.py')) != trial['verification_helper_sha256']:
        raise ValueError('Verification helper drift')
    ck = torch.load(args.resume, map_location='cpu', weights_only=False)
    validate(ck['protocol_sha256'], p, sha(args.registration))
    if (ck['cycle'] != 9 or ck['boundary'] != 'complete_condition_cycle'
            or ck['controller'] != args.controller or ck['seed'] != 20261025
            or ck['learner']['algorithm'] != 'cheq'
            or ck['learner'].get('terminal_loss_weight', 1) != 1):
        raise ValueError('Expected unweighted formal CHEQ cycle9')
    root = args.runtime.resolve()
    for name, expected in json.loads((root/'SOURCE_HASHES.json').read_text()).items():
        if sha(root/'source'/name) != expected:
            raise ValueError('Frozen source drift: '+name)
    cpus = [int(v) for v in args.cpus.split(',')]
    first = {'impedance':13, 'admittance':26, 'vmc':39}[args.controller]
    if args.workers != 12 or cpus != list(range(first, first+13)):
        raise ValueError('Original twelve samplers and CPU allocation required')
    sys.path.insert(0, str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    from published_terminal_loss_weight_20261026 import weighted_class
    from validate_published_finite_check_20261025 import digest
    if args.check_only:
        # No optimization. Ensure the new objective wrapper restores all state.
        torch.set_num_threads(1)
        cls = weighted_class(PublishedLearner, 128)
        learner = cls(root, dimension=ck['replay']['arrays']['actions'].shape[1], direct=False,
            seed=20261025, device='cpu', algorithm='cheq', critic_layer_norm=True,
            numerical_amendments=True, critic_clock=True)
        learner.load_state_dict(ck['learner'])
        restored = learner.state_dict()
        assert restored.pop('terminal_loss_weight') == 128
        # CPU construction cannot preserve a CUDA execution context; restore
        # retains the saved CUDA RNG explicitly when CUDA is available.
        assert digest(restored) == digest(ck['learner'])
        for key, value in [('learner_batch_size',256), ('learner_updates_per_transition',2), ('critic_clock',False)]:
            bad = copy.deepcopy(p); bad[key] = value
            try: validate(ck['protocol_sha256'], bad, sha(args.registration))
            except ValueError: pass
            else: raise AssertionError('Protected contract change accepted')
        for key, value in [('weight',1), ('new_cycles',2), ('auxiliary_weights_imported',True)]:
            bad = copy.deepcopy(p); bad['terminal_weight_stage'][key] = value
            try: validate(ck['protocol_sha256'], bad, sha(args.registration))
            except ValueError: pass
            else: raise AssertionError('Unregistered intervention accepted')
        print(json.dumps(dict(passed=True, controller=args.controller, full_state_unchanged=True,
            checkpoint_sha256=sha(args.resume), patch=learner.terminal_weight_receipt)))
        return
    del ck
    args.algorithm, args.seed, args.cycles = 'cheq', 20261025, 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with (args.output.parent/'TERMINAL_STAGE_EXECUTION.json').open('x') as f:
        json.dump(dict(time=time.time(), driver_sha256=sha(__file__), helper_sha256=sha(helper),
            parent_checkpoint=trial['checkpoint'], weight=128, new_cycles=1,
            auxiliary_weights_imported=False), f, indent=2)
    trainer = root/'source/tools/train_published_compliance_20261025.py'
    spec = importlib.util.spec_from_file_location('frozen_terminal_stage', trainer)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.PublishedLearner = weighted_class(PublishedLearner, 128)
    module.validate_resume_protocol = validate
    module.main(args)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('runtime', 'registration', 'resume', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--controller', choices=['impedance','admittance','vmc'], required=True)
    p.add_argument('--cpus', required=True)
    p.add_argument('--workers', type=int, default=12)
    p.add_argument('--device', required=True)
    p.add_argument('--check-only', action='store_true')
    main(p.parse_args())
