"""Audit all four frozen observer-calibration trials, including regressions."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def longest_true(mask):
    longest = current = 0
    for value in mask:
        current = current + 1 if value else 0
        longest = max(longest, current)
    return longest


def main():
    base = ROOT / 'outputs/esn_office_observer_scale_20260927'
    plan = ROOT / 'configs/esn_office_observer_scale_20260927.json'
    model = ROOT / 'outputs/esn_office_resolved_stress_20260927/r34_half_gain/model.npz'
    references = {
        'esn_original_scale1': 'esn_office_r34_stress_20260927/results/r34_original',
        'esn_hard_scale1': 'esn_office_r34_stress_20260927/results/r34_hard',
        'zero_original_scale1': 'esn_office_resolved_stress_20260927/results/zero_original_resolved',
        'zero_hard_scale1': 'esn_office_memory_ablation_20260927/results/zero_hard',
    }
    allowed_sources = {'haptic_vmc_teacher_20260916.py', 'validate_office_apparatus_v5_20260917.py'}
    rows = []
    for job in json.loads(plan.read_text())['jobs']:
        folder = base / 'results' / job['id']
        reference = ROOT / 'outputs' / references[job['id']]
        result = json.loads((folder / 'rollout.json').read_text())
        old = json.loads((reference / 'rollout.json').read_text())
        execution = json.loads((folder / 'execution.json').read_text())
        audit = json.loads((folder / 'observer_audit.json').read_text())
        assert execution['exit_code'] == 0 and execution['plan_sha256'] == digest(plan)
        assert result['execution_complete'] and result['full_task_horizon_completed']
        assert result['model_sha256'] == old['model_sha256'] == digest(folder / 'rollout.mjb')
        assert result['physics_resolution'] == old['physics_resolution']
        assert result['schedule'] == old['schedule']
        assert result['observer_settings']['friction_velocity_scale'] == .001
        assert audit['diagnostic_truth_used_by_controller'] is False
        assert audit['shadow_observer_used_by_controller'] is False
        assert audit['observer_reconstruction_max_abs_nm'] < 1e-10
        assert audit['sidecar_sha256'] == digest(folder / 'observer_truth_sidecar.npz')
        changed_sources = {k for k in result['source_sha256']
                           if result['source_sha256'][k] != old['source_sha256'].get(k)}
        assert changed_sources <= allowed_sources, changed_sources
        changed_arguments = {k: [old['arguments'].get(k), value]
                             for k, value in result['arguments'].items()
                             if value != old['arguments'].get(k)}
        assert set(changed_arguments) <= {
            'output', 'esn_model', 'observer_friction_velocity_scale',
            'esn_memory_ablation', 'rod_start', 'rod_hold'}, changed_arguments
        with np.load(folder / 'rollout.npz') as trace, np.load(folder / 'observer_truth_sidecar.npz') as side:
            np.testing.assert_allclose(side['time'][:-1], trace['neuron_time'], atol=1e-10, rtol=0)
            np.testing.assert_allclose(side['estimated'][:-1], trace['observation'][:, 32:39], atol=1e-10, rtol=0)
            assert len(trace['time']) == 1375
            if audit['actor'] == 'esn':
                assert result['neural_logging']['model_sha256'] == digest(model)
                actor = OfficeVMCMemoryESN(model)
                action_error = state_error = 0.
                for obs, action, state in zip(trace['observation'], trace['applied_action'], trace['reservoir_state'], strict=True):
                    action_error = max(action_error, float(np.max(np.abs(actor.act(obs) - action))))
                    state_error = max(state_error, float(np.max(np.abs(actor.state - state))))
                assert max(action_error, state_error) < 1e-10
            else:
                assert result['neural_logging']['model_sha256'] is None
                np.testing.assert_array_equal(trace['applied_action'], 0.)
                action_error = state_error = 0.
            # The stage stored here follows task.update. The terminal failed
            # stage has no outgoing transition; these are its actual gate inputs.
            stage5 = trace['stage'] == 5
            load_change = trace['observation'][:, 41] - trace['task_carry_load']
            ready_parts = {
                'position': trace['task_position_error_m'] < .012,
                'rotation': trace['task_rotation_error_rad'] < .12,
                'speed': trace['task_speed_mps'] < .025,
                'load_transfer': np.isfinite(trace['task_carry_load']) & (load_change > .4),
            }
            all_ready = np.logical_and.reduce(list(ready_parts.values())) & stage5
            readiness = dict(
                samples=int(stage5.sum()),
                max_ready_recorded_s=float(trace['task_ready_s'][stage5].max()),
                longest_consecutive_ready_samples=longest_true(all_ready),
                ready_fraction={k: float(v[stage5].mean()) for k, v in ready_parts.items()},
                final_position_error_mm=float(trace['task_position_error_m'][-1] * 1000),
                final_load_change_n=float(load_change[-1]),
                caveat='A successful transition sample is stored in stage6; stage5 excludes that sample.',
            )
        with np.load(folder / 'rollout_metrics/substep_metrics.npz') as raw:
            dt = raw['dt']
            assert abs(float(dt.sum()) - 55.) < 1e-7
            error = raw['error'].astype(np.float64)
            assert np.isfinite(error).all()
            measured = [float(np.sqrt(np.sum(error**2 * dt[:, None]) / dt.sum())),
                        float(np.max(np.linalg.norm(raw['twist'][:, :3].astype(np.float64), axis=1))),
                        float(np.max(np.abs(raw['qfrc_actuator'])))]
            keys = ['position_rmse_3d_m', 'linear_speed_peak_mps', 'generalized_actuator_torque_peak_nm']
            np.testing.assert_allclose(measured, [result['metrics'][k] for k in keys], rtol=2e-7, atol=1e-8)
        same_trajectory = {
            group: dict(duration_s=value['duration_s'],
                        candidate_error_rms_norm_nm=float(np.linalg.norm(value['error_rmse_nm'])),
                        shadow_old_error_rms_norm_nm=float(np.linalg.norm(value['baseline_error_rmse_nm'])))
            for group, value in audit['bins'].items()
        }
        def summary(j):
            return dict(task=j['task_success'], strict=j['strict_success'], stage=j['final_task_stage'],
                        rmse_mm=j['metrics']['position_rmse_3d_m'] * 1000,
                        peak_torque_nm=j['metrics']['generalized_actuator_torque_peak_nm'],
                        peak_speed_mps=j['metrics']['linear_speed_peak_mps'],
                        penetration_mm=j['stats']['max_external_penetration_m'] * 1000,
                        rod_contact_s=j['stats']['events'].get('rod', {}).get('duration_s', 0.),
                        task_events=j['task_events'], release_supported=j['release_supported'])
        rows.append(dict(case=job['id'], candidate=summary(result), reference=summary(old),
                         same_trajectory_estimation_errors=same_trajectory,
                         stage5_readiness=readiness, action_replay_max_abs=action_error,
                         reservoir_replay_max_abs=state_error, changed_sources=sorted(changed_sources),
                         changed_arguments=changed_arguments,
                         reference_result_sha256=digest(reference / 'rollout.json'),
                         files_sha256={str(p.relative_to(folder)): digest(p)
                                       for p in sorted(folder.rglob('*')) if p.is_file()}))
    report = dict(complete=True, independent_checks_passed=True, rows=rows,
                  candidate_promoted=False, default_scale_radps=.005, candidate_scale_radps=.001,
                  checkpoint_sha256=digest(model), plan_sha256=digest(plan),
                  source_sha256=digest(Path(__file__)),
                  caveats=['Same-trajectory old observer is a shadow, not a separate controller.',
                           'Truth includes payload and is offline only.',
                           'Task and ESN both receive changed proprioception; no new sensor or changed gate.',
                           'Ideal encoder simulation does not establish hardware calibration.',
                           'No-contact bins use instantaneous contact classification; filters can retain earlier contact.'])
    (base / 'OBSERVER_SCALE_AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = ['# Fixed observer calibration: failure-inclusive audit', '',
             'The .001 rad/s candidate is NOT promoted. Default .005 and R34 remain unchanged.', '',
             '| Case | Old task/strict | Candidate task/strict | Old stage5 shadow RMS Nm | Candidate stage5 RMS Nm | Final position error mm |',
             '|---|---|---|---:|---:|---:|']
    for row in rows:
        old, new = row['reference'], row['candidate']
        stage = row['same_trajectory_estimation_errors']['stage_5']
        lines.append(f"| {row['case']} | {old['task']}/{old['strict']} | {new['task']}/{new['strict']} | "
                     f"{stage['shadow_old_error_rms_norm_nm']:.6f} | {stage['candidate_error_rms_norm_nm']:.6f} | "
                     f"{row['stage5_readiness']['final_position_error_mm']:.4f} |")
    lines += ['', *report['caveats']]
    (base / 'OBSERVER_SCALE_AUDIT.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
