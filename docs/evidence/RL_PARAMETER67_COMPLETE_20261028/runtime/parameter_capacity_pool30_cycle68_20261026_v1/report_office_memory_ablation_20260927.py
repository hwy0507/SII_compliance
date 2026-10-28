"""Failure-inclusive matched closed-loop reservoir ablation and replay audit."""
import hashlib
import json
import sys
from pathlib import Path

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


def main():
    base = ROOT / 'outputs/esn_office_memory_ablation_20260927'
    plan_path = ROOT / 'configs/esn_office_memory_ablation_20260927.json'
    plan = json.loads(plan_path.read_text())
    model = base / 'source_snapshot/models/r34.npz'
    paths = {key: ROOT / path for key, path in plan['reference_results'].items()}
    paths.update({job['id']: base / 'results' / job['id'] / 'rollout.json' for job in plan['jobs']})
    cases = {}
    missing = []
    for name, path in paths.items():
        if not path.exists() or not path.with_suffix('.npz').exists():
            missing.append(name)
            continue
        result = json.loads(path.read_text())
        row = dict(path=str(path.relative_to(ROOT)), result_sha256=digest(path),
                   trajectory_sha256=digest(path.with_suffix('.npz')), result=result)
        if result['neural_logging']['enabled']:
            assert result['neural_logging']['model_sha256'] == digest(model)
            actor = OfficeVMCMemoryESN(model)
            reset = result['neural_logging'].get('memory_ablation', 'none') == 'reset_each_observation'
            max_action = max_state = 0.
            with np.load(path.with_suffix('.npz')) as trace:
                for obs, expected, state in zip(trace['observation'], trace['applied_action'], trace['reservoir_state']):
                    if reset:
                        actor.reset()
                    max_action = max(max_action, float(np.max(np.abs(actor.act(obs) - expected))))
                    max_state = max(max_state, float(np.max(np.abs(actor.state - state))))
            assert max_action < 1e-10 and max_state < 1e-10
            row['replay_max_abs'] = dict(action=max_action, reservoir=max_state)
        else:
            with np.load(path.with_suffix('.npz')) as trace:
                assert np.count_nonzero(trace['applied_action']) == 0
        with np.load(path.with_suffix('.npz')) as trace:
            late = (trace['time'] > 50.) & (trace['stage'] == 5)
            row['late_load_transfer'] = dict(frames=int(late.sum()))
            if late.any():
                row['late_load_transfer'].update(
                    mean_action=trace['applied_action'][late].mean(axis=0).tolist(),
                    mean_pre_step_error_m=float(trace['task_position_error_m'][late].mean()),
                    max_ready_s=float(trace['task_ready_s'][late].max()),
                    mean_wrench=trace['observation'][late, 39:45].mean(axis=0).tolist())
        raw_path = path.parent / 'rollout_metrics/substep_metrics.npz'
        row['independent_substeps_available'] = raw_path.exists()
        if raw_path.exists():
            with np.load(raw_path) as raw:
                dt = raw['dt']
                error = raw['error'].astype(np.float64)
                metrics = result['metrics']
                independent = [float(np.sqrt(np.sum(error * error * dt[:, None]) / dt.sum())),
                               float(np.max(np.linalg.norm(raw['twist'][:, :3].astype(np.float64), axis=1))),
                               float(np.max(np.abs(raw['qfrc_actuator'])))]
                expected = [metrics['position_rmse_3d_m'], metrics['linear_speed_peak_mps'],
                            metrics['generalized_actuator_torque_peak_nm']]
                np.testing.assert_allclose(independent, expected, rtol=2e-7, atol=1e-8)
                assert abs(float(dt.sum()) - 55.) < 1e-7
            row['substeps_sha256'] = digest(raw_path)
        cases[name] = row
    paired = {}
    for condition in ('original', 'rod_start7', 'hard'):
        names = [f'{method}_{condition}' for method in ('r34', 'reset', 'zero')]
        if not all(name in cases for name in names):
            continue
        records = [cases[name]['result'] for name in names]
        assert len({r['model_sha256'] for r in records}) == 1
        excluded = {'output', 'esn_model', 'esn_mode', 'memory_ablation'}
        args = [{k: v for k, v in r['arguments'].items() if k not in excluded} for r in records]
        assert args[0] == args[1] == args[2]
        assert records[0]['fixture'] == records[1]['fixture'] == records[2]['fixture']
        common = set.intersection(*(set(r['source_sha256']) for r in records))
        allowed_change = 'validate_office_apparatus_v5_20260917.py'
        for source in common - {allowed_change}:
            assert len({r['source_sha256'][source] for r in records}) == 1, source
        initial = []
        for name in names:
            with np.load((ROOT / cases[name]['path']).with_suffix('.npz')) as trace:
                initial.append((trace['neuron_qpos'][0], trace['observation'][0], trace['qpos'][0]))
        for candidate in initial[1:]:
            for actual, expected in zip(candidate, initial[0]):
                np.testing.assert_array_equal(actual, expected)
        paired[condition] = dict(model_match=True, fixture_and_arguments_match=True,
                                 initial_state_observation_and_first_step_match=True,
                                 common_source_match_except_diagnostic_evaluator=True,
                                 evaluator_hashes=[r['source_sha256'][allowed_change] for r in records])
    complete = not missing
    report = dict(complete=complete, missing=missing, cases=cases, paired_audit=paired,
                  source_sha256=digest(Path(__file__)), plan_sha256=digest(plan_path),
                  checkpoint_sha256=digest(model), withheld_used=False,
                  caveat='Reset ESN retains current-input response and fixed trained weights; it is an inference ablation, not an optimized feedforward baseline. Three conditions do not establish generalization.')
    (base / 'MEMORY_ABLATION_RESULTS.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = ['# Closed-loop memory ablation', '', f'Complete: {complete}. Missing: {missing}.', '',
             '| Condition | Method | Task | Strict | RMSE mm | Torque Nm | Speed m/s | Penetration mm | Rod s |',
             '|---|---|---|---|---:|---:|---:|---:|---:|']
    for condition in ('original', 'rod_start7', 'hard'):
        for method in ('r34', 'reset', 'zero'):
            name = f'{method}_{condition}'
            if name not in cases:
                continue
            r = cases[name]['result']; m = r['metrics']; s = r['stats']
            lines.append(f"| {condition} | {method} | {r['task_success']} | {r['strict_success']} | "
                         f"{m['position_rmse_3d_m'] * 1000:.3f} | {m['generalized_actuator_torque_peak_nm']:.3f} | "
                         f"{m['linear_speed_peak_mps']:.5f} | {s['max_external_penetration_m'] * 1000:.6f} | "
                         f"{s['events'].get('rod', {}).get('duration_s', 0):.3f} |")
    lines += ['', report['caveat'], '', 'RMSE is distance to the current stage goal, time-weighted, not final placement error.']
    (base / 'MEMORY_ABLATION_RESULTS.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
