"""Local-only, bounded RL diagnostics with immutable inputs and resumable stages.

No SSH, no scheduler, no held-out evaluation. Run inside a local user systemd
unit capped at 3 GiB, with one simulator and one numerical thread. A completed
smoke checkpoint is continued, never replaced or counted as a learned success.
"""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from office_v7_uniform24_20261008 import read, write, sha, now, FORMAL

TOOLS = Path(__file__).resolve().parent
LOCK_FD = None
PATCHED = (
    'local_rl_campaign_20261009.py', 'office_v7_uniform24_20261008.py',
    'research72_train_rl_20261003.py', 'run_paper_final_validation_20261003.py',
    'train_baseline_repair_rl_20261008.py', 'baseline_repair_worker_20261008.py',
    'baseline_fullrange_controllers_20261009.py', 'test_baseline_fullrange_20261009.py',
    'test_baseline_repair_rl_20261008.py', 'report_office_v7_uniform24_20261008.py',
    'audit_repair_parameter_trace_20261008.py',
)


def hashes(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and '.git' not in p.parts
            and p.suffix != '.pyc'}


def prepare(root, runtime):
    if platform.node() != 'airpig':
        raise RuntimeError('This campaign is authorized on local airpig only')
    history = runtime/'history'
    root.mkdir(parents=True, exist_ok=False)
    shutil.copytree(history/'source_v9', root/'source',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in PATCHED:
        shutil.copy2(TOOLS/name, root/'source/tools'/name)
    parameter = root/'parameter_fullrange'
    shutil.copytree(history/'parameter_v2', parameter,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copy2(TOOLS/'baseline_fullrange_controllers_20261009.py', parameter)
    (parameter/'controllers.py').write_text('from baseline_fullrange_controllers_20261009 import *\n')
    agent = parameter/'official_parameter_agent.py'
    original = agent.read_text()
    old = 'UPSTREAM = Path("/home/arm1/vmc_mujoco_runtime/SimbaV2")'
    assert original.count(old) == 1
    agent.write_text(original.replace(old, 'UPSTREAM = Path('+repr(str(runtime/'SimbaV2'))+')'))
    write(root/'PATH_ADAPTATION.json', dict(original_agent_sha256=sha(history/'parameter_v2/official_parameter_agent.py'),
        adapted_agent_sha256=sha(agent), change='Only UPSTREAM filesystem path; upstream commit guard unchanged'))
    prior = read(parameter/'PRIORS.json')
    prior['parameter_mapping'] = 'full legal bounds; original logarithmic rate/tank constraints'
    write(parameter/'PRIORS.json', prior)
    for name in ('CONDITIONS.json', 'teacher.json'):
        shutil.copy2(history/name, root/name)
    # Do not copy or read old/new final identities in this development campaign.
    prior_protocol = read(history/'PROTOCOL.json')
    jobs = [dict(name=name, controller=controller, reward=reward, hp='exploratory')
            for name, controller, reward in (
                ('direct_office_task', None, 'office_task'),
                ('parameter_impedance', 'impedance', 'metric'),
                ('parameter_admittance', 'admittance', 'metric'),
                ('parameter_vmc', 'vmc', 'metric'),
                ('direct_metric', None, 'metric'))]
    for source in (jobs[0], jobs[1]):
        jobs.append(dict(source, name=source['name']+'_historical_entropy', hp='historical'))
    start = datetime.now(timezone.utc)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=TOOLS, text=True).strip()
    protocol = dict(schema='sii-baseline-strengthening-v1', registered_utc=now(),
        authorization='2026-10-09 user: repair and strengthen RL baselines, local computation only; server reserved for other use',
        compute_host=platform.node(), source_base_commit=commit, runtime=str(runtime),
        source_scope='Historical source_v9 plus explicitly hashed local infrastructure overlays; frozen physics unchanged',
        baseline_commit='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',
        formal_model_sha256=FORMAL, physics_dt_s=.00005, duration_s=55.,
        condition_file_sha256=sha(root/'CONDITIONS.json'),
        training_dispatch_deadline_utc=(start+timedelta(hours=48)).isoformat(),
        deadline_basis='Agent fail-safe for this finite diagnostic queue, not a user time grant or convergence criterion',
        budgets=dict(training_seeds=[2026100911], rl_steps_per_family_seed=500000,
            diagnostic_segment_steps=11000, smoke_steps=1375,
            planned_max_new_interactions=77000),
        rl_hyperparameters=dict(historical=dict(entropy_coef=-2., initial_temperature=.0001),
                                exploratory=dict(entropy_coef=-.5, initial_temperature=.01)),
        jobs=jobs, unchanged=prior_protocol['unchanged'],
        resources=dict(host='airpig', server_compute=False, simulators=1, numerical_threads=1,
            memory_max_bytes=3221225472, swap_max_bytes=0, gpu='local RTX 5080 Laptop'),
        purity='No teacher demonstrations or BC; teacher.json only supplies unchanged worker configuration plumbing',
        readiness='11k is infrastructure/exploration diagnostic, not sufficient training. Inspect learning and development curves before 50k/100k/250k/500k and three-seed confirmation.',
        selection='All eight development identities for each diagnostic checkpoint; no final identities, no outcome-driven environment/gate edits',
        completion='Stop after finite diagnostic queue; no automatic claim of convergence, fairness completion or ESN superiority')
    write(root/'PROTOCOL.json', protocol)
    write(root/'SOURCE_HASHES.json', hashes(root/'source'))
    write(root/'PARAMETER_HASHES.json', hashes(parameter))
    write(root/'RUNTIME_HASHES.json', {name: hashes(runtime/name) for name in
          ('v6', 'menagerie', 'SimbaV2', 'simba_reward_20260930')})
    write(root/'execution.json', dict(status='registered', registered_utc=now(), host=platform.node()))
    print(json.dumps(dict(root=str(root), protocol_sha256=sha(root/'PROTOCOL.json'))))


def verify(root):
    p = read(root/'PROTOCOL.json')
    assert platform.node() == p['compute_host'] == 'airpig', 'No remote compute authorized'
    assert str(Path(os.environ['SII_LOCAL_RUNTIME']).resolve()) == p['runtime']
    assert hashes(root/'source') == read(root/'SOURCE_HASHES.json')
    assert hashes(root/'parameter_fullrange') == read(root/'PARAMETER_HASHES.json')
    assert {name: hashes(Path(p['runtime'])/name) for name in read(root/'RUNTIME_HASHES.json')} == read(root/'RUNTIME_HASHES.json')
    assert sha(root/'CONDITIONS.json') == p['condition_file_sha256']
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'))
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    assert int((cg/'memory.max').read_text()) <= 3*1024**3
    assert (cg/'memory.swap.max').read_text().strip() == '0'
    return p


def command(root, label, argv):
    receipt = root/(label+'.execution.json')
    if receipt.exists():
        old = read(receipt)
        assert old['status'] == 'complete', 'Preserve failed/interrupted attempt; use a new attempt directory'
        assert old['command'] == argv
        for path, digest in old.get('artifacts', {}).items():
            assert sha(path) == digest
        return
    if shutil.disk_usage(root).free < 30*1024**3:
        raise RuntimeError('Less than 30 GiB free; stop before new episode, preserve artifacts')
    record = dict(status='running', started_utc=now(), command=argv, host=platform.node())
    write(receipt, record)
    with (root/(label+'.log')).open('x') as log:
        result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT,
                                pass_fds=() if LOCK_FD is None else (LOCK_FD,))
    record.update(returncode=result.returncode, ended_utc=now(),
                  status='complete' if result.returncode == 0 else 'failed_preserved')
    if (root/label/'execution.json').exists():
        record['artifacts'] = {str(root/label/'execution.json'): sha(root/label/'execution.json')}
    write(receipt, record)
    if result.returncode:
        raise RuntimeError(label+' failed; inspect '+str(root/(label+'.log')))


