"""Review preserved py-spy raw data with explicit all/empty/framed denominators.

This reads existing evidence only. No process attachment, simulation or updates.
Raw format without thread IDs cannot identify the main thread unambiguously.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


CATEGORIES = {
    'finite_check': ['assert_finite_parameters ('],
    'replay_sampling': ['sample (', 'published_replay_device_cache'],
    'backward': ['backward ('],
    'adam_step': ['adam.py:'],
    'selector_wait': ['selectors.py:'],
    'checkpoint': ['checkpoint_now ('],
    'learner_update': ['update (', 'published_compliance_learner'],
    'policy_action': ['act (', 'published_compliance_learner'],
    'target_update': ['update_target_networks ('],
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def summarize(raw):
    total = empty = 0
    leaves, inclusive = Counter(), Counter()
    for line in raw.splitlines():
        stack, count = line.rsplit(' ', 1)
        count = int(count)
        if count <= 0:
            raise ValueError('Sample counts must be positive')
        total += count
        if not stack:
            empty += count
            continue
        frames = stack.split(';')
        if any(not frame.strip() for frame in frames):
            raise ValueError('Unexpected empty frame inside nonempty stack')
        leaves[frames[-1]] += count
        for category, needles in CATEGORIES.items():
            if all(needle in stack for needle in needles):
                inclusive[category] += count
    if not total:
        raise ValueError('No samples')
    framed = total - empty

    def row(count):
        return dict(samples=count, fraction_all=count/total,
                    fraction_framed=count/framed if framed else None)

    return dict(total_samples=total, empty_stack_samples=empty,
                framed_samples=framed, empty_fraction_all=empty/total,
                inclusive={key: row(inclusive[key]) for key in CATEGORIES},
                top_framed_leaves=[dict(frame=key, **row(count))
                                   for key, count in leaves.most_common(20)])


def review(directory, registration):
    original = json.loads((directory/'SUMMARY.json').read_text())
    if sha(registration) != original['registration_sha256']:
        raise ValueError('Registration hash mismatch')
    protocol = json.loads(registration.read_text())
    if set(original['methods']) != set(protocol['targets']):
        raise ValueError('Target set mismatch')
    methods = {}
    for method, old in original['methods'].items():
        raw = directory/(method+'.folded')
        if sha(raw) != old['raw_sha256']:
            raise ValueError('Raw profile hash mismatch: '+method)
        value = summarize(raw.read_text())
        if value['total_samples'] != old['total_samples']:
            raise ValueError('Original sample total mismatch')
        for key, fraction in old['inclusive_fractions'].items():
            if value['inclusive'][key]['fraction_all'] != fraction:
                raise ValueError('Original inclusive count mismatch: '+key)
        if not old['target_identity_verified']:
            raise ValueError('Missing target identity verification')
        methods[method] = dict(**value, raw_sha256=old['raw_sha256'],
            before=old['before'], after=old['after'],
            observed_new_steps=old['observed_new_steps'],
            observed_new_updates=old['observed_new_updates'],
            progress_timestamp_delta_s=(old['after']['wall_time_utc']
                                       - old['before']['wall_time_utc']))
    return dict(methods=methods, registration_sha256=sha(registration),
        original_summary_sha256=sha(directory/'SUMMARY.json'),
        review_source_sha256=sha(__file__),
        sampling_requested_s=protocol['duration_s'], rate_hz=protocol['rate_hz'],
        diagnostic_optimizer_updates=0, new_physics_processes=0,
        original_evidence_modified=False, training_configuration_changed=False,
        interpretation=[
            'Empty stacks are counted separately; they do not establish CPU or GPU idleness.',
            'Framed fractions use nonempty Python-stack samples, not identified main-thread wall time.',
            'Inclusive categories overlap; do not add their fractions.',
            'Stack presence is not CUDA kernel timing or a measured optimization speedup.',
            'Progress timestamp intervals differ from the requested sampling duration; do not divide step deltas by 60.',
            'Shared workload and sampling overhead limit extrapolation to unsampled online throughput.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = review(args.directory, args.registration)
    with args.output.open('x') as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False)+'\n')
