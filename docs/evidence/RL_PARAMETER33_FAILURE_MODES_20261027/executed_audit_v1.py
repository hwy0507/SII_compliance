"""Inspect saved outcome switches; no simulation, inference, or gate changes."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(root):
    os.sched_setaffinity(0, {52})
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    reg = json.loads((root/'REGISTRATION.json').read_text())
    assert reg['cycles'] == [32, 33] and len(reg['cases']) == 4
    assert not (root/'REVIEW.json').exists()
    for ref in reg['inputs'].values():
        assert sha(ref['path']) == ref['sha256']
    rows, traces = [], {}
    for case in reg['cases']:
        method, condition = case['method'], case['condition']
        pair = []
        for cycle in reg['cycles']:
            prefix = f'{method}:{condition}:{cycle}:'
            def read(name):
                return json.loads(Path(reg['inputs'][prefix+name]['path']).read_text())
            rollout, terminal = read('rollout.json'), read('TERMINAL.json')
            for name in ['office_task_v4_20260917.py', 'planned_hand_corner_20261002.py',
                         'validate_office_apparatus_v5_20260917.py']:
                assert rollout['source_sha256'][name] == reg['inputs'][name]['sha256']
            result = terminal['result']
            for key in ['task_success', 'strict_success', 'physical_valid', 'final_task_stage', 'abort_reason']:
                assert result[key] == rollout[key]
            assert result['full_task_horizon_completed'] and result['abort_reason'] is None
            peak = rollout['stats']['max_external_penetration_m']
            assert result['physical_valid'] == (peak <= .0002)
            assert result['strict_success'] == (result['task_success'] and result['physical_valid'])
            stages = {event['stage']: event['time_s'] for event in rollout['task_events']}
            row = dict(cycle=cycle, result=result, stage_times_s=stages,
                completion_time_s=terminal['completion_time_s'],
                model_sha256=terminal['model_sha256'],
                external_penetration_mm=peak*1000,
                penetration_margin_below_gate_mm=(.0002-peak)*1000,
                worst_external_pair=rollout['stats']['worst_external_pair'],
                object_final_position=rollout['object_final_position'],
                placement_error_xy_m=rollout['placement_error_xy_m'])
            path = Path(reg['inputs'][prefix+'rollout.npz']['path'])
            with np.load(path, allow_pickle=False) as data:
                assert data['time'].shape == (1375,)
                assert np.isfinite(data['time']).all() and np.all(np.diff(data['time']) > 0)
                if method == 'admittance' and condition == 'active_long_train_0300':
                    keys = ['time', 'stage', 'task_ready_s', 'task_position_error_m',
                            'task_rotation_error_rad', 'task_speed_mps', 'object_position']
                    trace = {key: data[key].copy() for key in keys}
                    assert all(np.isfinite(value).all() for value in trace.values())
                    traces[cycle] = trace
                    row['last_saved_sample'] = {key: value[-1].tolist() for key, value in trace.items()}
                    row['carry_start_s'] = stages['carry']
                    row['time_available_after_carry_start_s'] = terminal['terminal_time_s']-stages['carry']
                    row['lift_stage_duration_s'] = stages['carry']-stages['lift']
                    row['carry_to_load_transfer_s'] = stages.get('load_transfer', float('nan'))-stages['carry']
                    if not np.isfinite(row['carry_to_load_transfer_s']):
                        row['carry_to_load_transfer_s'] = None
            pair.append(row)
        assert pair[0]['model_sha256'] == pair[1]['model_sha256']
        rows.append(dict(**case, cycles=pair))
    saved = root/'long0300_saved_trace.npz'
    np.savez_compressed(saved, **{f'cycle{cycle}_{key}': value
        for cycle, trace in traces.items() for key, value in trace.items()})
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    x = np.arange(len(rows))
    for index, cycle in enumerate([32, 33]):
        axes[0, 0].bar(x+(index-.5)*.35,
            [row['cycles'][index]['external_penetration_mm'] for row in rows],
            width=.35, label=str(cycle))
        trace = traces[cycle]
        axes[0, 1].step(trace['time'], trace['stage'], where='post', label=str(cycle))
        axes[1, 0].plot(trace['time'], trace['task_position_error_m']*1000, label=str(cycle))
        axes[1, 1].plot(trace['time'], trace['task_ready_s'], label=str(cycle))
    axes[0, 0].axhline(.2, color='red', linestyle='--', label='Original 0.2 mm gate')
    axes[0, 0].set(xticks=x, xticklabels=['I short0600', 'A long0300', 'A short0600', 'V short0000'],
        ylabel='Recorded external penetration (mm)', title='All four outcome-switch pairs')
    axes[0, 1].set(title='Admittance long0300: saved task stage', xlabel='Time (s)',
        yticks=[0, 1, 2, 3, 4, 5, 6, 7],
        yticklabels=['approach', 'align', 'grasp', 'lift', 'carry', 'load', 'release', 'retreat'])
    axes[1, 0].axhline(12, color='grey', linestyle='--', label='Nominal waypoint tolerance')
    axes[1, 0].set(title='Saved WBC target-position error', xlabel='Time (s)', ylabel='Error (mm)')
    axes[1, 1].set(title='Saved task readiness timer', xlabel='Time (s)', ylabel='Ready time (s)')
    for axis in axes.flat:
        axis.legend(fontsize=8)
        axis.grid(alpha=.2)
    fig.suptitle('Saved32/33 outcomes; no physical replay or causal policy attribution')
    plot = root/'failure_modes.png'
    fig.savefig(plot, dpi=140)
    plt.close(fig)
    for ref in reg['inputs'].values():
        assert sha(ref['path']) == ref['sha256']
    result = dict(passed=True, time=time.time(), source_sha256=sha(__file__),
        registration_sha256=sha(root/'REGISTRATION.json'), cases=rows,
        inputs_unchanged=True, saved_trace_sha256=sha(saved), plot_sha256=sha(plot),
        new_physics=0, neural_inference=0, optimizer_updates=0, convergence_claim=False,
        limitation='Retrospective saved JSON/40ms trajectory inspection. Penetration is the existing recorded aggregate, not independently recomputed raw physics. WBC error is not a replay of route cursor, target selection, or the full readiness guard. Last saved sample precedes terminal time. Timing and outcome association do not establish causes of action changes, or a counterfactual success with extra time. Gates, horizon and learners unchanged.')
    (root/'REVIEW.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.root)
    except BaseException as error:
        (args.root/'FAILURE.json').write_text(json.dumps(dict(time=time.time(), error=repr(error)))+'\n')
        raise