def training_command(root, job, output, limit, checkpoint=None):
    p = read(root/'PROTOCOL.json')
    argv = [sys.executable, str(root/'source/tools/train_baseline_repair_rl_20261008.py'),
        '--root', str(root), '--output', str(root/output), '--parameter-source', str(root/'parameter_fullrange'),
        '--seed', str(p['budgets']['training_seeds'][0]), '--steps', '500000',
        '--stop-at-step', str(limit), '--reward', job['reward'], '--hyperparameter-id', job['hp']]
    if job['controller']:
        argv += ['--controller', job['controller']]
    if checkpoint:
        argv += ['--resume-checkpoint', str(checkpoint)]
    return argv


def development(root, job, training):
    state = read(root/training/'execution.json')
    checkpoint = state['checkpoint_rows'][-1]
    assert state['status'] == 'complete'
    manifest = root/(training+'.checkpoint.json')
    data = dict(checkpoint=checkpoint['path'], hashes=checkpoint['hashes'], controller=job['controller'],
        training_protocol=str(root/training/'PROTOCOL.json'),
        training_protocol_sha256=sha(root/training/'PROTOCOL.json'))
    if manifest.exists():
        assert read(manifest) == data
    else:
        write(manifest, data)
    runtime = Path(read(root/'PROTOCOL.json')['runtime'])
    for c in read(root/'CONDITIONS.json')['conditions']:
        if c['role'] != 'development':
            continue
        label = training+'__'+c['id']
        argv = [sys.executable, str(root/'source/tools/baseline_repair_worker_20261008.py'),
            '--research-protocol', str(root/'PROTOCOL.json'), '--protocol-sha256', sha(root/'PROTOCOL.json'),
            '--research-condition', c['id'], '--phase', 'development', '--worker-kind', 'adapted_rl',
            '--v6-input', str(runtime/'v6'), '--reference', str(runtime/'v6/esn_original_v2/rollout.json'),
            '--config', str(root/'teacher.json'), '--output', str(root/label), '--contact-audit',
            '--physics-dt', '.00005', '--parameter-source', str(root/'parameter_fullrange'),
            '--agent-checkpoint', checkpoint['path'], '--checkpoint-manifest', str(manifest)]
        if job['controller']:
            argv += ['--controller', job['controller']]
        command(root, label, argv)
        if job['controller']:
            parameter_audit(root, label)


