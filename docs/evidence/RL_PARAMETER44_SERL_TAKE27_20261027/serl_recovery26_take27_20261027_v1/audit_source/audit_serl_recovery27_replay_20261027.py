"""Independent scalar reconstruction of every newly stored multistep target."""
from collections import defaultdict
import numpy as np


def audit(checkpoint, parent, transitions):
    current, old = checkpoint['replay'], parent['replay']
    n = old['size']
    extra, previous = current['multistep_target_extension'], old['multistep_target_extension']
    assert extra['marker'] == previous['marker'] == checkpoint['learner']['multistep_target_extension']
    assert parent['learner']['multistep_target_extension'] == extra['marker']
    for key in ['target_rewards','target_bootstrap','target_endpoints','target_lengths']:
        np.testing.assert_array_equal(extra[key][:n], previous[key])
    assert extra['ready'][:len(previous['ready'])] == previous['ready']
    old_pending = {i for ids in previous['pending'].values() for i in ids}
    assert len(old_pending) == 930 and set(previous['pending']) == set(range(30))
    assert sorted(previous['ready']+list(old_pending)) == list(range(n))
    assert all(extra['pending'].get(k) == v for k,v in previous['pending'].items())
    ready = set(extra['ready'])
    pending = [i for ids in extra['pending'].values() for i in ids]
    assert len(ready) == len(extra['ready'])
    assert sorted(extra['ready']+pending) == list(range(current['size']))
    rows = defaultdict(list)
    for row in transitions:
        assert row['cycle']==27 and row['recovery_stream'] in range(30,60)
        rows[(row['cycle'],row['condition'])].append(row)
    expected_pending = set(old_pending)
    mature = 0
    for episode in rows.values():
        assert sum(bool(row['done']) for row in episode) <= 1
        if any(row['done'] for row in episode):assert episode[-1]['done']
        for j, row in enumerate(episode):
            i = row['step']-1
            future = episode[j:j+32]
            done = bool(future[-1]['done'])
            if len(future)<32 and not done:
                expected_pending.add(i)
                assert i not in ready and extra['target_endpoints'][i] == -1
                continue
            assert i in ready
            end = future[-1]['step']-1
            value = sum(.9995**k*float(current['arrays']['rewards'][entry['step']-1,0]) for k,entry in enumerate(future))
            assert extra['target_rewards'][i] == np.float32(value)
            assert extra['target_bootstrap'][i] == np.float32(0. if done else .9995**(len(future)-1))
            assert extra['target_endpoints'][i] == end
            assert extra['target_lengths'][i] == len(future)
            mature += 1
    assert expected_pending == set(pending)
    assert mature+len(pending)-len(old_pending) == current['size']-n
    return dict(passed=True, retained_derived_rows=n, new_mature_rows=mature,
                new_pending_rows=len(pending)-len(old_pending), quarantined_old_pending_rows=len(old_pending), all_new_derived_targets_exact=True,
                uniform_sampling_domain='mature rows only; pending excluded')
