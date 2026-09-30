"""Frozen classical search followed by shared validation; never select on validation."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = {'fr3_link0', 'fr3_link1', 'fr3_link2', 'fr3_link3', 'fr3_link4'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def candidates():
    result = []
    for family, stiffnesses in [('impedance', (300, 600, 900, 1200)),
                               ('admittance', (60, 95, 150, 240))]:
        for stiffness in stiffnesses:
            for zeta in (.7, 1.2):
                parameters = dict(stiffness=stiffness, zeta=zeta)
                if family == 'impedance':
                    parameters.update(rot_stiffness=stiffness/20, mass=1., inertia=.08,
                                      nullspace_damping=2.)
                else:
                    parameters.update(rot_stiffness=4*stiffness/95, mass=.55, inertia=.065)
                result.append(dict(id=f'{family}_k{stiffness}_z{zeta}', family=family,
                                   parameters=parameters))
    return result


def validation_fixtures():
    triples = [(-.125, .5775, .0925), (-.125, .5825, .1075),
               (0., .5775, .1075), (0., .5825, .0925),
               (.075, .5775, .0925), (.075, .5825, .1075)]
    return [dict(seed=9400+i, push_angle=a, push_height=h, payload_mass=m)
            for i, (a, h, m) in enumerate(triples)]


def average_ranks(values):
    values = np.asarray(values)
    return np.array([1 + np.sum(values < v) + .5*(np.sum(values == v)-1) for v in values])


def verify_model_pairing(rows):
    by_fixture = {}
    for row in rows:
        if 'execution_error' in row:
            raise ValueError('Cannot verify model pairing for an execution failure')
        by_fixture.setdefault(row['fixture']['seed'], set()).add(row['model_mjb_sha256'])
    if any(len(hashes) != 1 for hashes in by_fixture.values()):
        raise ValueError('Compiled physical model differs between paired methods')


def select(rows, configurations, fixtures):
    """Require the entire predeclared budget; failed executions cannot win."""
    expected = {(c['id'], f['seed']) for c in configurations for f in fixtures}
    actual = [(r['candidate']['id'], r['fixture']['seed']) for r in rows]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError('Incomplete or duplicate development matrix')
    if any('execution_error' in r for r in rows):
        raise ValueError('Execution failures: preserve results and fix before selection')
    selections = {}
    for family in ('impedance', 'admittance'):
        scores = []
        for cfg in [c for c in configurations if c['family'] == family]:
            part = [r for r in rows if r['candidate']['id'] == cfg['id']]
            metrics = np.mean([[r['tracking_rmse_25hz_m'], r['actuator_torque_peak_nm'],
                                r['linear_speed_peak_substep_mps']] for r in part], axis=0)
            if not np.isfinite(metrics).all():
                raise ValueError('Nonfinite candidate metrics')
            scores.append(dict(candidate=cfg, strict_success=sum(r['strict_success'] for r in part),
                               task_success=sum(r['task_success'] for r in part), means=metrics.tolist()))
        matrix = np.asarray([s['means'] for s in scores])
        ranks = sum(average_ranks(matrix[:, j]) for j in range(3))
        for score, rank in zip(scores, ranks):
            score['metric_rank_sum'] = float(rank)
        ordered = sorted(scores, key=lambda s: (-s['strict_success'], -s['task_success'],
                                                s['metric_rank_sum'], s['candidate']['id']))
        selections[family] = dict(selected=ordered[0]['candidate'], scores=ordered,
                                  reliable_on_all_development_conditions=ordered[0]['strict_success'] == len(fixtures))
    return selections


def run_job(candidate, fixture, protocol, menagerie, output):
    job = output / candidate['id'] / str(fixture['seed'])
    job.mkdir(parents=True)
    stem = job / 'rollout' / 'rollout'
    family = candidate['family']
    classical = family in ('impedance', 'admittance')
    runner = (ROOT/'scripts'/f'run_panel_{family}_reference_20260923.py') if classical else (
        ROOT/'scripts'/'run_panel_push_20260920.py')
    params = {k: v for k, v in protocol['reference'].items()
              if v is not None and k not in ('output', 'render', 'settle_only', 'model')}
    params.update(fixture, scene='push', event_stage='loaded_lift', duration=24.,
                  menagerie=str(menagerie), mixture=0., teacher_profile='memory',
                  teacher_force_source='estimated', output=str(stem))
    if family in ('esn', 'mlp'):
        params['model'] = protocol['models'][family]['path']
    command = [sys.executable, str(ROOT/'scripts/run_with_substep_metrics_20260923.py'),
               '--runner', str(runner), '--metrics-output', str(job/'metrics'), '--']
    for key, value in params.items():
        command.extend(['--'+key.replace('_', '-'), str(value)])
    prefix = '--reference-' if family == 'impedance' else '--classical-'
    for key, value in candidate['parameters'].items():
        command.extend([prefix+key.replace('_', '-'), str(value)])
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
               MUJOCO_GL='egl', PANELS_ENABLED='1', UNIFIED_6D_TEACHER='1',
               PRIMITIVE_RUNNER_PATH=str(ROOT/'scripts/run_primitive_teacher_v7_20260917.py'),
               CORE_VMC_CONFIG=json.dumps(protocol['vmc']),
               PANEL_CONFIG=json.dumps(dict(protocol['panel'], rod_height_m=fixture['push_height'])))
    record = dict(candidate=candidate, fixture=fixture, command=command,
                  environment={k: env[k] for k in ('PANELS_ENABLED', 'UNIFIED_6D_TEACHER',
                      'PRIMITIVE_RUNNER_PATH', 'CORE_VMC_CONFIG', 'PANEL_CONFIG')})
    (job/'command.json').write_text(json.dumps(record, indent=2)+'\n')
    try:
        with (job/'run.log').open('w') as log:
            done = subprocess.run(command, cwd=ROOT, env=env, stdout=log,
                                  stderr=subprocess.STDOUT, timeout=3600)
        if done.returncode:
            raise RuntimeError(f'Runner exit {done.returncode}')
        result = json.loads(stem.with_suffix('.json').read_text())
        audit = json.loads((job/'metrics/audit_manifest.json').read_text())
        if audit['error'] or not audit['enabled'] or len(audit['episodes']) != 1:
            raise ValueError('Missing or ambiguous physical audit')
        physical = audit['episodes'][0]
        if physical['samples'] < int(23.99/physical['timestep_s']):
            raise ValueError('Incomplete physical substep trace')
        with np.load(stem.with_suffix('.npz'), allow_pickle=False) as trace:
            if trace['observation'].shape != (600, 48):
                raise ValueError('Unexpected observation contract or duration')
            rmse = float(np.sqrt(np.mean(np.sum((trace['position']-trace['target'])**2, axis=1))))
        contacts = result['panel_audit']['contacts']
        external = [v for k, v in contacts.items() if k != 'target_object_geom']
        upstream = any(set(v['bodies']) & UPSTREAM for v in external)
        record.update(task_success=bool(result['success']),
                      strict_success=bool(result.get('accepted_panel_demo') and not upstream),
                      upstream=upstream, tracking_rmse_25hz_m=rmse,
                      actuator_torque_peak_nm=physical['generalized_actuator_torque_peak_nm'],
                      linear_speed_peak_substep_mps=physical['linear_speed_peak_mps'],
                      endpoint_error_m=result['endpoint_error_m'],
                      max_penetration_mm=1000*max(v['max_penetration_m'] for v in external),
                      rod_contact_s=contacts['push_rod_geom']['duration_s'],
                      result=str(stem.with_suffix('.json')), result_sha256=digest(stem.with_suffix('.json')),
                      model_mjb_sha256=digest(stem.with_suffix('.mjb')), physical=physical)
        if not np.isfinite([record[k] for k in ('tracking_rmse_25hz_m', 'actuator_torque_peak_nm',
                                               'linear_speed_peak_substep_mps')]).all():
            raise ValueError('Nonfinite metrics')
    except Exception as exc:
        record['execution_error'] = f'{type(exc).__name__}: {exc}'
        record['log'] = str(job/'run.log')
    (job/'result.json').write_text(json.dumps(record, indent=2, allow_nan=False)+'\n')
    return record


def matrix(configurations, fixtures, protocol, args, directory):
    rows = []
    directory.mkdir(parents=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_job, c, f, protocol, args.menagerie, directory)
                   for c in configurations for f in fixtures]
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            (directory/'results.json').write_text(json.dumps(rows, indent=2, allow_nan=False)+'\n')
            print(json.dumps(dict(phase=directory.name, completed=len(rows), total=len(futures),
                                  candidate=row['candidate']['id'], seed=row['fixture']['seed'],
                                  error=row.get('execution_error'), strict_success=row.get('strict_success'))), flush=True)
    (directory/'FINAL_RESULT.json').write_text(json.dumps(dict(rows=rows), indent=2, allow_nan=False)+'\n')
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base-protocol', type=Path, required=True)
    p.add_argument('--menagerie', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--workers', type=int, default=4)
    p.add_argument('--plan-only', action='store_true')
    args = p.parse_args()
    if not 1 <= args.workers <= 4:
        raise ValueError('Workers must be between 1 and 4')
    if args.output.exists():
        raise FileExistsError('Use a fresh output directory; no silent resume/overwrite')
    protocol = json.loads(args.base_protocol.read_text())
    if protocol['observation'] != 'proprio48' or [f['seed'] for f in protocol['fixtures']] != [9300,9301,9302]:
        raise ValueError('Expected original panel48 development protocol')
    configurations = candidates()
    manifest = dict(scope='fixed-budget development search and predeclared same-layout validation; not office blind test',
                    base_protocol_sha256=digest(args.base_protocol), candidates=configurations,
                    development_fixtures=protocol['fixtures'], validation_fixtures=validation_fixtures(),
                    selection='max strict passes; max task passes; min sum average metric ranks; lexicographic id',
                    development_episodes=48, validation_episodes=30,
                    specification_sha256=digest(ROOT/'docs/CLASSICAL_TUNING_PROTOCOL_20260923.md'),
                    source_sha256={f.name: digest(f) for f in sorted((ROOT/'scripts').glob('*.py'))},
                    frozen_models=protocol['models'], plan_only=args.plan_only)
    args.output.mkdir(parents=True)
    (args.output/'protocol.json').write_text(json.dumps(manifest, indent=2, allow_nan=False)+'\n')
    if args.plan_only:
        print(f'Frozen plan: {args.output}/protocol.json; no simulation started')
        return
    for value in protocol['models'].values():
        if digest(value['path']) != value['sha256']:
            raise ValueError('Frozen model changed')
    rows = matrix(configurations, protocol['fixtures'], protocol, args, args.output/'development')
    verify_model_pairing(rows)
    selection = select(rows, configurations, protocol['fixtures'])
    (args.output/'selection.json').write_text(json.dumps(selection, indent=2, allow_nan=False)+'\n')
    validation = [selection[f]['selected'] for f in ('impedance','admittance')]
    validation += [dict(id=f, family=f, parameters={}) for f in ('vmc','mlp','esn')]
    validation_rows = matrix(validation, validation_fixtures(), protocol, args, args.output/'validation')
    if any('execution_error' in row for row in validation_rows):
        raise RuntimeError('Validation has execution errors; raw failures preserved, no COMPLETE marker')
    verify_model_pairing(validation_rows)
    (args.output/'COMPLETE.json').write_text(json.dumps(dict(development_episodes=48, validation_episodes=30,
                                               selection_sha256=digest(args.output/'selection.json')))+'\n')


if __name__ == '__main__':
    main()