def parameter_audit(root, run):
    command(root, run.replace('/', '__')+'_parameter_audit', [sys.executable,
        str(root/'source/tools/audit_repair_parameter_trace_20261008.py'),
        '--run', str(root/run), '--parameter-source', str(root/'parameter_fullrange'),
        '--output', str(root/run/'INDEPENDENT_PARAMETER_AUDIT.json')])


def run(root, phase):
    global LOCK_FD
    # One global local campaign lock, inherited by descendants on abnormal exit.
    lock = (root.parent/'.local-rl-compute.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    LOCK_FD = lock.fileno()
    p = verify(root)
    state = dict(status='running', phase=phase, started_utc=now(), host=platform.node())
    write(root/'execution.json', state)
    try:
        if phase == 'preflight':
            for dim in (5, 7):
                command(root, 'contract_action'+str(dim), [sys.executable,
                    str(root/'source/tools/test_baseline_repair_rl_20261008.py'),
                    '--parameter-source', str(root/'parameter_fullrange'), '--action-dimension', str(dim),
                    '--output', str(root/('CONTRACT_ACTION'+str(dim)+'.json'))])
            command(root, 'fullrange', [sys.executable, str(root/'source/tools/test_baseline_fullrange_20261009.py'),
                '--parameter-source', str(root/'parameter_fullrange'), '--output', str(root/'FULLRANGE.json')])
            import mujoco
            import numpy as np
            model = mujoco.MjModel.from_binary_path(str(Path(p['runtime'])/'v6/construction/rollout.mjb'))
            model.opt.timestep = .00005
            buffer = np.empty(mujoco.mj_sizeModel(model), dtype=np.uint8)
            mujoco.mj_saveModel(model, None, buffer)
            import hashlib
            assert hashlib.sha256(buffer.tobytes()).hexdigest() == FORMAL
            write(root/'PREFLIGHT.json', dict(status='passed', formal_model_sha256=FORMAL,
                host=platform.node(), python=sys.version, packages={d.metadata['Name']:d.version for d in importlib.metadata.distributions()},
                scope='GPU gradient/checkpoint/normalizer + parameter contracts + exact model; not learned task success'))
        else:
            assert read(root/'PREFLIGHT.json')['status'] == 'passed'
            smoke = 'direct_office_task_smoke'
            command(root, smoke, training_command(root, p['jobs'][0], smoke, 1375))
            if phase == 'run':
                for i, job in enumerate(p['jobs']):
                    assert datetime.now(timezone.utc) < datetime.fromisoformat(p['training_dispatch_deadline_utc'])
                    label = job['name']+'_segment011k'
                    cp = read(root/smoke/'execution.json')['checkpoint_rows'][-1]['path'] if i == 0 else None
                    command(root, label, training_command(root, job, label, 11000, cp))
                    if job['controller']:
                        for row in read(root/label/'execution.json')['rows']:
                            parameter_audit(root, str(Path(row['run']).relative_to(root)))
                    development(root, job, label)
        state.update(status='complete_review_required', ended_utc=now())
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc), ended_utc=now())
        raise
    finally:
        write(root/'execution.json', state)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'preflight', 'smoke', 'run'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--runtime', type=Path)
    args = parser.parse_args()
    if args.phase == 'prepare':
        prepare(args.root.resolve(), args.runtime.resolve(strict=True))
    else:
        run(args.root.resolve(), args.phase)
