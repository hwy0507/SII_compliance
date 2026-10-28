"""Wait for complete55 and validate its frozen state; never execute physics."""
from pathlib import Path
import hashlib, json, os, subprocess, time

B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT = B / 'runs/parameter55_frozen_full30_20261028_v1'
RT = Path(__file__).resolve().parent
PARENT = B / 'runs/parameter_capacity_pool30_cycle55_20261026_v1'
REVIEW = B / 'runs/parameter_capacity_pool30_cycle55_review_20261026_v1'
PLAN_SHA = '906bb31f23a3c63b49edc5e298407c284c81af173cd3d5f816581c4325fac986'

def read(p):
    return json.loads(p.read_text())

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def write(p, value):
    p.write_text(json.dumps(value, indent=2) + '\n')

def live(job):
    try:
        f = Path(f"/proc/{job['pid']}/stat").read_text().split(') ')[1].split()
        return f[19] == job['proc_start_ticks'] and f[0] != 'Z'
    except FileNotFoundError:
        return False

def main():
    os.sched_setaffinity(0, {3})
    assert sha(OUT / 'PLAN.json') == PLAN_SHA
    plan = read(OUT / 'PLAN.json')
    assert read(OUT / 'validation53/REVIEW.json')['passed']
    for name, expected in plan['source_hashes'].items():
        assert sha(RT / name) == expected
    deadline = time.monotonic() + plan['preparation_wait_seconds']
    binding = None
    while True:
        assert time.monotonic() < deadline, 'Original four-hour frozen55 preparation wait expired'
        for failure in [PARENT / 'ARCHIVE_REVIEW_FAILURE.json', *PARENT.glob('*/train/FAILURE.json')]:
            assert not failure.exists(), str(failure)
        launch = PARENT / 'LAUNCH.json'
        if launch.exists():
            if binding is None:
                binding = dict(time=time.time(), launch_sha256=sha(launch), jobs=read(launch)['jobs'])
                assert {j['controller'] for j in binding['jobs']} == set(plan['controllers'])
                write(OUT / 'PARENT55_BINDING.json', binding)
            assert sha(launch) == binding['launch_sha256']
            for job in binding['jobs']:
                finished = PARENT / job['controller'] / 'train/FINISHED.json'
                if not live(job):
                    assert finished.exists() and read(finished)['status'] == 'stopped_at_complete_cycle'
            if (PARENT / 'ARCHIVE_REVIEW_FINISHED.json').exists() and (REVIEW / 'FINISHED.json').exists():
                assert read(PARENT / 'ARCHIVE_REVIEW_FINISHED.json')['completed']
                assert read(REVIEW / 'FINISHED.json')['completed']
                if not any(live(job) for job in binding['jobs']):
                    break
        time.sleep(5)
    complete = read(REVIEW / 'REVIEW.json')
    assert complete['passed'] and (REVIEW / 'health/DIAGNOSIS.json').exists()
    commands = []
    for method in plan['controllers']:
        parent = PARENT / method / 'REGISTRATION.json'
        protocol = read(parent)
        assert protocol['conditions'] == plan['conditions']
        assert protocol['replay_capacity_stage']['parent_cycle'] == 23
        assert protocol['replay_capacity_followup_stage']['parent_cycle'] == 47
        checkpoint = B / 'runs/parameter_capacity_pool30_cycle55_archive_20261026_v1' / method / 'cycle_00055.pt'
        digest = sha(checkpoint)
        assert digest == complete['methods'][method]['checkpoint_sha256']
        journal = PARENT / method / 'train/cycle_00055/active_short_train_0600/actor_intervals.jsonl'
        reg = read(OUT / 'validation53' / method / 'REGISTRATION.json')
        reg.update(parent_cycle=55, checkpoint=str(checkpoint), checkpoint_sha256=digest,
                   training_registration=str(parent), training_registration_sha256=sha(parent),
                   required_review=str(REVIEW / 'REVIEW.json'), required_review_sha256=sha(REVIEW / 'REVIEW.json'),
                   gate_observations=str(journal), gate_observations_sha256=sha(journal))
        assert reg['runtime'] == protocol['runtime']
        assert reg['source_hashes'] == plan['source_hashes']
        assert reg['cpu'] == plan['cpu_mapping'][method] and reg['device'] == 'cuda:0'
        dest = OUT / method
        dest.mkdir()
        write(dest / 'REGISTRATION.json', reg)
        commands.append(dict(controller=method, command=[str(B / 'env/bin/python'), str(RT / 'evaluate_parameter55_frozen_full30_20261028.py'), '--registration', str(dest / 'REGISTRATION.json')]))
    write(OUT / 'COMMANDS.json', dict(jobs=commands))
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='0,1,2,3', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
    processes, identities = [], []
    for job in commands:
        proc = subprocess.Popen(job['command'] + ['--check-only'], stdout=(OUT / job['controller'] / 'check_only.log').open('x'), stderr=subprocess.STDOUT, env=env)
        processes.append((job['controller'], proc))
        identities.append(dict(job, pid=proc.pid, proc_start_ticks=Path(f'/proc/{proc.pid}/stat').read_text().split(') ')[1].split()[19]))
    write(OUT / 'CHECK_ONLY_LAUNCH.json', dict(time=time.time(), jobs=identities))
    deadline = time.monotonic() + 600
    while any(proc.poll() is None for _, proc in processes):
        if time.monotonic() >= deadline:
            write(OUT / 'CHECK_ONLY_OBSERVATION_TIMEOUT.json', dict(time=time.time(), jobs=identities, children_not_terminated=True, automatic_retry=False))
            raise TimeoutError('Observation ended; inspect original check-only children, do not restart')
        time.sleep(2)
    codes = {method: proc.returncode for method, proc in processes}
    write(OUT / 'CHECK_ONLY_EXIT_CODES.json', codes)
    assert all(value == 0 for value in codes.values()), codes
    for method in plan['controllers']:
        check = read(OUT / method / 'CHECK_ONLY_REVIEW.json')
        assert check['passed'] and check['full_replay_restored_exact'] and check['validated_parent_cycle'] == 55
    write(OUT / 'CHECK_ONLY_COMPLETE.json', dict(time=time.time(), passed=True, plan_sha256=PLAN_SHA, new_physics=0, new_optimizer_updates=0, automatic_evaluation=False))

if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        write(OUT / 'PREPARATION_FAILURE.json', dict(time=time.time(), error=repr(error), automatic_retry=False))
        raise
