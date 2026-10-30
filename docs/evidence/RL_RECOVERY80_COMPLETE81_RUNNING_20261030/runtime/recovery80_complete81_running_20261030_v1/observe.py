from pathlib import Path
import hashlib, json, os, time
B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
D = Path(__file__).parent
R = B / 'runs/parameter_partial75_recovery_cycle81_20261029_v1'
G = Path('/tmp/sii_gpu_util_guard_20261030_v7')
os.sched_setaffinity(0, {7})
def read(p): return json.loads(Path(p).read_text())
def put(p, x):
    with p.open('x') as f: f.write(json.dumps(x, indent=2) + '\n')
def live(j):
    p = Path(f'/proc/{j["pid"]}/stat')
    if not p.exists(): return False
    s = p.read_text().rsplit(')', 1)[1].split()
    return s[19] == j['proc_start_ticks'] and s[0] != 'Z'
jobs = [(j['controller'], j, None) for j in read(R / 'LAUNCH.json')['jobs']]
jobs += [('archive', read(R / 'MONITOR_LAUNCH.json'), None), ('startup', read(R / 'STARTUP_LAUNCH.json'), R / 'startup/REVIEW.json')]
for name, folder in [('loss', 'parameter_recovery81_loss_20261029_v1'), ('labels', 'parameter_recovery81_task_labels_20261029_v1'), ('vmc_terminal', 'vmc_recovery81_terminal_followup_20261029_v1'), ('admittance_terminal', 'admittance_recovery81_terminal_followup_20261029_v1'), ('window79_81', 'parameter_recovery79_81_reward_stability_20261030_v1')]:
    jobs.append((name, read(B / 'runs' / folder / 'LAUNCH.json'), None))
launch = read(G / 'LAUNCH.json')
for name, pid, start in [('guard', launch['pid'], '570509460')] + [('gpu' + str(i), launch['workers'][str(i)], '570509475') for i in range(4)]:
    jobs.append((name, dict(pid=pid, proc_start_ticks=start), None))
put(D / 'OBSERVATION_PLAN.json', dict(time=time.time(), duration_seconds=180, interval_seconds=30,
    jobs=[dict(name=n, identity=j, terminal=str(p) if p else None) for n, j, p in jobs],
    new_physics=0, optimizer_updates=0, automatic_restart=False))
start = time.monotonic()
rows = []
try:
    while True:
        row = dict(time=time.time(), jobs=[], steps={})
        for name, j, terminal in jobs:
            alive = live(j)
            done = terminal is not None and terminal.exists() and read(terminal)['passed']
            assert alive or done, name
            row['jobs'].append(dict(name=name, live=alive, verified_terminal=bool(done)))
        for m in ['impedance', 'admittance', 'vmc']:
            assert not (R / m / 'train/FAILURE.json').exists()
            row['steps'][m] = read(R / m / 'train/PROGRESS.json')['steps']
        row['gpu'] = json.loads((G / 'samples.jsonl').read_text().splitlines()[-1])
        assert time.time() - row['gpu']['time'] < 20
        rows.append(row)
        with (D / 'OBSERVATIONS.jsonl').open('a') as f: f.write(json.dumps(row) + '\n')
        print(json.dumps(dict(sample=len(rows), steps=row['steps'], gpu=[v['utilization'] for v in row['gpu']['gpus']])), flush=True)
        if time.monotonic() - start >= 180: break
        time.sleep(30)
    saved = [json.loads(l) for l in (D / 'OBSERVATIONS.jsonl').read_text().splitlines()]
    assert saved == rows
    assert all(rows[-1]['steps'][m] > rows[0]['steps'][m] for m in rows[0]['steps'])
    put(D / 'OBSERVATION_FINISHED.json', dict(passed=True, time=time.time(), elapsed=time.monotonic()-start,
        samples=len(rows), identities=len(jobs), first_steps=rows[0]['steps'], last_steps=rows[-1]['steps'],
        saved_rows_verified=True, scientific_processes_continue=True))
except BaseException as e:
    put(D / 'OBSERVATION_FAILURE.json', dict(time=time.time(), error=repr(e)))
    raise
