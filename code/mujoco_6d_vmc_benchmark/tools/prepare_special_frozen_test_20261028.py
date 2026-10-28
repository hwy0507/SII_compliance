"""Pin the current12 test inputs before new student fitting finishes.

Preparation reads manifests, never runs a simulator or reads test outcomes.
Execution requires the complete, audited nine-model fit and an inactive
original fitting service. It dispatches exactly one frozen108 matrix.
"""
import argparse
import ast
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def require(value, reason):
    if not value:
        raise ValueError(reason)


def manifest(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*.py'))}


def formal_model_check(source, model_path, protocol):
    # Match frozen evaluation_settings: its archived geometry has dt=1e-4,
    # while its in-memory formal copy has dt=5e-5. Never rewrite the archive.
    import mujoco
    import numpy as np
    tree = ast.parse((source / 'physics_source/tools/paper_office_worker_20261002.py').read_text())
    values = [ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'V6_SHA' for t in node.targets)]
    require(len(values) == 1 and sha(model_path) == values[0], 'Archived geometry differs from frozen loader')
    model = mujoco.MjModel.from_binary_path(str(model_path))
    original_dt = model.opt.timestep
    model.opt.timestep = protocol['physics_dt_s']
    buffer = np.empty(mujoco.mj_sizeModel(model), dtype=np.uint8)
    mujoco.mj_saveModel(model, None, buffer)
    formal = hashlib.sha256(buffer.tobytes()).hexdigest()
    require(formal == protocol['formal_model_sha256'], 'Formal MJB drift')
    return dict(archived_geometry_sha256=values[0], archived_dt=original_dt,
                formal_dt=protocol['physics_dt_s'], formal_sha256=formal,
                simulation_steps=0, archive_modified=False, mujoco=mujoco.__version__)


def prepare(root, training, evaluation, source, handoff):
    require(not root.exists() and not evaluation.exists(), 'Use new preparation/evaluation paths')
    parent = read(source / 'REGISTRATION.json')
    protocol = read(source / 'PROTOCOL.json')
    conditions = read(source / 'CONDITIONS.json')['conditions']
    require(len(conditions) == len({c['id'] for c in conditions}) == 12, 'Require original12 conditions')
    require(sha(source / 'CONDITIONS.json') == parent['condition_sha256'] == protocol['condition_file_sha256'], 'Condition drift')
    require(sha(source / 'PROTOCOL.json') == parent['protocol_sha256'], 'Protocol drift')
    require(manifest(source / 'physics_source') == parent['physics_source_sha256'], 'Frozen physics source drift')
    runtime = Path(parent['runtime'])
    model = runtime / 'v6/construction/rollout.mjb'
    require(protocol['physics_dt_s'] == .00005 and protocol['duration_s'] == 55., 'Changed physics clock/horizon')
    model_check = formal_model_check(source, model, protocol)
    handoff_plan = read(handoff / 'REGISTRATION.json')
    require(Path(handoff_plan['training']) == training, 'Wrong fitting handoff')
    files = [source / n for n in ('REGISTRATION.json', 'CONDITIONS.json', 'PROTOCOL.json')]
    files += [model, runtime / 'v6/PROTOCOL.json', runtime / 'v6/esn_original_v2/rollout.json', handoff / 'REGISTRATION.json']
    root.mkdir(parents=True)
    snapshot = root / 'tools'
    snapshot.mkdir()
    for name in ('run_nonrl_spt_matrix_20261025.py', 'audit_special_scene_fits_20261028.py',
                 'train_special_scene_models_20261028.py', 'prepare_special_frozen_test_20261028.py'):
        shutil.copy2(ROOT / 'tools' / name, snapshot / name)
    registration = dict(schema='sii-special-frozen108-preparation-v1',
        registered_utc=datetime.now(timezone.utc).isoformat(), training=str(training),
        evaluation=str(evaluation), source_run=str(source), handoff=str(handoff),
        handoff_service='sii-special-learning-handoff-v2-20261028.service',
        runtime=str(runtime), python=parent['simulation_python'], expected_models=9, expected_episodes=108,
        conditions=[c['id'] for c in conditions], physics_source_sha256=parent['physics_source_sha256'],
        model_check=model_check,
        input_hashes={str(p): sha(p) for p in files}, tools_sha256=manifest(snapshot),
        metrics='Task/Strict full denominators; BOTH-success conditional SPT, global108 minimum BOTH T_ref; all-episode mean peak torque; contact-dt comfort; machine compliance',
        limitations='Previously inspected current test conditions; no claim of unseen confirmation, no test model selection. This preparation is not a completed test or new-model audit.',
        resource=dict(simulators=1, threads=1, memory_max_bytes=3*1024**3, swap_bytes=0))
    write(root / 'REGISTRATION.json', registration)
    print(json.dumps(dict(status='prepared_not_dispatched', root=str(root), episodes=108,
                          registration_sha256=sha(root / 'REGISTRATION.json'))))


