"""Bounded auxiliary profiler of the unchanged published learner and replay.

Uses an immutable checkpoint in a separate process; auxiliary updates are
discarded. Profiles diagnose launch/sampling/synchronization costs, not online
speedups or convergence. Shared-load/profiler wall times are not benchmarks.
"""
import argparse
import cProfile
import hashlib
import json
import os
from pathlib import Path
import pstats
import sys
import time

import numpy as np
import torch


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(args):
    protocol = json.loads(args.registration.read_text())
    if sha(__file__) != protocol['source_sha256'] or sha(protocol['checkpoint']) != protocol['checkpoint_sha256']:
        raise ValueError('Registered source/checkpoint drift')
    if not Path(protocol['required_diagnostic_summary']).exists():
        raise ValueError('Previous finite diagnosis has not finished')
    os.sched_setaffinity(0, {protocol['cpu']})
    os.nice(protocol['nice'])
    torch.set_num_threads(1)
    root, out = Path(protocol['runtime']), Path(protocol['output'])
    if sha(root/'RUNTIME.json') != protocol['runtime_sha256']:
        raise ValueError('Runtime drift')
    sys.path.insert(0, str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    from train_published_compliance_20261025 import Replay
    checkpoint = torch.load(protocol['checkpoint'], map_location='cpu', weights_only=False)
    if checkpoint['boundary'] != 'complete_condition_cycle':
        raise ValueError('Expected complete-cycle archive')
    state, arrays = checkpoint['learner'], checkpoint['replay']['arrays']
    learner = PublishedLearner(root, dimension=arrays['actions'].shape[1],
        direct=checkpoint['controller'] == 'direct', seed=protocol['seed'], device=protocol['device'],
        algorithm=state['algorithm'], critic_layer_norm=state['critic_layer_norm'],
        numerical_amendments=state['numerical_amendments'])
    learner.load_state_dict(state)
    replay = Replay(arrays['actions'].shape[1], arrays['observations'].shape[1], protocol['seed'])
    replay.load_state_dict(checkpoint['replay'])
    out.mkdir(parents=True, exist_ok=False)
    start = time.time()
    def update():
        with torch.profiler.record_function('sii/replay_cpu_sample'):
            batch = replay.sample(protocol['batch_size'])
        with torch.profiler.record_function('sii/published_update_including_transfer_validation_metrics'):
            learner.update(batch)
    for _ in range(protocol['warmup_updates']):
        update()
    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(protocol['python_profile_updates']):
        update()
    profiler.disable()
    profiler.dump_stats(str(out/'python_profile.pstats'))
    with (out/'python_profile.txt').open('w') as stream:
        pstats.Stats(profiler, stream=stream).sort_stats('cumulative').print_stats(45)
    with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,
            torch.profiler.ProfilerActivity.CUDA], record_shapes=False, profile_memory=False) as prof:
        for _ in range(protocol['torch_profile_updates']):
            update()
            prof.step()
    prof.export_chrome_trace(str(out/'torch_trace.json'))
    events = prof.key_averages()
    (out/'torch_cpu.txt').write_text(events.table(sort_by='self_cpu_time_total', row_limit=35))
    (out/'torch_cuda.txt').write_text(events.table(sort_by='self_cuda_time_total', row_limit=35))
    rows = [dict(name=e.key, calls=e.count, self_cpu_us=e.self_cpu_time_total,
                 total_cpu_us=e.cpu_time_total, self_device_us=e.self_device_time_total,
                 total_device_us=e.device_time_total) for e in events]
    expected = sum(protocol[k] for k in ('warmup_updates', 'python_profile_updates', 'torch_profile_updates'))
    actual = learner.learner.num_gradient_steps-state['num_gradient_steps']
    if actual != expected:
        raise AssertionError('Auxiliary update count mismatch')
    (out/'SUMMARY.json').write_text(json.dumps(dict(controller=checkpoint['controller'],
        checkpoint_sha256=protocol['checkpoint_sha256'], registration_sha256=sha(args.registration),
        started_unix=start, elapsed_s=time.time()-start, auxiliary_updates=actual,
        formal_state_changed=False, auxiliary_weights_saved=False, new_physical_transitions=0,
        profiler_events=rows, limitations='Low-priority shared CPU/GPU; profiling adds overhead. '
        'No online speedup, convergence, or all-card utilization claim.'), indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    main(parser.parse_args())
