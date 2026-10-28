"""Independently check saved statistics and add noncausal terminal timing."""
from pathlib import Path
import hashlib
import json
import math
import os
import statistics
import time

os.sched_setaffinity(0, {54})
import numpy as np
OUT = Path(__file__).resolve().parent
report = json.loads((OUT/'REVIEW.json').read_text())
results = {}

def check(values, saved):
    ordered = sorted(values)
    n = len(values)
    def quantile(q):
        x = (n-1)*q
        lo = math.floor(x)
        return ordered[lo] + (ordered[math.ceil(x)]-ordered[lo])*(x-lo)
    count = math.ceil(n*.01)
    expected = dict(count=n, mean=statistics.fmean(values), median=statistics.median(values),
                    p95=quantile(.95), p99=quantile(.99), maximum=max(values), minimum=min(values),
                    top_one_percent_count=count,
                    top_one_percent_sum_fraction=math.fsum(ordered[-count:])/math.fsum(values),
                    bottom_99percent_mean=statistics.fmean(ordered[:-count]),
                    greater_than_5_count=sum(v>5 for v in values),
                    greater_than_10_count=sum(v>10 for v in values))
    for k, v in expected.items():
        assert math.isclose(v, saved[k], abs_tol=1e-12, rel_tol=1e-12), (k,v,saved[k])

for cycle, value in report['methods']['vmc'].items():
    source = value['source']
    raw = Path(source['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == source['sha256']
    rows = [json.loads(line) for line in raw.splitlines()]
    values = [r['agent_train/q_loss'] for r in rows]
    assert np.array_equal(np.load(OUT/f'cycle{cycle}_critic.npy'), np.asarray(values))
    for name, selected in [('all',values), ('first5000',values[:5000]), ('last5000',values[-5000:])]:
        check(selected, value[name])
    for b in value['bins']:
        check(values[b['first_update_offset']:b['last_update_offset']+1], b)
    episode_bytes = Path(source['episodes_path']).read_bytes()
    assert hashlib.sha256(episode_bytes).hexdigest() == source['episodes_sha256']
    eps = [json.loads(line) for line in episode_bytes.splitlines()]
    first = min(eps, key=lambda e:e['total_steps'])
    offset = first['total_steps']-rows[0]['step']
    assert rows[offset]['step'] == first['total_steps']
    before = values[offset-1000:offset]
    after = values[offset:offset+1000]
    results[cycle] = dict(statistics_and_arrays_exact=True, all_42_bins_checked=True,
                          first_terminal=dict(condition=first['condition'], step=first['total_steps'],
                                              zero_based_update_offset=offset),
                          mean1000_before=statistics.fmean(before), mean1000_from_terminal=statistics.fmean(after),
                          median1000_before=statistics.median(before), median1000_from_terminal=statistics.median(after),
                          new_terminal_count_in_following1000=sum(first['total_steps']<=e['total_steps']<first['total_steps']+1000 for e in eps))
assert hashlib.sha256((OUT/'loss_distribution.png').read_bytes()).hexdigest()==report['plot_sha256']
(OUT/'SAVED_REVIEW.json').write_text(json.dumps(dict(passed=True, time=time.time(), methods=results,
    plot_inspected=True, convergence_claim=False, causal_claim=False, new_physics=0, optimizer_updates=0,
    limitation='Timing association from saved episode completion clocks only; actual historical minibatch samples and pre-terminal critic predictions not reconstructed. Cannot attribute individual spikes or certify them benign.'),indent=2)+'\n')
print(json.dumps(results,indent=2))
