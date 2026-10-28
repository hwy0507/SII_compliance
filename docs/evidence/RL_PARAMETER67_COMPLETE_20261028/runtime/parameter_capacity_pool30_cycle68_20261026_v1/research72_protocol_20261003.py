"""Register the new finite research window and data identities before simulation.

This is a new authorization, not an extension of the finished twelve-hour study.
The sealed file is generated once; final workers will require a model lock.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import secrets

START = '2026-10-03T11:30:00+00:00'
END = '2026-10-06T11:30:00+00:00'
BASE = '33f438075649508ceb8f84479880d5d622f4eb4f'
BASELINE = 'ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6'
FIELDS = ('ball_speed', 'person_start', 'rod_start', 'person_stroke', 'rod_stroke')
LOW = (1.305, 3.5, 12.5, .18, .2115)
HIGH = (1.595, 4.5, 13.5, .22, .2585)
TEACHER = dict(recovery=dict(threshold_n=.5, attack_s=.12, release_s=1.,
    offset_m=.035, gain_per_s=4., velocity_mps=.12, activation_mode='progress', progress_distance_m=.02))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def sample(seed, groups):
    rng = random.Random(seed)
    rows = []
    for role, count in groups:
        for i in range(count):
            values = {k: round(rng.uniform(lo, hi), 6) for k, lo, hi in zip(FIELDS, LOW, HIGH)}
            assert values['rod_start'] - (values['person_start'] + 7.) >= 1.
            rows.append(dict(id=f'{role}_{i:03d}', role=role, overrides=values))
    assert len({json.dumps(x['overrides'], sort_keys=True) for x in rows}) == len(rows)
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    a = p.parse_args()
    if datetime.now(timezone.utc) >= datetime.fromisoformat(END):
        raise ValueError('New dispatch window expired')
    root = a.root.resolve(); root.mkdir(parents=True, exist_ok=False)
    development = sample(2026100372, [('train', 32), ('imitation_validation', 8), ('development', 8)])
    write(root/'CONDITIONS.json', dict(schema='sii-research72-conditions-v1', conditions=development))
    sealed_seed = secrets.randbits(128)
    sealed = sample(sealed_seed, [('heldout', 24)])
    known = {json.dumps(x['overrides'], sort_keys=True) for x in development}
    assert not any(json.dumps(x['overrides'], sort_keys=True) in known for x in sealed)
    (root/'sealed').mkdir()
    write(root/'sealed/HELDOUT.json', dict(schema='sii-research72-conditions-v1', seed=sealed_seed, conditions=sealed))
    (root/'sealed/HELDOUT.json').chmod(0o400)
    write(root/'teacher.json', TEACHER)
    write(root/'PROTOCOL.json', dict(schema='sii-research72-v1', registered_utc=datetime.now(timezone.utc).isoformat(),
        authorization_start_utc=START, dispatch_deadline_utc=END,
        time_basis='User authorized approximately 3–4 days around 11:30 UTC Oct 3; conservative 72 h inclusive of planning. Stop early if sufficient evidence; finish in-flight episodes at cutoff.',
        source_base_commit=BASE, baseline_commit=BASELINE, protocol_generator_sha256=sha(Path(__file__)),
        condition_file_sha256=sha(root/'CONDITIONS.json'), sealed_condition_sha256=sha(root/'sealed/HELDOUT.json'),
        teacher_config_sha256=sha(root/'teacher.json'),
        world='office-validation-v6', geometry_sha256='173e404bed4531cd193afc299f7c2243c276ce75797a169d8ea7c49d0bda8d11',
        formal_model_sha256='d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3',
        physics_dt_s=.00005, duration_s=55, environment_seed=2026091751,
        unchanged=['geometry', 'target', 'planner', 'common WBC', '48D/7D actor contract', '25 Hz actor / 4 ms servo',
                   'actuator amplitude/slew', 'contact material', 'task/strict gates', 'ball launch 2 s'],
        disturbance_distribution=dict(fields=FIELDS, lower=LOW, upper=HIGH,
            scope='Same previously registered local disturbance ranges, new identities; not new geometry or broad real-world generalization.'),
        data_roles=dict(train=32, imitation_validation=8, development=8, sealed_final=24),
        first_batch=dict(teacher='enhanced35mm', episodes=48, qualification='full 55 s AND original task AND strict; failed executions retained outside positive demonstration set',
            training_targets='Save actual requested, clipped, filtered action and physical execution; common-filter-aware learning may be compared without changing deployment filter.'),
        budget_caps=dict(teacher_parameter_candidates=12, classical_candidates_per_family=12,
            learning_candidates_per_family_seed=24, training_seeds=[2026100301,2026100302,2026100303],
            rl_adaptation_steps_per_family_seed=80000,
            rl_families=['parameter_admittance','parameter_impedance','parameter_vmc','direct_metric','direct_office_task']),
        budgets_semantics='Caps, not promises of exhausted compute or equality of unlike operations. Each stage registers actual candidates before runs; ledger reports data, optimizer, simulator and wall time separately. Stop new development by hour 48 to reserve audit/test time.',
        fairness=['Same qualifying demonstrations/splits to pure ESN, MLP and RNN',
            '128 hidden/reservoir units; also report trainable/total parameters, latency and exposure',
            'Memoryless and temporal-loss ablations on matched data',
            'Classical/RL adaptation uses train/development only; frozen primitive-transfer results remain separate',
            'Freeze every final model before any sealed rollout; evaluate all registered finalists, no success eligibility filter',
            'No test-based retraining or gate/environment modification; preserve failure and numerical abort'],
        analysis=['Primary original task/strict success with paired conditions and seed uncertainty',
            'Contact exposure and P95/peak/force-magnitude integral by event; absent contact is NA',
            'Recovery latency with censoring; completion and released-placement evidence',
            'Conditional jointly-successful comparisons accompanied by full-cohort failures/coverage',
            'RMSE, cumulative tracking error, actual actuator peak/slew, peak speed',
            'Paired confidence intervals and multiplicity disclosure, no post-hoc weighted winner score'],
        resources=dict(local_simulators=1, local_threads=1, memory_max_per_worker='3G', swap_max=0, spark_simulators=4,
            placement='Prefer local learning/postprocessing; native frozen Spark libraries for physics parity.'),
        completion='Stop when protocol, robust comparisons, independent audits and report are complete, even if ESN does not win. Otherwise stop dispatch at deadline and publish remaining gaps. No journal submission or real-hardware claim.'))
    print(json.dumps(dict(root=str(root), protocol_sha256=sha(root/'PROTOCOL.json'),
        conditions_sha256=sha(root/'CONDITIONS.json'), sealed_sha256=sha(root/'sealed/HELDOUT.json'))))


if __name__ == '__main__':
    main()