def validate(root):
    reg = read(root / 'REGISTRATION.json')
    require(reg['schema'] == 'sii-special-frozen108-preparation-v1', 'Wrong registration')
    require(manifest(root / 'tools') == reg['tools_sha256'], 'Prepared tools changed')
    require(sha(Path(__file__)) == reg['tools_sha256']['prepare_special_frozen_test_20261028.py'], 'Dispatcher changed')
    for name, digest in reg['input_hashes'].items():
        require(sha(Path(name)) == digest, f'Pinned input changed: {name}')
    source = Path(reg['source_run'])
    require(manifest(source / 'physics_source') == reg['physics_source_sha256'], 'Physics source changed')
    return reg


def run(root):
    lock = (root / '.dispatch.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    reg = validate(root)
    require(not (root / 'execution.json').exists(), 'Do not duplicate or silently restart a dispatch')
    require(not Path(reg['evaluation']).exists(), 'Evaluation already exists; inspect it')
    handoff = read(Path(reg['handoff']) / 'execution.json')
    require(handoff['status'] == 'fitting_complete_pending_test_review', 'Original fitting handoff incomplete')
    state = dict(line.split('=', 1) for line in subprocess.check_output(
        ['systemctl', '--user', 'show', reg['handoff_service'], '-p', 'ActiveState', '-p', 'Result'], text=True).splitlines())
    require(state == dict(ActiveState='inactive', Result='success'), 'Original fitting service still active or failed')
    cg = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    limit = (cg / 'memory.max').read_text().strip()
    require(limit != 'max' and int(limit) <= 3*1024**3 and (cg / 'memory.swap.max').read_text().strip() == '0', 'Real <=3GiB/swap0 required')
    require(all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')), 'One numerical thread required')
    training = Path(reg['training'])
    require(sha(training / 'MODEL_LOCK.json') == handoff['model_lock_sha256'], 'Wrong fitting output')
    require(len(read(training / 'MODEL_LOCK.json')['models']) == 9, 'Need all nine models')
    receipt = dict(status='auditing_fits', started_utc=datetime.now(timezone.utc).isoformat(),
                   registration_sha256=sha(root / 'REGISTRATION.json'))
    write(root / 'execution.json', receipt)
    try:
        audit = root / 'FIT_AUDIT.json'
        command = [reg['python'], str(root / 'tools/audit_special_scene_fits_20261028.py'),
                   '--root', str(training), '--physics-source', str(Path(reg['source_run']) / 'physics_source'),
                   '--output', str(audit)]
        with (root / 'fit_audit.log').open('x') as stream:
            subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True)
        result = read(audit)
        require(result['status'] == 'passed' and result['model_lock_sha256'] == handoff['model_lock_sha256'], 'Fit audit did not qualify actual models')
        validate(root)
        receipt.update(status='evaluating_frozen108', fit_audit_sha256=sha(audit))
        write(root / 'execution.json', receipt)
        command = [reg['python'], str(root / 'tools/run_nonrl_spt_matrix_20261025.py'),
                   '--source-run', reg['source_run'], '--root', reg['evaluation'], '--runtime', reg['runtime'],
                   '--python', reg['python'], '--model-lock', str(training / 'MODEL_LOCK.json')]
        with (root / 'evaluation.log').open('x') as stream:
            subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True)
        final = read(Path(reg['evaluation']) / 'execution.json')
        require(final['status'] == 'complete' and final['completed'] == 108, 'Incomplete frozen matrix')
        validate(root)
        receipt.update(status='evaluation_complete_pending_independent_audit',
                       report_sha256=sha(Path(reg['evaluation']) / 'REPORT.json'))
    except BaseException as exc:
        receipt.update(status='failed_preserved', error=repr(exc))
        raise
    finally:
        receipt['ended_utc'] = datetime.now(timezone.utc).isoformat()
        write(root / 'execution.json', receipt)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--training', type=Path)
    p.add_argument('--evaluation', type=Path)
    p.add_argument('--source-run', type=Path)
    p.add_argument('--handoff', type=Path)
    p.add_argument('--run', action='store_true')
    a = p.parse_args()
    if a.run:
        run(a.root.resolve())
    else:
        require(all((a.training, a.evaluation, a.source_run, a.handoff)), 'Preparation needs all four input paths')
        prepare(a.root.resolve(), a.training.resolve(), a.evaluation.resolve(), a.source_run.resolve(), a.handoff.resolve())
