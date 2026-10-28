"""Bounded local diagnostic positive controls; never final benchmark scores.

Keep the archived planner's exact routes, payload/support/robot properties,
gates, control rates and safety limits. Only after planning, disable explicitly
listed non-support obstacle collisions for a diagnostic fixture. Frozen-world
evaluation is a separate fixture. No obstacle information enters a controller.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def hashes(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and p.suffix in ('.py', '.json')}


DISABLED_NAMES = (
    'office_monitor_foot', 'office_monitor_stand', 'office_monitor_screen',
    'office_notebook', 'office_keyboard', 'office_v5_pillar',
    'office_v5_pillar_mount', 'office_v5_corner_face', 'office_v5_unexpected_edge',
    'office_v5_ball_geom', 'office_v5_person_torso', 'office_v5_person_head',
    'office_v5_person_leg_-1', 'office_v5_person_foot_-1',
    'office_v5_person_leg_1', 'office_v5_person_foot_1',
    'office_v5_upper_arm_geom', 'office_v5_forearm_geom', 'office_v5_human_palm',
    'office_v5_human_finger_0', 'office_v5_human_finger_1',
    'office_v5_human_finger_2', 'office_v5_human_finger_3',
    'office_v5_human_thumb', 'office_v5_push_rod_geom',
)


def disable_obstacles(model, fixture):
    import mujoco
    if fixture == 'frozen':
        return []
    assert fixture in ('clear', 'edge_only', 'active_only', 'events_off')
    if fixture == 'events_off':
        return []
    # Archived model has two explicit ball/support pairs. Keep these so the
    # inactive ball does not fall through the floor. No explicit robot/payload
    # obstacle pair may bypass the diagnostic masks.
    pairs = {(model.geom(int(a)).name, model.geom(int(b)).name)
             for a, b in zip(model.pair_geom1, model.pair_geom2)}
    assert pairs == {('office_floor', 'office_v5_ball_geom'),
                     ('office_desk_top', 'office_v5_ball_geom')}, pairs
    changed = []
    for name in DISABLED_NAMES:
        if fixture == 'edge_only' and name == 'office_v5_unexpected_edge':
            continue
        if fixture == 'active_only' and name in DISABLED_NAMES[9:]:
            continue
        i = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, name)
        assert i >= 0, name
        changed.append(dict(name=name, id=i, original_contype=int(model.geom_contype[i]),
                            original_conaffinity=int(model.geom_conaffinity[i])))
        model.geom_contype[i] = 0
        model.geom_conaffinity[i] = 0
    return changed


def worker(args, rest):
    import mujoco
    import numpy as np
    import paper_office_worker_20261002 as office
    import planned_hand_corner_20261002 as planner
    original_settings = office.evaluation_settings
    original_plan = planner.build_plan
    registration = read(args.root/'REGISTRATION.json')
    assert sha(args.root/'REGISTRATION.json') == args.registration_sha256
    condition = next(c for c in registration.get('conditions', [registration['condition']])
                     if c['id'] == args.condition)
    assert condition['role'] == 'development'
    output = Path(rest[rest.index('--output')+1])
    binary = args.runtime/'v6/construction/rollout.mjb'
    original_save = mujoco.mj_saveModel
    expected_model = mujoco.MjModel.from_binary_path(str(binary))
    expected_model.opt.timestep = .00005
    changes = disable_obstacles(expected_model, args.fixture)
    buffer = np.empty(mujoco.mj_sizeModel(expected_model), dtype=np.uint8)
    original_save(expected_model, None, buffer)
    expected = hashlib.sha256(buffer.tobytes()).hexdigest()

    def settings(v6, dt, condition_file=None, condition_id=None):
        assert dt == .00005 and condition_file is None and condition_id is None
        parent_hash, overrides, provenance = original_settings(v6, dt)
        assert parent_hash == registration['frozen_model_sha256']
        overrides.update(condition['overrides'])
        if args.fixture not in ('frozen', 'active_only'):
            overrides['events'] = 'settle'
        provenance.update(diagnostic_only=args.fixture != 'frozen', fixture=args.fixture,
            data_role='development_diagnostic', condition=condition,
            registration_sha256=args.registration_sha256, parent_model_sha256=parent_hash,
            model_sha256=expected, diagnostic_collision_changes=changes,
            interpretation='Clear/edge-only fixtures are positive controls, never comprehensive benchmark scores')
        return expected, overrides, provenance

    def plan(env, base, **kwargs):
        task, metadata = original_plan(env, base, **kwargs)
        # Planning always sees the original model. The same route, posture,
        # target and task gate are retained in every diagnostic variant.
        actual_changes = disable_obstacles(env.model, args.fixture)
        assert actual_changes == changes
        write(output/'DIAGNOSTIC_FIXTURE.json', dict(fixture=args.fixture,
            diagnostic_only=args.fixture != 'frozen', changes=changes,
            original_plan=metadata, plan_sha256=hashlib.sha256(
                json.dumps(metadata, sort_keys=True).encode()).hexdigest(),
            preserved=['robot', 'payload', 'support surfaces', 'planned route', 'gates',
                       'actor inputs', 'actuator limits', 'physical timestep']))
        return task, metadata

    office.evaluation_settings = settings
    planner.build_plan = plan
    original_main = office.worker.main

    def recorded_main():
        office.worker.EXTRA_SOURCE_FILES.append(Path(__file__))
        return original_main()

    office.worker.main = recorded_main
    sys.argv = [sys.argv[0], *rest]
    if args.controller == 'nominal':
        import research72_nominal_worker_20261003 as selected
    else:
        import paper_classical_worker_20261002 as selected
        sys.argv += ['--controller', args.controller, '--parameter-source', str(args.root/'parameter')]
    selected.main()


def prepare(args):
    assert platform.node() == 'airpig' and not args.root.exists()
    benchmark = Path(__file__).resolve().parents[1]
    history = args.runtime/'history'
    args.root.mkdir(parents=True)
    source = args.root/'source'
    shutil.copytree(history/'source_v9', source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in (Path(__file__).name, 'replay_repair_dynamic_controllers_20261009.py',
                 'audit_repair_parameter_trace_20261008.py', 'diagnose_classical_stall_20261010.py'):
        shutil.copy2(Path(__file__).with_name(name), source/'tools'/name)
    shutil.copytree(history/'parameter_v2', args.root/'parameter',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    conditions = read(history/'CONDITIONS.json')['conditions']
    condition = next(c for c in conditions if c['id'] == args.condition)
    assert condition['role'] == 'development'
    methods = args.methods
    jobs = [dict(name=f'{fixture}__{method}', fixture=fixture, controller=method)
            for fixture in args.fixtures for method in methods]
    reg = dict(schema='classical-local-acceptance-v1', registered_utc=now(),
        source_base_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=benchmark, text=True).strip(),
        authorization='2026-10-10 user: repair and substantiate traditional baselines; local compute only',
        runtime=str(args.runtime), condition=condition, source_hashes=hashes(source),
        parameter_hashes=hashes(args.root/'parameter'),
        frozen_model_sha256='d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3',
        physics_dt_s=.00005, duration_s=55., resources=dict(simulators=1, threads=1,
            memory_max_bytes=3*1024**3, swap_max_bytes=0, server_compute=False),
        jobs=jobs, max_episodes=len(jobs), final_test_reads=0,
        decision='Explicit finite diagnostic matrix; inspect results before registering tuning or further ablations. No automatic budget extension.',
        acceptance='Actual full-horizon Task success and preserved safety limits. Diagnostic success is not final task success.',
        disabled_collision_names=list(DISABLED_NAMES))
    write(args.root/'REGISTRATION.json', reg)
    write(args.root/'execution.json', dict(status='prepared', registered_utc=now(), completed=[]))
    print(args.root, sha(args.root/'REGISTRATION.json'), flush=True)


def run(args):
    assert platform.node() == 'airpig'
    reg = read(args.root/'REGISTRATION.json')
    assert hashes(args.root/'source') == reg['source_hashes']
    assert hashes(args.root/'parameter') == reg['parameter_hashes']
    lock_path = args.runtime.parent/'.local-rl-compute.lock'
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = dict(status='running', started_utc=now(), pid=os.getpid(), host=platform.node(),
                     registration_sha256=sha(args.root/'REGISTRATION.json'), completed=[])
        write(args.root/'execution.json', state)
        try:
            jobs = list(reg['jobs'])
            for job in jobs:
                if (args.root/'STOP_REQUESTED').exists():
                    state['status'] = 'stopped_at_safe_boundary'
                    break
                if shutil.disk_usage(args.root).free < 30*1024**3:
                    raise RuntimeError('Preserve 30 GiB free disk')
                out = args.root/job['name']
                receipt = args.root/(job['name']+'.execution.json')
                if receipt.exists():
                    row = read(receipt)
                    assert row['status'] == 'complete', 'Preserve failed/interrupted attempt'
                    assert sha(out/'AUDIT.json') == row['audit_sha256']
                    state['completed'].append(row)
                    if reg.get('confirmation_rule') and len(state['completed']) == len(reg['jobs']):
                        jobs.extend(confirmation_jobs(args.root, reg, state['completed']))
                    continue
                config = args.root/(job['name']+'.config.json')
                write(config, dict(parameters=job['parameters']) if 'parameters' in job else {})
                source = args.root/'source'
                command = [sys.executable, str(source/'tools'/Path(__file__).name), 'worker',
                    '--root', str(args.root), '--runtime', str(args.runtime),
                    '--fixture', job['fixture'], '--controller', job['controller'],
                    '--condition', job.get('condition_id', reg['condition']['id']),
                    '--registration-sha256', sha(args.root/'REGISTRATION.json'),
                    '--v6-input', str(args.runtime/'v6'), '--reference',
                    str(args.runtime/'v6/esn_original_v2/rollout.json'),
                    '--config', str(config), '--output', str(out), '--physics-dt', '.00005', '--contact-audit']
                env = dict(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
                    MUJOCO_GL='egl', JAX_PLATFORMS='cpu', SII_LOCAL_RUNTIME=str(args.runtime),
                    MUJOCO_MENAGERIE_PATH=str(args.runtime/'menagerie'),
                    SII_SOURCE_BASE_COMMIT=reg['source_base_commit'])
                unit = 'sii-classical-accept-'+hashlib.sha256(str(out).encode()).hexdigest()[:12]
                launch = ['systemd-run', '--user', '--wait', '--pipe', '--collect', '--unit='+unit,
                    '--property=MemoryMax=3G', '--property=MemorySwapMax=0', '--property=TasksMax=128',
                    '--property=CPUAffinity=1,6', '--working-directory='+str(source)]
                launch += ['--setenv='+k+'='+v for k, v in env.items()]
                row = dict(job=job, status='running', started_utc=now(), command=command, unit=unit)
                write(receipt, row)
                state['active'] = job
                write(args.root/'execution.json', state)
                with (args.root/(job['name']+'.log')).open('x') as log:
                    rc = subprocess.run(launch+command, stdout=log, stderr=subprocess.STDOUT).returncode
                row.update(returncode=rc, ended_utc=now())
                if rc:
                    row['status'] = 'failed_preserved'
                    write(receipt, row)
                    raise RuntimeError(job['name']+' failed; preserve attempt and inspect log')
                audit = read(out/'AUDIT.json')
                assert read(out/'execution.json')['status'] == 'complete'
                # A physical early abort is a retained algorithm outcome,
                # not an infrastructure error and not eligible as success.
                assert 0 < audit['physical_seconds'] <= 55.000001
                assert not audit['task_success'] or audit['full_horizon']
                checks = []
                scripts = []
                if job['controller'] != 'nominal':
                    scripts.append(('shield', 'audit_repair_parameter_trace_20261008.py'))
                if job['controller'] in ('vmc', 'admittance'):
                    scripts.append(('dynamic', 'replay_repair_dynamic_controllers_20261009.py'))
                for label, script in scripts:
                    target = args.root/(job['name']+'.'+label+'.json')
                    cmd = [sys.executable, str(source/'tools'/script), '--run', str(out),
                        '--parameter-source', str(args.root/'parameter'), '--output', str(target)]
                    audit_launch = [x if x != '--unit='+unit else '--unit='+unit+'-'+label for x in launch]
                    with (args.root/(job['name']+'.'+label+'.log')).open('x') as log:
                        rc = subprocess.run(audit_launch+cmd, stdout=log, stderr=subprocess.STDOUT).returncode
                    checks.append(dict(kind=label, command=cmd, returncode=rc))
                    if rc:
                        row.update(status='audit_failure_preserved', checks=checks)
                        write(receipt, row)
                        raise RuntimeError('Independent controller audit failed: '+job['name']+'/'+label)
                    assert read(target)['status'] == 'passed'
                    checks[-1]['sha256'] = sha(target)
                row.update(status='complete', audit=audit, audit_sha256=sha(out/'AUDIT.json'),
                           trace_sha256=sha(out/'rollout.npz'), checks=checks)
                write(receipt, row)
                state['completed'].append(row)
                state['active'] = None
                write(args.root/'execution.json', state)
                if reg.get('confirmation_rule') and len(state['completed']) == len(reg['jobs']):
                    jobs.extend(confirmation_jobs(args.root, reg, state['completed']))
            else:
                state['status'] = 'complete'
        except BaseException as exc:
            state.update(status='failed_preserved', error=repr(exc))
            raise
        finally:
            state['ended_utc'] = now()
            write(args.root/'execution.json', state)


def rank_candidates(reg, rows):
    """Completed physical failures stay in every score; no stage-name reward."""
    ranked = {}
    for method in ('vmc', 'admittance', 'impedance'):
        group = []
        for candidate in [c for c in reg['candidates'] if c['controller'] == method]:
            rr = [r for r in rows if r['job'].get('candidate') == candidate['name']]
            assert len(rr) == len(reg['screen_conditions'])
            assert {r['job']['condition_id'] for r in rr} == set(reg['screen_conditions'])
            assert all(r['status'] == 'complete' for r in rr)
            audits = [r['audit'] for r in rr]
            distances = [r['placement_error_xy_m'] if r['placement_error_xy_m'] is not None else 1e6 for r in audits]
            score = [sum(r['strict_success'] for r in audits), sum(r['task_success'] for r in audits),
                sum(r['full_horizon'] for r in audits), -max(distances), -sum(distances),
                -max(r['penetration_mm'] for r in audits), -sum(r['rmse_mm'] for r in audits),
                -sum(r['peak_torque_nm'] for r in audits)]
            group.append(dict(candidate=candidate, score=score))
        ranked[method] = sorted(group, key=lambda r: r['score'], reverse=True)
    return ranked


def confirmation_jobs(root, reg, rows):
    ranked = rank_candidates(reg, rows)
    jobs = []
    for method in ('vmc', 'admittance', 'impedance'):
        for row in ranked[method][:2]:
            c = row['candidate']
            for condition in reg['confirmation_conditions']:
                jobs.append(dict(name=c['name']+'__'+condition, candidate=c['name'],
                    controller=method, fixture='frozen', condition_id=condition, parameters=c['parameters']))
    selection = dict(registration_sha256=sha(root/'REGISTRATION.json'), ranked=ranked, jobs=jobs,
        rule=reg['confirmation_rule'], screen_receipt_hashes={r['job']['name']:sha(root/(r['job']['name']+'.execution.json')) for r in rows})
    path = root/'SELECTION.json'
    if path.exists():
        assert read(path) == selection
    else:
        write(path, selection)
    return jobs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('prepare', 'run', 'worker'))
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--runtime', type=Path, required=True)
    choices=('clear', 'edge_only', 'active_only', 'events_off', 'frozen')
    p.add_argument('--fixture', choices=choices)
    p.add_argument('--fixtures', nargs='+', choices=choices, default=['clear'])
    p.add_argument('--methods', nargs='+', choices=('nominal', 'vmc', 'admittance', 'impedance'),
                   default=['nominal', 'vmc', 'admittance', 'impedance'])
    p.add_argument('--condition', default='repair_development_000')
    p.add_argument('--controller', choices=('nominal', 'vmc', 'admittance', 'impedance'))
    p.add_argument('--registration-sha256')
    args, rest = p.parse_known_args()
    args.root = args.root.resolve()
    args.runtime = args.runtime.resolve()
    if args.mode == 'worker':
        worker(args, rest)
    else:
        assert not rest
        (prepare if args.mode == 'prepare' else run)(args)


if __name__ == '__main__':
    main()
