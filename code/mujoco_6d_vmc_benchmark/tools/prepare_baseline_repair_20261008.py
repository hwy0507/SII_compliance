"""Register the user-authorized 15h repair campaign before new rollouts."""
import argparse
import json
from pathlib import Path
import random
import shutil
from office_v7_uniform24_20261008 import sha, write, now, FORMAL, PARAMETER

START = '2026-10-08T13:23:12+00:00'
TRAIN_END = '2026-10-08T23:23:12+00:00'
END = '2026-10-09T04:23:12+00:00'
BASE = 'd5627f49a94651962bdb3f0c5a75c4b503c325ab'
BOUNDS = dict(ball_speed=(1.305, 1.595), person_start=(4., 5.), rod_start=(13.5, 14.5),
              person_stroke=(.18, .22), rod_stroke=(.2115, .2585), rod_hold=(4.5, 5.5))


def sample(seed, role, count):
    rng = random.Random(seed)
    columns = {}
    for key, (lo, hi) in BOUNDS.items():
        values = [round(lo+(hi-lo)*(i+rng.random())/count, 6) for i in range(count)]
        rng.shuffle(values); columns[key] = values
    rows = []
    for i in range(count):
        v = {k:x[i] for k,x in columns.items()}
        v.update(ball_launch_time_s=2., interaction_schedule='legacy', events='all', duration=55.,
                 seed=2026091751, planned_hand_corner=True, unexpected_edge=True,
                 combined_thick_corner_pillar_v4=True, allow_lateral_rejoin=True)
        assert v['rod_start']-v['person_start']-7. >= 1.5
        rows.append(dict(id=f'repair_{role}_{i:03d}', role=role, overrides=v))
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--history', type=Path, default=Path('/home/arm1/sii_shared/SII_compliance/runs/main/office_v7_uniform24_20261008'))
    a = p.parse_args(); root = a.root.resolve(); root.mkdir(parents=True, exist_ok=False)
    source = root/'source_v1'
    shutil.copytree(a.history/'source', source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('baseline_repair_controllers_20261008.py', 'baseline_repair_worker_20261008.py',
                 'test_baseline_repair_20261008.py', Path(__file__).name, 'run_baseline_repair_screen_20261008.py',
                 'baseline_repair_online_worker_20261008.py', 'train_baseline_repair_rl_20261008.py',
                 'baseline_repair_rl_diagnostics_20261008.py', 'test_baseline_repair_rl_20261008.py'):
        shutil.copy2(Path(__file__).with_name(name), source/'tools'/name)
    parameter = root/'parameter_v1'
    shutil.copytree(PARAMETER, parameter, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copy2(parameter/'controllers.py', parameter/'controllers_legacy.py')
    shutil.copy2(Path(__file__).with_name('baseline_repair_controllers_20261008.py'), parameter/'baseline_repair_controllers_20261008.py')
    (parameter/'controllers.py').write_text('"""Explicit v1 repaired adapter; historical implementation kept beside it."""\nfrom baseline_repair_controllers_20261008 import *\n')
    models = json.loads((a.history/'MODEL_MANIFEST.json').read_text())
    priors = json.loads((parameter/'PRIORS.json').read_text())
    for method in ('vmc', 'admittance', 'impedance'):
        chosen = next(c for c in models['candidates'] if c['family'] == 'classical_'+method)
        priors['methods'][method]['center'] = chosen['config']['parameters']
    priors['selection'] = 'Previous development-selected centers, explicit interface repair; new candidates separately registered'
    write(parameter/'PRIORS.json', priors)
    conditions = sample(202610081501, 'train', 32) + sample(202610081502, 'development', 8)
    # This diagnostic retains the MJB, target, planner and all physical limits.
    # Only active disturbances are off; remaining static contacts are reported.
    acceptance = dict(conditions[0]['overrides'], events='settle')
    conditions.append(dict(id='repair_acceptance_000', role='acceptance', overrides=acceptance))
    write(root/'CONDITIONS.json', dict(conditions=conditions))
    (root/'sealed').mkdir()
    write(root/'sealed/HELDOUT.json', dict(conditions=sample(202610081503, 'final', 24)))
    (root/'sealed/HELDOUT.json').chmod(0o400)
    write(root/'REFERENCE_MODELS.json', models)
    write(root/'teacher.json', next(c for c in models['candidates'] if c['family']=='enhanced_teacher')['config'])
    write(root/'PROTOCOL.json', dict(schema='sii-baseline-repair-15h-v1', registered_utc=now(),
        authorization='User grants 15 hours to fix baseline problems and rerun fair comparisons; local and Spark compute authorized; no recurring automation.',
        authorization_start_utc=START, training_dispatch_deadline_utc=TRAIN_END, dispatch_deadline_utc=END,
        time_basis='Clock at start of this user turn. Ten hours repair/development/training, five hours reserved for freeze/evaluation/audit. Finish in-flight episodes; no new dispatch after cutoff.',
        source_base_commit=BASE, baseline_commit='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',
        formal_model_sha256=FORMAL, physics_dt_s=.00005, duration_s=55.,
        condition_file_sha256=sha(root/'CONDITIONS.json'), sealed_condition_sha256=sha(root/'sealed/HELDOUT.json'),
        reference_models_sha256=sha(root/'REFERENCE_MODELS.json'), distribution=BOUNDS,
        unchanged=['MJB geometry/contact/friction', 'planner/target', 'task and strict gates', 'actor canonical48 proprioceptive fields', 'actuator amplitude/slew', 'common action filter'],
        controller_repairs=['VMC physical action units match decoder', 'projected impedance equilibrium, bounded nominal/torque-equivalent commands', 'model friction feedforward and nullspace posture, explicitly logged'],
        development_acceptance='Active-disturbance-off diagnostic, same static MJB. Require lift/progress and safety, not counted as full complex-task success or absent-static-contact claim.',
        budgets=dict(classical_candidates_per_family=24, screen_conditions=2, confirmation_top_per_family=2,
            confirmation_conditions=8, training_seeds=[2026100811,2026100812], rl_steps_per_family_seed=200000,
            rl_families=['parameter_vmc','parameter_admittance','parameter_impedance','direct_metric','direct_office_task']),
        selection='Development only: strict count, task count, full/physically-valid count, stage progress, penetration, RMSE and torque. Finite search is not proof of globally optimal baseline.',
        final='Freeze before reading new final24; all16 existing families, all failures retained. Additional algorithms or warmstarts require separately named registered rows; never relabel BC as pure RL.',
        training_fairness='Disclose teacher data, prior exposure, interaction/gradient/search budgets and architecture separately; common evaluation does not imply equal training history.',
        resources=dict(spark_max_new_simulators=10, spark_cpu_affinity='5-9,15-19', local_max_simulators=1,
            threads_per_worker=1, memory_max_per_worker='3GiB', memory_swap_max=0,
            authorization='Current all-compute request supersedes previous four/eight-way scope for this new run; preserve paused historical jobs'),
        completion='Report repaired implementations, all-method results and unresolved limits honestly; never require ESN to win. No physical hardware claims.'))
    rng = random.Random(202610081504); candidates = []
    for method in ('vmc', 'admittance', 'impedance'):
        prior = priors['methods'][method]
        vectors = [prior['center']]
        if method == 'impedance':
            vectors += [[k, 45., 1.4, 1.4, 1.] for k in (450., 900., 1500.)]
        while len(vectors) < 24:
            vectors.append([lo*(hi/lo)**rng.random() for lo,hi in prior['bounds']])
        for i, theta in enumerate(vectors):
            candidates.append(dict(name=f'{method}_{i:02d}', method=method, parameters=theta))
    write(root/'CLASSICAL_CANDIDATES.json', dict(seed=202610081504, candidates=candidates))
    write(root/'SOURCE_V1_HASHES.json', {str(f.relative_to(source)):sha(f) for f in source.rglob('*') if f.is_file()})
    write(root/'PARAMETER_V1_HASHES.json', {str(f.relative_to(parameter)):sha(f) for f in parameter.rglob('*') if f.is_file()})
    write(root/'execution.json', dict(status='registered', started_utc=now(), protocol_sha256=sha(root/'PROTOCOL.json')))
    print(json.dumps(dict(root=str(root), protocol_sha256=sha(root/'PROTOCOL.json'), source=str(source), parameter_source=str(parameter))))


if __name__ == '__main__':
    main()
