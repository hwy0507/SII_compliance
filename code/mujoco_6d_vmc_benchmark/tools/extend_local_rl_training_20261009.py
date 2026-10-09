"""Finite local checkpoint continuation with audited development learning curves.

Wait for the immutable 11k campaign and its independent final audit, then acquire
its SAME compute lock. No scheduler, remote compute, reward changes or final-test
access. A failed learning plateau requests scientific review, never 'convergence'.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import fcntl
import hashlib
import os
from pathlib import Path
import platform
import queue
import shutil
import subprocess
import sys
import threading
import time

import local_rl_campaign_20261009 as campaign
from office_v7_uniform24_20261008 import read, write, sha, now


def assess(history):
    """Operational development screen, not statistical or multi-seed convergence."""
    assert history and all(r['completed'] == 8 for r in history)
    assert all(0 <= r['strict'] <= r['task'] <= 8 for r in history)
    recent = history[-3:]
    candidate = (len(recent) == 3 and recent[-1]['steps']-recent[0]['steps'] >= 22000
                 and all(r['task'] >= 7 and r['strict'] >= 6 for r in recent)
                 and max(r['strict'] for r in recent)-min(r['strict'] for r in recent) <= 1)
    # Two post-diagnostic checkpoints across substantial additional exposure.
    extended = [r for r in history if r['steps'] >= 55000]
    stalled = (len(extended) >= 2 and all(r['task'] == 0 for r in extended[-2:]))
    return dict(candidate_usable_and_stable=candidate,
                zero_task_learning_stall=stalled,
                converged=False, final_comparison_authorized=False,
                next_step=('independent_seed_confirmation' if candidate else
                           'reward_exploration_control_review' if stalled else 'continue_training'))


def require_complete_training(state, checkpoint_limit):
    assert state['status'] == 'complete'
    assert state['stop_reason'] == 'step_budget', 'Deadline/interruption is not a completed budget'
    # An aborted episode may leave less than one whole episode of budget.
    assert checkpoint_limit-1375 < state['steps'] <= checkpoint_limit
    assert state['checkpoint_rows'][-1]['step'] == state['steps']
    assert all('result' in row for row in state['rows'])


def prepare(root, out):
    assert platform.node() == 'airpig'
    assert not out.exists()
    protocol = read(root/'PROTOCOL.json')
    assert campaign.hashes(root/'source') == read(root/'SOURCE_HASHES.json')
    assert campaign.hashes(root/'parameter_fullrange') == read(root/'PARAMETER_HASHES.json')
    out.mkdir(parents=True)
    shutil.copytree(Path(__file__).resolve().parent, out/'source/tools',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    registration = dict(schema='sii-local-rl-extended-training-v1', registered_utc=now(),
        authorization='2026-10-09 user: continue RL training until a usable converged policy before comparison',
        parent_root=str(root), parent_protocol_sha256=sha(root/'PROTOCOL.json'),
        compute_host='airpig', server_compute=False, max_simulators=2,
        memory_max_per_lane=3*1024**3, memory_swap_max=0, numerical_threads=1,
        coordinator_memory_max=1024**3, admission_available_memory_gib=7,
        condition_file_sha256=sha(root/'CONDITIONS.json'), jobs=protocol['jobs'],
        cumulative_interaction_checkpoints=[55000,110000,220000,499125],
        maximum_additional_interactions=7*(499125-11000),
        initial_next_stage_additional_interactions=7*(55000-11000),
        original_optimizer_schedule_steps=500000,
        dispatch_deadline_utc=protocol['training_dispatch_deadline_utc'],
        deadline_basis='Inherited operational fail-safe, not a new user time limit and not a convergence criterion; review and register continuation if reached',
        resume='Preserve actor/critic/targets/temperature/normalizers/optimizer/replay/RNG; same reward and scientific protocol',
        unchanged=['formal MJB and dt5e-5','32train/8development identities','canonical48 actor fields',
                   'actuator amplitude and slew','Task/Strict gates','no teacher labels or BC'],
        readiness=dict(task_at_least=7, strict_at_least=6, denominator=8,
            consecutive_checkpoints=3, strict_count_range_at_most=1,
            interpretation='Operational usability screen only; three-seed confirmation and learning-curve review still required, never final-test ranking'),
        failed_plateau='If all seven settings have zero Task at two consecutive >=55k checkpoints, stop blind dispatch for scientific reward/exploration/control review, not convergence',
        terminal_policy='No final evaluation dispatched. A finite segment is part of ongoing baseline development, not goal completion.',
        archive='All raw failures retained locally; stage-boundary storage checks; server only receives separately verified files',
        source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).parent,text=True).strip())
    write(out/'REGISTRATION.json',registration)
    write(out/'SOURCE_HASHES.json',campaign.hashes(out/'source'))
    print('Registered:', out, 'sha256:', sha(out/'REGISTRATION.json'))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--extension', type=Path, required=True)
    p.add_argument('--prepare', action='store_true')
    a = p.parse_args(); root = a.root.resolve(); out = a.extension.resolve()
    if a.prepare: prepare(root,out); return
    registration = read(out/'REGISTRATION.json')
    assert platform.node() == registration['compute_host'] == 'airpig'
    assert str(root) == registration['parent_root']
    assert sha(root/'PROTOCOL.json') == registration['parent_protocol_sha256']
    assert campaign.hashes(out/'source') == read(out/'SOURCE_HASHES.json')
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'))
    deadline = datetime.fromisoformat(registration['dispatch_deadline_utc'])
    protocol = read(root/'PROTOCOL.json')
    assert deadline == datetime.fromisoformat(protocol['training_dispatch_deadline_utc'])
    assert registration['jobs'] == protocol['jobs']
    assert registration['cumulative_interaction_checkpoints'] == [55000, 110000, 220000, 499125]
    assert registration['max_simulators'] == 2
    assert not (out/'execution.json').exists(), 'Preserve an interrupted attempt; recover explicitly'
    execution = dict(status='waiting_for_parent', started_utc=now(), host=platform.node(),
        registration_sha256=sha(out/'REGISTRATION.json'), rounds=[], failures=[],
        latest_parent=None, server_compute=False, final_test_reads=0)
    guard = threading.Lock(); stop = threading.Event(); lane_state = threading.local()
    lock = None

    def save():
        execution['updated_utc'] = now(); write(out/'execution.json', execution)

    def check_budget():
        if datetime.now(timezone.utc) >= deadline:
            raise RuntimeError('Dispatch safety deadline: preserve checkpoints; no convergence claim')
        if shutil.disk_usage(root).free < 40*1024**3:
            raise RuntimeError('Less than40GiB disk free: preserve all failures and request archival review')

    def managed(directory, label, argv):
        check_budget()
        assert not stop.is_set(), 'Another lane failed; no new dispatch'
        receipt = directory/(label+'.execution.json')
        if receipt.exists():
            existing = read(receipt)
            assert existing['status'] == 'complete' and existing['command'] == argv
            for name, digest in existing.get('artifacts', {}).items(): assert sha(name) == digest
            return
        unit = ('sii-local-rl-extend-'+str(lane_state.number)+'-'
                +hashlib.sha256((str(out)+label).encode()).hexdigest()[:12])
        command = ['systemd-run','--user','--wait','--pipe','--collect','--unit='+unit,
            '--property=MemoryMax=3G','--property=MemorySwapMax=0','--property=TasksMax=256',
            '--property=CPUAffinity='+['1,6','2,7'][lane_state.number],
            '--working-directory='+str(root/'source')]
        environment = dict(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
            MUJOCO_GL='egl', JAX_PLATFORMS='cuda', XLA_PYTHON_CLIENT_PREALLOCATE='false',
            XLA_PYTHON_CLIENT_MEM_FRACTION='0.12', SII_LOCAL_RUNTIME=protocol['runtime'],
            MUJOCO_MENAGERIE_PATH=str(Path(protocol['runtime'])/'menagerie'),
            SII_SOURCE_BASE_COMMIT=protocol['source_base_commit'])
        command += ['--setenv='+k+'='+v for k,v in environment.items()]+argv
        record = dict(status='running', started_utc=now(), command=argv, managed_command=command,
            host=platform.node(), lane=lane_state.number, extension_sha256=execution['registration_sha256'])
        write(receipt, record)
        with (directory/(label+'.log')).open('x') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                    pass_fds=(lock.fileno(),))
        artifacts = [root/label/'execution.json', root/label/'AUDIT.json']
        if '--output' in argv:
            target = Path(argv[argv.index('--output')+1])
            if target.is_file(): artifacts.append(target)
        record.update(status='complete' if result.returncode == 0 else 'failed_preserved',
            returncode=result.returncode, ended_utc=now(),
            artifacts={str(f):sha(f) for f in artifacts if f.is_file()})
        write(receipt, record)
        if result.returncode: raise RuntimeError('Failed preserved: '+str(receipt))

    save()
    try:
        while True:
            check_budget()
            parent = read(root/'parallel_v2.execution.json')
            observer = read(root/'monitor_v2/execution.json')
            execution['latest_parent'] = dict(coordinator=parent['status'], observer=observer['status'],
                                              completed=parent['completed'])
            save()
            if parent['status'] == 'failed_preserved' or observer['status'] == 'failed_preserved':
                raise RuntimeError('Parent failed; do not restart or bypass failed audit')
            if (parent['status'] == 'diagnostics_complete_review_required'
                    and observer['status'] == 'complete_review_required'):
                break
            time.sleep(30)
        parent_audit = root/'monitor_v2/FINAL_DEVELOPMENT_AUDIT.json'
        report = read(parent_audit)
        assert len(report['methods']) == len(protocol['jobs']) == 7
        assert all(m['all_development_complete'] for m in report['methods'])
        assert all(a['returncode'] == 0 for a in observer['audits'])
        assert sha(parent_audit) == observer['audits'][-1]['output_sha256']
        lock = (root.parent/'.local-rl-compute.lock').open('a')
        # The parent may still be exiting after publishing its final receipt.
        while True:
            check_budget()
            try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB); break
            except BlockingIOError: time.sleep(5)
        campaign.verify(root)
        while True:
            check_budget()
            available = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                                 if line.startswith('MemAvailable:')))
            if available >= 7*1024**2: break
            execution.update(status='waiting_for_memory', available_kib=available); save(); time.sleep(30)
        execution.update(status='running', parent_audit_sha256=sha(parent_audit), admitted_available_kib=available)
        save()
        campaign.command = managed
        histories = {m['method']:[dict(steps=11000, completed=m['completed'], task=m['task'], strict=m['strict'])]
                     for m in report['methods']}
        previous_suffix = 'segment011k'
        for limit in registration['cumulative_interaction_checkpoints']:
            check_budget()
            prior_limit = 11000 if previous_suffix == 'segment011k' else int(previous_suffix[8:])
            # Reserve the entire round before either lane starts. Retain raw
            # failures; never delete checkpoints to squeeze through a budget.
            required_bytes = (40*1024**3 + len(protocol['jobs'])
                              *((limit-prior_limit+1374)//1375)*256*1024**2)
            if shutil.disk_usage(root).free < required_bytes:
                execution.update(status='storage_review_required', required_bytes=required_bytes,
                                 ended_utc=now()); save(); return
            suffix = f'extended{limit:06d}'
            pending = queue.Queue()
            for job in protocol['jobs']: pending.put(job)
            stage = dict(limit=limit, suffix=suffix, started_utc=now(), completed=[])
            execution['rounds'].append(stage); save()

            def lane(number):
                lane_state.number = number
                while not stop.is_set():
                    try: job = pending.get_nowait()
                    except queue.Empty: return
                    try:
                        old = read(root/(job['name']+'_'+previous_suffix)/'execution.json')
                        previous_limit = 11000 if previous_suffix == 'segment011k' else int(previous_suffix[8:])
                        require_complete_training(old, previous_limit)
                        label = job['name']+'_'+suffix
                        cp = old['checkpoint_rows'][-1]['path']
                        managed(root, label, campaign.training_command(root, job, label, limit, cp))
                        trained = read(root/label/'execution.json'); require_complete_training(trained, limit)
                        if job['controller']:
                            for row in trained['rows']:
                                campaign.parameter_audit(root, str(Path(row['run']).relative_to(root)))
                        campaign.development(root, job, label)
                        with guard: stage['completed'].append(job['name']); save()
                    except BaseException as exc:
                        stop.set()
                        with guard: execution['failures'].append(dict(method=job['name'], error=repr(exc))); save()
                        return

            with ThreadPoolExecutor(max_workers=2) as pool: list(pool.map(lane, range(2)))
            if execution['failures']: raise RuntimeError('Stage failed; receipts and live-lane completion preserved')
            lane_state.number = 0
            audit_path = out/(suffix+'_development.json')
            managed(out, suffix+'_audit', [sys.executable,
                str(Path(__file__).with_name('audit_local_rl_development_20261009.py')),
                '--root',str(root),'--output',str(audit_path),'--training-suffix',suffix])
            report = read(audit_path)
            assert len(report['methods']) == 7 and all(m['all_development_complete'] for m in report['methods'])
            for m in report['methods']:
                actual = read(root/(m['method']+'_'+suffix)/'execution.json')['steps']
                histories[m['method']].append(dict(steps=actual, completed=m['completed'], task=m['task'], strict=m['strict']))
            decisions = {name:assess(values) for name,values in histories.items()}
            stage.update(ended_utc=now(), audit_sha256=sha(audit_path), decisions=decisions)
            write(out/'LEARNING_CURVES.json', dict(histories=histories, decisions=decisions,
                scope='Repeated development screening, not final test or independent-seed convergence'))
            save()
            if any(d['candidate_usable_and_stable'] for d in decisions.values()):
                execution['status'] = 'candidate_requires_seed_confirmation'; break
            if all(d['zero_task_learning_stall'] for d in decisions.values()):
                execution['status'] = 'learning_stalled_scientific_review_required'; break
            previous_suffix = suffix
        else: execution['status'] = 'budget_complete_not_converged_review_required'
        execution['ended_utc'] = now(); save()
    except BaseException as exc:
        execution.update(status='failed_preserved', error=repr(exc), ended_utc=now()); save(); raise


if __name__ == '__main__': main()
