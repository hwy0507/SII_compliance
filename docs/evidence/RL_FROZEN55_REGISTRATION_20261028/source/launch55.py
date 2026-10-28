"""Launch exactly the reviewed, preregistered frozen55 ninety-episode evaluation."""
from pathlib import Path
import hashlib, json, os, subprocess, time

B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT = B / 'runs/parameter55_frozen_full30_20261028_v1'
RT = Path(__file__).resolve().parent

def read(p):
    return json.loads(p.read_text())

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def write(p, value):
    p.write_text(json.dumps(value, indent=2) + '\n')

assert not (OUT / 'LAUNCH.json').exists()
assert sha(OUT / 'PLAN.json') == '906bb31f23a3c63b49edc5e298407c284c81af173cd3d5f816581c4325fac986'
plan = read(OUT / 'PLAN.json')
assert read(OUT / 'CHECK_ONLY_COMPLETE.json')['passed']
approval = read(OUT / 'PRELAUNCH_REVIEW.json')
assert approval['passed'] and approval['parent_cycle'] == 55
assert approval['plan_sha256'] == sha(OUT / 'PLAN.json')
assert approval['check_only_complete_sha256'] == sha(OUT / 'CHECK_ONLY_COMPLETE.json')
for name, expected in plan['source_hashes'].items():
    assert sha(RT / name) == expected
env = dict(os.environ, CUDA_VISIBLE_DEVICES='0,1,2,3', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
jobs = []
commands = read(OUT / 'COMMANDS.json')['jobs']
assert {j['controller'] for j in commands} == set(plan['controllers']) and len(commands) == 3
for job in commands:
    assert '--validation-cycle' not in job['command'] and '--check-only' not in job['command']
    reg = read(OUT / job['controller'] / 'REGISTRATION.json')
    assert reg['parent_cycle'] == 55 and reg['action_seed'] == plan['action_seed'] and reg['case_ids'] == plan['case_ids']
    assert read(OUT / job['controller'] / 'CHECK_ONLY_REVIEW.json')['passed']
    proc = subprocess.Popen(job['command'], stdout=(OUT / job['controller'] / 'driver.log').open('x'), stderr=subprocess.STDOUT, env=env, start_new_session=True)
    jobs.append(dict(job, pid=proc.pid, start=Path(f'/proc/{proc.pid}/stat').read_text().split(') ')[1].split()[19], time=time.time()))
    write(OUT / 'LAUNCH.json', dict(jobs=jobs, all_spawned=len(jobs) == 3))
source = RT / 'review_parameter55_frozen_full30_20261028.py'
write(OUT / 'REVIEW_REGISTRATION.json', dict(evaluators=jobs, source_sha256=sha(source), plan_sha256=sha(OUT / 'PLAN.json'), time=time.time(), maximum_wait_seconds=21600))
proc = subprocess.Popen([str(B / 'env/bin/python'), str(source), '--root', str(OUT)], stdout=(OUT / 'review.log').open('x'), stderr=subprocess.STDOUT, env=env, start_new_session=True)
write(OUT / 'REVIEW_LAUNCH.json', dict(pid=proc.pid, proc_start_ticks=Path(f'/proc/{proc.pid}/stat').read_text().split(') ')[1].split()[19], time=time.time()))
