"""Launch one reviewed Direct34 cycle and its audits; no automatic successor."""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, time

B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
ROOT = Path(__file__).resolve().parent
OUT = B / 'runs/serl_take_cycle34_20261027_v1'
PARENT = B / 'runs/serl_take_cycle33_20261027_v1'
PREP = B / 'runtime/prepare34_parameter54_20261028_v1'

def read(p):
    return json.loads(p.read_text())

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def write(p, value):
    p.write_text(json.dumps(value, indent=2) + '\n')

def identity(pid):
    return Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()

assert not (OUT / 'LAUNCH.json').exists()
decision = read(ROOT / 'DECISION34.json')
assert decision['passed'] and decision['plot_inspected']
assert decision['parent_cycle'] == 33 and decision['new_cycle'] == 34
assert decision['new_cycles'] == 1 and decision['automatic_followup'] is False
assert decision['convergence_claim'] is False
assert {'parent_review', 'health', 'loss', 'check_only'} <= set(decision['evidence'])
for item in decision['evidence'].values():
    assert sha(item['path']) == item['sha256']
assert read(PREP / 'direct_FINISHED.json')['prepared']
assert read(PARENT / 'ARCHIVE_REVIEW_FINISHED.json')['completed']
for job in read(PARENT / 'LAUNCH.json')['jobs']:
    try:
        fields = identity(job['pid'])
    except FileNotFoundError:
        continue
    assert fields[19] != job['proc_start_ticks'] or fields[0] == 'Z'
preparation = read(OUT / 'PREPARATION_REVIEW.json')
assert preparation['passed'] and preparation['parent_cycle'] == 33 and preparation['new_cycle'] == 34
assert sha(OUT / 'REGISTRATION.json') == preparation['registration_sha256']
for key in ['checkpoint', 'review', 'health', 'check_only']:
    item = preparation[key]
    assert sha(item['path']) == item['sha256']
for label, key in [('parent_review', 'review'), ('health', 'health'), ('check_only', 'check_only')]:
    assert decision['evidence'][label] == preparation[key]
assert decision['evidence']['loss']['path'] == str(B / 'runs/direct33_complete_loss_20261028_v1/REVIEW.json')
assert read(Path(decision['evidence']['loss']['path']))['passed']
assert read(OUT / 'CHECK_ONLY_EXIT.json')['exit_code'] == 0
assert read(OUT / 'CHECK_ONLY_REVIEW.json')['passed']
for name, digest in read(ROOT / 'SOURCE_FREEZE.json')['files'].items():
    assert sha(ROOT / name) == digest

cmd = read(OUT / 'COMMAND.json')['command']
assert cmd[cmd.index('--output') + 1] == str(OUT / 'direct')
assert cmd[cmd.index('--resume') + 1] == preparation['checkpoint']['path']
assert cmd[cmd.index('--registration') + 1] == str(OUT / 'REGISTRATION.json')
assert '--check-only' not in cmd
(OUT / 'audit_source').mkdir()
for name in ['startup_review.py', 'archive_review.py']:
    shutil.copyfile(ROOT / name, OUT / name)
shutil.copyfile(ROOT / 'audit_serl_take34_replay_20261027.py', OUT / 'audit_source/audit_serl_take34_replay_20261027.py')
write(OUT / 'PRELAUNCH_REVIEW.json', dict(preparation, scientific_decision=decision, plot_inspected=True, time=time.time()))
env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1', CUDA_VISIBLE_DEVICES='0', XLA_PYTHON_CLIENT_PREALLOCATE='false', JAX_COMPILATION_CACHE_DIR=str(B / 'runtime/jax_compilation_cache'))
log = OUT / 'direct_driver.log'
p = subprocess.Popen(cmd, stdout=log.open('x'), stderr=subprocess.STDOUT, env=env, start_new_session=True)
job = dict(controller='direct', command=cmd, pid=p.pid, proc_start_ticks=identity(p.pid)[19], time=time.time(), log=str(log))
write(OUT / 'LAUNCH.json', dict(time=time.time(), jobs=[job], new_cycles=1, automatic_followup=False))
for name, args, receipt in [
    ('archive_review', ['serl_take', '34'], 'MONITOR_LAUNCH.json'),
    ('startup_review', [], 'STARTUP_LAUNCH.json'),
]:
    script = OUT / (name + '.py')
    p = subprocess.Popen([str(B / 'env/bin/python'), str(script)] + args, stdout=(OUT / (name + '.log')).open('x'), stderr=subprocess.STDOUT, env=env, start_new_session=True)
    write(OUT / receipt, dict(pid=p.pid, proc_start_ticks=identity(p.pid)[19], time=time.time(), script_sha256=sha(script)))
print(json.dumps(dict(learner=job, archive=read(OUT / 'MONITOR_LAUNCH.json'), startup=read(OUT / 'STARTUP_LAUNCH.json')), indent=2))
