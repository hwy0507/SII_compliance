"""Independent read-only schema2 person anchor-0 diagnostics; no simulation.

Reconstruct contiguous force-qualified intervals directly from every physical
sample. Net displacement is additional reporting, not a new admission rule.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from teacher_bank_pilot_failure_causes_20260930 import sha


def analyze(folder):
    audit = json.loads((folder/'audit.json').read_text())
    request = json.loads((folder/'request.json').read_text())
    fixture = request['fixture']
    assert fixture['apparatus'] == 'person'
    hashes = {name: sha(folder/name) for name in audit['files_sha256']}
    assert hashes == audit['files_sha256'], 'Raw artifact hash mismatch'
    hashes['audit.json'] = sha(folder/'audit.json')
    hashes['request.json'] = sha(folder/'request.json')
    with np.load(folder/'exposure.npz', allow_pickle=False) as data:
        assert int(data['schema']) == 2
        raw = data['person_physics']
        saved = data['person_window_runs']
    assert raw.shape == (550000, 6) and np.isfinite(raw).all()
    with np.load(folder/'rollout_metrics/substep_metrics.npz', allow_pickle=False) as physics:
        np.testing.assert_allclose(raw[:, 0]+raw[:, 1], physics['time'], rtol=0, atol=1e-8)
        np.testing.assert_allclose(raw[:, 1], physics['dt'], rtol=0, atol=1e-12)
    np.testing.assert_allclose(raw[1:, 0], raw[:-1, 0]+raw[:-1, 1], rtol=0, atol=1e-8)
    start = fixture['start_s']
    retract = start+fixture['press_s']+fixture['hold_s']
    push = -np.asarray(fixture['axis'])/np.linalg.norm(fixture['axis'])
    window = (raw[:, 0] >= start-1e-9) & (raw[:, 0]+raw[:, 1] <= retract+1e-9)
    contact = window & (raw[:, 2] > .05)
    edges = np.diff(np.r_[False, contact, False].astype(int))
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    runs, recovered = [], []
    for first, end in zip(starts, ends):
        part = raw[first:end]
        delta = part[:, 3:]-part[0, 3:]
        signed = delta@push
        tangent = np.linalg.norm(delta-signed[:, None]*push, axis=1)
        duration = float(part[:, 1].sum())
        maximum = float(max(0., signed.max()))
        recovered.append([part[0, 0], part[-1, 0]+part[-1, 1], duration,
            tangent.max(), np.linalg.norm(delta, axis=1).max(), max(0., delta[:, 2].max()),
            part[:, 2].max(), maximum])
        runs.append(dict(first_index=int(first), end_index_exclusive=int(end),
            first_s=float(part[0, 0]), end_s=float(part[-1, 0]+part[-1, 1]),
            duration_s=duration, max_signed_push_m=maximum,
            net_signed_push_m=float(signed[-1]), min_signed_push_m=float(signed.min()),
            max_norm_displacement_m=float(np.linalg.norm(delta, axis=1).max()),
            net_norm_displacement_m=float(np.linalg.norm(delta[-1])),
            duration_qualified=duration > .4+1e-12,
            registered_qualified=duration > .4+1e-12 and maximum >= .01))
    recovered = np.asarray(recovered).reshape(-1, 8)
    np.testing.assert_allclose(recovered, saved, rtol=0, atol=1e-10)
    longest = max(range(len(runs)), key=lambda i: runs[i]['duration_s'])
    most_yield = max(range(len(runs)), key=lambda i: runs[i]['max_signed_push_m'])
    sustained = [i for i, run in enumerate(runs) if run['duration_qualified']]
    accepted = [i for i, run in enumerate(runs) if run['registered_qualified']]
    assert accepted == audit['exposure']['diagnostics']['accepted_run_indices']
    macro_part = raw[starts[0]:np.flatnonzero(window)[-1]+1]
    macro_signed = (macro_part[:, 3:]-macro_part[0, 3:])@push
    gaps = raw[starts[1:], 0]-(raw[ends[:-1]-1, 0]+raw[ends[:-1]-1, 1])
    threshold_failures = []
    if not sustained:
        threshold_failures.append('continuous_press_hold_hand_contact_not_over_0p4s')
    if not accepted:
        threshold_failures.append('signed_hand_yield_along_push_below_1cm')
    assert threshold_failures == audit['exposure']['reasons']
    return dict(method=request['method'], fixture=fixture, controller=request['teacher'],
        original_task=audit['task'], original_strict=audit['strict'], original_eligible=audit['eligible'],
        original_exposure=audit['exposure'], hashes_sha256=hashes,
        physical_sample_count=len(raw), physical_duration_s=float(raw[:, 1].sum()),
        recovered_runs_max_abs_difference=float(abs(recovered-saved).max()),
        independent_exposure_failures=threshold_failures,
        total_window_contact_s=float(recovered[:, 2].sum()), window_run_count=len(runs),
        longest_run_index=longest, longest_run=runs[longest],
        maximum_yield_run_index=most_yield, maximum_yield_run=runs[most_yield],
        sustained_run_indices=sustained, accepted_run_indices=accepted,
        macro=dict(origin='First in-window physical force-qualified sample, not preceding pose',
            first_s=float(macro_part[0, 0]), last_s=float(macro_part[-1, 0]),
            max_signed_push_m=float(macro_signed.max()), net_signed_push_m=float(macro_signed[-1]),
            caveat='Across intermittent contact and nominal task motion; not a gate or causal no-push comparison'),
        contact_predicate_gaps=dict(count=len(gaps), median_s=float(np.median(gaps)),
            p90_s=float(np.quantile(gaps, .9)), maximum_s=float(gaps.max()),
            fraction_le_1ms=float(np.mean(gaps <= .001+1e-10)),
            total_s=float(gaps.sum()),
            caveat='Force <= .05N splits; not proof of geometric detachment or numerical artifacts'),
        all_runs=runs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.run.resolve(), args.output.resolve()
    if output.exists() or root == output or root in output.parents:
        raise ValueError('Use new output directory outside original run')
    results = {method: analyze(root/f'search/active_long/{method}/c00/0')
               for method in ('vmc', 'admittance', 'impedance')}
    result = dict(scope='v10 training search c00 person anchor 0; no generalization claim',
        run=str(root), script_sha256=sha(Path(__file__)),
        source_sha256={name: sha(root/'source'/name) for name in
            ('tools/teacher_bank_rollout_20260930.py', 'tools/teacher_bank_exposure_20260930.py',
             'tools/teacher_bank_classical_20260930.py')},
        checks='Independent raw contiguous-run reconstruction; unchanged .05N/.4s/.01m gates; raw hash and physical time binding',
        cases=results)
    output.mkdir(parents=True)
    destination = output/'review.json'
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(output=str(destination), sha256=sha(destination))))


if __name__ == '__main__':
    main()
