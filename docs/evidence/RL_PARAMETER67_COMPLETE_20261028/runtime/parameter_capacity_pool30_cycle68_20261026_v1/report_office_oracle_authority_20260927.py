"""Audit privileged diagnostic traces without treating them as ESN results."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    base = ROOT / 'outputs/esn_office_oracle_authority_20260927'
    old = ROOT / 'outputs/esn_office_contact_solver_20260927/results/parity'
    parity = base / 'results/parity'
    with np.load(parity / 'rollout.npz') as a, np.load(old / 'rollout.npz') as b:
        assert set(a.files) == set(b.files)
        for key in a.files:
            np.testing.assert_array_equal(a[key], b[key], err_msg=key)
    with np.load(parity / 'rollout_metrics/substep_metrics.npz') as a, np.load(old / 'rollout_metrics/substep_metrics.npz') as b:
        assert set(a.files) == set(b.files)
        for key in a.files:
            np.testing.assert_array_equal(a[key], b[key], err_msg=key)
    ref = json.loads((parity / 'rollout.json').read_text())
    rows = []
    for mode in ('parity', 'oracle_slew', 'oracle_instant'):
        folder = base / 'results' / mode
        result = json.loads((folder / 'rollout.json').read_text())
        manifest = json.loads((folder / 'oracle_manifest.json').read_text())
        execution = json.loads((folder / 'execution.json').read_text())
        assert execution['exit_code'] == 0
        assert result['model_sha256'] == ref['model_sha256'] == digest(folder / 'rollout.mjb')
        assert result['source_sha256'] == ref['source_sha256']
        assert not result['task_success'] and not result['full_task_horizon_completed']
        assert manifest['deployed_policy_candidate'] is False
        with np.load(folder / 'oracle_substeps.npz') as z, np.load(parity / 'oracle_substeps.npz') as reference:
            commands = z['command']
            active = np.flatnonzero(z['contact_available'])
            onset = int(active[0])
            np.testing.assert_array_equal(z['command'][:onset], reference['command'][:onset])
            assert np.all(np.abs(commands) <= np.array([87, 87, 87, 87, 12, 12, 12]) + 1e-10)
            delta = np.diff(commands, axis=0) / .0000015625
            np.testing.assert_allclose(delta, z['command_rate'][1:], rtol=1e-12, atol=1e-9)
            physical_rates = np.max(np.abs(delta), axis=0)
            window_rates = np.max(np.abs(commands[2560:] - commands[:-2560]), axis=0) / .004
            bounds = np.array([700, 700, 700, 700, 160, 160, 160])
            if mode in ('parity', 'oracle_slew'):
                assert np.all(window_rates <= bounds + 1e-6)
            if mode == 'oracle_slew':
                assert np.all(physical_rates <= bounds + 1e-6)
            with np.load(folder / 'rollout_metrics/substep_metrics.npz') as raw:
                np.testing.assert_allclose(raw['qfrc_actuator'], commands, rtol=1e-6, atol=1e-6)
                assert abs(float(raw['dt'].sum()) - .08) < 1e-10
        rows.append(dict(mode=mode, penetration_mm=manifest['penetration_mm'],
                         physical_gate_passed=bool(manifest['penetration_mm'] <= .2), task_success=False,
                         identical_control_before_contact=True,
                         maximum_physical_step_command_rate_nmps=physical_rates.tolist(),
                         maximum_4ms_window_command_rate_nmps=window_rates.tolist(),
                         original_4ms_slew_budget_obeyed=bool(np.all(window_rates <= bounds + 1e-6)),
                         limits='Privileged diagnostic only; instantaneous variant also violates torque slew.',
                         hashes={str(p.relative_to(folder)): digest(p) for p in sorted(folder.rglob('*')) if p.is_file()}))
    report = dict(complete=True, prior_parity_all_trace_and_metric_arrays_exact=True,
                  source_sha256=digest(Path(__file__)), rows=rows,
                  caveats=['No global control-optimality proof.',
                           'The recorded manifest physical-step slew check is stricter than the original 4ms zero-order-hold command schedule; parity does obey its original 4ms rate budget.',
                           'All three probes fail the physical criterion; no successful task or ESN improvement is claimed.',
                           'No live ESN receives contact truth or additional sensing.'])
    (base / 'ORACLE_AUTHORITY_AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, indent=2))
    for row in rows:
        print(row['mode'], row['penetration_mm'], row['original_4ms_slew_budget_obeyed'])


if __name__ == '__main__':
    main()
