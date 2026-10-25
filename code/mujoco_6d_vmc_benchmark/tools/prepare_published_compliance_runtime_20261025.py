"""Materialize an auditable NEW runtime from Git sources and pinned robot assets.

This never claims to recover the missing historical office-v6 MJB/checkpoints.
It copies source before execution, retrieves only the parameter adapter subtree
from baseline, and applies the existing main-branch controller repairs. No
historical run, shared simulator, task gate or public limiter is edited.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys


BENCH = Path(__file__).resolve().parents[1]
REPO = BENCH.parents[1]
BASELINE = 'f6e8f8c2711a93f0b5dfc88c608bd82647084d5d'
CHEQ = '1a3c1fee3332848068afdb127c4fa33eee420418'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def git(*args, cwd=REPO):
    return subprocess.check_output(['git', *args], cwd=cwd).decode().strip()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def manifest(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and '.git' not in p.parts}


def prepare(output, menagerie, cheq):
    from teacher_bank_asset_audit_20260930 import collect_robot_assets
    import mujoco
    if mujoco.__version__ != '3.11.0':
        raise RuntimeError('Expected MuJoCo 3.11.0')
    if output.exists():
        raise FileExistsError('Use a new runtime; existing attempts are preserved')
    asset_hashes = collect_robot_assets(menagerie)
    if git('rev-parse', 'HEAD', cwd=cheq) != CHEQ:
        raise ValueError('Published implementation revision mismatch')
    if git('status', '--porcelain', cwd=cheq):
        raise ValueError('Published implementation checkout is not clean')
    output.mkdir(parents=True)
    source = output/'source'
    for name in ('scripts', 'tools', 'assets'):
        shutil.copytree(BENCH/name, source/name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.log'))
    parameter = output/'parameter'
    prefix = 'code/mujoco_6d_vmc_benchmark/experiments/parameter_rl_20261002/'
    names = git('ls-tree', '-r', '--name-only', BASELINE, '--', prefix).splitlines()
    if not names:
        raise RuntimeError('Missing baseline parameter subtree')
    for name in names:
        target = parameter/name.removeprefix(prefix)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(subprocess.check_output(['git', 'show', BASELINE+':'+name], cwd=REPO))
    original_hash = sha(parameter/'controllers.py')
    (parameter/'controllers.py').rename(parameter/'controllers_legacy.py')
    (parameter/'controllers.py').write_text(
        '"""Existing repaired main-branch adapter; original retained beside it."""\n'
        'from baseline_repair_controllers_20261008 import *\n')
    shutil.copytree(cheq, output/'published_cheq',
                    ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
    write(output/'SOURCE_HASHES.json', manifest(source))
    write(output/'PARAMETER_HASHES.json', manifest(parameter))
    write(output/'CHEQ_HASHES.json', manifest(output/'published_cheq'))
    write(output/'ROBOT_ASSET_HASHES.json', asset_hashes)
    packages = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode()
    (output/'requirements.lock.txt').write_text(packages)
    write(output/'RUNTIME.json', dict(
        schema='sii-published-compliance-source-runtime-v1',
        created_utc=datetime.now(timezone.utc).isoformat(), host=platform.node(),
        python=sys.executable, python_version=platform.python_version(),
        mujoco_version=mujoco.__version__, source_commit=git('rev-parse', 'HEAD'),
        source_worktree_status=git('status', '--porcelain'),
        source_snapshot_manifest_sha256=sha(output/'SOURCE_HASHES.json'),
        baseline_commit=BASELINE, original_controller_sha256=original_hash,
        controller_repairs='existing main baseline_repair_controllers_20261008.py',
        parameter_manifest_sha256=sha(output/'PARAMETER_HASHES.json'),
        published_repository='https://github.com/Data-Science-in-Mechanical-Engineering/polishing-cheq',
        published_commit=CHEQ, published_manifest_sha256=sha(output/'CHEQ_HASHES.json'),
        menagerie=str(menagerie), menagerie_commit=git('rev-parse', 'HEAD', cwd=menagerie),
        menagerie_manifest_sha256=sha(output/'ROBOT_ASSET_HASHES.json'),
        requirements_sha256=sha(output/'requirements.lock.txt'),
        historical_mjb_recovered=False, historical_esn_checkpoint_recovered=False,
        physics_dt_s=.00005, actor_period_s=.04, horizon_s=55.,
        status='source_runtime_prepared_not_physics_or_learning_validated',
        scope='New common task cohort must be frozen before training; historical results are not paired with this runtime'))
    print(json.dumps(dict(output=str(output), source_files=len(manifest(source)),
                          robot_asset_files=len(asset_hashes))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--menagerie', type=Path, required=True)
    parser.add_argument('--published-cheq', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.output.resolve(), args.menagerie.resolve(), args.published_cheq.resolve())
