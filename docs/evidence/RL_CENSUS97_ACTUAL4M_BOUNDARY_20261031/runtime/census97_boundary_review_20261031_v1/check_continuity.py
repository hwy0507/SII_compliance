"""Read-only closure of next-context evidence on the original boundary snapshots."""
from pathlib import Path
import os, json, hashlib, time, traceback, gc

D = Path(__file__).resolve().parent
B = D.parents[1]
BOUND = B / 'runs/census97_capacity_boundary_20261031_v1'
RUN = B / 'runs/parameter_census_cycle97_20261031_v1'

def read(p):
    return json.loads(p.read_text())

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def put(p, obj):
    with p.open('x') as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write('\n')

def compare_links(arrays, transitions):
    import numpy as np
    by = {}
    for t in transitions:
        by.setdefault(t['condition'], []).append(t)
    links = []
    for rows in by.values():
        for current, following in zip(rows, rows[1:]):
            if current['done']:
                raise ValueError('Unexpected same-condition restart within finite97')
            links.append((current['step'] - 1, following['step'] - 1))
    index = np.asarray(links, dtype=np.int64)
    np.testing.assert_array_equal(arrays['next_observations'][index[:, 0]],
                                  arrays['observations'][index[:, 1]])
    return dict(links)

def main():
    os.sched_setaffinity(0, {11})
    import numpy as np
    import torch
    torch.set_num_threads(1)
    plan = read(D / 'PLAN.json')
    assert sha(Path(__file__)) == plan['source_sha256']
    original = read(BOUND / 'REVIEW.json')
    assert original['passed']
    for p, expected in plan['source_bindings'].items():
        assert sha(Path(p)) == expected
    # Targeted checks: this supplement must detect the missing next-context
    # column and must also reject a changed non-context feature.
    synthetic = dict(observations=np.zeros((2, 52), np.float32),
                     next_observations=np.zeros((2, 52), np.float32))
    records = [dict(step=1, condition='a', done=False),
               dict(step=2, condition='a', done=False)]
    compare_links(synthetic, records)
    rejected = []
    for col in (48, 0):
        synthetic['next_observations'][0, col] = 1
        try:
            compare_links(synthetic, records)
        except AssertionError:
            rejected.append(col)
        else:
            raise AssertionError('Corrupt next-state column accepted')
        synthetic['next_observations'][0, col] = 0
    assert rejected == [48, 0]
    methods = {}
    for method, entry in original['methods'].items():
        snap = Path(entry['snapshot']['path'])
        before = sha(snap)
        assert before == entry['snapshot']['sha256']
        ck = torch.load(snap, map_location='cpu', weights_only=False, mmap=True)
        n = ck['steps']
        assert n == entry['steps'] and n > 4000000
        transitions, raw = [], []
        with (RUN / method / 'train/transitions.jsonl').open('rb') as f:
            for line in f:
                t = json.loads(line)
                if t['step'] > n:
                    break
                transitions.append(t)
                raw.append(line)
        assert hashlib.sha256(b''.join(raw)).hexdigest() == entry['new_journal_prefix_sha256']
        assert [t['step'] for t in transitions] == list(range(entry['parent_steps'] + 1, n + 1))
        arrays = ck['replay']['arrays']
        links = compare_links(arrays, transitions)
        contexts = {t['step'] - 1: t['context'] for t in transitions}
        indices = np.asarray(list(contexts), dtype=np.int64)
        np.testing.assert_array_equal(arrays['observations'][indices, 48],
                                      np.asarray(list(contexts.values()), np.float32))
        boundary_rows = []
        for i in range(3999998, 4000003):
            j = links[i]
            np.testing.assert_array_equal(arrays['next_observations'][i, 48], np.float32(contexts[j]))
            boundary_rows.append(dict(replay_index=i, following_same_condition_index=j,
                                      current_context=float(arrays['observations'][i, 48]),
                                      next_context=float(arrays['next_observations'][i, 48]),
                                      next_transition_context=contexts[j]))
        assert sha(snap) == before
        methods[method] = dict(steps=n, snapshot_sha256=before,
                              new_rows=len(transitions), exact_all52_links=len(links),
                              tail_rows_without_following_in_snapshot=len(transitions)-len(links),
                              all_new_current_contexts_exact=True, boundary_rows=boundary_rows)
        del ck, arrays, transitions, raw
        gc.collect()
    put(D / 'CONTINUITY_REVIEW.json', dict(passed=True, time=time.time(), methods=methods,
        rejected_columns=rejected, physics_steps=0, optimizer_updates=0,
        original_boundary_review_sha256=sha(BOUND / 'REVIEW.json'),
        scope='Full52 next-state equality to following same-condition current state on every available new link; all current contexts match original transitions. Five boundary next-context values explicitly checked. Snapshot tails without a following transition excluded. Original full-prefix/actor-journal checks remain prerequisite; no convergence claim.'))
    print(json.dumps(methods), flush=True)

if __name__ == '__main__':
    try:
        main()
    except BaseException:
        put(D / ('FAILURE_' + str(time.time_ns()) + '.json'), dict(time=time.time(), traceback=traceback.format_exc()))
        raise
