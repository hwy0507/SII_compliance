"""Independent array arithmetic for the fixed complete67 ranking at complete68."""
from pathlib import Path
import hashlib
import json
import math
import os
import time

os.sched_setaffinity(0, {53})
import numpy as np

OUT = Path(__file__).parent


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def near(actual, expected):
    assert math.isfinite(actual) and math.isfinite(expected)
    assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), (actual, expected)


def main():
    assert read(OUT / 'FINISHED.json')['completed'], 'Incomplete ranked68 followup'
    report = read(OUT / 'REVIEW.json')
    plan = read(OUT / 'PLAN.json')
    root = Path(plan['parent_followup'])
    assert report['passed'] and report['plan_sha256'] == sha(OUT / 'PLAN.json')
    assert sha(root / 'PLAN.json') == plan['parent_plan_sha256']
    assert sha(root / 'LAUNCH.json') == plan['parent_launch_sha256']
    assert read(root / 'FINISHED.json')['completed']
    assert read(root / 'SAVED_VALUES_REVIEW.json')['passed']
    assert report['original68_review_sha256'] == sha(root / 'REVIEW.json')
    assert report['values68_sha256'] == sha(root / 'values.npz')
    for name, digest in plan['sources'].items():
        assert sha(OUT / name) == digest
    for item in plan['inputs'].values():
        assert sha(item['path']) == item['sha256']
    ranking = read(plan['inputs']['ranked67']['path'])['all2034_ranked']
    rows = report['all2034_original_ranked_followup']
    assert len(rows) == len(ranking) == 2034
    assert [r['original67_rank'] for r in rows] == list(range(1, 2035))
    assert [r['replay_index'] for r in rows] == [r['replay_index'] for r in ranking]
    assert len({r['replay_index'] for r in rows}) == 2034
    with np.load(plan['inputs']['values67']['path'], allow_pickle=False) as a, np.load(root / 'values.npz', allow_pickle=False) as b:
        assert len(a['indices']) == 2034 and len(b['indices']) == 2064
        for key in ['indices', 'rewards']:
            np.testing.assert_array_equal(a[key], b[key][:2034])
        np.testing.assert_array_equal(a['masks'], b['masks'][:, :2034])
        np.testing.assert_array_equal(a['q_after'], b['q_before'])
        np.testing.assert_array_equal(a['denominator'], b['old_denominator'])
        masks = a['masks'].astype(np.float64)
        rewards = a['rewards'].astype(np.float64)[None, :]
        old = masks * np.square(a['q_after'].astype(np.float64) - rewards)
        new = masks * np.square(b['q_after'][:, :2034].astype(np.float64) - rewards)
        expected = {
            'sse67': old.sum(axis=0),
            'sse68': new.sum(axis=0),
            'contribution67': (128 * old / a['denominator'][:, None]).sum(axis=0),
            'contribution68': (128 * new / b['denominator'][:, None]).sum(axis=0),
            'contribution68_using67_denominator': (128 * new / a['denominator'][:, None]).sum(axis=0),
        }
        expected['sse_change'] = expected['sse68'] - expected['sse67']
        positions = {int(index): i for i, index in enumerate(a['indices'])}
        for row in rows:
            i = positions[row['replay_index']]
            for key, values in expected.items():
                near(row[key], float(values[i]))
        for key, values in expected.items():
            near(report['totals'][key], math.fsum(map(float, values)))
        assert report['improve'] == int(np.sum(expected['sse_change'] < 0))
        assert report['worsen'] == int(np.sum(expected['sse_change'] > 0))
    focus = [row for row in rows if row['replay_index'] in plan['fixed67_top2_indices']]
    assert focus == report['original67_top2']
    assert [r['replay_index'] for r in focus] == plan['fixed67_top2_indices']
    full = read(root / 'REVIEW.json')
    for key, full_key in [
        ('sse67', 'old2034_sse_before'), ('sse68', 'old2034_sse_after'),
        ('contribution67', 'old2034_contribution_before'),
        ('contribution68', 'old2034_contribution_after'),
        ('contribution68_using67_denominator', 'old2034_after_using_old_denominator'),
    ]:
        near(report['totals'][key], full[full_key])
    result = dict(
        passed=True, time=time.time(), all2034_independent_vector_arithmetic=True,
        fixed67_ranking_and_top2_preserved=True, original_arrays_exact=True,
        full2034_totals_reproduced=True, review_sha256=sha(OUT / 'REVIEW.json'),
        reviewer_sha256=sha(Path(__file__)), new_physics=0, new_forward=0,
        optimizer_updates=0, replay_writes=0, convergence_claim=False,
    )
    with (OUT / 'SAVED_REVIEW.json').open('x') as target:
        target.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
