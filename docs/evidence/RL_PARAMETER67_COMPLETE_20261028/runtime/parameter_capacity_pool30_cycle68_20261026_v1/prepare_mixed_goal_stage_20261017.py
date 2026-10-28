"""Prepare a unique four-family continuation from mixed exact checkpoints.

This handles a finite stage that stopped at an episode boundary before all
families were dispatched.  It preserves the stopped stage and records the
per-family parent execution/checkpoint lineage explicitly.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


GIB = 1024 ** 3


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    tmp.replace(path)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def manifest(folder):
    folder = Path(folder)
    return {str(p.relative_to(folder)): digest(p) for p in sorted(folder.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}


def checkpoint(execution):
    assert execution['status'] == 'complete'
    assert execution['rows'] and execution['checkpoint_rows']
    cp = execution['checkpoint_rows'][-1]
    assert cp['step'] == execution['steps']
    assert execution['stop_reason'] == 'requested'
    return cp


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--stage03', type=Path, required=True)
    p.add_argument('--stage02', type=Path, required=True)
    p.add_argument('--destination', type=Path, required=True)
    args = p.parse_args()
    stage03 = args.stage03.resolve(); stage02 = args.stage02.resolve(); dest = args.destination.resolve()
    assert not dest.exists(), 'Never reuse a stage directory'
    reg03 = read(stage03 / 'REGISTRATION.json')
    reg02 = read(stage02 / 'REGISTRATION.json')
    state03 = read(stage03 / 'execution.json')
    assert state03['status'] == 'stopped_at_episode_boundary'
    assert state03.get('reason') == 'requested'
    assert len(reg03['jobs']) == len(reg02['jobs']) == 4
    by03 = {j['name']: j for j in reg03['jobs']}
    by02 = {j['name']: j for j in reg02['jobs']}
    assert set(by03) == set(by02)
    stage02_cps = {}
    for job in reg02['jobs']:
        if job['name'] == 'direct_task_safety':
            continue
        execution = read(Path(job['output']) / 'execution.json')
        assert execution['status'] == 'complete'
        assert execution['stop_reason'] == 'step_budget'
        cp = execution['checkpoint_rows'][-1]
        assert cp['step'] == 23375 and cp['episode'] == execution['episodes']
        stage02_cps[job['name']] = cp
    direct = read(stage03 / 'direct_task_safety' / 'execution.json')
    direct_cp = checkpoint(direct)
    assert direct_cp['step'] == 29512

    dest.mkdir(parents=True)
    shutil.copytree(stage03 / 'source', dest / 'source', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copytree(stage03 / 'parameter_n25', dest / 'parameter_n25', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    reg = deepcopy(reg03)
    started = datetime.now(timezone.utc)
    source = dest / 'source'; parameter = dest / 'parameter_n25'
    jobs = []
    parent_lineage = {}
    for old in reg03['jobs']:
        name = old['name']
        if name == 'direct_task_safety':
            cp = direct_cp
            parent_root = stage03
            parent_execution = stage03 / 'direct_task_safety' / 'execution.json'
        else:
            cp = stage02_cps[name]
            parent_root = stage02
            parent_execution = stage02 / name / 'execution.json'
        new = dict(old)
        new.update(
            inherited_steps=cp['step'],
            limit=cp['step'] + 11000,
            checkpoint=cp['path'],
            checkpoint_hashes=cp['hashes'],
            output=str(dest / name),
            unit='sii-rl-goal-' + hashlib.sha256(str(dest / name).encode()).hexdigest()[:12],
            parent_execution_sha256=digest(parent_execution),
            credit_migration=False,
            backend_migration=True,
        )
        jobs.append(new)
        parent_lineage[name] = dict(root=str(parent_root), execution_sha256=digest(parent_execution),
                                    checkpoint=cp)

    # Include this preparation tool in the immutable runtime snapshot.
    current_tool = Path(__file__)
    shutil.copy2(current_tool, source / 'tools' / current_tool.name)
    reg.update(
        registered_utc=started.isoformat(),
        run_root=str(dest), source=str(source), parameter_source=str(parameter),
        source_manifest=manifest(source), parameter_manifest=manifest(parameter),
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source.parents[4], text=True).strip(),
        source_worktree_state='Mixed exact-checkpoint continuation; stopped stage and all parent receipts retained.',
        dispatch_deadline_utc=(started + timedelta(hours=24)).isoformat(),
        stop_file=str(dest / 'STOP_REQUESTED'), jobs=jobs,
        coordinator_unit='sii-rl-goal-stage-' + hashlib.sha256(str(dest).encode()).hexdigest()[:12],
        preflight_required_jobs=[j['name'] for j in jobs],
        new_interactions_per_family=11000, maximum_new_interactions=44000,
        previous_mixed_stage=dict(stage03=str(stage03), stage03_execution_sha256=digest(stage03 / 'execution.json'),
                                  stage02=str(stage02), stage02_registration_sha256=digest(stage02 / 'REGISTRATION.json')),
        parent_checkpoint_lineage=parent_lineage,
        evidence_basis='Finite mixed continuation after disk-reserve stop at a closed episode boundary; no episode is replayed.',
    )
    reg.pop('LAUNCH', None)
    write(dest / 'REGISTRATION.json', reg)
    print(json.dumps(dict(destination=str(dest), coordinator=reg['coordinator_unit'],
                          jobs=[dict(name=j['name'], inherited_steps=j['inherited_steps'], limit=j['limit'],
                                     checkpoint=j['checkpoint']) for j in jobs]),
                     indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
