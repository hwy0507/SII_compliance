"""Deploy the prepared full69 loss audit only after reviewed actual69 launch."""
from pathlib import Path
import ast
import hashlib
import json
import os
import subprocess
import time

B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
HERE = Path(__file__).resolve().parent
RUN = B / 'runs/parameter_capacity_pool30_cycle69_20261026_v1'
OUT = B / 'runs/parameter69_loss_20261028_v1'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def live(job):
    path = Path(f'/proc/{job["pid"]}/stat')
    if not path.exists():
        return False
    stat = path.read_text().rsplit(')', 1)[1].split()
    return stat[19] == job['proc_start_ticks'] and stat[0] != 'Z'


def write_new(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')


def main():
    decision_path = B / 'runtime/prepare_parameter69_20261028_v1/DECISION69.json'
    decision = read(decision_path)
    assert decision['passed'] and decision['plot_inspected']
    assert decision['parent_cycle'] == 68 and decision['new_cycle'] == 69
    assert not decision['convergence_claim'] and not decision['automatic_followup']
    evidence = {Path(item['path']): item['sha256'] for item in decision['evidence'].values()}
    required = [
        B / 'runs/parameter_capacity65_67_reward_stability_20261028_v1' / name
        for name in ['REVIEW.json', 'SAVED_ARITHMETIC_REVIEW.json', 'PLOT_INSPECTION.json']
    ]
    required += [
        B / f'runs/{method}68_terminal_anchor_followup_20261028_v1' / name
        for method in ['vmc', 'admittance']
        for name in ['REVIEW.json', 'SAVED_VALUES_REVIEW.json', 'PLOT_INSPECTION.json']
    ]
    required += [
        B / 'runs/parameter68_loss_20261028_v1' / name
        for name in ['REVIEW.json', 'PAIRED_GATE_REVIEW.json', 'SAVED_REVIEW.json', 'PLOT_INSPECTION.json']
    ]
    required += [
        B / 'runs/parameter_task_label_audit68_20261028_v1' / name
        for name in ['FINISHED68.json', 'COMPLETE67_68.json', 'COMPLETE67_68_SAVED_REVIEW.json']
    ]
    required += [
        B / 'runs/parameter_capacity_pool30_cycle68_review_20261026_v1/REVIEW.json',
        B / 'runs/parameter_capacity_pool30_cycle68_review_20261026_v1/health/DIAGNOSIS.json',
        B / 'runs/parameter_capacity_pool30_cycle68_review_20261026_v1/health/PLOT_INSPECTION.json',
        RUN / 'CHECK_ONLY_COMPLETE.json',
        B / 'runs/parameter_capacity68_70_reward_stability_20261028_v1/PLAN.json',
    ]
    # The original68-70 window is pending69/70; require its fixed PLAN, not its future verdict.
    assert set(required) <= evidence.keys(), 'Full68 loss, labels, health, terminals, restore and fixed window PLAN must be bound'
    for path, digest in evidence.items():
        assert sha(path) == digest, str(path)
    launch_path = RUN / 'LAUNCH.json'
    launch = read(launch_path)
    assert launch['new_cycles'] == 1 and not launch['automatic_followup']
    assert {j['controller'] for j in launch['jobs']} == {'impedance', 'admittance', 'vmc'}
    assert len(launch['jobs']) == 3 and all(live(j) for j in launch['jobs'])
    source_review = read(HERE / 'SOURCE_REVIEW.json')
    assert source_review['passed']
    sources = {}
    for item in source_review['files']:
        path = HERE / item['name']
        assert sha(path) == item['sha256']
        sources[item['name']] = path.read_bytes()
        ast.parse(sources[item['name']])
    assert set(sources) == {'audit.py', 'paired_gate.py', 'review_saved.py', 'wait.py'}
    assert not OUT.exists(), 'No duplicate or partial deployment overwrite'
    OUT.mkdir()
    for name, data in sources.items():
        with (OUT / name).open('xb') as stream:
            stream.write(data)
        assert (OUT / name).read_bytes() == data
    plan = dict(time=time.time(), registered_after_training_launch=True,
                static_prepared_before_training=True, parent_run=str(RUN), jobs=launch['jobs'],
                python=str(B / 'env/bin/python'), fixed_timeout_seconds=7200,
                automatic_training=False, convergence_claim=False, diagnostic_cpu=54,
                window='Complete69 actual episode lengths; full descriptive49-69; paired68-69. '
                       'Original65-67 and all historical windows retained; original68-70 still pending69/70.',
                files={name: sha(OUT / name) for name in sources},
                actual_launch_sha256=sha(launch_path), decision69_sha256=sha(decision_path),
                deployment_source_sha256=sha(Path(__file__)))
    write_new(OUT / 'PLAN.json', plan)
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
               MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
    with (OUT / 'driver.log').open('x') as log:
        process = subprocess.Popen([plan['python'], str(OUT / 'wait.py')], stdout=log,
                                   stderr=subprocess.STDOUT, env=env, start_new_session=True)
    ticks = Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
    receipt = dict(pid=process.pid, proc_start_ticks=ticks, time=time.time(),
                   plan_sha256=sha(OUT / 'PLAN.json'), automatic_training=False)
    write_new(OUT / 'LAUNCH.json', receipt)
    assert live(receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
