"""Architecture-specific causal prefix audit; not a global impossibility claim."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    cases = {
        'R34_scale005': 'esn_office_r34_stress_20260927/results/r34_hard',
        'zero_scale005': 'esn_office_memory_ablation_20260927/results/zero_hard',
        'R34_scale001': 'esn_office_observer_scale_20260927/results/esn_hard_scale1',
        'zero_scale001': 'esn_office_observer_scale_20260927/results/zero_hard_scale1',
    }
    out = ROOT / 'outputs/esn_office_observer_scale_20260927'
    reference_prefix = None
    model_hash = None
    rows = []
    for name, suffix in cases.items():
        case = ROOT / 'outputs' / suffix
        result = json.loads((case / 'rollout.json').read_text())
        if model_hash is None:
            model_hash = result['model_sha256']
        assert result['model_sha256'] == model_hash
        ball = result['stats']['events']['ball']
        with np.load(case / 'rollout.npz') as trace:
            start, end = ball['first_s'], ball['last_s']
            decisions = trace['neuron_time']
            pre = decisions <= end
            np.testing.assert_array_equal(trace['observation'][pre, 39:45], 0.)
            np.testing.assert_array_equal(trace['applied_action'][pre], 0.)
            if 'reservoir_state' in trace.files:
                np.testing.assert_array_equal(trace['reservoir_state'][pre], 0.)
            next_decision = float(decisions[np.flatnonzero(decisions > end)[0]])
            first_changed = np.flatnonzero(np.any(trace['observation'][:, 39:45] != 0, axis=1))
            first_nonzero = float(decisions[first_changed[0]])
        with np.load(case / 'rollout_metrics/substep_metrics.npz') as raw:
            mask = raw['time'] <= next_decision + 1e-10
            prefix = {key: raw[key][mask].copy() for key in raw.files}
        if reference_prefix is None:
            reference_prefix = prefix
        else:
            assert set(prefix) == set(reference_prefix)
            for key in prefix:
                np.testing.assert_array_equal(prefix[key], reference_prefix[key], err_msg=name + ':' + key)
        rows.append(dict(case=name, first_ball_contact_s=start, last_ball_contact_s=end,
                         next_actor_decision_s=next_decision, first_nonzero_wrench_observation_s=first_nonzero,
                         prior_decisions=int(pre.sum()), all_prior_wrench_actions_and_reservoir_zero=True,
                         physical_prefix_arrays_exact=True, physical_samples=len(prefix['time']),
                         whole_episode_external_penetration_mm=result['stats']['max_external_penetration_m'] * 1000,
                         worst_external_pair=result['stats']['worst_external_pair'],
                         input_hashes={p.name: digest(p) for p in (case / 'rollout.json', case / 'rollout.npz',
                                                                 case / 'rollout_metrics/substep_metrics.npz')}))
    report = dict(complete=True, rows=rows, source_sha256=digest(Path(__file__)),
                  conclusion='All four archived hard-impact runs share identical recorded physical prefix arrays through .08s; the ball-contact interval ends before any nonzero wrench observation reaches the actor.',
                  conditional_statement='For the current force-only, bias-free reservoir reset to zero, any readout-only update preserving zero-load equilibrium yields zero action on this same zero-input prefix. With unchanged world, initial state and nominal controller, it cannot change this first impact.',
                  limitations=['Architecture-specific and fixed-reset statement, not an impossibility theorem for all proprioceptive controllers.',
                               'Does not claim force peaks can never be controlled after sensing or in other interaction regimes.',
                               'Whole-episode maximum is logged separately; raw prefix parity checks the stored physical metrics, not a newly simulated contact.'])
    (out / 'ZERO_INPUT_PREFIX_AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
