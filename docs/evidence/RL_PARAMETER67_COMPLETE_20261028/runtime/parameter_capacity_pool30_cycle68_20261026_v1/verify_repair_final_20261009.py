"""Verify the complete repaired16x24 cohort and compute all ESN paired contrasts.

This is analysis only. Require an already frozen model registry and completed
final evaluation. No checkpoint selection, learning, or simulator is invoked.
"""
import argparse
import math
from pathlib import Path
import numpy as np
from office_v7_uniform24_20261008 import read, write, sha, now
from report_office_v7_uniform24_20261008 import build, LABELS
from research72_paired_statistics_20261003 import crossed_difference, contact_pair_arrays, recovery_summary
from evaluate_baseline_repair_20261008 import validate_candidate


def mcnemar(left, right):
    wins = sum(bool(a) and not bool(b) for a,b in zip(left,right))
    losses = sum(bool(b) and not bool(a) for a,b in zip(left,right))
    n = wins+losses
    probability = min(1., 2*sum(math.comb(n,k) for k in range(min(wins,losses)+1))/2**n) if n else 1.
    return dict(esn_only=wins, comparator_only=losses, discordant=n, exact_two_sided_p=probability)


def holm(values):
    ordered = sorted(values, key=values.get)
    previous = 0.
    adjusted = {}
    for rank,key in enumerate(ordered):
        previous = max(previous, min(1., values[key]*(len(ordered)-rank)))
        adjusted[key] = previous
    return adjusted


def contrast(esn, other):
    result = {}
    for key in ('task_success','strict_success'):
        a = [r[key] for r in esn]
        b = [r[key] for r in other]
        result[key] = dict(mcnemar(a,b), paired_difference=crossed_difference([a],[b]))
    both_full = np.array([[a['full_horizon'] and b['full_horizon'] for a,b in zip(esn,other)]])
    both_strict = both_full & np.array([[a['strict_success'] and b['strict_success'] for a,b in zip(esn,other)]])
    result['global_metrics'] = {}
    for key in ('rmse_mm','peak_torque_nm','peak_speed_mps'):
        a,b = [[r[key] for r in rows] for rows in (esn,other)]
        result['global_metrics'][key] = dict(
            jointly_full=crossed_difference([a],[b],eligible=both_full),
            jointly_strict=crossed_difference([a],[b],eligible=both_strict))
    result['contact_metrics'] = {}
    for event in ('ball','human','rod','unknown_edge'):
        result['contact_metrics'][event] = {}
        for key in ('contact_p95_force_n','impulse_ns','contact_duration_s'):
            a,b,eligible = contact_pair_arrays([esn],[other],event,key)
            result['contact_metrics'][event][key] = crossed_difference(a,b,eligible=eligible)
    result['scope'] = 'ESN minus comparator; one frozen model per family, NOT a training-seed variance estimate. Contact comparisons condition on both strict success and exposure and are exploratory, not causal effects.'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    assert not args.output.exists()
    lock = read(root/'FINAL_MODEL_LOCK.json')
    assert lock['status'] == 'frozen' and lock['protocol_sha256'] == sha(root/'PROTOCOL.json')
    assert sha(lock['models']) == lock['models_sha256']
    for name,digest in lock['source_hashes'].items(): assert sha(Path(lock['source'])/name) == digest
    for candidate in read(lock['models'])['candidates']: validate_candidate(candidate)
    final = root/'final_evaluation'
    execution = read(final/'execution.json')
    assert execution['status'] == 'complete' and execution['completed'] == execution['expected'] == 384
    rebuilt = build(final)
    saved = read(final/'REPORT.json')
    assert {k:v for k,v in rebuilt.items() if k != 'interpretation'} == {k:v for k,v in saved.items() if k != 'interpretation'}
    assert rebuilt['complete'] and len({(r['family'],r['condition_id']) for r in rebuilt['rows']}) == 384
    assert all(f['completed'] == 24 for f in rebuilt['families'])
    assert read(final/'PROTOCOL.json')['parent_protocol_sha256'] == sha(root/'PROTOCOL.json')
    verified = []
    for row in rebuilt['rows']:
        run = Path(row['receipt']).with_suffix('').with_suffix('')
        audit = row['audit']
        assert sha(run/'rollout.npz') == row['trace_sha256']
        assert sha(run/'rollout.mjb') == audit['model_sha256']
        assert sha(run/'execution_chain.npz') == audit['chain_sha256']
        assert sha(run/'rollout_metrics/substep_metrics.npz') == audit['metrics_sha256']
        assert audit['common_filter_replay_max_abs'] == 0.
        family = row['family']
        if family.startswith('parameter_') or family.startswith('direct_'):
            assert audit['raw_actor_replay_max_abs'] == 0. and audit['normalization_unchanged']
        elif audit['actor_replay_performed']:
            assert audit['action_replay_max_abs'] <= 1e-10
            if audit['reservoir_replay_max_abs'] is not None:
                assert audit['reservoir_replay_max_abs'] <= 1e-10
        else:
            assert family.startswith('classical_') or family == 'nominal_zero'
        verified.append(dict(family=family,condition_id=row['condition_id'],trace_sha256=row['trace_sha256']))
    grouped = {family:sorted([r for r in rebuilt['rows'] if r['family']==family],key=lambda r:r['condition_id']) for family in LABELS}
    ids = [r['condition_id'] for r in grouped['esn']]
    assert all([r['condition_id'] for r in rows] == ids for rows in grouped.values())
    comparisons = {family:contrast([r['metrics'] for r in grouped['esn']], [r['metrics'] for r in rows])
        for family,rows in grouped.items() if family != 'esn'}
    for key in ('task_success','strict_success'):
        adjusted = holm({family:value[key]['exact_two_sided_p'] for family,value in comparisons.items()})
        for family,value in comparisons.items(): value[key]['holm_adjusted_p_over_15_comparators'] = adjusted[family]
    recoveries = {family:{event:recovery_summary([r['metrics'] for r in rows],event)
        for event in ('ball','human','rod')} for family,rows in grouped.items()}
    args.output.mkdir()
    write(args.output/'VERIFIED_SUMMARY.json',dict(created_utc=now(),source_sha256=sha(__file__),
        report_sha256=sha(final/'REPORT.json'), lock_sha256=sha(root/'FINAL_MODEL_LOCK.json'),
        complete=True, episodes_verified=384, families=rebuilt['families'],
        raw_artifact_hashes_verified=True, report_rebuilt_exact_except_declared_interpretation=True,
        short_failures_retained=True, verified_pairs=verified,
        classical_replay_scope='Common filter and policy consistency; native torque shield/servo recurrence audited separately, not a full independent dynamics replay.'))
    write(args.output/'PAIRED_COMPARISONS.json',dict(created_utc=now(),source_sha256=sha(__file__),
        comparisons=comparisons, recovery=recoveries,
        multiplicity='Exact success tests adjusted separately over15 comparators for Task and Strict. Bootstrap metric intervals are exploratory without multiplicity correction.',
        limitation='Conditional metric comparisons exclude failures only for a separately labeled subset; full failure counts remain in all-method success table. No contact is NA. Finite24-condition results are not a proof of real-world generalization.'))
    print('Verified384episodes and15paired comparisons; no simulation or selection',flush=True)


if __name__ == '__main__': main()
