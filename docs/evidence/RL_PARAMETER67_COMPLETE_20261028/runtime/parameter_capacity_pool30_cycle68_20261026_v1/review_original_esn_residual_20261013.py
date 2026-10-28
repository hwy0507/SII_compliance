"""Read-only replay and descriptive diagnostics of all eight old ESN episodes.

No physical integration, tuning, counterfactual success claim, or gate change.
Writes a new evidence file only; historical audits are never overwritten.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    source = args.run / 'source'
    sys.path.insert(0, str(source / 'scripts'))
    from current_student_policy_20260921 import load_current
    from wbc_velocity_residual_core import VelocityResidualActionFilter, VelocityResidualSafetyConfig

    paths = sorted((args.run / 'episodes').glob('esn__repair_development_*/AUDIT.json'))
    assert len(paths) == 8
    rows = []
    for audit_path in paths:
        p = audit_path.parent
        audit = json.loads(audit_path.read_text())
        execution = json.loads((p / 'execution.json').read_text())
        checked_source = {}
        for name in ('current_student_policy_20260921.py', 'office_vmc_memory_esn_20260927.py',
                     'wbc_velocity_residual_core.py', 'planned_hand_corner_20261002.py'):
            rel = 'scripts/' + name
            checked_source[rel] = sha(source / rel)
            assert checked_source[rel] == execution['source_sha256'][rel]
        for name, field in [('rollout.npz', 'trace_sha256'), ('execution_chain.npz', 'chain_sha256'),
                            ('rollout.mjb', 'model_sha256')]:
            assert sha(p / name) == audit[field]
        checkpoint = p / 'checkpoint.npz'
        assert sha(checkpoint) == 'acd3b27e37c3e7d7690570df5276f52492d6597951643bf5011ad8ac2aee2ec7'
        actor = load_current(checkpoint)
        safety = VelocityResidualSafetyConfig(**execution['action_filter_config'])
        filt = VelocityResidualActionFilter(safety)
        with np.load(p / 'rollout.npz') as z, np.load(p / 'execution_chain.npz') as chain:
            obs = z['observation']; time = z['neuron_time']; hand = z['hand']
            predicted = []; states = []; twists = []; scales = []
            for o in obs:
                a = actor.act(o)
                predicted.append(a.copy()); states.append(actor.state.copy())
                filtered = filt.filter(a, .04)
                twists.append(filtered.cartesian_yield_twist.copy()); scales.append(filtered.wbc_scale)
            np.testing.assert_array_equal(predicted, chain['requested_action'])
            np.testing.assert_array_equal(states, z['reservoir_state'])
            np.testing.assert_array_equal(twists, chain['yield_twist'])
            np.testing.assert_array_equal(scales, chain['wbc_scale'])
            # Exact zero-load equilibrium from reset, with real changing context.
            actor.reset(); zero_peak = 0.
            for o in obs:
                quiet = o.copy(); quiet[39:45] = 0
                zero_peak = max(zero_peak, float(np.max(np.abs(actor.act(quiet)))))
            assert zero_peak == 0.
            # Unused public-interface fields cannot alter this actor's output.
            actor.reset(); used = [*range(14, 17), *range(20, 23), *range(26, 29), *range(39, 48)]
            unused = sorted(set(range(48)) - set(used))
            for i, o in enumerate(obs):
                altered = o.copy(); altered[unused] = 123.456
                np.testing.assert_array_equal(actor.act(altered), predicted[i])
            def window(lo, hi):
                mask = (time >= lo - 1e-7) & (time < hi - 1e-7)
                raw = chain['requested_action'][mask]
                yz = chain['yield_twist'][mask, 2]
                return dict(start_s=lo, end_s=hi, frames=int(mask.sum()),
                    nominal_z_mean_mmps=float(obs[mask, 16].mean() * 1000),
                    requested_z_mean_mmps=float(raw[:, 3].mean() * safety.maximum_linear_yield_mps * 1000),
                    filtered_z_mean_mmps=float(yz.mean() * 1000),
                    z_request_abs_max=float(np.max(np.abs(raw[:, 3]))),
                    z_filter_difference_max_mmps=float(np.max(np.abs(raw[:, 3] * safety.maximum_linear_yield_mps - yz)) * 1000),
                    any_channel_slew_limited_fraction=float(chain['slew_limited'][mask].mean()),
                    wbc_scale_mean=float(chain['wbc_scale'][mask].mean()),
                    measured_z_mean_mmps=float((obs[mask, 16] - obs[mask, 28]).mean() * 1000))
            row = dict(condition=p.name.split('__')[1], checkpoint_sha256=sha(checkpoint),
                audit_sha256=sha(audit_path), source_sha256=checked_source,
                input_sha256={name: sha(p / name) for name in (
                    'rollout.npz', 'execution_chain.npz', 'execution.json', 'research_substeps.npz',
                    'independent_contacts.npz', 'research_channels.json')},
                task=audit['task_success'], strict=audit['strict_success'],
                rmse_mm=audit['rmse_mm'], peak_torque_nm=audit['peak_torque_nm'],
                peak_speed_mps=audit['peak_speed_mps'], penetration_mm=audit['penetration_mm'],
                exact_action_state_filter_replay=True, zero_load_from_reset_peak=zero_peak,
                unused_field_invariance=True, linear_yield_limit_mmps=safety.maximum_linear_yield_mps * 1000,
                release_start_s=audit['stages'].get('6', {}).get('start_s'),
                any_action_clipped_fraction=float(np.any(abs(chain['requested_action']) >= 1 - 1e-9, axis=1).mean()))
            if row['condition'] == 'repair_development_001':
                row['previously_identified_window'] = window(25.48, 30.20)
            with np.load(p / 'research_substeps.npz') as sub, np.load(p / 'independent_contacts.npz') as contacts:
                ts = contacts['time']; cursor = sub['route_cursor']; force = sub['contact_force_sum']
                edge = force[:, 4] > .01
                row['edge_contact_seconds_above_0_01N'] = float(edge.sum() * .00005)
                row['edge_force_peak_n'] = float(force[:, 4].max())
                row['edge_contact_first_last_s'] = [float(ts[edge][0]), float(ts[edge][-1])] if edge.any() else None
                # A descriptive waypoint residence, NOT a new stall/success gate.
                carry = audit['stages'].get('4')
                segments = []
                if carry:
                    idx = np.flatnonzero((ts >= carry['start_s'] - .04 - 1e-7) & (ts < carry['end_s'] - 1e-7))
                    changes = np.r_[0, np.flatnonzero(np.diff(cursor[idx]) != 0) + 1, len(idx)]
                    for a, b in zip(changes[:-1], changes[1:]):
                        part = idx[a:b]
                        if np.any(edge[part]):
                            segments.append((len(part), int(part[0]), int(part[-1])))
                if segments:
                    n, a, b = max(segments)
                    lo = float(ts[a] - .00005); hi = float(ts[b])
                    row['longest_edge_overlapping_waypoint_residence'] = dict(
                        cursor=int(cursor[a]), duration_s=n * .00005, **window(lo, hi))
            rows.append(row)
            print(json.dumps({k: v for k, v in row.items() if k not in ('input_sha256', 'source_sha256')}, ensure_ascii=False), flush=True)
    result = dict(scope='Frozen original ESN; all eight completed development identities; diagnostic only',
        physics_rerun=False, tuning=False, script_sha256=sha(Path(__file__)), rows=rows,
        limitations=['Exact replay uses the frozen implementation, not an independently derived controller.',
                    'No counterfactual physical rollout: no proof that stronger residuals resolve contact.',
                    'Waypoint residence may include useful motion; not a failure classification.',
                    'Task/strict/whole-episode metrics reused from hash-bound existing audits.',
                    'Unused-field invariance is not by itself proof of upstream observation provenance.'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
