"""Hand-calculated metric contract checks, never experimental results."""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path


def check(auditor):
    spec = importlib.util.spec_from_file_location('checked_special_auditor', auditor)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    models = {f'{f}_s{s}': dict(name=f'{f}_s{s}', family=f, seed=s)
              for f in ('esn_ridge', 'rnn_scratch', 'mlp_scratch') for s in (1, 2, 3)}
    rows = []
    for name in models:
        # Two BOTH successes, a Task-only success, and a safe Task failure.
        # Peak torque must include all four; contact pooling must include the
        # Task-only episode. Reference is shared across all nine models.
        for k, (task, strict, t, peak, contact, ratio, violation) in enumerate((
            (True, True, 10., 10., 1., 1., False),
            (True, True, 20., 20., 0., None, False),
            (True, False, 5., 30., 3., 0., True),
            (False, False, None, 100., 0., None, False))):
            rows.append(dict(method=name, condition=f'c{k}', task_success=task,
                strict_success=strict, completion_time_s=t, peak_torque_nm=peak,
                comfort=dict(human_contact_duration_s=contact,
                    human_comfort_torque_compliance=ratio, machine_safety_violation=violation)))
    original = copy.deepcopy(rows)
    ref, methods, families = module.summaries(rows, models)
    assert rows == original, 'Summary mutated source rows'
    assert ref == 10., 'Task-only fast completion must not set BOTH reference'
    expected = dict(episodes=4, task_success=3, strict_success=2, both_success=2,
        task_success_rate=.75, strict_success_rate=.5, spt_mean=.75,
        spt_valid_episodes=2, spt_missing_time_episodes=0, peak_torque_mean_nm=40.,
        human_comfort_torque_compliance_contact_time_weighted=.25,
        human_contact_duration_s_total=4., machine_compliance_rate=.75)
    assert all(v == expected for v in methods.values())
    assert all(families[f]['spt_mean']['mean'] == .75 and
               families[f]['spt_mean']['sample_sd'] == 0 for f in families)
    checks = ['hand_computed_six_metrics_all_failure_denominators',
              'both_only_global_reference_excludes_faster_task_only',
              'comfort_contact_time_weighted_not_episode_mean', 'source_rows_not_mutated']
    for invalid in (None, 0., -1., float('nan'), float('inf')):
        damaged = copy.deepcopy(rows)
        damaged[0]['completion_time_s'] = invalid
        try:
            module.summaries(damaged, models)
        except ValueError as exc:
            assert 'completion time' in str(exc)
        else:
            raise AssertionError('Invalid BOTH completion time accepted')
    checks.append('five_missing_or_invalid_both_times_rejected')
    damaged = copy.deepcopy(rows)
    for row in damaged:
        row['task_success'] = row['strict_success'] = False
        row['completion_time_s'] = None
    ref, empty, _ = module.summaries(damaged, models)
    assert ref is None and all(v['spt_mean'] is None and v['spt_valid_episodes'] == 0
                               and v['episodes'] == 4 for v in empty.values())
    checks.append('zero_success_spt_is_na_failures_retained')
    no_contact = copy.deepcopy(rows)
    for row in no_contact:
        row['comfort'].update(human_contact_duration_s=0., human_comfort_torque_compliance=None)
    _, nc, nf = module.summaries(no_contact, models)
    field = 'human_comfort_torque_compliance_contact_time_weighted'
    assert all(v[field] is None for v in nc.values())
    assert all(v[field]['mean'] is None for v in nf.values())
    checks.append('no_contact_method_and_family_remain_na')
    partial = copy.deepcopy(rows)
    for row in partial:
        if row['method'] == 'esn_ridge_s1':
            row.update(task_success=False, strict_success=False, completion_time_s=None)
    _, _, summary = module.summaries(partial, models)
    assert summary['esn_ridge']['spt_mean']['per_seed'] == [None, .75, .75]
    assert summary['esn_ridge']['spt_mean']['mean'] is None
    checks.append('missing_seed_not_silently_dropped_from_family_spt')
    # Change a success in another family: every method must use the same T_ref.
    shared = copy.deepcopy(rows)
    next(r for r in shared if r['method'] == 'mlp_scratch_s3' and r['condition'] == 'c0')['completion_time_s'] = 4.
    ref, methods, _ = module.summaries(shared, models)
    assert ref == 4. and math.isclose(methods['esn_ridge_s1']['spt_mean'], .3)
    checks.append('reference_shared_across_families_and_seeds')
    return dict(status='synthetic_metric_contract_checks_passed_not_experiment',
        auditor_path=str(auditor.resolve()),
        auditor_sha256=hashlib.sha256(auditor.read_bytes()).hexdigest(),
        checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), checks=checks,
        limitations=['Synthetic hand-calculated values only; no student success or physical audit evidence.',
                    'Full-grid, source/hash, replay, finite and completion gates are enforced by the full auditor, not summaries alone.'])


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--auditor', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    result = check(a.auditor)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(result)
