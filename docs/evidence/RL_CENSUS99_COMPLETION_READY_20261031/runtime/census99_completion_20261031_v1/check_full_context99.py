"""Close the next-context evidence gap over every new complete99 transition."""
from pathlib import Path
import os, sys, json, hashlib, time, gc

D = Path(__file__).resolve().parent
B = D.parents[1]
R = B / 'runs/parameter_census_cycle99_20261031_v1'
V = B / 'runs/parameter_census_cycle99_review_20261031_v1'
HELPER = B / 'runtime/census97_boundary_review_20261031_v1'
read = lambda p: json.loads(p.read_text())

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def main():
    import numpy as np
    import torch
    os.sched_setaffinity(0, {11})
    torch.set_num_threads(1)
    plan = read(D / 'CONTEXT_PLAN.json')
    assert sha(Path(__file__)) == plan['source_sha256']
    assert sha(HELPER / 'check_continuity.py') == plan['helper_sha256']
    assert read(HELPER / 'CONTINUITY_REVIEW.json')['passed']
    assert read(V / 'FINISHED.json')['completed']
    full = read(V / 'REVIEW.json')
    assert full['passed']
    sys.path.insert(0, str(HELPER))
    from check_continuity import compare_links
    methods = {}
    for m, record in full['methods'].items():
        cp = B / 'runs/parameter_census_cycle99_archive_20261031_v1' / m / 'cycle_00099.pt'
        assert sha(cp) == record['checkpoint_sha256']
        ck = torch.load(cp, map_location='cpu', weights_only=False, mmap=True)
        assert ck['boundary'] == 'complete_condition_cycle' and ck['cycle'] == 99
        arrays = ck['replay']['arrays']
        source = R / m / 'train/transitions.jsonl'
        ts = [json.loads(line) for line in source.read_text().splitlines()]
        parent = read(R / m / 'REGISTRATION.json')['post_interruption_continuation']['parent_steps']
        assert len(ts) == record['new_transitions'] == ck['steps']-parent
        assert [t['step'] for t in ts] == list(range(parent+1, ck['steps']+1))
        assert all(t['cycle'] == 99 for t in ts)
        links = compare_links(arrays, ts)
        idx = np.asarray([t['step']-1 for t in ts], np.int64)
        contexts = np.asarray([t['context'] for t in ts], np.float32)
        np.testing.assert_array_equal(arrays['observations'][idx, 48], contexts)
        terminals = [t for t in ts if t['done']]
        assert len(terminals) == len({t['condition'] for t in terminals}) == 30
        ti = np.asarray([t['step']-1 for t in terminals], np.int64)
        np.testing.assert_array_equal(arrays['next_observations'][ti, 48], arrays['observations'][ti, 48])
        assert set(links) | set(ti.tolist()) == set(idx.tolist())
        assert not set(links) & set(ti.tolist())
        assert sha(cp) == record['checkpoint_sha256']
        methods[m] = dict(new_rows=len(ts), all52_nonterminal_links=len(links), terminal_rows=len(terminals),
            every_new_row_covered=True, all_current_contexts_match_journal=True,
            all_terminal_next_contexts_match_registered_terminal_rule=True,
            checkpoint_sha256=record['checkpoint_sha256'], transitions_sha256=sha(source))
        del ck, arrays, ts
        gc.collect()
        print(m, methods[m], flush=True)
    with (D / 'FULL_CONTEXT_REVIEW.json').open('x') as f:
        json.dump(dict(passed=True, time=time.time(), methods=methods, physics_steps=0, optimizer_updates=0,
            scope='All new99 rows: full52 next-state equality to following same-condition current state for nonterminals; all current contexts match original log, all terminal next contexts match original copied-current rule. Supplements the original full actor-journal review, with no tail exclusions at complete boundary.'), f, indent=2)
        f.write('\n')

if __name__ == '__main__':
    main()
