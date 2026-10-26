"""Describe complete-cycle reward changes using saved terms and outcome switches."""
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
    reg = json.loads((root/'REGISTRATION.json').read_text())
    assert reg['cycles'] == [27, 28, 29]
    assert sha(__file__) == reg['source_sha256']
    components = ['progress', 'occupancy', 'time', 'comfort_torque', 'contact_force',
                  'torque_slew', 'penetration', 'peak_torque', 'terminal',
                  'failure_tail', 'completion_efficiency']
    refs = reg['inputs']
    for ref in refs.values():
        assert sha(ref['path']) == ref['sha256']

    def read(key):
        return json.loads(Path(refs[key]['path']).read_text())

    methods = {}
    for method in ['impedance', 'admittance', 'vmc']:
        cycles = []
        for cycle in reg['cycles']:
            key = f'{method}:{cycle}'
            review = read(f'{key}:review')
            assert review['passed'] and read(f'{key}:finished')['completed']
            assert review['methods'][method]['max_reward_reconstruction_error'] == 0
            episodes = [json.loads(line) for line in
                        Path(refs[f'{key}:episodes']['path']).read_text().splitlines()]
            by_id = {e['condition']: e for e in episodes}
            assert len(episodes) == len(by_id) == 30
            sums = {case: dict.fromkeys(components, 0.) for case in by_id}
            rewards = collections.defaultdict(float)
            counts = collections.Counter()
            with Path(refs[f'{key}:transitions']['path']).open() as stream:
                for line in stream:
                    row = json.loads(line)
                    assert row['cycle'] == cycle and row['condition'] in by_id
                    terms = row['reward_terms']
                    assert abs(sum(terms[name] for name in components)-row['reward']) < 1e-10
                    case = row['condition']
                    counts[case] += 1
                    rewards[case] += row['reward']
                    for name in components:
                        sums[case][name] += terms[name]
            assert sum(counts.values()) == 41250
            rows = {}
            for case, episode in by_id.items():
                assert counts[case] == episode['steps'] == 1375
                assert abs(rewards[case]-episode['reward']) < 1e-8
                terminal = read(f'{key}:{case}:terminal')
                rollout = read(f'{key}:{case}:rollout')
                assert terminal['model_sha256'] == rollout['model_sha256'] == episode['model_sha256']
                for name in ['task_success', 'strict_success', 'abort_reason', 'full_task_horizon_completed']:
                    assert episode[name] == terminal['result'][name] == rollout[name]
                rows[case] = dict(reward=episode['reward'], terms=sums[case],
                    task=episode['task_success'], strict=episode['strict_success'],
                    final_stage=episode['final_task_stage'],
                    saved_external_penetration_mm=rollout['stats']['max_external_penetration_m']*1000,
                    saved_worst_external_pair=rollout['stats']['worst_external_pair'])
            mean = sum(e['reward'] for e in episodes)/30
            assert abs(mean-review['methods'][method]['reward_mean']) < 1e-10
            cycles.append(dict(cycle=cycle, mean_reward=mean, conditions=rows))
        comparisons = []
        for before, after in zip(cycles, cycles[1:]):
            rows = []
            for case in sorted(before['conditions']):
                old, new = before['conditions'][case], after['conditions'][case]
                delta = new['reward']-old['reward']
                terms = {name: new['terms'][name]-old['terms'][name] for name in components}
                assert abs(sum(terms.values())-delta) < 1e-8
                rows.append(dict(condition=case, reward_delta=delta, contribution_to_mean=delta/30,
                    task_switch=old['task'] != new['task'], strict_switch=old['strict'] != new['strict'],
                    task_before=old['task'], task_after=new['task'],
                    strict_before=old['strict'], strict_after=new['strict'],
                    saved_penetration_mm_before=old['saved_external_penetration_mm'],
                    saved_penetration_mm_after=new['saved_external_penetration_mm'], term_deltas=terms))
            delta = after['mean_reward']-before['mean_reward']
            assert abs(sum(row['contribution_to_mean'] for row in rows)-delta) < 1e-10
            switched = [row for row in rows if row['task_switch'] or row['strict_switch']]
            contribution = sum(row['contribution_to_mean'] for row in switched)
            comparisons.append(dict(before=before['cycle'], after=after['cycle'], mean_delta=delta,
                switched_conditions=[row['condition'] for row in switched],
                switched_contribution=contribution, unchanged_outcome_contribution=delta-contribution,
                switched_share_of_net_delta=contribution/delta if abs(delta) > 1e-10 else None,
                mean_term_deltas={name: sum(row['term_deltas'][name] for row in rows)/30 for name in components},
                conditions=sorted(rows, key=lambda row: abs(row['reward_delta']), reverse=True)))
        methods[method] = dict(cycles=cycles, comparisons=comparisons)
    for ref in refs.values():
        assert sha(ref['path']) == ref['sha256']
    report = dict(passed=True, time=time.time(), methods=methods, new_physics=0,
        optimizer_updates=0, neural_forward_passes=0, saved_transitions_verified=371250,
        convergence_claim=False,
        limitation='Exploratory fixed27-29 attribution after full results were visible. All30 conditions retained. Saved term sums and episode labels are verified against complete prior audits; saved rollout penetration is a descriptive reported peak, not independently recomputed raw substeps. Outcome-switch contributions are arithmetic, not proof that a single transition caused loss or that stochastic action noise caused the switch. No reward/gate changes or automatic training decisions.')
    (root/'REVIEW.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print({m: [{k: c[k] for k in ['before', 'after', 'mean_delta', 'switched_conditions',
          'switched_contribution', 'unchanged_outcome_contribution']} for c in v['comparisons']]
          for m, v in methods.items()}, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.root)
    except BaseException as error:
        (args.root/'FAILURE.json').write_text(json.dumps(dict(error=repr(error), time=time.time()))+'\n')
        raise
