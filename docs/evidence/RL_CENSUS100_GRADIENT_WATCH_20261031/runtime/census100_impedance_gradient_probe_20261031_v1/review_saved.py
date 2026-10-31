from pathlib import Path
import hashlib, json, math, time, os
import numpy as np

D = Path(__file__).resolve().parent
B = D.parents[1]
O = B / 'runs/census100_impedance_gradient_probe_20261031_v1'
read = lambda p: json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

os.sched_setaffinity(0, {10})
plan = read(D / 'PLAN.json')
report = read(O / 'REVIEW.json')
assert report['passed'] and read(O / 'FINISHED.json')['passed']
assert read(O / 'FINISHED.json')['elapsed_s'] <= plan['budget_seconds']
assert sha(D / 'probe.py') == plan['source_sha256'] == report['source']['sha256']
for item in plan['inputs']:
    assert sha(item['path']) == item['sha256']
assert report['critic_index'] == 4 and report['critic_index_base'] == 0
assert report['physics_steps'] == report['optimizer_updates'] == 0
assert report['weight_promotion'] is False
groups = ['old92', 'new99', 'other_mask1_terminals']
summary = {}
with np.load(plan['values']['path']) as base:
    rows = {int(index): i for i, index in enumerate(base['indices'])}
    chosen = [rows[i] for i in plan['replay_indices']]
    expected = {'old92': [chosen[0]], 'new99': [chosen[1]],
                'other_mask1_terminals': [i for i, mask in enumerate(base['masks'][:, 4]) if mask == 1 and i not in chosen]}
    assert [int(base['cycles'][i]) for i in chosen] == [92, 99]
    assert len(expected['other_mask1_terminals']) == 2385
    for label, method in report['methods'].items():
        assert method == read(O / (label + '_REVIEW.json'))
        assert method['checkpoint'] == plan['snapshots'][label]
        assert method['learner_adam_replay_rng_unchanged'] and method['parameter_grad_buffers_absent']
        assert sha(method['values']['path']) == method['values']['sha256']
        prediction_key = 'initial_prediction' if label == 'complete99' else 'prefix_prediction'
        scalar = {}
        with np.load(method['values']['path']) as values:
            for group in groups:
                selection = expected[group]
                np.testing.assert_array_equal(values[group + '_replay_indices'], base['indices'][selection])
                assert np.all(base['masks'][selection, 4] == 1)
                pred = values[group + '_prediction']
                assert len(pred) == method['groups'][group]['rows'] == len(selection)
                np.testing.assert_allclose(pred, base[prediction_key][selection, 4], rtol=1e-5, atol=1e-5)
                mse = math.fsum((float(q) - float(r)) ** 2 for q, r in zip(pred, base['rewards'][selection])) / len(selection)
                assert math.isclose(mse, method['groups'][group]['mse'], rel_tol=2e-6, abs_tol=1e-8)
                vec = values[group]
                assert vec.shape == (method['gradient_dimension'],) == (81921,) and np.isfinite(vec).all()
                scalar[group] = dict(rows=len(selection), mse_recomputed_float64=mse)
            for pair, data in method['pairs'].items():
                left, right = pair.split('__')
                x, y = values[left], values[right]
                dot = math.fsum(float(a) * float(b) for a, b in zip(x, y))
                nx = math.sqrt(math.fsum(float(a) ** 2 for a in x))
                ny = math.sqrt(math.fsum(float(b) ** 2 for b in y))
                for key, value in [('dot', dot), ('left_norm', nx), ('right_norm', ny), ('cosine', dot / (nx * ny))]:
                    assert math.isclose(data[key], value, rel_tol=1e-12, abs_tol=1e-10)
                assert data['local_steepest_descent_conflict'] == (dot < 0)
        summary[label] = scalar
result = dict(passed=True, time=time.time(), all_saved_vectors_and_scalar_arithmetic_verified=True,
              exact_group_membership_and_original_masks=True, groups=summary,
              source_sha256=sha(__file__), probe_source_sha256=sha(D / 'probe.py'),
              interpretation='All six local cosine values are positive. These two saved states show no first-order conflict among the three terminal SSE objectives for critic4. No sampled-batch, nonterminal TD, Adam or online-causality claim. This review verifies saved arithmetic, not a second autograd execution.')
with (O / 'SAVED_REVIEW.json').open('x') as f:
    json.dump(result, f, indent=2, allow_nan=False)
    f.write('\n')
print(json.dumps(result, indent=2))
