"""Explain completed impedance stalls from saved telemetry only.

Contact labels are post-hoc diagnostics, never policy inputs. No simulation,
learning, parameter selection or changes to the bounded controller reference.
"""
import argparse
from pathlib import Path

import numpy as np

from office_v7_uniform24_20261008 import read, write, sha, now


def inspect(run):
    audit = read(run/'AUDIT.json')
    result = read(run/'rollout.json')
    assert sha(run/'rollout.npz') == audit['trace_sha256']
    with np.load(run/'impedance_servo.npz', allow_pickle=False) as archive:
        values = archive['values']; columns = list(archive['columns'])
        selection = values[:, 0] >= values[-1, 0]-10.
        window = values[selection]
        error = window[:, [columns.index('error_'+str(i)) for i in range(3)]]
        wrench = window[:, [columns.index('wrench_'+str(i)) for i in range(3)]]
        error_norm = np.linalg.norm(error, axis=1)
        scale = window[:, columns.index('feasible_scale')]
    with np.load(run/'impedance_repair_servo.npz', allow_pickle=False) as archive:
        values = archive['values']; columns = list(archive['columns'])
        window = values[selection]
        requested = window[:, [columns.index('requested_equivalent_qdot_'+str(i)) for i in range(7)]]
        limited = window[:, [columns.index('limited_equivalent_qdot_'+str(i)) for i in range(7)]]
        command_difference = np.max(abs(requested-limited), axis=1)
    with np.load(run/'parameter_actions.npz', allow_pickle=False) as archive:
        parameters = archive['parameters'][-250:]
        tank_scale = archive['energy_scale']
    with np.load(run/'rollout_metrics/substep_metrics.npz', allow_pickle=False) as archive:
        times = archive['time']
        speed = np.linalg.norm(archive['twist'][times >= times[-1]-10., :3].astype(float), axis=1)
    edge = result['stats'].get('unexpected_edge', {})
    return dict(run=str(run), task=audit['task_success'], strict=audit['strict_success'],
        stage=audit['stage'], full_horizon=audit['full_horizon'],
        placement_error_xy_m=audit['placement_error_xy_m'], max_lift_m=audit['max_lift_m'],
        unexpected_edge_contact=edge,
        last10s=dict(mean_position_spring_error_m=error.mean(0).tolist(),
            mean_position_spring_error_norm_m=float(error_norm.mean()),
            position_error_at_4cm_bound_fraction=float(np.mean(error_norm >= .04-1e-7)),
            mean_commanded_cartesian_force_n=wrench.mean(0).tolist(),
            rms_actual_linear_speed_mps=float(np.sqrt(np.mean(speed**2))),
            command_limiter_changed_fraction=float(np.mean(command_difference > 1e-10)),
            torque_feasible_scale_min=float(scale.min()),
            mean_applied_parameters=parameters.mean(0).tolist()),
        whole_episode_min_parameter_energy_scale=float(tank_scale.min()),
        evidence={name:sha(run/name) for name in ('AUDIT.json','rollout.json',
            'impedance_servo.npz','impedance_repair_servo.npz','parameter_actions.npz',
            'rollout_metrics/substep_metrics.npz')})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); root = a.root.resolve(); assert not a.output.exists()
    state = read(root/'parameter_impedance_segment011k/execution.json')
    assert state['status'] == 'complete'
    rows = [dict(role='train', condition=row['condition_id'], **inspect(Path(row['run']))) for row in state['rows']]
    for condition in read(root/'CONDITIONS.json')['conditions']:
        if condition['role'] != 'development': continue
        run = root/('parameter_impedance_segment011k__'+condition['id'])
        receipt = root/(run.name+'.execution.json')
        if receipt.exists() and read(receipt)['status'] == 'complete':
            rows.append(dict(role='development', condition=condition['id'], **inspect(run)))
    report = dict(created_utc=now(), source_sha256=sha(__file__), new_physics_steps=0,
        gradient_updates=0, episodes=rows,
        interpretation='Association from saved trajectories, not a causal intervention or proof that impedance cannot succeed. '
            'A 4cm spring-reference boundary is an existing controller constraint, not an actuator limit; it is unchanged. '
            'Commanded wrench is a controller output, not measured contact force. '
            'Contact truth is used only for this post-hoc failure analysis, never supplied to the policy.')
    write(a.output, report)
    print('Completed episodes inspected:', len(rows))
    for role in ('train','development'):
        selected = [r for r in rows if r['role'] == role]
        print(role, 'episodes', len(selected), 'carry', sum(r['stage']=='carry' for r in selected),
              'edge_contact_seconds', [round(r['unexpected_edge_contact'].get('duration_s',0),3) for r in selected])


if __name__ == '__main__': main()
