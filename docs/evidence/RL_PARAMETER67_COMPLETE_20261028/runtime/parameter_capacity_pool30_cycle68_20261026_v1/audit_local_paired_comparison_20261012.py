"""Read-only final integrity audit of the registered 168-row development cohort.

The campaign already recomputes physics/contact metrics from raw substeps. This
separate pass verifies the complete identity grid, evidence hashes, actor replay,
and aggregation. It adds no training, physics, selection, or held-out reads.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

from compare_local_baselines_20261012 import REFERENCE, require, summarise
from local_rl_campaign_20261009 import hashes
from office_v7_uniform24_20261008 import read, sha, now


def verify_grid(rows, methods, conditions):
    expected = {(m, c) for m in methods for c in conditions}
    counts = Counter((r['method'], r['condition']) for r in rows)
    require(set(counts) == expected and all(n == 1 for n in counts.values()),
            'Incomplete, duplicate, or unregistered method/condition grid')


def verify_values(audit, metrics):
    for key in ('task_success', 'strict_success', 'full_horizon'):
        require(audit[key] == metrics[key], 'Outcome mismatch: ' + key)
    require(not metrics['task_success'] or metrics['full_horizon'], 'Short episode counted successful')
    require(not metrics['strict_success'] or metrics['task_success'], 'Strict without task')
    for key in ('rmse_mm', 'peak_torque_nm', 'peak_speed_mps'):
        require(abs(audit[key] - metrics[key]) < 1e-4, 'Metric mismatch: ' + key)


def audit(root):
    reg, state = read(root/'REGISTRATION.json'), read(root/'execution.json')
    require(state['status'] == 'complete_review_required', 'Campaign not complete')
    require(state['registration_sha256'] == sha(root/'REGISTRATION.json'), 'Registration changed')
    require(state['new_episodes_completed'] == 64 and state['verified_rows'] == 168, 'Wrong completion counts')
    require(state['final_test_reads'] == 0 and not state['server_compute'], 'Execution scope changed')
    for name, key in [('SOURCE_HASHES.json', 'source_manifest_sha256'),
                      ('CONDITIONS.json', 'condition_sha256'),
                      ('REFERENCE_MODELS.json', 'reference_manifest_sha256')]:
        require(sha(root/name) == reg[key], 'Frozen manifest changed: ' + name)
    require(hashes(root/'source') == read(root/'SOURCE_HASHES.json'), 'Frozen source changed')
    lock, report = read(root/'MODEL_LOCK.json'), read(root/'REPORT.json')
    methods = list(REFERENCE) + lock['classical_finalists'] + list(lock['rl']['methods'])
    conditions = {c['id']: c for c in read(root/'CONDITIONS.json')['conditions']}
    require(len(methods) == len(set(methods)) == 21 and len(conditions) == 8, 'Wrong roster')
    require(all(c['role'] == 'development' for c in conditions.values()), 'Not development')
    require(report['final_test_reads'] == 0 and report['expected_rows'] == 168, 'Report scope changed')
    verify_grid(report['rows'], methods, conditions)
    require(report['methods'] == summarise(report['rows'], methods, set(conditions)), 'Aggregation changed')
    references = {c['family']: c for c in lock['references']}
    for c in references.values():
        if c.get('checkpoint'):
            require(sha(c['checkpoint']) == c['checkpoint_sha256'], 'Checkpoint changed')
    evidence = []
    for row in report['rows']:
        path, metric_path = Path(row['run']), Path(row['metric_file'])
        require(sha(metric_path) == row['metric_sha256'], 'Metric file changed')
        metrics = read(metric_path)
        require(metrics == row['metrics'], 'Embedded metrics changed')
        require(sha(path/'AUDIT.json') == row['audit_sha256'], 'Worker audit changed')
        worker_audit, execution = read(path/'AUDIT.json'), read(path/'execution.json')
        require(execution['status'] == 'complete', 'Worker incomplete')
        require(sha(path/'execution.json') == metrics['execution_sha256'], 'Worker execution changed')
        require(sha(path/'rollout.mjb') == reg['formal_model_sha256'] == metrics['model_sha256'], 'Physics model changed')
        for filename, key in [('rollout.npz', 'trace_sha256'),
                              ('rollout_metrics/substep_metrics.npz', 'native_metrics_sha256'),
                              ('research_substeps.npz', 'research_metrics_sha256')]:
            require(sha(path/filename) == metrics[key], 'Raw evidence changed: ' + str(path/filename))
        require(row['trace_sha256'] == metrics['trace_sha256'] == worker_audit['trace_sha256'], 'Trace identity mismatch')
        require(sha(path/'execution_chain.npz') == worker_audit['chain_sha256'], 'Action chain changed')
        arguments = read(path/'rollout.json')['arguments']
        require(all(arguments[k] == v for k, v in conditions[row['condition']]['overrides'].items()), 'Condition changed')
        require(worker_audit['common_filter_replay_max_abs'] == 0, 'Common filter replay failed')
        verify_values(worker_audit, metrics)
        reference = references.get(row['method'], {})
        if reference.get('checkpoint'):
            require(execution['checkpoint_sha256'] == reference['checkpoint_sha256'], 'Executed checkpoint mismatch')
            require(worker_audit['actor_replay_performed'] and worker_audit['action_replay_max_abs'] <= 1e-10,
                    'Student action replay failed')
            state_error = worker_audit['reservoir_replay_max_abs']
            require(state_error is None or state_error <= 1e-10, 'Student state replay failed')
        evidence.append(dict(method=row['method'], condition=row['condition'], run=str(path),
                             metric_sha256=row['metric_sha256'], trace_sha256=row['trace_sha256']))
        print('verified', len(evidence), row['method'], row['condition'], flush=True)
    return dict(status='passed', created_utc=now(), source_sha256=sha(Path(__file__)),
                registration_sha256=sha(root/'REGISTRATION.json'), report_sha256=sha(root/'REPORT.json'),
                verified_rows=len(evidence), methods=report['methods'], evidence=evidence,
                new_physics_steps=0, final_test_reads=0,
                limitation='Integrity/aggregation audit of independently recomputed development metrics; not another simulation, convergence proof, or held-out test.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    require(not a.output.exists(), 'Preserve existing audit')
    result = audit(a.root)
    with a.output.open('x') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')
