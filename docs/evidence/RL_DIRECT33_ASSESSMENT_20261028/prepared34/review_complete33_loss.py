"""Bounded read-only loss review after the original Direct33 learner exits."""
from pathlib import Path
import hashlib, json, os, statistics, time

os.sched_setaffinity(0, {54})
B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
ROOT = Path(__file__).resolve().parent
RUN = B / 'runs/serl_take_cycle33_20261027_v1'
OUT = B / 'runs/direct33_complete_loss_20261028_v1'

def read(p):
    return json.loads(p.read_text())

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def write(p, value):
    p.write_text(json.dumps(value, indent=2) + '\n')

def live(job):
    try:
        parts = Path(f"/proc/{job['pid']}/stat").read_text().split(') ')[1].split()
        return parts[19] == job['proc_start_ticks'] and parts[0] != 'Z'
    except FileNotFoundError:
        return False

try:
    plan = read(OUT / 'PLAN.json')
    assert sha(RUN / 'LAUNCH.json') == plan['launch_sha256']
    assert sha(Path(__file__)) == plan['source_sha256']
    job = plan['learner']
    deadline = time.monotonic() + plan['maximum_wait_seconds']
    while True:
        assert time.monotonic() < deadline, 'Fixed loss review wait expired'
        assert not (RUN / 'direct/FAILURE.json').exists()
        done = RUN / 'direct/FINISHED.json'
        if done.exists() and not live(job):
            assert read(done)['status'] == 'stopped_at_complete_cycle'
            break
        assert live(job), 'Original learner exited without complete FINISHED'
        time.sleep(5)
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    source = RUN / 'direct/optimizer.jsonl'
    digest = sha(source)
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    assert len(rows) == 41250
    assert [r['step'] for r in rows] == list(range(1328041, 1369291))
    result = dict(time=time.time(), source=dict(path=str(source), sha256=digest), rows=len(rows), metrics={}, new_physics=0, optimizer_updates=0, convergence_claim=False)
    keys = ['serl/critic/critic_loss', 'serl/actor/actor_loss']
    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    for axis, key in zip(axes, keys):
        values = [r[key] for r in rows]
        arr = np.asarray(values)
        assert np.isfinite(arr).all()
        stats = dict(first1000=float(arr[:1000].mean()), last1000=float(arr[-1000:].mean()), mean=float(arr.mean()), maximum=float(arr.max()), minimum=float(arr.min()), nonfinite=0)
        assert abs(stats['mean'] - statistics.fmean(values)) < 1e-10
        assert stats['maximum'] == max(values)
        result['metrics'][key] = stats
        axis.plot(np.arange(len(arr))[::20], arr[::20], alpha=.25, lw=.5)
        rolling = np.convolve(arr, np.ones(1000)/1000, mode='valid')
        axis.plot(np.arange(len(rolling))+999, rolling)
        axis.set_title(key)
        axis.set_xlabel('optimizer row')
        axis.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(OUT / 'loss.png', dpi=140)
    assert sha(source) == digest
    result.update(passed=True, independent_saved_arithmetic=True, plot_sha256=sha(OUT / 'loss.png'), plot_inspected=False)
    write(OUT / 'REVIEW.json', result)
except BaseException as error:
    write(OUT / 'FAILURE.json', dict(time=time.time(), error=repr(error)))
    raise
