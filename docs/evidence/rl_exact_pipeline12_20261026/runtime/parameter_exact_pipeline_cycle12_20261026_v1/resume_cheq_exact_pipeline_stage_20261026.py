"""One finite cycle with exactly equivalent replay and target-update batching.

Retain the projected terminal-weight128 objective and complete formal cycle11
state. Probe weights are never imported; online throughput must be measured.
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
    allowed = {'resume_parent_registration', 'completed_stage_continuation', 'terminal_weight_stage', 'target_projection_stage', 'exact_pipeline_stage'}
    if ({k:v for k,v in previous.items() if k not in allowed} !=
            {k:v for k,v in protocol.items() if k not in allowed}):
        raise ValueError('Protected contract changed')
    if previous['terminal_weight_stage'] != protocol['terminal_weight_stage']:
        raise ValueError('Inherited terminal stage metadata changed')
    if previous['target_projection_stage'] != protocol['target_projection_stage']:
        raise ValueError('Inherited projection metadata changed')
    trial = protocol['exact_pipeline_stage']
    stage = protocol['completed_stage_continuation']
    if (trial['parent_cycle'] != 11 or trial['new_cycles'] != 1 or trial['projection'] is not True or trial['weight'] != 128
            or trial['auxiliary_weights_imported'] is not False or stage['new_cycles'] != 1
            or stage['parent_cycle'] != 11 or stage['actor_learning_rate_factor'] is not None
            or protocol['learner_batch_size'] != 32768 or protocol['learner_updates_per_transition'] != 1
            or stage.get('bellman_target_count') is not None):
        raise ValueError('Expected one cycle, weight128 and original workload/actor/targets')
    for name in ('cycle_review', 'health_review', 'probe_review', 'startup_review'):
        ref = trial[name]
        if sha(ref['path']) != ref['sha256']:
            raise ValueError('Scientific evidence drift: '+name)
    method = trial['controller']
    cycle = json.loads(Path(trial['cycle_review']['path']).read_text())
    health = json.loads(Path(trial['health_review']['path']).read_text())
    probe = json.loads(Path(trial['probe_review']['path']).read_text())
    if (not cycle['passed'] or not probe['passed'] or any(
            d['methods'][method]['checkpoint_sha256'] != trial['checkpoint']['sha256']
            for d in (cycle, health))):
        raise ValueError('Evidence does not cover this exact checkpoint')
    startup = json.loads(Path(trial['startup_review']['path']).read_text())
    if (not startup['passed'] or probe['methods'][method]['checkpoint_sha256'] != startup['methods'][method]['checkpoint_sha256']
            or startup['methods'][method]['parent_sha256'] != cycle['methods'][method]['source_parent_sha256']
            or not probe['methods'][method]['full_state_identical']):
        raise ValueError('Equivalence probe and formal cycle must share the audited parent')


def main(args):
    import torch
    p = json.loads(args.registration.read_text())
    trial = p['exact_pipeline_stage']
    if (str(args.resume.resolve()) != trial['checkpoint']['path']
            or sha(args.resume) != trial['checkpoint']['sha256']
            or args.controller != trial['controller'] or sha(__file__) != trial['driver_sha256']):
        raise ValueError('Exact reviewed formal checkpoint and driver required')
    helper = Path(__file__).with_name('published_exact_projected_learner_20261026.py')
    if sha(helper) != trial['helper_sha256']:
        raise ValueError('Weighting implementation drift')
    if sha(Path(__file__).with_name('validate_published_finite_check_20261025.py')) != trial['verification_helper_sha256']:
        raise ValueError('Verification helper drift')
    for name, expected in trial['dependency_hashes'].items():
        if sha(Path(__file__).with_name(name)) != expected:
            raise ValueError('Projection dependency drift: '+name)
    ck = torch.load(args.resume, map_location='cpu', weights_only=False)
    validate(ck['protocol_sha256'], p, sha(args.registration))
    if (ck['cycle'] != 11 or ck['boundary'] != 'complete_condition_cycle'
            or ck['controller'] != args.controller or ck['seed'] != 20261025
            or ck['learner']['algorithm'] != 'cheq'
            or ck['learner'].get('terminal_loss_weight') != 128 or ck['learner'].get('finite_target_projection') != dict(version=1,terminal_cap=30.,gamma=.9995,maximum_actions=1375,position='target critic Q before stochastic entropy term',upper_only=True)):
        raise ValueError('Expected projected weighted formal CHEQ cycle11')
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
    from published_projected_terminal_learner_20261026 import MARKER
    from published_exact_pipeline_20261026 import cache_class
    from published_exact_projected_learner_20261026 import exact_class
    from validate_published_finite_check_20261025 import digest
    if args.check_only:
        # No optimization. Ensure the new objective wrapper restores all state.
        torch.set_num_threads(1)
        cls = exact_class(PublishedLearner)
        learner = cls(root, dimension=ck['replay']['arrays']['actions'].shape[1], direct=False,
            seed=20261025, device='cpu', algorithm='cheq', critic_layer_norm=True,
            numerical_amendments=True, critic_clock=True)
        learner.load_state_dict(ck['learner'])
        restored = learner.state_dict()
        assert restored['finite_target_projection'] == MARKER
        # CPU construction cannot preserve a CUDA execution context; restore
        # retains the saved CUDA RNG explicitly when CUDA is available.
        assert digest(restored) == digest(ck['learner'])
        for key, value in [('learner_batch_size',256), ('learner_updates_per_transition',2), ('critic_clock',False)]:
            bad = copy.deepcopy(p); bad[key] = value
            try: validate(ck['protocol_sha256'], bad, sha(args.registration))
            except ValueError: pass
            else: raise AssertionError('Protected contract change accepted')
        for key, value in [('weight',1), ('projection',False), ('new_cycles',2), ('auxiliary_weights_imported',True)]:
            bad = copy.deepcopy(p); bad['exact_pipeline_stage'][key] = value
            try: validate(ck['protocol_sha256'], bad, sha(args.registration))
            except ValueError: pass
            else: raise AssertionError('Unregistered intervention accepted')
        print(json.dumps(dict(passed=True, controller=args.controller, full_state_unchanged=True,
            checkpoint_sha256=sha(args.resume), patch=learner.pipeline_receipt)))
        return
    del ck
    args.algorithm, args.seed, args.cycles = 'cheq', 20261025, 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with (args.output.parent/'EXACT_PIPELINE_STAGE_EXECUTION.json').open('x') as f:
        json.dump(dict(time=time.time(), driver_sha256=sha(__file__), helper_sha256=sha(helper),
            parent_checkpoint=trial['checkpoint'], weight=128, projection=True, new_cycles=1,
            auxiliary_weights_imported=False), f, indent=2)
    trainer = root/'source/tools/train_published_compliance_20261025.py'
    spec = importlib.util.spec_from_file_location('frozen_exact_pipeline_stage', trainer)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    import published_replay_device_cache_20261025 as cache_module
    cache_module.DeviceReplayCache = cache_class(cache_module.DeviceReplayCache)
    module.PublishedLearner = exact_class(PublishedLearner)
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
