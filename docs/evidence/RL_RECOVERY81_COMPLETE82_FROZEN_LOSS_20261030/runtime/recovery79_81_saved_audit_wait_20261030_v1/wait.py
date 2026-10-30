from pathlib import Path
import hashlib, json, os, subprocess, time
D = Path(__file__).parent
def read(p): return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def put(p, x):
    with p.open('x') as f: f.write(json.dumps(x, indent=2) + '\n')
def live(j):
    p = Path(f'/proc/{j["pid"]}/stat')
    if not p.exists(): return False
    s = p.read_text().rsplit(')', 1)[1].split()
    return s[19] == j['proc_start_ticks'] and s[0] != 'Z'
os.sched_setaffinity(0, {54})
try:
    plan = read(D / 'PLAN.json')
    root = Path(plan['root'])
    for ref in plan['sources'].values(): assert sha(ref['path']) == ref['sha256']
    while True:
        for name in ['FAILURE.json', 'WAIT_FAILURE.json']:
            assert not (root / name).exists(), name
        alive = live(plan['original_waiter'])
        if (root / 'REVIEW.json').exists() and not alive:
            assert read(root / 'REVIEW.json')['passed']
            break
        assert alive, 'Original window waiter absent without complete report; no restart'
        assert time.time() < plan['original_deadline_unix'], 'Original window deadline reached; no extension or restart'
        time.sleep(5)
    assert not (root / 'SAVED_ARITHMETIC_REVIEW.json').exists(), 'Saved review already exists; refuse duplicate execution'
    for ref in plan['sources'].values(): assert sha(ref['path']) == ref['sha256']
    result = subprocess.run([plan['python'], str(root / 'review_saved.py')], check=True)
    assert read(root / 'SAVED_ARITHMETIC_REVIEW.json')['passed']
    put(D / 'FINISHED.json', dict(passed=True, time=time.time(), saved_arithmetic_sha256=sha(root / 'SAVED_ARITHMETIC_REVIEW.json'), new_physics=0, optimizer_updates=0, plot_inspected=False, automatic_training=False))
except BaseException as e:
    put(D / 'FAILURE.json', dict(time=time.time(), error=repr(e)))
    raise
