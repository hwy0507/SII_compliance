"""Read saved complete-cycle Task/Strict/physical labels; no simulation or training."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import time

BASE = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
METHODS = ('impedance', 'admittance', 'vmc')


def read(path):
    return json.loads(path.read_text())


def ref(path):
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'path': str(path), 'sha256': digest}


def run_path(cycle):
    assert cycle in (80,81), 'Only completed recovery80/81; interrupted75 excluded'
    return BASE / f'runs/parameter_partial75_recovery_cycle{cycle}_20261029_v1'


def review_path(cycle):
    assert cycle in (80,81), 'Only completed recovery80/81; interrupted75 excluded'
    return BASE / f'runs/parameter_partial75_recovery_cycle{cycle}_review_20261029_v1'


def audit(before, after, output):
    assert (before, after) == (80, 81), 'Consecutive complete recovery80/81 only'
    assert not output.exists(), 'Refuse to overwrite prior evidence'
    inputs = []
    maps = {}
    for cycle in (before, after):
        run = run_path(cycle)
        review = review_path(cycle)
        for path, key in ((run / 'ARCHIVE_REVIEW_FINISHED.json', 'completed'),
                          (review / 'FINISHED.json', 'completed'),
                          (review / 'REVIEW.json', 'passed')):
            assert path.exists() and read(path)[key], f'Incomplete cycle {cycle}: {path}'
            inputs.append(ref(path))
        for method in METHODS:
            path = run / method / 'train/episodes.jsonl'
            episodes = [json.loads(line) for line in path.read_text().splitlines()]
            mapped = {episode['condition']: episode for episode in episodes}
            assert len(episodes) == len(mapped) == 30
            assert all(e['cycle'] == cycle and math.isfinite(e['reward']) for e in episodes)
            maps[cycle, method] = mapped
            inputs.append(ref(path))
    methods = {}
    for method in METHODS:
        old, new = maps[before, method], maps[after, method]
        assert set(old) == set(new)
        pairs = []
        for condition in sorted(old):
            cases = []
            for cycle, episode in ((before, old[condition]), (after, new[condition])):
                folder = Path(episode['episode_path'])
                expected = run_path(cycle) / method / 'train' / f'cycle_{cycle:05d}' / condition
                assert folder == expected
                rollout_path = folder / 'rollout.json'
                evaluator_path = folder / 'executed_evaluator.py.txt'
                rollout = read(rollout_path)
                assert "physical_valid=abort_reason is None and stats['max_external_penetration_m']<=.0002" in evaluator_path.read_text()
                penetration = rollout['stats']['max_external_penetration_m']
                assert math.isfinite(penetration)
                physical = rollout['abort_reason'] is None and penetration <= .0002
                assert physical == rollout['physical_valid'] == episode['physical_valid']
                assert rollout['task_success'] == episode['task_success']
                assert bool(rollout['task_success'] and physical) == rollout['strict_success'] == episode['strict_success']
                assert rollout['abort_reason'] == episode['abort_reason']
                model = ref(folder / 'rollout.mjb')
                assert model['sha256'] == rollout['model_sha256'] == episode['model_sha256']
                cases.append(dict(cycle=cycle, task=episode['task_success'], strict=episode['strict_success'],
                                  physical_valid=physical, abort_reason=episode['abort_reason'],
                                  penetration_mm=1000 * penetration, reward=episode['reward'],
                                  model=model, evaluator=ref(evaluator_path), rollout=ref(rollout_path)))
            assert cases[0]['model']['sha256'] == cases[1]['model']['sha256']
            assert cases[0]['evaluator']['sha256'] == cases[1]['evaluator']['sha256']
            changed = [key for key in ('task', 'strict', 'physical_valid', 'abort_reason') if cases[0][key] != cases[1][key]]
            pairs.append(dict(condition=condition, changed_fields=changed, cases=cases))
        methods[method] = dict(all30=pairs, changes=[p for p in pairs if p['changed_fields']],
                               task_only_changes=[p for p in pairs if 'task' in p['changed_fields'] and 'strict' not in p['changed_fields']],
                               counts={str(cycle): {key: sum(p['cases'][i][key] for p in pairs) for key in ('task', 'strict', 'physical_valid')} for i, cycle in enumerate((before, after))})
    for item in inputs:
        assert ref(Path(item['path'])) == item
    for method in methods.values():
        for pair in method['all30']:
            for case in pair['cases']:
                for key in ('model', 'evaluator', 'rollout'):
                    assert ref(Path(case[key]['path'])) == case[key]
    report = dict(passed=True, time=time.time(), cycles=[before, after], methods=methods, inputs=inputs,
                  source=ref(Path(__file__)), saved_rollouts_checked=181, new_physics=0, optimizer_updates=0,
                  gate_unchanged=True, convergence_claim=False,
                  limitation='Complete recovery80 to complete recovery81; original75 remains interrupted. All 90 paired conditions and 181 saved rollout labels checked, including Task-only changes. Saved physical statistics and executed gate are checked; no independent substep recomputation or task trajectory replay, no new gate or causal claim.')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({m: {'counts': v['counts'], 'changes': [(p['condition'], p['changed_fields']) for p in v['changes']]} for m, v in methods.items()}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--before', type=int, required=True)
    parser.add_argument('--after', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit(args.before, args.after, args.output)
