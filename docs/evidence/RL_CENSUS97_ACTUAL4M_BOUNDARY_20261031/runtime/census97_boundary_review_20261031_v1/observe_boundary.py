"""Finite read-only observation while the already running boundary audit finishes."""
from pathlib import Path
import os, json, time, hashlib, traceback

D = Path(__file__).resolve().parent
B = D.parents[1]
R = B / 'runs/parameter_census_cycle97_20261031_v1'
BOUND = B / 'runs/census97_capacity_boundary_20261031_v1'
read = lambda p: json.loads(p.read_text())

def put(p, value):
    with p.open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')

def main():
    os.sched_setaffinity(0, {54})
    plan = read(D / 'PLAN.json')
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == plan['observer_sha256']
    ids = plan['identities']
    guard = Path(plan['guard_root'])
    start = time.monotonic()
    rows = []
    with (D / 'OBSERVATIONS.jsonl').open('x') as f:
        while time.time() < plan['observation_deadline_unix']:
            complete = (BOUND / 'REVIEW.json').exists()
            for j in ids:
                if complete and j['pid'] == plan['boundary_pid']:
                    continue
                state = Path('/proc', str(j['pid']), 'stat').read_text().rsplit(')', 1)[1].split()
                assert state[0] != 'Z' and state[19] == j['start']
            assert not (guard / 'STOP').exists() and not (guard / 'FAILURE.json').exists()
            assert not list(BOUND.glob('FAILURE*')) and not (R / 'ARCHIVE_REVIEW_FAILURE.json').exists()
            progress = {m: read(R / m / 'train/PROGRESS.json') for m in plan['methods']}
            for m in plan['methods']:
                assert not (R / m / 'train/FAILURE.json').exists()
                assert not (R / m / 'DRIVER_FAILURE.json').exists()
            sample = json.loads((guard / 'samples.jsonl').read_text().splitlines()[-1])
            assert time.time() - sample['time'] < 20
            row = dict(time=time.time(), elapsed_seconds=time.monotonic()-start,
                       progress=progress, gpu=sample, boundary_complete=complete,
                       verified_identities=len(ids)-int(complete))
            rows.append(row)
            f.write(json.dumps(row) + '\n')
            f.flush()
            print(json.dumps(dict(time=row['time'], steps={m:v['steps'] for m,v in progress.items()},
                                  gpu=[g['utilization'] for g in sample['gpus']], boundary_complete=complete)), flush=True)
            if complete:
                assert read(BOUND / 'REVIEW.json')['passed']
                put(D / 'OBSERVATION_REVIEW.json', dict(passed=True, time=time.time(),
                    samples=len(rows), elapsed_seconds=time.monotonic()-start,
                    identities=ids, first_steps={m:rows[0]['progress'][m]['steps'] for m in plan['methods']},
                    last_steps={m:progress[m]['steps'] for m in plan['methods']},
                    boundary_completed=True, convergence_claim=False))
                return
            time.sleep(30)
    put(D / 'OBSERVATION_TIMEOUT.json', dict(time=time.time(), samples=len(rows),
        scientific_failure=False, scope='Bounded observer ended; original training and boundary audit were not stopped.'))

if __name__ == '__main__':
    try:
        main()
    except BaseException:
        put(D / ('OBSERVATION_FAILURE_' + str(time.time_ns()) + '.json'), dict(time=time.time(), traceback=traceback.format_exc()))
        raise
