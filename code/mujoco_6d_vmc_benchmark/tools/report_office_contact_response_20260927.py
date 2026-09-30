"""Independently verify untouched rollout and cloned-state response estimates."""
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    base = ROOT / 'outputs/esn_office_contact_response_20260927'
    case = base / 'results/response'
    reference = ROOT / 'outputs/esn_office_oracle_authority_20260927/results/parity'
    result = json.loads((case / 'rollout.json').read_text())
    old = json.loads((reference / 'rollout.json').read_text())
    assert result['model_sha256'] == old['model_sha256'] == digest(case / 'rollout.mjb')
    assert result['source_sha256'] == old['source_sha256']
    assert not result['task_success'] and not result['full_task_horizon_completed']
    for relative_path in ('rollout.npz', 'rollout_ball_detail.npz', 'rollout_metrics/substep_metrics.npz'):
        with np.load(case / relative_path) as current, np.load(reference / relative_path) as prior:
            assert set(current.files) == set(prior.files)
            for key in current.files:
                np.testing.assert_array_equal(current[key], prior[key], err_msg=relative_path + ':' + key)
    response = json.loads((case / 'contact_response.json').read_text())
    assert response['truth_enters_live_controller'] is False
    assert response['state_sha256'] == digest(case / 'response_states.npz')
    model = mujoco.MjModel.from_binary_path(str(case / 'rollout.mjb'))
    assert model.na == 0
    independent = []
    with np.load(case / 'response_states.npz') as states:
        for i, row in enumerate(response['rows']):
            data = mujoco.MjData(model)
            for key in ('qpos', 'qvel', 'ctrl', 'qfrc_applied', 'mocap_pos', 'mocap_quat'):
                getattr(data, key)[:] = states[key][i]
            data.time = row['time_s']
            mujoco.mj_forward(model, data)
            nominal_acc = data.qacc.copy()
            nominal_smooth = data.qacc_smooth.copy()
            relative = states['relative_jacobian'][i]
            rows = []
            for trial in row['trials']:
                clone = mujoco.MjData(model)
                mujoco.mj_copyData(clone, model, data)
                clone.ctrl[:7] = trial['torque_nm']
                mujoco.mj_forward(model, clone)
                constrained = float(relative @ (clone.qacc - nominal_acc))
                free = float(relative @ (clone.qacc_smooth - nominal_smooth))
                np.testing.assert_allclose(constrained, trial['constrained_solve_delta_acceleration_mps2'], atol=1e-6, rtol=1e-5)
                np.testing.assert_allclose(free, trial['free_mass_prediction_delta_acceleration_mps2'], atol=1e-8, rtol=1e-8)
                rows.append(dict(label=trial['label'], independent_free_delta_mps2=free,
                                 independent_constrained_delta_mps2=constrained))
            independent.append(dict(depth_m=row['actual_depth_m'], responses=rows))
    report = dict(complete=True, all_rollout_ball_and_physical_arrays_exact_parity=True,
                  independent_state_solves_passed=True, reconstructed_response=independent,
                  source_sha256=digest(Path(__file__)),
                  input_hashes={str(p.relative_to(case)): digest(p) for p in sorted(case.rglob('*')) if p.is_file()},
                  conclusion='At these penetrating states, the high-impedance coupled contact solve absorbs almost all of the motor-induced change in unconstrained normal acceleration into changed constraint force. This explains local insensitivity, not global controller impossibility.',
                  contact_parameters_changed=False, goal_achieved=False)
    (base / 'CONTACT_RESPONSE_AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = ['# Cloned-state contact response (read-only diagnostic)', '',
             'All live rollout, ball detail and physical metric arrays exactly match parity. No truth entered control.', '',
             '| Depth um | Positive free acceleration change m/s2 | Constrained change m/s2 | Ratio |',
             '|---|---:|---:|---:|']
    for row in response['rows']:
        trial = row['trials'][1]
        lines.append(f"| {row['actual_depth_m']*1e6:.3f} | {trial['free_mass_prediction_delta_acceleration_mps2']:.6f} | "
                     f"{trial['constrained_solve_delta_acceleration_mps2']:.9f} | {trial['constrained_over_free_ratio']:.9g} |")
    lines += ['', report['conclusion'], '', 'No material/solver/gate adjustment is promoted. No full-task or hardware success credit.']
    (base / 'CONTACT_RESPONSE_AUDIT.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
