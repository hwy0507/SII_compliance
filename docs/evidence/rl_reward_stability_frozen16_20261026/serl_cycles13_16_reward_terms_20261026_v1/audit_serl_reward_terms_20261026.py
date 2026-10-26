"""Attribute the complete13-to16 reward difference using audited saved terms."""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import os
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(root):
    os.sched_setaffinity(0, {52})
    import numpy as np
    reg = json.loads((root/'REGISTRATION.json').read_text())
    assert reg['cycles'] == [13, 16] and sha(__file__) == reg['source_sha256']
    for refs in reg['inputs'].values():
        for ref in refs.values():
            assert sha(ref['path']) == ref['sha256']
    components = ['progress', 'occupancy', 'time', 'comfort_torque', 'contact_force',
                  'torque_slew', 'penetration', 'peak_torque', 'terminal', 'failure_tail',
                  'completion_efficiency']
    results = []
    for cycle in reg['cycles']:
        refs = reg['inputs'][str(cycle)]
        episodes = [json.loads(v) for v in Path(refs['episodes']['path']).read_text().splitlines()]
        report = json.loads(Path(refs['review']['path']).read_text())
        assert report['passed'] and report['methods']['direct']['max_reward_reconstruction_error'] == 0
        by_id = {e['condition']: e for e in episodes}
        assert len(episodes) == len(by_id) == 30
        sums = {k: {name: 0. for name in components} for k in by_id}
        counts, rewards = collections.Counter(), collections.defaultdict(float)
        with Path(refs['transitions']['path']).open() as stream:
            for line in stream:
                t = json.loads(line)
                assert t['cycle'] == cycle and t['condition'] in by_id
                terms = t['reward_terms']
                assert abs(sum(terms[k] for k in components)-t['reward']) < 1e-10
                counts[t['condition']] += 1
                rewards[t['condition']] += t['reward']
                for k in components:
                    sums[t['condition']][k] += terms[k]
        assert sum(counts.values()) == 41250
        for case, e in by_id.items():
            assert counts[case] == e['steps'] == 1375
            assert abs(rewards[case]-e['reward']) < 1e-8
        means = {k: float(np.mean([v[k] for v in sums.values()])) for k in components}
        results.append(dict(cycle=cycle, mean_terms=means, per_condition=sums,
            final_stage_counts=dict(collections.Counter(e['final_task_stage'] for e in episodes))))
    delta = {k: results[1]['mean_terms'][k]-results[0]['mean_terms'][k] for k in components}
    report = dict(passed=True, time=time.time(), cycles=results, mean_term_deltas=delta,
        sum_of_mean_term_deltas=sum(delta.values()), new_physics=0, optimizer_updates=0,
        convergence_claim=False, limitation='Read-only attribution of saved reward terms from previously physically reconstructed complete-cycle reviews. It separates reward improvement components from task progression; it neither changes reward nor independently reruns dynamics.')
    for refs in reg['inputs'].values():
        for ref in refs.values():
            assert sha(ref['path']) == ref['sha256']
    (root/'REVIEW.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.root)
    except BaseException as error:
        (args.root/'FAILURE.json').write_text(json.dumps(dict(error=repr(error), time=time.time()))+'\n')
        raise
